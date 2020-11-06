#!/usr/bin/python3
# Usage: python trackEventCount.py
from ROOT import TFile
import subprocess

eosship = "root://eospublic.cern.ch/"
eospath = "/eos/experiment/ship/user/truf/muflux-reco/RUN_8000_"
runs = ['2383','2388','2389','2390','2392','2395','2396'] # intermediate fields
trackEventCountInRun = {}
for run in runs:
  temp = subprocess.check_output("xrdfs "+eosship+" ls "+eospath+run,shell=True).decode()
  trackEventCount = 0
  for fname in temp.split("\n"):
    if fname.find("ntuple")!=-1 and fname.find("refit")!=-1:
      # -----Import file-----
      f = TFile.Open(eosship+fname,"read")
      t = f.Get("tmuflux")
      # -----Scan for good event-----
      for event in t:
        if event.nTr > 0:
          trackEventCount += 1
  trackEventCountInRun[run] = trackEventCount

print(trackEventCountInRun)

totalEventCount = 0
for run in runs:
  totalEventCount += trackEventCountInRun[run]

print(totalEventCount)
