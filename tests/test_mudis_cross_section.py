# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

"""Pairing of simulated events with DIS entries in the legacy ``--MuDIS`` cross-section branch.

``MuDISGenerator`` starts at ``--firstEvent`` and starts again from entry 0
after the last entry, so the cross section of output event ``i`` must come
from DIS entry ``(firstEvent + i) % n``.
"""

from array import array

import pytest

ROOT = pytest.importorskip("ROOT")

import rootUtils
from mudis_cross_section import add_cross_section

# One distinct cross section per DIS entry, so any offset shows up.
CROSS_SECTIONS = [1.0e-3 * (entry + 1) for entry in range(6)]


def write_dis(path):
    """Write a DIS tree whose InMuon[0][10] holds the cross section."""
    output = ROOT.TFile.Open(str(path), "RECREATE")
    tree = ROOT.TTree("DIS", "cross-section test input")
    muons = ROOT.TClonesArray("TVectorD")
    tree.Branch("InMuon", muons, 32000, -1)
    for cross_section in CROSS_SECTIONS:
        muons.Clear()
        values = [0.0] * 14
        values[10] = cross_section
        rootUtils.assignClonesArrayItem(muons, 0, ROOT.TVectorD(14, array("d", values)))
        tree.Fill()
    tree.Write()
    output.Close()


def write_output(path, n_events):
    """Write a cbmsim tree with one entry per simulated event."""
    output = ROOT.TFile.Open(str(path), "RECREATE")
    tree = ROOT.TTree("cbmsim", "cross-section test output")
    event = array("i", [0])
    tree.Branch("event", event, "event/I")
    for i in range(n_events):
        event[0] = i
        tree.Fill()
    tree.Write()
    output.Close()


def read_cross_sections(path):
    with ROOT.TFile.Open(str(path), "READ") as source:
        tree = source.Get("cbmsim")
        values = []
        for entry in range(tree.GetEntries()):
            tree.GetEntry(entry)
            assert tree.event == entry
            values.append(tree.CrossSection)
        return values


@pytest.mark.parametrize(
    ("first_event", "n_events"),
    [(0, 6), (0, 3), (2, 3), (4, 4), (5, 6)],
)
def test_cross_section_follows_generator_entry(tmp_path, first_event, n_events):
    dis_file = tmp_path / "muonDis.root"
    output_file = tmp_path / "sim.root"
    write_dis(dis_file)
    write_output(output_file, n_events)

    add_cross_section(str(output_file), str(dis_file), first_event)

    expected = [CROSS_SECTIONS[(first_event + i) % len(CROSS_SECTIONS)] for i in range(n_events)]
    assert read_cross_sections(output_file) == pytest.approx(expected, rel=1e-6)
