#!/usr/bin/env python
# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

import json
import os

import geometry_config
import ROOT
import shipRoot_conf
import shipunit as u
from heavyFlavourScaling import (
    check_run_type_override,
    derive_cross_sections,
    format_summary,
)

mcEngine = "TGeant4"
simEngine = "Pythia8"
checkOverlap = True
outputDir = "."
dy = 6.0  # 10.
ds = 8  # 9 # 5=TP muon shield, 6=magnetized hadron, 7=short magnet design, 9=optimised with T4 as constraint, 8=requires config file

# example for primary interaction, nobias: python $FAIRSHIP/muonShieldOptimization/run_fixedTarget.py -n 10000 -e 10 -f -r 10
#                                                               10000 events, energy cut 10GeV, run nr 10, override existing output folder
# example for charm decays, python $FAIRSHIP/muonShieldOptimization/run_fixedTarget.py -C -M -n 10000 -e 10  -r 60 -b 50 -f
#                                                               10000 events, charm decays, energy cut 10GeV, run nr 60, override existing output folder
#                                                               increase di-muon BRs for resonances < 1.1GeV by a factor 50

# ----------------------------- Yandex production ------------------------------
import argparse
import logging
import shutil

logging.info("")
logger = logging.getLogger(os.path.splitext(os.path.basename(os.sys.argv[0]))[0])
logger.setLevel(logging.INFO)


def get_work_dir(run_number, tag: str | None = None) -> str:
    import socket

    host = socket.gethostname()
    job_base_name = os.path.splitext(os.path.basename(os.sys.argv[0]))[0]
    if tag:
        out_dir = f"{host}_{job_base_name}_{run_number}_{tag}"
    else:
        out_dir = f"{host}_{job_base_name}_{run_number}"
    return out_dir


logger.info("SHiP proton-on-taget simulator (C) Thomas Ruf, 2017")

ap = argparse.ArgumentParser(description='Run SHiP "pot" simulation')
ap.add_argument("-d", "--debug", action="store_true")
ap.add_argument("-f", "--force", action="store_true", help="force overwriting output directory")
ap.add_argument("-r", "--run-number", type=int, dest="runnr", default=1)
ap.add_argument(
    "--reproducible",
    action="store_true",
    help="Reduce nondeterministic log output for reproducibility/testing",
)
ap.add_argument(
    "-e", "--ecut", type=float, help="energy cut", default=0.5
)  # GeV   with 1 : ~1sec / event, with 2: 0.4sec / event, 10: 0.13sec
ap.add_argument("-n", "--num-events", type=int, help="number of events to generate", dest="nev", default=100)
ap.add_argument(
    "-G",
    "--G4only",
    action=argparse.BooleanOptionalAction,
    default=False,
    help="Whether or not to use Geant4 directly, no Pythia8 (--no-G4only or --G4only). Default set to False.",
)
ap.add_argument(
    "-P",
    "--pythiaDecay",
    action=argparse.BooleanOptionalAction,
    default=False,
    help="Whether or not to use Pythia8 for decays (--no-PythiaDecay or --PythiaDecay). Default set to False.",
)
ap.add_argument(
    "--pythia8-tune",
    dest="pythia8_tune",
    default="default",
    choices=["default", "FTFT"],
    help="Pythia8 tune for the primary interaction: default (Monash 2013) or FTFT "
    "(fixed-target open charm and beauty tune, arXiv:2608.29076).",
)
ap.add_argument("-t", "--tau-only", action=argparse.BooleanOptionalAction, dest="tauOnly", default=False)
ap.add_argument("-J", "--Jpsi-mainly", action=argparse.BooleanOptionalAction, dest="JpsiMainly", default=False)
ap.add_argument("-b", "--boostDiMuon", type=float, default=1.0, help="boost Di-muon branching ratios")
ap.add_argument("-X", "--boostFactor", type=float, default=1.0, help="boost Di-muon prod cross sections")
ap.add_argument(
    "--kaon-pion-splits",
    type=int,
    default=0,
    help="splitting factor for kaons and pions, in order to boost the number of muons stemming from their decays",
)
ap.add_argument(
    "--multiple-kpi-splits", action="store_true", help="split kaons and pions multiple times along the track path"
)

jpsi_group = ap.add_argument_group(
    "data-driven J/psi", "JpsiGenerator: NA50-normalised, SHiP-shaped J/psi source replacing Pythia8"
)
jpsi_group.add_argument(
    "--jpsi-data", action="store_true", help="J/psi-only sample from the data-driven model (no Pythia8)"
)
jpsi_group.add_argument(
    "--jpsi-inject",
    action="store_true",
    help="normal Pythia8 production with its J/psi vetoed and data-driven J/psi injected instead",
)
jpsi_group.add_argument(
    "--jpsi-per-event",
    type=float,
    default=None,
    help="with --jpsi-inject: mean number of J/psi added per event (alternative to --jpsi-enhancement)",
)
jpsi_group.add_argument(
    "--jpsi-enhancement",
    type=float,
    default=None,
    help="enhancement over the physical rate, weight 1/E per J/psi (1 = realistic). With --jpsi-data it sets "
    "the number of events, overriding -n; with --jpsi-inject it sets the J/psi content (default 1)",
)
jpsi_group.add_argument("--jpsi-shape", choices=["data", "hybrid", "gauss"], default="data")
jpsi_group.add_argument("--jpsi-tail", type=float, default=6.0, help="exponent n of (1-|xF|)^n")
jpsi_group.add_argument("--jpsi-ptsq", type=float, default=1.9, help="<pT^2> in GeV^2")
jpsi_group.add_argument("--jpsi-lambda", type=float, default=0.0, help="Collins-Soper polar coefficient")
jpsi_group.add_argument("--jpsi-output", choices=["mumu", "jpsi", "both"], default="mumu")

ap.add_argument("-C", "--charm", action=argparse.BooleanOptionalAction, default=False, help="generate charm decays")
ap.add_argument("-B", "--beauty", action=argparse.BooleanOptionalAction, default=False, help="generate beauty decays")
ap.add_argument(
    "-M",
    "--storeOnlyMuons",
    action=argparse.BooleanOptionalAction,
    default=False,
    help="store only muons, ignore neutrinos",
)
ap.add_argument("-N", "--skipNeutrinos", action=argparse.BooleanOptionalAction, default=False, help="skip neutrinos")
ap.add_argument(
    "-D",
    "--4darkPhoton",
    action=argparse.BooleanOptionalAction,
    dest="FourDP",
    default=False,
    help="enable ntuple production",
)
# for charm production
# A run is either charm or beauty, so only one ratio override is ever meaningful.
cross_section = ap.add_mutually_exclusive_group()
cross_section.add_argument(
    "-cc", "--chicc", type=float, default=None, help="ccbar over mbias cross section (overrides target-derived value)"
)
cross_section.add_argument(
    "-bb", "--chibb", type=float, default=None, help="bbbar over mbias cross section (overrides target-derived value)"
)
ap.add_argument(
    "--target-composition",
    default="W",
    choices=["W", "Mo"],
    help="Target composition. Default is Tungsten (W); Molybdenum (Mo) is the other preset.",
)
ap.add_argument(
    "-A",
    type=float,
    default=None,
    help=(
        "Target mass number; overrides --target-composition preset. "
        "Used to scale chicc/chibb as (A/A_Mo)^(heavyflavour_Ascale-mbias_Ascale) "
        "(default exponent: 0.29)."
    ),
)
ap.add_argument("-p", "--pot", default=4e13, help="number of protons on target per spill to normalize on")
ap.add_argument("-S", "--nStart", type=int, help="first event of input file to start", dest="nStart", default=0)
ap.add_argument(
    "-I",
    "--InputFile",
    type=str,
    dest="charmInputFile",
    default=ROOT.gSystem.Getenv("EOSSHIP")
    + "/eos/experiment/ship/data/Charm/Cascade-parp16-MSTP82-1-MSEL4-76Mpot_1.root",
    help="input file for charm/beauty decays",
)
ap.add_argument("-o", "--output", type=str, help="output directory", dest="work_dir", default=None)
ap.add_argument(
    "-rs", "--seed", type=int, help="random seed; default value is 0, see TRrandom::SetSeed documentation", default=0
)
ap.add_argument(
    "--DecayVolumeMedium",
    help="Set Decay Volume Medium. Choices are helium (default) or vacuums.",
    default="helium",
    choices=["helium", "vacuums"],
)
ap.add_argument(
    "--shieldName",
    help="Name of the shield in the database.",
    default="TRY_2026",
    choices=["TRY_2025", "TRY_2026"],
)
ap.add_argument(
    "--AddMuonShield",
    help="Whether or not to add the muon shield. Default set to False.",
    default=False,
    action=argparse.BooleanOptionalAction,
)
ap.add_argument(
    "--AddMuonShieldField",
    help="Whether or not to add the muon shield magnetic field. Default set to False.",
    default=False,
    action=argparse.BooleanOptionalAction,
)
ap.add_argument(
    "--AddHadronAbsorberOnly",
    help="Whether to only add the hadron absorber part of the muon shield. Default set to True.",
    default=True,
    action=argparse.BooleanOptionalAction,
)

ap.add_argument(
    "--z-offset", type=float, dest="z_offset", default=-84.0, help="z-offset for the FixedTargetGenerator [mm]"
)
ap.add_argument(
    "--x-offset", type=float, dest="x_offset", default=0.0, help="x-offset for the FixedTargetGenerator [mm]"
)
ap.add_argument(
    "--y-offset", type=float, dest="y_offset", default=0.0, help="y-offset for the FixedTargetGenerator [mm]"
)
ap.add_argument(
    "--beam-smear", type=float, dest="beam_smear", default=16.0, help="beam smearing for the FixedTargetGenerator [mm]"
)
ap.add_argument(
    "--beam-paint",
    type=float,
    dest="beam_paint",
    default=50.0,
    help="beam painting radius for the FixedTargetGenerator [mm]",
)
ap.add_argument(
    "--TARGET_YAML",
    dest="TARGET_YAML",
    help="File for target configuration",
    default=os.path.expandvars("$FAIRSHIP/geometry/target_config.yaml"),
)

ap.add_argument(
    "--AddCylindricalSensPlane",
    action="store_true",
    help="Whether or not to add cylindrical sensitive plane around the target. False by default.",
)
ap.add_argument(
    "--AddPostTargetSensPlane",
    action="store_true",
    help="Whether or not to add sensitive plane after the target. False by default.",
)

args = ap.parse_args()
if args.debug:
    logger.setLevel(logging.DEBUG)

if args.kaon_pion_splits < 0:
    ap.error("--kaon-pion-splits must be >= 0")
if args.multiple_kpi_splits and args.kaon_pion_splits == 0:
    ap.error("--multiple-kpi-splits requires --kaon-pion-splits > 0")
if args.jpsi_data and (args.charm or args.beauty or args.JpsiMainly or args.G4only):
    ap.error("--jpsi-data cannot be combined with --charm, --beauty, --Jpsi-mainly or --G4only")
if args.jpsi_inject and (args.jpsi_data or args.charm or args.beauty or args.JpsiMainly):
    ap.error("--jpsi-inject needs the minimum-bias production: not with --jpsi-data, --charm, --beauty or -J")
if args.jpsi_per_event is not None and not args.jpsi_inject:
    ap.error("--jpsi-per-event only applies to --jpsi-inject")
if args.jpsi_inject and args.jpsi_per_event is not None and args.jpsi_enhancement is not None:
    ap.error("give either --jpsi-enhancement or --jpsi-per-event, not both")


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
    if args.charm:
        args.work_dir = get_work_dir(args.runnr, "charm")
    if args.beauty:
        args.work_dir = get_work_dir(args.runnr, "beauty")
    else:
        args.work_dir = get_work_dir(args.runnr)
    if args.jpsi_data:
        args.work_dir = get_work_dir(args.runnr, "jpsi")
    elif args.jpsi_inject:
        args.work_dir = get_work_dir(args.runnr, "jpsi_inject")

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
# PYTHIA8 requires Random:seed to be in range [0, 900000000]
# When seed=0, ROOT generates a seed from system time which can exceed this limit
seed = args.seed
if seed == 0:
    ROOT.gRandom.SetSeed(0)  # Generate time-based seed
    seed = ROOT.gRandom.GetSeed()
# Clamp to PYTHIA8's maximum allowed seed value
if seed > 900000000:
    seed = seed % 900000000
ROOT.gRandom.SetSeed(seed)
shipRoot_conf.configure()  # load basic libraries, prepare atexit for python
if args.reproducible and not args.debug:
    ROOT.gErrorIgnoreLevel = ROOT.kWarning
ship_geo_kwargs = {
    "Yheight": dy,
    "DecayVolumeMedium": args.DecayVolumeMedium,
    "shieldName": args.shieldName,
    "TARGET_YAML": args.TARGET_YAML,
}
ship_geo = geometry_config.create_config(**ship_geo_kwargs)

txt = "pythia8_Geant4_"
if withEvtGen:
    txt = "pythia8_evtgen_Geant4_"
outFile = f"{outputDir}/{txt}{args.runnr}_{args.ecut}.root"
parFile = f"{outputDir}/ship.params.{txt}{args.runnr}_{args.ecut}.root"

# -----Timer--------------------------------------------------------
timer = ROOT.TStopwatch()
timer.Start()

# -----Create simulation run----------------------------------------
run = ROOT.FairRunSim()
run.SetName(mcEngine)  # Transport engine
if hasattr(run, "SetRunId"):
    run.SetRunId(args.runnr)
sink = ROOT.FairRootFileSink(outFile)
run.SetSink(sink)
ROOT.SetOwnership(sink, False)  # C++ FairRun takes ownership
if args.boostFactor > 1:
    # Turn off UseGeneralProcess to access GammaToMuons directly when cross-sections need to be changed
    os.environ["SET_GENERAL_PROCESS_TO_FALSE"] = "1"
if args.kaon_pion_splits > 0:
    os.environ["KAON_PION_SPLITS"] = str(args.kaon_pion_splits)
run.SetUserConfig("g4Config.C")  # user configuration file default g4Config.C
rtdb = run.GetRuntimeDb()

# -----Materials----------------------------------------------
run.SetMaterials("media.geo")
# -----Create geometry----------------------------------------------
cave = ROOT.ShipCave("CAVE")
cave.SetGeometryFileName("caveWithAir.geo")

run.AddModule(cave)
ROOT.SetOwnership(cave, False)  # C++ FairRunSim takes ownership

TargetStation = ROOT.ShipTargetStation(
    name="TargetStation",
    tl=ship_geo.target.length,
    tz=ship_geo.target.z,
    nS=ship_geo.target.nS,
    HeT=ship_geo.target.HeT,
)
TargetStation.SetLayerPosMat(
    d=ship_geo.target.xy,
    L=ship_geo.target.slices_length,
    G=ship_geo.target.slices_gap,
    M=ship_geo.target.slices_material,
)
target_version = getattr(ship_geo.target, "version", 1)
TargetStation.SetDesign(target_version)
if target_version >= 2:
    TargetStation.SetLastDiskDiameter(ship_geo.target.xy2)
TargetStation.SetShieldingReferenceLength(ship_geo.target.length_fixed)
run.AddModule(TargetStation)
ROOT.SetOwnership(TargetStation, False)  # C++ FairRunSim takes ownership


if args.AddPostTargetSensPlane:
    sensPlanePostT = ROOT.exitHadronAbsorber()
    sensPlanePostT.SetEnergyCut(args.ecut * u.GeV)
    sensPlanePostT.SetVetoPointName("PlanePostT")
    # by default, if the z-position is not set, the positioning is behind the hadron abosorber and the tracks are stopped when they hit the sens plane
    # if the z-position is set and has a reasonable value (below 1E8), then the tracks are not stopped and continue to the last plane after the hadron absorber
    sensPlanePostT.SetZposition(
        ship_geo.target.length + 7.6 * u.cm + 300 * u.mm
    )  # target length + vessel shift + shielding length
    sensPlanePostT.SetUseCaveCoordinates()  # position set from the cave to avoid extrusions since the plane is larger than the target vacuum box

    if args.storeOnlyMuons:
        sensPlanePostT.SetOnlyMuons()
    if args.skipNeutrinos:
        sensPlanePostT.SkipNeutrinos()
    if args.FourDP:
        sensPlanePostT.SetOpt4DP()
    run.AddModule(sensPlanePostT)
    ROOT.SetOwnership(sensPlanePostT, False)  # C++ FairRunSim takes ownership


if args.AddMuonShield or args.AddHadronAbsorberOnly:
    n_params = 15
    if not args.AddMuonShieldField:
        for i in range(ship_geo.muShield.nMagnets):
            ship_geo.muShield.params[i * n_params + 14] = 0  # set B field to 0
    if args.AddHadronAbsorberOnly:
        ship_geo.muShield.params = ship_geo.muShield.params[:15]  # set dXIn to 0

    MuonShield = ROOT.ShipMuonShield(
        in_params=list(ship_geo.muShield.params),
        z=ship_geo.muShield.z,
        WithConstShieldField=True,
        SC_key=ship_geo.SC_mag,
    )
    # MuonShield.SetSupports(False) # otherwise overlap with sensitive Plane
    run.AddModule(MuonShield)  # needs to be added because of magn hadron shield.
    ROOT.SetOwnership(MuonShield, False)  # C++ FairRunSim takes ownership


sensPlaneHA = ROOT.exitHadronAbsorber()
sensPlaneHA.SetNSplits(args.kaon_pion_splits)  # type: ignore[missing-attribute]
if args.multiple_kpi_splits:
    sensPlaneHA.SetSplitMultipleTimes()  # type: ignore[missing-attribute]
sensPlaneHA.SetEnergyCut(args.ecut * u.GeV)
sensPlaneHA.SetVetoPointName("PlaneHA")

sensPlaneT = None
if args.AddCylindricalSensPlane:  # add additional sensitive plane around target
    sensPlaneT = ROOT.exitHadronAbsorber()
    sensPlaneT.SetEnergyCut(args.ecut * u.GeV)
    sensPlaneT.SetVetoPointName("PlaneT")
    sensPlaneT.SetCylindricalPlane()
    # by default, if the z-position is not set, the positioning is behind the hadron abosorber and the tracks are stopped when they hit the sens plane
    # if the z-position is set and has a reasonable value (below 1E8), then the tracks are not stopped and continue to the last plane after the hadron absorber
    sensPlaneT.SetZposition(ship_geo.target.length)

if args.storeOnlyMuons:
    sensPlaneHA.SetOnlyMuons()
    if sensPlaneT is not None:
        sensPlaneT.SetOnlyMuons()
if args.skipNeutrinos:
    sensPlaneHA.SkipNeutrinos()
    if sensPlaneT is not None:
        sensPlaneT.SkipNeutrinos()
if args.FourDP:  # in case a ntuple should be filled with pi0,etas,omega
    sensPlaneHA.SetOpt4DP()
    if sensPlaneT is not None:
        sensPlaneT.SetOpt4DP()

run.AddModule(sensPlaneHA)
ROOT.SetOwnership(sensPlaneHA, False)  # C++ FairRunSim takes ownership

if args.AddCylindricalSensPlane:
    run.AddModule(sensPlaneT)
    ROOT.SetOwnership(sensPlaneT, False)  # C++ FairRunSim takes ownership

# -----Create PrimaryGenerator--------------------------------------
primGen = ROOT.FairPrimaryGenerator()


def make_jpsi_generator():
    """Data-driven J/psi source with the settings shared by both J/psi modes.

    Its Init() is called by FairPrimaryGenerator during run.Init(), after the
    geometry exists: that is when the target scan fixes the vertex
    distribution, the rate per POT and hence the weight.
    """
    g = ROOT.JpsiGenerator()
    g.SetMom(400.0 * u.GeV)
    g.SetRapidityShape(args.jpsi_shape)
    g.SetForwardTail(args.jpsi_tail)
    g.SetPtSq(args.jpsi_ptsq)
    g.SetPolarisation(args.jpsi_lambda)
    g.SetOutputMode(args.jpsi_output)
    g.SetTargetCoordinates(
        ship_geo.target.z0 + args.z_offset * u.mm,
        ship_geo.target.z0 + ship_geo.target.length,
        args.x_offset * u.mm,
        args.y_offset * u.mm,
    )
    g.SetSmearBeam(args.beam_smear * u.mm)
    g.SetPaintRadius(args.beam_paint * u.mm)
    g.SetSeed(seed)
    return g


jpsiGen = None
if args.jpsi_data:
    # J/psi-only sample: every event is one data-driven J/psi
    P8gen = None
    gen = jpsiGen = make_jpsi_generator()
    gen.SetPot(float(args.pot))
    if args.jpsi_enhancement is not None:
        gen.SetEnhancement(args.jpsi_enhancement)
    else:
        gen.SetNEvents(args.nev)
else:
    P8gen = ROOT.FixedTargetGenerator()
    P8gen.SetZoffset(args.z_offset * u.mm)
    P8gen.SetXoffset(args.x_offset * u.mm)
    P8gen.SetYoffset(args.y_offset * u.mm)
    P8gen.SetSmearBeam(args.beam_smear * u.mm)
    P8gen.SetPaintRadius(args.beam_paint * u.mm)
    # Use geometry constants instead of fragile TGeo navigation
    P8gen.SetTargetCoordinates(ship_geo.target.z0, ship_geo.target.z0 + ship_geo.target.length)
    P8gen.SetMom(400.0 * u.GeV)
    P8gen.SetEnergyCut(args.ecut * u.GeV)
    P8gen.SetDebug(args.debug)
    P8gen.SetHeartBeat(100000)
    if args.G4only:
        P8gen.SetG4only()
    if args.pythia8_tune != "default":
        P8gen.SetPythiaTune(args.pythia8_tune)
    if args.JpsiMainly:
        P8gen.SetJpsiMainly()
    if args.tauOnly:
        P8gen.SetTauOnly()
    if withEvtGen:
        P8gen.WithEvtGen()
    if args.boostDiMuon > 1:
        P8gen.SetBoost(
            args.boostDiMuon
        )  # will increase BR for rare eta,omega,rho ... mesons decaying to 2 muons in Pythia8
        # and later copied to Geant4
    P8gen.SetSeed(seed)
    # for charm/beauty
    #        print ' for experts: p pot= number of protons on target per spill to normalize on'
    #        print '            : c chicc= ccbar over mbias cross section'
    if args.charm or args.beauty:
        check_run_type_override(args.beauty, args.chicc, args.chibb)
        cs = derive_cross_sections(args.target_composition, args.A, args.chicc, args.chibb)
        P8gen.SetChicc(cs.chicc)
        P8gen.SetChibb(cs.chibb)
        print(format_summary(cs, None if args.A is not None else args.target_composition))
        print("--- process heavy flavours ---")
        P8gen.InitForCharmOrBeauty(charmInputFile, args.nev, args.pot, args.nStart)
    gen = P8gen
primGen.AddGenerator(gen)
ROOT.SetOwnership(gen, False)  # C++ FairPrimaryGenerator takes ownership
if args.jpsi_inject:
    # Pythia8 keeps producing everything else; its J/psi (and their decay
    # products) are not transported, and data-driven J/psi are added to the
    # same events instead. Each minimum-bias event stands for one POT.
    P8gen.SetVetoJpsi()
    jpsiGen = make_jpsi_generator()
    jpsiGen.SetInjection(True)
    jpsiGen.SetPotPerEvent(1.0)
    if args.jpsi_per_event is not None:
        jpsiGen.SetMeanPerEvent(args.jpsi_per_event)
    else:
        jpsiGen.SetEnhancement(args.jpsi_enhancement if args.jpsi_enhancement is not None else 1.0)
    primGen.AddGenerator(jpsiGen)
    ROOT.SetOwnership(jpsiGen, False)  # C++ FairPrimaryGenerator takes ownership
#
run.SetGenerator(primGen)
ROOT.SetOwnership(primGen, False)  # C++ FairRunSim takes ownership

# -----Initialize simulation run------------------------------------
run.Init()

gMC = ROOT.TVirtualMC.GetMC()
fStack = gMC.GetStack()
fStack.SetMinPoints(1)
fStack.SetEnergyCut(-1.0)
if args.kaon_pion_splits > 0:
    fStack.SetSplitting()
#
import AddDiMuonDecayChannelsToG4

if not args.jpsi_data:  # no Pythia instance in the data-driven J/psi mode
    AddDiMuonDecayChannelsToG4.Initialize(P8gen.GetPythia())

# boost gamma2muon conversion
if args.boostFactor > 1:
    ROOT.gROOT.ProcessLine('#include "Geant4/G4ProcessTable.hh"')
    ROOT.gROOT.ProcessLine('#include "Geant4/G4AnnihiToMuPair.hh"')
    ROOT.gROOT.ProcessLine('#include "Geant4/G4GammaConversionToMuons.hh"')
    gProcessTable = ROOT.G4ProcessTable.GetProcessTable()
    procAnnihil = gProcessTable.FindProcess(ROOT.G4String("AnnihiToMuPair"), ROOT.G4String("e+"))
    procGMuPair = gProcessTable.FindProcess(ROOT.G4String("GammaToMuPair"), ROOT.G4String("gamma"))
    procAnnihil.SetCrossSecFactor(args.boostFactor)
    procGMuPair.SetCrossSecFactor(args.boostFactor)

# -----Start run----------------------------------------------------
nev = args.nev
if jpsiGen is not None:
    print(jpsiGen.Summary())
if args.jpsi_data:
    nev = jpsiGen.NEventsToGenerate()  # fixed by the enhancement, known only after run.Init()
run.Run(nev)

# -----Finish-------------------------------------------------------
timer.Stop()
rtime = timer.RealTime()
ctime = timer.CpuTime()
print(" ")
print("Macro finished successfully.")
print(f"Output file is {outFile}")
if not args.reproducible:
    print(f"Real time {rtime} s, CPU time {ctime} s")
# ---post processing--- remove empty events --- save histograms
tmpFile = outFile + "tmp"
if ROOT.gROOT.GetListOfFiles().GetEntries() > 0:
    fin = ROOT.gROOT.GetListOfFiles()[0]
else:
    fin = ROOT.TFile.Open(outFile)
fHeader = fin.Get("FileHeader")
if fHeader:
    fHeader.SetRunId(args.runnr)
else:
    print("WARNING: FileHeader not found in simulation output; skipped FileHeader RunID update")
if args.charm or args.beauty:
    # normalization for charm
    poteq = P8gen.GetPotForCharm()
    info = "POT equivalent = %7.3G" % (poteq)
elif jpsiGen is not None:
    pot_sample = float(args.pot) if args.jpsi_data else float(nev)
    info = "POT = %7.3G, J/psi %s: weight = %.6G, J/psi->mumu/POT = %.4G, shape %s n=%g" % (
        pot_sample,
        "only" if args.jpsi_data else "injected (%.4G per event)" % jpsiGen.MeanPerEvent(),
        jpsiGen.EventWeight(),
        jpsiGen.ProbMuMuPerPot(),
        args.jpsi_shape,
        args.jpsi_tail,
    )
    with open(os.path.join(outputDir, "jpsi_generator_metadata.json"), "w") as fmeta:
        json.dump({str(k): float(v) for k, v in jpsiGen.Metadata()}, fmeta, indent=1)
else:
    info = f"POT = {args.nev}"

conditions = " with ecut=" + str(args.ecut)
if args.pythia8_tune != "default":
    conditions += " " + args.pythia8_tune
if args.JpsiMainly:
    conditions += " J"
if args.tauOnly:
    conditions += " T"
if withEvtGen:
    conditions += " V"
if args.boostDiMuon > 1:
    conditions += " diMu" + str(args.boostDiMuon)
if args.boostFactor > 1:
    conditions += " X" + str(args.boostFactor)

info += conditions
if fHeader:
    fHeader.SetTitle(info)
    print(f"Data generated {fHeader.GetTitle()}")
else:
    print(f"Data generated {info}")

nt = fin.Get("4DP")
if nt:
    nt = fin["4DP"]
    tf = ROOT.TFile("FourDP.root", "recreate")
    tnt = nt.CloneTree(0)
    for i in range(nt.GetEntries()):
        rc = nt.GetEvent(i)
        rc = tnt.Fill(nt.id, nt.px, nt.py, nt.pz, nt.x, nt.y, nt.z)
    tnt.Write()
    tf.Close()

t = fin["cbmsim"]
fout = ROOT.TFile(tmpFile, "recreate")
sTree = t.CloneTree(0)
nEvents = 0
for n in range(t.GetEntries()):
    rc = t.GetEvent(n)
    if (
        (len(t.PlaneHAPoint) > 0)
        or (args.AddCylindricalSensPlane and len(t.PlaneTPoint) > 0)
        or (args.AddPostTargetSensPlane and len(t.PlanePostTPoint) > 0)
    ):
        rc = sTree.Fill()
        nEvents += 1
fout.cd()
for k in fin.GetListOfKeys():
    x = fin.Get(k.GetName())
    className = x.Class().GetName()
    if className.find("TTree") < 0 and className.find("TNtuple") < 0:
        xcopy = x.Clone()
        rc = xcopy.Write()
sTree.AutoSave()
if fHeader:
    ff = fHeader.Clone(fout.GetName())
    fout.cd()
    ff.Write("FileHeader", ROOT.TObject.kSingleKey)
sTree.Write()
fout.Close()

rc1 = os.system("rm  " + outFile)
rc2 = os.system("mv " + tmpFile + " " + outFile)
print("removed out file, moved tmpFile to out file", rc1, rc2)

if rc1 == 0 and rc2 == 0:
    print("INFO: Adding file summary")
    fsr = vars(args)
    with ROOT.TFile.Open(outFile, "UPDATE") as _of:
        _of.WriteObject(ROOT.TString(json.dumps(fsr)), "FileSummary")
else:
    print("WARNING: tempFile mv or rm not successful. No attempt at FileSummary writing")

fin.SetWritable(False)  # bpyass flush error

print(f"Number of events produced with activity after hadron absorber: {nEvents}")

if checkOverlap:
    sGeo = ROOT.gGeoManager
    sGeo.CheckOverlaps()
    sGeo.PrintOverlaps()
    run.CreateGeometryFile("%s/geofile_full.root" % (outputDir))
    import saveBasicParameters

    saveBasicParameters.execute("%s/geofile_full.root" % (outputDir), ship_geo)
