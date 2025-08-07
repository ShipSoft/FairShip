"""ROOT and library initialization module.

This module provides controlled initialization of ROOT and related libraries,
replacing the side effects that previously happened during import.
"""

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


class ROOTInitializer:
    """Manages ROOT initialization with controlled side effects."""

    def __init__(self):
        self.is_initialized = False
        self.root_module: Optional[Any] = None
        self.initialization_config: dict[str, Any] = {}

    def initialize(self, seed: int = 0, config_level: int = 0) -> Any:
        """Initialize ROOT with controlled settings.

        Args:
            seed: Random seed for ROOT
            config_level: Configuration level (0 = basic)

        Returns:
            ROOT module reference

        """
        if self.is_initialized:
            logger.debug("ROOT already initialized")
            return self.root_module

        logger.info("Initializing ROOT...")

        try:
            # Import ROOT module
            import ROOT

            self.root_module = ROOT

            # Set random seed
            if seed != 0:
                ROOT.gRandom.SetSeed(seed)
                logger.debug(f"Set ROOT random seed to {seed}")
                self.initialization_config["seed"] = seed

            # Initialize shipRoot_conf if needed
            if config_level >= 0:
                self._initialize_ship_root_conf(config_level)

            self.is_initialized = True
            logger.info("ROOT initialization completed successfully")

            return self.root_module

        except ImportError as e:
            logger.error(f"Failed to import ROOT: {e}")
            raise
        except Exception as e:
            logger.error(f"ROOT initialization failed: {e}")
            raise

    def _initialize_ship_root_conf(self, config_level: int):
        """Initialize shipRoot_conf with controlled side effects."""
        try:
            import shipRoot_conf

            shipRoot_conf.configure(config_level)
            logger.debug(f"shipRoot_conf configured with level {config_level}")
            self.initialization_config["shipRoot_conf_level"] = config_level
        except ImportError:
            logger.warning("shipRoot_conf not available, skipping")
        except Exception as e:
            logger.warning(f"shipRoot_conf configuration failed: {e}")

    def get_initialization_summary(self) -> str:
        """Get a summary of the initialization performed."""
        if not self.is_initialized:
            return "ROOT not initialized"

        summary = ["ROOT Initialization Summary:"]
        summary.append(
            f"  Status: {'Initialized' if self.is_initialized else 'Not initialized'}"
        )

        for key, value in self.initialization_config.items():
            summary.append(f"  {key}: {value}")

        return "\n".join(summary)


class LibraryManager:
    """Manages loading of additional libraries."""

    def __init__(self):
        self.loaded_libraries: dict[str, bool] = {}
        self.root_initializer = ROOTInitializer()

    def ensure_root(self, **kwargs) -> Any:
        """Ensure ROOT is initialized."""
        return self.root_initializer.initialize(**kwargs)

    def load_library(self, library_name: str, required: bool = True) -> bool:
        """Load a ROOT library.

        Args:
            library_name: Name of the library to load
            required: Whether the library is required (raises on failure if True)

        Returns:
            True if loaded successfully, False otherwise

        """
        if library_name in self.loaded_libraries:
            return self.loaded_libraries[library_name]

        ROOT = self.ensure_root()

        try:
            result = ROOT.gSystem.Load(library_name)
            success = result == 0

            if success:
                logger.debug(f"Successfully loaded library: {library_name}")
            else:
                logger.warning(
                    f"Failed to load library {library_name} (result: {result})"
                )
                if required:
                    raise RuntimeError(
                        f"Required library {library_name} failed to load"
                    )

            self.loaded_libraries[library_name] = success
            return success

        except Exception as e:
            logger.error(f"Error loading library {library_name}: {e}")
            self.loaded_libraries[library_name] = False
            if required:
                raise
            return False

    def load_ship_libraries(self) -> dict[str, bool]:
        """Load standard SHiP libraries."""
        logger.info("Loading SHiP libraries...")

        # Standard SHiP libraries that might be needed
        ship_libraries = [
            "libShipPassive",
            "libShipField",
            "libveto",
            "libstrawtubes",
            "libecal",
            "libhcal",
            "libmuon",
            "libpid",
        ]

        results = {}
        for lib in ship_libraries:
            try:
                results[lib] = self.load_library(lib, required=False)
            except Exception as e:
                logger.debug(f"Optional library {lib} not loaded: {e}")
                results[lib] = False

        successful = sum(results.values())
        total = len(results)
        logger.info(f"Loaded {successful}/{total} SHiP libraries")

        return results

    def get_library_summary(self) -> str:
        """Get a summary of loaded libraries."""
        if not self.loaded_libraries:
            return "No libraries loaded"

        summary = ["Loaded Libraries:"]
        for lib, success in self.loaded_libraries.items():
            status = "✓" if success else "✗"
            summary.append(f"  {status} {lib}")

        return "\n".join(summary)


class InitializationManager:
    """High-level initialization manager."""

    def __init__(self):
        self.library_manager = LibraryManager()
        self.is_fully_initialized = False

    def initialize_simulation_environment(
        self, seed: int = 0, load_ship_libs: bool = True, config_level: int = 0
    ) -> dict[str, Any]:
        """Initialize the complete simulation environment.

        Args:
            seed: Random seed for ROOT
            load_ship_libs: Whether to load SHiP libraries
            config_level: Configuration level for shipRoot_conf

        Returns:
            Dictionary with initialized modules and status

        """
        logger.info("Initializing simulation environment...")

        try:
            # Initialize ROOT
            ROOT = self.library_manager.ensure_root(
                seed=seed, config_level=config_level
            )

            # Load SHiP libraries if requested
            library_results = {}
            if load_ship_libs:
                library_results = self.library_manager.load_ship_libraries()

            self.is_fully_initialized = True

            result = {
                "ROOT": ROOT,
                "libraries": library_results,
                "initialization_status": "success",
            }

            logger.info("Simulation environment initialized successfully")
            return result

        except Exception as e:
            logger.error(f"Simulation environment initialization failed: {e}")
            return {
                "ROOT": None,
                "libraries": {},
                "initialization_status": "failed",
                "error": str(e),
            }

    def get_full_summary(self) -> str:
        """Get complete initialization summary."""
        summary = ["Simulation Environment Initialization:"]
        summary.append(
            f"  Status: {'Fully Initialized' if self.is_fully_initialized else 'Not Initialized'}"
        )
        summary.append("")
        summary.append(
            self.library_manager.root_initializer.get_initialization_summary()
        )
        summary.append("")
        summary.append(self.library_manager.get_library_summary())

        return "\n".join(summary)


# Global initialization manager
_global_init_manager = InitializationManager()


def get_initialization_manager() -> InitializationManager:
    """Get the global initialization manager."""
    return _global_init_manager


def initialize_simulation_environment(**kwargs):
    """Initialize the simulation environment."""
    manager = get_initialization_manager()
    return manager.initialize_simulation_environment(**kwargs)
