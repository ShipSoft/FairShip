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

    ```
    If you work on lxplus, you should use SHIPSOFT=/cvmfs/ship.cern.ch/ShipSoft/gcc62, and skip to point 5 (no need to install FairSoft and FairRoot)

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
    setenv SHIPSOFT /cvmfs/ship.cern.ch/ShipSoft/gcc62
    setenv FAIRROOTPATH ${SHIPSOFT}/FairRootInst
    setenv SIMPATH      ${SHIPSOFT}/FairSoftInst
    setenv FAIRSHIP ${xxx}/FairShip
    source ${xxx}/FairShipRun/config.(c)sh
    ```

6. Now you can for example simulate some events, run reconstruction and analysis:

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
7. Some git hints:

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


