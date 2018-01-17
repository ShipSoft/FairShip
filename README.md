# FairShip

## Introduction

FairShip is the software framework for the SHiP experiment which is based on FairRoot. To use this software you need to install three packages: FairSoft, FairRoot and FairShip. The first two
pacakges are quite stable and you don't have to modify them. They will be updated
infrequently only when the FairRoot team releases a new version. In such a case you will be
warned and you have to rebuild them. All packages are managed in Git and GitHub. Please
read [the Git tutorial for SHiP](https://github.com/ShipSoft/FairShip/wiki/Git-Tutorial-for-SHiP) first, even if you already know Git, as it explains how development is done on GitHub.

## Prerequisites

All needed pre-requisites are provided by the FairSoft package, see below.

Additionally for developers:
  * clang-format (to format code according to our style guide)
  * clang-tidy (to check coding conventions -- mostly naming rules which are not covered by `cpplint`)

## Build Instructions, following tutorial given at Nov'17 collab meeting https://indico.cern.ch/event/663423/contributions/2760156/attachments/1555373/2445724/Ship-Soft-CollaborationMeetingNov2017.pdf 
0. For a full installation go to step 3. f you work on lxplus, or on SLC6/7 and have access to /cvmfs/ship.cern.ch, and you only want to install FairShip, define enviroment variables:
    ```bash
    export SHIPBUILD=/cvmfs/ship.cern.ch/SHiPBuild
    ```    

1. Install [FairShip]
    ```bash
    git clone https://github.com/ShipSoft/FairShip.git
    cd FairShip
    ./localConfig.sh
    ```    
2. Setup environment
    ```bash
    source FairShipRun/config.sh
    ```    

3. For a full installation on any linux system:
    ```bash
    mkdir SHiPBuild; cd SHiPBuild
    git clone https://github.com/ShipSoft/FairShip.git 
    FairShip/aliBuild.sh
    ```    

4. Setup environment
    ```bash
    alibuild/alienv enter (--shellrc) FairShip/latest
    ```    


## Old Build Instructions, not recommended anymore
0. If you work on lxplus, or on SLC6/7 and have access to /cvmfs/ship.cern.ch, define enviroment variables:
    ```bash
    export SHIPSOFT=/cvmfs/ship.cern.ch/ShipSoft
    export FAIRROOTPATH=${SHIPSOFT}/FairRootInst
    export SIMPATH=${SHIPSOFT}/FairSoftInst
    ```    
    move to step 4.

1. In case you use SLC6 where the GitHub cert is missing, first do (only once):

    ```bash
    mkdir ~/certs
    curl http://curl.haxx.se/ca/cacert.pem -o ~/certs/cacert.pem
    git config --global http.sslcainfo ~/certs/cacert.pem
    ```

2. Install [FairSoft]

    ```bash
    mkdir ~/ShipSoft    [ or where ever you like to place the software ]
    cd ~/ShipSoft
    git clone https://github.com/ShipSoft/FairSoft.git
    cd FairSoft
    cat DEPENDENCIES
    # Make sure all the required dependencies are installed
    ./configure.sh
    # Accept ShipSoft default
    # Experts can fine-tune if they like
    ```

3. Install [FairRoot]

    ```bash
    cd ~/ShipSoft
    git clone  https://github.com/ShipSoft/FairRoot.git
    cd FairRoot
    ./configure.sh
    ```

4. Install the [SHiP](https://github.com/ShipSoft/FairShip.git) software:

    ```bash
    cd ~/ShipSoft
    git clone https://github.com/ShipSoft/FairShip.git
    cd FairShip
    ./configure.sh
    ```

    To only compile FairShip, e.g. after the initial install and after having edited files, do:

    ```bash
    cd ~/ShipSoft/FairShipRun
    make
    ```

## Run Instructions

Before running the [SHiP](https://github.com/ShipSoft/FairShip.git) software, set the necessary environment by doing:

    ```bash
    source ~/ShipSoft/FairShipRun/config.[c]sh
    ```

Or if you work on lxplus, after logon, you have to do, for bash users:

    ```bash
    export xxx ~/myship    [ or where ever you like to place the software ]
    export SHIPSOFT=/cvmfs/ship.cern.ch/ShipSoft/gcc62
    export SIMPATH=$SHIPSOFT/FairSoftInst
    export FAIRROOTPATH=$SHIPSOFT/FairRootInst
    export FAIRSHIP=$xxx/FairShip
    source $xxx/FairShipRun/config.sh
    ```

And for csh users:

    ```bash
    setenv xxx ~/myship    [ or where ever you like to place the software ]
    setenv SHIPSOFT /cvmfs/ship.cern.ch/ShipSoft/gcc62
    setenv SIMPATH      ${SHIPSOFT}/FairSoftInst
    setenv FAIRROOTPATH ${SHIPSOFT}/FairRootInst
    setenv FAIRSHIP ${xxx}/FairShip
    source ${xxx}/FairShipRun/config.csh
    ```

Now you can for example simulate some events, run reconstruction and analysis:

    ```bash
    python $FAIRSHIP/macro/run_simScript.py
    >> Macro finished succesfully.
    >> Output file is  ship.conical.Pythia8-TGeant4.root

    python $FAIRSHIP/macro/ShipReco.py -f ship.conical.Pythia8-TGeant4.root -g geofile_full.conical.Pythia8-TGeant4.root
    >> finishing pyExit

    python -i $FAIRSHIP/macro/ShipAna.py -f ship.10.0.Pythia8-TGeant4_rec.root -g geofile_full.conical.Pythia8-TGeant4.root
    >> finished making plots
    ```

Run the event display:

    ```bash
    python -i $FAIRSHIP/macro/eventDisplay.py -f ship.10.0.Pythia8-TGeant4_rec.root -g geofile_full.conical.Pythia8-TGeant4.root
    // use SHiP Event Display GUI
    Use quit() or Ctrl-D (i.e. EOF) to exit
    ```

## Running Previous Versions

Some git hints on how to run previously tagged versions:

    ```bash
    mkdir $SHIPSOFT/v1
    cd $SHIPSOFT/v1
    git clone -b dev https://github.com/ShipSoft/FairSoft.git
    cd $SHIPSOFT/v1/FairSoft
    git checkout -b v1-00 v1-00
    ./configure.sh
    cd $SHIPSOFT/v1
    git clone -b dev https://github.com/ShipSoft/FairRoot.git
    cd $SHIPSOFT/v1/FairRoot
    git checkout -b v1-00 v1-00
    ./configure.sh
    cd $SHIPSOFT/v1
    git clone https://github.com/ShipSoft/FairShip.git
    cd FairShip
    git checkout -b v1-00 v1-00
    ./configure.sh
    cd ../FairShipRun
    source config.sh
    ```

## Contributing Code

### Build Targets Related to C++ Code Style-Guide

The following targets are only available if `clang-format`, `clang-tidy` and `git` are installed.

Build targets indicated with `*` always come in three different flavors.
  * `no-suffix`: executes the target on source files that changed compared to origin/master -- e.g. `make check-format`
  * `-staged`: executes the target on source files that have been staged -- e.g. `make check-format-staged`
  * `-all`: executes the target on all source files in the project -- e.g. `make check-format-all`

| Target          | Description  |
| --------------- | ------------ |
| `check-format*` | run clang-format on selected files. Fails if any file needs to be reformatted |
| `show-format*` | run clang-format on selected files and display differences |
| `format*` | run clang-format on selected files and update them in-place |
| `check-tidy*` | run clang-tidy on selected files. Fails if errors are found |
| `show-tidy*` | run clang-tidy on selected files and display errors. |
| `tidy*` | run clang-tidy on selected files and attempt to fix any warning automatically |
| `check-cpplint*` | run cpplint on selected files. Fails if errors are found and displays them. |
| `check-submission` | will build, run all tests, check formatting, code style, and generate documentation and coverage report |
| `fix-submission` | will attempt to fix the reported issues using `clang-format` and `clang-tidy`. Failing build, tests, compiler warnings, issues from cpplint and warnings from doxygen must be fixed manually. Also some `clang-tidy` issues cannot be resolved automatically |
