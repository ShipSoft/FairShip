#!/usr/bin/env python
import ROOT,os,sys,time,shipRoot_conf
import shipunit as u
from ShipGeoConfig import ConfigRegistry
from backports import tdirectory634


mcEngine     = "TGeant4"
simEngine    = "Pythia8"
checkOverlap = True
outputDir    = "."
dy           = 6.  # 10.
ds           = 8  # 9 # 5=TP muon shield, 6=magnetized hadron, 7=short magnet design, 9=optimised with T4 as constraint, 8=requires config file

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
    if tag:  out_dir = f"{host}_{job_base_name}_{run_number}_{tag}"
    else:    out_dir = f"{host}_{job_base_name}_{run_number}"
    return out_dir


logger.info("SHiP proton-on-taget simulator (C) Thomas Ruf, 2017")

ap = argparse.ArgumentParser(description='Run SHiP "pot" simulation')
ap.add_argument('-d', '--debug', action=argparse.BooleanOptionalAction, default=True)
ap.add_argument('-f', '--force', action=argparse.BooleanOptionalAction, default=True, help="force overwriting output directory")
ap.add_argument('-r', '--run-number', type=int, dest='runnr', default=1)
ap.add_argument('-e', '--ecut', type=float, help="energy cut", default=0.5)  # GeV   with 1 : ~1sec / event, with 2: 0.4sec / event, 10: 0.13sec
ap.add_argument('-n', '--num-events', type=int, help="number of events to generate", dest='nev', default=100)
ap.add_argument('-G', '--G4only', action=argparse.BooleanOptionalAction, default=False,
                help="Whether or not to use Geant4 directly, no Pythia8 (--no-G4only or --G4only). Default set to False.")
ap.add_argument('-P', '--pythiaDecay', action=argparse.BooleanOptionalAction, default=False,
                help="Whether or not to use Pythia8 for decays (--no-PythiaDecay or --PythiaDecay). Default set to False.")
# ap.add_argument('-V', '--EvtGen', action='store_true', dest='withEvtGen', default=withEvtGen, help="use EvtGen for decays")
ap.add_argument('-t', '--tau-only', action=argparse.BooleanOptionalAction, dest='tauOnly', default=False)
ap.add_argument('-J', '--Jpsi-mainly', action=argparse.BooleanOptionalAction, dest='JpsiMainly', default=False)
ap.add_argument('-b', '--boostDiMuon', type=float, default=1., help="boost Di-muon branching ratios")
ap.add_argument('-X', '--boostFactor', type=float, default=1., help="boost Di-muon prod cross sections")
ap.add_argument('-C', '--charm', action=argparse.BooleanOptionalAction, default=False, help="generate charm decays")
ap.add_argument('-B', '--beauty', action=argparse.BooleanOptionalAction, default=False, help="generate beauty decays")
ap.add_argument('-M', '--storeOnlyMuons', action=argparse.BooleanOptionalAction, default=False, help="store only muons, ignore neutrinos")
ap.add_argument('-N', '--skipNeutrinos', action=argparse.BooleanOptionalAction, default=False, help="skip neutrinos")
ap.add_argument('-D', '--4darkPhoton', action=argparse.BooleanOptionalAction, dest='FourDP', default=False, help="enable ntuple production")
# for charm production
ap.add_argument('-cc', '--chicc', default=1.7e-3, help="ccbar over mbias cross section")
ap.add_argument('-bb', '--chibb', default=1.6e-7, help="bbbar over mbias cross section")
ap.add_argument('-p', '--pot', default=5E13, help="number of protons on target per spill to normalize on")
ap.add_argument('-S', '--nStart', type=int, help="first event of input file to start", dest='nStart', default=0)
ap.add_argument('-I', '--InputFile', type=str, dest='charmInputFile', default=ROOT.gSystem.Getenv("EOSSHIP")+"/eos/experiment/ship/data/Charm/Cascade-parp16-MSTP82-1-MSEL4-76Mpot_1.root", help="input file for charm/beauty decays")
ap.add_argument('-o', '--output', type=str, help="output directory", dest='work_dir', default=None)
ap.add_argument('-rs', '--seed', type=int, help="random seed; default value is 0, see TRrandom::SetSeed documentation", default=0)
ap.add_argument('--DecayVolumeMedium', help='Set Decay Volume Medium. Choices are helium (default) or vacuums.', default='helium', choices=['helium', 'vacuums'])
ap.add_argument('--shieldName', help='Name of the shield in the database. New_HA_Design or warm_opt.', default='New_HA_Design', choices=['New_HA_Design', 'warm_opt'])
ap.add_argument('--AddMuonShield', help='Whether or not to add the muon shield. Default set to False.', default=False, action=argparse.BooleanOptionalAction)
ap.add_argument('--AddMuonShieldField', help='Whether or not to add the muon shield magnetic field. Default set to False.', default=False, action=argparse.BooleanOptionalAction)
ap.add_argument('--AddHadronAbsorberOnly', help='Whether to only add the hadron absorber part of the muon shield. Default set to False.', default=True, action=argparse.BooleanOptionalAction)

ap.add_argument('--z-offset', type=float, dest='z_offset', default=-84., help="z-offset for the FixedTargetGenerator [mm]")
ap.add_argument('--TARGET_YAML', dest='TARGET_YAML', help='File for target configuration', default=os.path.expandvars('$FAIRSHIP/geometry/target_config_Jun25.yaml'))

args = ap.parse_args()
if args.debug:
    logger.setLevel(logging.DEBUG)


if args.G4only:
    args.charm = False
    args.beauty = False
    withEvtGen = False
    args.pythiaDecay = False
elif args.pythiaDecay:
    withEvtGen = False
    logger.info("use Pythia8 as primary decayer")
else:
    withEvtGen = True
    logger.info("use EvtGen as primary decayer")
# withEvtGen = args.withEvtGen
if args.charm and args.beauty:
    logger.warning("charm and beauty decays are set! Beauty gets priority")
    args.charm = False
charmInputFile = args.charmInputFile

if args.work_dir is None:
    if args.charm: args.work_dir = get_work_dir(args.runnr, "charm")
    if args.beauty: args.work_dir = get_work_dir(args.runnr, "beauty")
    else: args.work_dir = get_work_dir(args.runnr)

logger.debug("work_dir: %s" % args.work_dir)
logger.debug("command line arguments: %s", args)
if os.path.exists(args.work_dir):
    logger.warning("output directory '%s' already exists." % args.work_dir)
    if args.force:
        logger.warning("...cleaning")
        for root, dirs, files in os.walk(args.work_dir):
            for f in files:
                os.unlink(os.path.join(root, f))
            for d in dirs:
                shutil.rmtree(os.path.join(root, d))
    else:
        logger.warning("...use '-f' option to overwrite it")
else:
    os.makedirs(args.work_dir)

os.chdir(args.work_dir)
# -------------------------------------------------------------------
ROOT.gRandom.SetSeed(args.seed)  # this should be propagated via ROOT to Pythia8 and Geant4VMC
shipRoot_conf.configure()      # load basic libraries, prepare atexit for python
ship_geo_kwargs = {'Yheight': dy,
                   'DecayVolumeMedium': args.DecayVolumeMedium, 'shieldName': args.shieldName,
                   'TARGET_YAML': args.TARGET_YAML
                   }
if args.AddMuonShield or args.AddHadronAbsorberOnly:
    ship_geo_kwargs['muShieldDesign'] = ds
ship_geo = ConfigRegistry.loadpy("$FAIRSHIP/geometry/geometry_config.py", **ship_geo_kwargs)

txt = 'pythia8_Geant4_'
if withEvtGen: txt = 'pythia8_evtgen_Geant4_'
outFile = f'{outputDir}/{txt}{args.runnr}_{args.ecut}.root'
parFile = f'{outputDir}/ship.params.{txt}{args.runnr}_{args.ecut}.root'

# -----Timer--------------------------------------------------------
timer = ROOT.TStopwatch()
timer.Start()

# -----Create simulation run----------------------------------------
run = ROOT.FairRunSim()
run.SetName(mcEngine)  # Transport engine
run.SetSink(ROOT.FairRootFileSink(outFile))  # Output file
run.SetUserConfig("g4Config.C") # user configuration file default g4Config.C
rtdb = run.GetRuntimeDb()

# -----Materials----------------------------------------------
run.SetMaterials("media.geo")
# -----Create geometry----------------------------------------------
cave= ROOT.ShipCave("CAVE")
cave.SetGeometryFileName("caveWithAir.geo")

run.AddModule(cave)

TargetStation = ROOT.ShipTargetStation(name="TargetStation",
                                       tl=ship_geo.target.length,
                                       tz=ship_geo.target.z,
                                       tV=ship_geo.targetVersion,
                                       nS=ship_geo.target.nS,
                                       HeT=ship_geo.target.HeT)
TargetStation.SetLayerPosMat(d=ship_geo.target.xy, L=ship_geo.target.slices_length, G=ship_geo.target.slices_gap, M=ship_geo.target.slices_material)
run.AddModule(TargetStation)


if args.AddMuonShield or args.AddHadronAbsorberOnly:
    n_magnets = 7
    n_params = 13
    if not args.AddMuonShieldField:
        for i in range(n_magnets):
            ship_geo.muShield.params[n_magnets + i * n_params + 12] = 0  # set B field to 0
    if args.AddHadronAbsorberOnly:
        for i in range(1, n_magnets):
            ship_geo.muShield.params[n_magnets + i * n_params] = 0  # set dXIn to 0

    MuonShield = ROOT.ShipMuonShield(in_params=list(ship_geo.muShield.params), z=ship_geo.muShield.z, WithConstShieldField=ship_geo.muShield.WithConstField,
                                     SC_key=ship_geo.SC_mag)
    # MuonShield.SetSupports(False) # otherwise overlap with sensitive Plane
    run.AddModule(MuonShield) # needs to be added because of magn hadron shield.
sensPlane = ROOT.exitHadronAbsorber()
sensPlane.SetEnergyCut(args.ecut*u.GeV)
if args.storeOnlyMuons: sensPlane.SetOnlyMuons()
if args.skipNeutrinos: sensPlane.SkipNeutrinos()
if args.FourDP: sensPlane.SetOpt4DP()  # in case a ntuple should be filled with pi0,etas,omega
# sensPlane.SetZposition(0.0001*u.cm)  # if not using automatic positioning behind default magnetized hadron absorber
run.AddModule(sensPlane)

# -----Create PrimaryGenerator--------------------------------------
primGen = ROOT.FairPrimaryGenerator()
P8gen = ROOT.FixedTargetGenerator()
P8gen.SetZoffset(args.z_offset*u.mm)
P8gen.SetTarget("/target_vacuum_box_1", 0., 0.)  # will distribute PV inside target, beam offset x=y=0.
P8gen.SetMom(400.*u.GeV)
P8gen.SetEnergyCut(args.ecut*u.GeV)
P8gen.SetDebug(args.debug)
P8gen.SetHeartBeat(100000)
if args.G4only: P8gen.SetG4only()
if args.JpsiMainly: P8gen.SetJpsiMainly()
if args.tauOnly:    P8gen.SetTauOnly()
if withEvtGen: P8gen.WithEvtGen()
if args.boostDiMuon > 1:
    P8gen.SetBoost(args.boostDiMuon)  # will increase BR for rare eta,omega,rho ... mesons decaying to 2 muons in Pythia8
                                 # and later copied to Geant4
P8gen.SetSeed(args.seed)
# for charm/beauty
#        print ' for experts: p pot= number of protons on target per spill to normalize on'
#        print '            : c chicc= ccbar over mbias cross section'
if args.charm or args.beauty:
    print("--- process heavy flavours ---")
    P8gen.InitForCharmOrBeauty(charmInputFile, args.nev, args.pot, args.nStart)
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
if args.boostFactor > 1:
    ROOT.gROOT.ProcessLine('#include "Geant4/G4ProcessTable.hh"')
    ROOT.gROOT.ProcessLine('#include "Geant4/G4AnnihiToMuPair.hh"')
    ROOT.gROOT.ProcessLine('#include "Geant4/G4GammaConversionToMuons.hh"')
    gProcessTable = ROOT.G4ProcessTable.GetProcessTable()
    procAnnihil = gProcessTable.FindProcess(ROOT.G4String('AnnihiToMuPair'), ROOT.G4String('e+'))
    procGMuPair = gProcessTable.FindProcess(ROOT.G4String('GammaToMuPair'), ROOT.G4String('gamma'))
    procGMuPair.SetCrossSecFactor(args.boostFactor)
    procAnnihil.SetCrossSecFactor(args.boostFactor)

# -----Start run----------------------------------------------------
run.Run(args.nev)

# -----Finish-------------------------------------------------------
timer.Stop()
rtime = timer.RealTime()
ctime = timer.CpuTime()
print(' ')
print("Macro finished successfully.")
print(f"Output file is {outFile}")
print(f"Real time {rtime} s, CPU time {ctime} s")
# ---post processing--- remove empty events --- save histograms
tmpFile = outFile + "tmp"
if ROOT.gROOT.GetListOfFiles().GetEntries() > 0:
    fin = ROOT.gROOT.GetListOfFiles()[0]
else:
    fin = ROOT.TFile.Open(outFile)
fHeader = fin["FileHeader"]
fHeader.SetRunId(args.runnr)
if args.charm or args.beauty:
    # normalization for charm
    poteq = P8gen.GetPotForCharm()
    info = "POT equivalent = %7.3G"%(poteq)
else:
    info = f"POT = {args.nev}"

conditions = " with ecut=" + str(args.ecut)
if args.JpsiMainly: conditions += " J"
if args.tauOnly:    conditions += " T"
if withEvtGen: conditions += " V"
if args.boostDiMuon > 1: conditions += " diMu" + str(args.boostDiMuon)
if args.boostFactor > 1: conditions += " X" + str(args.boostFactor)

info += conditions
fHeader.SetTitle(info)
print(f"Data generated {fHeader.GetTitle()}")

nt = fin.Get("4DP")
if nt:
    nt = fin["4DP"]
    tf = ROOT.TFile('FourDP.root','recreate')
    tnt = nt.CloneTree(0)
    for i in range(nt.GetEntries()):
        rc = nt.GetEvent(i)
        rc = tnt.Fill(nt.id, nt.px, nt.py, nt.pz, nt.x, nt.y, nt.z)
    tnt.Write()
    tf.Close()

t = fin["cbmsim"]
fout  = ROOT.TFile(tmpFile, 'recreate')
sTree = t.CloneTree(0)
nEvents = 0
for n in range(t.GetEntries()):
    rc = t.GetEvent(n)
    if t.vetoPoint.GetEntries() > 0:
        rc = sTree.Fill()
        nEvents += 1
    #t.Clear()
fout.cd()
for k in fin.GetListOfKeys():
    x = fin.Get(k.GetName())
    className = x.Class().GetName()
    if className.find('TTree') < 0 and className.find('TNtuple') < 0:
        xcopy = x.Clone()
        rc = xcopy.Write()
sTree.AutoSave()
ff = fin["FileHeader"].Clone(fout.GetName())
fout.cd()
ff.Write("FileHeader", ROOT.TObject.kSingleKey)
sTree.Write()
fout.Close()

rc1 = os.system("rm  " + outFile)
rc2 = os.system("mv " + tmpFile + " " + outFile)
print("removed out file, moved tmpFile to out file", rc1, rc2)
fin.SetWritable(False) # bpyass flush error

print(f"Number of events produced with activity after hadron absorber: {nEvents}")

if checkOverlap:
    sGeo = ROOT.gGeoManager
    sGeo.CheckOverlaps()
    sGeo.PrintOverlaps()
    run.CreateGeometryFile("%s/geofile_full.root" % (outputDir))
    import saveBasicParameters
    saveBasicParameters.execute("%s/geofile_full.root" % (outputDir), ship_geo)
