#!/usr/bin/env python3
"""
Test script for configuration management system (Phase 3).

This script verifies that the configuration management system works correctly
and provides proper state management for the simulation.
"""

import sys
import os
import tempfile
from pathlib import Path

# Add the python directory to the path
sys.path.insert(0, os.path.dirname(__file__))


def test_configuration_classes():
    """Test the configuration dataclasses."""
    print("Testing configuration classes...")
    
    try:
        from simulation_config import SimulationConfig, ParticleConfig, RuntimeConfig
        
        # Test ParticleConfig
        pc = ParticleConfig()
        assert pc.inclusive == "c"
        assert pc.hnl_enabled == True
        assert pc.charmonly == False
        
        # Test SimulationConfig  
        sc = SimulationConfig()
        assert sc.mc_engine == "TGeant4"
        assert sc.sim_engine == "Pythia8"
        assert sc.default_design == '2025'
        assert '2025' in sc.global_designs
        
        # Test RuntimeConfig
        rc = RuntimeConfig()
        assert rc.total_events == 100
        assert rc.current_event == 0
        
        print("✓ Configuration classes created successfully")
        return True
    except Exception as e:
        print(f"✗ Configuration classes test failed: {e}")
        return False


def test_configuration_manager():
    """Test the ConfigurationManager."""
    print("Testing ConfigurationManager...")
    
    try:
        from simulation_config import ConfigurationManager
        
        manager = ConfigurationManager()
        
        # Test initial state
        assert not manager.simulation_config.initialized
        assert manager.runtime_config.total_events == 100
        
        # Test summary generation
        summary = manager.get_summary()
        assert "Configuration Summary:" in summary
        assert "Simulation Engine: Pythia8" in summary
        
        print("✓ ConfigurationManager working correctly")
        return True
    except Exception as e:
        print(f"✗ ConfigurationManager test failed: {e}")
        return False


def test_options_loading():
    """Test loading configuration from options."""
    print("Testing options loading...")
    
    try:
        from simulation_config import ConfigurationManager
        
        # Create mock options
        class MockOptions:
            def __init__(self):
                self.A = 'b'
                self.nEvents = 500
                self.outputDir = '/tmp/test_output'
                self.theMass = 2.5
                self.DarkPhoton = True
                self.thecouplings = "1e-9,2e-9,3e-9"
                self.dy = 7.0
                self.caloDesign = 2
        
        options = MockOptions()
        manager = ConfigurationManager()
        
        # Mock units module
        class MockUnits:
            GeV = 1000.0
        
        manager.set_units_module(MockUnits())
        manager.load_from_options(options)
        
        # Check that options were loaded correctly
        assert manager.simulation_config.particle_config.inclusive == 'b'
        assert manager.runtime_config.total_events == 500
        assert manager.simulation_config.output_dir == '/tmp/test_output'
        assert manager.simulation_config.particle_config.dp_mass == 2.5
        assert not manager.simulation_config.particle_config.hnl_enabled  # DarkPhoton=True should disable HNL
        
        # Check global designs update
        assert 'custom' in manager.simulation_config.global_designs
        assert manager.simulation_config.global_designs['custom']['dy'] == 7.0
        assert manager.simulation_config.global_designs['custom']['caloDesign'] == 2
        
        print("✓ Options loading working correctly")
        return True
    except Exception as e:
        print(f"✗ Options loading test failed: {e}")
        return False


def test_runtime_config_generation():
    """Test runtime configuration generation."""
    print("Testing runtime config generation...")
    
    try:
        from simulation_config import ConfigurationManager
        
        class MockOptions:
            def __init__(self):
                self.command = None
                self.pythia8 = True
                self.eventDisplay = False
                self.outputDir = '/tmp/test'
        
        options = MockOptions()
        manager = ConfigurationManager()
        manager.load_from_options(options)
        manager.generate_runtime_config(options)
        
        runtime_config = manager.runtime_config
        
        # Check that files were generated
        assert runtime_config.tag is not None
        assert 'Pythia8-TGeant4' in runtime_config.tag
        assert runtime_config.output_file is not None
        assert runtime_config.parameter_file is not None
        assert runtime_config.geometry_file is not None
        
        # Check file paths
        assert runtime_config.output_file.endswith('.root')
        assert 'ship.' in runtime_config.output_file
        assert 'ship.params.' in runtime_config.parameter_file
        assert 'geofile_full.' in runtime_config.geometry_file
        
        print("✓ Runtime config generation working correctly")
        return True
    except Exception as e:
        print(f"✗ Runtime config generation test failed: {e}")
        return False


def test_configuration_serialization():
    """Test configuration save/load functionality."""
    print("Testing configuration serialization...")
    
    try:
        from simulation_config import ConfigurationManager
        
        # Create and configure manager
        manager = ConfigurationManager()
        
        class MockOptions:
            nEvents = 1000
            outputDir = '/test/path'
            A = 'c'
        
        class MockUnits:
            GeV = 1000.0
        
        manager.set_units_module(MockUnits())
        manager.load_from_options(MockOptions())
        
        # Test saving to file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            temp_file = f.name
        
        try:
            manager.save_to_file(temp_file, format='yaml')
            
            # Test loading from file
            new_manager = ConfigurationManager()
            new_manager.load_from_file(temp_file)
            
            # Verify configuration was preserved
            assert new_manager.runtime_config.total_events == 1000
            assert new_manager.simulation_config.output_dir == '/test/path'
            assert new_manager.simulation_config.particle_config.inclusive == 'c'
            
            print("✓ Configuration serialization working correctly")
            return True
            
        finally:
            # Clean up temp file
            os.unlink(temp_file)
            
    except Exception as e:
        print(f"✗ Configuration serialization test failed: {e}")
        return False


def test_root_initialization():
    """Test ROOT initialization system.""" 
    print("Testing ROOT initialization...")
    
    try:
        from root_initialization import ROOTInitializer, LibraryManager
        
        # Test ROOTInitializer
        initializer = ROOTInitializer()
        assert not initializer.is_initialized
        
        # Note: We can't actually test ROOT initialization in this environment
        # without the full SHiP setup, so we test the structure
        
        # Test LibraryManager
        lib_manager = LibraryManager()
        assert len(lib_manager.loaded_libraries) == 0
        
        summary = lib_manager.get_library_summary()
        assert "No libraries loaded" in summary
        
        print("✓ ROOT initialization classes created successfully")
        return True
    except Exception as e:
        print(f"✗ ROOT initialization test failed: {e}")
        return False


def test_global_functions():
    """Test global configuration functions."""
    print("Testing global configuration functions...")
    
    try:
        from simulation_config import get_config_manager, initialize_configuration
        
        # Test getting global manager
        manager1 = get_config_manager()
        manager2 = get_config_manager()
        
        # Should be the same instance
        assert manager1 is manager2
        
        # Test convenience initialization function
        class MockOptions:
            A = 'c'
            nEvents = 200
        
        class MockUnits:
            GeV = 1000.0
        
        initialized_manager = initialize_configuration(MockOptions(), MockUnits())
        
        assert initialized_manager.simulation_config.initialized
        assert initialized_manager.runtime_config.total_events == 200
        
        print("✓ Global configuration functions working correctly")
        return True
    except Exception as e:
        print(f"✗ Global configuration functions test failed: {e}")
        return False


def test_run_simscript_syntax():
    """Test that the updated run_simScript.py has valid syntax."""
    print("Testing updated run_simScript.py syntax...")
    
    try:
        script_path = os.path.join(os.path.dirname(__file__), '..', 'macro', 'run_simScript.py')
        
        with open(script_path, 'r') as f:
            code = f.read()
        
        # Check that our new imports are present
        assert 'from simulation_config import' in code
        assert 'from root_initialization import' in code
        assert 'config_manager = initialize_configuration' in code
        
        # Compile to check syntax
        compile(code, script_path, 'exec')
        
        print("✓ Updated run_simScript.py has valid syntax and imports")
        return True
    except SyntaxError as e:
        print(f"✗ Syntax error in run_simScript.py: {e}")
        return False
    except FileNotFoundError:
        print(f"✗ Could not find run_simScript.py")
        return False
    except Exception as e:
        print(f"✗ run_simScript.py test failed: {e}")
        return False


def main():
    """Run all Phase 3 tests."""
    print("Running Phase 3 (Configuration State Management) tests...")
    print("=" * 70)
    
    tests = [
        test_configuration_classes,
        test_configuration_manager,
        test_options_loading,
        test_runtime_config_generation,
        test_configuration_serialization,
        test_root_initialization,
        test_global_functions,
        test_run_simscript_syntax
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 70)
    print(f"Phase 3 tests completed: {passed}/{len(tests)} passed")
    
    if passed == len(tests):
        print("🎉 All Phase 3 tests passed! Configuration State Management is complete.")
        return 0
    else:
        print("❌ Some tests failed. Please review the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())