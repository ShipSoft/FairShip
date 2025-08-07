#!/usr/bin/env python
import os
import sys
import warnings

# Suppress common ROOT/cppyy warnings that don't affect functionality
warnings.filterwarnings("ignore", message="No precompiled header available")
warnings.filterwarnings("ignore", message="pkg_resources is deprecated")

# Core imports that are always needed
from argparse import ArgumentParser

from enhanced_configurators import (
    EnhancedSimulationConfiguratorFactory as SimulationConfiguratorFactory,
)
from generator_configurator import GeneratorConfiguratorFactory

# Configuration and initialization infrastructure
from lazy_loading import setup_lazy_imports
from root_initialization import initialize_simulation_environment
from simulation_config import initialize_configuration
from simulation_execution_configurator import SimulationExecutionConfiguratorFactory

parser = ArgumentParser()
group = parser.add_mutually_exclusive_group()

parser.add_argument("--evtcalc", help="Use EventCalc", action="store_true")
parser.add_argument("--Pythia6", dest="pythia6", help="Use Pythia6", action="store_true")
parser.add_argument("--Pythia8", dest="pythia8", help="Use Pythia8", action="store_true")
# === PG subcommand ===
subparsers = parser.add_subparsers(dest="command", help="Which mode to run")
pg_parser = subparsers.add_parser("PG", help="Use Particle Gun")

pg_parser.add_argument(
    "--multiplePG",
    help="Multiple particle guns in a x-y plane at a fixed z or in a 3D volume",
    action="store_true"
)
pg_parser.add_argument(
    "--pID", dest="pID", default=22, type=int,
    help="id of particle used by the gun (default=22)"
)
pg_parser.add_argument(
    "--Estart", default=10, type=float,
    help="start of energy range of particle gun (default=10 GeV)"
)
pg_parser.add_argument(
    "--Eend", default=10, type=float,
    help="end of energy range of particle gun (default=10 GeV)"
)
pg_parser.add_argument(
    "--Vx", dest="Vx", default=0, type=float,
    help="x position of particle gun (default=0 cm)"
)
pg_parser.add_argument(
    "--Vy", dest="Vy", default=0, type=float,
    help="y position of particle gun (default=0 cm)"
)
pg_parser.add_argument(
    "--Vz", dest="Vz", default=0, type=float,
    help="z position of particle gun (default=0 cm)"
)
pg_parser.add_argument(
    "--Dx", dest="Dx", type=float,
    help="size of the full uniform spread of PG xpos: (Vx - Dx/2, Vx + Dx/2)"
)
pg_parser.add_argument(
    "--Dy", dest="Dy", type=float,
    help="size of the full uniform spread of PG ypos: (Vy - Dy/2, Vy + Dy/2)"
)
# === Enf of PG commands ===
parser.add_argument("-A", help="b: signal from b, c: from c (default), bc: from Bc, or inclusive", default='c')
parser.add_argument("--Genie", dest="genie", help="Genie for reading and processing neutrino interactions", action="store_true")
parser.add_argument("--NuRadio", dest="nuradio", help="misuse GenieGenerator for neutrino radiography and geometry timing test", action="store_true")
parser.add_argument("--Ntuple", dest="ntuple", help="Use ntuple as input", action="store_true")
parser.add_argument("--MuonBack", dest="muonback", help="Generate events from muon background file, --Cosmics=0 for cosmic generator data", action="store_true")
parser.add_argument("--FollowMuon", dest="followMuon", help="Make muonshield active to follow muons", action="store_true")
parser.add_argument("--FastMuon", dest="fastMuon", help="Only transport muons for a fast muon only background estimate", action="store_true")
parser.add_argument("--phiRandom", help="only relevant for muon background generator, random phi", action="store_true")
parser.add_argument("--SmearBeam", dest="SmearBeam",  help="Standard deviation of beam smearing (muon background only) [cm]", default=0.8, type=float)
parser.add_argument("--PaintBeam", dest="PaintBeam",  help="Radius of beam painting (muon background only) [cm]", default=5, type=float)
parser.add_argument("--Cosmics", dest="cosmics", help="Use cosmic generator, argument switch for cosmic generator 0 or 1", default=None)  # TODO: Understand integer options, replace with store_true?
parser.add_argument("--MuDIS", dest="mudis", help="Use muon deep inelastic scattering generator", action="store_true")
parser.add_argument("--RpvSusy", dest="RPVSUSY", help="Generate events based on RPV neutralino", action="store_true")
parser.add_argument("--FixedTarget", dest="fixedTarget", help="Enable fixed target simulation", action="store_true")
parser.add_argument("--DarkPhoton", help="Generate dark photons", action="store_true")
parser.add_argument("--SusyBench", dest="RPVSUSYbench", help="Generate HP Susy", default=2)
parser.add_argument("-m", "--mass", dest="theMass", help="Mass of hidden particle, default 1.0 GeV for HNL, 0.2 GeV for DP", default=None, type=float)
parser.add_argument("-c", "--couplings", "--coupling", dest="thecouplings",  help="couplings 'U2e,U2mu,U2tau' or -c 'U2e,U2mu,U2tau' to set list of HNL couplings.\
 TP default for HNL, ctau=53.3km", default="0.447e-9,7.15e-9,1.88e-9")
parser.add_argument("-cp", "--production-couplings", dest="theprodcouplings",  help="production couplings 'U2e,U2mu,U2tau' to set the couplings for HNL production only"\
                                            ,default=None)
parser.add_argument("-cd", "--decay-couplings", dest="thedeccouplings",  help="decay couplings  'U2e,U2mu,U2tau' to set the couplings for HNL decay only", default=None)
parser.add_argument("-e", "--epsilon", dest="theDPepsilon", help="to set mixing parameter epsilon", default=0.00000008, type=float)
parser.add_argument("-n", "--nEvents", dest="nEvents", help="Number of events to generate", default=100, type=int)
parser.add_argument("-i", "--firstEvent", help="First event of input file to use", default=0, type=int)
parser.add_argument("-s", "--seed", dest="theSeed", help="Seed for random number. Only for experts, see TRrandom::SetSeed documentation", default=0, type=int)
parser.add_argument("-S", "--sameSeed",dest="sameSeed",  help="can be set to an integer for the muonBackground simulation with specific seed for each muon, only for experts!", default=False, type=int)
group.add_argument("-f", dest="inputFile", help="Input file if not default file", default=False)
parser.add_argument("-g", dest="geofile", help="geofile for muon shield geometry, for experts only", default=None)
parser.add_argument("-o", "--output", dest="outputDir", help="Output directory",  default=".")
parser.add_argument("-Y", dest="dy", help="max height of vacuum tank", default=10)
parser.add_argument("--caloDesign",
                    help="0=ECAL/HCAL TP 2=splitCal  3=ECAL/ passive HCAL",
                    default=3,
                    type=int,
                    choices=[0,2,3])
parser.add_argument("--strawDesign", help="Tracker design: 4=sophisticated straw tube design, horizontal wires; 10=straw of 2 cm diameter (default)",
                    default=4, type=int, choices=[4,10])
parser.add_argument("-F", dest="deepCopy", help="default = False: copy only stable particles to stack, except for HNL events", action="store_true")
parser.add_argument("-t", "--test", dest="testFlag", help="quick test", action="store_true")
parser.add_argument("--dry-run", dest="dryrun", help="stop after initialize", action="store_true")
parser.add_argument("-D", "--display", dest="eventDisplay", help="store trajectories", action="store_true")
parser.add_argument("--shieldName", help="The name of the muon shield in the database to use.", default="New_HA_Design", choices=["New_HA_Design", "warm_opt"])
parser.add_argument("--MesonMother", dest="MM", help="Choose DP production meson source: pi0, eta, omega, eta1, eta11", default='pi0')
parser.add_argument("--debug", help="1: print weights and field 2: make overlap check", default=0, type=int, choices=range(0,3))
parser.add_argument("--field_map", default=None, help="Specify spectrometer field map.")
parser.add_argument("--z-offset", dest="z_offset", help="z-offset for the FixedTargetGenerator [mm]", default=-84., type=float)
parser.add_argument(
    "--helium",
    dest="decayVolMed",
    help="Set Decay Volume medium to helium. NOOP, as default is helium",
    action="store_const",
    const="helium",
    default="helium"
)
parser.add_argument(
    "--vacuums",
    dest="decayVolMed",
    help="Set Decay Volume medium to vacuum(vessel structure changes)",
    action="store_const",
    const="vacuums",
    default="helium"
)

parser.add_argument("--SND", dest="SND", help="Activate SND.", action='store_true')
parser.add_argument(
    "--SND_design",
    help="Choose SND design(s) among [1,2,...] or 'all' to enable all. 1: EmulsionTarget, 2: MTC",
    nargs='+',
    default=[2],
)
parser.add_argument("--noSND", dest="SND", help="Deactivate SND. NOOP, as it currently defaults to off.", action='store_false')
parser.add_argument("--target-yaml", help="Path to the yaml target config file", default=os.path.expandvars("$FAIRSHIP/geometry/target_config_Jun25.yaml"))



options = parser.parse_args()

# Initialize configuration management system
print("Initializing simulation configuration...")

# Initialize lazy loading system
try:
    import_manager = setup_lazy_imports(options)
    # Access modules through lazy loading
    ROOT = import_manager.get_module('ROOT')
    u = import_manager.get_module('shipunit')
    shipRoot_conf = import_manager.get_module('shipRoot_conf')
    ut = import_manager.get_module('rootUtils')
    ConfigRegistry = import_manager.get_module('ShipGeoConfig').ConfigRegistry
    USING_LAZY_LOADING = True
except Exception as e:
    print(f"Warning: Lazy loading failed ({e}), falling back to direct imports")
    # Fallback to direct imports
    import ROOT
    import rootUtils as ut
    import shipunit as u
    from ShipGeoConfig import ConfigRegistry
    USING_LAZY_LOADING = False
    import_manager = None

# Initialize configuration with units module
config_manager = initialize_configuration(options, u)
config = config_manager.simulation_config
runtime_config = config_manager.runtime_config
particle_config = config.particle_config

# Set flag in config
config.using_lazy_loading = USING_LAZY_LOADING

# Extract commonly used values for backward compatibility
theHNLMass = particle_config.hnl_mass
theDPmass = particle_config.dp_mass

# Override argument defaults with configuration values if not explicitly set
if options.theMass is None:
    # Set default mass based on particle type
    if hasattr(options, 'DarkPhoton') and options.DarkPhoton:
        options.theMass = theDPmass
    else:
        options.theMass = theHNLMass

# Override design defaults with configuration values if they match hardcoded defaults
default = config.default_design
globalDesigns = config.global_designs
if options.dy == 10:  # If it's still the hardcoded default
    options.dy = globalDesigns[default]['dy']
if options.caloDesign == 3:  # If it's still the hardcoded default
    options.caloDesign = globalDesigns[default]['caloDesign']
if options.strawDesign == 4:  # If it's still the hardcoded default
    options.strawDesign = globalDesigns[default]['strawDesign']
theProductionCouplings = particle_config.production_couplings
theDecayCouplings = particle_config.decay_couplings
inclusive = particle_config.inclusive
charmonly = particle_config.charmonly
HNL = particle_config.hnl_enabled
mcEngine = config.mc_engine
inputFile = config.input_file
defaultInputFile = config.default_input_file
MCTracksWithHitsOnly = config.mc_tracks_with_hits_only
MCTracksWithEnergyCutOnly = config.mc_tracks_with_energy_cut_only
MCTracksWithHitsOrEnergyCut = config.mc_tracks_with_hits_or_energy_cut
DownScaleDiMuon = config.down_scale_dimuon

print(config_manager.get_summary())

# Handle SND_design: allow 'all' (case-insensitive) or list of ints
available_snd_designs = [1, 2]  # Extend this list as new designs are added
if any(str(x).lower() == 'all' for x in options.SND_design):
    options.SND_design = available_snd_designs
else:
    try:
        options.SND_design = [int(x) for x in options.SND_design]
    except Exception:
        print("Invalid value for --SND_design. Use integers or 'all'.")
        sys.exit(1)

# Additional option processing for motherMode and other special cases
if hasattr(options, 'MM') and options.MM:
     motherMode = options.MM
if hasattr(options, 'cosmics') and options.cosmics:
     simEngine = "Cosmics"
     Opt_high = int(options.cosmics)

# Handle couplings for backward compatibility
if hasattr(options, 'thecouplings') and options.thecouplings:
  theCouplings = [float(c) for c in options.thecouplings.split(",")]
else:
  # Use configuration values
  if theProductionCouplings == theDecayCouplings:
    theCouplings = theProductionCouplings or [0.447e-9,7.15e-9,1.88e-9]
  else:
    theCouplings = theProductionCouplings or [0.447e-9,7.15e-9,1.88e-9]


#sanity check
if (HNL and options.RPVSUSY) or (HNL and options.DarkPhoton) or (options.DarkPhoton and options.RPVSUSY):
 print("cannot have HNL and SUSY or DP at the same time, abort")
 sys.exit(2)

if (options.genie or options.nuradio) and defaultInputFile:
  inputFile = "/eos/experiment/ship/data/GenieEvents/genie-nu_mu.root"
if options.mudis and defaultInputFile:
  print('input file required if simEngine = muonDIS')
  print(" for example -f  /eos/experiment/ship/data/muonDIS/muonDis_1.root")
  sys.exit()

if (options.ntuple or options.muonback) and defaultInputFile :
  print('input file required if simEngine = Ntuple or MuonBack')
  print(" for example -f /eos/experiment/ship/data/Mbias/pythia8_Geant4-withCharm_onlyMuons_4magTarget.root")
  sys.exit()
# Initialize ROOT and libraries through controlled initialization
ROOT.gRandom.SetSeed(options.theSeed)  # this should be propagated via ROOT to Pythia8 and Geant4VMC

# Initialize simulation environment (ROOT libraries already loaded via lazy loading or direct import)
init_result = initialize_simulation_environment(
    seed=options.theSeed,
    load_ship_libs=True,
    config_level=0
)
ship_geo = ConfigRegistry.loadpy(
     "$FAIRSHIP/geometry/geometry_config.py",
     Yheight=options.dy,
     CaloDesign=options.caloDesign,
     strawDesign=options.strawDesign,
     muShieldGeo=options.geofile,
     shieldName=options.shieldName,
     DecayVolumeMedium=options.decayVolMed,
     SND=options.SND,
     SND_design=options.SND_design,
     TARGET_YAML=options.target_yaml
)

# Use runtime configuration for file naming
tag = runtime_config.tag
outFile = runtime_config.output_file
parFile = runtime_config.parameter_file

# rm older files !!!
for x in os.listdir(config.output_dir):
  if not x.find(tag)<0: os.system(f"rm {config.output_dir}/{x}" )

# In general, the following parts need not be touched
# ========================================================================

# -----Timer--------------------------------------------------------
timer = ROOT.TStopwatch()
timer.Start()
# ------------------------------------------------------------------------
# -----Create simulation run----------------------------------------
run = ROOT.FairRunSim()
run.SetName(mcEngine)  # Transport engine
run.SetSink(ROOT.FairRootFileSink(outFile))  # Output file
run.SetUserConfig("g4Config.C") # user configuration file default g4Config.C
rtdb = run.GetRuntimeDb()
# -----Create geometry----------------------------------------------
# import shipMuShield_only as shipDet_conf # special use case for an attempt to convert active shielding geometry for use with FLUKA
# import shipTarget_only as shipDet_conf
# Replaced direct import with configurator pattern
det_configurator = SimulationConfiguratorFactory.create_detector_configurator()
modules = det_configurator.configure(run,ship_geo)
# -----Configure Primary Generators--------------------------------------
# Create configurators
pythia_configurator = SimulationConfiguratorFactory.create_pythia_configurator()
cosmics_configurator = SimulationConfiguratorFactory.create_cosmics_configurator()
generator_configurator = GeneratorConfiguratorFactory.create_generator_configurator(
    ROOT, u, ut, ship_geo, pythia_configurator, cosmics_configurator
)

# Prepare configuration values for generator configurator
generator_config_values = {
    'HNL': HNL,
    'inputFile': inputFile,
    'inclusive': inclusive,
    'charmonly': charmonly,
    'motherMode': motherMode if 'motherMode' in locals() else 'pi0',
    'theProductionCouplings': theProductionCouplings,
    'theDecayCouplings': theDecayCouplings,
    'theCouplings': theCouplings,
    'theHNLMass': theHNLMass,
    'DownScaleDiMuon': DownScaleDiMuon,
    'MCTracksWithHitsOnly': MCTracksWithHitsOnly,
    'MCTracksWithEnergyCutOnly': MCTracksWithEnergyCutOnly,
    'MCTracksWithHitsOrEnergyCut': MCTracksWithHitsOrEnergyCut,
    'Opt_high': Opt_high if 'Opt_high' in locals() else None,
}

# Configure all generators
primGen, generators = generator_configurator.configure_all_generators(run, options, generator_config_values, modules)

# Update configuration values that may have been modified by generator setup
MCTracksWithHitsOnly = generator_config_values.get('MCTracksWithHitsOnly', MCTracksWithHitsOnly)

# -----Execute Simulation--------------------------------------
# Create configurators for simulation execution
geom_configurator = SimulationConfiguratorFactory.create_geometry_configurator()
utility_configurator = SimulationConfiguratorFactory.create_utility_configurator()
execution_configurator = SimulationExecutionConfiguratorFactory.create_simulation_execution_configurator(
    ROOT, u, config_manager, geom_configurator, utility_configurator
)

# Prepare execution configuration values
execution_config_values = {
    'MCTracksWithHitsOnly': MCTracksWithHitsOnly,
    'MCTracksWithEnergyCutOnly': MCTracksWithEnergyCutOnly,
    'MCTracksWithHitsOrEnergyCut': MCTracksWithHitsOrEnergyCut,
}

# Execute the complete simulation workflow
gMC, fStack, fieldMaker = execution_configurator.execute_full_simulation(
    run, rtdb, options, execution_config_values, ship_geo, runtime_config,
    timer, outFile, parFile, inputFile, generators, HNL, USING_LAZY_LOADING, import_manager
)

# ------------------------------------------------------------------------
# Create utility configurator for functions that might be called later
utility_configurator_global = SimulationConfiguratorFactory.create_utility_configurator()
def visualizeMagFields():
 utility_configurator_global.visualize_mag_fields()
def checkOverlapsWithGeant4():
 # after /run/initialize, but prints warning messages, problems with TGeo volume
 mygMC = ROOT.TGeant4.GetMC()
 mygMC.ProcessGeantCommand("/geometry/test/recursion_start 0")
 mygMC.ProcessGeantCommand("/geometry/test/recursion_depth 2")
 mygMC.ProcessGeantCommand("/geometry/test/run")
