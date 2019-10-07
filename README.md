# FairShip

## Introduction

FairShip is the software framework for the SHiP experiment which is based on
FairRoot. The dependencies of FairShip are tracked and installed using
[alibuild](https://alisw.github.io/alibuild/).

All packages are managed in Git and GitHub. Please read [the Git tutorial for
SHiP](https://github.com/ShipSoft/FairShip/wiki/Git-Tutorial-for-SHiP) first,
even if you already know Git, as it explains how development is done on GitHub.

## Prerequisites

All needed pre-requisites are provided by the FairSoft package, see below.

Additionally for developers:
  * clang-format (to format code according to our style guide)
  * clang-tidy (to check coding conventions -- mostly naming rules which are not covered by `cpplint`)
 
## Build Instructions using CVMFS

1. Download the FairShip software
    ```bash
    git clone https://github.com/ShipSoft/FairShip.git
    ```

2. Make sure you can access the SHiP CVMFS Repository
    ```bash
    ls /cvmfs/ship.cern.ch
    ```
3. Source the setUp script
    ```bash
    source /cvmfs/ship.cern.ch/SHiP-2018/latest/setUp.sh
    ```

4. Build the software using aliBuild
    ```bash
    aliBuild build FairShip --default fairship-2018 --always-prefer-system --config-dir $SHIPDIST
    ```

If you exit your shell session and you want to go back working on it, make sure to re-execute the third step.

To load the FairShip environement, after you build the software you can simply use:

5. Load the environment
    ```bash
    alienv enter FairShip/latest
    ```

However, this won't work if you are using HTCondor. In such case you can do:
    ```bash
    eval `alienv load FairShip/latest
    ```

## Docker Instructions
1. Build an docker image from a Dockerfile:
    ```bash
    git clone https://github.com/ShipSoft/FairShip.git
    cd FairShip
    docker build -t fairship .
    ``` 
2. Run the FairShip docker image:
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
    Line ```-e DISPLAY=unix$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix``` forwards graphics from the image to your local system         (similar to ssh -X). Line ```-v /local_workdir:/image_workdir``` shares ```/local_workdir``` directory on the local system with ```/image_workdir``` directory on the docker image system.

## Run Instructions

Set up the bulk of the environment from CVMFS.

```bash
source /cvmfs/ship.cern.ch/SHiP-2018/latest/setUp.sh
```

Load your local FairShip environment.

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
