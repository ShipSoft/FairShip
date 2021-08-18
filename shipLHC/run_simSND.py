#!/usr/bin/env python
import os
import sys
import getopt
import ROOT

import shipunit as u
import shipRoot_conf
import rootUtils as ut
from ShipGeoConfig import ConfigRegistry
from argparse import ArgumentParser

mcEngine     = "TGeant4"
simEngine    = "Pythia8"  # "Genie" # Ntuple
inactivateMuonProcesses  = False

MCTracksWithHitsOnly                  = False  # copy particles which produced a hit and their history
MCTracksWithEnergyCutOnly    = True # copy particles above a certain kin energy cut
MCTracksWithHitsOrEnergyCut = False # or of above, factor 2 file size increase compared to MCTracksWithEnergyCutOnly

parser = ArgumentParser()
group = parser.add_mutually_exclusive_group()

parser.add_argument("--Genie",   dest="genie",   help="Genie for reading and processing neutrino interactions", required=False, action="store_true")
parser.add_argument("--Ntuple",  dest="ntuple",  help="Use ntuple as input", required=False, action="store_true")
parser.add_argument("--MuonBack",dest="muonback",  help="Generate events from muon background file, --Cosmics=0 for cosmic generator data", required=False, action="store_true")
parser.add_argument("--Pythia8", dest="pythia8", help="Use Pythia8", required=False, action="store_true")
parser.add_argument("--PG",      dest="pg",      help="Use Particle Gun", required=False, action="store_true")
parser.add_argument("--pID",     dest="pID",     help="id of particle used by the gun (default=22)", required=False, default=22, type=int)
parser.add_argument("--Estart",  dest="Estart",  help="start of energy range of particle gun for muflux detector (default=10 GeV)", required=False, default=10, type=float)
parser.add_argument("--Eend",    dest="Eend",    help="end of energy range of particle gun for muflux detector (default=10 GeV)", required=False, default=10, type=float)
parser.add_argument("--EVx",    dest="EVx",    help="particle gun xpos", required=False, default=0, type=float)
parser.add_argument("--EVy",    dest="EVy",    help="particle gun ypos", required=False, default=0, type=float)
parser.add_argument("--EVz",    dest="EVz",    help="particle gun zpos", required=False, default=0, type=float)
parser.add_argument("--FollowMuon",dest="followMuon", help="Make muonshield active to follow muons", required=False, action="store_true")
parser.add_argument("--FastMuon",  dest="fastMuon",  help="Only transport muons for a fast muon only background estimate", required=False, action="store_true")
parser.add_argument('--eMin', type=float, help="energy cut", dest='ecut', default=-1.)
parser.add_argument("--Nuage",     dest="nuage",  help="Use Nuage, neutrino generator of OPERA", required=False, action="store_true")
parser.add_argument("--MuDIS",     dest="mudis",  help="Use muon deep inelastic scattering generator", required=False, action="store_true")
parser.add_argument("-n", "--nEvents",dest="nEvents",  help="Number of events to generate", required=False,  default=100, type=int)
parser.add_argument("-i", "--firstEvent",dest="firstEvent",  help="First event of input file to use", required=False,  default=0, type=int)
parser.add_argument("-s", "--seed",dest="theSeed",  help="Seed for random number. Only for experts, see TRrandom::SetSeed documentation", required=False,  default=0, type=int)
group.add_argument("-f",        dest="inputFile",       help="Input file if not default file", required=False, default=False)
parser.add_argument("-g",        dest="geofile",       help="geofile for muon shield geometry, for experts only", required=False, default=None)
parser.add_argument("-o", "--output",dest="outputDir",  help="Output directory", required=False,  default=".")
parser.add_argument("--boostFactor", dest="boostFactor",  help="boost mu brems", required=False, type=float,default=0)
parser.add_argument("--debug",   dest="debug",   help="debugging mode, check for overlaps", required=False, action="store_true")
parser.add_argument("-D", "--display", dest="eventDisplay", help="store trajectories", required=False, action="store_true")

options = parser.parse_args()

# user hook
userTask = False

class MyTask(ROOT.FairTask):
    "user task"

    def Exec(self,opt):
        ioman = ROOT.FairRootManager.Instance()
        MCTracks = ioman.GetObject("MCTrack")
        print('Hello',opt,MCTracks.GetEntries())
        fMC = ROOT.TVirtualMC.GetMC()
        if MCTracks.GetEntries()>100:  fMC.StopRun()

checking4overlaps = False
if options.debug: checking4overlaps = True

if options.pythia8:       simEngine = "Pythia8"
if options.pg:                 simEngine = "PG"
if options.genie:           simEngine = "Genie"
if options.ntuple:         simEngine = "Ntuple"
if options.muonback: simEngine = "MuonBack"
if options.nuage:          simEngine = "Nuage"
if options.mudis:          simEngine = "muonDIS"

if options.inputFile:
  if options.inputFile == "none": options.inputFile = None
  inputFile = options.inputFile
  defaultInputFile = False

if   simEngine == "Genie"  and defaultInputFile: 
   print('GENIE input file missing, exit')
   sys.exit()
if simEngine == "muonDIS" and defaultInputFile:
   print('input file required if simEngine = muonDIS. Example:')
   print("/eos/experiment/sndlhc/MonteCarlo/Pythia6/MuonDIS /muonDis_XXXX.root")
   print("  XXXX = run+cycle*100+k, k: 0 or 1000 for mu+ or mu-,  c: number of cycles: 10 events per incoming muon in each cycle, run: 1...10")
   print(" c = 0 - 2: mu->proton,  5 - 7:  mu->neutron")
   sys.exit()
if simEngine == "Nuage" and not inputFile:
   inputFile = 'Numucc.root'

if (simEngine == "Ntuple") and defaultInputFile :
  print('input file required if simEngine = Ntuple or MuonBack. Examples:')
  print ("crossing angle up:        /eos/experiment/sndlhc/MonteCarlo/FLUKA/muons_up/version1/unit30_Nm.root  (unit30_Pm.root)")
  print ("crossing angle down: /eos/experiment/sndlhc/MonteCarlo/FLUKA/muons_down/muons_VCdown_IR1-LHC.root")
  sys.exit()

print("SND@LHC setup for",simEngine,"to produce",options.nEvents,"events")

ROOT.gRandom.SetSeed(options.theSeed)  # this should be propagated via ROOT to Pythia8 and Geant4VMC
shipRoot_conf.configure(0)     # load basic libraries, prepare atexit for python

snd_geo = ConfigRegistry.loadpy("$FAIRSHIP/geometry/shipLHC_geom_config.py")

# Output file name, add dy to be able to setup geometry with ambiguities.
if simEngine == "PG": tag = simEngine + "_"+str(options.pID)+"-"+mcEngine
else: tag = simEngine+"-"+mcEngine

if not os.path.exists(options.outputDir):
  os.makedirs(options.outputDir)
if options.boostFactor>1:
   tag+='_boost'+str(options.boostFactor)
outFile = "%s/sndLHC.%s.root" % (options.outputDir, tag)

# rm older files !!! 
for x in os.listdir(options.outputDir):
  if not x.find(tag)<0: os.system("rm %s/%s" % (options.outputDir, x) )
# Parameter file name
parFile="%s/ship.params.%s.root" % (options.outputDir, tag)

# In general, the following parts need not be touched, except for user task
# ========================================================================

# -----Timer--------------------------------------------------------
timer = ROOT.TStopwatch()
timer.Start()
# ------------------------------------------------------------------------
# -----Create simulation run----------------------------------------
run = ROOT.FairRunSim()
run.SetName(mcEngine)  # Transport engine
run.SetOutputFile(outFile)  # Output file
run.SetUserConfig("g4Config.C") # user configuration file default g4Config.C 
rtdb = run.GetRuntimeDb() 
# add user task
if userTask:
  userTask   = MyTask()
  run.AddTask(userTask)

# -----Create geometry----------------------------------------------
import shipLHC_conf as sndDet_conf
modules = sndDet_conf.configure(run,snd_geo)

# -----Create PrimaryGenerator--------------------------------------
primGen = ROOT.FairPrimaryGenerator()

# -----Particle Gun-----------------------
if simEngine == "PG": 
  myPgun = ROOT.FairBoxGenerator(options.pID,1)
  myPgun.SetPRange(options.Estart,options.Eend)
  myPgun.SetPhiRange(0, 360) # // Azimuth angle range [degree]
  myPgun.SetXYZ(options.EVx*u.cm, options.EVy*u.cm, options.EVz*u.cm) 
  myPgun.SetThetaRange(0,0) # // Polar angle in lab system range [degree]
  primGen.AddGenerator(myPgun)
  ROOT.FairLogger.GetLogger().SetLogScreenLevel("WARNING") # otherwise stupid printout for each event
# -----muon DIS Background------------------------
if simEngine == "muonDIS":
   ut.checkFileExists(inputFile)
   primGen.SetTarget(0., 0.) 
   DISgen = ROOT.MuDISGenerator()
   mu_start, mu_end = (-3.7-2.0)*u.m , -0.3*u.m # tunnel wall -30cm in front of SND
   DISgen.SetPositions(0, mu_start, mu_end)
   if options.ecut > 0:  modules['Floor'].SetEmin(options.ecut)
   DISgen.Init(inputFile,options.firstEvent) 
   primGen.AddGenerator(DISgen)
   options.nEvents = min(options.nEvents,DISgen.GetNevents())
   inactivateMuonProcesses = True # avoid unwanted hadronic events of "incoming" muon flying backward
   print('MuDIS position info input=',mu_start, mu_end)
   print('Generate ',options.nEvents,' with DIS input', ' first event',options.firstEvent)

# -----neutrino interactions from nuage------------------------
if simEngine == "Nuage":
   primGen.SetTarget(0., 0.)
   Nuagegen = ROOT.NuageGenerator()
   Nuagegen.EnableExternalDecayer(1) #with 0 external decayer is disable, 1 is enabled
   Nuagegen.SetPositions(0., -snd_geo.EmulsionDet.zdim/2, snd_geo.EmulsionDet.zdim/2, -snd_geo.EmulsionDet.xdim/2, snd_geo.EmulsionDet.xdim/2, -snd_geo.EmulsionDet.ydim/2, snd_geo.EmulsionDet.ydim/2)
   ut.checkFileExists(inputFile)
   Nuagegen.Init(inputFile,options.firstEvent)
   primGen.AddGenerator(Nuagegen)
   options.nEvents = min(options.nEvents,Nuagegen.GetNevents())
   run.SetPythiaDecayer("DecayConfigNuAge.C")
   print('Generate ',options.nEvents,' with Nuage input', ' first event',options.firstEvent)

# -----neutrino interactions from GENIE------------------------
if simEngine=="Genie":
   ut.checkFileExists(inputFile)
   primGen.SetTarget(0., 0.) # do not interfere with GenieGenerator
   Geniegen = ROOT.GenieGenerator()
   Geniegen.Init(inputFile,options.firstEvent)
   Geniegen.SetPositions(snd_geo.EmulsionDet.zC+60*u.cm, snd_geo.EmulsionDet.zC-snd_geo.EmulsionDet.zdim/2,snd_geo.EmulsionDet.zC+snd_geo.EmulsionDet.zdim/2)
   Geniegen.SetDeltaE_Matching_FLUKAGenie(10.) #energy range for the search of a GENIE interaction with similar energy of FLUKA neutrino
   Geniegen.SetGenerationOption(2) # 0 standard, 1 FLUKA,2 Pythia
   primGen.AddGenerator(Geniegen)
   options.nEvents = min(options.nEvents,Geniegen.GetNevents())
   run.SetPythiaDecayer('DecayConfigPy8.C')
   print('Generate ',options.nEvents,' with Genie input for Ship@LHC', ' first event',options.firstEvent)

if simEngine == "Ntuple":
   ut.checkFileExists(inputFile)
   Ntuplegen = ROOT.NtupleGenerator_FLUKA()
   Ntuplegen.SetZ(snd_geo.Floor.z)
   Ntuplegen.Init(inputFile,options.firstEvent)
   primGen.AddGenerator(Ntuplegen)
   options.nEvents = min(options.nEvents,Ntuplegen.GetNevents())

if simEngine == "MuonBack":
# reading muon tracks from FLUKA
 fileType = ut.checkFileExists(inputFile)
 if fileType == 'tree':
 # 2018 background production 
  primGen.SetTarget(snd_geo.target.z0+70.845*u.m,0.)
 else:
  primGen.SetTarget(snd_geo.target.z0+50*u.m,0.)
 #
 MuonBackgen = ROOT.MuonBackGenerator()
 # MuonBackgen.FollowAllParticles() # will follow all particles after hadron absorber, not only muons
 MuonBackgen.Init(inputFile,options.firstEvent,options.phiRandom)
 if options.charm == 0: MuonBackgen.SetSmearBeam(5 * u.cm) # radius of ring, thickness 8mm
 elif DownScaleDiMuon: 
    if inputFile[0:4] == "/eos": test = os.environ["EOSSHIP"]+inputFile
    else: test = inputFile
    testf = ROOT.TFile.Open(test)
    if not testf.FileHeader.GetTitle().find('diMu100.0')<0:
        MuonBackgen.SetDownScaleDiMuon()   # avoid interference with boosted channels
        print("MuonBackgenerator: set downscale for dimuon on")
    testf.Close()
 if options.sameSeed: MuonBackgen.SetSameSeed(options.sameSeed)
 primGen.AddGenerator(MuonBackgen)
 options.nEvents = min(options.nEvents,MuonBackgen.GetNevents())
 MCTracksWithHitsOnly = True # otherwise, output file becomes too big
 print('Process ',options.nEvents,' from input file, with Phi random=',options.phiRandom, ' with MCTracksWithHitsOnly',MCTracksWithHitsOnly)
 
 # optional, boost gamma2muon conversion
 # ROOT.kShipMuonsCrossSectionFactor = 100. 

#
run.SetGenerator(primGen)
# ------------------------------------------------------------------------
if options.followMuon :  
    if 'Veto' in modules:
        options.fastMuon = True
        modules['Veto'].SetFollowMuon()
    if 'Floor' in modules:
        modules['Floor'].MakeSensitive()
        print('make floor sensitive')
if options.fastMuon :
     if 'Veto' in modules:       modules['Veto'].SetFastMuon()
     elif 'Floor' in modules: 
           modules['Floor'].SetFastMuon()
           print('only transport muons')
# ------------------------------------------------------------------------
#---Store the visualiztion info of the tracks, this make the output file very large!!
#--- Use it only to display but not for production!
if options.eventDisplay: run.SetStoreTraj(ROOT.kTRUE)
else:            run.SetStoreTraj(ROOT.kFALSE)



# -----Initialize simulation run------------------------------------
run.Init()
gMC = ROOT.TVirtualMC.GetMC()
fStack = gMC.GetStack()
if MCTracksWithHitsOnly:
 fStack.SetMinPoints(1)
 fStack.SetEnergyCut(-100.*u.MeV)
elif MCTracksWithEnergyCutOnly:
 fStack.SetMinPoints(-1)
 fStack.SetEnergyCut(100.*u.MeV)
elif MCTracksWithHitsOrEnergyCut: 
 fStack.SetMinPoints(1)
 fStack.SetEnergyCut(100.*u.MeV)
elif options.deepCopy: 
 fStack.SetMinPoints(0)
 fStack.SetEnergyCut(0.*u.MeV)

#
if options.boostFactor > 1:
 ROOT.gROOT.ProcessLine('#include "Geant4/G4ProcessTable.hh"')
 ROOT.gROOT.ProcessLine('#include "Geant4/G4MuBremsstrahlung.hh"')
 gProcessTable = ROOT.G4ProcessTable.GetProcessTable()
 procBrems        = gProcessTable.FindProcess(ROOT.G4String('muBrems'),ROOT.G4String('mu+'))
 procBrems.SetCrossSectionBiasingFactor(options.boostFactor)
#

if inactivateMuonProcesses :
 ROOT.gROOT.ProcessLine('#include "Geant4/G4ProcessTable.hh"')
 mygMC = ROOT.TGeant4.GetMC()
 mygMC.ProcessGeantCommand("/process/inactivate muPairProd")
 mygMC.ProcessGeantCommand("/process/inactivate muBrems")
 mygMC.ProcessGeantCommand("/process/inactivate muIoni")
 mygMC.ProcessGeantCommand("/process/inactivate muonNuclear")
 mygMC.ProcessGeantCommand("/particle/select mu+")
 mygMC.ProcessGeantCommand("/particle/process/dump")
 gProcessTable = ROOT.G4ProcessTable.GetProcessTable()
 procmu = gProcessTable.FindProcess(ROOT.G4String('muIoni'),ROOT.G4String('mu+'))
 procmu.SetVerboseLevel(2)

if options.debug:  ROOT.fair.Logger.SetConsoleSeverity("debug")
# -----Start run----------------------------------------------------
run.Run(options.nEvents)
# -----Runtime database---------------------------------------------
kParameterMerged = ROOT.kTRUE
parOut = ROOT.FairParRootFileIo(kParameterMerged)
parOut.open(parFile)
rtdb.setOutput(parOut)
rtdb.saveOutput()
rtdb.printParamContexts()
getattr(rtdb,"print")()
# ------------------------------------------------------------------------
geoFile = "%s/geofile_full.%s.root" % (options.outputDir, tag)
run.CreateGeometryFile(geoFile)
# save detector parameters dictionary in geofile
import saveBasicParameters
saveBasicParameters.execute(geoFile,snd_geo)

# checking for overlaps
if checking4overlaps:
 fGeo = ROOT.gGeoManager
 fGeo.SetNmeshPoints(10000)
 fGeo.CheckOverlaps(0.1)  # 1 micron takes 5minutes
 fGeo.PrintOverlaps()
 # check subsystems in more detail
 for x in fGeo.GetTopNode().GetNodes(): 
   x.CheckOverlaps(0.0001)
   fGeo.PrintOverlaps()
# -----Finish-------------------------------------------------------
timer.Stop()
rtime = timer.RealTime()
ctime = timer.CpuTime()
print(' ') 
print("Macro finished succesfully.") 

print("Output file is ",  outFile) 
print("Geometry file is ",geoFile)
print("Real time ",rtime, " s, CPU time ",ctime,"s")

# ------------------------------------------------------------------------
def checkOverlapsWithGeant4():
 # after /run/initialize, but prints warning messages, problems with TGeo volume
 mygMC = ROOT.TGeant4.GetMC()
 mygMC.ProcessGeantCommand("/geometry/test/recursion_start 0")
 mygMC.ProcessGeantCommand("/geometry/test/recursion_depth 2")
 mygMC.ProcessGeantCommand("/geometry/test/run")
