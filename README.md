# FairShip

[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/ShipSoft/FairShip/master.svg)](https://results.pre-commit.ci/latest/github/ShipSoft/FairShip/master) [![.github/workflows/build-run.yml](https://github.com/ShipSoft/FairShip/actions/workflows/build-run.yml/badge.svg)](https://github.com/ShipSoft/FairShip/actions/workflows/build-run.yml)

<!-- markdown-toc start - Don't edit this section. Run M-x markdown-toc-refresh-toc -->
**Table of contents**

- [FairShip](#fairship)
    - [Introduction](#introduction)
        - [Branches](#branches)
    - [Build instructions using CVMFS](#build-instructions-using-cvmfs)
    - [Local build, without access to CVMFS](#local-build-without-access-to-cvmfs)
    - [Run instructions](#run-instructions)
    - [Docker instructions](#docker-instructions)
    - [Troubleshooting information](#troubleshooting-information)
    - [Documentation](#documentation)
    - [Contributing code](#contributing-code)

<!-- markdown-toc end -->

## Introduction

FairShip is the software framework for the SHiP experiment which is based on
FairRoot. The dependencies of FairShip are tracked and installed using
[alibuild](https://alisw.github.io/alibuild/).

### Branches

<dl>
  <dt><code>master</code></dt>
  <dd>Main development branch.
      All python code is <b>required to be python 3</b>. Python 2 is no longer supported.
      Requires aliBuild default <code>release</code>.</dd>
  <dt><code>charmdet</code></dt>
  <dd>Branch for the charm cross-section measurement.
      Kept as reference for potential future studies.</dd>
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

## Build Instructions using CVMFS

On `lxplus` this is the recommended way to use `FairShip`. CVMFS can also be setup on your own machine (please see the [CVMFS documentation](https://cvmfs.readthedocs.io/en/stable/cpt-quickstart.html))

1. Download the FairShip software
    ```bash
    git clone https://github.com/ShipSoft/FairShip.git
    ```

2. Make sure you can access the SHiP CVMFS Repository
    ```bash
    ls /cvmfs/ship.cern.ch
    ```
3. Source the `setUp.sh` script from the CVMFS release you want to use (replace `$SHIP_RELEASE` with the release you want to use):
    ```bash
    source /cvmfs/ship.cern.ch/$SHIP_RELEASE/setUp.sh
    ```
    Info about different releases can be found in a [dedicated repository](https://github.com/ShipSoft/cvmfs_release).
    Please report issues with particular releases or the setup script there.

4. Build the software using aliBuild
    ```bash
    aliBuild build FairShip --always-prefer-system --config-dir $SHIPDIST --defaults release
    ```
    If you are not building `master`, you will need to select the appropriate default (see [Branches](#branches)).

If you exit your shell session and you want to go back working on it, make sure to re-execute the third step.

To load the FairShip environment, after you build the software you can simply use:

5. Load the environment
    ```bash
    alienv enter FairShip/latest
    ```

However, this won't work if you are using HTCondor. In such case you can do:

```bash
eval $(alienv load FairShip/latest --no-refresh)
```

## Local build, without access to CVMFS
Commands are similar to the previous case, but without access to CVMFS you need to build the required packages.

1. Install `alibuild` using `pipx` (recommended) or `pip`.
2. Clone the FairShip repository:
    ```bash
    git clone https://github.com/ShipSoft/FairShip.git
    ```
2. Clone the shipdist repository, which contains the recipes to build the software stack:
    ```bash
    git clone https://github.com/ShipSoft/shipdist.git
    ```
2. Build the software using aliBuild:
    ```bash
    aliBuild build FairShip --config-dir $SHIPDIST --defaults release
    ```
    NB: Depending on the platform you might have to pass the `--always-prefer-system` or `--force-unknown-architecture` flags to aliBuild. For debugging, `aliDoctor` is very useful!

3. Load the environment
    ```bash
    alienv enter FairShip/latest
    ```
## Run instructions

Set up the bulk of the environment from CVMFS (see the [dedicated repository](https://github.com/ShipSoft/cvmfs_release) for information about the available releases):

```bash
source /cvmfs/ship.cern.ch/$SHIP_RELEASE/setUp.sh
```

Load your local FairShip environment.

```bash
alienv enter (--shellrc) FairShip/latest
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

## Docker instructions

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

## Troubleshooting information

Please see the wiki for [FAQ](https://github.com/ShipSoft/FairShip/wiki/FAQ-and-common-issues#faq)s and [common issues](https://github.com/ShipSoft/FairShip/wiki/FAQ-and-common-issues#common-issues).

## Documentation

An [automatic class reference](https://shipsoft.github.io/FairShip/) is built using Doxygen from comments in the C++ code. Improving the comments will improve this documentation.

## Contributing code

* Any and all contributions are welcome!
* Contributions via pull requests are preferred, but if you require help with git, don't hesitate to write reach out to us.
* Please split your work into small commits with self-contained changes to make them easy to review and check.
* To help us consistently improve the quality of our code, please try to follow the [C++](https://github.com/ShipSoft/FairShip/wiki/CPP-guidelines) and [Python](https://github.com/ShipSoft/FairShip/wiki/Python-guidelines) guidelines.
