#!/bin/bash
# Pixi activation script for FairShip runtime environment
# Sourced automatically by `pixi run` / `pixi shell`
export FAIRSHIP="$PIXI_PROJECT_ROOT"
export FAIRSHIP_ROOT="$PIXI_PROJECT_ROOT"
export VMCWORKDIR="$PIXI_PROJECT_ROOT"
export GEOMPATH="$PIXI_PROJECT_ROOT/geometry"
export CONFIG_DIR="$PIXI_PROJECT_ROOT/gconfig"
# conda-forge's evtgen sets EVTGEN_ROOT; FixedTargetGenerator reads EVTGENDATA.
export EVTGENDATA="${EVTGEN_ROOT:-$CONDA_PREFIX/share/EvtGen}"
# shipRoot_conf.py uses GENFIT_ROOT to load libgenfit2 and locate headers.
export GENFIT_ROOT="$CONDA_PREFIX"
export PYTHONPATH="$PIXI_PROJECT_ROOT/build/lib:$PIXI_PROJECT_ROOT/python${PYTHONPATH:+:$PYTHONPATH}"
export LD_LIBRARY_PATH="$PIXI_PROJECT_ROOT/build/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
