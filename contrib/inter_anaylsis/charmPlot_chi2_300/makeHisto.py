#!/usr/bin/python3
# Usage: python3 makeHisto.py Y
from ROOT import TFile, TH2F, TH1F
import sys

# -----Import file-----
eosship = "root://eospublic.cern.ch/"
eospath = "/eos/experiment/ship/user/truf/muflux-sim/1GeV-inter/pythia8_Geant4_charm_0-19_1.0_mu/ntuple-ship.conical.MuonBack-TGeant4_dig_RT-Y.root"
Y = sys.argv[1]
f = TFile.Open(eosship+eospath.replace("Y",Y),"read")
t = f.Get("tmuflux")

# -----Create histograms-----
hppt = TH2F("hppt","Momentum distribution",300,0,300,40,0,4)
hp = TH1F("hp","Momentum distribution",300,0,300)
hpt = TH1F("hpt","Transverse momentum distribution",40,0,4)

# -----Fill histogram-----
for i,event in enumerate(t):
  if event.nTr > 0:
    noverbose = t.GetEvent(i)
    for j in range(event.nTr):
      if t.GoodTrack[j] == 111 and t.Chi2[j] < 0.9:
        Pz = t.Pz[j]
        Px = t.Px[j]
        Py = t.Py[j]
        Pt = (Px ** 2 + Py ** 2) ** 0.5
        P  = (Pt ** 2 + Pz ** 2) ** 0.5
        hppt.Fill(P,Pt)
        hp.Fill(P)
        hpt.Fill(Pt)
      
# -----Close imported file-----
hppt.SetDirectory(0)
hp.SetDirectory(0)
hpt.SetDirectory(0)
f.Close()

# -----Save histogram-----
# outFile = TFile.Open("output/histo-"+sys.argv[1]+".root","RECREATE")
outFile = TFile.Open("output.root","RECREATE")
hppt.Write()
hp.Write()
hpt.Write()
outFile.Close()
