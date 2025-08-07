"""
Simulation configurators to replace direct imports of configuration modules.

This module provides configurator classes that encapsulate the functionality
of various *_conf modules, allowing for better dependency injection and
reduced side effects during imports.
"""

import os
import ROOT
import shipunit as u


class PythiaConfigurator:
    """Configurator for Pythia8 generators, replacing pythia8_conf imports."""
    
    def __init__(self):
        self._pythia8_conf = None
        self._pythia8darkphoton_conf = None
    
    def _import_pythia8_conf(self):
        """Lazy import of pythia8_conf module."""
        if self._pythia8_conf is None:
            import pythia8_conf
            self._pythia8_conf = pythia8_conf
        return self._pythia8_conf
    
    def _import_pythia8darkphoton_conf(self):
        """Lazy import of pythia8darkphoton_conf module."""
        if self._pythia8darkphoton_conf is None:
            import pythia8darkphoton_conf
            self._pythia8darkphoton_conf = pythia8darkphoton_conf
        return self._pythia8darkphoton_conf
    
    def configure_hnl(self, P8gen, mass, production_couplings, decay_couplings, 
                      inclusive, deep_copy=False):
        """Configure Pythia8 for HNL production."""
        conf = self._import_pythia8_conf()
        return conf.configure(P8gen, mass, production_couplings, decay_couplings, 
                             inclusive, deep_copy)
    
    def configure_rpvsusy(self, P8gen, mass, couplings, sfermionmass, benchmark, 
                          inclusive, deep_copy=False, debug=True):
        """Configure Pythia8 for RPV SUSY production."""
        conf = self._import_pythia8_conf()
        return conf.configurerpvsusy(P8gen, mass, couplings, sfermionmass, 
                                    benchmark, inclusive, deep_copy, debug)
    
    def configure_dark_photon(self, P8gen, mass, epsilon, inclusive, mother_mode, 
                             deep_copy=False, debug=True):
        """Configure Pythia8 for dark photon production."""
        conf = self._import_pythia8darkphoton_conf()
        return conf.configure(P8gen, mass, epsilon, inclusive, mother_mode, 
                             deep_copy, debug)


class DetectorConfigurator:
    """Configurator for detector setup, replacing shipDet_conf imports."""
    
    def __init__(self):
        self._shipDet_conf = None
    
    def _import_shipDet_conf(self):
        """Lazy import of shipDet_conf module."""
        if self._shipDet_conf is None:
            import shipDet_conf
            self._shipDet_conf = shipDet_conf
        return self._shipDet_conf
    
    def configure(self, run, ship_geo):
        """Configure detector modules."""
        conf = self._import_shipDet_conf()
        return conf.configure(run, ship_geo)
    
    def configure_snd_old(self, yaml_file, emulsion_target_z_end, 
                         cave_floorHeightMuonShield):
        """Configure SND old detector."""
        conf = self._import_shipDet_conf()
        return conf.configure_snd_old(yaml_file, emulsion_target_z_end, 
                                     cave_floorHeightMuonShield)
    
    def configure_snd_mtc(self, yaml_file, ship_geo):
        """Configure SND MTC detector."""
        conf = self._import_shipDet_conf()
        return conf.configure_snd_mtc(yaml_file, ship_geo)
    
    def configure_veto(self, yaml_file, z0):
        """Configure veto detector."""
        conf = self._import_shipDet_conf()
        return conf.configure_veto(yaml_file, z0)


class GeometryConfigurator:
    """Configurator for geometry setup, replacing geomGeant4 imports."""
    
    def __init__(self):
        self._geomGeant4 = None
    
    def _import_geomGeant4(self):
        """Lazy import of geomGeant4 module."""
        if self._geomGeant4 is None:
            import geomGeant4
            self._geomGeant4 = geomGeant4
        return self._geomGeant4
    
    def add_vmc_fields(self, ship_geo, verbose=True):
        """Add VMC fields to geometry."""
        geom = self._import_geomGeant4()
        return geom.addVMCFields(ship_geo, verbose=verbose)
    
    def print_vmc_fields(self):
        """Print VMC fields information."""
        geom = self._import_geomGeant4()
        return geom.printVMCFields()
    
    def print_weights_and_fields(self, only_with_field=True, exclude=None):
        """Print weights and fields information."""
        geom = self._import_geomGeant4()
        if exclude is None:
            exclude = ['DecayVolume','Tr1','Tr2','Tr3','Tr4','Veto',
                      'Ecal','Hcal','MuonDetector','SplitCal']
        return geom.printWeightsandFields(onlyWithField=only_with_field, 
                                        exclude=exclude)


class CosmicsConfigurator:
    """Configurator for cosmic background, replacing CMBG_conf imports."""
    
    def __init__(self):
        self._CMBG_conf = None
    
    def _import_CMBG_conf(self):
        """Lazy import of CMBG_conf module."""
        if self._CMBG_conf is None:
            import CMBG_conf
            self._CMBG_conf = CMBG_conf
        return self._CMBG_conf
    
    def configure(self, cmbg_gen, ship_geo):
        """Configure cosmic background generator."""
        conf = self._import_CMBG_conf()
        return conf.configure(cmbg_gen, ship_geo)


class UtilityConfigurator:
    """Configurator for utility modules."""
    
    def __init__(self):
        self._saveBasicParameters = None
        self._checkMagFields = None
    
    def _import_saveBasicParameters(self):
        """Lazy import of saveBasicParameters module."""
        if self._saveBasicParameters is None:
            import saveBasicParameters
            self._saveBasicParameters = saveBasicParameters
        return self._saveBasicParameters
    
    def _import_checkMagFields(self):
        """Lazy import of checkMagFields module."""
        if self._checkMagFields is None:
            import checkMagFields
            self._checkMagFields = checkMagFields
        return self._checkMagFields
    
    def save_basic_parameters(self, filename, ship_geo):
        """Save basic parameters to file."""
        util = self._import_saveBasicParameters()
        return util.execute(filename, ship_geo)
    
    def visualize_mag_fields(self):
        """Visualize magnetic fields."""
        util = self._import_checkMagFields()
        return util.run()


class SimulationConfiguratorFactory:
    """Factory for creating simulation configurators."""
    
    @staticmethod
    def create_pythia_configurator():
        """Create a Pythia configurator."""
        return PythiaConfigurator()
    
    @staticmethod
    def create_detector_configurator():
        """Create a detector configurator."""
        return DetectorConfigurator()
    
    @staticmethod
    def create_geometry_configurator():
        """Create a geometry configurator."""
        return GeometryConfigurator()
    
    @staticmethod
    def create_cosmics_configurator():
        """Create a cosmics configurator."""
        return CosmicsConfigurator()
    
    @staticmethod
    def create_utility_configurator():
        """Create a utility configurator."""
        return UtilityConfigurator()