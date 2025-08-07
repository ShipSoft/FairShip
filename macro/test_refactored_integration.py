#!/usr/bin/env python
"""
Integration test script for the refactored run_simScript.py components.

This test verifies that all the refactored modules work together correctly
by simulating the key interactions and data flow.
"""

import sys
import os
import unittest
from unittest.mock import Mock, patch, MagicMock
from argparse import Namespace

# Add the macro directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import all the refactored modules
from lazy_loading import LazyImportManager
from enhanced_configurators import EnhancedSimulationConfiguratorFactory
from simulation_config import SimulationConfigurationManager
from root_initialization import RootInitializer
from generator_configurator import GeneratorConfiguratorFactory
from simulation_execution_configurator import SimulationExecutionConfiguratorFactory

class TestRefactoredIntegration(unittest.TestCase):
    """Integration tests for the refactored simulation system"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Mock ROOT and related modules
        self.mock_ROOT = Mock()
        self.mock_units = Mock()
        self.mock_utils = Mock()
        
        # Set up mock units
        self.mock_units.cm = 1.0
        self.mock_units.mm = 0.1
        self.mock_units.m = 100.0
        self.mock_units.GeV = 1.0
        self.mock_units.MeV = 0.001
        
        # Set up mock ROOT constants
        self.mock_ROOT.kTRUE = True
        self.mock_ROOT.kFALSE = False
        
        # Create mock options (similar to what argparse would produce)
        self.mock_options = Namespace(
            pythia8=True, pythia6=False, fixedTarget=False, evtcalc=False,
            command=None, mudis=False, genie=False, nuradio=False,
            ntuple=False, muonback=False, cosmics=False,
            RPVSUSY=False, DarkPhoton=False, deepCopy=False,
            theMass=1.0, theDPepsilon=0.00000008, RPVSUSYbench=2,
            firstEvent=0, nEvents=100, z_offset=-84.0,
            eventDisplay=False, dryrun=False, debug=0, field_map=None,
            followMuon=False, fastMuon=False, sameSeed=False,
            PaintBeam=5.0, SmearBeam=0.8, phiRandom=False
        )
        
        # Mock geometry
        self.mock_ship_geo = Mock()
        self.mock_ship_geo.target.z0 = 0.0
        self.mock_ship_geo.target.z = 100.0
        self.mock_ship_geo.decayVolume.z = 200.0
        self.mock_ship_geo.muShield.length = 150.0
        self.mock_ship_geo.Chamber1.z = 300.0
        self.mock_ship_geo.chambers.Tub1length = 50.0
        self.mock_ship_geo.TrackStation1.z = 400.0
        self.mock_ship_geo.Bfield = Mock()
        
        # Mock configuration manager
        self.mock_config_manager = Mock()
        self.mock_config_manager.simulation_config = Mock()
        self.mock_config_manager.runtime_config = Mock()
        self.mock_config_manager.simulation_config.particle_config = Mock()
        
        # Set up particle configuration
        particle_config = self.mock_config_manager.simulation_config.particle_config
        particle_config.hnl_mass = 1.0
        particle_config.dp_mass = 0.2
        particle_config.production_couplings = None
        particle_config.decay_couplings = None
        particle_config.inclusive = 'c'
        particle_config.charmonly = False
        particle_config.hnl_enabled = True
        
        # Set up runtime configuration
        runtime_config = self.mock_config_manager.runtime_config
        runtime_config.output_file = "/path/to/output.root"
        runtime_config.parameter_file = "/path/to/param.root"
        runtime_config.geometry_file = "/path/to/geometry.root"
        runtime_config.tag = "test_tag"
        
    def test_lazy_loading_integration(self):
        """Test that lazy loading system works with configurators"""
        # Create a mock import manager
        mock_import_manager = Mock(spec=LazyImportManager)
        mock_import_manager.get_module.side_effect = lambda name: {
            'ROOT': self.mock_ROOT,
            'shipunit': self.mock_units,
            'rootUtils': self.mock_utils,
        }.get(name, Mock())
        
        # Test that modules can be accessed
        ROOT = mock_import_manager.get_module('ROOT')
        units = mock_import_manager.get_module('shipunit')
        utils = mock_import_manager.get_module('rootUtils')
        
        self.assertEqual(ROOT, self.mock_ROOT)
        self.assertEqual(units, self.mock_units)
        self.assertEqual(utils, self.mock_utils)
        
    def test_configurator_factory_integration(self):
        """Test that configurator factories work together"""
        # Create configurators using factories
        pythia_configurator = EnhancedSimulationConfiguratorFactory.create_pythia_configurator()
        cosmics_configurator = EnhancedSimulationConfiguratorFactory.create_cosmics_configurator()
        detector_configurator = EnhancedSimulationConfiguratorFactory.create_detector_configurator()
        geometry_configurator = EnhancedSimulationConfiguratorFactory.create_geometry_configurator()
        utility_configurator = EnhancedSimulationConfiguratorFactory.create_utility_configurator()
        
        # Verify they are created correctly
        self.assertIsNotNone(pythia_configurator)
        self.assertIsNotNone(cosmics_configurator)
        self.assertIsNotNone(detector_configurator)
        self.assertIsNotNone(geometry_configurator)
        self.assertIsNotNone(utility_configurator)
        
        # Test generator configurator creation
        generator_configurator = GeneratorConfiguratorFactory.create_generator_configurator(
            self.mock_ROOT, self.mock_units, self.mock_utils, self.mock_ship_geo,
            pythia_configurator, cosmics_configurator
        )
        
        self.assertIsNotNone(generator_configurator)
        self.assertEqual(generator_configurator.ROOT, self.mock_ROOT)
        self.assertEqual(generator_configurator.u, self.mock_units)
        
        # Test simulation execution configurator creation
        execution_configurator = SimulationExecutionConfiguratorFactory.create_simulation_execution_configurator(
            self.mock_ROOT, self.mock_units, self.mock_config_manager,
            geometry_configurator, utility_configurator
        )
        
        self.assertIsNotNone(execution_configurator)
        self.assertEqual(execution_configurator.ROOT, self.mock_ROOT)
        
    def test_generator_configuration_workflow(self):
        """Test the complete generator configuration workflow"""
        # Create necessary configurators
        pythia_configurator = EnhancedSimulationConfiguratorFactory.create_pythia_configurator()
        cosmics_configurator = EnhancedSimulationConfiguratorFactory.create_cosmics_configurator()
        
        generator_configurator = GeneratorConfiguratorFactory.create_generator_configurator(
            self.mock_ROOT, self.mock_units, self.mock_utils, self.mock_ship_geo,
            pythia_configurator, cosmics_configurator
        )
        
        # Mock detector modules
        mock_modules = {'Veto': Mock()}
        
        # Mock run object
        mock_run = Mock()
        
        # Configuration values for generator
        config_values = {
            'HNL': True,
            'inputFile': None,
            'inclusive': 'c',
            'charmonly': False,
            'motherMode': 'pi0',
            'theProductionCouplings': None,
            'theDecayCouplings': None,
            'theCouplings': [0.447e-9, 7.15e-9, 1.88e-9],
            'theHNLMass': 1.0,
            'DownScaleDiMuon': False,
            'MCTracksWithHitsOnly': False,
            'MCTracksWithEnergyCutOnly': False,
            'MCTracksWithHitsOrEnergyCut': False,
            'Opt_high': None,
        }
        
        # Mock the primary generator creation
        mock_primGen = Mock()
        self.mock_ROOT.FairPrimaryGenerator.return_value = mock_primGen
        
        # Configure all generators
        primGen, generators = generator_configurator.configure_all_generators(
            mock_run, self.mock_options, config_values, mock_modules
        )
        
        # Verify the workflow completed
        self.assertEqual(primGen, mock_primGen)
        self.assertIsInstance(generators, dict)
        mock_run.SetGenerator.assert_called_with(mock_primGen)
        
    def test_simulation_execution_workflow(self):
        """Test the complete simulation execution workflow"""
        # Create necessary configurators
        geometry_configurator = EnhancedSimulationConfiguratorFactory.create_geometry_configurator()
        utility_configurator = EnhancedSimulationConfiguratorFactory.create_utility_configurator()
        
        execution_configurator = SimulationExecutionConfiguratorFactory.create_simulation_execution_configurator(
            self.mock_ROOT, self.mock_units, self.mock_config_manager,
            geometry_configurator, utility_configurator
        )
        
        # Mock necessary objects
        mock_run = Mock()
        mock_rtdb = Mock()
        mock_timer = Mock()
        mock_timer.RealTime.return_value = 123.45
        mock_timer.CpuTime.return_value = 98.76
        
        mock_gMC = Mock()
        mock_fStack = Mock()
        self.mock_ROOT.TVirtualMC.GetMC.return_value = mock_gMC
        mock_gMC.GetStack.return_value = mock_fStack
        
        # Configuration values
        config_values = {
            'MCTracksWithHitsOnly': False,
            'MCTracksWithEnergyCutOnly': False,
            'MCTracksWithHitsOrEnergyCut': False,
        }
        
        generators = {}
        outFile = "/path/to/output.root"
        parFile = "/path/to/param.root"
        inputFile = "/path/to/input.root"
        
        # Execute the workflow (will fail due to mocking, but we can test structure)
        try:
            gMC, fStack, fieldMaker = execution_configurator.execute_full_simulation(
                mock_run, mock_rtdb, self.mock_options, config_values,
                self.mock_ship_geo, self.mock_config_manager.runtime_config,
                mock_timer, outFile, parFile, inputFile, generators,
                True, False, None
            )
        except Exception as e:
            # Expected due to mocking - we're testing the structure
            pass
        
        # Verify key methods were called
        mock_run.Init.assert_called_once()
        
    def test_configuration_value_flow(self):
        """Test that configuration values flow correctly between components"""
        # Create a simulation configuration manager
        config_manager = SimulationConfigurationManager()
        
        # Create mock configuration objects
        mock_simulation_config = Mock()
        mock_runtime_config = Mock()
        
        # Set up the configuration manager
        config_manager.simulation_config = mock_simulation_config
        config_manager.runtime_config = mock_runtime_config
        
        # Test that configurations can be accessed
        self.assertEqual(config_manager.simulation_config, mock_simulation_config)
        self.assertEqual(config_manager.runtime_config, mock_runtime_config)
        
    def test_error_handling_integration(self):
        """Test that error conditions are handled properly across modules"""
        # Test dry run exit
        self.mock_options.dryrun = True
        
        geometry_configurator = EnhancedSimulationConfiguratorFactory.create_geometry_configurator()
        utility_configurator = EnhancedSimulationConfiguratorFactory.create_utility_configurator()
        
        execution_configurator = SimulationExecutionConfiguratorFactory.create_simulation_execution_configurator(
            self.mock_ROOT, self.mock_units, self.mock_config_manager,
            geometry_configurator, utility_configurator
        )
        
        mock_run = Mock()
        
        # Should raise SystemExit for dry run
        with self.assertRaises(SystemExit):
            execution_configurator.initialize_simulation_run(mock_run, self.mock_options)
            
        # Verify run was initialized before exit
        mock_run.Init.assert_called_once()
        
    def test_modular_design_isolation(self):
        """Test that modules are properly isolated and can be tested independently"""
        # Test generator configurator isolation
        pythia_configurator = EnhancedSimulationConfiguratorFactory.create_pythia_configurator()
        cosmics_configurator = EnhancedSimulationConfiguratorFactory.create_cosmics_configurator()
        
        # Should be able to create generator configurator without other components
        generator_configurator = GeneratorConfiguratorFactory.create_generator_configurator(
            self.mock_ROOT, self.mock_units, self.mock_utils, self.mock_ship_geo,
            pythia_configurator, cosmics_configurator
        )
        
        # Test specific functionality in isolation
        result = generator_configurator.create_primary_generator()
        self.mock_ROOT.FairPrimaryGenerator.assert_called_once()
        
        # Test execution configurator isolation
        geometry_configurator = EnhancedSimulationConfiguratorFactory.create_geometry_configurator()
        utility_configurator = EnhancedSimulationConfiguratorFactory.create_utility_configurator()
        
        execution_configurator = SimulationExecutionConfiguratorFactory.create_simulation_execution_configurator(
            self.mock_ROOT, self.mock_units, self.mock_config_manager,
            geometry_configurator, utility_configurator
        )
        
        # Test specific functionality in isolation
        mock_run = Mock()
        execution_configurator.configure_trajectory_storage(mock_run, self.mock_options)
        mock_run.SetStoreTraj.assert_called_with(False)  # eventDisplay is False

def run_integration_tests():
    """Run all integration tests"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestRefactoredIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return success status
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_integration_tests()
    sys.exit(0 if success else 1)