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

* Add option for helium-filled decay volume
* Add pre-commit config: This will be phased in to improve code quality and spot issues as early as possible. Status visible in README and CI enabled for new pull requests.
* Add CHANGELOG.md
* Add `.git-blame-ignore-revs` to allow automatic reformatting etc. without polluting git blame
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

### Changed

* Update getGeoInformation command line interface
* Update SST geometry constants #483
* Housekeeping: Use same clang-format and clang-tidy config as FairRoot
* Decay Vessel configuration now imported from a yaml file
* Geometry of Decay Vessel updated to new design

### Removed

* Remove obsolete files related to old ways of installing or testing FairShip
* Remove uses of future and past modules #473
* Remove Geant3 dependency
* Remove unimplemented event display functions (see #497)
* Disable SND by default
