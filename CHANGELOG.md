# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a
Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to
Calendar Versioning (year.month), with the possibility of patch releases
(year.month.patch).

Until April 2024 (inclusive) no changelog was kept. We might try to reconstruct
it in future.

## Unreleased

### Added

* feat(python): Add experimental script to compare histograms
* feat(python): Add experimental script to check overlaps quickly
* **Corrections in MuonDIS simulation**
  The DIS interactions are now time-shifted to be consistent with the original incoming muon. Additionally, tracks from soft interactions of the original muon along with the muon's veto response are preserved (in muonDis.root) and included up to the DIS interaction point. To be noted that the muon veto points are manually added using add_muonresponse.py, which modifies the simulation file. This replaces the old method of "backward-travelling muon" to generate the incoming muon's veto response. All MuonDIS simulation scripts have been updated and consolidated within FairShip/muonDIS, ensuring consistency for new productions.
* Added a custom CrossSection branch to the simulation file to save the DIS cross sections from muonDIS.
* Added new warm muon shield `warm_opt` in geometry_config
* Added new parameters to muon shield to support configurations from current optimisation campaign
* Added event_inspector class to experimental analysis_toolkit to streamline usage of helper functions; Added dump_event() as a start.
* Add (optional) MgB2 field map
* ShipBFieldMap: Added LOG info and fatal
* Folder ```SND``` is added for new versions of SND integrated to the Muon Shield
* First version of ```MTC``` (```SND/MTC```) is introduced. Scint part is fully implemented, the Sci-Fi part is implemented in simplified version. Geometrical parameters of ```MTC``` are stored in ```geometry/MTC_config.yaml``` file
* New key for ```macro/run_simScript.py``` for choosing SND options is added: ```--SND_design```
* Geometry_config.py: Added MS design `New_HA_Design` based on the MS `warm_opt`  with new version of HA
* Add access to decoded numbers (stations, views etc.) of strawtubes hits
* Add June 2025 target configuration
* Definition of Pressured Helium for the target, two version 200 Celsius degree and 90 Celsius degree.
* Add backport for new TFile/TDirectory `__get_item__` pythonisation
* SND/EmulsionTarget folder, with the Target and TargetTracker classes from nutaudet
* Added fibre structure for MTC and digitization. Fibre <-> SiPM mapping is done in ```SND/MTC/MTCDetector.cxx```, can be extracted and tested in ```python/SciFiMapping.py```, that is subsequently used in ```python/shipDigiReco.py```
* Implement proximity shielding design from 26/06/2025 by G. Humphreys
* Added the hole for SND in the Muon Shield, that is created automatically if SND key is enabled (works so far for SND_design == 2)
* Implement vacuum in target facility
* Implement target helium vessel
* feat(python): Add z-offset to FixedTargetGenerator
* Add missing --FixedTarget option to run_simScript.py
* feat: Support for multiple SND designs in simulation setup
  - The `--SND_design` option in `macro/run_simScript.py` now accepts multiple values and an 'all' option to enable all available SND designs.
  - The geometry configuration and detector setup (`geometry/geometry_config.py`, `python/shipDet_conf.py`) have been updated to instantiate all requested SND detectors.
  - This enables running with multiple SND subdetectors simultaneously and is future-proof for additional SND designs.

### Fixed

* chore: Fix file endings
* chore: trim trailing whitespace
* Fix mismatch dimension cavern ECN3 TCC8
* fix: use standard library to expand env
* fix: autoload Pythia8 instead of manually loading in run_simScript.py
* fix(geometry): fix typo of "vacuums" for strawtubes medium
* fix(reco): Fix segmentation fault due to dummy containers (#453, #519)
* fix: don't use TFile's deprecated attribute syntax
* fix(digi): Fix logic of SST digitisation (#662)
* Fix double append of recognized stracks
* fix(ShieldUtils.py): The fieldmap offset was calibrated with the old version of MS
* fix(ShieldUtils.py): changing code to be more pythonic, adding new element in the output tuple -- the list of the Muon Shield magnet z-coordinates, that can be used to set a location of SND inside the Muon Shield
* fix(shipDet_conf.py): changing paths to yaml files to more pythonic (```os.path.join()``` now)
* Fix splitcal strip dimensions and number of modules
* fix: Ensure the web viewer is disabled when checking for geometry overlaps (workaround for https://github.com/root-project/root/issues/18881)
* fix(EvtCalc): Fix crash due to string formatting
* Fix: Field direction of first magnet section 2 was wrong
* Fix: How the cavern is translated in z direction
* Fix: Preliminary fix of the length of the Target (to be refine)
* Fix: in `python/ShieldUtils.py` still used old coordinate system (SND was not correctly positioned in `python/shipDet_conf.py`)
* Fix `beam smearing`: replace incorrect Gaussian radius with proper 2D Gaussian sampling. Ensures physical consistency; radius now follows Rayleigh distribution as expected.
* Reconstruction: reverse nmeas > 0 check to make sure 𝜒² is defined
* Fix: MTC geometry overlap
* fix(FixedTargetGenerator): Don't assume anything about the target substructure

### Changed

* Don't special case EOS paths (fix #566)
* Setting up the Muon shield geometry by ROOT files is completely replaced with the temporary solution of dict in the `geometry/geometry_config.py`.
* Set up of the shield name is now done using the `--shieldName` flag instead of `--scName`.
* Allow using standalone TPythia for use with ROOT 6.32+
* Use git-lfs to track ROOT files
* shipDet_conf behaviour no longer depends on the muon shield version.
* feat(digi): Use STL vectors for SST digitisation
* feat(digi): Use STL vectors for SBT digitisation
* Change max x of stereo hits to match straw length
* Get rid of straw diameter dependency in scale factor
* Assume all tracks are muons during track fit (avoid using MC truth)
* Change of UBT geometry, remove implementation of RPC and setting a new scoring plane of 4×6 m
* Allow specifying spectrometer field map
* Obtain tauMuDet z position from muonshield position and length, instead of chamber trackers
* Update tracker station z positions, fix UBT, TimeDet & SplitCal position (s. integration layout EDMS 3287817 v1)
* feat(geometry): Make SplitCal the default calorimeter
* Resize SplitCal to 4×6 m²
* feat(geometry): Define target configuration in yaml
* strawtubes detID is now 7-digit! (without plane number)
* Change strawtubes detID decode function to tuple output
* Change separate constructions of tracker stations 1/2 and 3/4 to being identical
* `fWithConstShieldFiel` Defined as input flag for MS design in `geometry_config.py`
* MS design have B field as parameter
* Changed the parametrization of the field in `ShipMuonShield.cxx`
* Make the warm muon shield with new hadron absorber the default option
* feat(geometry): Change coordinate system to z_0 := start of target
* Insert Proximity shield in the geometry
* Removed old stuff legacy in `shipMuonShield.cxx` (like LE and fFloor)
* Event Display: Don't try to recreate geometry config
* Geometry: Make the tungsten target the default (Jun25 config)
* Change EmulsionTarget detID decode function to tuple output
* Particle Gun has been updated: now user can set the coordinates of the PG via keys --V{x,y,z} and use --D{x,y} to uniformly smear the signal in a given x and y range
+ makeCascade: Added new default target, moved to argparse
* run_simScript.py: use options directly internally instead of using intermediate variables

### Removed

* fix: Remove unused, unrunnable shipPatRec_prev.py
* feat(geometry): Dropped support for old geometries without DecayVolumeMedium explicitly set(pre 24.11 release case).
* MS: Removed old options 7, 9, 10
* MS: Removed cobalt option
* MS: Removed stepGeo option
* MS: Removed the flag constant field in Absorber (HS) -> fixed to 1.7 T
* MS: run_simScript.py: The --noSC flag is removed, whether or not a configuration is SC hybrid depends on the config selected. Configurations are defined in the shield_db in geometry_config.py
* Removed old nuTauTargetDesign configurations from 0 to 2. Currently supported: 3 (2018, magnetized target) and 4 (Current, not magnetized target and spectrometer)
* build(field,nutaudet): remove unnecessary ROOT_INCLUDE_DIR include
* feat(geometry): Remove 2018, 2022 global designs
* run_simScript.py: remove --muShieldDesign flag
* Remove unused straw veto station
* ShipAna.py: remove broken calorimetry
* Remove strawtubes_single class
* Removed outdated version `sc_v6` since it is not fitting in the Cavern (also in the build-run)
* feat(geometry): remove TP liquid scintillator variables
* Remove unused python/shipMuShield_only.py
* Remove (broken?) support for Nuage generator
* Remove nuTauTargetDesign variable, options
* Remove reloading of the `geometry_config.py` in `shipDet_conf.py`
* Remove nutaudet folder, replaced by SND folder
* Remove deprecated NuTauDet field map
* Remove tankDesign variable, options
* Remove target versions older than CDR
* Remove hadron absorber in ShipTargetStation.cxx

## 25.01

### Added

* New analysis toolkit prototype added as part of the 'experimental' package.
* Simple analysis example script now available in 'examples/'

### Fixed

* Use ConstructedAt + std::swap to replace removed pythonization for TCA
* Octant symmetry was incorrect for B_z when using field maps (reported and fixed by M. Ferro-Luzzi)
* Tof calculation corrected in GenieGenerator.cxx, wrong units previously used.
* Genfit measurements now give the correct detector ID
* Fix TEvePointSetPrintOut
* Event Display: Fix drawing of MC and Geo tracks
* AddressOf is outdated function in ROOT, changed with addressof (in field/)

### Changed
* Changed the dimension of the cave (ref. https://indico.cern.ch/event/1507466/contributions/6345273/attachments/3003438/5293503/Quick%20Update%20on%20FAIRSHIP%20geometry-1.pdf):
	1) Updated dimensions of TCC8 and ECN3.
	2) Added a step in ECN3.
	3) Removed the coat of the absorber.
	4) Modified the dimensions of the HA and absorber.

* Set Decay Volume Medium as helium (previously vacuums),can be explicitly switched to vacuum with --vacuums.
* Medium of SST boxes will be the same as DecayVolumeMedium (previously, always vacuum)
* Don't prune tracks (before we were using the CFL option to Track::prune, see https://github.com/GenFit/GenFit/blob/e81adeb07c8643301a1d9f7ae25048557cc72dff/core/include/Track.h#L298)
* **EventCalc LLP event generator**
This modification to the EventCalc interface accommodates for generic N-body LLP decays.

### Removed

* Remove Millepede
* Remove outdated example shipEvent_ex.py
* Remove ALPACA generator

## 24.11

This release follows the first round of breaking changes and is tagged for the launch of background simulations. It requires a CVMFS release of 24.10 or later.

### Added

- Introduce the EventCalc LLP event generator, a decay event sampler for inclusive final states. For further details, consult the dedicated presentation at the 30th SHiP CM [here](https://indico.cern.ch/event/1448055/contributions/6142341/attachments/2939894/5165450/SHiP_collaboration_meeting_talk_MFerrillo.pdf). See also #528.
- Add a conversion script, `FairShip/macro/convertEvtCalc.py`, to convert EventCalc's output kinematics to a format compatible with the simulation script.

### Fixed

- Add missing includes in `ecalMatch` and `ecalReco`.
- Fix compilation warnings for unused or uninitialized variables (see #481).

### Changed

- Migrate `shipStrawTracking` to use `argparse`.
- Update CMake to use an external `genfit2`.
- Ensure `shipStrawTracking`, `shipDigiReco`, and `shipVertex` are compatible with the current version of `genfit`.

### Removed

- Remove obsolete renaming scripts.
- Remove the `online` directory. For respective versions, see the `charmdet` and `muflux` branches.
- Remove the `charmdet` directory. For the latest version, see the `charmdet` branch.
- Remove the preshower and CaloDesign 1 (TP+Preshower).
- Remove the bundled `genfit`.
- Remove the conditions database.

## 24.10 - Freiburg

This release prepares for breaking changes and is the last to include charm cross-section measurement code and obsolete detector configurations.

### Added

- Add an option for a helium-filled decay volume.
- Add a pre-commit configuration to improve code quality and identify issues early.
- Add a `CHANGELOG.md` file.
- Add a `.git-blame-ignore-revs` file to ignore automatic reformatting in git blame.
- Add automatically built documentation using Doxygen.
- Add a `CODEOWNERS` file to automate review requests.
- Add separate configuration files for vacuum and helium in the decay vessel.
- Add an option to enable or disable the SND.

### Fixed

- Remove trailing whitespace and fix line endings.
- Fix compilation warnings from deprecations (see #469).
- Fix an issue with SST parameters (see #489).
- Clean up the Veto implementation.
- Fix a crash in the event display and PID when the entrance lid is missing.
- Ensure the `ShipReco.py` output file is closed correctly.
- Remove an unused argument for `MuDISGenerator::SetPositions`.

### Changed

- Update the `getGeoInformation` command-line interface.
- Update SST geometry constants (see #483).
- Use the same `clang-format` and `clang-tidy` configurations as FairRoot.
- Import the decay vessel configuration from a YAML file.
- Update the decay vessel geometry to the new design.
- Increase the minimum required CMake version to 3.12.
- Use FairRoot's `find_package2` to find ROOT, VMC, and fmt.
- Increase the minimum required ROOT version to 6.26.
- Use `find_package` to find Boost.
- Set the FairLogger dependency instead of using manual includes.

### Removed

- Remove obsolete installation and testing files.
- Remove uses of `future` and `past` modules (see #473).
- Remove the Geant3 dependency.
- Remove unimplemented event display functions (see #497).
- Disable the SND by default.
- Remove CMake commands no longer provided by FairRoot 19.
- Remove old CMake files for ROOT 5.
- Remove an old, outdated tracking script.
