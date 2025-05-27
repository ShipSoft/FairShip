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
* feat(geometry): Change coordinate system to z_0 := start of target

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
* feat(geometry): remove TP liquid scintillator variables

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

Release after first round of breaking changes. Requires CVMFS release ≥ 24.10.
Tagged for launch of background simulations.

### Added

* **EventCalc LLP event generator**
  This modification introduces a first implementation of the EventCalc decay
  event sampler in FairShip for inclusive final states. For further details,
  consult the dedicated presentation at the 30th SHiP CM
  [here](https://indico.cern.ch/event/1448055/contributions/6142341/attachments/2939894/5165450/SHiP_collaboration_meeting_talk_MFerrillo.pdf). See also #528.
* Add a conversion script `FairShip/macro/convertEvtCalc.py` to convert the
  EventCalc output sampled kinematics (.dat) as input to the simulation script
  (.root). _Remark_: This will eventually become unnecessary when this
  conversion is implemented within the EventCalc tool itself.

### Fixed

* Fix missing includes in ecalMatch and ecalReco
* Fix compilation warnings due to unused or uninitiliazed variables #481

### Changed

* shipStrawTracking: Move to argparse
* CMake: Use external genfit2
* shipStrawTracking, shipDigiReco, shipVertex: Make compatible with current genfit

### Removed

* Remove obsolete renaming scripts
* Remove online, please see charmdet and muflux branches for respective versions
* Remove charmdet, please see charmdet branch for latest version
* Remove preshower and CaloDesign 1 (TP+Preshower)
* Remove bundled genfit
* Remove conditions DB, will almost certainly look different, copy in git
  history for reference

## 24.10 - Freiburg

Tag release to prepare for breaking changes. Last release to include charm
cross-section measurement code, and obsolete detector configurations.

### Added

* Add option for helium-filled decay volume
* Add pre-commit config: This will be phased in to improve code quality and
  spot issues as early as possible. Status visible in README and CI enabled for
  new pull requests.
* Add CHANGELOG.md
* Add `.git-blame-ignore-revs` to allow automatic reformatting etc. without
  polluting git blame
* Automatically built documentation using Doxygen
* Add CODEOWNERS file to automatically trigger reviews by the relevant experts
* Add different configuration files for vacuum /helium for the Decay Vessel
* Add option to enable/disable SND

### Fixed

* Remove trailing whitespace and fix line endings
* Fix compilation warnings due to deprecations #469
* Fix issue with SST parameters #489
* Cleaned up Veto Implementation
* Fix crash of event display, PID when no entrance lid present
* Close ShipReco.py output file
* Remove unused (silently ignored!) argument for MuDISGenerator::SetPositions

### Changed

* Update getGeoInformation command line interface
* Update SST geometry constants #483
* Housekeeping: Use same clang-format and clang-tidy config as FairRoot
* Decay Vessel configuration now imported from a yaml file
* Geometry of Decay Vessel updated to new design
* Housekeeping: Bump minimum CMake version to 3.12
* Housekeeping: Use FairRoot's `find_package2` to find ROOT, VMC, fmt
* Housekeeping: Bump minimum ROOT version to 6.26
* Housekeeping: Use find_package to find BOOST
* Housekeeping: Set FairLogger dep instead of manual includes

### Removed

* Remove obsolete files related to old ways of installing or testing FairShip
* Remove uses of future and past modules #473
* Remove Geant3 dependency
* Remove unimplemented event display functions (see #497)
* Disable SND by default
* Housekeeping: Don't use CMake commands no longer provided by FairRoot 19
* Housekeeping: Remove old CMake for ROOT 5
* Remove old, outdated tracking script
