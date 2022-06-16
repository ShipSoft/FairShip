#!/usr/bin/env python 
from __future__ import print_function
import ROOT,os,sys,time,shipRoot_conf
ROOT.gROOT.ProcessLine('#include "FairModule.h"')
time.sleep(20)

import shipunit as u
from ShipGeoConfig import ConfigRegistry

mcEngine     = "TGeant4"
runnr        = 1
nev          = 10# 000000

setup = {}
setup['10']  = {'thickness': 2*u.cm, 'material':'aluminium','momentum':  10*u.GeV}
setup['100'] = {'thickness': 2*u.cm, 'material':'aluminium','momentum': 100*u.GeV}
setup['200'] = {'thickness': 2*u.cm, 'material':'aluminium','momentum': 200*u.GeV}

# 8cm = 0.9X0


s = sys.argv[1]
thickness = setup[s]['thickness']
material = setup[s]['material']
momentum = setup[s]['momentum']

checkOverlap = True

outFile = "gconv"+s+".root"
theSeed      = int(10000 * time.time() % 10000000)
ecut      = 0.0
                 
# -------------------------------------------------------------------
ROOT.gRandom.SetSeed(theSeed)  # this should be propagated via ROOT to Pythia8 and Geant4VMC
shipRoot_conf.configure()      # load basic libraries, prepare atexit for python
ship_geo = ConfigRegistry.loadpy("$FAIRSHIP/geometry/geometry_config.py", Yheight = 10, tankDesign = 5, muShieldDesign = 7, nuTauTargetDesign=1)

# -----Timer--------------------------------------------------------
timer = ROOT.TStopwatch()
timer.Start()

# -----Create simulation run----------------------------------------
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

class Block(ROOT.pyFairModule):
 "block of material"
 def __init__(self): 
   ROOT.pyFairModule.__init__(self,self)
   self.sensPlane = None
 def ConstructGeometry(self):
    print("Construct Block")
    top=ROOT.gGeoManager.GetTopVolume()
    geoLoad=ROOT.FairGeoLoader.Instance()
    geoFace=geoLoad.getGeoInterface()
    media=geoFace.getMedia()
    geoBuild=geoLoad.getGeoBuilder()
    ShipMedium=media.getMedium(material)
    W = ROOT.gGeoManager.GetMedium(material)
    if not W: 
        rc = geoBuild.createMedium(ShipMedium)
        W = ROOT.gGeoManager.GetMedium(material)
    aBox = ROOT.gGeoManager.MakeBox("target", W, 100.*u.cm, 100.*u.cm, thickness)
    top.AddNode(aBox, 1, ROOT.TGeoTranslation(0, 0, 0 ))
    if self.sensPlane: self.sensPlane.AddSensitiveVolume(aBox)
 def InitParContainers():
    print("not implemented!")
 def makeSensitive(self,sensPlane):
    self.sensPlane = sensPlane

sensPlane = ROOT.exitHadronAbsorber()
sensPlane.SetEnergyCut(ecut*u.GeV) 
sensPlane.SetZposition(thickness+10*u.cm)
run.AddModule(sensPlane)
target = Block()
target.makeSensitive(sensPlane)
run.AddModule(target)

primGen = ROOT.FairPrimaryGenerator()
myPgun  = ROOT.FairBoxGenerator(22,1) # pdg id  and multiplicity
myPgun.SetPRange(momentum-0.01,momentum+0.01)
myPgun.SetPhiRange(0,0) # // Azimuth angle range [degree]
myPgun.SetThetaRange(0,0) # // Polar angle in lab system range [degree]
myPgun.SetXYZ(0.*u.cm, 0.*u.cm, -10.*u.cm - (thickness) )
primGen.AddGenerator(myPgun)
run.SetGenerator(primGen)
#
run.SetGenerator(primGen)
# -----Initialize simulation run------------------------------------
run.Init()
gMC = ROOT.TVirtualMC.GetMC()

fStack = gMC.GetStack()
fStack.SetMinPoints(1)
fStack.SetEnergyCut(-1.)

boostFactor = 100.
if boostFactor > 1:
 ROOT.gROOT.ProcessLine('#include "Geant4/G4ProcessTable.hh"')
 ROOT.gROOT.ProcessLine('#include "Geant4/G4AnnihiToMuPair.hh"')
 ROOT.gROOT.ProcessLine('#include "Geant4/G4GammaConversionToMuons.hh"')
 gProcessTable = ROOT.G4ProcessTable.GetProcessTable()
 procAnnihil = gProcessTable.FindProcess(ROOT.G4String('AnnihiToMuPair'),ROOT.G4String('e+'))
 procGMuPair = gProcessTable.FindProcess(ROOT.G4String('GammaToMuPair'),ROOT.G4String('gamma'))
 procGMuPair.SetCrossSecFactor(boostFactor)
 procAnnihil.SetCrossSecFactor(boostFactor)

# -----Start run----------------------------------------------------
run.Run(nev)

# -----Start Analysis---------------
ROOT.gROOT.ProcessLine('#include "Geant4/G4EmParameters.hh"')
emP = ROOT.G4EmParameters.Instance()
emP.Dump()

import rootUtils as ut 

f=ROOT.gROOT.GetListOfFiles()[0]
h={}
ut.bookHist(h,'muons','muon mult',10,-0.5,9.5)
ut.bookHist(h,'electrons','e mult',10,-0.5,9.5)
sTree = f.cbmsim
for n in range(sTree.GetEntries()):
 rc = sTree.GetEvent(n)
 nMu = 0
 nEl = 0
 for aHit in sTree.vetoPoint:
   if abs(sTree.MCTrack[aHit.GetTrackID()].GetPdgCode())==13: nMu+=1
   if abs(sTree.MCTrack[aHit.GetTrackID()].GetPdgCode())==11: nEl+=1
 rc = h['muons'].Fill(nMu)
 rc = h['electrons'].Fill(nEl)
h['muons'].Draw()

# -----Finish-------------------------------------------------------
timer.Stop()
rtime = timer.RealTime()
ctime = timer.CpuTime()
print(' ') 
print("Macro finished succesfully.") 
print("Output file is ",  outFile) 
print("Real time ",rtime, " s, CPU time ",ctime,"s")
