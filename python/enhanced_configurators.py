"""
Enhanced simulation configurators with lazy loading integration.

This module extends the basic configurators with lazy loading capabilities
and better integration with the import management system.
"""

from lazy_loading import get_import_manager, lazy_import_decorator
from simulation_configurators import (
    PythiaConfigurator as BasicPythiaConfigurator,
    DetectorConfigurator as BasicDetectorConfigurator,
    GeometryConfigurator as BasicGeometryConfigurator,
    CosmicsConfigurator as BasicCosmicsConfigurator,
    UtilityConfigurator as BasicUtilityConfigurator
)
import logging

logger = logging.getLogger(__name__)


class LazyPythiaConfigurator:
    """Enhanced Pythia configurator with lazy loading."""
    
    def __init__(self):
        self._import_manager = get_import_manager()
    
    @lazy_import_decorator(['pythia8_conf'])
    def configure_hnl(self, P8gen, mass, production_couplings, decay_couplings, 
                      inclusive, deep_copy=False):
        """Configure Pythia8 for HNL production with lazy loading."""
        logger.debug("Configuring HNL with lazy-loaded pythia8_conf")
        pythia8_conf = self._import_manager.get_module('pythia8_conf')
        return pythia8_conf.configure(P8gen, mass, production_couplings, 
                                    decay_couplings, inclusive, deep_copy)
    
    @lazy_import_decorator(['pythia8_conf'])
    def configure_rpvsusy(self, P8gen, mass, couplings, sfermionmass, benchmark, 
                          inclusive, deep_copy=False, debug=True):
        """Configure Pythia8 for RPV SUSY production with lazy loading."""
        logger.debug("Configuring RPV SUSY with lazy-loaded pythia8_conf")
        pythia8_conf = self._import_manager.get_module('pythia8_conf')
        return pythia8_conf.configurerpvsusy(P8gen, mass, couplings, sfermionmass, 
                                           benchmark, inclusive, deep_copy, debug)
    
    @lazy_import_decorator(['pythia8darkphoton_conf'])
    def configure_dark_photon(self, P8gen, mass, epsilon, inclusive, mother_mode, 
                             deep_copy=False, debug=True):
        """Configure Pythia8 for dark photon production with lazy loading."""
        logger.debug("Configuring dark photon with lazy-loaded pythia8darkphoton_conf")
        pythia8darkphoton_conf = self._import_manager.get_module('pythia8darkphoton_conf')
        return pythia8darkphoton_conf.configure(P8gen, mass, epsilon, inclusive, 
                                              mother_mode, deep_copy, debug)


class LazyDetectorConfigurator:
    """Enhanced detector configurator with lazy loading."""
    
    def __init__(self):
        self._import_manager = get_import_manager()
    
    @lazy_import_decorator(['shipDet_conf'])
    def configure(self, run, ship_geo):
        """Configure detector modules with lazy loading."""
        logger.debug("Configuring detectors with lazy-loaded shipDet_conf")
        shipDet_conf = self._import_manager.get_module('shipDet_conf')
        return shipDet_conf.configure(run, ship_geo)
    
    @lazy_import_decorator(['shipDet_conf'])
    def configure_snd_old(self, yaml_file, emulsion_target_z_end, 
                         cave_floorHeightMuonShield):
        """Configure SND old detector with lazy loading."""
        shipDet_conf = self._import_manager.get_module('shipDet_conf')
        return shipDet_conf.configure_snd_old(yaml_file, emulsion_target_z_end, 
                                            cave_floorHeightMuonShield)
    
    @lazy_import_decorator(['shipDet_conf'])
    def configure_snd_mtc(self, yaml_file, ship_geo):
        """Configure SND MTC detector with lazy loading."""
        shipDet_conf = self._import_manager.get_module('shipDet_conf')
        return shipDet_conf.configure_snd_mtc(yaml_file, ship_geo)
    
    @lazy_import_decorator(['shipDet_conf'])
    def configure_veto(self, yaml_file, z0):
        """Configure veto detector with lazy loading."""
        shipDet_conf = self._import_manager.get_module('shipDet_conf')
        return shipDet_conf.configure_veto(yaml_file, z0)


class LazyGeometryConfigurator:
    """Enhanced geometry configurator with lazy loading."""
    
    def __init__(self):
        self._import_manager = get_import_manager()
    
    @lazy_import_decorator(['geomGeant4'])
    def add_vmc_fields(self, ship_geo, verbose=True):
        """Add VMC fields to geometry with lazy loading."""
        logger.debug("Adding VMC fields with lazy-loaded geomGeant4")
        geomGeant4 = self._import_manager.get_module('geomGeant4')
        return geomGeant4.addVMCFields(ship_geo, verbose=verbose)
    
    @lazy_import_decorator(['geomGeant4'])
    def print_vmc_fields(self):
        """Print VMC fields information with lazy loading."""
        geomGeant4 = self._import_manager.get_module('geomGeant4')
        return geomGeant4.printVMCFields()
    
    @lazy_import_decorator(['geomGeant4'])
    def print_weights_and_fields(self, only_with_field=True, exclude=None):
        """Print weights and fields information with lazy loading."""
        geomGeant4 = self._import_manager.get_module('geomGeant4')
        if exclude is None:
            exclude = ['DecayVolume','Tr1','Tr2','Tr3','Tr4','Veto',
                      'Ecal','Hcal','MuonDetector','SplitCal']
        return geomGeant4.printWeightsandFields(onlyWithField=only_with_field, 
                                              exclude=exclude)


class LazyCosmicsConfigurator:
    """Enhanced cosmics configurator with lazy loading."""
    
    def __init__(self):
        self._import_manager = get_import_manager()
    
    @lazy_import_decorator(['CMBG_conf'])
    def configure(self, cmbg_gen, ship_geo):
        """Configure cosmic background generator with lazy loading."""
        logger.debug("Configuring cosmics with lazy-loaded CMBG_conf")
        CMBG_conf = self._import_manager.get_module('CMBG_conf')
        return CMBG_conf.configure(cmbg_gen, ship_geo)


class LazyUtilityConfigurator:
    """Enhanced utility configurator with lazy loading."""
    
    def __init__(self):
        self._import_manager = get_import_manager()
    
    @lazy_import_decorator(['saveBasicParameters'])
    def save_basic_parameters(self, filename, ship_geo):
        """Save basic parameters to file with lazy loading."""
        logger.debug("Saving basic parameters with lazy-loaded saveBasicParameters")
        saveBasicParameters = self._import_manager.get_module('saveBasicParameters')
        return saveBasicParameters.execute(filename, ship_geo)
    
    @lazy_import_decorator(['checkMagFields'])
    def visualize_mag_fields(self):
        """Visualize magnetic fields with lazy loading."""
        logger.debug("Visualizing magnetic fields with lazy-loaded checkMagFields")
        checkMagFields = self._import_manager.get_module('checkMagFields')
        return checkMagFields.run()


class EnhancedSimulationConfiguratorFactory:
    """Factory for creating enhanced configurators with lazy loading."""
    
    @staticmethod
    def create_pythia_configurator():
        """Create a lazy Pythia configurator."""
        return LazyPythiaConfigurator()
    
    @staticmethod
    def create_detector_configurator():
        """Create a lazy detector configurator."""
        return LazyDetectorConfigurator()
    
    @staticmethod
    def create_geometry_configurator():
        """Create a lazy geometry configurator."""
        return LazyGeometryConfigurator()
    
    @staticmethod
    def create_cosmics_configurator():
        """Create a lazy cosmics configurator."""
        return LazyCosmicsConfigurator()
    
    @staticmethod
    def create_utility_configurator():
        """Create a lazy utility configurator."""
        return LazyUtilityConfigurator()
    
    @staticmethod
    def create_all_configurators():
        """Create all configurators as a convenient bundle."""
        return {
            'pythia': EnhancedSimulationConfiguratorFactory.create_pythia_configurator(),
            'detector': EnhancedSimulationConfiguratorFactory.create_detector_configurator(),
            'geometry': EnhancedSimulationConfiguratorFactory.create_geometry_configurator(),
            'cosmics': EnhancedSimulationConfiguratorFactory.create_cosmics_configurator(),
            'utility': EnhancedSimulationConfiguratorFactory.create_utility_configurator()
        }


# Compatibility layer - allows using the same interface as basic configurators
SimulationConfiguratorFactory = EnhancedSimulationConfiguratorFactory