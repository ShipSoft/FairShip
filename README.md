# FairShip

[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/ShipSoft/FairShip/master.svg)](https://results.pre-commit.ci/latest/github/ShipSoft/FairShip/master) [![Pixi Build](https://github.com/ShipSoft/FairShip/actions/workflows/pixi-build.yml/badge.svg)](https://github.com/ShipSoft/FairShip/actions/workflows/pixi-build.yml) [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.18020628.svg)](https://doi.org/10.5281/zenodo.18020628)[![REUSE status](https://api.reuse.software/badge/github.com/ShipSoft/FairShip)](https://api.reuse.software/info/github.com/ShipSoft/FairShip)

<!-- markdown-toc start - Don't edit this section. Run M-x markdown-toc-refresh-toc -->
**Table of contents**

- [FairShip](#fairship)
    - [Introduction](#introduction)
        - [Branches](#branches)
    - [Using pixi](#using-pixi)
    - [Run instructions](#run-instructions)
    - [Docker instructions](#docker-instructions)
    - [Troubleshooting information](#troubleshooting-information)
    - [Documentation](#documentation)
    - [License](#license)
    - [Contributing code](#contributing-code)
    - [Legacy releases (CVMFS + aliBuild)](#legacy-releases-cvmfs--alibuild)

<!-- markdown-toc end -->

## Introduction

FairShip is the software framework for the SHiP experiment which is based on
FairRoot. Its dependencies are managed with [pixi](https://pixi.sh) — see
[Using pixi](#using-pixi) below. See the
[FairShip wiki](https://github.com/ShipSoft/FairShip/wiki) for additional
documentation.

### Branches

<dl>
  <dt><code>master</code></dt>
  <dd>Main development branch.
      All python code is <b>required to be python 3</b>. Python 2 is no longer supported.</dd>
  <dt><code>charmdet</code></dt>
  <dd>Branch for the charm cross-section measurement.
      Kept as reference for potential future studies.</dd>
  <dt><code>SHiP-2018</code></dt>
  <dd>Frozen branch for the CDS, kept for backward compatibility.
      Python 2 only. Builds via the
      <a href="#legacy-releases-cvmfs--alibuild">legacy aliBuild path</a> only.</dd>
  <dt><code>muflux</code></dt>
  <dd>Branch for the muon flux analysis.
      Python 2 only. Builds via the
      <a href="#legacy-releases-cvmfs--alibuild">legacy aliBuild path</a> only.</dd>
</dl>

All packages are managed in Git and GitHub. Please read [the Git tutorial for
SHiP](https://github.com/ShipSoft/FairShip/wiki/Git-Tutorial-for-SHiP) first,
even if you already know Git, as it explains how development is done on GitHub.

## Using pixi

[Pixi](https://pixi.sh) manages all dependencies via the `pixi.toml` and
`activate.sh` already included in this repository. The activation script sets
`FAIRSHIP` and `GEOMPATH` (among others) to `PIXI_PROJECT_ROOT`, so the pixi
project root **must** be the FairShip clone itself — it contains the required
`geometry/` and `files/` directories.

PS: no need to source the environment from cvmfs with this...

### Build from source (recommended)

1. [Install pixi](https://pixi.sh/latest/#installation) if you haven't already.

   ```bash
   curl -fsSL https://pixi.sh/install.sh | sh
   ```
   Check the location of .pixi and .cache files that it has enough space, about 12 GB required!
   ```bash
   pixi info
   ```
   And if required, move the .pixi and .cache directories and set the environment variables to where you want them in .bashrc:
   ```bash
   export PATH="<full_path>/.pixi/bin:$PATH"
   export PIXI_HOME=<full_path>/.pixi
   export PIXI_CACHE_DIR=<full_path>/.cache
   ```
(PS: Remember to source again the .bashrc to set them properly)

2. Clone and build:
    ```bash
    git clone https://github.com/ShipSoft/FairShip.git
    cd FairShip
    pixi run build
    ```

3. Run commands inside the environment:
   The following requires to be inside FairShip/
   ```bash
    pixi run python macro/run_simScript.py --tag my-simulation
    ```

    Or start a shell, within FairShip/, from which you can "cd" into any workdir of your choice:
    ```bash
    pixi shell
    cd <path_to_your_workdir>
    python <path_to_FairShip>/macro/run_simScript.py --tag my-simulation
    ```

### Using the pre-built package

Pre-built FairShip packages are available from the
[ship](https://prefix.dev/channels/ship) channel. Because `activate.sh`
expects `geometry/`, `files/`, and other data directories at
`PIXI_PROJECT_ROOT`, the simplest approach is to add `fairship` directly to
the clone:

```bash
git clone https://github.com/ShipSoft/FairShip.git
cd FairShip
pixi add fairship
pixi run python macro/run_simScript.py --tag my-simulation
```

## Run instructions

Start a shell with the FairShip environment activated:

```bash
pixi shell
```

(Or prefix individual commands with `pixi run`.) Then you can simulate some
events, run reconstruction and analysis:

```bash
python $FAIRSHIP/macro/run_simScript.py --tag my-simulation
>> [...]
>> Macro finished successfully.
>> [...]
>> Output file is  sim_my-simulation.root
>> Geometry file is geo_my-simulation.root
>> [...]

python $FAIRSHIP/macro/ShipReco.py -f sim_my-simulation.root -g geo_my-simulation.root
>> [...]
>> finished writing tree
>> Exit normally
>> (This creates sim_my-simulation_rec.root with digitisation and reconstruction data)

python -i $FAIRSHIP/macro/ShipAna.py -f sim_my-simulation.root -r sim_my-simulation_rec.root -g geo_my-simulation.root
>> finished making plots
>> Exit normally
```

**Note**: Simulation output files use the naming convention `{sim,geo,params}_{identifier}.root`, where the identifier is either a UUID (auto-generated) or a custom tag specified with `--tag`. ShipReco creates a separate reconstruction file (`*_rec.root`) containing only digitisation and reconstruction branches. The original simulation file is not modified. ShipAna uses both files via ROOT's friend tree mechanism to access both MC truth and reconstruction data.

Alternatively, you can make use of the experimental `analysis_toolkit` to run a simple pre-selection check on the events. An example script can be found in `$FAIRSHIP/examples/analysis_example.py`.

Simulate MC signal events with EventCalc:

```bash
python $FAIRSHIP/macro/convertEvtCalc.py -f test_input.dat -o test_folder
```
and then:
```bash
python $FAIRSHIP/macro/run_simScript.py --evtcalc -n 1 -o test_folder -f test_folder/test_input.root
```

Run the event display:

```bash
python -i $FAIRSHIP/macro/eventDisplay.py -f sim_my-simulation.root -r sim_my-simulation_rec.root -g geo_my-simulation.root
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

## License

FairShip is distributed under the GNU Lesser General Public License v3.0 or later (LGPL-3.0-or-later). See the [LICENSE](LICENSE) file for details.

Copyright is held by CERN for the benefit of the SHiP Collaboration. Some components are distributed under different licenses and copyrights - see the individual file headers and the [LICENSES](LICENSES/) directory for details. This project follows the [REUSE specification](https://reuse.software/) for licensing information.

## Contributing code

* Any and all contributions are welcome!
* Contributions via pull requests are preferred, but if you require help with git, don't hesitate to write reach out to us.
* Please split your work into small commits with self-contained changes to make them easy to review and check.
* To help us consistently improve the quality of our code, please try to follow the [C++](https://github.com/ShipSoft/FairShip/wiki/CPP-guidelines) and [Python](https://github.com/ShipSoft/FairShip/wiki/Python-guidelines) guidelines.

## Legacy releases (CVMFS + aliBuild)

aliBuild on top of a CVMFS-provided toolchain was the supported default up to
and including release **26.05**. From **26.06** onwards [pixi](#using-pixi) is
the recommended build path; CVMFS images of newer releases (e.g. 26.06) may
still be published for convenience, but are no longer the primary
distribution channel. These instructions are kept for users running existing
CVMFS releases and for legacy branches (`SHiP-2018`, `muflux`). The
[shipdist](https://github.com/ShipSoft/shipdist) repository (aliBuild recipes)
is now in maintenance mode.

### With CVMFS (lxplus and similar)

1. Clone the FairShip software (initialise `git-lfs` first if you've never
   used it):
    ```bash
    git lfs install
    git clone https://github.com/ShipSoft/FairShip.git
    ```
2. Make sure CVMFS is mounted:
    ```bash
    ls /cvmfs/ship.cern.ch
    ```
3. Source the chosen release (see the
   [cvmfs_release](https://github.com/ShipSoft/cvmfs_release) repo for the
   list):
    ```bash
    source /cvmfs/ship.cern.ch/$SHIP_RELEASE/setUp.sh
    ```
4. Build with aliBuild:
    ```bash
    aliBuild build FairShip --always-prefer-system --config-dir $SHIPDIST --defaults release
    ```
    For legacy branches, swap `--defaults release` for `--defaults fairship-2018`.
5. Load the environment:
    ```bash
    alienv enter FairShip/latest
    ```
    Or, in non-interactive contexts (e.g. HTCondor):
    ```bash
    eval $(alienv load FairShip/latest --no-refresh)
    ```

### Without CVMFS

1. Install [aliBuild](https://alisw.github.io/alibuild/) via `pipx` or `pip`.
2. Clone [shipdist](https://github.com/ShipSoft/shipdist) alongside FairShip:
    ```bash
    git clone https://github.com/ShipSoft/shipdist.git
    ```
3. Build:
    ```bash
    aliBuild build FairShip --config-dir ./shipdist --defaults release
    ```
    Pass `--always-prefer-system` or `--force-unknown-architecture` if needed;
    `aliDoctor` helps when something doesn't resolve.
4. Load the environment:
    ```bash
    alienv enter FairShip/latest
    ```
