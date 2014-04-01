This is a very basic implementation of a software framework for the SHIP experiment which is based on FairRoot. To use this software you need:

1. Install [FairSoft](https://github.com/FairRootGroup/FairSoft/tree/dev)

    ```bash
    # First do this (only once) on SLC6 where the github cert is missing
    mkdir ~/certs
    curl http://curl.haxx.se/ca/cacert.pem -o ~/certs/cacert.pem
    git config --global http.sslcainfo ~/certs/cacert.pem
    ```

    ```bash
    mkdir ~/ShipSoft
    cd ~/ShipSoft
    #git clone https://github.com/FairRootGroup/FairSoft.git
    git clone -b dev https://github.com/FairRootGroup/FairSoft.git
    cd FairSoft
    # On SLC6 do: export FC=gfortran
    ./configure.sh
    # 1) gcc (on Linux) 5) Clang (on OSX)
    # 1) No Debug Info
    # 2) Internet (install G4 files from internet)
    # path: ~/ShipSoft/FairSoftInst
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
    root -q ../FairShip/macro/run_sim.C
    root ../FairShip/macro/eventDisplay.C
    // Click on "FairEventManager" (in the top-left pane)
    // Click on the "Info" tab (on top of the bottom-left pane)
    // Increase the "Current Event" to >0 to see the events
    root [1] .q
    ```

Testing psuh mailer.
