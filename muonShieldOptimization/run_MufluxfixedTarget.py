#!/usr/bin/env python 
from __future__ import print_function
import ROOT,os,sys,time,shipRoot_conf
import shipunit as u
from ShipGeoConfig import ConfigRegistry

mcEngine     = "TGeant4"
simEngine    = "Pythia8"
runnr        = 1000
nev          = 500
checkOverlap = False
G4only       = False
storeOnlyMuons = False
withEvtGen     = True
boostDiMuon    = 1.
boostFactor    = 1.
charm          = False
beauty         = False
chicc = 1.7e-3
chibb = 1.6e-7
npot  = 5E13
nStart = 0

charmInputFile = "root://eoslhcb.cern.ch//eos/ship/data/Charm/Cascade-parp16-MSTP82-1-MSEL4-76Mpot_1.root"
nStart = 0

outputDir    = "."
theSeed      = int(10000 * time.time() % 10000000)
work_dir  = "./"
ecut      = 0.5 # GeV   with 1 : ~1sec / event, with 2: 0.4sec / event, 10: 0.13sec
                 
dy           = 10.
dv           = 5 # 4=TP elliptical tank design, 5 = optimized conical rectangular design
ds           = 7 # 5=TP muon shield, 6=magnetized hadron, 7=short magnet design 
nud          = 1 # 0=TP, 1=new magnet option for short muon shield, 2= no magnet surrounding neutrino detector

# example for primary interaction, nobias: python $FAIRSHIP/muonShieldOptimization/run_fixedTarget.py -n 10000 -e 10 -f -r 10
#                                                               10000 events, energy cut 10GeV, run nr 10, override existing output folder
# example for charm decays, python $FAIRSHIP/muonShieldOptimization/run_fixedTarget.py -C -M -n 10000 -e 10  -r 60 -b 50 -f
#                                                               10000 events, charm decays, energy cut 10GeV, run nr 60, override existing output folder
#                                                               increase di-muon BRs for resonances < 1.1GeV by a factor 50

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
  global runnr, nev, ecut, G4only, tauOnly,JpsiMainly, work_dir,Debug,withEvtGen,boostDiMuon,\
         boostFactor,charm,beauty,charmInputFile,nStart,storeOnlyMuons,chicc,chibb,npot, nStart
  logger.info("SHiP proton-on-taget simulator (C) Thomas Ruf, 2017")

  ap = argparse.ArgumentParser(
      description='Run SHiP "pot" simulation')
  ap.add_argument('-d', '--debug', action='store_true', dest='debug')
  ap.add_argument('-f', '--force', action='store_true', help="force overwriting output directory")
  ap.add_argument('-cs', '--CharmdetSetup', type=int, dest='CharmdetSetup',help="setting detector setup", default=0)
  ap.add_argument('-ct', '--CharmTarget', type=int, dest='CharmTarget',help="choosing target configuration for charm exposure", default=3)
  ap.add_argument('-r', '--run-number', type=int, dest='runnr', default=runnr)
  ap.add_argument('-e', '--ecut', type=float, help="energy cut", dest='ecut', default=ecut)
  ap.add_argument('-n', '--num-events', type=int, help="number of events to generate", dest='nev', default=nev)
  ap.add_argument('-G', '--G4only', action='store_true', dest='G4only',     default=False, help="use Geant4 directly, no Pythia8")
  ap.add_argument('-P', '--PythiaDecay', action='store_true', dest='pythiaDecay', default=False,  help="use Pythia8 for decays")
  ap.add_argument('-V', '--EvtGen',      action='store_true', dest='withEvtGen',  default=withEvtGen,   help="use EvtGen for decays")
  ap.add_argument('-t', '--tau-only',     action='store_true', dest='tauOnly',     default=False)
  ap.add_argument('-J', '--Jpsi-mainly',  action='store_true', dest='JpsiMainly',  default=False)
  ap.add_argument('-b', '--boostDiMuon', type=float,   dest='boostDiMuon',  default=boostDiMuon, help="boost Di-muon branching ratios")
  ap.add_argument('-X', '--boostFactor', type=float,   dest='boostFactor',  default=boostFactor, help="boost Di-muon prod cross sections")
  ap.add_argument('-C', '--charm',      action='store_true',  dest='charm',  default=charm, help="generate charm decays")
  ap.add_argument('-B', '--beauty',     action='store_true',  dest='beauty', default=beauty, help="generate beauty decays")
  ap.add_argument('-M', '--storeOnlyMuons',  action='store_true',  dest='storeOnlyMuons',  default=storeOnlyMuons, help="store only muons, ignore neutrinos")
# for charm production       
  ap.add_argument('-cc','--chicc',action='store_true',  dest='chicc',  default=chicc, help="ccbar over mbias cross section")
  ap.add_argument('-bb','--chibb',action='store_true',  dest='chibb',  default=chibb, help="bbbar over mbias cross section")
  ap.add_argument('-p','--pot',action='store_true',  dest='npot',  default=npot, help="number of protons on target per spill to normalize on")
  ap.add_argument('-S','--nStart',action='store_true',  dest='nStart',  default=nStart, help="first event of input file to start")
  ap.add_argument('-I', '--InputFile', type=str, dest='charmInputFile',  default=charmInputFile, help="input file for charm/beauty decays")
  ap.add_argument('-o','--output'    , type=str, help="output directory", dest='work_dir', default=None)
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
  if G4only:
    args.charm  = False
    args.beauty = False
    args.withEvtGen = False
    args.pythiaDecay = False
  elif args.pythiaDecay:
    withEvtGen = False
    args.withEvtGen = False
    logger.info("use Pythia8 as primary decayer")
  else:
    withEvtGen = True
    logger.info("use EvtGen as primary decayer")
  withEvtGen     = args.withEvtGen
  charm  = args.charm
  beauty = args.beauty
  if charm and beauty: 
    logger.warn("charm and beauty decays are set! Beauty gets priority")
    charm = False
  charmInputFile = args.charmInputFile
  nStart = int(args.nStart)
  Debug  = args.debug
  if args.work_dir is None:
    if charm: args.work_dir = get_work_dir(runnr,"charm")
    if beauty: args.work_dir = get_work_dir(runnr,"beauty")
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
#this is for the muon flux geometry
ship_geo = ConfigRegistry.loadpy("$FAIRSHIP/geometry/charm-geometry_config.py", Setup = args.CharmdetSetup, cTarget = args.CharmTarget)

txt = 'pythia8_Geant4_'
if withEvtGen: txt = 'pythia8_evtgen_Geant4_'
outFile = outputDir+'/'+txt+str(runnr)+'_'+str(ecut)+'.root'
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
import charmDet_conf as shipDet_conf
modules = shipDet_conf.configure(run,ship_geo)

# -----Create PrimaryGenerator--------------------------------------
primGen = ROOT.FairPrimaryGenerator()
P8gen = ROOT.FixedTargetGenerator()
if (ship_geo.MufluxSpectrometer.muflux==True):
 P8gen.SetTarget("/TargetArea_1",0.,0.) # will distribute PV inside target, beam offset x=y=0.
else:
 P8gen.SetCharmTarget() #looks for charm target instead of SHiP standard target
 P8gen.SetTarget("volTarget_1",0.,0.) # will distribute PV inside target, beam offset x=y=0.
 if ship_geo.Box.gausbeam:
  primGen.SetBeam(0.,0., 0.5, 0.5) #more central beam, for hits in downstream detectors    
  primGen.SmearGausVertexXY(True) #sigma = x
 else:
  primGen.SetBeam(0.,0., ship_geo.Box.TX-1., ship_geo.Box.TY-1.) #Uniform distribution in x/y on the target (0.5 cm of margin at both sides)
  primGen.SmearVertexXY(True)
P8gen.SetMom(400.*u.GeV)
P8gen.SetEnergyCut(ecut*u.GeV)
P8gen.SetDebug(Debug)
if G4only: P8gen.SetG4only()
if withEvtGen: P8gen.WithEvtGen()
if boostDiMuon > 1:
 P8gen.SetBoost(boostDiMuon) # will increase BR for rare eta,omega,rho ... mesons decaying to 2 muons in Pythia8
                            # and later copied to Geant4
P8gen.SetSeed(theSeed)
# for charm/beauty
#        print ' for experts: p pot= number of protons on target per spill to normalize on'
#        print '            : c chicc= ccbar over mbias cross section'
if charm or beauty:
 P8gen.InitForCharmOrBeauty("root://eoslhcb.cern.ch//eos/ship/data/Charm/Cascade-parp16-MSTP82-1-MSEL4-76Mpot_1.root",nev,npot,nStart)
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
print(' ') 
print("Macro finished succesfully.") 
print("Output file is ",  outFile) 
print("Real time ",rtime, " s, CPU time ",ctime,"s")

if (ship_geo.MufluxSpectrometer.muflux==True):
# ---post processing--- remove empty events --- save histograms
 tmpFile = outFile+"tmp"
 fin   = ROOT.gROOT.GetListOfFiles()[0]

 fHeader = fin.FileHeader
 fHeader.SetRunId(runnr)
 if charm or beauty:
 # normalization for charm
  poteq = P8gen.GetPotForCharm()
  fHeader.SetTitle("POT equivalent = %7.3G"%(poteq))
 else: 
  fHeader.SetTitle("POT = "+str(nev))
 print("Data generated ", fHeader.GetTitle())
 t     = fin.cbmsim
 fout  = ROOT.TFile(tmpFile,'recreate' )
 sTree = t.CloneTree(0)
 nEvents = 0
 for n in range(t.GetEntries()):
     rc = t.GetEvent(n)
     if (t.ScintillatorPoint.GetEntries()>0): 
          rc = sTree.Fill()
          nEvents+=1  
     #t.Clear()
 fout.cd()
 for x in fin.GetList():
  if not x.Class().GetName().find('TH')<0: 
    xcopy = x.Clone()
    rc = xcopy.Write()
 sTree.AutoSave()
 ff   = fin.FileHeader.Clone(fout.GetName())
 fout.cd()
 ff.Write("FileHeader", ROOT.TObject.kSingleKey)
 sTree.Write()
 fout.Close()
 os.system("mv "+tmpFile+" "+outFile)

 print("Number of events produced with activity after hadron absorber:",nEvents) 

else:
 print("No post processing done")

sGeo = ROOT.gGeoManager
run.CreateGeometryFile("%s/geofile_full.root" % (outputDir))

if checkOverlap:
 sGeo = ROOT.gGeoManager
 sGeo.CheckOverlaps()
 sGeo.PrintOverlaps()
 run.CreateGeometryFile("%s/geofile_full.root" % (outputDir))
 import saveBasicParameters
 saveBasicParameters.execute("%s/geofile_full.root" % (outputDir),ship_geo)

