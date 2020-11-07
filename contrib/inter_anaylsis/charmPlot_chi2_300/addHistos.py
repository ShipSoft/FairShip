#!/usr/bin/python3
# Usage: python3 addHistos.py
from ROOT import TList, TFile, TH1F, TH2F
import os, sys, subprocess

hpptList = TList()
hpList = TList()
hptList = TList()

def mergeHistos():
  global hpptList, hpList, hptList
  hppt = TH2F("hppt","Momentum distribution",300,0,300,40,0,4)
  hp = TH1F("hp","Momentum distribution",300,0,300)
  hpt = TH1F("hpt","Transverse momentum distribution",40,0,4)
  hppt.Merge(hpptList)
  hp.Merge(hpList)
  hpt.Merge(hptList)
  hppt.Write()
  hp.Write()
  hpt.Write()
  
def makeTotalHisto():
  global hpptList, hpList, hptList
  outFile = TFile.Open("output/histo-intermediate-charm.root","RECREATE")
  mergeHistos()
  outFile.Close()
  hpptList.Delete()
  hpList.Delete()
  hptList.Delete()

TotalGoodEventCount = 0
for Y in range(5):
  fpath = "output/histo-Y.root".replace("Y",str(Y))
  fr = TFile.Open(fpath,"read")
  hppttemp = fr.Get("hppt")
  hppttemp.SetDirectory(0)
  hpptList.Add(hppttemp)
  hptemp = fr.Get("hp")
  hptemp.SetDirectory(0)
  hpList.Add(hptemp)
  hpttemp = fr.Get("hpt")
  hpttemp.SetDirectory(0)
  hptList.Add(hpttemp)
  fr.Close()

makeTotalHisto()
