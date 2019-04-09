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
parser.add_argument("-n", "--Nevents", dest="nevents", help="number of events", required=False)
parser.add_argument("-pg", "--ParticleGun", dest="PG", help="particle gun", required=False)
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
 if options.PG:
   myPgun = ROOT.FairBoxGenerator(13,1)
   myPgun.SetPRange(0.,10.)
   myPgun.SetPhiRange(0, 0)
   myPgun.SetXYZ(0.*u.cm, 0.*u.cm, -thickness)
   myPgun.SetThetaRange(0,0)
   primGen.AddGenerator(myPgun)
 else:
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

 run.CreateGeometryFile("geofile.root")
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
nev = int(options.nevents)
if not options.PG:
 f=ROOT.TFile.Open(fname)
 nev = f.cbmsim.GetEntries()
 f.Close()
#run()

def analyze():
 ut.bookHist(h,'PinPout','pin pout',105,-0.5,10.,105,-0.5,10.)
 f=ROOT.TFile(outFile)
 sTree = f.cbmsim
 for n in range(sTree.GetEntries()):
  rc = sTree.GetEvent(n)
  mu = sTree.MCTrack[0]
  Pout = -0.49
  for v in sTree.vetoPoint:
   if v.GetTrackID()==0:
    if v.LastPoint()[2]>119.9:
     Pout = v.LastMom().Mag()
  rc = h['PinPout'].Fill(mu.GetP(),Pout)
 ut.writeHists(h,'PinPout.root')
