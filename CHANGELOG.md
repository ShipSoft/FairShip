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
* Add support for Pythia 8.3xx. 8.2xx is still supported via preprocessor macros for the time being.
* Add dedicated --print-fields and --check-overlaps flags to run_simScript.py to use these debug tools.
* Add EvtGenDecayer for decaying J/psi (and other particles in future) when specifying the --EvtGenDecayer option
* Add enough straws to cover aperture entirely
* Add SST frame option (4 = aluminium, 10 = steel [default])
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


### Fixed

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

### Changed

* Replace ConfigRegistry with function-based geometry configuration API. Use `geometry_config.create_config(**params)` instead of `ConfigRegistry.loadpy()`
* Move `geometry_config.py` from `geometry/` to `python/` directory and update all imports from `from geometry import geometry_config` to `import geometry_config`
* Refactor strawtubes digitisation to use dedicated detector class
  - Created `strawtubesDetector` class inheriting from `BaseDetector`
  - Moved digitisation logic from `ShipDigiReco` to `detectors/strawtubesDetector.py`
  - Updated naming from "Strawtubes" to "strawtubes" for consistency
  - Changed branch name from "Digi_StrawtubesHits" to "Digi_strawtubesHits"
* Rename MtcDetPoint and MtcDetHit classes to MTCDetPoint and MTCDetHit for consistency with detector naming conventions
* Refactor digitisation to use detector classes for MTC, muon, time, SBT, and UpstreamTagger detectors
* Make BaseDetector an abstract base class to enforce interface contract
* Rewrite UpstreamTaggerHit for simplified scoring plane detector, remove RPC-specific code (#701, #354, #355)
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
* UBT box dimensions (BoxX, BoxY, BoxZ) are now configurable via geometry_config.py instead of hardcoded
* Configuration storage modernized from pickle to JSON
  - Geometry configurations are now saved as JSON strings (using `std::string`) instead of pickled Python objects in ROOT files
  - Automatic format detection: new code reads both JSON (new format) and pickle (legacy format) files without user intervention
* Change the logic of SiPM channel encoding in MTC. Now the number of SiPM is 1 and has a number of channels that fits the width of the plane. If the number of channels exceeds 1000, iterating a SiPM digit to 1 and distributing channels among new number of SiPMs.
* Set default parameters of MTC to 60x60 cm^2 and 4 aggregated channels according to Sep 2025 CM.
* Placement of SiliconTarget has been shifted by 10 cm to bring the final layer to within 10 cm of the MTC.

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
* Removed 38 unused RPC geometry parameters from UpstreamTagger configuration (legacy from pre-simplification)
* Remove deprecated NuTauDet field map
* Remove tankDesign variable, options
* Remove target versions older than CDR
* Remove hadron absorber in ShipTargetStation.cxx
* Remove old ecal and hcal in all of FairSHiP, affected files are notably the entire ecal and hcal directories as well as macro/run_anaEcal.py and python/shipPid.py. geometry/geometry_config.py, muonShieldOptimization/ana_ShipMuon.py, macro/ShipReco.py, macro/ShipAna.py, python/shipStrawTracking.py and python/shipPid.py.
* Remove globalDesigns dictionary from run_simScript.py and create_field_perturbation.py, use inline defaults instead
* Remove unused CaloDesign parameter from geometry configuration (only splitCal supported after ECAL/HCAL removal)
* Removed unused class ShipChamber (leftover from TP design)
* Removed unused run_simPgun.py

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
