#!/usr/bin/env python 
import ROOT,os,sys,getopt,time
import shipunit as u
import shipRoot_conf
import ShipGeoConfig

mcEngine     = "TGeant4"
simEngine    = "Pythia8"  # "Genie" # Ntuple
nEvents      = 100
inclusive    = False  # True = all processes if False only ccbar -> HNL
deepCopy     = False  # False = copy only stable particles to stack, except for HNL events
eventDisplay = False
inputFile    = None
theSeed      = int(10000 * time.time() % 10000000)

try:
        opts, args = getopt.getopt(sys.argv[1:], "o:D:FHPu:n:f:c:hqv:sl:A",["Pythia6","Pythia8","Genie","Ntuple","nEvents=", "display", "seed="])
except getopt.GetoptError:
        # print help information and exit:
        print ' enter --Pythia8 to generate events with Pythia8 (signal/inclusive) or --Genie for reading and processing neutrino interactions \
                or --Pythia6 for muon nucleon scattering'  
        sys.exit()
for o, a in opts:
        if o in ("--display"):
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
        if o in ("-n", "--nEvents="):
            nEvents = int(a)
        if o in ("-s", "--seed="):
            theSeed = int(a)
        if o in ("-f"):
            inputFile = a
        if o in ("-A"):
            inclusive = True
        if o in ("-F"):
            deepCopy = True

print "FairShip setup for",simEngine,"to produce",nEvents,"events"
if simEngine == "Ntuple" and not inputFile :
  print 'input file required if simEngine = Ntuple'
ROOT.gRandom.SetSeed(theSeed)  # this should be propagated via ROOT to Pythia8 and Geant4VMC
shipRoot_conf.configure()
ship_geo = ShipGeoConfig.Config().loadpy("$FAIRSHIP/geometry/geometry_config.py")

# Output file name
tag = simEngine+"-"+mcEngine
if eventDisplay: tag = tag+'_D'
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
shipDet_conf.configure(run)
# -----Create PrimaryGenerator--------------------------------------
primGen = ROOT.FairPrimaryGenerator()

if simEngine == "Pythia8":
 primGen.SetTarget(ship_geo.target.z0, 0.) 
# -----Pythia8--------------------------------------
 P8gen = ROOT.Pythia8Generator()
 import pythia8_conf
 pythia8_conf.configure(P8gen,inclusive,deepCopy)
 primGen.AddGenerator(P8gen)
 if inclusive: 
  # check presence of HNL
  P8gen.GetPythiaInstance(9900014)
if simEngine == "Pythia6":
# set muon interaction close to decay volume
 primGen.SetTarget(ship_geo.target.z0+70*u.m, 0.) 
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
 Geniegen.Init(inputFile) 
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
 Ntuplegen.Init(inputFile) 
 primGen.AddGenerator(Ntuplegen)
 nEvents = min(nEvents,Ntuplegen.GetNevents())
 print 'Process ',nEvents,' from input file'
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
# -----Start run----------------------------------------------------
run.Run(nEvents)
# ------------------------------------------------------------------------
if simEngine != "Ntuple" and simEngine != "Genie":  
# -----Runtime database---------------------------------------------
 kParameterMerged = ROOT.kTRUE
 parOut = ROOT.FairParRootFileIo(kParameterMerged)
 parOut.open(parFile)
 rtdb.setOutput(parOut)
 rtdb.saveOutput()   # for the moment, it blocks when using Genie, no idea why
 rtdb.printParamContexts()
# ------------------------------------------------------------------------
run.CreateGeometryFile("geofile_full."+tag+".root")  
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
