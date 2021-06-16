#!/usr/bin/env python 
import ROOT,os,sys,getopt,time,shipRoot_conf
from argparse import ArgumentParser

import shipunit as u
from ShipGeoConfig import ConfigRegistry

mcEngine     = "TGeant4"
runnr        = 1

setup = {}
setup['Fig3'] = {'thickness': 0.1*u.cm, 'material':'lead','momentum': 2*u.GeV,'maxTheta':0.2}
setup['Fig4'] = {'thickness': 0.1*u.cm, 'material':'lead','momentum': 8*u.GeV,'maxTheta':0.04}
setup['Fig5'] = {'thickness': 0.1*u.cm, 'material':'lead','momentum': 14*u.GeV,'maxTheta':0.02}

setup['Fig6'] = {'thickness': 1.44*u.cm, 'material':'copper','momentum': 11.7*u.GeV,'maxTheta':0.045}
setup['Fig7'] = {'thickness': 1.44*u.cm, 'material':'copper','momentum': 7.3*u.GeV,'maxTheta':0.045}

parser = ArgumentParser()
parser.add_argument("-b", "--heartbeat",  dest="heartbeat", type=int,  help="progress report",            default=10000)
parser.add_argument("-n", "--nEvents",      dest="nEvents",     type=int,  help="number of events",        default=10000)
parser.add_argument("-s", "--setup",            dest="s",                    type=str,  help="setup to simulate", default='Fig3')
options = parser.parse_args()
s       = options.s
nev = options.nEvents
thickness       = setup[s]['thickness']
material         = setup[s]['material']
momentum = setup[s]['momentum']
maxTheta     = setup[s]['maxTheta']

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

target = ROOT.boxTarget()
target.SetTarget(material,thickness)
run.AddModule(target)

primGen = ROOT.FairPrimaryGenerator()
myPgun  = ROOT.FairBoxGenerator(13,1) # pdg id  and multiplicity
myPgun.SetPRange(momentum-0.01,momentum+0.01)
myPgun.SetPhiRange(0,0) # // Azimuth angle range [degree]
myPgun.SetThetaRange(0,0) # // Polar angle in lab system range [degree]
myPgun.SetXYZ(0.*u.cm, 0.*u.cm, -10.*u.cm - (thickness) )
ROOT.FairLogger.GetLogger().SetLogScreenLevel("WARNING") # otherwise stupid printout for each event

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

f=ROOT.TFile(outFile)
h={}
ut.bookHist(h,'theta','scattering angle '+str(momentum)+'GeV/c;{Theta}(rad)',5000,0,maxTheta)
ut.bookHist(h,'theta2D','scattering angle '+str(momentum)+'GeV/c;{Theta}(rad)',5000,-maxTheta,maxTheta)
sTree = f.cbmsim
for n in range(sTree.GetEntries()):
 rc = sTree.GetEvent(n)
 for aHit in sTree.vetoPoint:
   if not aHit.GetTrackID()==0: continue
   pt = ROOT.TMath.Sqrt(aHit.GetPx()**2+aHit.GetPy()**2)
   scat = ROOT.TMath.ATan2(pt,aHit.GetPz())
   rc = h['theta'].Fill(scat)
   scatX = ROOT.TMath.ATan2(aHit.GetPx(),aHit.GetPz())
   scatY = ROOT.TMath.ATan2(aHit.GetPy(),aHit.GetPz())
   rc = h['theta'].Fill(scat)
   rc = h['theta2D'].Fill(scatX)
   rc = h['theta2D'].Fill(scatY)
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
