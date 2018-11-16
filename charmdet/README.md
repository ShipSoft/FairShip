# Simulation for Charm cross section and Muon flux measurements

## Geometry classes

This folder contains the geometry classes for the detectors used in charm cross section and Muon flux measurements.

Classes currently used by charm simulation:

* `Box` class: Emulsion Target 
* `Spectrometer` class: Pixel and SciFi detectors
* `MufluxSpectrometer` class: Goliath structure and Drift Tubes T3 and T4  
* `MuonTagger` class: RPCs for muon identification  


Classes currently used by muon flux simulation:  

* `MufluxSpectrometer` class: Tracking stations T1 through T4
* `MuonTagger` class: RPCs for muon identification
* `Scintillator` class: drift tube trigger scintillators (i.e. S2)
* `ReProcessAbsorber`

`Point` classes are used for MonteCarlo simulations and contain MC truth
information, `Hit` class when present are used for digitization and
reconstruction (used for muon flux measurement, still absent for charm cross
section)

## Simulations for charm cross section measurement

In general:

Option `--CharmdetSetup 1` activates charm cross section geometry, while
`--CharmdetSetup 0` activates muon flux geometry.

Only the most useful options have been explained here. For the complete list of
available options please refer to the related scripts.

Charm production simulations are done from `macro/run_simScript.py`. Example
syntax:  `python $FAIRSHIP/macro/run_simScript.py --charm 1 -A charmonly
--CharmdetSetup 1 -f Cascadefile -n 1000 -o outputfolder`

Useful options:
* `--charm 1`: activates `charmdet` configuration instead of SHiP standard (both
  for charm cross section and muon flux measurements)
* `-A charmonly`: activates
  charm production simulation
* `-f`: input file with charm vertices (if you have Kerberos configured (e.g.
  by default on `lxplus`), this will be taken directly
  from `/eos/ship/data/Charm/Cascade-parp16-MSTP82-1-MSEL4-978Bpot.root` by
  default)
* `-n`: number of events
* `-o`: output of folder where geometry and output of simulation will be saved  

General POT simulations are done from
`muonShieldOptimization/run_MufluxfixedTarget.py`. Example of syntax:
 
 `python $FAIRSHIP/muonShieldOptimization/run_MufluxfixedTarget.py
 --CharmdetSetup 1 -G -e 0.001 -n 1000 -o outputfolder`
 
 It is a derivation of the fixed target simulation used in SHiP, applied to
 `charmdet` geometry.
 
 Useful options:
 
* `-e`: Energy cut for adding tracks to `Geant4` propagation (choosing a high cut
  allows to save memory for larger simulations)
* `-n`: Number of events
* `-o`: output of folder where geometry and output of simulation will be saved
* `-r`: number of run (can be used as folder naming if `-o` option is not used)
* `-f` : force overwriting of directory (DANGEROUS: if used in a wrong
    directory, it will delete it. DO NOT USE IT together with `-o` option)  


Different options for proton generation:

* `-V`: default one, proton interactions generated with `Pythia` and `EvtGen` is
  used for decays
* `-P`: both proton interactions and decays handled with `Pythia`
* `-G`: most basic simulation: one 400 GeV proton directly sent to `Geant4`

Details can be found here: <https://cds.cern.ch/record/2280572>.

All simulations use `Geant4` for propagation. IMPORTANT: Both `-V` and `-P`
generate all interactions in target. Due to small dimensions of target used in
`charmdet` measurement, many protons pass through without interacting. To
correctly simulate surviving protons and their tracks in detectors, use `-G`
option.

For any question or doubt about these simulations, contact Thomas Ruf
(<mailto:thomas.ruf@cern.ch>) or Antonio Iuliano
(<mailto:antonio.iuliano@cern.ch>)  

## Simulations for muon flux measurements

## Checking geometry output  Event display can be launched in the following way:
`python -i $FAIRSHIP/macro/eventDisplay.py -f simulationfile.root -g
geofile.root`

(actual names of `simulationfile.root` and `geofile.root` depend on the
launched simulation)

Positions and dimensions of volumes can be checked in the following way:
`python $FAIRSHIP/macro/getGeoInformation.py -g geofile.root`
 
Useful options:

* `-v`: name of the volume to expand (see list of volume daughters)
* `-l`: 'depth' level of the subnode expansion (how many daughters are showed)  
