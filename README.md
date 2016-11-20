FairShip is the software framework for the SHiP experiment which is based on FairRoot. To use this software you need to install three packages: FairSoft, FairRoot and FairShip. The first two
pacakges are quite stable and you don't have to modify them. They will be updated
infrequently only when the FairRoot team releases a new version. In such a case you will be
warned and you have to rebuild them. All packages are managed in Git and GitHub. Please
read [the Git tutorial for SHiP](https://github.com/ShipSoft/FairShip/wiki/Git-Tutorial-for-SHiP) first, even if you already know Git as it explains how development is done on GitHub.

Let get started:

1 December 2015: FairSoft and FairRoot are put in place with simplified configurations scripts

1. In case you use SLC6 where the GitHub cert is missing, first do (only once):

    ```bash
    mkdir ~/certs
    curl http://curl.haxx.se/ca/cacert.pem -o ~/certs/cacert.pem
    git config --global http.sslcainfo ~/certs/cacert.pem
    ```

2. Set several required shell variables, needed during the installation and running of the
   different software packages. Put these in your shell's rc file (~/.bashrc or ~/.cshrc).
   For bash:

    ```bash
    export SHIPSOFT=~/ShipSoft
    export SIMPATH=$SHIPSOFT/FairSoftInst
    export FAIRROOTPATH=$SHIPSOFT/FairRootInst
    ```

    or for the csh:

    ```bash
    setenv SHIPSOFT ~/ShipSoft
    setenv SIMPATH ${SHIPSOFT}/FairSoftInst
    setenv FAIRROOTPATH ${SHIPSOFT}/FairRootInst
    ```

3. Install [FairSoft]

    ```bash
    mkdir $SHIPSOFT
    cd $SHIPSOFT
    git clone https://github.com/ShipSoft/FairSoft.git
    cd FairSoft
    cat DEPENDENCIES
    # Make sure all the required dependencies are installed
    ./configure.sh
    # accept ShipSoft default
    # no, for experts
    ```

4. Install [FairRoot]

    ```bash
    cd $SHIPSOFT
    git clone  https://github.com/ShipSoft/FairRoot.git
    cd FairRoot
    mkdir build
    ./configure.sh
    ```

5. Install the [SHIP](https://github.com/ShipSoft/FairShip.git) software:

    ```bash
    cd $SHIPSOFT (or at any other place XXX
    git clone https://github.com/ShipSoft/FairShip.git
    cd FairShip
    ./configure.sh
    
    for only compiling
    cd FairShipRun
    make
    
    If you work on lxplus, after logon, you always have to do:
    setenv xxx ${HOME}
    setenv SHIPSOFT /afs/cern.ch/ship/sw/ShipSoft/dev
    setenv FAIRROOTPATH ${SHIPSOFT}/FairRootInst
    setenv SIMPATH      ${SHIPSOFT}/FairSoftInst
    setenv FAIRSHIP ${xxx}/FairShip
    source ${xxx}/FairShipRun/config.(c)sh
    ```

Old procedure:

1. In case you use SLC6 where the GitHub cert is missing, first do (only once):

    ```bash
    mkdir ~/certs
    curl http://curl.haxx.se/ca/cacert.pem -o ~/certs/cacert.pem
    git config --global http.sslcainfo ~/certs/cacert.pem
    ```

2. Set several required shell variables, needed during the installation and running of the
   different software packages. Put these in your shell's rc file (~/.bashrc or ~/.cshrc).
   For bash:

    ```bash
    export SHIPSOFT=~/ShipSoft
    export SIMPATH=$SHIPSOFT/FairSoftInst
    export FAIRROOTPATH=$SHIPSOFT/FairRootInst
    export FAIRSHIP=$SHIPSOFT/FairShip
    export FAIRSHIPRUN=$SHIPSOFT/FairShipRun
    ```

    or for the csh:

    ```bash
    setenv SHIPSOFT ~/ShipSoft
    setenv SIMPATH ${SHIPSOFT}/FairSoftInst
    setenv FAIRROOTPATH ${SHIPSOFT}/FairRootInst
    setenv FAIRSHIP ${SHIPSOFT}/FairShip
    setenv FAIRSHIPRUN ${SHIPSOFT}/FairShipRun
    ```

3. Install [FairSoft](https://github.com/FairRootGroup/FairSoft/tree/dev)

    ```bash
    mkdir $SHIPSOFT
    cd $SHIPSOFT
    git clone -b master https://github.com/ShipSoft/FairSoft.git
    cd FairSoft
    cat DEPENDENCIES
    # Make sure all the required dependencies are installed
    # On SLC6 do: export FC=gfortran
    ./configure.sh
    # 1) gcc (on Linux) 5) Clang (on OSX)
    # 3) Optimization
    # 1) Yes (install Simulation)
    # 2) Internet (install G4 files from internet)
    # 1) Yes (install python bindings)
    # path: $SHIPSOFT/FairSoftInst [$SIMPATH is set in script]
    ```

4. Install [FairRoot](http://fairroot.gsi.de/?q=node/82)

    ```bash
    cd $SHIPSOFT
    git clone -b master https://github.com/ShipSoft/FairRoot.git
    cd FairRoot
    mkdir build
    cd build
    cmake .. -DCMAKE_INSTALL_PREFIX=$FAIRROOTPATH -DCMAKE_BUILD_TYPE=RELEASE
    ( 
     on some platforms eventually use: 
     cmake .. -DCMAKE_INSTALL_PREFIX=$FAIRROOTPATH -DCMAKE_BUILD_TYPE=RELEASE -DUSE_DIFFERENT_COMPILER=TRUE
    )
    make
    make install
    ```

    To run the tests do:

    ```bash
    cd $SHIPSOFT/FairRoot/build
    make test
    ```

5. Install the [SHIP](https://github.com/ShipSoft/FairShip.git) software:

    ```bash
    cd $SHIPSOFT (or at any other place XXX, assuming environment variable FAIRSHIP set to XXX/FairShip
    git clone https://github.com/ShipSoft/FairShip.git
    mkdir FairShipRun
    cd FairShipRun
    cmake ../FairShip
    ( 
     on some platforms eventually use: 
     cmake ../FairShip -DUSE_DIFFERENT_COMPILER=TRUE
    )
    make
    . config.sh    [or source config.csh]
    
    If you work on lxplus, after logon, you always have to do:
    setenv xxx ${HOME}
    setenv SHIPSOFT /afs/cern.ch/ship/sw/ShipSoft
    setenv FAIRROOTPATH ${SHIPSOFT}/FairRootInst
    setenv SIMPATH      ${SHIPSOFT}/FairSoftInst
    setenv FAIRSHIP ${xxx}/FairShip
    source ${xxx}/FairShipRun/config.csh
    ```

6. Now you can for example simulate some events, run reconstruction and analysis:

    ```bash
    python $FAIRSHIP/macro/run_simScript.py 
    >> Macro finished succesfully.
    >> Output file is  ship.10.0.Pythia8-TGeant4.root

    python $FAIRSHIP/macro/ShipReco.py -f ship.10.0.Pythia8-TGeant4.root -g geofile_full.10.0.Pythia8-TGeant4.root
    >> finishing pyExit

    python $FAIRSHIP/macro/ShipAna.py -f ship.10.0.Pythia8-TGeant4_rec.root -g geofile_full.10.0.Pythia8-TGeant4.root
    >> finished making plots
    ```

    Run the event display:

    ```bash
    python -i $FAIRSHIP/macro/eventDisplay.py -f ship.10.0.Pythia8-TGeant4.root -g geofile_full.10.0.Pythia8-TGeant4.root
    // use SHiP Event Display GUI 
    // to switch on / off detectors (little trick to make it faster, main window, tick off Scenes/Geometry scene, then switch on / off detectors in SHiP Event Display GUI, then tick on again Scenes/Geometry scene)
    // hit next event, or enter event number and hit return
    Use quit() or Ctrl-D (i.e. EOF) to exit
    ```
7. Retrieving tagged versions:

    ```bash
    mkdir $SHIPSOFT/v1
    cd $SHIPSOFT/v1
    git clone -b dev https://github.com/ShipSoft/FairSoft.git
    cd $SHIPSOFT/v1/FairSoft
    git checkout -b v1-00 v1-00
    // installation procedure as above
    cd $SHIPSOFT/v1
    git clone -b dev https://github.com/ShipSoft/FairRoot.git
    cd $SHIPSOFT/v1/FairRoot
    git checkout -b v1-00 v1-00
    // installation procedure as above
    cd $SHIPSOFT/v1
    git clone https://github.com/ShipSoft/FairShip.git
    cd FairShip
    git checkout -b v1-00 v1-00
    // installation procedure as above
    ```


