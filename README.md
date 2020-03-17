# FairShip

## Introduction

FairShip is the software framework for the SHiP experiment which is based on
FairRoot. The dependencies of FairShip are tracked and installed using
[alibuild](https://alisw.github.io/alibuild/).

### Branches

<dl>
  <dt><code>master</code></dt>
  <dd>Main development branch.
      All python code is <b>required to be compatible with python 2 and 3</b> until compatibility with python 2 can be dropped.
      Requires aliBuild default <code>fairship</code>.</dd>
  <dt><code>SHiP-2018</code></dt>
  <dd>Frozen branch for the CDS, kept for backward compatibility. 
      Python 2 only.
      Requires aliBuild default <code>fairship-2018</code>.</dd>
  <dt><code>muflux</code></dt>
  <dd>Branch for the muon flux analysis.
      Python 2 only.
      Requires aliBuild default <code>fairship-2018</code>.</dd>
</dl>

All packages are managed in Git and GitHub. Please read [the Git tutorial for
SHiP](https://github.com/ShipSoft/FairShip/wiki/Git-Tutorial-for-SHiP) first,
even if you already know Git, as it explains how development is done on GitHub.


## Prerequisites

All needed pre-requisites are provided by the FairSoft package, see below.

Additionally for developers:
  * clang-format (to format code according to our style guide)
  * clang-tidy (to check coding conventions -- mostly naming rules which are not covered by `cpplint`)

## Build Instructions using CVMFS


## Build Instructions, following [the tutorial given at the Nov'17 collab meeting](https://indico.cern.ch/event/663423/contributions/2760156/attachments/1555373/2445724/Ship-Soft-CollaborationMeetingNov2017.pdf)
0. For a full installation go to step 3. If you work on lxplus, or on SLC6/CC7
   and have access to `/cvmfs/ship.cern.ch`, and you only want to install FairShip, define enviroment variables:
    ```bash
    export SHIPBUILD=/cvmfs/ship.cern.ch/SHiPBuild
    ```    

1. Install FairShip
    ```bash
    git clone https://github.com/ShipSoft/FairShip.git
    cd FairShip
    ./localBuild.sh
    ```    
2. Setup environment
    ```bash

    source FairShipRun/config.sh
    ```    

3. For a full installation on any linux system:

    aliBuild build FairShip --default fairship --always-prefer-system --config-dir $SHIPDIST
    ```
    If you are not building `master`, you will need to select the appropriate default (see [Branches](#branches)).

If you exit your shell session and you want to go back working on it, make sure to re-execute the third step.

To load the FairShip environment, after you build the software you can simply use:

5. Load the environment

    ```bash
    mkdir SHiPBuild; cd SHiPBuild
    git clone https://github.com/ShipSoft/FairShip.git 
    FairShip/aliBuild.sh
    ```    


4. Setup environment
    ```bash
    alibuild/alienv enter (--shellrc) FairShip/latest
    ```    
    
## Docker Instructions
1. Build an docker image from a Dockerfile:

However, this won't work if you are using HTCondor. In such case you can do:

```bash
eval alienv load FairShip/latest
```

## Local build, without access to CVMFS
Commands are similar to the previous case, but without access to CVMFS you need to build the required packages.
1. Download the FairShip software

    ```bash
    git clone https://github.com/ShipSoft/FairShip.git
    ```
2. Build the software using aliBuild
    ```bash
    FairShip/aliBuild.sh
    ```
3. Load the environment
    ```bash
    alibuild/alienv enter FairShip/latest
    ```
## Run Instructions

Partial installation, step 1 of above :

```bash
source FairShipRun/config.sh
```    

If you have a full installation, step 3 of above:

```bash
alibuild/alienv enter (--shellrc) FairShip/latest
```    

Now you can for example simulate some events, run reconstruction and analysis:

```bash
python $FAIRSHIP/macro/run_simScript.py
>> Macro finished succesfully.
>> Output file is  ship.conical.Pythia8-TGeant4.root

python $FAIRSHIP/macro/ShipReco.py -f ship.conical.Pythia8-TGeant4.root -g geofile_full.conical.Pythia8-TGeant4.root
>> finishing pyExit

python -i $FAIRSHIP/macro/ShipAna.py -f ship.conical.Pythia8-TGeant4_rec.root -g geofile_full.conical.Pythia8-TGeant4.root
>> finished making plots
```

Run the event display:

```bash
python -i $FAIRSHIP/macro/eventDisplay.py -f ship.conical.Pythia8-TGeant4_rec.root -g geofile_full.conical.Pythia8-TGeant4.root
// use SHiP Event Display GUI
Use quit() or Ctrl-D (i.e. EOF) to exit
```

## Docker Instructions

Docker is **not** the recommended way to run `FairShip` locally. It is ideal
for reproducing reproducible, stateless environments for debugging, HTCondor
and cluster use, or when a strict separation between `FairShip` and the host is
desirable.

1. Build an docker image from the provided `Dockerfile`:
    ```bash
    git clone https://github.com/ShipSoft/FairShip.git
    cd FairShip
    docker build -t fairship .
    ``` 
2. Run the `FairShip` docker image:
    ```bash
    docker run -i -t --rm fairship /bin/bash
    ``` 
3. Advanced docker run options:
    ```bash
    docker run -i -t --rm \
    -e DISPLAY=unix$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix \
    -v /local_workdir:/image_workdir \
    fairship /bin/bash
    ``` 
    The option `-e DISPLAY=unix$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix` forwards graphics from the docker to your local system (similar to `ssh -X`). The option `-v /local_workdir:/image_workdir` mounts `/local_workdir` on the local system as `/image_workdir` within docker.

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
