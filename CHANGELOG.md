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

### Changed


* Change naming convention for simulation files to `{sim,geo,params}_{uuid4}.root`, with optional `--tag` parameter to specify custom identifier

### Fixed

* Fix file-filtering logic to support STL branches
* Update MuonBackGenerator to support both TClonesArray and std::vector input formats for MCTrack and vetoPoint branches
* Fix function call in run_simScript.py to use SetPhiRandomize instead of deprecated SetPhiRandom
+ Update run_fixedTarget to save tracks for hits in post-target sensitive plane
* Set correct trackIDs for exitHadronAbsorber class

### Removed

## 25.12 - 2025-12-22

### Added

#### Physics and Simulation

* Add EvtGenDecayer for decaying J/psi (and other particles in future) when specifying the --EvtGenDecayer option
* **Corrections in MuonDIS simulation**
  The DIS interactions are now time-shifted to be consistent with the original incoming muon. Additionally, tracks from soft interactions of the original muon along with the muon's veto response are preserved (in muonDis.root) and included up to the DIS interaction point. To be noted that the muon veto points are manually added using add_muonresponse.py, which modifies the simulation file. This replaces the old method of "backward-travelling muon" to generate the incoming muon's veto response. All MuonDIS simulation scripts have been updated and consolidated within FairShip/muonDIS, ensuring consistency for new productions.
* Added a custom CrossSection branch to the simulation file to save the DIS cross sections from muonDIS.
* **Unified beam smearing implementation across all generators**
  - Updated `HNLPythia8Generator` to use consistent Gaussian beam smearing and circular beam painting, replacing the previous uniform square implementation
  - Added beam smearing and painting support to `FixedTargetGenerator`
  - All generators (`MuonBackGenerator`, `HNLPythia8Generator`, `FixedTargetGenerator`) now use the same beam smearing algorithm: Gaussian smearing with `--SmearBeam` parameter and uniform circular painting with `--PaintRadius` parameter
  - The `--SmearBeam` and `--PaintBeam` command-line options in `run_simScript.py` now apply to all generators, not just muon background simulation
  - Implemented shared `BeamSmearingUtils` utility using modern C++17 features (std::pair return and structured bindings) to eliminate code duplication
* Big update of genie generation scripts `macro/makeGenieEvents.py` and `python/genie_interface.py`:
  - Universal choice of neutrino flavor to simulate
  - Handy way to enable/disable charm and tau decays of the products
  - Rewriting the code with modern pythonic style preserving backward compatibility
* Adding new keys specifically for genie regime in `macro/run_simScript.py` and copying `gst` TTree from the genie input file to the output file of the `macro/run_simScript.py`:
  - Adjust the z range where to simulate the neutrino interactions via `--z_start_nu` and `--z_end_nu` keys
  - Replacing the `--Genie` key with `Genie` as a subparser
  - Copying `gst` TTree is similar to `sndsw`
* Add support for Pythia 8.3xx. 8.2xx is still supported via preprocessor macros for the time being.
* Support using TPythia6 provided by ROOTEGPythia6 for ROOT ≥ 6.32

#### SND Detector System

* Folder ```SND``` is added for new versions of SND integrated to the Muon Shield
* First version of ```MTC``` (```SND/MTC```) is introduced. Scint part is fully implemented, the Sci-Fi part is implemented in simplified version. Geometrical parameters of ```MTC``` are stored in ```geometry/MTC_config.yaml``` file
* Added fibre structure for MTC and digitization. Fibre <-> SiPM mapping is done in ```SND/MTC/MTCDetector.cxx```, can be extracted and tested in ```python/SciFiMapping.py```, that is subsequently used in ```python/shipDigiReco.py```
* Add visualization methods to SciFiMapping.py to visualize Sci-Fi in MTC, including draw_channel(), draw_channel_XY(), and draw_combined_scifi_views()
* First version of SND/SiliconTarget, this layout for this iteration consists of 120 3.5mm W planes with pairs of silicon planes placed 1mm from the surface of the tungsten. As a temporary solution, the detector is placed within the second last magnet of the muon shield. Configuration of detector in simScript is coupled to the SND_design == 2 along with the MTC.
* SND/EmulsionTarget folder, with the Target and TargetTracker classes from nutaudet
* New key for ```macro/run_simScript.py``` for choosing SND options is added: ```--SND_design```
* Support for multiple SND designs in simulation setup
  - The `--SND_design` option in `macro/run_simScript.py` now accepts multiple values and an 'all' option to enable all available SND designs.
  - The geometry configuration and detector setup (`geometry/geometry_config.py`, `python/shipDet_conf.py`) have been updated to instantiate all requested SND detectors.
  - This enables running with multiple SND subdetectors simultaneously and is future-proof for additional SND designs.
* Added the hole for SND in the Muon Shield, that is created automatically if SND key is enabled (works so far for SND_design == 2)

#### Geometry and Target Station

* Add June 2025 target configuration
* Geometry: Make the tungsten target the default (Jun25 config)
* Definition of Pressured Helium for the target, two version 200 Celsius degree and 90 Celsius degree.
* Implement vacuum in target facility
* Implement target helium vessel
* Enclose target in steel (316L) cylinder
* Add option for an additional sensitive plane around the target in run_fixedTarget
* Implement proximity shielding design from 26/06/2025 by G. Humphreys
* Added new warm muon shield `warm_opt` in geometry_config
* Added new parameters to muon shield to support configurations from current optimisation campaign
* Geometry_config.py: Added MS design `New_HA_Design` based on the MS `warm_opt` with new version of HA
* Add (optional) MgB2 field map

#### Data Classes and I/O

* **Data classes now support ROOT RNtuple I/O**
  All FairShip data classes (Hits, Points, Tracks, Particles) have been refactored for ROOT RNtuple compatibility. Changes include: public copy constructors, const-correct getter methods, replacement of TVector3 storage with std::array, and complete refactoring of ShipParticle to remove TParticle inheritance. Comprehensive RNtuple I/O tests verify all 20 data classes can be written to and read from RNtuple format.
* Add RNtuple conversion and inspection utilities (`macro/convertTreeToRNTuple.py`, `macro/inspect_tree_branches.py`) for testing and validation. Note that FairRoot I/O currently uses TClonesArray which is not supported by RNtuple.
* Add EventId and TrackID for MCTrack and HAPoint #944
* **Add ISTLPointContainer interface for STL-based detector track index updating**
  Introduces ISTLPointContainer interface enabling polymorphic track index updating for detectors using std::vector storage. ShipStack now automatically detects and handles both STL-based and TClonesArray-based detectors, ensuring MC points maintain correct track references after track filtering. Also adds missing parameterised constructors to simpleTarget and exitHadronAbsorber.

#### Tools and Utilities

* Add dedicated --print-fields and --check-overlaps flags to run_simScript.py to use these debug tools.
* Add experimental script to compare histograms
* Add experimental script to check overlaps quickly
* Add CI job to run fixed target simulation (run_fixedTarget.py)
* Added event_inspector class to experimental analysis_toolkit to streamline usage of helper functions; Added dump_event() as a start.
* ShipBFieldMap: Added LOG info and fatal
* Add backport for new TFile/TDirectory `__get_item__` pythonisation

#### Detector Improvements

* Add access to decoded numbers (stations, views etc.) of strawtubes hits
* Add enough straws to cover aperture entirely
* Add SST frame option (4 = aluminium, 10 = steel [default])
* Add z-offset to FixedTargetGenerator
* Add missing --FixedTarget option to run_simScript.py

#### Reconstruction

* Added initial implementation for ACTS based track reconstruction. This iteration includes independent tracking geometries for SiliconTarget, MTC, and Strawtubes.

### Changed

#### Data Structure Modernization

* **Migrate detector MC point storage from TClonesArray to std::vector**
  Ten detector classes now use `std::vector<PointType>` instead of `TClonesArray` for storing MC simulation points. This modernises the codebase with standard C++ containers, improves type safety, and leverages `FairRootManager::RegisterAny()` for ROOT I/O. Affected detectors: TimeDet, UpstreamTagger, strawtubes, splitcal, veto, Target, TargetTracker, SiliconTarget, MTCDetector, and simpleTarget.
* **Migrate ShipStack MC track storage from TClonesArray to std::vector**
  ShipStack now uses `std::vector<ShipMCTrack>` instead of `TClonesArray` for storing MC tracks written to output. This completes the migration of MC data storage to modern C++ containers and enables `RegisterAny()` for MCTrack I/O. Includes bounds checking in ShipAna.py for all MCTrack vector accesses to handle the stricter indexing behaviour of std::vector compared to TClonesArray.
* Migrate Tracklet container in shipDigiReco from TClonesArray to std::vector
* Complete migration from TClonesArrays to STL vectors for all detectors (timeDetector, muonDetector, vetoHitOnTrack, strawtubes, splitcal)
* Modernise data classes by removing obsolete BOOST serialisation (Tracklet, vetoHitOnTrack, ShipHit, TrackInfo)
  - Replace BOOST serialisation with native ROOT 6 serialisation
  - Modernise Tracklet constructor to accept `std::vector<unsigned int>` indices
  - Update vetoHitOnTrack to use parameterised constructor in Python code
  - Add const correctness to TrackInfo accessor methods
  - Update Python code in shipDigiReco.py to use modern constructors
  - Bump ClassDef versions to 2 for schema evolution
  - Add TrackInfo to RNTuple I/O test suite

#### Physics and Simulation

* Change GEANT4 Physics list from QGSP_BERT_HP_PEN to FTFP_BERT_HP_EMZ following GEANT4 team recommendation and studies by Hanae Tilquin presented at Nov. 2025 collaboration meeting and following software meetings.
* J/psi are no longer decayed using Geant4 when using the --EvtGenDecayer option

#### Target Station Geometry

* **Target station geometry updated with nested volume approach**
  Implemented tantalum cladding (1.5mm) around tungsten target layers using nested volumes instead of separate shell and disc volumes. This reduces geometry complexity from 4N to 2N volumes per N layers, eliminates overlaps between layers, and improves GEANT4 navigation efficiency. Updated vessel dimensions (inner diameter semantics, 62mm lid distance) and steel enclosure thickness (66.9mm) to match BDF Fluka model. Tantalum density updated to 16.7 g/cm³.

#### Digitisation Framework

* Refactor strawtubes digitisation to use dedicated detector class
  - Created `strawtubesDetector` class inheriting from `BaseDetector`
  - Moved digitisation logic from `ShipDigiReco` to `detectors/strawtubesDetector.py`
  - Updated naming from "Strawtubes" to "strawtubes" for consistency
  - Changed branch name from "Digi_StrawtubesHits" to "Digi_strawtubesHits"
* Complete refactoring of all digitisation to use BaseDetector pattern (MTC, muon, time, SBT, UpstreamTagger, strawtubes, splitcal)
* Make BaseDetector an abstract base class to enforce interface contract
* Remove TClonesArray support from digitisation framework. BaseDetector now exclusively uses std::vector, removing branchType parameter
* Integrate splitcal cluster reconstruction into splitcalDetector class
* Use STL vectors for SST digitisation
* Use STL vectors for SBT digitisation
* Use maximum splitting (99) for vector branches instead of no splitting (-1)
* Make TTree branch split level configurable in BaseDetector, set splitLevel=1 for MTC

#### Geometry Configuration System

* Replace ConfigRegistry with function-based geometry configuration API. Use `geometry_config.create_config(**params)` instead of `ConfigRegistry.loadpy()`
* Move `geometry_config.py` from `geometry/` to `python/` directory and update all imports from `from geometry import geometry_config` to `import geometry_config`
* Configuration storage modernized from pickle to JSON
  - Geometry configurations are now saved as JSON strings (using `std::string`) instead of pickled Python objects in ROOT files
  - Automatic format detection: new code reads both JSON (new format) and pickle (legacy format) files without user intervention
* Define target configuration in yaml
* Move SST geometry parameters to yaml
* Change coordinate system to z_0 := start of target
* Event Display: Don't try to recreate geometry config

#### Muon Shield and Field Maps

* Setting up the Muon shield geometry by ROOT files is completely replaced with the temporary solution of dict in the `geometry/geometry_config.py`.
* Set up of the shield name is now done using the `--shieldName` flag instead of `--scName`.
* shipDet_conf behaviour no longer depends on the muon shield version.
* `fWithConstShieldField` Defined as input flag for MS design in `geometry_config.py`
* MS design have B field as parameter
* Changed the parametrization of the field in `ShipMuonShield.cxx`
* Make the warm muon shield with new hadron absorber the default option
* Insert Proximity shield in the geometry
* Removed old stuff legacy in `shipMuonShield.cxx` (like LE and fFloor)
* Allow specifying spectrometer field map

#### Detector Geometry Updates

* Rewrite UpstreamTaggerHit for simplified scoring plane detector, remove RPC-specific code (#701, #354, #355)
* Change of UBT geometry, remove implementation of RPC and setting a new scoring plane of 4×6 m
* UBT box dimensions (BoxX, BoxY, BoxZ) are now configurable via geometry_config.py instead of hardcoded
* Make SplitCal the default calorimeter
* Resize SplitCal to 4×6 m²
* Update tracker station z positions, fix UBT, TimeDet & SplitCal position (s. integration layout EDMS 3287817 v1)
* Obtain tauMuDet z position from muonshield position and length, instead of chamber trackers
* Update spectrometer yoke pit size according to EDMS no. 3309666
* Change separate constructions of tracker stations 1/2 and 3/4 to being identical
* Update strawtubes class

#### Strawtubes and SST

* strawtubes detID is now 7-digit! (without plane number)
* Change strawtubes detID decode function to tuple output
* Change max x of stereo hits to match straw length
* Get rid of straw diameter dependency in scale factor
* Change SST gas mixture to Ar/CO2 80%/20% at 1 bar

#### SND and MTC

* Rename MtcDetPoint and MtcDetHit classes to MTCDetPoint and MTCDetHit for consistency with detector naming conventions
* Change the logic of SiPM channel encoding in MTC. Now the number of SiPM is 1 and has a number of channels that fits the width of the plane. If the number of channels exceeds 1000, iterating a SiPM digit to 1 and distributing channels among new number of SiPMs.
* Set default parameters of MTC to 60x60 cm^2 and 4 aggregated channels according to Sep 2025 CM.
* Placement of SiliconTarget has been shifted by 10 cm to bring the final layer to within 10 cm of the MTC.
* Change EmulsionTarget detID decode function to tuple output

#### Generators

* Improve FixedTargetGenerator geometry handling
  - Replace fragile hardcoded TGeo navigation paths with geometry constants from `ship_geo.target`
  - Add `SetTargetCoordinates()` method to accept geometry-based start/end z-coordinates from `run_simScript.py`
  - Use robust `ship_geo.target.z0` and `ship_geo.target.length` instead of brittle `"cave_1/target_vacuum_box_1/TargetArea_1/HeVolume_1"` path
  - Maintain backward compatibility with legacy TGeo navigation as fallback
* Improve Pythia8Generator geometry handling
  - Apply same geometry robustness improvements as FixedTargetGenerator
  - Replace fragile `"volTarget_1"` TGeo navigation with geometry constants from `ship_geo.target`
  - Add `SetTargetCoordinates()` method for robust geometry-based target configuration
  - Maintain backward compatibility with legacy TGeo navigation as fallback
* Particle Gun has been updated: now user can set the coordinates of the PG via keys --V{x,y,z} and use --D{x,y} to uniformly smear the signal in a given x and y range

#### Reconstruction

* Assume all tracks are muons during track fit (avoid using MC truth)
* Reverse nmeas > 0 check to make sure 𝜒² is defined

#### Data Classes

* Use value storage for both hits and clusters instead of pointer storage (splitcal)
* Replace TVector3 with std::array and hit pointers with indices in splitcalCluster for RNtuple compatibility
* Replace splitcalPoint* constructor with vector-based constructor
* Move energy weights from Hit to Cluster, eliminating internal vectors (splitcal)
* Move MeanMaterialBudget to standalone function to reduce duplication and allow proper attribution of code to ALICE

#### Build System and Dependencies

* Use git-lfs to track ROOT files
* Allow using standalone TPythia for use with ROOT 6.32+
* FairShip is now licensed under LGPLv3+

#### Code Quality and Maintenance

* Consolidate basiclibs module into eventDisplay.py as it was only used by that single script
* Don't special case EOS paths (fix #566)
* run_simScript.py: use options directly internally instead of using intermediate variables
* makeCascade: Added new default target, moved to argparse
* The decorators from decorators.py now need to be applied explicitly using the new `apply_decorators` function.
* The --debug flag to run_simScript.py now controls the severity that FairLogger logs.

### Fixed

#### Geometry

* Changes to g4config.in to ensure it works with newer versions of GEANT4
* Fix mismatch dimension cavern ECN3 TCC8
* Fix typo of "vacuums" for strawtubes medium
* Ensure the web viewer is disabled when checking for geometry overlaps (workaround for https://github.com/root-project/root/issues/18881)
* Fix: Field direction of first magnet section 2 was wrong
* Fix: How the cavern is translated in z direction
* Fix: Preliminary fix of the length of the Target (to be refine)
* Fix splitcal strip dimensions and number of modules
* Fix: MTC geometry overlap

#### Simulation and Generators

* Fix FixedTargetGenerator to ensure it works with newer versions of Pythia
* Don't assume anything about the target substructure (FixedTargetGenerator)
* Fix crash in run_simScript.py
* Fix crash caused by decorators.py
* Fix missing decays of J/psi by using EvtGenDecayer
* Fix: hard cast bug in genie generator: after replacing old C-style cast histogram variable got nullptr value which afterwards caused segmentation fault
* Fix beam smearing: replace incorrect Gaussian radius with proper 2D Gaussian sampling. Ensures physical consistency; radius now follows Rayleigh distribution as expected.
* Fix EvtCalc crash due to string formatting

#### MTC and SND

* Correct extraction of SiPM channel positions in MTC
* Fix refactoring issue that broke MTC digitization
* Fix the condition in the sipm channel <-> fiber mapping that stopped looping over channels because of the distance between a fiber and a channel. Setting a flexible condition that depends on the aggregated channel size.
* Add flags for `python/ScifiMapping.py`
* Fixed SiliconTarget detector identifier.
* Fix the wrong methods in SND/MTC/MTCDetPoint.cxx to extract layer_id and layer_type for the MCPoint.
* Use GetLayerType instead of GetStationType in MTCDetector

#### Muon Shield and Field

* The fieldmap offset was calibrated with the old version of MS (ShieldUtils.py)
* Changing code to be more pythonic, adding new element in the output tuple -- the list of the Muon Shield magnet z-coordinates, that can be used to set a location of SND inside the Muon Shield (ShieldUtils.py)
* Fix: in `python/ShieldUtils.py` still used old coordinate system (SND was not correctly positioned in `python/shipDet_conf.py`)
* Changing paths to yaml files to more pythonic (`os.path.join()` now) (shipDet_conf.py)

#### Data Classes and I/O

* Make muonHit copy constructor public for std::vector compatibility
* Fix segmentation fault due to dummy containers (#453, #519)
* Fix logic of SST digitisation (#662)
* Fix double append of recognized stracks

#### Event Display and Reconstruction

* Fix event display crash caused by premature ROOT object initialization

#### Build System

* Remove SIMPATH dependency, replaced with EVTGENDATA for EvtGen data files (#648)
* Fix EvtGen library linking order for old autotools-based EvtGen installations
* Use standard library to expand env
* Autoload Pythia8 instead of manually loading in run_simScript.py

#### Code Quality

* Fix file endings
* Trim trailing whitespace
* Don't use TFile's deprecated attribute syntax
* Use lowercase FairLogger severities (uppercase ones are deprecated)
* Correct paths for default input files

### Removed

#### Custom Utilities

* Removed custom logger utilities (python/logger.py, utils/logger.hxx) in favour of Python's standard logging module

#### Build System

* Remove BOOST dependency from CMake build system - no longer required as ROOT 6 provides native serialisation

#### Obsolete Detector Configurations

* Remove Goliath magnet geometry and field implementation (ShipGoliath, ShipGoliathField, and associated field maps)
* Dropped support for old geometries without DecayVolumeMedium explicitly set (pre 24.11 release case).
* Removed old nuTauTargetDesign configurations from 0 to 2. Currently supported: 3 (2018, magnetized target) and 4 (Current, not magnetized target and spectrometer)
* Remove 2018, 2022 global designs
* Remove deprecated NuTauDet field map
* Remove target versions older than CDR
* Remove nutaudet folder, replaced by SND folder
* Remove old ecal and hcal in all of FairShip, affected files are notably the entire ecal and hcal directories as well as macro/run_anaEcal.py and python/shipPid.py. geometry/geometry_config.py, muonShieldOptimization/ana_ShipMuon.py, macro/ShipReco.py, macro/ShipAna.py, python/shipStrawTracking.py and python/shipPid.py.
* Remove ecal and hcal geometry files
* Removed unused class ShipChamber (leftover from TP design)
* Remove unused CaloDesign parameter from geometry configuration (only splitCal supported after ECAL/HCAL removal)
* Remove TP liquid scintillator variables

#### Muon Shield

* MS: Removed old options 7, 9, 10
* MS: Removed cobalt option
* MS: Removed stepGeo option
* MS: Removed the flag constant field in Absorber (HS) -> fixed to 1.7 T
* MS: run_simScript.py: The --noSC flag is removed, whether or not a configuration is SC hybrid depends on the config selected. Configurations are defined in the shield_db in geometry_config.py
* run_simScript.py: remove --muShieldDesign flag

#### Detector Components

* Remove unused straw veto station
* Remove strawtubes_single class
* Removed outdated version `sc_v6` since it is not fitting in the Cavern (also in the build-run)
* Removed 38 unused RPC geometry parameters from UpstreamTagger configuration (legacy from pre-simplification)
* Remove tankDesign variable, options
* Remove hadron absorber in ShipTargetStation.cxx
* Remove muon system
* Remove simpleTarget and personal study study_muEloss.py

#### Obsolete Code

* Remove unused, unrunnable shipPatRec_prev.py
* ShipAna.py: remove broken calorimetry
* Remove unused python/shipMuShield_only.py
* Remove (broken?) support for Nuage generator
* Remove nuTauTargetDesign variable, options
* Remove reloading of the `geometry_config.py` in `shipDet_conf.py`
* Removed unused run_simPgun.py
* Remove TTCluster.py
* Remove pid class

#### Build System

* Remove unused files for FLUKA
* Remove unused CMake modules
* Remove globalDesigns dictionary from run_simScript.py and create_field_perturbation.py, use inline defaults instead
* build(field,nutaudet): remove unnecessary ROOT_INCLUDE_DIR include

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
