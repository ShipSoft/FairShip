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

### Fixed

### Added

### Changed

### Removed

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
