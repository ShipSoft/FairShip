#!/usr/bin/env python 
from __future__ import print_function
import ROOT,os,sys,getopt,time
import shipunit as u
import shipRoot_conf
import ShipGeoConfig


inFile ="geant.root"  
outFile="ana.root"
# Parameter file name
parFile="params.root"
nEvents=2000
# In general, the following parts need not be touched
# ========================================================================

# -----Timer--------------------------------------------------------
timer=ROOT.TStopwatch()
timer.Start()
# ------------------------------------------------------------------------
shipRoot_conf.configure()
# -----Create analysis run------------------------------------------
run=ROOT.FairRunAna()
run.SetInputFile(inFile)    # Input file
run.SetOutputFile(outFile)  # Output file
# -----Calorimeter part --------------------------------------------
# Creates. exports and fills calorimeter structure
ecalFiller=ROOT.ecalStructureFiller("ecalFiller", 1, "ecal.geo")
ecalFiller.SetUseMCPoints(ROOT.kTRUE)
ecalFiller.StoreTrackInformation()
run.AddTask(ecalFiller)
# Simple analysis
ecalAna=ROOT.ecalAnalysisSimple("simpleAna",0)
run.AddTask(ecalAna)
# -----Runtime database---------------------------------------------
rtdb=run.GetRuntimeDb()
kParameterMerged = ROOT.kTRUE
parIo1=ROOT.FairParRootFileIo()
parIo1.open(parFile)
rtdb.setFirstInput(parIo1)
rtdb.setOutput(parIo1)
rtdb.saveOutput()   # for the moment, it blocks when using Genie, no idea why
rtdb.printParamContexts()
# -----Start run----------------------------------------------------
run.Init()
run.Run(0,nEvents)
# ------------------------------------------------------------------------
#run.CreateGeometryFile("geofile_full."+tag+".root")  
# -----Finish-------------------------------------------------------
timer.Stop()
rtime = timer.RealTime()
ctime = timer.CpuTime()
print(' ') 
print("Macro finished succesfully.") 
print("Output file is ",  outFile) 
print("Parameter file is ",parFile)
print("Real time ",rtime, " s, CPU time ",ctime,"s")

# ------------------------------------------------------------------------
