# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

"""Read, merge and write the FileSummary record of FairShip output files.

A FileSummary is a JSON string stored as a ``TString`` under the key
``FileSummary``. A stage that reads other FairShip files merges their
summaries: ``PoT`` is summed, ``EnergyCut`` and ``prodSite`` are collected,
and each input's own summary is kept in ``inputFileSummaries``, in the order
of ``inputFiles``, so the whole processing chain of a file can be traced.
"""

import json
import os
from datetime import datetime
from typing import Any

import ROOT


def read_file_summary(path) -> dict[str, Any] | None:
    """Return the FileSummary of a ROOT file as a dict, or None.

    None means that the file has no FileSummary or cannot be opened; a
    warning says which. Environment variables in the path are expanded.
    """
    expanded = os.path.expandvars(str(path))
    try:
        with ROOT.TFile.Open(expanded, "READ") as source:
            if not any(key.GetName() == "FileSummary" for key in source.GetListOfKeys()):
                print(f"[WARNING] No FileSummary in {path}")
                return None
            return json.loads(str(source.Get("FileSummary")))
    except OSError:
        # PyROOT raises instead of returning a null file.
        print(f"[WARNING] Could not open {expanded} to read its FileSummary")
    except json.JSONDecodeError:
        print(f"[WARNING] FileSummary of {path} is not valid JSON")
    return None


def _flatten_unique(values):
    """Unique values in first-seen order, with lists (merged summaries) expanded."""
    unique = []
    for value in values:
        for item in value if isinstance(value, list) else [value]:
            if item not in unique:
                unique.append(item)
    return unique


def merge_file_summaries(input_files) -> dict[str, Any]:
    """Merge the FileSummary records of the input files of a stage.

    The result keeps the keys ``run_simScript.py`` has always written (``PoT``,
    ``EnergyCut``, ``prodSite``, ``inputFiles``, ``PoTperFile``, ``date``) and
    adds ``inputFileSummaries``: the summary of each input file, or None.
    ``PoTperFile`` and ``inputFileSummaries`` line up with ``inputFiles``. A
    missing key in an input summary is skipped, so summaries of other stages
    can be merged too. ``PoT`` describes the input files as a whole, also when
    only part of their entries is processed.
    """
    if isinstance(input_files, (str, os.PathLike)):
        input_files = [input_files]
    summaries = [read_file_summary(name) for name in input_files]
    found = [summary for summary in summaries if summary is not None]
    # One entry per input file, None where the file has no PoT.
    pot_per_file = [
        summary["PoT"] if summary is not None and isinstance(summary.get("PoT"), (int, float)) else None
        for summary in summaries
    ]
    return {
        "PoT": sum(pot for pot in pot_per_file if pot is not None),
        "EnergyCut": _flatten_unique(summary["EnergyCut"] for summary in found if "EnergyCut" in summary),
        "prodSite": _flatten_unique(summary["prodSite"] for summary in found if "prodSite" in summary),
        "inputFiles": [str(name) for name in input_files],
        "PoTperFile": pot_per_file,
        "date": datetime.today().strftime("%Y-%m-%d"),
        "inputFileSummaries": summaries,
    }


def write_file_summary(path, summary: dict[str, Any]) -> None:
    """Write (or replace) the FileSummary of an existing ROOT file."""
    with ROOT.TFile.Open(str(path), "UPDATE") as output:
        output.WriteObject(ROOT.TString(json.dumps(summary)), "FileSummary", "Overwrite")
