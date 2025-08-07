"""Centralized configuration management for SHiP simulation.

This module provides a comprehensive configuration system that manages
all global variables, default values, validation, and state management.
"""

import json
import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional, Union

import yaml

logger = logging.getLogger(__name__)


@dataclass
class ParticleConfig:
    """Configuration for particle physics parameters."""

    # HNL parameters
    hnl_mass: Optional[float] = None  # Will be set to 1.0 * GeV after units available
    production_couplings: Optional[list] = None
    decay_couplings: Optional[list] = None

    # Dark photon parameters
    dp_mass: Optional[float] = None  # Will be set to 0.2 * GeV after units available
    dp_epsilon: float = 0.00000008

    # Process selection
    inclusive: str = "c"
    charmonly: bool = False
    hnl_enabled: bool = True


@dataclass
class SimulationConfig:
    """Main simulation configuration container."""

    # Engine configuration
    mc_engine: str = "TGeant4"
    sim_engine: str = "Pythia8"

    # Event handling
    down_scale_dimuon: bool = False
    mc_tracks_with_hits_only: bool = False
    mc_tracks_with_energy_cut_only: bool = True
    mc_tracks_with_hits_or_energy_cut: bool = False

    # Input/output
    input_file: str = (
        "/eos/experiment/ship/data/Charm/Cascade-parp16-MSTP82-1-MSEL4-978Bpot.root"
    )
    default_input_file: bool = True
    output_dir: str = "."

    # Geometry designs
    global_designs: dict[str, dict[str, Union[int, float]]] = field(
        default_factory=lambda: {
            "2023": {"dy": 6.0, "caloDesign": 3, "strawDesign": 10},
            "2025": {"dy": 6.0, "ds": 8, "caloDesign": 2, "strawDesign": 10},
        }
    )
    default_design: str = "2025"

    # Particle physics
    particle_config: ParticleConfig = field(default_factory=ParticleConfig)

    # Runtime state
    using_lazy_loading: bool = False
    initialized: bool = False


@dataclass
class RuntimeConfig:
    """Runtime configuration that changes during execution."""

    # Current event processing
    current_event: int = 0
    total_events: int = 100

    # File names (generated at runtime)
    output_file: Optional[str] = None
    parameter_file: Optional[str] = None
    geometry_file: Optional[str] = None

    # Tag for file naming
    tag: Optional[str] = None

    # Timing information
    start_time: Optional[float] = None
    end_time: Optional[float] = None


class ConfigurationManager:
    """Central configuration manager for the simulation."""

    def __init__(self):
        self.simulation_config = SimulationConfig()
        self.runtime_config = RuntimeConfig()
        self._config_file_path: Optional[Path] = None
        self._units_module = None

    def set_units_module(self, units_module):
        """Set the units module and initialize unit-dependent defaults."""
        self._units_module = units_module
        self._initialize_unit_dependent_defaults()

    def _initialize_unit_dependent_defaults(self):
        """Initialize default values that depend on units."""
        if self._units_module is None:
            logger.warning(
                "Units module not set, cannot initialize unit-dependent defaults"
            )
            return

        u = self._units_module
        pc = self.simulation_config.particle_config

        if pc.hnl_mass is None:
            pc.hnl_mass = 1.0 * u.GeV
            logger.debug("Set default HNL mass to 1.0 GeV")

        if pc.dp_mass is None:
            pc.dp_mass = 0.2 * u.GeV
            logger.debug("Set default DP mass to 0.2 GeV")

    def load_from_options(self, options):
        """Load configuration from command line options."""
        logger.info("Loading configuration from command line options")

        sim_config = self.simulation_config
        runtime_config = self.runtime_config
        pc = sim_config.particle_config

        # Process options and update configuration
        if hasattr(options, "A") and options.A != "c":
            pc.inclusive = options.A
            if options.A == "b":
                sim_config.input_file = "/eos/experiment/ship/data/Beauty/Cascade-run0-19-parp16-MSTP82-1-MSEL5-5338Bpot.root"
            elif options.A.lower() == "charmonly":
                pc.charmonly = True
                pc.hnl_enabled = False
            elif options.A not in ["b", "c", "bc", "meson", "pbrem", "qcd"]:
                pc.inclusive = True

        # File handling
        if hasattr(options, "inputFile") and options.inputFile:
            if options.inputFile == "none":
                sim_config.input_file = None
            else:
                sim_config.input_file = options.inputFile
            sim_config.default_input_file = False

        # Physics options
        if hasattr(options, "RPVSUSY") and options.RPVSUSY:
            pc.hnl_enabled = False

        if hasattr(options, "DarkPhoton") and options.DarkPhoton:
            pc.hnl_enabled = False

        # Mass and coupling settings
        if hasattr(options, "theMass") and options.theMass:
            if hasattr(options, "DarkPhoton") and options.DarkPhoton:
                pc.dp_mass = options.theMass
            else:
                pc.hnl_mass = options.theMass

        if hasattr(options, "theDPepsilon"):
            pc.dp_epsilon = options.theDPepsilon

        # Couplings
        if hasattr(options, "thecouplings") and options.thecouplings:
            couplings = [float(c) for c in options.thecouplings.split(",")]
            pc.production_couplings = pc.decay_couplings = couplings

        if hasattr(options, "theprodcouplings") and options.theprodcouplings:
            pc.production_couplings = [
                float(c) for c in options.theprodcouplings.split(",")
            ]

        if hasattr(options, "thedeccouplings") and options.thedeccouplings:
            pc.decay_couplings = [float(c) for c in options.thedeccouplings.split(",")]

        # Runtime settings
        if hasattr(options, "nEvents"):
            runtime_config.total_events = options.nEvents

        if hasattr(options, "outputDir"):
            sim_config.output_dir = options.outputDir

        # Geometry settings
        if hasattr(options, "dy"):
            # Update the current design with custom dy
            current_design = sim_config.global_designs[sim_config.default_design].copy()
            current_design["dy"] = options.dy
            sim_config.global_designs["custom"] = current_design
            sim_config.default_design = "custom"

        if hasattr(options, "caloDesign"):
            current_design = sim_config.global_designs.get(
                "custom", sim_config.global_designs[sim_config.default_design].copy()
            )
            current_design["caloDesign"] = options.caloDesign
            sim_config.global_designs["custom"] = current_design
            sim_config.default_design = "custom"

        if hasattr(options, "strawDesign"):
            current_design = sim_config.global_designs.get(
                "custom", sim_config.global_designs[sim_config.default_design].copy()
            )
            current_design["strawDesign"] = options.strawDesign
            sim_config.global_designs["custom"] = current_design
            sim_config.default_design = "custom"

        # Test file handling
        if hasattr(options, "testFlag") and options.testFlag:
            sim_config.input_file = (
                "$FAIRSHIP/files/Cascade-parp16-MSTP82-1-MSEL4-76Mpot_1_5000.root"
            )

        # Deep copy option
        if hasattr(options, "deepCopy"):
            # This affects MC track handling, store for later use
            setattr(runtime_config, "deep_copy", options.deepCopy)

        self.simulation_config.initialized = True
        logger.info("Configuration loaded successfully from options")

    def generate_runtime_config(self, options):
        """Generate runtime-specific configuration."""
        logger.debug("Generating runtime configuration")

        runtime_config = self.runtime_config
        sim_config = self.simulation_config

        # Generate tag for file naming
        if hasattr(options, "command") and options.command == "PG":
            pID = getattr(options, "pID", 22)
            runtime_config.tag = f"PG_{pID}-{sim_config.mc_engine}"
        else:
            # Determine simulation engine from options
            engines = [
                "pythia8",
                "evtcalc",
                "pythia6",
                "genie",
                "nuradio",
                "ntuple",
                "muonback",
                "mudis",
                "fixedTarget",
                "cosmics",
            ]
            sim_engine = "Pythia8"  # default
            for engine in engines:
                if hasattr(options, engine) and getattr(options, engine):
                    sim_engine = engine.capitalize()
                    break
            sim_config.sim_engine = sim_engine
            runtime_config.tag = f"{sim_engine}-{sim_config.mc_engine}"

        # Add special modifiers to tag
        if sim_config.particle_config.charmonly:
            runtime_config.tag = (
                f"{sim_config.sim_engine}CharmOnly-{sim_config.mc_engine}"
            )

        if hasattr(options, "eventDisplay") and options.eventDisplay:
            runtime_config.tag += "_D"

        runtime_config.tag = "conical." + runtime_config.tag

        # Generate file paths
        output_dir = Path(sim_config.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        runtime_config.output_file = str(output_dir / f"ship.{runtime_config.tag}.root")
        runtime_config.parameter_file = str(
            output_dir / f"ship.params.{runtime_config.tag}.root"
        )
        runtime_config.geometry_file = str(
            output_dir / f"geofile_full.{runtime_config.tag}.root"
        )

        logger.debug(f"Generated runtime config with tag: {runtime_config.tag}")

    def validate_configuration(self) -> bool:
        """Validate the current configuration."""
        logger.debug("Validating configuration")

        sim_config = self.simulation_config
        pc = sim_config.particle_config

        # Check for conflicting physics options
        conflicting_options = sum(
            [
                pc.hnl_enabled,
                hasattr(self, "_rpvsusy_enabled") and self._rpvsusy_enabled,
                hasattr(self, "_dark_photon_enabled") and self._dark_photon_enabled,
            ]
        )

        if conflicting_options > 1:
            logger.error("Cannot have HNL, SUSY, and DP enabled simultaneously")
            return False

        # Validate file paths
        if sim_config.input_file and not sim_config.input_file.startswith("$"):
            input_path = Path(sim_config.input_file)
            if not input_path.exists():
                logger.warning(f"Input file does not exist: {sim_config.input_file}")

        # Validate couplings
        if pc.production_couplings and pc.decay_couplings:
            if len(pc.production_couplings) != len(pc.decay_couplings):
                logger.warning("Production and decay couplings have different lengths")

        logger.info("Configuration validation completed")
        return True

    def save_to_file(self, file_path: Union[str, Path], format: str = "yaml"):
        """Save configuration to file."""
        file_path = Path(file_path)

        config_dict = {
            "simulation_config": asdict(self.simulation_config),
            "runtime_config": asdict(self.runtime_config),
        }

        if format.lower() == "yaml":
            with open(file_path, "w") as f:
                yaml.dump(config_dict, f, default_flow_style=False)
        elif format.lower() == "json":
            with open(file_path, "w") as f:
                json.dump(config_dict, f, indent=2)
        else:
            raise ValueError(f"Unsupported format: {format}")

        logger.info(f"Configuration saved to {file_path}")

    def load_from_file(self, file_path: Union[str, Path]):
        """Load configuration from file."""
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")

        with open(file_path) as f:
            if file_path.suffix.lower() in [".yaml", ".yml"]:
                config_dict = yaml.safe_load(f)
            elif file_path.suffix.lower() == ".json":
                config_dict = json.load(f)
            else:
                raise ValueError(f"Unsupported file format: {file_path.suffix}")

        # Reconstruct configuration objects
        if "simulation_config" in config_dict:
            sim_dict = config_dict["simulation_config"]
            particle_dict = sim_dict.pop("particle_config", {})

            self.simulation_config = SimulationConfig(**sim_dict)
            self.simulation_config.particle_config = ParticleConfig(**particle_dict)

        if "runtime_config" in config_dict:
            self.runtime_config = RuntimeConfig(**config_dict["runtime_config"])

        logger.info(f"Configuration loaded from {file_path}")

    def get_summary(self) -> str:
        """Get a human-readable configuration summary."""
        sim_config = self.simulation_config
        runtime_config = self.runtime_config
        pc = sim_config.particle_config

        summary = ["Configuration Summary:"]
        summary.append(f"  Simulation Engine: {sim_config.sim_engine}")
        summary.append(f"  MC Engine: {sim_config.mc_engine}")
        summary.append(f"  Design: {sim_config.default_design}")
        summary.append(f"  Input File: {sim_config.input_file}")
        summary.append(f"  Output Directory: {sim_config.output_dir}")
        summary.append(f"  Total Events: {runtime_config.total_events}")

        if pc.hnl_enabled:
            summary.append(f"  HNL Mass: {pc.hnl_mass}")
            summary.append(f"  HNL Inclusive: {pc.inclusive}")

        if hasattr(self, "_dark_photon_enabled") and self._dark_photon_enabled:
            summary.append(f"  Dark Photon Mass: {pc.dp_mass}")
            summary.append(f"  Dark Photon Epsilon: {pc.dp_epsilon}")

        summary.append(f"  Using Lazy Loading: {sim_config.using_lazy_loading}")

        return "\n".join(summary)


# Global configuration manager instance
_global_config_manager = ConfigurationManager()


def get_config_manager() -> ConfigurationManager:
    """Get the global configuration manager."""
    return _global_config_manager


def initialize_configuration(options, units_module=None):
    """Initialize the global configuration system."""
    manager = get_config_manager()

    if units_module:
        manager.set_units_module(units_module)

    manager.load_from_options(options)
    manager.generate_runtime_config(options)

    if not manager.validate_configuration():
        raise RuntimeError("Configuration validation failed")

    return manager
