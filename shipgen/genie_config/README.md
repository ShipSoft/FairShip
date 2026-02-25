# Configuration files for GENIE simulations

## Introduction

Following ROOT's deprecation of TPythia6, these files replace the Pythia6Decayer
with Pythia8Decayer in GENIE.

## Details

For more information, see:

- https://genie-mc.github.io/releases.html
- https://github.com/GENIE-MC/Generator/pull/430

To use these files, set the `GXMLPATH` environment variable to this folder before
launching the simulation. This is done automatically by `makeGenieEvents.py`.

This folder mirrors the structure of the default GENIE configuration and currently
only contains the files needed to switch from Pythia6Decayer to Pythia8Decayer.

## History

- February 2026: Initial creation (Antonio Iuliano)

## Notes on particle decays

Particle decays were previously configured in `UserPhysicsOptions.xml`. They are
now provided in a "tune" folder. See for example:
https://github.com/SND-LHC/sndsw/blob/master/shipgen/genie_config/SNDGHE19_00b/CommonDecay.xml

GENIE no longer decays tau and charmed hadrons by default (this was the default
in our old branch: https://github.com/ShipSoft/GENIE/blob/v2.12.6-ship2021/config/UserPhysicsOptions.xml),
so we no longer need to override these settings.
