# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

"""Write reco_objects_v3.root, reco objects in their old on-file versions.

The file holds one event with a two-daughter ShipParticle (class version 3,
before particles had any number of daughters) and a SHiP::RecoVertex (class
version 1, before track weights), so that the read rules in
shipdata/LinkDef.h can be tested. It has to be written with a libShipData of
those versions, e.g. a FairShip build at 26.10:

    python make_reco_objects_v3.py <old build>/lib/libShipData.so
"""

import sys

import ROOT

if ROOT.gSystem.Load(sys.argv[1]) < 0:
    sys.exit(f"cannot load {sys.argv[1]}")
assert ROOT.TClass.GetClass("ShipParticle").GetClassVersion() == 3
assert ROOT.TClass.GetClass("SHiP::RecoVertex").GetClassVersion() == 1

f = ROOT.TFile("reco_objects_v3.root", "RECREATE")
tree = ROOT.TTree("cbmsim", "reco objects of old class versions")
particles = ROOT.std.vector("ShipParticle")()
vertices = ROOT.std.vector("SHiP::RecoVertex")()
tree.Branch("Particles", particles, 32000, -1)
tree.Branch("RecoVertices", vertices, 32000, -1)

particles.push_back(
    ROOT.ShipParticle(
        9900015,
        0,
        -1,
        -1,
        3,
        7,
        ROOT.TLorentzVector(1.0, 2.0, 30.0, 31.0),
        ROOT.TLorentzVector(10.0, -5.0, 6000.0, 0.0),
    )
)
cov = ROOT.std.array("double", 6)()
for i, value in enumerate([1.0, 0.0, 0.0, 1.0, 0.0, 4.0]):
    cov[i] = value
vertex = ROOT.SHiP.RecoVertex(ROOT.TVector3(10.0, -5.0, 6000.0), cov, 0.5, 1.0)
vertex.AddTrack(3, ROOT.TVector3(0.5, 1.0, 15.0), cov)
vertex.AddTrack(7, ROOT.TVector3(0.5, 1.0, 15.0), cov)
vertices.push_back(vertex)

tree.Fill()
tree.Write()
f.Close()
