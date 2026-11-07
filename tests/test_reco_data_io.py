# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

"""Reco particles and vertices written to and read back from ROOT files."""

from pathlib import Path

import pytest

DATA = Path(__file__).parent / "data"


def write_and_read(ROOT, tmp_path, branch, objects):
    """Write `objects` as one event of a vector branch and read them back."""
    path = str(tmp_path / f"{branch}.root")
    f = ROOT.TFile(path, "RECREATE")
    tree = ROOT.TTree("cbmsim", "")
    container = ROOT.std.vector(type(objects[0]).__cpp_name__)()
    tree.Branch(branch, container, 32000, -1)
    for obj in objects:
        container.push_back(obj)
    tree.Fill()
    tree.Write()
    f.Close()

    f = ROOT.TFile(path)
    tree = f.Get("cbmsim")
    tree.GetEntry(0)
    # Copies, so that they outlive the file
    read = [type(o)(o) for o in getattr(tree, branch)]
    f.Close()
    return read


def covariance(ROOT, values):
    cov = ROOT.std.array("double", len(values))()
    for i, value in enumerate(values):
        cov[i] = value
    return cov


def test_particle_with_three_daughters(root_with_shipdata, tmp_path):
    ROOT = root_with_shipdata
    daughters = ROOT.std.vector("int")([2, 5, 9])
    particle = ROOT.ShipParticle(
        9900015, 0, -1, -1, daughters, ROOT.TLorentzVector(1, 2, 30, 31), ROOT.TLorentzVector(0, 0, 6000, 0)
    )
    (read,) = write_and_read(ROOT, tmp_path, "Particles", [particle])
    assert read.GetNDaughters() == 3
    assert list(read.GetDaughters()) == [2, 5, 9]
    assert read.GetFirstDaughter() == 2
    assert read.GetLastDaughter() == 9
    with pytest.raises(Exception, match="out_of_range"):
        read.GetDaughter(3)


def test_two_daughter_constructor(root_with_shipdata):
    ROOT = root_with_shipdata
    particle = ROOT.ShipParticle(
        9900015, 0, -1, -1, 4, 6, ROOT.TLorentzVector(1, 2, 30, 31), ROOT.TLorentzVector(0, 0, 6000, 0)
    )
    assert particle.GetNDaughters() == 2
    assert (particle.GetDaughter(0), particle.GetDaughter(1)) == (4, 6)


def test_vertex_track_weights(root_with_shipdata, tmp_path):
    ROOT = root_with_shipdata
    cov = covariance(ROOT, [1, 0, 0, 1, 0, 4])
    vertex = ROOT.SHiP.RecoVertex(ROOT.TVector3(1, 2, 6000), cov, 3.5, 3.0)
    vertex.AddTrack(0, ROOT.TVector3(0, 0, 10), cov, 0.9)
    vertex.AddTrack(1, ROOT.TVector3(0, 0, 20), cov, 0.2)
    vertex.AddTrack(2, ROOT.TVector3(0, 0, 30), cov)
    (read,) = write_and_read(ROOT, tmp_path, "RecoVertices", [vertex])
    assert list(read.trackIds()) == [0, 1, 2]
    assert list(read.trackWeights()) == pytest.approx([0.9, 0.2, 1.0])
    assert read.chi2() == pytest.approx(3.5)


def test_old_class_versions_are_read(root_with_shipdata):
    """Two-daughter particles (v3) and unweighted vertices (v1) still read."""
    ROOT = root_with_shipdata
    f = ROOT.TFile(str(DATA / "reco_objects_v3.root"))
    tree = f.Get("cbmsim")
    tree.GetEntry(0)
    (particle,) = tree.Particles
    assert list(particle.GetDaughters()) == [3, 7]
    assert particle.GetNDaughters() == 2
    assert particle.Pz() == pytest.approx(30.0)
    (vertex,) = tree.RecoVertices
    assert list(vertex.trackIds()) == [3, 7]
    assert list(vertex.trackWeights()) == [1.0, 1.0]
    f.Close()
