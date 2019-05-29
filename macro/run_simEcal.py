#!/usr/bin/env python
momentum = 1
import ROOT,os,sys,getopt,time
import shipunit as u
import shipRoot_conf
import ShipGeoConfig

mcEngine     = "TGeant3"
simEngine    = "Pythia8"  # "Genie" # Ntuple
nEvents      = 2000
inclusive    = False  # True = all processes if False only ccbar -> HNL
deepCopy     = False  # False = copy only stable particles to stack, except for HNL events
eventDisplay = False
inputFile    = None
theSeed      = int(10000 * time.time() % 10000000)

if momentum>5  : nEvents=1000
if momentum>20 : nEvents=500

print "FairShip setup for",simEngine,"to produce",nEvents,"events"
if simEngine == "Ntuple" and not inputFile :
  print 'input file required if simEngine = Ntuple'
if simEngine == "Pythia6" and not inputFile :
  print 'pythia6 requires inputfile'
ROOT.gRandom.SetSeed(theSeed)  # this should be propagated via ROOT to Pythia8 and Geant4VMC
shipRoot_conf.configure()
ship_geo = ShipGeoConfig.Config().loadpy("$FAIRSHIP/geometry/geometry_config.py")

# Output file name
outFile ="geant.root"

# rm older files !!! 
os.system("rm params.root")
# Parameter file name
parFile="params.root"

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
rtdb = run.GetRuntimeDb() 
# -----Create geometry----------------------------------------------
import shipDet_conf
shipDet_conf.configure(run)
# -----Create PrimaryGenerator--------------------------------------
primGen=ROOT.FairPrimaryGenerator()
boxGen=ROOT.FairBoxGenerator(22,1);
boxGen.SetPRange(momentum, momentum)
boxGen.SetPhiRange(0,0)
boxGen.SetThetaRange(0,0)
#boxGen.SetXYZ(0,0,-9900)
boxGen.SetXYZ(0,0,2400)
primGen.AddGenerator(boxGen)
run.SetGenerator(primGen)

# ------------------------------------------------------------------------

#---Store the visualiztion info of the tracks, this make the output file very large!!
#--- Use it only to display but not for production!
if eventDisplay: run.SetStoreTraj(ROOT.kTRUE)
else:            run.SetStoreTraj(ROOT.kFALSE)
# -----Initialize simulation run------------------------------------
run.Init()
fStack = ROOT.gMC.GetStack()
#fStack.SetEnergyCut(.3*u.MeV)
# ------------------------------------------------------------------------
if simEngine != "Genie" and simEngine != "Ntuple":  
# -----Runtime database---------------------------------------------
 kParameterMerged = ROOT.kTRUE
 parOut = ROOT.FairParRootFileIo(kParameterMerged)
 parOut.open(parFile)
 rtdb.setOutput(parOut)
 rtdb.saveOutput()   # for the moment, it blocks when using Genie, no idea why
 rtdb.printParamContexts()
# -----Start run----------------------------------------------------
run.Run(nEvents)
# ------------------------------------------------------------------------
run.CreateGeometryFile("geofile_full.root")  
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
