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

* Add EventId and TrackID for MCTrack and HAPoint #944
* **Data classes now support ROOT RNtuple I/O**
  All FairShip data classes (Hits, Points, Tracks, Particles) have been refactored for ROOT RNtuple compatibility. Changes include: public copy constructors, const-correct getter methods, replacement of TVector3 storage with std::array, and complete refactoring of ShipParticle to remove TParticle inheritance. Comprehensive RNtuple I/O tests verify all 20 data classes can be written to and read from RNtuple format.
+ Add option for an additional sensitive plane around the target in run_fixedTarget
* Add CI job to run fixed target simulation (run_fixedTarget.py)
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
* Add support for Pythia 8.3xx. 8.2xx is still supported via preprocessor macros for the time being.
* Add dedicated --print-fields and --check-overlaps flags to run_simScript.py to use these debug tools.
* Add EvtGenDecayer for decaying J/psi (and other particles in future) when specifying the --EvtGenDecayer option
* Add enough straws to cover aperture entirely
* Add SST frame option (4 = aluminium, 10 = steel [default])
* Fix EvtGen library linking order for old autotools-based EvtGen installations
* feat: Unified beam smearing implementation across all generators
  - Updated `HNLPythia8Generator` to use consistent Gaussian beam smearing and circular beam painting, replacing the previous uniform square implementation
  - Added beam smearing and painting support to `FixedTargetGenerator`
  - All generators (`MuonBackGenerator`, `HNLPythia8Generator`, `FixedTargetGenerator`) now use the same beam smearing algorithm: Gaussian smearing with `--SmearBeam` parameter and uniform circular painting with `--PaintRadius` parameter
  - The `--SmearBeam` and `--PaintBeam` command-line options in `run_simScript.py` now apply to all generators, not just muon background simulation
  - Fixed unit handling to ensure proper conversion between GEANT4 units (cm-based) and Pythia8 units (mm-based) in each generator
  - Implemented shared `BeamSmearingUtils` utility using modern C++17 features (std::pair return and structured bindings) to eliminate code duplication
* Big update of genie generation scripts `macro/makeGenieEvents.py` and `python/genie_interface.py`:
  - Universal choice of neutrino flavor to simulate
  - Handy way to enable/disable charm and tau decays of the products
  - Rewriting the code with modern pythonic style preserving backward compatibility
* Adding new keys specifically for genie regime in `macro/run_simScript.py` and copying `gst` TTree from the genie input file to the output file of the `macro/run_simScript.py`:
  - Adjust the z range where to simulate the neutrino interactions via `--z_start_nu and `--z_end_nu` keys
  - Replacing the `--Genie` key with `Genie` as a subparser
  - Copying `gst` TTree is similar to `sndsw`
- Enclose target in steel (316L) cylinder
* First version of SND/SiliconTarget, this layout for this iteration consists of 120 3.5mm W planes with pairs of silicon planes placed 1mm from the surface of the tungsten. As a temporary solution, the detector is placed within the second last magnet of the muon shield. Configuration of detector in simScript is coupled to the SND_design == 2 along with the MTC.
* Add visualization methods to SciFiMapping.py to visualize Sci-Fi in MTC, including draw_channel(), draw_channel_XY(), and draw_combined_scifi_views()
* Support using TPythia6 provided by ROOTEGPythia6 for ROOT ≥ 6.32

* Added initial implementation for ACTS based track reconstruction. This iteration includes independent tracking geometries for SiliconTarget, MTC, and Strawtubes.

### Fixed

* refactor(splitcal): Replace splitcalPoint* constructor with vector-based constructor
* fix(splitcal): Move energy weights from Hit to Cluster, eliminating internal vectors
+ Fix FixedTargetGenerator to ensure it works with newer versions of Pythia
* fix(eventDisplay): Fix event display crash caused by premature ROOT object initialization
* Remove SIMPATH dependency, replaced with EVTGENDATA for EvtGen data files (#648)
* fix(digi): Make TTree branch split level configurable in BaseDetector, set splitLevel=1 for MTC
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
* Fix crash in run_simScript.py
* Fix crash caused by decorators.py
* Use lowercase FairLogger severities (uppercase ones are deprecated)
* Correct paths for default input files
* Fix missing decays of J/psi by using EvtGenDecayer
* Fix: hard cast bug in genie generator: after replacing old C-style cast histogram variable got nullptr value which afterwards caused segmentation fault
* Correct extraction of SiPM channel positions in MTC
* Fix refactoring issue that broke MTC digitization
* Fix the condition in the sipm channel <-> fiber mapping that stopped looping over channels because of the distance between a fiber and a channel. Setting a flexible condition that depends on the aggregated channel size.
* Add flags for `python/ScifiMapping.py`
* Fixed SiliconTarget detector identifier.
* fix(muon): Make muonHit copy constructor public for std::vector compatibility

### Changed

* Replace ConfigRegistry with function-based geometry configuration API. Use `geometry_config.create_config(**params)` instead of `ConfigRegistry.loadpy()`
* Move `geometry_config.py` from `geometry/` to `python/` directory and update all imports from `from geometry import geometry_config` to `import geometry_config`
* Refactor strawtubes digitisation to use dedicated detector class
  - Created `strawtubesDetector` class inheriting from `BaseDetector`
  - Moved digitisation logic from `ShipDigiReco` to `detectors/strawtubesDetector.py`
  - Updated naming from "Strawtubes" to "strawtubes" for consistency
  - Changed branch name from "Digi_StrawtubesHits" to "Digi_strawtubesHits"
* Rename MtcDetPoint and MtcDetHit classes to MTCDetPoint and MTCDetHit for consistency with detector naming conventions
* Complete refactoring of all digitisation to use BaseDetector pattern (MTC, muon, time, SBT, UpstreamTagger, strawtubes, splitcal)
* Make BaseDetector an abstract base class to enforce interface contract
* Remove TClonesArray support from digitisation framework. BaseDetector now exclusively uses std::vector, removing branchType parameter
* Rewrite UpstreamTaggerHit for simplified scoring plane detector, remove RPC-specific code (#701, #354, #355)
* Complete migration from TClonesArrays to STL vectors for all detectors (timeDetector, muonDetector, vetoHitOnTrack, strawtubes, splitcal)
* Integrate splitcal cluster reconstruction into splitcalDetector class
* refactor(splitcal): Use value storage for both hits and clusters instead of pointer storage
* refactor(splitcal): Replace TVector3 with std::array and hit pointers with indices in splitcalCluster for RNtuple compatibility
* refactor(digi): Use maximum splitting (99) for vector branches instead of no splitting (-1)
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
* Update spectrometer yoke pit size according to EDMS no. 3309666
* feat: Improve FixedTargetGenerator geometry handling
  - Replace fragile hardcoded TGeo navigation paths with geometry constants from `ship_geo.target`
  - Add `SetTargetCoordinates()` method to accept geometry-based start/end z-coordinates from `run_simScript.py`
  - Use robust `ship_geo.target.z0` and `ship_geo.target.length` instead of brittle `"cave_1/target_vacuum_box_1/TargetArea_1/HeVolume_1"` path
  - Maintain backward compatibility with legacy TGeo navigation as fallback
* feat: Improve Pythia8Generator geometry handling
  - Apply same geometry robustness improvements as FixedTargetGenerator
  - Replace fragile `"volTarget_1"` TGeo navigation with geometry constants from `ship_geo.target`
  - Add `SetTargetCoordinates()` method for robust geometry-based target configuration
  - Maintain backward compatibility with legacy TGeo navigation as fallback
- The decorators from decorators.py now need to be applied explicitly using the new `apply_decorators` function.
- The --debug flag to run_simScript.py now controls the severity that FairLogger logs.
- J/psi are no longer decayed using Geant4 when using the --EvtGenDecayer option
* Move SST geometry parameters to yaml
* Update strawtubes class
* Change SST gas mixture to Ar/CO2 80%/20% at 1 bar
* FairShip is now licensed under LGPLv3+
* UBT box dimensions (BoxX, BoxY, BoxZ) are now configurable via geometry_config.py instead of hardcoded
* Configuration storage modernized from pickle to JSON
  - Geometry configurations are now saved as JSON strings (using `std::string`) instead of pickled Python objects in ROOT files
  - Automatic format detection: new code reads both JSON (new format) and pickle (legacy format) files without user intervention
* Change the logic of SiPM channel encoding in MTC. Now the number of SiPM is 1 and has a number of channels that fits the width of the plane. If the number of channels exceeds 1000, iterating a SiPM digit to 1 and distributing channels among new number of SiPMs.
* Set default parameters of MTC to 60x60 cm^2 and 4 aggregated channels according to Sep 2025 CM.
* Placement of SiliconTarget has been shifted by 10 cm to bring the final layer to within 10 cm of the MTC.
* Modernise data classes by removing obsolete BOOST serialisation (Tracklet, vetoHitOnTrack, ShipHit, TrackInfo)
  - Replace BOOST serialisation with native ROOT 6 serialisation
  - Modernise Tracklet constructor to accept `std::vector<unsigned int>` indices
  - Update vetoHitOnTrack to use parameterised constructor in Python code
  - Add const correctness to TrackInfo accessor methods
  - Update Python code in shipDigiReco.py to use modern constructors
  - Bump ClassDef versions to 2 for schema evolution
  - Add TrackInfo to RNTuple I/O test suite

### Removed

* Remove BOOST dependency from CMake build system - no longer required as ROOT 6 provides native serialisation
* Remove Goliath magnet geometry and field implementation (ShipGoliath, ShipGoliathField, and associated field maps)
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
* Removed 38 unused RPC geometry parameters from UpstreamTagger configuration (legacy from pre-simplification)
* Remove deprecated NuTauDet field map
* Remove tankDesign variable, options
* Remove target versions older than CDR
* Remove hadron absorber in ShipTargetStation.cxx
* Remove old ecal and hcal in all of FairShip, affected files are notably the entire ecal and hcal directories as well as macro/run_anaEcal.py and python/shipPid.py. geometry/geometry_config.py, muonShieldOptimization/ana_ShipMuon.py, macro/ShipReco.py, macro/ShipAna.py, python/shipStrawTracking.py and python/shipPid.py.
* Remove unused files for FLUKA
* Remove unused CMake modules
* Remove globalDesigns dictionary from run_simScript.py and create_field_perturbation.py, use inline defaults instead
* Remove unused CaloDesign parameter from geometry configuration (only splitCal supported after ECAL/HCAL removal)
* Removed unused class ShipChamber (leftover from TP design)
* Removed unused run_simPgun.py
* Remove ecal and hcal geometry files
* Remove simpleTarget and personal study study_muEloss.py
* Remove TTCluster.py
* Remove pid class
* Remove muon system

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
