#!/usr/bin/env python 
import ROOT,os,sys,getopt,time,shipRoot_conf
import shipunit as u
from ShipGeoConfig import ConfigRegistry
time.sleep(20)

mcEngine     = "TGeant4"
simEngine    = "Pythia8"
runnr        = 1
nev          = 1000
checkOverlap = True
G4only       = False
storeOnlyMuons = False
withEvtGen     = True 
boostDiMuon    = 1.
boostFactor    = 1.
charm          = False
beauty         = False
charmInputFile = "root://eoslhcb.cern.ch//eos/ship/data/Charm/Cascade-parp16-MSTP82-1-MSEL4-76Mpot_1.root"
nStart = 0

outputDir    = "."
theSeed      = int(10000 * time.time() % 10000000)
work_dir  = "./"
ecut      = 0.5 # GeV   with 1 : ~1sec / event, with 2: 0.4sec / event, 10: 0.13sec
                 # pythia = geant4 conversion = 0.4/100 
dy           = 10.
dv           = 5 # 4=TP elliptical tank design, 5 = optimized conical rectangular design
ds           = 7 # 5=TP muon shield, 6=magnetized hadron, 7=short magnet design 
nud          = 1 # 0=TP, 1=new magnet option for short muon shield, 2= no magnet surrounding neutrino detector


#----------------------------- Yandex production ------------------------------
import shutil
import argparse
import logging
logging.info("")
logger = logging.getLogger(os.path.splitext(os.path.basename(os.sys.argv[0]))[0])
logger.setLevel(logging.INFO)


def get_work_dir(run_number,tag=None):
  import socket
  host = socket.gethostname()
  job_base_name = os.path.splitext(os.path.basename(os.sys.argv[0]))[0]
  if tag:  out_dir = "{host}_{base}_{runnr}_{comment}".format(host=host, base=job_base_name, runnr=run_number, comment=tag)
  else:    out_dir = "{host}_{base}_{runnr}".format(host=host, base=job_base_name, runnr=run_number)
  return out_dir


def init():
  global runnr, nev, ecut, G4only, tauOnly,JpsiMainly, work_dir,Debug,withEvtGen,boostDiMuon,boostFactor,charm,beauty,charmInputFile,nStart,storeOnlyMuons
  logger.info("SHiP proton-on-taget simulator (C) Thomas Ruf, 2017")

  ap = argparse.ArgumentParser(
      description='Run SHiP "pot" simulation')
  ap.add_argument('-d', '--debug', action='store_true', dest='debug')
  ap.add_argument('-f', '--force', action='store_true', help="force overwriting output directory")
  ap.add_argument('-r', '--run-number', type=int, dest='runnr', default=runnr)
  ap.add_argument('-e', '--ecut', type=float, help="energy cut", dest='ecut', default=ecut)
  ap.add_argument('-n', '--num-events', type=int, help="number of events to generate", dest='nev', default=nev)
  ap.add_argument('-G', '--G4only', action='store_true', dest='G4only',     default=False, help="use Geant4 directly, no Pythia8")
  ap.add_argument('-P', '--PythiaDecay', action='store_true', dest='pythiaDecay', default=False,  help="use Pythia8 for decays")
  ap.add_argument('-V', '--EvtGen',      action='store_true', dest='withEvtGen',  default=True,   help="use EvtGen for decays")
  ap.add_argument('-t', '--tau-only',     action='store_true', dest='tauOnly',     default=False)
  ap.add_argument('-J', '--Jpsi-mainly',  action='store_true', dest='JpsiMainly',  default=False)
  ap.add_argument('-b', '--boostDiMuon', type=float,   dest='boostDiMuon',  default=boostDiMuon, help="boost Di-muon branching ratios")
  ap.add_argument('-X', '--boostFactor', type=float,   dest='boostFactor',  default=boostFactor, help="boost Di-muon prod cross sections")
  ap.add_argument('-C', '--charm',      action='store_true',  dest='charm',  default=charm, help="generate charm decays")
  ap.add_argument('-B', '--beauty',     action='store_true',  dest='beauty', default=beauty, help="generate beauty decays")
  ap.add_argument('-I', '--inputFile',  action='store_true',  dest='charmInputFile',  default=charmInputFile, help="input file for charm/beauty decays")
  ap.add_argument('-s', '--nStart',  action='store_true',  dest='nStart',  default=nStart, help="first event of input file if any")
  ap.add_argument('-M', '--storeOnlyMuons',  action='store_true',  dest='storeOnlyMuons',  default=storeOnlyMuons, help="store only muons, ignore neutrinos")
  ap.add_argument('-o', '--output', type=str, help="output directory", dest='work_dir', default=None)
  args = ap.parse_args()
  if args.debug:
      logger.setLevel(logging.DEBUG)
  runnr        = args.runnr
  nev          = args.nev
  ecut         = args.ecut
  tauOnly      = args.tauOnly
  JpsiMainly   = args.JpsiMainly
  G4only       = args.G4only
  boostFactor  = args.boostFactor
  boostDiMuon  = args.boostDiMuon
  storeOnlyMuons = args.storeOnlyMuons
  charm  = args.charm
  beauty = args.beauty
  if charm and beauty: 
    logger.warn("charm and beauty decays are set! Beauty gets priority")
    charm = False
  charmInputFile = args.charmInputFile
  nStart = args.nStart
  Debug  = args.debug
  if args.pythiaDecay:
    withEvtGen = False
    logger.info("use Pythia8 as primary decayer")
  else:
    withEvtGen = True
    logger.info("use EvtGen as primary decayer") 
  if args.work_dir is None:
    if charm: args.work_dir = get_work_dir(runnr,"charm")
    if charm: args.work_dir = get_work_dir(runnr,"beauty")
    else: args.work_dir = get_work_dir(runnr)
  work_dir = args.work_dir
  logger.debug("work_dir: %s" % work_dir)
  logger.debug("command line arguments: %s", args)
  if os.path.exists(work_dir):
    logger.warn("output directory '%s' already exists." % work_dir)
    if args.force:
      logger.warn("...cleaning")
      for root, dirs, files in os.walk(work_dir):
        for f in files:
          os.unlink(os.path.join(root, f))
        for d in dirs:
          shutil.rmtree(os.path.join(root, d))
    else:
      logger.warn("...use '-f' option to overwrite it")
  else:
    os.makedirs(work_dir)
  return args

args = init()
os.chdir(work_dir)
# -------------------------------------------------------------------

ROOT.gRandom.SetSeed(theSeed)  # this should be propagated via ROOT to Pythia8 and Geant4VMC
shipRoot_conf.configure()      # load basic libraries, prepare atexit for python
ship_geo = ConfigRegistry.loadpy("$FAIRSHIP/geometry/geometry_config.py", Yheight = dy, tankDesign = dv, muShieldDesign = ds, nuTauTargetDesign=nud)

outFile = outputDir+'/pythia8_Geant4_'+str(runnr)+'_'+str(ecut)+'.root'
parFile = outputDir+'/ship.params.pythia8_Geant4_'+str(runnr)+'_'+str(ecut)+'.root'

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

TargetStation = ROOT.ShipTargetStation("TargetStation",ship_geo.target.length,ship_geo.hadronAbsorber.length,
                                                        ship_geo.target.z,ship_geo.hadronAbsorber.z,ship_geo.targetOpt,ship_geo.target.sl)
TargetStation.SetLayerPosMat(ship_geo.target.xy,ship_geo.target.L1,ship_geo.target.M1,ship_geo.target.L2,ship_geo.target.M2,\
  ship_geo.target.L3,ship_geo.target.M3,ship_geo.target.L4,ship_geo.target.M4,ship_geo.target.L5,ship_geo.target.M5,\
  ship_geo.target.L6,ship_geo.target.M6,ship_geo.target.L7,ship_geo.target.M7,ship_geo.target.L8,ship_geo.target.M8,\
  ship_geo.target.L9,ship_geo.target.M9,ship_geo.target.L10,ship_geo.target.M10,ship_geo.target.L11,ship_geo.target.M11,\
  ship_geo.target.L12,ship_geo.target.M12,ship_geo.target.L13,ship_geo.target.M13,ship_geo.target.L14,ship_geo.target.M14,\
  ship_geo.target.L15,ship_geo.target.M15,ship_geo.target.L16,ship_geo.target.M16,ship_geo.target.L17,ship_geo.target.M17)
run.AddModule(TargetStation)
MuonShield = ROOT.ShipMuonShield("MuonShield",ship_geo.muShieldDesign,"ShipMuonShield",ship_geo.muShield.z,ship_geo.muShield.dZ0,ship_geo.muShield.dZ1,\
               ship_geo.muShield.dZ2,ship_geo.muShield.dZ3,ship_geo.muShield.dZ4,ship_geo.muShield.dZ5,ship_geo.muShield.dZ6,\
               ship_geo.muShield.dZ7,ship_geo.muShield.dZ8,ship_geo.muShield.dXgap,ship_geo.muShield.LE,ship_geo.Yheight*4./10.,0.) 
MuonShield.SetSupports(False) # otherwise overlap with sensitive Plane 
run.AddModule(MuonShield) # needs to be added because of magn hadron shield.
sensPlane = ROOT.exitHadronAbsorber()
sensPlane.SetEnergyCut(ecut*u.GeV) 
if storeOnlyMuons: sensPlane.SetOnlyMuons()
# sensPlane.SetZposition(0.*u.cm) # if not using automatic positioning behind default magnetized hadron absorber
run.AddModule(sensPlane)

# -----Create PrimaryGenerator--------------------------------------
primGen = ROOT.FairPrimaryGenerator()
P8gen = ROOT.FixedTargetGenerator()
P8gen.SetTarget("/TargetArea_1",0.,0.) # will distribute PV inside target, beam offset x=y=0.
P8gen.SetMom(400.*u.GeV)
P8gen.SetEnergyCut(ecut*u.GeV)
if G4only: P8gen.SetG4only()
if withEvtGen: P8gen.WithEvtGen()
if boostDiMuon > 1:
 P8gen.SetBoost(boostDiMuon) # will increase BR for rare eta,omega,rho ... mesons decaying to 2 muons in Pythia8
                            # and later copied to Geant4
P8gen.SetSeed(theSeed)
# for charm/beauty
#        print ' for experts: p pot= number of protons on target per spill to normalize on'
#        print '            : c chicc= ccbar over mbias cross section'
charm = True
if charm or beauty:
 pot = 5.E13
 nStart = 0
 P8gen.InitForCharmOrBeauty("root://eoslhcb.cern.ch//eos/ship/data/Charm/Cascade-parp16-MSTP82-1-MSEL4-76Mpot_1.root",pot,nStart)
# P8gen.SetDebug(ROOT.kTRUE)
primGen.AddGenerator(P8gen)
#
run.SetGenerator(primGen)
# -----Initialize simulation run------------------------------------
run.Init()

gMC = ROOT.TVirtualMC.GetMC()
fStack = gMC.GetStack()
fStack.SetMinPoints(1)
fStack.SetEnergyCut(-1.)
#
import AddDiMuonDecayChannelsToG4
AddDiMuonDecayChannelsToG4.Initialize(P8gen.GetPythia())

# boost gamma2muon conversion
if boostFactor > 1:
 import G4processes
 gProcessTable = G4processes.G4ProcessTable.GetProcessTable()
 procAnnihil = gProcessTable.FindProcessA('AnnihiToMuPair','e+')
 procGMuPair = gProcessTable.FindProcess('GammaToMuPair','gamma')
 procGMuPair.SetCrossSecFactor(boostFactor)
 procAnnihil.SetCrossSecFactor(boostFactor)

# -----Start run----------------------------------------------------
run.Run(nev)

# -----Finish-------------------------------------------------------
timer.Stop()
rtime = timer.RealTime()
ctime = timer.CpuTime()
print ' ' 
print "Macro finished succesfully." 
print "Output file is ",  outFile 
print "Real time ",rtime, " s, CPU time ",ctime,"s"


# ---post processing--- remove empty events
tmpFile = outFile+"tmp"
fin   = ROOT.gROOT.GetListOfFiles()[0]
fHeader = fin.FileHeader
fHeader.SetRunId(runnr)
if charm or beauty:
 poteq = P8gen.GetPotForCharm()
 fHeader.SetTitle("POT equivalent = %7F.1"%(poteq))
else: 
 fHeader.SetTitle("POT = "+str(nev))
t     = fin.cbmsim
fout  = ROOT.TFile(tmpFile,'recreate' )
sTree = t.CloneTree(0)
nEvents = 0
for n in range(t.GetEntries()):
     rc = t.GetEvent(n)
     if t.MCTrack.GetEntries()>1: 
          rc = sTree.Fill()
          nEvents+=1
     #t.Clear()
sTree.AutoSave()
ff   = fin.FileHeader.Clone(fout.GetName())
fout.cd()
ff.Write("FileHeader", ROOT.TObject.kSingleKey)
fout.Write()
fout.Close()
os.system("mv "+tmpFile+" "+outFile)

print "Number of events produced with activity after hadron absorber:",nEvents

if checkOverlap:
 sGeo = ROOT.gGeoManager
 sGeo.CheckOverlaps()
 sGeo.PrintOverlaps()
 run.CreateGeometryFile("%s/geofile_full.root" % (outputDir))
 import saveBasicParameters
 saveBasicParameters.execute("%s/geofile_full.root" % (outputDir),ship_geo)

