#!/usr/bin/env python 
import ROOT,os,sys,getopt,time
import shipunit as u
import shipRoot_conf
from ShipGeoConfig import ConfigRegistry

mcEngine     = "TGeant4"
simEngine    = "Pythia8"  # "Genie" # Ntuple
nEvents      = 100 
firstEvent   = 0
inclusive    = False  # True = all processes if False only ccbar -> HNL
deepCopy     = False  # False = copy only stable particles to stack, except for HNL events
eventDisplay = False
inputFile    = None
theSeed      = int(10000 * time.time() % 10000000)
dy           = 10.
inactivateMuonProcesses = False   # provisionally for making studies of various muon background sources
checking4overlaps = True

try:
        opts, args = getopt.getopt(sys.argv[1:], "D:FHPu:n:i:f:c:hqv:sl:A:Y:i",["Pythia6","Pythia8","Genie","Ntuple","MuonBack",\
                                   "Cosmics","nEvents=", "display", "seed=", "firstEvent="])
except getopt.GetoptError:
        # print help information and exit:
        print ' enter --Pythia8 to generate events with Pythia8 (signal/inclusive) or --Genie for reading and processing neutrino interactions \
                or --Pythia6 for muon nucleon scattering'  
        print '    --MuonBack to generate events from muon background file, --Cosmics for cosmic generator data'  
        sys.exit()
for o, a in opts:
        if o in ("-D","--display"):
            eventDisplay = True
        if o in ("--Pythia6"):
            simEngine = "Pythia6"
        if o in ("--Pythia8"):
            simEngine = "Pythia8"
        if o in ("--Genie"):
            simEngine = "Genie"
            if not inputFile:   inputFile = 'Genie-mu-_anti_nu_mu-gntp.113.gst.root'
        if o in ("--Ntuple"):
            simEngine = "Ntuple"
        if o in ("--MuonBack"):
            simEngine = "MuonBack"
        if o in ("--Cosmics"):
            simEngine = "Cosmics"
        if o in ("-n", "--nEvents="):
            nEvents = int(a)
        if o in ("-i", "--firstEvent="):
            firstEvent = int(a)
        if o in ("-s", "--seed="):
            theSeed = int(a)
        if o in ("-f"):
            inputFile = a
        if o in ("-A"):
            inclusive = True
        if o in ("-Y"): 
            dy = float(a)
        if o in ("-F"):
            deepCopy = True

print "FairShip setup for",simEngine,"to produce",nEvents,"events"
if (simEngine == "Ntuple" or simEngine == "MuonBack") and not inputFile :
  print 'input file required if simEngine = Ntuple or MuonBack'
ROOT.gRandom.SetSeed(theSeed)  # this should be propagated via ROOT to Pythia8 and Geant4VMC
shipRoot_conf.configure()      # load basic libraries, prepare atexit for python
# - muShieldDesign    = 2  # 1=passive 2=active (default)
# - targetOpt         = 5  # 0=solid   >0 sliced, 5 pieces of tungsten, 4 air slits (default)
# - strawDesign       = 4  # simplistic tracker design,  4=sophisticated straw tube design, horizontal wires (default)
# - HcalOption        = -1 # no hcal,  0=hcal after muon
ship_geo = ConfigRegistry.loadpy("$FAIRSHIP/geometry/geometry_config.py", HcalOption = 0, Yheight = dy )
# Output file name, add dy to be able to setup geometry with ambiguities.
tag = simEngine+"-"+mcEngine
if eventDisplay: tag = tag+'_D'
if dy: tag = str(dy)+'.'+tag 
outFile ="ship."+tag+".root"  

# rm older files !!! 
os.system("rm *."+tag+".root")
# Parameter file name
parFile="ship.params."+tag+".root"

# In general, the following parts need not be touched
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
# -----Create geometry----------------------------------------------
import shipDet_conf
modules = shipDet_conf.configure(run,ship_geo)
# -----Create PrimaryGenerator--------------------------------------
primGen = ROOT.FairPrimaryGenerator()

if simEngine == "Pythia8":
 primGen.SetTarget(ship_geo.target.z0, 0.) 
# -----Pythia8--------------------------------------
 P8gen = ROOT.HNLPythia8Generator()
 import pythia8_conf
 pythia8_conf.configure(P8gen,inclusive,deepCopy)
 primGen.AddGenerator(P8gen)
if simEngine == "Pythia6":
# set muon interaction close to decay volume
 primGen.SetTarget(ship_geo.target.z0+ship_geo.muShield.length, 0.) 
# -----Pythia6-------------------------
 P6gen = ROOT.tPythia6Generator()
 P6gen.SetMom(50.*u.GeV)
 P6gen.SetTarget("gamma/mu+","n0") # default "gamma/mu-","p+"
 primGen.AddGenerator(P6gen)
if simEngine == "Genie":
# Genie
 pointZero =  -ship_geo.decayVolume.length/2. - 1.*u.cm  # nu interaction in last 10% of interactionLength of mushield
 # pointZero =   0.  # for testing
 primGen.SetTarget(pointZero, 0.)
 Geniegen = ROOT.GenieGenerator()
 Geniegen.Init(inputFile,firstEvent) 
 primGen.AddGenerator(Geniegen)
 nEvents = min(nEvents,Geniegen.GetNevents())
 print 'Generate ',nEvents,' with Genie input'
#  add tungsten to PDG
 pdg = ROOT.TDatabasePDG.Instance()
 pdg.AddParticle('W','Ion', 1.71350e+02, True, 0., 74, 'XXX', 1000741840)
#
 run.SetPythiaDecayer('DecayConfigPy8.C')  # this does not work !! It insists of using DecayConfig.C 
 # this requires writing a C macro, would have been easier to do directly in python! 
 # for i in [431,421,411,-431,-421,-411]:
 # ROOT.gMC.SetUserDecay(i) # Force the decay to be done w/external decayer
if simEngine == "Ntuple":
# reading previously processed muon events, [-50m - 50m]
 primGen.SetTarget(50*u.m+ship_geo.target.z0, 0.)
 Ntuplegen = ROOT.NtupleGenerator()
 Ntuplegen.Init(inputFile,firstEvent)
 primGen.AddGenerator(Ntuplegen)
 nEvents = min(nEvents,Ntuplegen.GetNevents())
 print 'Process ',nEvents,' from input file'
#
if simEngine == "MuonBack":
# reading muon tracks from previous Pythia8/Geant4 simulation, [-50m - 50m]
 primGen.SetTarget(50*u.m+ship_geo.target.z0, 0.)
 MuonBackgen = ROOT.MuonBackGenerator()
 MuonBackgen.Init(inputFile,firstEvent)
 primGen.AddGenerator(MuonBackgen)
 nEvents = min(nEvents,MuonBackgen.GetNevents())
 print 'Process ',nEvents,' from input file'
#
if simEngine == "Cosmics":
 targetz = 0;
 primGen.SetTarget(targetz, 0.)
 Cosmicsgen = ROOT.CosmicsGenerator()
 Cosmicsgen.Init(targetz)
 primGen.AddGenerator(Cosmicsgen)
print 'Process ',nEvents,' Cosmic events'
#
run.SetGenerator(primGen)
# ------------------------------------------------------------------------

#---Store the visualiztion info of the tracks, this make the output file very large!!
#--- Use it only to display but not for production!
if eventDisplay: run.SetStoreTraj(ROOT.kTRUE)
else:            run.SetStoreTraj(ROOT.kFALSE)
# -----Initialize simulation run------------------------------------
run.Init()
fStack = ROOT.gMC.GetStack()
if not deepCopy : fStack.SetEnergyCut(100.*u.MeV)
if eventDisplay:
 # Set cuts for storing the trajectories, can only be done after initialization of run (?!)
  trajFilter = ROOT.FairTrajFilter.Instance()
  trajFilter.SetStepSizeCut(10*u.cm);  
  trajFilter.SetVertexCut(-20*u.m, -20*u.m,ship_geo.target.z0-1*u.m, 20*u.m, 20*u.m, 200.*u.m)
  trajFilter.SetMomentumCutP(0.1*u.GeV)
  trajFilter.SetEnergyCut(0., 400.*u.GeV)
  trajFilter.SetStorePrimaries(ROOT.kTRUE)
  trajFilter.SetStoreSecondaries(ROOT.kTRUE)
# manipulate G4 geometry to enable magnetic field in active shielding, VMC can't do it.
if ship_geo.muShieldDesign != 1:
 import geomGeant4
 geomGeant4.setMagnetField()
 geomGeant4.printWeightsandFields()
if inactivateMuonProcesses : 
 mygMC = ROOT.TGeant4.GetMC()
 mygMC.ProcessGeantCommand("/process/inactivate muPairProd")
 mygMC.ProcessGeantCommand("/process/inactivate muBrems")
 mygMC.ProcessGeantCommand("/process/inactivate muIoni")
 mygMC.ProcessGeantCommand("/particle/select mu+")
 mygMC.ProcessGeantCommand("/particle/process/dump")
 import G4processes
 gProcessTable = G4processes.G4ProcessTable.GetProcessTable()
 procmu = gProcessTable.FindProcess('muIoni','mu+')
 procmu.SetVerboseLevel(2)     
# -----Start run----------------------------------------------------
run.Run(nEvents)
# -----Runtime database---------------------------------------------
kParameterMerged = ROOT.kTRUE
parOut = ROOT.FairParRootFileIo(kParameterMerged)
parOut.open(parFile)
rtdb.setOutput(parOut)
rtdb.saveOutput()
rtdb.printParamContexts()
# ------------------------------------------------------------------------
run.CreateGeometryFile("geofile_full."+tag+".root") 
#
# checking for overlaps
if checking4overlaps:
 ROOT.gGeoManager.CheckOverlaps()
 ROOT.gGeoManager.PrintOverlaps()
# -----Finish-------------------------------------------------------
timer.Stop()
rtime = timer.RealTime()
ctime = timer.CpuTime()
print ' ' 
print "Macro finished succesfully." 
print "Output file is ",  outFile 
print "Parameter file is ",parFile
print "Real time ",rtime, " s, CPU time ",ctime,"s"

# ------------------------------------------------------------------------

def checkOverlapsWithGeant4():
 # after /run/initialize, but prints warning messages, problems with TGeo volume
 mygMC = ROOT.TGeant4.GetMC()
 mygMC.ProcessGeantCommand("/geometry/test/recursion_start 0")
 mygMC.ProcessGeantCommand("/geometry/test/recursion_depth 2")
 mygMC.ProcessGeantCommand("/geometry/test/run")

