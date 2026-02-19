# Config files for GENIE simulations without Pythia6Decayer

## Intro

Following ROOT deprecation of TPythia6,

these files replace the Pythia6Decayer with Pythia8Decayer.

## Details

For info, see:

* https://genie-mc.github.io/releases.html
* https://github.com/GENIE-MC/Generator/pull/430

to use them, set GXMLPATH env variable to this folder before launching this simulation.

To avoid confusion, this folder is exactly the same as the GENIE one.

Therefore, it does not contain any modifications we would like to make.

For that, it is best to create our own tune config folder, with these files and any additional change we may need.

See comment line down.

## Creation Date

Antonio Iuliano, 18 February 2026

## Unrelated comments
Particle Decays were once set in UsersPhyicsOptions.xml

Now they are provided in a "tune" folder, see for example

https://github.com/SND-LHC/sndsw/blob/master/shipgen/genie_config/SNDGHE19_00b/CommonDecay.xml

GENIE by default does not make tau and charmed hadron decay anymore.

(That was the default in our old branch, 

https://github.com/ShipSoft/GENIE/blob/v2.12.6-ship2021/config/UserPhysicsOptions.xml)

So we do not need to override these lines anymore.
