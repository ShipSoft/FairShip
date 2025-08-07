"""Lazy loading infrastructure for SHiP simulation modules.

This module provides sophisticated lazy loading capabilities to defer imports
until they are actually needed, reducing startup time and side effects.
"""

import contextlib
import importlib
import logging
from functools import wraps
from typing import Callable, Optional

# Set up logging for lazy loading diagnostics
logger = logging.getLogger(__name__)


class ImportTracker:
    """Tracks which modules have been imported and when."""

    def __init__(self):
        self.imported_modules: dict[str, float] = {}
        self.import_order: list[str] = []

    def record_import(self, module_name: str) -> None:
        """Record when a module was imported."""
        import time

        if module_name not in self.imported_modules:
            self.imported_modules[module_name] = time.time()
            self.import_order.append(module_name)
            logger.debug(f"Lazily imported: {module_name}")

    def get_import_summary(self) -> str:
        """Get a summary of all imports performed."""
        if not self.imported_modules:
            return "No lazy imports performed"

        summary = f"Lazy imports performed ({len(self.imported_modules)} total):\n"
        for i, module_name in enumerate(self.import_order, 1):
            timestamp = self.imported_modules[module_name]
            summary += f"  {i:2d}. {module_name} (t={timestamp:.3f})\n"
        return summary


class LazyModule:
    """A proxy object that imports a module only when accessed."""

    def __init__(self, module_name: str, tracker: ImportTracker = None):
        self._module_name = module_name
        self._module = None
        self._tracker = tracker or ImportTracker()
        self._import_error = None

    def _ensure_imported(self):
        """Ensure the module is imported."""
        if self._module is None and self._import_error is None:
            try:
                self._module = importlib.import_module(self._module_name)
                self._tracker.record_import(self._module_name)
            except ImportError as e:
                self._import_error = e
                logger.error(f"Failed to import {self._module_name}: {e}")
                raise

    def __getattr__(self, name):
        self._ensure_imported()
        return getattr(self._module, name)

    def __call__(self, *args, **kwargs):
        self._ensure_imported()
        return self._module(*args, **kwargs)

    @property
    def is_imported(self) -> bool:
        """Check if the module has been imported."""
        return self._module is not None


class ModuleLoader:
    """Central module loader with conditional loading capabilities."""

    def __init__(self):
        self.tracker = ImportTracker()
        self._loaded_modules: dict[str, LazyModule] = {}
        self._loading_conditions: dict[str, Callable[[], bool]] = {}

    def register_module(
        self,
        name: str,
        module_name: str,
        condition: Optional[Callable[[], bool]] = None,
    ) -> LazyModule:
        """Register a module for lazy loading."""
        if name not in self._loaded_modules:
            lazy_module = LazyModule(module_name, self.tracker)
            self._loaded_modules[name] = lazy_module
            if condition:
                self._loading_conditions[name] = condition
        return self._loaded_modules[name]

    def get_module(self, name: str) -> LazyModule:
        """Get a registered module."""
        if name not in self._loaded_modules:
            raise KeyError(f"Module {name} not registered")

        # Check loading condition if present
        if name in self._loading_conditions:
            condition = self._loading_conditions[name]
            if not condition():
                raise RuntimeError(f"Loading condition not met for module {name}")

        return self._loaded_modules[name]

    def preload_modules(self, module_names: list[str]) -> None:
        """Preload specific modules."""
        for name in module_names:
            if name in self._loaded_modules:
                try:
                    self._loaded_modules[name]._ensure_imported()
                except ImportError as e:
                    logger.warning(f"Failed to preload {name}: {e}")

    def get_import_summary(self) -> str:
        """Get summary of all lazy imports."""
        return self.tracker.get_import_summary()


class SimulationModuleLoader(ModuleLoader):
    """Specialized module loader for SHiP simulation modules."""

    def __init__(self, options=None):
        super().__init__()
        self.options = options
        self._setup_simulation_modules()

    def _setup_simulation_modules(self):
        """Set up all simulation modules with their loading conditions."""
        # Core modules - always available
        self.register_module("ROOT", "ROOT")
        self.register_module("shipunit", "shipunit")
        self.register_module("rootUtils", "rootUtils")
        self.register_module("shipRoot_conf", "shipRoot_conf")

        # Geometry and configuration modules
        self.register_module("ShipGeoConfig", "ShipGeoConfig")

        # Generator-specific modules with conditions
        self.register_module(
            "pythia8_conf", "pythia8_conf", condition=lambda: self._is_pythia8_needed()
        )

        self.register_module(
            "pythia8darkphoton_conf",
            "pythia8darkphoton_conf",
            condition=lambda: self.options
            and getattr(self.options, "DarkPhoton", False),
        )

        self.register_module(
            "CMBG_conf",
            "CMBG_conf",
            condition=lambda: self.options and getattr(self.options, "cosmics", False),
        )

        # Detector and geometry modules
        self.register_module("shipDet_conf", "shipDet_conf")

        self.register_module(
            "geomGeant4", "geomGeant4", condition=lambda: self._is_geometry_needed()
        )

        # Utility modules
        self.register_module("saveBasicParameters", "saveBasicParameters")
        self.register_module("checkMagFields", "checkMagFields")

    def _is_pythia8_needed(self) -> bool:
        """Check if Pythia8 modules are needed."""
        if not self.options:
            return True  # Default to allowing import
        return getattr(self.options, "pythia8", False)

    def _is_geometry_needed(self) -> bool:
        """Check if geometry modules are needed."""
        if not self.options:
            return True  # Default to allowing import
        # Geometry is needed unless it's a dry run
        return not getattr(self.options, "dryrun", False)

    def update_options(self, options):
        """Update the options used for conditional loading."""
        self.options = options


@contextlib.contextmanager
def controlled_import_context(modules_to_load: list[str] = None):
    """Context manager for controlling when imports happen."""
    loader = ModuleLoader()

    # Register and preload specified modules
    if modules_to_load:
        for module_name in modules_to_load:
            loader.register_module(module_name, module_name)
        loader.preload_modules(modules_to_load)

    try:
        yield loader
    finally:
        # Log import summary
        summary = loader.get_import_summary()
        logger.info(f"Import context completed:\n{summary}")


def lazy_import_decorator(module_dependencies: list[str]):
    """Ensure required modules are loaded before function execution."""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create a temporary loader for this function
            with controlled_import_context(module_dependencies) as loader:  # noqa: F841
                return func(*args, **kwargs)

        return wrapper

    return decorator


class ImportManager:
    """High-level import manager for the simulation script."""

    def __init__(self):
        self.loader = None
        self.is_initialized = False

    def initialize(self, options=None):
        """Initialize the import manager with runtime options."""
        self.loader = SimulationModuleLoader(options)
        self.is_initialized = True
        logger.info("Import manager initialized")

    def get_module(self, name: str):
        """Get a module through the lazy loading system."""
        if not self.is_initialized:
            raise RuntimeError(
                "ImportManager not initialized. Call initialize() first."
            )
        return self.loader.get_module(name)

    def update_options(self, options):
        """Update the options for conditional loading."""
        if self.loader:
            self.loader.update_options(options)

    def get_import_summary(self) -> str:
        """Get a summary of all imports performed."""
        if self.loader:
            return self.loader.get_import_summary()
        return "Import manager not initialized"


# Global import manager instance
_global_import_manager = ImportManager()


def get_import_manager() -> ImportManager:
    """Get the global import manager instance."""
    return _global_import_manager


def setup_lazy_imports(options=None):
    """Set up lazy imports for the simulation script."""
    manager = get_import_manager()
    manager.initialize(options)
    return manager
