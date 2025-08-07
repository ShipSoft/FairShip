#!/usr/bin/env python
"""
Test script for the generator configurator module.
"""

import sys
import os
import unittest
from unittest.mock import Mock, patch, MagicMock

# Add the macro directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from generator_configurator import GeneratorConfigurator, GeneratorConfiguratorFactory

class TestGeneratorConfigurator(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        self.mock_ROOT = Mock()
        self.mock_units = Mock()
        self.mock_utils = Mock()
        self.mock_ship_geo = Mock()
        self.mock_pythia_configurator = Mock()
        self.mock_cosmics_configurator = Mock()
        
        # Set up mock geometry objects
        self.mock_ship_geo.target.z0 = 0.0
        self.mock_ship_geo.target.z = 100.0
        self.mock_ship_geo.decayVolume.z = 200.0
        self.mock_ship_geo.muShield.length = 150.0
        self.mock_ship_geo.Chamber1.z = 300.0
        self.mock_ship_geo.chambers.Tub1length = 50.0
        self.mock_ship_geo.TrackStation1.z = 400.0
        self.mock_ship_geo.TrackStation2.z = 500.0
        self.mock_ship_geo.tauMudet.zMudetC = 600.0
        self.mock_ship_geo.MuonStation3.z = 700.0
        self.mock_ship_geo.Box.gausbeam = False
        self.mock_ship_geo.Box.TX = 10.0
        self.mock_ship_geo.Box.TY = 10.0
        
        # Set up mock units
        self.mock_units.cm = 1.0
        self.mock_units.mm = 0.1
        self.mock_units.m = 100.0
        self.mock_units.GeV = 1.0
        self.mock_units.MeV = 0.001
        
        self.configurator = GeneratorConfigurator(
            self.mock_ROOT, self.mock_units, self.mock_utils, 
            self.mock_ship_geo, self.mock_pythia_configurator, 
            self.mock_cosmics_configurator
        )
        
        # Set up mock options
        self.mock_options = Mock()
        self.mock_options.pythia8 = False
        self.mock_options.pythia6 = False
        self.mock_options.fixedTarget = False
        self.mock_options.evtcalc = False
        self.mock_options.command = None
        self.mock_options.mudis = False
        self.mock_options.genie = False
        self.mock_options.nuradio = False
        self.mock_options.ntuple = False
        self.mock_options.muonback = False
        self.mock_options.cosmics = False
        self.mock_options.RPVSUSY = False
        self.mock_options.DarkPhoton = False
        self.mock_options.deepCopy = False
        self.mock_options.theMass = 1.0
        self.mock_options.theDPepsilon = 0.00000008
        self.mock_options.RPVSUSYbench = 2
        self.mock_options.firstEvent = 0
        self.mock_options.nEvents = 100
        self.mock_options.z_offset = -84.0
        self.mock_options.pID = 22
        self.mock_options.Estart = 10.0
        self.mock_options.Eend = 10.0
        self.mock_options.Vx = 0.0
        self.mock_options.Vy = 0.0
        self.mock_options.Vz = 0.0
        self.mock_options.multiplePG = False
        self.mock_options.PaintBeam = 5.0
        self.mock_options.SmearBeam = 0.8
        self.mock_options.phiRandom = False
        self.mock_options.sameSeed = False
        self.mock_options.followMuon = False
        self.mock_options.fastMuon = False
        
    def test_create_primary_generator(self):
        """Test primary generator creation"""
        result = self.configurator.create_primary_generator()
        self.mock_ROOT.FairPrimaryGenerator.assert_called_once()
        
    def test_configure_pythia8_generators_disabled(self):
        """Test Pythia8 generator configuration when disabled"""
        result = self.configurator.configure_pythia8_generators(
            Mock(), self.mock_options, {}
        )
        self.assertIsNone(result)
        
    def test_configure_pythia8_generators_hnl(self):
        """Test Pythia8 generator configuration for HNL"""
        self.mock_options.pythia8 = True
        mock_primGen = Mock()
        mock_P8gen = Mock()
        self.mock_ROOT.HNLPythia8Generator.return_value = mock_P8gen
        
        config_values = {
            'HNL': True,
            'inputFile': None,
            'inclusive': 'c',
            'charmonly': False,
            'theProductionCouplings': None,
            'theDecayCouplings': None,
            'theCouplings': [0.447e-9, 7.15e-9, 1.88e-9],
        }
        
        result = self.configurator.configure_pythia8_generators(
            mock_primGen, self.mock_options, config_values
        )
        
        self.assertEqual(result, mock_P8gen)
        mock_primGen.SetTarget.assert_called_with(0.0, 0.)
        self.mock_ROOT.HNLPythia8Generator.assert_called_once()
        mock_P8gen.SetParameters.assert_called_with("ProcessLevel:all = off")
        
    def test_configure_particle_gun(self):
        """Test particle gun configuration"""
        self.mock_options.command = "PG"
        self.mock_options.pID = 22
        self.mock_options.Estart = 5.0
        self.mock_options.Eend = 15.0
        self.mock_options.Vx = 1.0
        self.mock_options.Vy = 2.0
        self.mock_options.Vz = 3.0
        self.mock_options.multiplePG = False
        
        mock_primGen = Mock()
        mock_pgun = Mock()
        self.mock_ROOT.FairBoxGenerator.return_value = mock_pgun
        
        result = self.configurator.configure_particle_gun(mock_primGen, self.mock_options)
        
        self.assertEqual(result, mock_pgun)
        self.mock_ROOT.FairBoxGenerator.assert_called_with(22, 1)
        mock_pgun.SetPRange.assert_called_with(5.0, 15.0)
        mock_pgun.SetPhiRange.assert_called_with(0, 360)
        mock_pgun.SetThetaRange.assert_called_with(0, 0)
        mock_pgun.SetXYZ.assert_called_with(1.0, 2.0, 3.0)
        mock_primGen.AddGenerator.assert_called_with(mock_pgun)
        
    def test_configure_particle_gun_multiple(self):
        """Test multiple particle gun configuration"""
        self.mock_options.command = "PG"
        self.mock_options.multiplePG = True
        self.mock_options.Dx = 4.0
        self.mock_options.Dy = 6.0
        
        mock_primGen = Mock()
        mock_pgun = Mock()
        self.mock_ROOT.FairBoxGenerator.return_value = mock_pgun
        
        result = self.configurator.configure_particle_gun(mock_primGen, self.mock_options)
        
        mock_pgun.SetBoxXYZ.assert_called_once()
        
    def test_configure_evtcalc_generator(self):
        """Test EvtCalc generator configuration"""
        self.mock_options.evtcalc = True
        inputFile = "/path/to/input.root"
        
        mock_primGen = Mock()
        mock_evtgen = Mock()
        mock_evtgen.GetNevents.return_value = 50
        self.mock_ROOT.EvtCalcGenerator.return_value = mock_evtgen
        
        result = self.configurator.configure_evtcalc_generator(
            mock_primGen, self.mock_options, inputFile
        )
        
        self.assertEqual(result, mock_evtgen)
        mock_primGen.SetTarget.assert_called_with(0.0, 0.0)
        self.mock_utils.checkFileExists.assert_called_with(inputFile)
        mock_evtgen.Init.assert_called_with(inputFile, 0)
        mock_evtgen.SetPositions.assert_called_with(zTa=100.0, zDV=200.0)
        mock_primGen.AddGenerator.assert_called_with(mock_evtgen)
        self.assertEqual(self.mock_options.nEvents, 50)
        
    def test_configure_all_generators(self):
        """Test configuration of all generators"""
        mock_run = Mock()
        config_values = {
            'HNL': False,
            'inputFile': None,
            'inclusive': 'c',
            'charmonly': False,
            'Opt_high': None,
        }
        mock_modules = {}
        
        mock_primGen = Mock()
        self.mock_ROOT.FairPrimaryGenerator.return_value = mock_primGen
        
        primGen, generators = self.configurator.configure_all_generators(
            mock_run, self.mock_options, config_values, mock_modules
        )
        
        self.assertEqual(primGen, mock_primGen)
        self.assertIsInstance(generators, dict)
        mock_run.SetGenerator.assert_called_with(mock_primGen)

class TestGeneratorConfiguratorFactory(unittest.TestCase):
    
    def test_create_generator_configurator(self):
        """Test factory method"""
        mock_ROOT = Mock()
        mock_units = Mock()
        mock_utils = Mock()
        mock_ship_geo = Mock()
        mock_pythia_configurator = Mock()
        mock_cosmics_configurator = Mock()
        
        result = GeneratorConfiguratorFactory.create_generator_configurator(
            mock_ROOT, mock_units, mock_utils, mock_ship_geo,
            mock_pythia_configurator, mock_cosmics_configurator
        )
        
        self.assertIsInstance(result, GeneratorConfigurator)
        self.assertEqual(result.ROOT, mock_ROOT)
        self.assertEqual(result.u, mock_units)
        self.assertEqual(result.ut, mock_utils)
        self.assertEqual(result.ship_geo, mock_ship_geo)

def run_tests():
    """Run all tests"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestGeneratorConfigurator))
    suite.addTests(loader.loadTestsFromTestCase(TestGeneratorConfiguratorFactory))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return success status
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)