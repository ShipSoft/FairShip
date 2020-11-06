#!/usr/bin/python3
# Usage: python addHistos.py [arg]
# [arg] = #run, TOTAL, LOOP
from ROOT import TList, TFile, TH1F, TH2F
import os, sys, subprocess

hpptList = TList()
hpList = TList()
hptList = TList()
runs = ['2383','2388','2389','2390','2392','2395','2396']

def addHistoToList(fpath):
  global hpptList, hpList, hptList
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
  
def addRunToList(run):
  if os.path.exists("output/RUN_8000_"+str(run)):
    temp = subprocess.check_output("ls output/RUN_8000_"+str(run),shell=True).decode()
  else:
    print("Error: run folder output/RUN_8000_"+str(run)+"/ does not exist.")
    sys.exit()
  for f in temp.split("\n"):
    if f:
      fpath = "output/RUN_8000_"+str(run)+"/"+f
      addHistoToList(fpath)
  
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

def makeRunHisto(run):
  global hpptList, hpList, hptList
  addRunToList(run)
  if not os.path.exists("output/HistoRunSum"):
    os.mkdir("output/HistoRunSum")
  outFile = TFile.Open("output/HistoRunSum/histo-RUN_8000_"+str(run)+".root","RECREATE")
  mergeHistos()
  outFile.Close()
  hpptList.Delete()
  hpList.Delete()
  hptList.Delete()
  
def makeTotalHisto():
  global runs, hpptList, hpList, hptList
  for run in runs:
    addRunToList(run)
  outFile = TFile.Open("output/histo-intermediate-data.root","RECREATE")
  mergeHistos()
  outFile.Close()
  hpptList.Delete()
  hpList.Delete()
  hptList.Delete()
  
def error():
  print("Correct usage: python addHistos.py [arg]")
  print("[arg] = #run, TOTAL, LOOP")
  print("#run = 2383,2388,2389,2390,2392,2395,2396")
  print("TOTAL - Sum over all runs, creating a single histogram.")
  print("LOOP - Loop over all runs, creating individual histograms.")
  
if len(sys.argv) != 2:
  print("Error: number of arguments does not match.")
  error()
elif sys.argv[1] == "TOTAL":
  makeTotalHisto()
elif sys.argv[1] == "LOOP":
  for run in runs:
    makeRunHisto(run)
elif sys.argv[1] in runs:
  makeRunHisto(run)
else:
  print("Error: argument is not recognised.")
  error()
