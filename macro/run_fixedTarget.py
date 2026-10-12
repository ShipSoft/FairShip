#!/usr/bin/env python
# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

import hashlib
import json
import math
import os

import geometry_config
import ROOT
import shipRoot_conf
import shipunit as u
from heavyFlavourScaling import (
    check_input_flavour,
    check_run_type_override,
    derive_cross_sections,
    file_is_beauty,
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
    "data-driven J/psi",
    "JpsiGenerator: NA50 normalisation, rapidity shape from NA50 and SHiP Table 5 (arXiv:2604.03661), instead of "
    "Pythia8's J/psi (the default). Physics weights: each event stands for one POT, the POT normalisation is applied "
    "in the analysis",
)
jpsi_group.add_argument(
    "--jpsi-data", action="store_true", help="J/psi-only sample, one data-driven J/psi per event (no Pythia8)"
)
jpsi_group.add_argument(
    "--jpsi-inject",
    action="store_true",
    help="minimum-bias production with Pythia8's J/psi (and descendants) not transported, data-driven J/psi added "
    "as an independent weighted overlay (mean yields preserved, no correlation with the host event)",
)
jpsi_group.add_argument(
    "--jpsi-per-event",
    type=float,
    default=None,
    help="with --jpsi-inject: mean number of J/psi added per event, weight rate/mu (default: the physical rate, "
    "weight 1)",
)
jpsi_group.add_argument(
    "--jpsi-config",
    default=None,
    help="key-value file overriding the nominal J/psi generator (testing and variations, keys in JpsiSampler.h)",
)

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
if args.pythia8_tune != "default" and (args.charm or args.beauty or args.G4only):
    ap.error("--pythia8-tune only affects the Pythia8 primary interaction, which --charm/--beauty/--G4only do not run")
if args.jpsi_data and (
    args.jpsi_inject
    or args.charm
    or args.beauty
    or args.JpsiMainly
    or args.tauOnly
    or args.G4only
    or args.pythiaDecay
    or args.boostDiMuon > 1
    or args.pythia8_tune != "default"
):
    ap.error(
        "--jpsi-data replaces Pythia8: not with --jpsi-inject, --charm, --beauty, -J, -t, --G4only, --pythiaDecay, "
        "--boostDiMuon or --pythia8-tune"
    )
if args.jpsi_inject and (args.charm or args.beauty or args.JpsiMainly or args.G4only):
    ap.error("--jpsi-inject needs the Pythia8 minimum-bias production: not with --charm, --beauty, -J or --G4only")
if (args.jpsi_per_event is not None) and not args.jpsi_inject:
    ap.error("--jpsi-per-event only applies to --jpsi-inject")
if args.jpsi_config and not (args.jpsi_data or args.jpsi_inject):
    ap.error("--jpsi-config needs --jpsi-data or --jpsi-inject")
if args.jpsi_config:
    # the macro changes into the work directory before the generator reads it
    args.jpsi_config = os.path.abspath(args.jpsi_config)
    if not os.path.isfile(args.jpsi_config):
        ap.error(f"--jpsi-config: no such file {args.jpsi_config}")


if args.G4only:
    args.charm = False
    args.beauty = False
    withEvtGen = False
    args.pythiaDecay = False
elif args.jpsi_data:
    withEvtGen = False
    logger.info("no Pythia8 or EvtGen: the J/psi -> mu mu decay is made by JpsiGenerator")
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
        tag = "charm"
    elif args.beauty:
        tag = "beauty"
    elif args.jpsi_data:
        tag = "jpsi"
    elif args.pythia8_tune != "default":
        tag = args.pythia8_tune
    else:
        tag = None
    if args.jpsi_inject:
        tag = "jpsi_inject" if tag is None else tag + "_jpsi_inject"
        if args.jpsi_per_event is not None:
            tag += f"_mu{args.jpsi_per_event:g}"
    if args.jpsi_config:
        # variations of the configuration must not share a directory: tag it with a hash of the file
        with open(args.jpsi_config, "rb") as _f:
            tag = (tag or "jpsi") + "_cfg" + hashlib.sha256(_f.read()).hexdigest()[:8]
    args.work_dir = get_work_dir(args.runnr, tag)

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
    sensPlanePostT.SetZposition(158.64 * u.cm + 300 * u.mm + 6.2 * u.cm)
    # NOMINAL target length + vessel shift + shielding length
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
    """Data-driven J/psi source. Its Init() runs inside run.Init(), once the geometry exists: the target scan
    then fixes the vertex distribution and the rate per POT, hence the weight."""
    g = ROOT.JpsiGenerator()
    if args.jpsi_config:
        g.SetConfigFile(args.jpsi_config)
    g.SetMom(400.0 * u.GeV)
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
P8gen = None
if args.jpsi_data:
    # J/psi-only sample: one data-driven J/psi per event, weight = J/psi -> mu mu per POT
    jpsiGen = make_jpsi_generator()
    jpsiGen.SetNEvents(args.nev)
    primGen.AddGenerator(jpsiGen)
    ROOT.SetOwnership(jpsiGen, False)  # C++ FairPrimaryGenerator takes ownership
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
        # cascade files written by makeCascadePythia8.py carry the cross section they were made with;
        # the flavour is taken from the file, as FixedTargetGenerator does
        with ROOT.TFile.Open(charmInputFile) as _fin:
            sigma_QQ = _fin.Get("sigma_QQ").GetVal() if _fin.Get("sigma_QQ") else None
            _ntuple = _fin.Get("pythia6")
            _ntuple.GetEntry(0)
            input_is_beauty = file_is_beauty(_ntuple.M)
            del _ntuple  # owned by the file, which is closed below
        check_input_flavour(args.beauty, input_is_beauty)
        if sigma_QQ:
            flavour = "beauty" if input_is_beauty else "charm"
            print(
                f"Input file {flavour} cross section per nucleon: {1e3 * sigma_QQ:.3g} ub, used to scale chi{flavour[0] * 2}"
            )
        cs = derive_cross_sections(args.target_composition, args.A, args.chicc, args.chibb, sigma_QQ, args.beauty)
        P8gen.SetChicc(cs.chicc)
        P8gen.SetChibb(cs.chibb)
        print(format_summary(cs, None if args.A is not None else args.target_composition))
        print("--- process heavy flavours ---")
        P8gen.InitForCharmOrBeauty(charmInputFile, args.nev, args.pot, args.nStart)
    primGen.AddGenerator(P8gen)
    ROOT.SetOwnership(P8gen, False)  # C++ FairPrimaryGenerator takes ownership
    if args.jpsi_inject:
        # Pythia8 keeps producing everything else; its J/psi and their descendants are not transported, and
        # data-driven J/psi are added to the same events (one POT each) instead
        P8gen.SetVetoJpsi()
        jpsiGen = make_jpsi_generator()
        jpsiGen.SetInjection(True)
        jpsiGen.SetPotPerEvent(1.0)
        if args.jpsi_per_event is not None:
            jpsiGen.SetMeanPerEvent(args.jpsi_per_event)
        else:
            jpsiGen.SetEnhancement(1.0)
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

if P8gen is not None:  # no Pythia8 instance in the J/psi-only mode
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
if jpsiGen is not None:
    print(jpsiGen.Summary())
run.Run(args.nev)

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
# not simply the first open file: for charm and beauty the generator keeps the input file open
fin = ROOT.gROOT.GetListOfFiles().FindObject(outFile)
if not fin:
    fin = ROOT.TFile.Open(outFile)
fHeader = fin.Get("FileHeader")
if fHeader:
    fHeader.SetRunId(args.runnr)
else:
    print("WARNING: FileHeader not found in simulation output; skipped FileHeader RunID update")
if (args.charm or args.beauty) and P8gen is not None:  # --charm/--beauty exclude --jpsi-data
    # normalization for charm
    poteq = P8gen.GetPotForCharm()
    info = "POT equivalent = %7.3G" % (poteq)
elif args.jpsi_data:
    info = f"POT = {args.nev} (J/psi only, one per event, weights per POT)"
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
if args.jpsi_inject:
    conditions += " JpsiInject"
if args.jpsi_config:
    conditions += " JpsiConfig=" + os.path.basename(args.jpsi_config)

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
    if jpsiGen is not None:
        # every event stands for one POT; the J/psi weights are physics weights (per POT)
        # JSON has no NaN: a setting that is not in use (e.g. map_tail_n without a data map) is stored as null
        fsr["JpsiGenerator"] = {str(k): (float(v) if math.isfinite(v) else None) for k, v in jpsiGen.Metadata()}
        fsr["JpsiGeneratorVersion"] = str(jpsiGen.Version())
        fsr["JpsiGeneratorConfig"] = str(jpsiGen.ConfigFile()) or "nominal"
        # the configuration and data-map files themselves, to reproduce the run
        fsr["JpsiGeneratorConfigText"] = str(jpsiGen.ConfigText())
    # the seed actually used (--seed 0 draws one from the clock), to reproduce the run
    fsr["seed_used"] = seed
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
