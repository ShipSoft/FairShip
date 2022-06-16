#!/usr/bin/env python 
from __future__ import print_function
import ROOT,os,sys,time,shipRoot_conf
ROOT.gROOT.ProcessLine('#include "FairModule.h"')
time.sleep(20)

import shipunit as u
from ShipGeoConfig import ConfigRegistry

mcEngine     = "TGeant4"
runnr        = 1
nev          = 10000000

setup = {}
setup['Fig3'] = {'thickness': 0.1*u.cm, 'material':'lead','momentum': 2*u.GeV,'maxTheta':0.2}
setup['Fig4'] = {'thickness': 0.1*u.cm, 'material':'lead','momentum': 8*u.GeV,'maxTheta':0.04}
setup['Fig5'] = {'thickness': 0.1*u.cm, 'material':'lead','momentum': 14*u.GeV,'maxTheta':0.02}

setup['Fig6'] = {'thickness': 1.44*u.cm, 'material':'copper','momentum': 11.7*u.GeV,'maxTheta':0.045}
setup['Fig7'] = {'thickness': 1.44*u.cm, 'material':'copper','momentum': 7.3*u.GeV,'maxTheta':0.045}

s = sys.argv[1]
thickness = setup[s]['thickness']
material = setup[s]['material']
momentum = setup[s]['momentum']
maxTheta = setup[s]['maxTheta']

checkOverlap = True
storeOnlyMuons = True

outFile = "msc"+s+".root"
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
if storeOnlyMuons: sensPlane.SetOnlyMuons()
sensPlane.SetZposition(thickness+10*u.cm)
run.AddModule(sensPlane)
target = Block()
run.AddModule(target)

primGen = ROOT.FairPrimaryGenerator()
myPgun  = ROOT.FairBoxGenerator(13,1) # pdg id  and multiplicity
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

# -----Start run----------------------------------------------------
run.Run(nev)

# -----Start Analysis---------------
ROOT.gROOT.ProcessLine('#include "Geant4/G4EmParameters.hh"')
emP = ROOT.G4EmParameters.Instance()
emP.Dump()

import rootUtils as ut 

f=ROOT.gROOT.GetListOfFiles()[0]
h={}
ut.bookHist(h,'theta','scattering angle '+str(momentum)+'GeV/c;{Theta}(rad)',500,0,maxTheta)
sTree = f.cbmsim
for n in range(sTree.GetEntries()):
 rc = sTree.GetEvent(n)
 for aHit in sTree.vetoPoint:
   if not aHit.GetTrackID()==0: continue
   pt = ROOT.TMath.Sqrt(aHit.GetPx()**2+aHit.GetPy()**2)
   scat = ROOT.TMath.ATan2(pt,aHit.GetPz())
   rc = h['theta'].Fill(scat)
ut.bookCanvas(h,key=s,title=s,nx=900,ny=600,cx=1,cy=1)
tc = h[s].cd(1)
tc.SetLogy(1)
h['theta_100']=h['theta'].Clone('theta_100')
h['theta_100']=h['theta'].Rebin(5)
h['theta_100'].Scale(1./h['theta_100'].GetMaximum())
h['theta_100'].Draw()
h[s].Print(s+'.png')
h[s].Print(s+'.root')

f.Write(h['theta'].GetName())
f.Write(h['theta_100'].GetName())

# -----Finish-------------------------------------------------------
timer.Stop()
rtime = timer.RealTime()
ctime = timer.CpuTime()
print(' ') 
print("Macro finished succesfully.") 
print("Output file is ",  outFile) 
print("Real time ",rtime, " s, CPU time ",ctime,"s")
