#!/usr/bin/env python
"""Test runner for simulation refactoring tests.

This script runs all the tests for the refactored simulation components.
"""

import os
import sys
import unittest


def discover_and_run_tests():
    """Discover and run all tests in the simulation test directory"""
    # Get the directory containing this script
    test_dir = os.path.dirname(os.path.abspath(__file__))

    # Create test loader
    loader = unittest.TestLoader()

    # Discover tests in the current directory
    suite = loader.discover(test_dir, pattern='test_*.py')

    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped) if hasattr(result, 'skipped') else 0}")

    if result.failures:
        print("\nFAILURES:")
        for test, traceback in result.failures:
            newline = '\n'
            error_msg = traceback.split('AssertionError: ')[-1].split(newline)[0] if 'AssertionError:' in traceback else 'See details above'
            print(f"- {test}: {error_msg}")

    if result.errors:
        print("\nERRORS:")
        for test, traceback in result.errors:
            newline = '\n'
            error_msg = traceback.split(newline)[-2] if traceback else 'Unknown error'
            print(f"- {test}: {error_msg}")

    # Return success status
    success = len(result.failures) == 0 and len(result.errors) == 0
    print(f"\nOverall result: {'PASSED' if success else 'FAILED'}")
    return success

if __name__ == '__main__':
    success = discover_and_run_tests()
    sys.exit(0 if success else 1)
