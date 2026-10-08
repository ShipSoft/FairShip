# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

"""Round trip of the NewMuDIS post-processing on small hand-made files.

``post_process`` pairs each simulated event with the DIS interaction it was
generated from by walking the MuonDIS input in replay order, then copies the
incoming muon's hits upstream of the vertex into that event. These tests build
a MuonDIS input split over two files, with uneven DIS counts per material and
a muon without any interaction, plus a matching ``cbmsim`` output carrying the
``muDIS_*`` identity branches that ``NewMuDISGenerator`` writes. They check
that hits land on the right events, that a non-zero start entry is counted
across files, and that a mismatch stops the run without touching the output.
"""

from array import array

import pytest

ROOT = pytest.importorskip("ROOT")

# The test needs the compiled newMuonDIS dictionary (material labels) and the
# detector point classes; fail loudly rather than skip if they are missing.
if ROOT.gSystem.Load("libShipMuDIS") < 0:
    raise ImportError("libShipMuDIS could not be loaded; build FairShip and run the tests in its environment")

from MuDISGenerator_postProcessing import _MARKER, _POINT_BRANCHES, post_process

MATERIALS = [str(label) for label in ROOT.NewMuDISGenerator.GetMaterialNames()]
MUON_MASS = 0.10566

# Two input files: muons 0 and 1 in the first, muon 2 in the second.
# Muon 1 has no DIS interaction at all and must be skipped by the replay order.
FIRST_FILE = [
    {
        "hits": {"muon_UBTPoints": [3270.0], "muon_SBTPoints": [3500.0], "muon_SSTPoints": [8500.0]},
        "dis": {"HE": [4000.0, 4100.0]},
    },
    {"hits": {"muon_SBTPoints": [3300.0]}, "dis": {}},
]
SECOND_FILE = [
    {"hits": {"muon_SBTPoints": [3400.0], "muon_TDPoints": [9000.0]}, "dis": {"AIR": [8000.0]}},
]
# (muon entry across both files, material, DIS index), in replay order.
REPLAY_FROM_START = [(0, "HE", 0), (0, "HE", 1), (2, "AIR", 0)]
# A simulated hit already in every output event, which must be kept.
SIMULATED_Z = 9999.0


def make_point(class_name, z, track_id):
    point = getattr(ROOT, class_name)()
    point.SetXYZ(0.0, 0.0, z)
    point.SetTrackID(track_id)
    return point


def write_input(path, muons):
    """Write a MuonDIS tree with only the branches post_process reads."""
    output = ROOT.TFile.Open(str(path), "RECREATE")
    tree = ROOT.TTree("MuonDIS", "post-processing test input")
    hits = {branch: ROOT.std.vector[class_name]() for branch, class_name in _POINT_BRANCHES}
    for branch, vector in hits.items():
        tree.Branch(branch, vector)
    counts = {material: array("i", [0]) for material in MATERIALS}
    vertices = {material: ROOT.std.vector["double"]() for material in MATERIALS}
    for material in MATERIALS:
        tree.Branch(f"muon_nDISevt_{material}", counts[material], f"muon_nDISevt_{material}/I")
        tree.Branch(f"mudis_DISvz_{material}", vertices[material])
    for muon in muons:
        for branch, class_name in _POINT_BRANCHES:
            hits[branch].clear()
            for z in muon["hits"].get(branch, ()):
                hits[branch].push_back(make_point(class_name, z, track_id=1))
        for material in MATERIALS:
            dis_z = muon["dis"].get(material, ())
            counts[material][0] = len(dis_z)
            vertices[material].clear()
            for z in dis_z:
                vertices[material].push_back(z)
        tree.Fill()
    tree.Write()
    output.Close()


def write_output(path, identities):
    """Write a cbmsim tree as the simulation leaves it, one entry per identity."""
    output = ROOT.TFile.Open(str(path), "RECREATE")
    tree = ROOT.TTree("cbmsim", "post-processing test output")
    tracks = ROOT.std.vector["ShipMCTrack"]()
    tree.Branch("MCTrack", tracks)
    points = {class_name: ROOT.std.vector[class_name]() for _, class_name in _POINT_BRANCHES}
    for class_name, vector in points.items():
        tree.Branch(class_name, vector)
    muon_entry = array("i", [0])
    dis_index = array("i", [0])
    material = ROOT.TString()
    tree.Branch("muDIS_muEntry", muon_entry, "muDIS_muEntry/I")
    tree.Branch("muDIS_material", material)
    tree.Branch("muDIS_disIndex", dis_index, "muDIS_disIndex/I")
    for event, (entry, label, index) in enumerate(identities):
        tracks.clear()
        # Untracked incoming muon at MCTrack[0], as NewMuDISGenerator adds it.
        tracks.push_back(ROOT.ShipMCTrack(13, -1, 0.0, 0.0, 50.0, MUON_MASS, 0.0, 0.0, 3000.0, 0.0, 0, event, 0, 1.0))
        for vector in points.values():
            vector.clear()
        points["vetoPoint"].push_back(make_point("vetoPoint", SIMULATED_Z, track_id=1))
        muon_entry[0] = entry
        dis_index[0] = index
        material.Clear()
        material.Append(label)
        tree.Fill()
    tree.Write()
    output.Close()


def read_events(path):
    """Return, per output entry, the identity and the z and track ID of every point."""
    events = []
    with ROOT.TFile.Open(str(path), "READ") as source:
        tree = source.Get("cbmsim")
        for entry in range(tree.GetEntries()):
            tree.GetEntry(entry)
            event = {
                "identity": (int(tree.muDIS_muEntry), str(tree.muDIS_material), int(tree.muDIS_disIndex)),
                "event_id": tree.MCTrack[0].GetEventID(),
            }
            for _, class_name in _POINT_BRANCHES:
                event[class_name] = [
                    (point.GetZ(), point.GetTrackID(), point.GetEventID()) for point in getattr(tree, class_name)
                ]
            events.append(event)
        restored = bool(source.Get(_MARKER))
    return events, restored


@pytest.fixture
def inputs(tmp_path):
    first = tmp_path / "muondis_a.root"
    second = tmp_path / "muondis_b.root"
    write_input(first, FIRST_FILE)
    write_input(second, SECOND_FILE)
    return [str(first), str(second)]


def test_material_labels_used_by_the_test_exist():
    assert {"HE", "AIR"} <= set(MATERIALS)


def test_restores_hits_upstream_of_each_vertex(tmp_path, inputs):
    output = tmp_path / "sim.root"
    write_output(output, REPLAY_FROM_START)

    counts = post_process(output, inputs, start_event=0)

    # Both HE events get the UBT and SBT hits of muon 0 (z < 4000, 4100), not its
    # SST hit; the AIR event gets the SBT hit of muon 2 (z < 8000), not its TD hit.
    assert counts == {"UpstreamTaggerPoint": 2, "vetoPoint": 3, "strawtubesPoint": 0, "TimeDetPoint": 0}
    events, restored = read_events(output)
    assert restored
    assert [event["identity"] for event in events] == REPLAY_FROM_START
    expected_veto_z = [[SIMULATED_Z, 3500.0], [SIMULATED_Z, 3500.0], [SIMULATED_Z, 3400.0]]
    expected_ubt_z = [[3270.0], [3270.0], []]
    for event, veto_z, ubt_z in zip(events, expected_veto_z, expected_ubt_z):
        assert [z for z, _, _ in event["vetoPoint"]] == pytest.approx(veto_z)
        assert [z for z, _, _ in event["UpstreamTaggerPoint"]] == pytest.approx(ubt_z)
        assert event["strawtubesPoint"] == []
        assert event["TimeDetPoint"] == []
        # The simulated hit is untouched; restored hits point at MCTrack[0] of this event.
        assert event["vetoPoint"][0][1] == 1
        for _, track_id, event_id in event["vetoPoint"][1:] + event["UpstreamTaggerPoint"]:
            assert track_id == 0
            assert event_id == event["event_id"]


def test_start_entry_counts_across_input_files(tmp_path, inputs):
    output = tmp_path / "sim.root"
    # Starting at muon 1 skips muon 0; muon 1 has no DIS, so the first event is
    # muon 2, the first entry of the second file and entry 2 overall.
    write_output(output, [(2, "AIR", 0)])

    counts = post_process(output, inputs, start_event=1)

    assert counts["vetoPoint"] == 1
    events, _ = read_events(output)
    assert [z for z, _, _ in events[0]["vetoPoint"]] == pytest.approx([SIMULATED_Z, 3400.0])


@pytest.mark.parametrize(
    "identities",
    [
        [(0, "HE", 1), (0, "HE", 0), (2, "AIR", 0)],  # DIS order swapped within a muon
        [(0, "HE", 0), (0, "HE", 1), (1, "AIR", 0)],  # wrong muon entry
        [(0, "HE", 0), (0, "AIR", 1), (2, "AIR", 0)],  # wrong material
    ],
)
def test_mismatch_raises_and_leaves_output_unchanged(tmp_path, inputs, identities):
    output = tmp_path / "sim.root"
    write_output(output, identities)
    before = output.read_bytes()

    with pytest.raises(ValueError, match="replayed"):
        post_process(output, inputs, start_event=0)

    assert output.read_bytes() == before
    assert not list(tmp_path.glob(".sim.mudis-*.root"))


def test_more_output_events_than_interactions_raises(tmp_path, inputs):
    output = tmp_path / "sim.root"
    write_output(output, [*REPLAY_FROM_START, (2, "AIR", 1)])

    with pytest.raises(ValueError, match="No input DIS interaction"):
        post_process(output, inputs, start_event=0)

    events, restored = read_events(output)
    assert not restored
    assert len(events) == 4
