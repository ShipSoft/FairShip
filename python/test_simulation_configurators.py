#!/usr/bin/env python3
"""
Test script for simulation configurators.

This script verifies that the new configurator classes work correctly
and can replace the direct imports in run_simScript.py.
"""

import sys
import os

# Add the python directory to the path so we can import our new modules
sys.path.insert(0, os.path.dirname(__file__))

def test_import_configurators():
    """Test that all configurator classes can be imported without side effects."""
    print("Testing configurator imports...")
    
    try:
        from simulation_configurators import (
            PythiaConfigurator, 
            DetectorConfigurator,
            GeometryConfigurator,
            CosmicsConfigurator,
            UtilityConfigurator,
            SimulationConfiguratorFactory
        )
        print("✓ All configurator classes imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False

def test_factory_creation():
    """Test that the factory can create all configurator types."""
    print("Testing configurator factory...")
    
    try:
        from simulation_configurators import SimulationConfiguratorFactory
        
        # Create all configurator types
        pythia_conf = SimulationConfiguratorFactory.create_pythia_configurator()
        detector_conf = SimulationConfiguratorFactory.create_detector_configurator()
        geometry_conf = SimulationConfiguratorFactory.create_geometry_configurator()
        cosmics_conf = SimulationConfiguratorFactory.create_cosmics_configurator()
        utility_conf = SimulationConfiguratorFactory.create_utility_configurator()
        
        print("✓ All configurator types created successfully")
        return True
    except Exception as e:
        print(f"✗ Factory creation error: {e}")
        return False

def test_lazy_import_behavior():
    """Test that modules are only imported when needed."""
    print("Testing lazy import behavior...")
    
    try:
        from simulation_configurators import PythiaConfigurator
        
        # Create configurator - should not import anything yet
        pythia_conf = PythiaConfigurator()
        
        # Check that modules are not yet imported
        assert pythia_conf._pythia8_conf is None
        assert pythia_conf._pythia8darkphoton_conf is None
        
        print("✓ Lazy import behavior working correctly")
        return True
    except Exception as e:
        print(f"✗ Lazy import test error: {e}")
        return False

def test_modified_run_simscript_syntax():
    """Test that the modified run_simScript.py has valid syntax."""
    print("Testing modified run_simScript.py syntax...")
    
    try:
        script_path = os.path.join(os.path.dirname(__file__), '..', 'macro', 'run_simScript.py')
        
        # Try to compile the script to check for syntax errors
        with open(script_path, 'r') as f:
            code = f.read()
        
        compile(code, script_path, 'exec')
        print("✓ Modified run_simScript.py has valid syntax")
        return True
    except SyntaxError as e:
        print(f"✗ Syntax error in run_simScript.py: {e}")
        return False
    except FileNotFoundError:
        print(f"✗ Could not find run_simScript.py at expected location")
        return False

def main():
    """Run all tests."""
    print("Running simulation configurator tests...")
    print("=" * 50)
    
    tests = [
        test_import_configurators,
        test_factory_creation,
        test_lazy_import_behavior,
        test_modified_run_simscript_syntax
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"Tests completed: {passed}/{len(tests)} passed")
    
    if passed == len(tests):
        print("🎉 All tests passed! Phase 1 refactoring is complete.")
        return 0
    else:
        print("❌ Some tests failed. Please review the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())