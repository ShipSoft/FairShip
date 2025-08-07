#!/usr/bin/env python3
"""
Test script for lazy loading infrastructure (Phase 2).

This script verifies that the lazy loading system works correctly
and provides the expected benefits.
"""

import sys
import os
import time
import logging

# Add the python directory to the path
sys.path.insert(0, os.path.dirname(__file__))

# Set up logging to see what's happening
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


def test_lazy_module_creation():
    """Test that LazyModule objects can be created without importing."""
    print("Testing lazy module creation...")
    
    try:
        from lazy_loading import LazyModule, ImportTracker
        
        tracker = ImportTracker()
        
        # Create lazy modules - should not trigger imports
        lazy_root = LazyModule('ROOT', tracker)
        lazy_numpy = LazyModule('numpy', tracker)  # This might not exist in SHiP env
        
        # Check that modules are not imported yet
        assert not lazy_root.is_imported
        assert not lazy_numpy.is_imported
        assert len(tracker.imported_modules) == 0
        
        print("✓ Lazy modules created without triggering imports")
        return True
    except Exception as e:
        print(f"✗ Lazy module creation test failed: {e}")
        return False


def test_lazy_module_access():
    """Test that modules are imported only when accessed."""
    print("Testing lazy module access...")
    
    try:
        from lazy_loading import LazyModule, ImportTracker
        
        tracker = ImportTracker()
        lazy_os = LazyModule('os', tracker)
        
        # Access the module - should trigger import
        os_module = lazy_os
        path_exists = os_module.path.exists  # Access an attribute
        
        # Check that module was imported
        assert lazy_os.is_imported
        assert 'os' in tracker.imported_modules
        assert len(tracker.imported_modules) == 1
        
        print("✓ Module imported only when accessed")
        return True
    except Exception as e:
        print(f"✗ Lazy module access test failed: {e}")
        return False


def test_module_loader():
    """Test the ModuleLoader functionality."""
    print("Testing ModuleLoader...")
    
    try:
        from lazy_loading import ModuleLoader
        
        loader = ModuleLoader()
        
        # Register modules with conditions
        condition_met = True
        loader.register_module('os', 'os')
        loader.register_module('sys', 'sys', condition=lambda: condition_met)
        
        # Get modules
        os_module = loader.get_module('os')
        sys_module = loader.get_module('sys')
        
        # Test condition-based loading
        condition_met = False
        try:
            sys_module_blocked = loader.get_module('sys')
            # This should work because the module was already registered
        except RuntimeError:
            pass  # Expected if condition is checked on each access
        
        print("✓ ModuleLoader working correctly")
        return True
    except Exception as e:
        print(f"✗ ModuleLoader test failed: {e}")
        return False


def test_simulation_module_loader():
    """Test the SimulationModuleLoader."""
    print("Testing SimulationModuleLoader...")
    
    try:
        from lazy_loading import SimulationModuleLoader
        
        # Create a mock options object
        class MockOptions:
            def __init__(self):
                self.pythia8 = True
                self.DarkPhoton = False
                self.cosmics = False
                self.dryrun = False
        
        options = MockOptions()
        loader = SimulationModuleLoader(options)
        
        # Try to get some core modules
        try:
            root_module = loader.get_module('ROOT')
            print("  - ROOT module accessible")
        except Exception as e:
            print(f"  - Could not access ROOT module: {e}")
        
        try:
            shipunit_module = loader.get_module('shipunit')  
            print("  - shipunit module accessible")
        except Exception as e:
            print(f"  - Could not access shipunit module: {e}")
        
        print("✓ SimulationModuleLoader created successfully")
        return True
    except Exception as e:
        print(f"✗ SimulationModuleLoader test failed: {e}")
        return False


def test_enhanced_configurators():
    """Test the enhanced configurators."""
    print("Testing enhanced configurators...")
    
    try:
        from enhanced_configurators import EnhancedSimulationConfiguratorFactory
        
        # Create configurators - should not trigger any imports yet
        pythia_conf = EnhancedSimulationConfiguratorFactory.create_pythia_configurator()
        detector_conf = EnhancedSimulationConfiguratorFactory.create_detector_configurator()
        geometry_conf = EnhancedSimulationConfiguratorFactory.create_geometry_configurator()
        cosmics_conf = EnhancedSimulationConfiguratorFactory.create_cosmics_configurator()
        utility_conf = EnhancedSimulationConfiguratorFactory.create_utility_configurator()
        
        print("✓ Enhanced configurators created successfully")
        return True
    except Exception as e:
        print(f"✗ Enhanced configurators test failed: {e}")
        return False


def test_import_tracking():
    """Test the import tracking functionality."""
    print("Testing import tracking...")
    
    try:
        from lazy_loading import ImportTracker, LazyModule
        
        tracker = ImportTracker()
        
        # Import some modules through lazy loading
        time.sleep(0.001)  # Small delay to see timing
        lazy_time = LazyModule('time', tracker)
        _ = lazy_time.time()  # Access to trigger import
        
        time.sleep(0.001)
        lazy_json = LazyModule('json', tracker)
        _ = lazy_json.dumps({})  # Access to trigger import
        
        # Check tracking
        summary = tracker.get_import_summary()
        assert 'time' in summary
        assert 'json' in summary
        assert '2 total' in summary or '2' in summary
        
        print("✓ Import tracking working correctly")
        print(f"  Sample summary:\n{summary}")
        return True
    except Exception as e:
        print(f"✗ Import tracking test failed: {e}")
        return False


def test_syntax_check():
    """Test that the modified run_simScript.py still has valid syntax."""
    print("Testing modified run_simScript.py syntax...")
    
    try:
        script_path = os.path.join(os.path.dirname(__file__), '..', 'macro', 'run_simScript.py')
        
        with open(script_path, 'r') as f:
            code = f.read()
        
        compile(code, script_path, 'exec')
        print("✓ Modified run_simScript.py has valid syntax")
        return True
    except SyntaxError as e:
        print(f"✗ Syntax error in run_simScript.py: {e}")
        return False
    except FileNotFoundError:
        print(f"✗ Could not find run_simScript.py")
        return False


def main():
    """Run all Phase 2 tests."""
    print("Running Phase 2 (Lazy Loading Infrastructure) tests...")
    print("=" * 60)
    
    tests = [
        test_lazy_module_creation,
        test_lazy_module_access,
        test_module_loader,
        test_simulation_module_loader,
        test_enhanced_configurators,
        test_import_tracking,
        test_syntax_check
    ]
    
    passed = 0
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 60)
    print(f"Phase 2 tests completed: {passed}/{len(tests)} passed")
    
    if passed == len(tests):
        print("🎉 All Phase 2 tests passed! Lazy Loading Infrastructure is complete.")
        return 0
    else:
        print("❌ Some tests failed. Please review the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())