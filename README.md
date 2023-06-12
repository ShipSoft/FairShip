# FairShip

<!-- markdown-toc start - Don't edit this section. Run M-x markdown-toc-refresh-toc -->
**Table of Contents**

- [FairShip](#fairship)
    - [Introduction](#introduction)
        - [Branches](#branches)
    - [Build Instructions using CVMFS](#build-instructions-using-cvmfs)
    - [Local build, without access to CVMFS](#local-build-without-access-to-cvmfs)
    - [Run Instructions](#run-instructions)
    - [Docker Instructions](#docker-instructions)
    - [Contributing Code](#contributing-code)

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
    source /cvmfs/ship.cern.ch/SHiP-2022/May/setUp.sh
    ```

4. Build the software using aliBuild
    ```bash
    aliBuild build FairShip --always-prefer-system --config-dir $SHIPDIST
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

Set up the bulk of the environment from CVMFS.

```bash
source /cvmfs/ship.cern.ch/SHiP-2022/May/setUp.sh
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

* Any and all contributions are welcome!
* Contributions via pull requests are preferred, but if you require help with git, don't hesitate to write reach out to us.
* Please split your work into small commits with self-contained changes to make them easy to review and check.
