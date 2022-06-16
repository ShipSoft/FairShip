#!/usr/bin/env python 
from __future__ import print_function
import ROOT,os,sys,time,shipRoot_conf
ROOT.gROOT.ProcessLine('#include "FairModule.h"')
time.sleep(20)

import shipunit as u
from ShipGeoConfig import ConfigRegistry

mcEngine     = "TGeant4"
runnr        = 1
nev          = 1000000

setup = {}
setup['TLV'] = {'thickness':  0.1*u.cm, 'material':'tungsten','min momentum': 400*u.GeV,'max momentum': 400*u.GeV}

s = 'TLV'
thickness = setup[s]['thickness']
material = setup[s]['material']
minmomentum = setup[s]['min momentum']
maxmomentum = setup[s]['max momentum']

checkOverlap = True

outFile = "TLV.root"
theSeed   = 0
ecut      = 0.0
                 
# -------------------------------------------------------------------
ROOT.gRandom.SetSeed(theSeed)  # this should be propagated via ROOT to Pythia8 and Geant4VMC
shipRoot_conf.configure()      # load basic libraries, prepare atexit for python
ship_geo = ConfigRegistry.loadpy("$FAIRSHIP/geometry/geometry_config.py", Yheight = 10, tankDesign = 5, muShieldDesign = 7, nuTauTargetDesign=1)

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


class Block(ROOT.pyFairModule):
 "block of material"
 def __init__(self): ROOT.pyFairModule.__init__(self,self)
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
 def InitParContainers():
    print("not implemented!")

sensPlane = ROOT.exitHadronAbsorber()
sensPlane.SetEnergyCut(ecut*u.GeV) 
sensPlane.SetZposition(thickness+10*u.cm)
run.AddModule(sensPlane)
target = Block()
run.AddModule(target)

primGen = ROOT.FairPrimaryGenerator()
myPgun  = ROOT.FairBoxGenerator(2212,1) # pdg id  and multiplicity
myPgun.SetPRange(minmomentum,maxmomentum)
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

# -----Start run----------------------------------------------------
run.Run(nev)

# -----Start Analysis---------------

import rootUtils as ut 

f=ROOT.TFile('TLV.root')
pdg = ROOT.TDatabasePDG.Instance()
h={}
sTree = f.cbmsim
ut.bookHist(h,'Ekin','Ekin of particles in sens plane',400000,0.,400)
ut.bookHist(h,'EkinLow','Ekin of particles in sens plane',1000,0.,0.001)
for n in range(sTree.GetEntries()):
 rc = sTree.GetEvent(n)
 for aHit in sTree.vetoPoint:
   oTrack = sTree.MCTrack[aHit.GetTrackID()]
   M = pdg.GetParticle(oTrack.GetPdgCode()).Mass()
   Ekin = ROOT.TMath.Sqrt( aHit.GetPx()**2+aHit.GetPy()**2+aHit.GetPz()**2 + M**2) - M
   rc = h['Ekin'].Fill(Ekin)
   rc = h['EkinLow'].Fill(Ekin)
ut.bookCanvas(h,key=s,title=s,nx=900,ny=600,cx=1,cy=1)
tc = h[s].cd(1)
tc.SetLogy(1)
h['Ekin'].Draw()

# tungsten dedex mev cm**2/g 1.145 * rho g/cm-3 19.3 * 0.1
#          interactionLength 191.9 / 19.3 = 9.94cm, 0.1/9.94 = 1%

# -----Finish-------------------------------------------------------
timer.Stop()
rtime = timer.RealTime()
ctime = timer.CpuTime()
print(' ') 
print("Macro finished succesfully.") 
print("Output file is ",  outFile) 
print("Real time ",rtime, " s, CPU time ",ctime,"s")
