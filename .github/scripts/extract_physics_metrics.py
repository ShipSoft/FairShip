#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

"""
Extract lightweight physics metrics from ROOT files for git notes storage.

This script extracts key statistics and metadata from simulation/reconstruction
output files, storing them as compact JSON for quick comparisons in CI.
"""

import argparse
import json
import math
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Union

import ROOT
import tomllib

ROOT.gROOT.SetBatch(True)


def load_config(config_path: Optional[Union[str, Path]] = None) -> dict[str, Any]:
    """Load configuration from TOML file."""
    if config_path is None:
        config_path = Path(__file__).parent / "metrics_config.toml"

    with open(config_path, "rb") as f:
        config = tomllib.load(f)

    # Validate required configuration sections
    required_keys = {
        "files": ["process"],
        "extraction": ["max_histogram_depth", "fit_functions"],
        "comparison": ["float_tolerance", "n_sigma"],
    }

    for section, keys in required_keys.items():
        if section not in config:
            raise ValueError(f"Missing required config section: [{section}]")
        for key in keys:
            if key not in config[section]:
                raise ValueError(f"Missing required config key: [{section}].{key}")

    return config


def extract_tree_info(root_file: Any, tree_name: str) -> Optional[dict[str, Any]]:
    """Extract basic information from a TTree."""
    tree = root_file.Get(tree_name)
    if not tree or not isinstance(tree, ROOT.TTree):
        return None

    return {
        "entries": {"value": tree.GetEntries(), "compare": "exact"},
        "branches": {"value": tree.GetNbranches(), "compare": "exact"},
    }


def extract_histogram_stats(
    hist: Any, fit_functions: Optional[list[str]] = None
) -> Optional[dict[str, Any]]:
    """
    Extract statistical summary from a histogram.

    Args:
        hist: ROOT histogram object (TH1, TH2, TH3, TProfile)
        fit_functions: List of fit function names to search for

    Returns
    -------
        Dictionary with histogram statistics, or None if not applicable
    """
    if not hist:
        return None

    # Only extract basic stats for 1D histograms
    # TH2, TH3, TProfile can be added later with appropriate metrics
    if not isinstance(hist, ROOT.TH1):
        return None

    # Skip TH2, TH3 for now (they inherit from TH1 but need different metrics)
    if isinstance(hist, (ROOT.TH2, ROOT.TH3)):
        return None

    entries = hist.GetEntries()
    mean = hist.GetMean()
    rms = hist.GetRMS()

    stats = {
        "entries": {
            "value": entries,
            "uncertainty": math.sqrt(entries) if entries > 0 else 0,
            "compare": "statistical",
        },
        "mean": {
            "value": mean,
            "uncertainty": hist.GetMeanError(),
            "compare": "statistical",
        },
        "rms": {
            "value": rms,
            "uncertainty": hist.GetRMSError(),
            "compare": "statistical",
        },
        "integral": {"value": hist.Integral(), "compare": "float"},
    }

    # Check for attached fit functions
    fit_func = None
    if fit_functions:
        for func_name in fit_functions:
            fit_func = hist.GetListOfFunctions().FindObject(func_name)
            if fit_func:
                break

    # If no named function found, get first TF1 in the list
    if not fit_func and hist.GetListOfFunctions().GetSize() > 0:
        for obj in hist.GetListOfFunctions():
            if isinstance(obj, ROOT.TF1):
                fit_func = obj
                break

    if fit_func and isinstance(fit_func, ROOT.TF1):
        stats["fit"] = {
            "type": {"value": fit_func.GetName(), "compare": "exact"},
            "parameters": {
                fit_func.GetParName(i): {
                    "value": fit_func.GetParameter(i),
                    "uncertainty": fit_func.GetParError(i),
                    "compare": "statistical",
                }
                for i in range(fit_func.GetNpar())
            },
        }

    return stats


def extract_histograms_recursive(
    directory: Any,
    path: str = "",
    max_depth: int = 3,
    fit_functions: Optional[list[str]] = None,
) -> dict[str, dict[str, Any]]:
    """
    Recursively extract histogram statistics from ROOT directory.

    Args:
        directory: ROOT directory to process
        path: Current path prefix for naming
        max_depth: Maximum recursion depth (decremented on each level)
        fit_functions: List of fit function names to search for

    Returns
    -------
        Dictionary mapping histogram paths to their statistics
    """
    if max_depth <= 0:
        return {}

    histograms = {}

    for key in directory.GetListOfKeys():
        obj_name = key.GetName()
        obj = directory.Get(obj_name)
        current_path = f"{path}/{obj_name}" if path else obj_name

        if isinstance(obj, ROOT.TDirectory):
            sub_hists = extract_histograms_recursive(
                obj, current_path, max_depth - 1, fit_functions
            )
            histograms.update(sub_hists)
        elif isinstance(obj, ROOT.TH1):
            stats = extract_histogram_stats(obj, fit_functions)
            if stats and stats["entries"]["value"] > 0:
                histograms[current_path] = stats

    return histograms


def extract_metrics_from_file(
    file_path: Path, config: dict[str, Any]
) -> Optional[dict[str, Any]]:
    """
    Extract all relevant metrics from a ROOT file.

    Args:
        file_path: Path to ROOT file
        config: Configuration dictionary

    Returns
    -------
        Dictionary with file metrics, or None if file cannot be opened

    Note:
        To add support for new ROOT object types (TGraph, TProfile, etc.):
        1. Write an extraction function (e.g., extract_graph_info)
        2. Add a new key to the metrics dict (e.g., "graphs": {})
        3. Add an isinstance check in the loop below
    """
    with ROOT.TFile.Open(str(file_path)) as root_file:
        if not root_file or root_file.IsZombie():
            return None

        metrics = {
            "file_size": file_path.stat().st_size,
            "trees": {},
            "histograms": {},
        }

        # Extract TTrees from top level
        for key in root_file.GetListOfKeys():
            obj = root_file.Get(key.GetName())
            if isinstance(obj, ROOT.TTree):
                tree_info = extract_tree_info(root_file, key.GetName())
                if tree_info:
                    metrics["trees"][key.GetName()] = tree_info  # type: ignore[index]

        # Extract histograms recursively from all directories
        metrics["histograms"] = extract_histograms_recursive(
            root_file,
            max_depth=config["extraction"]["max_histogram_depth"],
            fit_functions=config["extraction"]["fit_functions"],
        )

        return metrics


def extract_all_metrics(
    config_dir: Union[str, Path], config: dict[str, Any]
) -> Optional[dict[str, Any]]:
    """
    Extract metrics from all relevant files in a configuration directory.

    Args:
        config_dir: Directory containing ROOT files
        config: Configuration dictionary

    Returns
    -------
        Dictionary with metrics from all processed files, or None if dir not found
    """
    config_path = Path(config_dir)

    if not config_path.exists():
        print(f"ERROR: Configuration directory not found: {config_path}")
        return None

    metrics = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "configuration": config_path.name,
        "files": {},
    }

    for filename in config["files"]["process"]:
        file_path = config_path / filename
        if file_path.exists():
            file_metrics = extract_metrics_from_file(file_path, config)
            if file_metrics:
                metrics["files"][filename] = file_metrics  # type: ignore[index]

    return metrics


def main() -> int:
    """Extract physics metrics from ROOT files for git notes storage."""
    parser = argparse.ArgumentParser(
        description="Extract physics metrics from ROOT files for git notes storage"
    )
    parser.add_argument(
        "config_dir",
        help="Directory containing ROOT files (e.g., '.' for current directory)",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Output JSON file (default: stdout)",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON output",
    )
    parser.add_argument(
        "--config",
        help=(
            "Path to configuration file "
            "(default: metrics_config.toml in script directory)"
        ),
    )

    args = parser.parse_args()

    config = load_config(args.config)
    metrics = extract_all_metrics(args.config_dir, config)

    if metrics is None:
        return 1

    json_kwargs: dict[str, Any] = {"indent": 2} if args.pretty else {}
    json_output = json.dumps(metrics, **json_kwargs)

    if args.output:
        Path(args.output).write_text(json_output)
        print(f"Metrics written to {args.output}")
    else:
        print(json_output)

    return 0


if __name__ == "__main__":
    sys.exit(main())
