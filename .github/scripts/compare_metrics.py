#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

"""
Compare physics metrics from two JSON files.

Comparison modes are defined in the JSON for each metric:
- "exact": Values must be exactly equal
- "float": Floating-point comparison with relative tolerance
- "statistical": Compare within combined statistical uncertainties
"""

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any, Optional, Union

import yaml


def load_config(config_path: Optional[Union[str, Path]] = None) -> dict[str, Any]:
    """Load configuration from YAML file."""
    if config_path is None:
        config_path = Path(__file__).parent / "metrics_config.yaml"

    with open(config_path) as f:
        config = yaml.safe_load(f)

    # Validate required configuration for comparison
    if "comparison" not in config:
        raise ValueError("Missing required config section: [comparison]")
    if "float_tolerance" not in config["comparison"]:
        raise ValueError("Missing required config key: [comparison].float_tolerance")
    if "n_sigma" not in config["comparison"]:
        raise ValueError("Missing required config key: [comparison].n_sigma")

    return config


def compare_metric(
    ref_metric: dict[str, Any],
    new_metric: dict[str, Any],
    name: str,
    float_tolerance: float = 1e-9,
    n_sigma: float = 3.0,
) -> list[str]:
    """
    Compare two metrics based on their comparison mode.

    ref_metric/new_metric format:
    {
        "value": <number>,
        "compare": "exact" | "float" | "statistical",
        "uncertainty": <number>  # optional, required for "statistical"
    }
    """
    if not isinstance(ref_metric, dict) or not isinstance(new_metric, dict):
        return []

    ref_value = ref_metric.get("value")
    new_value = new_metric.get("value")
    compare_mode = ref_metric.get("compare", "exact")

    if compare_mode == "exact":
        if ref_value != new_value:
            return [f"  {name}: {ref_value} → {new_value}"]
        return []

    elif compare_mode == "float":
        if ref_value == 0 and new_value == 0:
            return []
        if ref_value == 0:
            if abs(new_value) > float_tolerance:  # type: ignore[arg-type]
                return [f"  {name}: 0 → {new_value:.4g}"]
            return []

        rel_diff = abs(new_value - ref_value) / abs(ref_value)  # type: ignore[operator,arg-type]
        if rel_diff > float_tolerance:
            return [
                f"  {name}: {ref_value:.4g} → {new_value:.4g} (Δ={rel_diff * 100:.4g}%)"
            ]
        return []

    elif compare_mode == "statistical":
        ref_unc = ref_metric.get("uncertainty", 0)
        new_unc = new_metric.get("uncertainty", 0)

        combined_unc = math.sqrt(ref_unc**2 + new_unc**2)

        if combined_unc == 0:
            if ref_value != new_value:
                return [f"  {name}: {ref_value} → {new_value} (no uncertainties)"]
            return []

        deviation = abs(ref_value - new_value) / combined_unc  # type: ignore[operator]
        if deviation > n_sigma:
            return [
                f"  {name}: {ref_value:.4g}±{ref_unc:.4g} → "
                f"{new_value:.4g}±{new_unc:.4g} ({deviation:.1f}σ)"
            ]
        return []

    return []


def compare_dict_recursive(
    ref_dict: dict[str, Any],
    new_dict: dict[str, Any],
    path: str = "",
    float_tolerance: float = 1e-9,
    n_sigma: float = 3.0,
) -> list[str]:
    """Recursively compare nested dictionaries of metrics."""
    differences = []

    for key, ref_value in ref_dict.items():
        if key not in new_dict:
            differences.append(f"  {path}{key}: missing in new metrics")
            continue

        new_value = new_dict[key]
        current_path = f"{path}{key}."

        if isinstance(ref_value, dict):
            if "value" in ref_value and "compare" in ref_value:
                diffs = compare_metric(
                    ref_value, new_value, f"{path}{key}", float_tolerance, n_sigma
                )
                differences.extend(diffs)
            else:
                diffs = compare_dict_recursive(
                    ref_value, new_value, current_path, float_tolerance, n_sigma
                )
                differences.extend(diffs)

    return differences


def compare_metrics(
    ref_metrics: dict[str, Any],
    new_metrics: dict[str, Any],
    float_tolerance: float = 1e-9,
    n_sigma: float = 3.0,
) -> tuple[list[str], dict[str, int]]:
    """
    Compare two metrics dictionaries.

    Each metric in the JSON specifies its comparison mode:
    - "exact": values must match exactly
    - "float": floating-point comparison with tolerance
    - "statistical": comparison within combined uncertainties

    float_tolerance: relative tolerance for "float" mode
    n_sigma: number of sigma for "statistical" mode
    """
    all_differences = []
    summary = {
        "files_compared": 0,
        "files_missing": 0,
        "trees_compared": 0,
        "histograms_compared": 0,
        "fits_compared": 0,
        "total_differences": 0,
    }

    ref_files = ref_metrics.get("files", {})
    new_files = new_metrics.get("files", {})

    for filename, ref_file in ref_files.items():
        if filename not in new_files:
            all_differences.append(f"\nFile missing: {filename}")
            summary["files_missing"] += 1
            continue

        summary["files_compared"] += 1
        new_file = new_files[filename]
        file_diffs = []

        for tree_name, ref_tree in ref_file.get("trees", {}).items():
            if tree_name not in new_file.get("trees", {}):
                file_diffs.append(f"  Tree missing: {tree_name}")
                continue

            summary["trees_compared"] += 1
            new_tree = new_file["trees"][tree_name]

            tree_diffs = compare_dict_recursive(
                ref_tree, new_tree, f"{tree_name}.", float_tolerance, n_sigma
            )
            file_diffs.extend(tree_diffs)

        for hist_name, ref_hist in ref_file.get("histograms", {}).items():
            if hist_name not in new_file.get("histograms", {}):
                file_diffs.append(f"  Histogram missing: {hist_name}")
                continue

            summary["histograms_compared"] += 1
            new_hist = new_file["histograms"][hist_name]

            hist_diffs = compare_dict_recursive(
                ref_hist, new_hist, f"{hist_name}.", float_tolerance, n_sigma
            )
            file_diffs.extend(hist_diffs)

            if "fit" in ref_hist:
                summary["fits_compared"] += 1

        if file_diffs:
            all_differences.append(f"\n{filename}:")
            all_differences.extend(file_diffs)
            summary["total_differences"] += len(file_diffs)

    return all_differences, summary


def main() -> int:
    """Compare physics metrics from two JSON files."""
    parser = argparse.ArgumentParser(
        description="Compare physics metrics from two JSON files"
    )
    parser.add_argument(
        "reference",
        help="Reference metrics JSON file",
    )
    parser.add_argument(
        "new",
        help="New metrics JSON file to compare",
    )
    parser.add_argument(
        "--float-tolerance",
        type=float,
        help="Relative tolerance for float comparisons (default: from config)",
    )
    parser.add_argument(
        "--n-sigma",
        type=float,
        help="Number of sigma for statistical comparisons (default: from config)",
    )
    parser.add_argument(
        "--fail-on-diff",
        action="store_true",
        help="Exit with code 1 if differences found",
    )
    parser.add_argument(
        "--config",
        help=(
            "Path to configuration file "
            "(default: metrics_config.yaml in script directory)"
        ),
    )

    args = parser.parse_args()

    # Load config and apply defaults
    config = load_config(args.config)
    float_tolerance = (
        args.float_tolerance
        if args.float_tolerance is not None
        else config["comparison"]["float_tolerance"]
    )
    n_sigma = (
        args.n_sigma if args.n_sigma is not None else config["comparison"]["n_sigma"]
    )

    try:
        ref_metrics = json.loads(Path(args.reference).read_text())
        new_metrics = json.loads(Path(args.new).read_text())
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        return 1
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON: {e}")
        return 1

    differences, summary = compare_metrics(
        ref_metrics, new_metrics, float_tolerance, n_sigma
    )

    print("=" * 80)
    print("Physics Metrics Comparison")
    print("=" * 80)
    print(f"\nReference: {args.reference}")
    print(f"New:       {args.new}")
    print(f"Float tolerance: {float_tolerance}")
    print(f"N-sigma:         {n_sigma}")
    print(f"\nReference timestamp: {ref_metrics.get('timestamp', 'unknown')}")
    print(f"New timestamp:       {new_metrics.get('timestamp', 'unknown')}")
    print("\n" + "-" * 80)
    print("Summary:")
    print(f"  Files compared:      {summary['files_compared']}")
    print(f"  Files missing:       {summary['files_missing']}")
    print(f"  Trees compared:      {summary['trees_compared']}")
    print(f"  Histograms compared: {summary['histograms_compared']}")
    print(f"  Fits compared:       {summary['fits_compared']}")
    print(f"\n  Total differences:   {summary['total_differences']}")

    if differences:
        print("\n" + "-" * 80)
        print("Differences found:")
        for diff in differences:
            print(diff)
        print("=" * 80)

        if args.fail_on_diff:
            return 1
    else:
        print("\nNo differences found")
        print("=" * 80)

    return 0


if __name__ == "__main__":
    sys.exit(main())
