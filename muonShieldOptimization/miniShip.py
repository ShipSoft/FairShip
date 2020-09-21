#!/usr/bin/env python 
import ROOT,os,shipRoot_conf,geomGeant4
import shipunit as u

mcEngine     = "TGeant4"
simEngine    = "Pythia8"
runnr        = 1
nev          = 1000
checkOverlap = True
G4only       = False
storeOnlyMuons = False
skipNeutrinos  = False
FourDP = False
boostDiMuon    = 1.
boostFactor    = 1.

outputDir    = "."
work_dir  = "./"
ecut      = 0.0 # GeV                 

# example for primary interaction, nobias: python $FAIRSHIP/muonShieldOptimization/run_fixedTarget.py -n 10000 -e 10 -f -r 10
#                                                               10000 events, energy cut 10GeV, run nr 10, override existing output folder


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
  global runnr, nev, ecut, G4only, tauOnly, work_dir,Debug,boostDiMuon,\
         boostFactor,storeOnlyMuons,npot,skipNeutrinos,FourDP,setup,field
  logger.info("miniSHiP proton-on-taget simulator (C) Thomas Ruf, 2020")

  ap = argparse.ArgumentParser(
      description='Run SHiP "pot" simulation')
  ap.add_argument('-d', '--debug', action='store_true', dest='debug')
  ap.add_argument('-f', '--force', action='store_true', help="force overwriting output directory")
  ap.add_argument('-r', '--run-number', type=int, dest='runnr', default=runnr)
  ap.add_argument('-e', '--ecut', type=float, help="energy cut", dest='ecut', default=ecut)
  ap.add_argument('-n', '--num-events', type=int, help="number of events to generate", dest='nev', default=nev)
  ap.add_argument('-T', '--target',   type=float, help="target length", dest='targetLength', default=100.)
  ap.add_argument('-W', '--targetMaterial', help="target material", dest='targetMaterial', default="tungsten")
  ap.add_argument('-A', '--absorber', type=float, help="absorber length", dest='muShieldLength', default=150)
  ap.add_argument('-I', '--absorberMaterialI', help="inner absorber material", dest='absorberMaterialI', default="tungsten")
  ap.add_argument('-J', '--absorberMaterialO', help="outer absorber material", dest='absorberMaterialO', default="iron")
  ap.add_argument('-B', '--bfield',type=float, help="magnetic field", dest='field', default=0)
  ap.add_argument('-G', '--G4only', action='store_true', dest='G4only',     default=False, help="use Geant4 directly, no Pythia8")
  ap.add_argument('-P', '--PythiaDecay', action='store_true', dest='pythiaDecay', default=False,  help="use Pythia8 for decays")
  ap.add_argument('-b', '--boostDiMuon', type=float,   dest='boostDiMuon',  default=boostDiMuon, help="boost Di-muon branching ratios")
  ap.add_argument('-X', '--boostFactor', type=float,   dest='boostFactor',  default=boostFactor, help="boost Di-muon prod cross sections")
  ap.add_argument('-M', '--storeOnlyMuons',  action='store_true',  dest='storeOnlyMuons',  default=storeOnlyMuons, help="store only muons, ignore neutrinos")
  ap.add_argument('-N', '--skipNeutrinos',  action='store_true',  dest='skipNeutrinos',  default=False, help="skip neutrinos")
  ap.add_argument('-D', '--4darkPhoton',  action='store_true',  dest='FourDP',  default=False, help="enable ntuple production")
  ap.add_argument('-o','--output'    , type=str, help="output directory", dest='work_dir', default=None)
  ap.add_argument('-rs','--seed', type=int, help="random seed; default value is 0, see TRrandom::SetSeed documentation", dest='seed', default=0)
  args = ap.parse_args()
  if args.debug:
      logger.setLevel(logging.DEBUG)
  runnr        = args.runnr
  nev          = args.nev
  ecut         = args.ecut
  G4only       = args.G4only
  boostFactor  = args.boostFactor
  boostDiMuon  = args.boostDiMuon
  storeOnlyMuons = args.storeOnlyMuons
  skipNeutrinos  = args.skipNeutrinos
  FourDP         = args.FourDP
  field          = args.field
  setup = {'target':{'length':args.targetLength,'material':args.targetMaterial},
           'absorber':{'length':args.muShieldLength,'materialI':args.absorberMaterialI,'materialO':args.absorberMaterialO}}

  if G4only:
    args.pythiaDecay = False
  elif args.pythiaDecay:
    logger.info("use Pythia8 as primary decayer")
  Debug  = args.debug
  if args.work_dir is None:
     args.work_dir = get_work_dir(runnr)
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
ROOT.gRandom.SetSeed(args.seed)  # this should be propagated via ROOT to Pythia8 and Geant4VMC
shipRoot_conf.configure()      # load basic libraries, prepare atexit for python

txt = 'pythia8_Geant4_'
outFile = outputDir+'/'+txt+str(runnr)+'_'+str(ecut)+'_'+\
          setup['target']['material']+str(int(setup['target']['length']))+'_'+\
          setup['absorber']['materialI']+setup['absorber']['materialO']+str(int(setup['absorber']['length']))+'_B'+str(field)+'.root'
parFile = outputDir+'/ship.params.'+txt+str(runnr)+'_'+str(ecut)+'.root'

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
cave.SetGeometryFileName("caveWithAir.geo")
run.AddModule(cave)

targetAndAbsorber = ROOT.miniShip()
targetAndAbsorber.SetTarget(setup['target']['material'],setup['target']['length'])
targetAndAbsorber.SetAbsorber(setup['absorber']['materialI'],setup['absorber']['materialO'],setup['target']['length'],field)
targetAndAbsorber.SetEnergyCut(ecut*u.GeV)
if storeOnlyMuons: targetAndAbsorber.SetOnlyMuons()
if skipNeutrinos:  targetAndAbsorber.SkipNeutrinos()
run.AddModule(targetAndAbsorber)
print "target and absorber created"

# -----Create PrimaryGenerator--------------------------------------
primGen = ROOT.FairPrimaryGenerator()
P8gen = ROOT.FixedTargetGenerator()
P8gen.SetTarget("TargetArea_1",0.,0.) # will distribute PV inside target, beam offset x=y=0.
P8gen.SetCharmTarget()
P8gen.SetMom(20.*u.GeV)
P8gen.SetEnergyCut(ecut*u.GeV)
P8gen.SetDebug(Debug)
P8gen.SetHeartBeat(100000)
if G4only: P8gen.SetG4only()
if boostDiMuon > 1:
 P8gen.SetBoost(boostDiMuon) # will increase BR for rare eta,omega,rho ... mesons decaying to 2 muons in Pythia8
                            # and later copied to Geant4
P8gen.SetSeed(args.seed)
primGen.AddGenerator(P8gen)
#
run.SetGenerator(primGen)
# -----Initialize simulation run------------------------------------
run.Init()

geomGeant4.setMagnetField(flag='dump')
gMC = ROOT.TVirtualMC.GetMC()
fStack = gMC.GetStack()
fStack.SetMinPoints(1)
fStack.SetEnergyCut(-1.)
#
import AddDiMuonDecayChannelsToG4
AddDiMuonDecayChannelsToG4.Initialize(P8gen.GetPythia())

# boost gamma2muon conversion
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

# -----Finish-------------------------------------------------------
timer.Stop()
rtime = timer.RealTime()
ctime = timer.CpuTime()
print ' ' 
print "Macro finished succesfully." 
print "Output file is ",  outFile 
print "Real time ",rtime, " s, CPU time ",ctime,"s"
# ---post processing--- remove empty events --- save histograms
tmpFile = outFile+"tmp"
if ROOT.gROOT.GetListOfFiles().GetEntries()>0:
 fin   = ROOT.gROOT.GetListOfFiles()[0]
else:
 fin = ROOT.TFile.Open(outFile)
fHeader = fin.FileHeader
fHeader.SetRunId(runnr)
info = "POT = "+str(nev)

conditions = " with ecut="+str(ecut)
if boostDiMuon > 1: conditions+=" diMu"+str(boostDiMuon)
if boostFactor > 1: conditions+=" X"+str(boostFactor)

info += conditions
fHeader.SetTitle(info)
print "Data generated ", fHeader.GetTitle()

nt = fin.Get('4DP')
if nt:
 tf = ROOT.TFile('FourDP.root','recreate')
 tnt = nt.CloneTree(0)
 for i in range(nt.GetEntries()):
  rc = nt.GetEvent(i)
  rc = tnt.Fill(nt.id,nt.px,nt.py,nt.pz,nt.x,nt.y,nt.z)
 tnt.Write()
 tf.Close()

t     = fin.cbmsim
fout  = ROOT.TFile(tmpFile,'recreate' )
sTree = t.CloneTree(0)
nEvents = 0
for n in range(t.GetEntries()):
     rc = t.GetEvent(n)
     if t.vetoPoint.GetEntries()>0: 
          rc = sTree.Fill()
          nEvents+=1
     #t.Clear()
fout.cd()
for k in fin.GetListOfKeys():
 x = fin.Get(k.GetName())
 className = x.Class().GetName()
 if className.find('TTree')<0 and className.find('TNtuple')<0: 
   xcopy = x.Clone()
   rc = xcopy.Write()
sTree.AutoSave()
ff   = fin.FileHeader.Clone(fout.GetName())
fout.cd()
ff.Write("FileHeader", ROOT.TObject.kSingleKey)
sTree.Write()
fout.Close()

rc1 = os.system("rm  "+outFile)
rc2 = os.system("mv "+tmpFile+" "+outFile)
print "removed out file, moved tmpFile to out file",rc1,rc2
fin.SetWritable(False) # bpyass flush error

print "Number of events produced with activity after hadron absorber:",nEvents

if checkOverlap:
 sGeo = ROOT.gGeoManager
 sGeo.CheckOverlaps()
 sGeo.PrintOverlaps()
 run.CreateGeometryFile("%s/geofile_full.root" % (outputDir))

