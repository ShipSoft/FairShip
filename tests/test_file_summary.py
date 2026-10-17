# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

"""Merging of FileSummary records across processing stages."""

import json

import pytest

ROOT = pytest.importorskip("ROOT")

from file_summary import merge_file_summaries, read_file_summary, write_file_summary


def make_file(path, summary=None):
    """Write a ROOT file, with the given FileSummary if any."""
    with ROOT.TFile.Open(str(path), "RECREATE") as output:
        ROOT.TNamed("payload", "").Write()
        if summary is not None:
            output.WriteObject(ROOT.TString(json.dumps(summary)), "FileSummary")
    return str(path)


def test_merge_keeps_legacy_keys_and_input_summaries(tmp_path):
    fixed_target = {"PoT": 1000, "EnergyCut": 0.5, "prodSite": "cern"}
    # A run_simScript.py output stores EnergyCut and prodSite as lists.
    simulation = {"PoT": 500, "EnergyCut": [0.5, 1.0], "prodSite": ["cern"], "seed": 3}
    names = [
        make_file(tmp_path / "a.root", fixed_target),
        make_file(tmp_path / "b.root", simulation),
        make_file(tmp_path / "c.root"),
    ]
    merged = merge_file_summaries(names)
    assert merged["PoT"] == 1500
    assert merged["EnergyCut"] == [0.5, 1.0]
    assert merged["prodSite"] == ["cern"]
    assert merged["PoTperFile"] == [1000, 500, None]
    assert merged["inputFiles"] == names
    assert merged["inputFileSummaries"] == [fixed_target, simulation, None]


def test_pot_per_file_keeps_equal_values(tmp_path):
    names = [make_file(tmp_path / f"{i}.root", {"PoT": 100}) for i in range(2)]
    merged = merge_file_summaries(names)
    assert merged["PoTperFile"] == [100, 100]
    assert merged["PoT"] == 200


def test_merge_accepts_summaries_without_pot(tmp_path):
    stage = {"stage": "prepareEvents", "seed": 7}
    merged = merge_file_summaries(make_file(tmp_path / "prepared.root", stage))
    assert merged["PoT"] == 0
    assert merged["EnergyCut"] == []
    assert merged["inputFileSummaries"] == [stage]


def test_unreadable_input_warns(tmp_path, capsys):
    missing = str(tmp_path / "missing.root")
    assert read_file_summary(missing) is None
    assert "Could not open" in capsys.readouterr().out
    assert merge_file_summaries([missing])["inputFileSummaries"] == [None]


def test_write_replaces_summary(tmp_path):
    name = make_file(tmp_path / "out.root", {"PoT": 1})
    write_file_summary(name, {"PoT": 2})
    write_file_summary(name, {"PoT": 3})
    assert read_file_summary(name) == {"PoT": 3}
    with ROOT.TFile.Open(name) as source:
        assert [key.GetName() for key in source.GetListOfKeys()].count("FileSummary") == 1
