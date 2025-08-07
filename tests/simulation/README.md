# Simulation Refactoring Tests

This directory contains comprehensive tests for the refactored simulation components.

## Test Structure

- `test_generator_configurator.py` - Tests for the generator configuration module
- `test_simulation_execution_configurator.py` - Tests for the simulation execution module
- `test_refactored_integration.py` - Integration tests for the complete system
- `run_tests.py` - Test runner for all simulation tests

## Running Tests

### Run All Tests
```bash
cd tests/simulation
python run_tests.py
```

### Run Individual Test Files
```bash
cd tests/simulation
python -m unittest test_generator_configurator.py
python -m unittest test_simulation_execution_configurator.py
python -m unittest test_refactored_integration.py
```

### Run Specific Test Classes
```bash
python -m unittest test_generator_configurator.TestGeneratorConfigurator
python -m unittest test_simulation_execution_configurator.TestSimulationExecutionConfigurator
```

### Run Specific Test Methods
```bash
python -m unittest test_generator_configurator.TestGeneratorConfigurator.test_configure_pythia8_generators_hnl
```

## Test Coverage

The test suite provides comprehensive coverage of:

### Unit Tests
- **Generator Configuration**: All generator types (Pythia8, Pythia6, Particle Gun, etc.)
- **Simulation Execution**: Stack configuration, trajectory filtering, post-processing
- **Factory Patterns**: Configurator creation and dependency injection
- **Error Handling**: Failure modes and edge cases

### Integration Tests
- **Module Interactions**: Data flow between components
- **Configuration Propagation**: Values passed correctly between modules
- **Workflow Validation**: Complete simulation pipeline execution
- **Backward Compatibility**: Original functionality preserved

### Mock-Based Testing
- External dependencies (ROOT, shipunit, etc.) are mocked
- Tests run without requiring full SHiP environment
- Fast execution and reliable results
- Isolated component testing

## Test Output

The test runner provides detailed output including:
- Test execution progress with verbose output
- Summary of passed/failed/error tests
- Detailed failure and error reporting
- Overall success/failure status

Example output:
```
test_configure_pythia8_generators_hnl ... ok
test_configure_particle_gun ... ok
test_configure_all_generators ... ok

==============================
TEST SUMMARY
==============================
Tests run: 25
Failures: 0
Errors: 0
Skipped: 0

Overall result: PASSED
```

## Dependencies

Tests use Python's built-in `unittest` framework with `unittest.mock` for mocking external dependencies. No additional test dependencies are required.

## Adding New Tests

When adding new functionality:

1. **Unit Tests**: Add tests to the appropriate test file
2. **Integration Tests**: Update `test_refactored_integration.py` for new workflows
3. **Mock Objects**: Create appropriate mocks for new external dependencies
4. **Test Coverage**: Ensure new code paths are tested

### Test Naming Convention
- Test files: `test_<module_name>.py`
- Test classes: `Test<ClassName>`
- Test methods: `test_<functionality_being_tested>`

### Mock Strategy
- Mock external dependencies (ROOT, shipunit, etc.)
- Use `unittest.mock.Mock` and `unittest.mock.patch`
- Verify method calls and return values
- Test error conditions with mock exceptions
