This is a very basic implementation of a software framework for the SHIP experiment which is based on FairRoot. To use this software you need:

1. Install [FairSoft](https://github.com/FairRootGroup/FairSoft/tree/dev)

    ```bash
    mkdir ~/ShipSoft
    cd ~/ShipSoft
    #git clone https://github.com/FairRootGroup/FairSoft.git
    git clone -b dev https://github.com/FairRootGroup/FairSoft.git
    cd FairSoft
    ./configure.sh
    # clang (on OSX), gcc (on Linux)
    # install G4 files
    # not-optimized
    # ~/ShipSoft/FairSoftInst
    ```

2. Install [FairRoot](http://fairroot.gsi.de/?q=node/82)

    ```bash
    # Set the shell variable SIMPATH to the installation directory
    export SIMPATH=~/ShipSoft/FairSoftInst
    [setenv SIMPATH ~/ShipSoft/FairSoftInst]

    cd ~/ShipSoft
    git clone -b dev https://github.com/FairRootGroup/FairRoot.git
    cd FairRoot
    mkdir build
    cd build
    cmake -DCMAKE_INSTALL_PREFIX="~/ShipSoft/FairRootInst" ..
    make
    make install
    ```

    To run the tests do:

    ```bash
    # To run test: make new shell, do not define SIMPATH
    cd ~/ShipSoft/FairRoot/build
    make test
    ```

3. Install the [SHIP](https://github.com/ShipSoft/FairShip.git) software:

    ```bash
    # Set the shell variable FAIRROOTPATH to the FairRoot installation directory
    export FAIRROOTPATH=~/ShipSoft/FairRootInst
    [setenv FAIRROOTPATH ~/ShipSoft/FairRootInst]

    cd ~/ShipSoft
    git clone https://github.com/ShipSoft/FairShip.git
    mkdir FairShipRun
    cd FairShipRun
    cmake ../FairShip
    make
    . config.sh    [or source config.csh]
    ```

    Now you can for example simulate some events and run the event display:

    ```bash
    root ../FairShip/macro/run_sim.C
    root ../FairShip/macro/eventDisplay.C
    ```

