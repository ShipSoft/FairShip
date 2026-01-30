# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration


import ROOT

nJob = 1
nMult = 1000  # 100000 # number of events / muon
muonIn = "/media/Data/HNL/muVetoDIS/muDISVetoCounter.root"

#
from array import array

PDG = ROOT.TDatabasePDG.Instance()
masssq = {}


def getMasssq(pid):
    apid = abs(int(pid))
    if apid not in masssq:
        masssq[apid] = PDG.GetParticle(apid).Mass() ** 2
    return masssq[apid]


# prepare muon input for FairShip/Geant4 processing
# incoming muon,      id:px:py:pz:x:y:z:ox:oy:oz:pythiaid:parentid:ecut:w

# just duplicate muon n times, rather stupid job

fout = ROOT.TFile("muonEm_" + str(nJob) + ".root", "recreate")
dTree = ROOT.TTree("pythia8-Geant4", "muons for EM studies")
iMuon = ROOT.TClonesArray("TVectorD")
iMuonBranch = dTree.Branch("InMuon", iMuon, 32000, -1)
dPart = ROOT.TClonesArray("TVectorD")
dPartBranch = dTree.Branch("Particles", dPart, 32000, -1)

# read file with muons hitting concrete wall
fin = ROOT.TFile(muonIn)  # id:px:py:pz:x:y:z:w
sTree = fin.muons

for k in range(sTree.GetEntries()):
    rc = sTree.GetEvent(k)
    # make n events / muon
    px, py, pz = sTree.px, sTree.py, sTree.pz
    x, y, z = sTree.x, sTree.y, sTree.z
    pid, w = sTree.id, sTree.w
    p = ROOT.TMath.Sqrt(px * px + py * py + pz * pz)
    E = ROOT.TMath.Sqrt(getMasssq(pid) + p * p)
    mu = array("d", [pid, px, py, pz, E, x, y, z, w])
    muPart = ROOT.TVectorD(9, mu)
    for n in range(nMult):
        dPart.Clear()
        iMuon.Clear()
        tca_vec = iMuon.ConstructedAt(0)
        tca_vec.ResizeTo(muPart)
        ROOT.std.swap(tca_vec, muPart)
        m = array("d", [pid, px, py, pz, E])
        part = ROOT.TVectorD(5, m)
        # copy to branch
        nPart = len(dPart)
        if dPart.GetSize() == nPart:
            dPart.Expand(nPart + 10)
        tca_vec = dPart.ConstructedAt(nPart)
        tca_vec.ResizeTo(part)
        ROOT.std.swap(tca_vec, part)
        dTree.Fill()
fout.cd()
dTree.Write()
print("created", sTree.GetEntries() * nMult, " events")
