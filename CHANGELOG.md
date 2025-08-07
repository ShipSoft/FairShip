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

- Add an experimental script to compare histograms.
- Add an experimental script to quickly check for overlaps.
- Time-shift MuonDIS interactions to be consistent with the original incoming muon. Tracks from soft interactions and the muon's veto response are now preserved.
- Add a custom `CrossSection` branch to the simulation file to save DIS cross sections from MuonDIS.
- Add the new `warm_opt` warm muon shield in `geometry_config`.
- Add new parameters to the muon shield to support configurations from the current optimization campaign.
- Add an `event_inspector` class to the experimental `analysis_toolkit` to streamline the use of helper functions.
- Add an optional MgB2 field map.
- Add `LOG` `info` and `fatal` to `ShipBFieldMap`.
- Add the `SND` folder for new versions of SND integrated with the Muon Shield.
- Introduce the first version of the `MTC` (`SND/MTC`), with a fully implemented scintillator part and a simplified Sci-Fi part. Geometrical parameters are stored in `geometry/MTC_config.yaml`.
- Add the `--SND_design` key to `macro/run_simScript.py` to select SND options.
- Add the `New_HA_Design` MS design in `geometry_config.py`, based on the `warm_opt` MS with a new version of HA.
- Add access to decoded numbers (stations, views, etc.) of straw tube hits.
- Add the June 2025 target configuration.
- Define pressured helium for the target at 200 and 90 degrees Celsius.
- Add a backport for the new `TFile`/`TDirectory` `__getitem__` pythonization.
- Add the `SND/EmulsionTarget` folder with `Target` and `TargetTracker` classes from `nutaudet`.
- Add a fibre structure for the MTC and digitization. The fibre-SiPM mapping is defined in `SND/MTC/MTCDetector.cxx` and can be tested in `python/SciFiMapping.py`.
- Implement the proximity shielding design from 26/06/2025 by G. Humphreys.
- Add a hole for the SND in the Muon Shield, created automatically when the SND key is enabled.
- Implement a vacuum in the target facility.
- Implement a target helium vessel.
- Add a z-offset to `FixedTargetGenerator`.
- Add missing --FixedTarget option to run_simScript.py.
- feat: Support for multiple SND designs in simulation setup
  - The `--SND_design` option in `macro/run_simScript.py` now accepts multiple values and an 'all' option to enable all available SND designs.
  - The geometry configuration and detector setup (`geometry/geometry_config.py`, `python/shipDet_conf.py`) have been updated to instantiate all requested SND detectors.
  - This enables running with multiple SND subdetectors simultaneously and is future-proof for additional SND designs.

### Fixed

- Fix file endings.
- Trim trailing whitespace.
- Fix a dimension mismatch in the ECN3 TCC8 cavern.
- Use the standard library to expand environment variables.
- Autoload Pythia8 instead of manually loading it in `run_simScript.py`.
- Fix a typo of "vacuums" for the straw tubes medium.
- Fix a segmentation fault due to dummy containers (see #453, #519).
- Do not use `TFile`'s deprecated attribute syntax.
- Fix the logic of SST digitization (see #662).
- Fix double appending of recognized stracks.
- The field map offset was calibrated with the old version of the MS.
- Make the code in `ShieldUtils.py` more Pythonic and add the list of Muon Shield magnet z-coordinates to the output tuple.
- Change paths to YAML files in `shipDet_conf.py` to be more Pythonic.
- Fix SplitCal strip dimensions and the number of modules.
- Ensure the web viewer is disabled when checking for geometry overlaps (workaround for [root-project/root#18881](httpshttps://github.com/root-project/root/issues/18881)).
- Fix a crash due to string formatting in `EvtCalc`.
- Fix the field direction of the first magnet in Section 2.
- Fix how the cavern is translated in the z-direction.
- Preliminarily fix the length of the target.
- The coordinate system in `python/ShieldUtils.py` was outdated, causing incorrect SND positioning.
- Fix beam smearing by replacing the incorrect Gaussian radius with proper 2D Gaussian sampling.
- Reverse the `nmeas > 0` check in reconstruction to ensure that chi-squared is defined.
- Fix an MTC geometry overlap.
- Do not assume anything about the target substructure in `FixedTargetGenerator`.

### Changed

- Do not special-case EOS paths (see #566).
- Replace the setup of the Muon Shield geometry from ROOT files with a temporary dictionary in `geometry/geometry_config.py`.
- Use the `--shieldName` flag instead of `--scName` to set the shield name.
- Allow using a standalone TPythia for use with ROOT 6.32+.
- Use git-lfs to track ROOT files.
- The behavior of `shipDet_conf` no longer depends on the muon shield version.
- Use STL vectors for SST digitization.
- Use STL vectors for SBT digitization.
- Change the maximum x of stereo hits to match the straw length.
- Remove the straw diameter dependency in the scale factor.
- Assume all tracks are muons during the track fit.
- Change the UBT geometry by removing the RPC implementation and setting a new scoring plane of 4x6 m.
- Allow specifying the spectrometer field map.
- Obtain the `tauMuDet` z-position from the muon shield position and length.
- Update tracker station z-positions and fix the UBT, TimeDet, and SplitCal positions.
- Make SplitCal the default calorimeter.
- Resize SplitCal to 4x6 m².
- Define the target configuration in a YAML file.
- The `strawtubes` `detID` is now 7 digits.
- Change the `strawtubes` `detID` decode function to return a tuple.
- Constructions of tracker stations 1/2 and 3/4 are now identical.
- `fWithConstShieldFiel` is now an input flag for the MS design in `geometry_config.py`.
- The MS design now has the B-field as a parameter.
- Change the field parametrization in `ShipMuonShield.cxx`.
- Make the warm muon shield with the new hadron absorber the default option.
- Change the coordinate system to have z=0 at the start of the target.
- Insert a proximity shield into the geometry.
- Remove legacy code from `shipMuonShield.cxx`.
- Do not try to recreate the geometry config in the event display.
- Make the tungsten target the default (Jun25 config).
- Change the `EmulsionTarget` `detID` decode function to return a tuple.
- The particle gun can now be configured with `--V{x,y,z}` and `--D{x,y}`.
- `makeCascade` now has a new default target and uses `argparse`.
- `run_simScript.py` now uses options directly instead of intermediate variables.

### Removed

- Remove the unused and unrunnable `shipPatRec_prev.py`.
- Drop support for old geometries without `DecayVolumeMedium` explicitly set.
- Remove old MS options 7, 9, and 10.
- Remove the cobalt MS option.
- Remove the `stepGeo` MS option.
- Remove the constant field flag in the Absorber (HS), now fixed to 1.7 T.
- The `--noSC` flag in `run_simScript.py` is removed.
- Remove old `nuTauTargetDesign` configurations 0-2.
- Remove an unnecessary `ROOT_INCLUDE_DIR` include.
- Remove the 2018 and 2022 global designs.
- Remove the `--muShieldDesign` flag from `run_simScript.py`.
- Remove the unused straw veto station.
- Remove broken calorimetry from `ShipAna.py`.
- Remove the `strawtubes_single` class.
- Remove the outdated `sc_v6` version.
- Remove TP liquid scintillator variables.
- Remove the unused `python/shipMuShield_only.py`.
- Remove support for the Nuage generator.
- Remove the `nuTauTargetDesign` variable and options.
- Remove reloading of `geometry_config.py` in `shipDet_conf.py`.
- Remove the `nutaudet` folder, which has been replaced by the `SND` folder.
- Remove the deprecated NuTauDet field map.
- Remove the `tankDesign` variable and options.
- Remove target versions older than the CDR.
- Remove the hadron absorber in `ShipTargetStation.cxx`.

## 25.01

### Added

- Add prototype of a new analysis toolkit in the `experimental` package.
- Add a simple analysis example script in the `examples/` directory.

### Fixed

- Use `ConstructedAt` and `std::swap` to replace removed pythonization for `TClonesArray`.
- Correct B_z octant symmetry for field maps.
- Correct time-of-flight calculation in `GenieGenerator.cxx` by using correct units.
- Ensure Genfit measurements provide the correct detector ID.
- Fix `TEvePointSetPrintOut`.
- Fix drawing of Monte Carlo and geometry tracks in the event display.
- Replace outdated `AddressOf` ROOT function with `addressof` in the `field/` directory.

### Changed

- Update cavern dimensions, including TCC8 and ECN3, and add a step in ECN3. The absorber coat has been removed, and the dimensions of the HA and absorber have been modified. For further details, see the presentation [here](https://indico.cern.ch/event/1507466/contributions/6345273/attachments/3003438/5293503/Quick%20Update%20on%20FAIRSHIP%20geometry-1.pdf).
- Set the decay volume medium to helium by default, with an option to switch to vacuum using the `--vacuums` flag.
- The medium of the SST boxes now matches the decay volume medium.
- Disable track pruning (see #533).
- Accommodate generic N-body LLP decays in the EventCalc interface.

### Removed

- Remove Millepede.
- Remove the outdated `shipEvent_ex.py` example.
- Remove the ALPACA generator.

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
