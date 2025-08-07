#!/usr/bin/env python
"""Test script for the simulation execution configurator module."""

import sys
import unittest
from unittest.mock import Mock, patch

# Import from python directory (already in PYTHONPATH in runtime environment)
from simulation_execution_configurator import (
    SimulationExecutionConfigurator,
    SimulationExecutionConfiguratorFactory,
)


class TestSimulationExecutionConfigurator(unittest.TestCase):
    """Test class for simulation execution configurator."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_ROOT = Mock()
        self.mock_units = Mock()
        self.mock_config_manager = Mock()
        self.mock_geom_configurator = Mock()
        self.mock_utility_configurator = Mock()

        # Set up mock units
        self.mock_units.MeV = 0.001
        self.mock_units.GeV = 1.0
        self.mock_units.mm = 0.1
        self.mock_units.m = 100.0

        # Set up mock ROOT constants
        self.mock_ROOT.kTRUE = True
        self.mock_ROOT.kFALSE = False

        self.configurator = SimulationExecutionConfigurator(
            self.mock_ROOT,
            self.mock_units,
            self.mock_config_manager,
            self.mock_geom_configurator,
            self.mock_utility_configurator,
        )

        # Set up mock options
        self.mock_options = Mock()
        self.mock_options.eventDisplay = False
        self.mock_options.dryrun = False
        self.mock_options.mudis = False
        self.mock_options.deepCopy = False
        self.mock_options.debug = 0
        self.mock_options.field_map = None
        self.mock_options.nEvents = 100
        self.mock_options.muonback = False
        self.mock_options.DarkPhoton = False

        # Set up mock geometry
        self.mock_ship_geo = Mock()
        self.mock_ship_geo.target.z0 = 0.0
        self.mock_ship_geo.Bfield = Mock()

        # Set up mock timer
        self.mock_timer = Mock()
        self.mock_timer.RealTime.return_value = 123.45
        self.mock_timer.CpuTime.return_value = 98.76

    def test_configure_trajectory_storage_enabled(self):
        """Test trajectory storage configuration when enabled."""
        self.mock_options.eventDisplay = True
        mock_run = Mock()

        self.configurator.configure_trajectory_storage(mock_run, self.mock_options)

        mock_run.SetStoreTraj.assert_called_with(True)

    def test_configure_trajectory_storage_disabled(self):
        """Test trajectory storage configuration when disabled."""
        self.mock_options.eventDisplay = False
        mock_run = Mock()

        self.configurator.configure_trajectory_storage(mock_run, self.mock_options)

        mock_run.SetStoreTraj.assert_called_with(False)

    def test_initialize_simulation_run_normal(self):
        """Test normal simulation run initialization."""
        mock_run = Mock()
        mock_gMC = Mock()
        mock_fStack = Mock()

        self.mock_ROOT.TVirtualMC.GetMC.return_value = mock_gMC
        mock_gMC.GetStack.return_value = mock_fStack

        gMC, fStack = self.configurator.initialize_simulation_run(
            mock_run, self.mock_options
        )

        mock_run.Init.assert_called_once()
        self.assertEqual(gMC, mock_gMC)
        self.assertEqual(fStack, mock_fStack)

    def test_initialize_simulation_run_dryrun(self):
        """Test simulation run initialization with dry run."""
        self.mock_options.dryrun = True
        mock_run = Mock()

        with self.assertRaises(SystemExit):
            self.configurator.initialize_simulation_run(mock_run, self.mock_options)

        mock_run.Init.assert_called_once()

    def test_configure_stack_parameters_hits_only(self):
        """Test stack parameter configuration for hits only."""
        mock_fStack = Mock()
        config_values = {"MCTracksWithHitsOnly": True}

        self.configurator.configure_stack_parameters(
            mock_fStack, self.mock_options, config_values
        )

        mock_fStack.SetMinPoints.assert_called_with(1)
        mock_fStack.SetEnergyCut.assert_called_with(-100.0 * self.mock_units.MeV)

    def test_configure_stack_parameters_energy_cut_only(self):
        """Test stack parameter configuration for energy cut only."""
        mock_fStack = Mock()
        config_values = {"MCTracksWithEnergyCutOnly": True}

        self.configurator.configure_stack_parameters(
            mock_fStack, self.mock_options, config_values
        )

        mock_fStack.SetMinPoints.assert_called_with(-1)
        mock_fStack.SetEnergyCut.assert_called_with(100.0 * self.mock_units.MeV)

    def test_configure_stack_parameters_deep_copy(self):
        """Test stack parameter configuration for deep copy."""
        self.mock_options.deepCopy = True
        mock_fStack = Mock()
        config_values = {}

        self.configurator.configure_stack_parameters(
            mock_fStack, self.mock_options, config_values
        )

        mock_fStack.SetMinPoints.assert_called_with(0)
        mock_fStack.SetEnergyCut.assert_called_with(0.0 * self.mock_units.MeV)

    def test_configure_trajectory_filter_enabled(self):
        """Test trajectory filter configuration when enabled."""
        self.mock_options.eventDisplay = True
        mock_trajFilter = Mock()
        self.mock_ROOT.FairTrajFilter.Instance.return_value = mock_trajFilter

        self.configurator.configure_trajectory_filter(
            self.mock_options, self.mock_ship_geo
        )

        self.mock_ROOT.FairTrajFilter.Instance.assert_called_once()
        mock_trajFilter.SetStepSizeCut.assert_called_once()
        mock_trajFilter.SetVertexCut.assert_called_once()
        mock_trajFilter.SetMomentumCutP.assert_called_once()
        mock_trajFilter.SetEnergyCut.assert_called_once()
        mock_trajFilter.SetStorePrimaries.assert_called_with(True)
        mock_trajFilter.SetStoreSecondaries.assert_called_with(True)

    def test_configure_trajectory_filter_disabled(self):
        """Test trajectory filter configuration when disabled."""
        self.mock_options.eventDisplay = False

        self.configurator.configure_trajectory_filter(
            self.mock_options, self.mock_ship_geo
        )

        self.mock_ROOT.FairTrajFilter.Instance.assert_not_called()

    def test_configure_magnetic_fields_with_field_map(self):
        """Test magnetic field configuration with field map."""
        self.mock_ship_geo.Bfield.fieldMap = "existing_map"
        self.mock_options.field_map = "new_map"
        mock_fieldMaker = Mock()
        self.mock_geom_configurator.add_vmc_fields.return_value = mock_fieldMaker

        result = self.configurator.configure_magnetic_fields(
            self.mock_ship_geo, self.mock_options
        )

        self.assertEqual(self.mock_ship_geo.Bfield.fieldMap, "new_map")
        self.mock_geom_configurator.add_vmc_fields.assert_called_with(
            self.mock_ship_geo, verbose=True
        )
        self.assertEqual(result, mock_fieldMaker)

    def test_configure_magnetic_fields_without_field_map(self):
        """Test magnetic field configuration without field map."""
        # Remove fieldMap attribute
        del self.mock_ship_geo.Bfield.fieldMap

        result = self.configurator.configure_magnetic_fields(
            self.mock_ship_geo, self.mock_options
        )

        self.assertIsNone(result)
        self.mock_geom_configurator.add_vmc_fields.assert_not_called()

    def test_print_debug_info_enabled(self):
        """Test debug info printing when enabled."""
        self.mock_options.debug = 1

        self.configurator.print_debug_info(self.mock_options)

        self.mock_geom_configurator.print_vmc_fields.assert_called_once()
        self.mock_geom_configurator.print_weights_and_fields.assert_called_once()

    def test_print_debug_info_disabled(self):
        """Test debug info printing when disabled."""
        self.mock_options.debug = 0

        self.configurator.print_debug_info(self.mock_options)

        self.mock_geom_configurator.print_vmc_fields.assert_not_called()
        self.mock_geom_configurator.print_weights_and_fields.assert_not_called()

    def test_run_simulation(self):
        """Test simulation run execution."""
        mock_run = Mock()

        self.configurator.run_simulation(mock_run, self.mock_options)

        mock_run.Run.assert_called_with(100)

    def test_save_runtime_database(self):
        """Test runtime database saving."""
        mock_rtdb = Mock()
        mock_parOut = Mock()
        self.mock_ROOT.FairParRootFileIo.return_value = mock_parOut
        parFile = "/path/to/param.root"

        self.configurator.save_runtime_database(mock_rtdb, parFile)

        self.mock_ROOT.FairParRootFileIo.assert_called_with(True)
        mock_parOut.open.assert_called_with(parFile)
        mock_rtdb.setOutput.assert_called_with(mock_parOut)
        mock_rtdb.saveOutput.assert_called_once()
        mock_rtdb.printParamContexts.assert_called_once()

    def test_save_geometry_file(self):
        """Test geometry file saving."""
        mock_run = Mock()
        mock_runtime_config = Mock()
        mock_runtime_config.geometry_file = "/path/to/geometry.root"

        self.configurator.save_geometry_file(
            mock_run, mock_runtime_config, self.mock_ship_geo
        )

        mock_run.CreateGeometryFile.assert_called_with("/path/to/geometry.root")
        self.mock_utility_configurator.save_basic_parameters.assert_called_with(
            "/path/to/geometry.root", self.mock_ship_geo
        )

    @patch("builtins.print")
    def test_print_simulation_results(self, mock_print):
        """Test simulation results printing."""
        outFile = "/path/to/output.root"
        parFile = "/path/to/param.root"
        generators = {}
        HNL = False

        self.configurator.print_simulation_results(
            self.mock_timer, outFile, parFile, generators, self.mock_options, HNL
        )

        self.mock_timer.Stop.assert_called_once()
        self.mock_timer.RealTime.assert_called_once()
        self.mock_timer.CpuTime.assert_called_once()

        # Check that print was called with expected messages
        print_calls = []
        for call in mock_print.call_args_list:
            if call.args:
                if len(call.args) == 1:
                    print_calls.append(call.args[0])
                else:
                    # Handle print calls with multiple arguments
                    print_calls.append(" ".join(str(arg) for arg in call.args))
        self.assertIn("Macro finished successfully.", print_calls)
        self.assertIn(f"Output file is  {outFile}", print_calls)

    @patch("builtins.print")
    def test_print_comprehensive_summary(self, mock_print):
        """Test comprehensive summary printing."""
        USING_LAZY_LOADING = True
        mock_import_manager = Mock()
        mock_import_manager.get_import_summary.return_value = "Import summary"

        self.configurator.print_comprehensive_summary(
            USING_LAZY_LOADING, mock_import_manager
        )

        self.mock_config_manager.get_summary.assert_called_once()
        mock_import_manager.get_import_summary.assert_called_once()

        print_calls = []
        for call in mock_print.call_args_list:
            if call.args:
                print_calls.append(call.args[0])
            elif call.kwargs and "end" in call.kwargs:
                # Handle print calls with keyword arguments
                print_calls.append("")
        self.assertIn("SIMULATION SUMMARY", print_calls)


class TestSimulationExecutionConfiguratorFactory(unittest.TestCase):
    """Test factory class."""

    def test_create_simulation_execution_configurator(self):
        """Test factory method."""
        mock_ROOT = Mock()
        mock_units = Mock()
        mock_config_manager = Mock()
        mock_geom_configurator = Mock()
        mock_utility_configurator = Mock()

        result = SimulationExecutionConfiguratorFactory.create_simulation_execution_configurator(
            mock_ROOT,
            mock_units,
            mock_config_manager,
            mock_geom_configurator,
            mock_utility_configurator,
        )

        self.assertIsInstance(result, SimulationExecutionConfigurator)
        self.assertEqual(result.ROOT, mock_ROOT)
        self.assertEqual(result.u, mock_units)
        self.assertEqual(result.config_manager, mock_config_manager)


def run_tests():
    """Run all tests."""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestSimulationExecutionConfigurator))
    suite.addTests(
        loader.loadTestsFromTestCase(TestSimulationExecutionConfiguratorFactory)
    )

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Return success status
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
