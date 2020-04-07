# conditionsDB package

## Introduction

This package provides functionality to communicate with a conditions database (CDB) storage back-end.
It provides a generic API that facilitates storage and retrieval of conditions data from any supported
storage back-end.

### Supported storage back-ends
Currently, the following storage back-ends are supported:

* MongoDB

## Package structure

* [**databases/**] Contains storage back-end adapters. More information about these adapters can be found in the readme inside this directory.
* [**demo/**] Contains a documented demo script that demonstrates how to use the conditionsDB API.
* [**tests/**] Contains unit tests, regression tests and benchmarking scripts for this package and all supported storage adapters. More information about these tests and scripts can be found in the readme inside this directory.
* [**config.yml**] Default configuration file that will be used by the package's API factory to produce a CDB API instance.
* [**Doxyfile**] Configuration file for Doxygen. See Documentation generation for more info.
* [**factory.py**] Module that implements the CDB API factory.
* [**interface.py**] Module that defines the CDB API.
* [**requirements.txt**] Package's Python dependencies list. Can be used by PIP to install the required package dependencies on the target machine.
* [**start_mongodb_locally.sh**] Shell script that starts a local MongoDB server (if installed). See further documentation inside the script.

## Package dependencies
### Python
The required Python dependencies for this package are listed in the `requirements.txt` file. This file can be used by PIP to automatically install these dependencies. Run `pip install -r requirements.txt` from the current directory to install all dependencies.

Make sure to update the `requirements.txt` file whenever there are new dependencies (e.g. when a new storage back-end adapter is implemented).

### Storage back-ends
Storage back-ends actually store the conditions data. A storage back-end can consist of a full-fledged database management system (like MongoDB) or consist of a simple text file. The corresponding back-end adapter will take care of all the necessary translations and operations between the CDB API and the storage back-end. In order to use a specific storage back-end this back-end must be available to the system (i.e. FairSHiP). For every supported storage back-end the required dependencies are listed below.

* [**MongoDB**] A MongoDB server, either installed locally or available via the network. See the User Manual for more info on how to set up a MongoDB server.

### aliBuild integration
Most of the users of the current system rely on the automatic building tool aliBuild. This tool can traverse a dependency graph and install the dependencies on the Operating System, in correct order. The dependencies that we introduced in this project were Python modules. In order for aliBuild to install these modules, we had to update the dependency graph. The specific script that we had to update was python_modules.sh, which contains all the python module related dependencies. Since either using aliBuild or not should have the same result, the dependencies that we included in python_modules.sh are the same as in requirements.txt that is specified above. 

## Documentation generation
For the production of a reference manual, we decided to use the documentation generator Doxygen, which is primary used for C++. Since the majority of the project is not documented according to Doxygen standards, we had to specify which of the files are. This can be done via Doxyfile, which is the configuration file of Doxygen. The specific folder of the project was specified as a starting point. The recursive mechanism for sub-folders was activated and rules for the exclusion of specific sub-folders were introduced.
In order to reproduce the documentation, you should first install doxygen. Then inside the folder conditionsDatabase you will be able to find Doxyfile, which is currently configured for the project. The commands that you should run are the following:

doxygen Doxyfile ---> produces the latex and html files for the reference manual.

cd docs/latex 	 ---> Inside this folder there is a makefile, which will produce the pdf.

make pdf	 ---> Produces the pdf. The name of the file will be refman.pdf

## Supported Python version
This package is developed to work with Python 2. However, wherever possible we tried to use constructs that are compatible with both Python 2 and 3. Also, whenever relevant we documented the code with updates that can be applied when porting to Python 3.
