#!/usr/bin/python3
# Usage: python3 makeHisto.py XXXXX-Y
from ROOT import TFile, TH2F, TH1F
import sys

# -----Import file-----
eosship = "root://eospublic.cern.ch/"
eospath = "/eos/experiment/ship/user/truf/muflux-sim/1GeV-inter/pythia8_Geant4_1.0_cXXXXX_mu/ntuple-ship.conical.MuonBack-TGeant4_dig_RT-Y.root"
args = sys.argv[1].split("-")
XXXXX = args[0]
Y = args[1]
f = TFile.Open(eosship+eospath.replace("XXXXX",XXXXX).replace("Y",Y),"read")
t = f.Get("tmuflux")

# -----Create histograms-----
hppt = TH2F("hppt","Momentum distribution",300,0,300,40,0,4)     # -----------------
hp = TH1F("hp","Momentum distribution",300,0,300)                # MC inclusive
hpt = TH1F("hpt","Transverse momentum distribution",40,0,4)      # -----------------
hppt2 = TH2F("hppt2","Momentum distribution",300,0,300,40,0,4)   # -----------------
hp2 = TH1F("hp2","Momentum distribution",300,0,300)              # dimuon G4
hpt2 = TH1F("hpt2","Transverse momentum distribution",40,0,4)    # -----------------
hppt3 = TH2F("hppt3","Momentum distribution",300,0,300,40,0,4)   # -----------------
hp3 = TH1F("hp3","Momentum distribution",300,0,300)              # photon conversion
hpt3 = TH1F("hpt3","Transverse momentum distribution",40,0,4)    # -----------------
hppt4 = TH2F("hppt4","Momentum distribution",300,0,300,40,0,4)   # -----------------
hp4 = TH1F("hp4","Momentum distribution",300,0,300)              # e+ annihilation
hpt4 = TH1F("hpt4","Transverse momentum distribution",40,0,4)    # -----------------
hppt7 = TH2F("hppt7","Momentum distribution",300,0,300,40,0,4)   # -----------------
hp7 = TH1F("hp7","Momentum distribution",300,0,300)              # dimuon P8
hpt7 = TH1F("hpt7","Transverse momentum distribution",40,0,4)    # -----------------

# -----Fill histogram-----
for i,event in enumerate(t):
  if event.nTr > 0 and event.channel != 5:
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
        if event.channel == 2:
          hppt2.Fill(P,Pt)
          hp2.Fill(P)
          hpt2.Fill(Pt)
        if event.channel == 3:
          hppt3.Fill(P,Pt)
          hp3.Fill(P)
          hpt3.Fill(Pt)
        if event.channel == 4:
          hppt4.Fill(P,Pt)
          hp4.Fill(P)
          hpt4.Fill(Pt)
        if event.channel == 7:
          hppt7.Fill(P,Pt)
          hp7.Fill(P)
          hpt7.Fill(Pt)
      
# -----Close imported file-----
hppt.SetDirectory(0)
hp.SetDirectory(0)
hpt.SetDirectory(0)
hppt2.SetDirectory(0)
hp2.SetDirectory(0)
hpt2.SetDirectory(0)
hppt3.SetDirectory(0)
hp3.SetDirectory(0)
hpt3.SetDirectory(0)
hppt4.SetDirectory(0)
hp4.SetDirectory(0)
hpt4.SetDirectory(0)
hppt7.SetDirectory(0)
hp7.SetDirectory(0)
hpt7.SetDirectory(0)
f.Close()

# -----Save histogram-----
# outFile = TFile.Open("output/histo-"+sys.argv[1]+".root","RECREATE")
outFile = TFile.Open("output.root","RECREATE")
hppt.Write()
hp.Write()
hpt.Write()
hppt2.Write()
hp2.Write()
hpt2.Write()
hppt3.Write()
hp3.Write()
hpt3.Write()
hppt4.Write()
hp4.Write()
hpt4.Write()
hppt7.Write()
hp7.Write()
hpt7.Write()
outFile.Close()
