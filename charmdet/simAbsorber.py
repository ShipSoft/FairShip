#!/usr/bin/env python 
import ROOT,os,sys,getopt,time,shipRoot_conf
ROOT.gROOT.ProcessLine('#include "FairModule.h"')

import shipunit as u
from ShipGeoConfig import ConfigRegistry
PDG = ROOT.TDatabasePDG.Instance()

mcEngine     = "TGeant4"

setup = {}
# 
setup['muflux'] = {'thickness': 240*u.cm/2., 'material':'iron'}
s = 'muflux'
thickness = setup[s]['thickness']
material  = setup[s]['material']

import rootUtils as ut 
h={}

from argparse import ArgumentParser
parser = ArgumentParser()
parser.add_argument("-f", "--file", dest="fname", help="input file", required=True)
options = parser.parse_args()

fname = options.fname
outFile = fname.replace('.root','_sim.root')

def run():
# -------------------------------------------------------------------
 ROOT.gRandom.SetSeed(0)  # this should be propagated via ROOT to Pythia8 and Geant4VMC
 shipRoot_conf.configure()      # load basic libraries, prepare atexit for python
# -----Timer--------------------------------------------------------
 timer = ROOT.TStopwatch()
 timer.Start()
# -----Create simulation run----------------------------------------
 gFairBaseContFact = ROOT.FairBaseContFact() # required by change to FairBaseContFact to avoid TList::Clear errors
 run = ROOT.FairRunSim()
 run.SetName(mcEngine)  # Transport engine
 run.SetOutputFile(outFile)  # Output file
 run.SetUserConfig("g4Config.C") # user configuration file default g4Config.C
 rtdb = run.GetRuntimeDb() 
# -----Materials----------------------------------------------
 run.SetMaterials("media.geo")  
# -----Create geometry----------------------------------------------
 cave= ROOT.ShipCave("CAVE")
 cave.SetGeometryFileName("cave.geo")
 run.AddModule(cave)
#
 target = ROOT.simpleTarget()
 target.SetEnergyCut(0.) 
 target.SetParameters(material,thickness,0.)
 if storeOnlyMuons: target.SetFastMuon()
 run.AddModule(target)
#
 primGen = ROOT.FairPrimaryGenerator()
 mufluxSim = ROOT.ReProcessAbsorber()
 mufluxSim.Init(fname)
 mufluxSim.SetZposition(-thickness)
 primGen.AddGenerator(mufluxSim)
#
 run.SetGenerator(primGen)
# -----Initialize simulation run------------------------------------
 run.Init()
 gMC = ROOT.TVirtualMC.GetMC()

 fStack = gMC.GetStack()
 fStack.SetMinPoints(1)
 fStack.SetEnergyCut(-1.)

# -----Start run----------------------------------------------------
 print "run for ",nev,"events"
 run.Run(nev)

# -----Finish-------------------------------------------------------
 timer.Stop()
 rtime = timer.RealTime()
 ctime = timer.CpuTime()
 print ' ' 
 print "Macro finished succesfully." 
 print "Output file is ",  outFile 
 print "Real time ",rtime, " s, CPU time ",ctime,"s"

storeOnlyMuons = True
nev = 100
run()

