# README

This directory contains unit tests, regression tests and benchmarking scripts for this
package and all supported storage adapters. For testing we use the PyTest framework.
Tests for storage adapters must go in their own directory. The following naming convention for these
directories must be adhered to: 'test_***adapter-name***'.

## Directory structure
* [**test_mongodb/**] Contains unit tests and regression tests for the MongoDB storage back-end adapter.
* [**benchmark_api.py**] Module that contains benchmarking code to run performance benchmarks for the CDB API.
* [**dummydata_generator.py**] Module that implements a dummy data generator to populate a mongo DB with.
* [**test_config.yml**] Config file that will be used during tests.
* [**test_factory.py**] Module that contains tests for the factory.py module.