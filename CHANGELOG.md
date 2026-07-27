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

* Add `--pythia8-tune` (`default`, `FTFT`) to `run_fixedTarget.py` and `FixedTargetGenerator::SetPythiaTune` to select the FTFT Pythia8 tune for open charm and beauty production in fixed-target collisions (arXiv:2608.29076) in the Pythia8 primary interaction. The Pythia8 default (Monash 2013) remains the default. Charm and beauty read from cascade input files are unaffected.

* Add converter of neutrino flux to the aegir-genie format


### Changed

### Fixed

### Removed

## 26.09 - 2026-09-15

This release fixes bugs that change simulation output. Samples produced with
26.07 or earlier are not directly comparable where magnetic field maps,
strawtube hit recording, SBT veto decisions, or HNL, dark photon and RPV-SUSY
production rates are involved. `G4only` FixedTarget runs also draw a different
random sequence.

### Added

* He Balloon added with configurable thickness and material.
* 2026 BDF target design (33 pure tungsten disks with a larger rear block, steel core with serpentine He cooling grooves, jacket tube, flanges, upstream beam window and cover plate, and domed rear endcap), extracted from CATIA model ST1A07710_01_AB.02. Select with `--target-yaml geometry/target_config_2026.yaml`; the legacy design remains the default. Downstream elements are positioned using the nominal legacy target length so both designs can be compared directly.
* Write a `FileSummary` record into the `run_simScript.py` output, merging the `PoT`, `EnergyCut` and `prodSite` entries of the generator input files and listing the inputs with their individual PoT, so event provenance can be traced back through the simulation chain. Only files the generators actually read are recorded, and a missing or unreadable input summary warns instead of failing a completed simulation. This is a different record from the `run_fixedTarget.py` `FileSummary` added in 26.04, which stores the run options.
* Add `--target-composition` (`W` default, `Mo`) and `-A` to `run_fixedTarget`, deriving the charm and beauty over min-bias cross-section ratios from the target mass number by scaling the Molybdenum reference values as `(A/A_Mo)^(1 - 0.71)`
* Add `AI_POLICY.md` at the repository root, kept in sync through the shared config-sync workflow

### Changed

* Decay volume rebuilt as nested solids: the decay medium sits inside the PVC balloon, which sits inside a solid support vessel (`decay_medium` ⊂ `HeBalloon` ⊂ `VetoInnerWall`). This replaces the previous per-block sibling volumes, which were placed at exactly coincident surfaces. The `HeBalloon` layer is created only when the balloon thickness is greater than zero; otherwise `decay_medium` is placed directly inside `VetoInnerWall`. The per-block `decay_medium_block{N}` volumes (previously the renamed `DecayVacuum_block{N}` fiducial volumes) are merged into a single `decay_medium`, so the old per-block name no longer exists. Dimensions and materials are unchanged; navigation is simpler and slightly faster.
* SBT sensitive medium is now LAB-based liquid scintillator (`LiquidScintillator`) rather than the plastic `Scintillator`, which remains in use by SplitCal
* Unify the two identical aluminium entries in `media.geo` (`aluminium` and `Aluminum`) into a single `Aluminium` material and update all references, including `geometry/veto_config_helium.yaml`. Configuration files using the old spellings need updating.
* Changed option name from `--target_composition` to `--target-composition` in `makeCascade` and `makeDecay`
* `--chicc` and `--chibb` become explicit `float` overrides in `run_fixedTarget`, defaulting to the value derived from the target mass number
* Make `--chicc` and `--chibb` mutually exclusive in `makeDecay` and `run_fixedTarget`, and raise a clear error when the override does not match the run type (e.g. `--chicc` for a beauty run) instead of silently ignoring it
* Deduplicate the charm/beauty over min-bias cross-section scaling shared by `makeDecay` and `run_fixedTarget` into `python/heavyFlavourScaling.py`
* Take the proximity shielding reference length from the geometry configuration (`target.length_fixed`) and pass it to `ShipTargetStation` through `SetShieldingReferenceLength`, instead of hardcoding it as 158.64 cm in Python and 1586.4 mm in C++; the C++ side now aborts if it is left unset. The `hadronAbsorber.z` placement is unchanged.
* Centralise the ROOT ≥ 6.32 `TClonesArray` element-assignment workaround as `rootUtils.assignClonesArrayItem` and migrate the six scripts carrying hand-copied variants of it, removing the remaining `ROOT.std.swap` uses in `makeMuonEM` and `muDIS_mergeFiles` that corrupted the source object
* Split `--validation`'s `track_stats` into separate `track_counts`, `track_numeric_stats` and `pdg_counts` accumulators, skip missing branches explicitly, and report the accumulated track weight as a `Track weight` line in the MCTrack validation section
* Raise the minimum CMake version to 3.26 and drop the redundant `cmake_policy(SET CMP0118 NEW)`, which is NEW by default at that floor
* Use dense vectors instead of `std::map` for ShipStack track selection and index remapping, roughly halving CPU time and reducing peak memory for high-multiplicity events (e.g. kaon/pion splitting)
* Count ShipStack MC points per track instead of per (track, detector) and stop the mother-flagging walk at already-flagged ancestors, further reducing track-selection CPU time for high-multiplicity events
* Cache geometry lookups in the digitisation hot paths: `strawtubes::StrawEndPoints` caches endpoints per `detID` instead of rebuilding the volume path and re-navigating on every hit, and `splitcalHit` caches the strip `TGeoNode` per name instead of scanning all strip nodes for every digitised hit. Both caches are keyed by geometry-derived identifiers, so results are unchanged.
* Memoise the HNL total decay width and reuse the integrand `TF1` across `integral()` calls. `NDecayWidth()` was recomputed for each of the roughly 40 `findBranchingRatio()` calls during generator setup, each triggering up to 33 numerical integrals. Widths and branching ratios are bit-identical.
* Reduce repeated scans in pattern recognition and tracking QA: use sets for the used-hit, duplicate-hit and outside-station membership tests in the nested seed loops of `shipPatRec`/`shipStrawTracking`, and build one `strawtubesPoint` index per event in `tracking_benchmark` instead of rescanning the branch in each of the four truth helpers
* Build a per-event trackID to hits map in `eventDisplay.DrawMCTracks` instead of re-iterating every hit collection for every MC track, and resolve branches with `getattr` instead of `eval`. Branch and in-branch ordering are preserved.
* Avoid wasted work in the generator hot paths: take the `G4only` early return in `FixedTargetGenerator` before the interaction-point rejection sampling whose result that mode discards, look up `muList` with `find()` instead of a linear scan in `MuonBackGenerator`, and demote the per-decay "not in EvtGen list" warning in `TEvtGenDecayer` to debug. The `G4only` `gRandom` draw sequence changes as a result, and is statistically equivalent.

### Fixed

#### Magnetic field

* Fix the field-map reader: clamp off-grid reads so trilinear interpolation's `iBin+1` neighbour no longer wraps onto the opposite corner of the next slice (weight 1 at the upper edge), reject maps with fewer than two bins per axis instead of silently zeroing the field everywhere, declare the bin count `Nu` as `Int_t` rather than `Float_t`, and correct the x-y quadrant-symmetry comment, which omitted the `Bz` sign flip for `y < 0`
* Zero the `FairShipFields::get` outputs before use and null-check `gMC->GetMagField()`. The work array was seeded from the caller's uninitialised outputs, and the early-return paths never wrote `Bx`/`By`/`Bz`, handing genfit garbage.
* Persist and reload field-map parameters again in `ShipFieldPar`, where the Bell branch was gated on `fType in [1, kMaxFieldMapType]` and shadowed the field-map branch; initialise `ShipBellField::fOrient` and `ShipFieldPar::fBtube`, and make `ShipBellField::Print()` report the Bell parameters instead of the constant-field message copied from `ShipConstField`
* Build the composite field once in `ShipFieldMaker::defineComposite` after all members are collected. It was constructed inside the loop over field names, so N composites were built from progressively incomplete field lists, and N-1 of them leaked.
* Draw an independent noise value per core in `add_noise_to_field` and drop the self-normalisation, so `--peak` sets the amplitude rather than only the sign; remove the dead `dStruct.x/y/z` writes in `convertMisisMap`, which PyROOT silently attached as Python attributes and no branch stored

#### Generators and decays

* Read the final row of every branching-ratio histogram in `pythia8_conf_utils.parse_histograms`. An off-by-one slice dropped the last bin, so production branching ratios interpolated to 0 at the highest mass point. The data-row regex now also accepts a leading minus sign, which is needed to parse the terminating rows and recovers the nonzero final values in the `lambdab`, `Xib` and `Omega_b` histograms.
* Correct the dark photon production rates: test `pbrem1` before the `pbrem` substring so the dipole mode is reachable, return rate 0 instead of 1 for an unknown mother PDG or production mode, and match `proton_bremsstrahlung.hProdPDF` bin widths to the sample grids, where the theta step was twice too large and shifted and the momentum step divided by `binsp-1` on an endpoint-excluded grid, double-filling and skipping bins
* Fix RPV-SUSY production and decay: accumulate `sumBR` in the B0 block of `pythia8_conf.configurerpvsusy` so the `22 22` filler that normalises each meson's BR table is added (its absence distorted the B0 against B+ neutralino production ratio), honour a boolean `inclusive` argument, and rewrite the dimensionally inconsistent K\*/D\*/phi vector-meson factor in `rpvsusy.Width_N_L` to match the sibling `Width_H_L` form
* Disable Lambda_c decays inside Pythia8 in `DecayConfigNuAge`. The line read `15:mayDecay = off`, a copy of the tau line, so Lambda_c was decayed by Pythia8 instead of being returned to transport. Also initialise `AlphaPDG`/`He5PDG` in `UserDecay` and skip on a failed `TDatabasePDG` lookup, rather than configuring a decay for an arbitrary PDG code.
* Give each `HNLbranchings` instance its own integrand `TF1` name, so live instances cannot collide in ROOT's global function list

#### Geometry and digitisation

* Fix out-of-bounds writes in detector geometry construction. `ShipMuonShield::Initialize` wrote 16 magnet-parameter vectors through `operator[]` after only `reserve()`-ing capacity, and now also guards against configuring more magnets than the hardcoded `fieldDirection` list provides; `splitcal::ConstructGeometry` created only `newHCALfilter[0]`/`newHCALdet[0]` but placed `fnHCALSamplings` of them, dereferencing uninitialised volume pointers.
* Size the splitcal HCAL volume arrays to `fnHCALSamplings` with `std::vector` instead of fixed `[100]` arrays, which could overflow now that the construction loop is driven by the configurable sampling count
* Record every straw-tube traversal in `strawtubes::ProcessHits`. A never-cleared `fVolumeID` marker made the code skip any hit whose exited straw matched it, so after the first hit in a straw every later traversal — curling track, delta ray, next track, next event — was dropped along with its energy loss.
* Use the Y-layer z-map when computing the splitcal cluster start and end Z from the Y projection. Indexing the X-layer map with Y-layer keys silently inserted 0 through `operator[]` and roughly halved the reported z. Clusters with no X or no Y hits now return early with only the energy set, instead of dereferencing empty weighted maps.
* Initialise `TimeDetHit` `t_1`/`t_2` and `MTCDetHit` time in-class so they are no longer indeterminate on the default-constructor and null-track paths, guard the `MTCDetHit` scintillator branch against an empty points vector (NaN coordinates, `FLT_MAX` time), assign `fDetList` in `ShipStack::UpdateTrackIndex` so it stops leaking a detector iterator every event, and correct the `strawtubes::StrawEndPoints` declaration to match the definition's `(bot, top)` argument order
* Reject unknown target design versions with a fatal error naming the value, instead of falling through a bare `else` and silently building the 2026 target
* Thread a single accumulator through `geomGeant4.nextLevel` so the printed total magnet mass includes depth ≥ 3 and the top-level leaves, apply `fieldsList[0]` instead of a hardcoded `MainSpecMap` in the single-field fallback, and pass the global detector id rather than the local fibre id to `GetLocalPos` in `SciFiMapping`, which had dropped the plane tilt

#### Reconstruction and analysis

* Apply tesla units to both components of the MTC constant field in `ACTSReco`. `acts.Vector3(0.0, -1.2, 0.0 * u.T)` left the y component in ACTS natural units (about -4000 T), so every Kalman fit through the MTC used a field roughly 4000 times too strong.
* Correct the two-track vertex fit in `shipVertex`. The transverse residual model used `a[0] + a[3]*(a[2] - z0)` while the genfit states are extrapolated to `z = z0`, flipping the slope term's sign, mirroring the chi2 landscape about `a[2] = z0` and producing wrong-sign z-slope covariance terms. The stepwise extrapolation also mutated the reference returned by `getFittedState()` in place, so a track reused in a later pair carried a state left at a previous candidate vertex.
* Accumulate the fractional MC-truth votes in `Tracklet::link2MCTrack` as `double`. An `unordered_map<int, int>` truncated every `1./nTot` increment to 0, so the minimum-fraction threshold never fired and the function returned the last point's track ID rather than the dominant track.
* Fix `convertToACTS`: seed `gRandom` once before the event loop, where it was reseeded every event so strawtube digitisation drew an identical random sequence each time, and draw `t0` from `gRandom` instead of a fresh default-seeded `TRandom`; create the vertex-tree vectors empty so event 0 no longer carries a spurious all-zero vertex; encode the per-event vertex index in the barcode instead of a constant; and preserve the SND `SiliconTarget` per-track hit counts, which were cleared before the MTC block
* Open the input file read-only in the `shipStrawTracking` QA step, where it was opened for update and wrote a duplicate key cycle of the unmodified tree into the user's file. The dead `--method` option now warns, and the fitted-state handler reports the actual exception instead of mislabelling `ZeroDivisionError`/`KeyError` as a fitted-state problem.
* Treat `-n` as an event count in `ShipReco` (`min(entries, firstEvent + nEvents)`) rather than an end index, and move the per-event SBT/UBT/track decisions and the `nrtracks`/`nrSBT` fills out of the per-candidate loop in `ShipAna`, which double-filled them for multi-candidate events

#### Veto and decay vessel

* `veto` now registers the configured `sensitiveMed` instead of a hardcoded medium name; previously any other value resolved to a null `TGeoMedium`
* Repair the SBT veto decisions in `shipVeto`: for `mcParticle > 0` test whether the particle is absent from a digi, instead of excluding any digi with a differing contributor, which wrongly dropped mixed-contributor digis that do contain the particle; compare the straw-veto distance against `distmin` in `fiducialCheck`, where the computed distance was previously unused; seed `self.random` (now a `TRandom3`), the generator the class actually draws from, instead of `ROOT.gRandom`; and return the `SBT_decision` result from `SBT_plastic_decision`/`SBT_liquid_decision`, which discarded the tuple and returned `None`
* Match the fiducial-volume checks in `shipVeto` and `analysis_toolkit` on the `decay_medium` name prefix. The explicit volume list they used had also gone stale, still naming `decay_medium_block3` to `decay_medium_block5`.

#### Muon DIS and muon-shield studies

* Fix `makeMuonDIS` under ROOT ≥ 6.32, where `TClonesArray` item assignment raises and the script did not run at all: use `ConstructedAt(i)` plus copy-assign for the muon, DIS and soft-daughter vectors. Set the DIS cross section (event weight) in the muon vector before it is copied to the output, so entries no longer store the previous event's value, and track the converged proton and neutron cross sections separately so `update_file()` applies the one matching each entry's target flag instead of overwriting every entry with the last (neutron) value.
* Fix the muon-DIS ntuple makers: replace `TClonesArray` item assignment in `make_nTuple_SBT`, `make_nTuple_Tr` and `add_muonresponse`; write the final SBT-hit count into the SBT column (`-3`) rather than the UBT column (`-2`); and apply the missing `track_id == muon_` filter to the strawtube loop in `make_nTuple_Tr`, which in multi-muon events processed every muon's hits once per muon
* Replace the removed `TDirectory` attribute access (`file.DIS`, `file.cbmsim`) with item access throughout the `muonDIS` scripts
* Validate `--nDIS` immediately after argument parsing in `makeMuonDIS`. Zero divides by zero in the cross-section index calculation, and an odd value splits the proton and neutron DIS phases unequally at the `a == nDIS // 2` target switch.
* Fix a batch of muon-shield optimisation script and detector bugs: initialise `exitHadronAbsorber`'s `EMax`, `fUniqueID` and `fUseCaveCoordinates` in-class, where a garbage `EMax` could stop every track and a garbage flag selected the wrong geometry branch; pass the now-required `-g` geometry argument and split single-token option strings in `run_reco`; build the `hadd` file list as a string and wire the CLI run range and charm flag through to `compactify` in `compactingBackgroundProduction`; drop the per-branch `Fill()` that doubled entries in `muDIS_mergeFiles`; copy rather than `std::swap` the muon vector in `makeMuonEM`; correct `int(prod/10)` in `run_prod` and the run range in `runCharmHadProd`; assign the `origin()` result and open files before `Get()` in `ana_ShipMuon`; and fix the duplicated PDG 4232 in `extractNeutrinosAndUpdateWeight`
* Initialise loop-dependent variables before use in the muon-shield optimisation scripts. `ana_ShipMuon` now fails fast when no geofile is found, guards MC-track access on the track actually fetched, skips rare-event lines preceding the first record, and dispatches on the process type for mixed work lists; `runCharmHadProd` hoists the loop-invariant `orun` so `merge()` no longer depends on the last iteration having run; and `run_reco` tracks `(inputfile, geofile)` per job instead of reusing variables leaked from the launch loop, binds the `Popen` handle before the `None` check, and skips prefixes without a geofile when merging ntuples.
* Flush the last rare-event record in `ana_ShipMuon.makeNicePrintout`. A record was appended only when the next header was parsed, so the final record of every input file was dropped from the printed table and from the weighted muon rates.
* Close the event files opened by `ana_ShipMuon.eventsWithStrawPoints` and `eventsWithEntryPoints`
* Replace the untyped setup dictionaries in `study_muMSC.py` and `study_GammaConv.py` with a `NamedTuple` per script, so the material string no longer shares a type with the numeric thickness and momentum. Values are unchanged.

#### Macros and simulation driver

* Fail with a clear error when an explicit `--inputFile` matches no files. The empty result still disabled the default-input fallback, and `ut.checkFileExists` accepts an empty list, so setup proceeded with no input at all.
* Fix `run_simScript` argument handling: `-f none` set `inputFile` to `None` and then iterated it (`TypeError`); `--SusyBench` lacked `type=int`, so any supplied value indexed int-keyed dictionaries as a string; and three error paths (missing muon-DIS or ntuple input, cosmics init failure) exited with status 0, reporting success to batch systems
* Fix macro import-time crashes and stale API calls: `mergeMbias` referenced the nonexistent `hadronAbsorber.length` at import and drew a stale loop variable into every pad; `dumpEvent` called the nonexistent `Config.loadpy`; `getInteractionAndRadiationLength` now calls the free `shipgen::MeanMaterialBudget` with a 10-element parameter array instead of the removed `GenieGenerator` member; and `run_ACTSTracking` joins its output path with a separator and takes an integer `--nEvents`
* Fix `eventDisplay`, `makeCascade`, `makeDecay` and `runPythia8`: `-i/--HiddenParticleID` takes `type=int`, and the HNL end-vertex daughter search uses a found flag so the last MC track is not silently used; `makeCascade`'s interpolation-anchor update is dedented out of the inner gap-fill loop so the anchor advances; `makeDecay` opens the EOS histogram fallback through the `$EOSSHIP` prefix and fixes a printf placeholder passed to `print()`; and the `runPythia8` analysis functions guard against empty histograms so the non-Drell-Yan modes do not divide by zero
* Advance the pad counter for empty species in `mergeMbias.TplotP`. An empty first species made the next species draw over the previous pad and left the last pad blank on both the P and >P canvases.
* Open `makeDecay` input paths directly rather than routing any path containing the substring `eos` through XRootD; ROOT resolves `/eos` paths itself through FUSE or XRootD
* Accept an explicit `-A` without `--target-composition` in `heavyFlavourScaling.derive_cross_sections`, where calls such as `derive_cross_sections(A=181)` were rejected, and omit the target label from the printed summary when `-A` overrides the preset, so a stale preset name no longer appears beside the overriding value

#### Python helpers and type checking

* Harden miscellaneous Python helpers: `global_variables.__getattr__` raises `AttributeError` for missing attributes instead of returning `None`, which also made `hasattr` always true and masked typos; `saveBasicParameters` uses `Config` in the string branch, where it built an `AttrDict` and then called `dumps_json`, which only `Config` provides, and guards the `FAIRROOT_HASH` environment lookup; `shipDet_conf` applies the missing `* u.cm` to `snd_nuTauTT_TTY`; `TrackExtrapolateTool` honours its documented None-on-failure contract and guards against division by `pz == 0`; `analysis_toolkit` always defines `veto_geo`, guards the empty-average NaN and aligns the fiducial threshold with its 100 cm docstring; and `eminem_importer` applies the column unit when an offset is given without an offset unit
* Harden the ROOT and histogram-comparison helpers: `rootUtils.checkFileExists` now classifies tree and ntuple files correctly, closes the files it opens and exits non-zero on a genuine type mismatch; `bookProf` reuses an existing profile instead of resetting and discarding it; `readHists` no longer leaks its file; `checkMagFields` tests `InheritsFrom('TH3')` rather than `ClassName() == 'TH3F'`, so the projections are actually made because `bookHist` creates `TH3D`, and iterates a snapshot instead of mutating the histogram dictionary while looping over it; and `compare_histograms` compares bin contents and errors instead of `TH1::IsEqual`, which compares `TObject` addresses and so always reported identical histograms as different, and propagates a non-zero exit
* Correct type annotations and ROOT stubs flagged by `pyrefly`: the smeared-hit helpers' `digiHit`/`detID` are ints, the vertex-fit chi2 returns a float and `z0` is a float z coordinate in cm; the histogram dictionary holds `TH1`/`TH2` subtypes and the run database holds both string and int lists, and `compactify`'s charm flag is passed as `bool`; `generate_file` requires the parsed `args` and passes `header`/`index` to `to_csv` as bools; and the stubs gain the `shipgen` namespace with `MeanMaterialBudget` plus the `SetDesign`, `SetLastDiskDiameter` and `SetShieldingReferenceLength` setters on `ShipTargetStation`

### Removed

* Remove the unreachable proton-PID downgrade (`2212` to `+-211`) and the hardcoded `pidProton` flag from `shipVertex` and `ShipReco`, together with the divergent unconditional copy of the same rule in `ShipAna.RedoVertexing`. Every track in `FitTracks` is fitted under the muon hypothesis, so the branch could never fire.

## 26.07 - 2026-07-21

### Added

* Add option to split kaons and pions right before they decay, to increase the number of muons
* Added TRY_2026 MS version.
* Make particle gun polar angle configurable via `--thetaMin`/`--thetaMax`
* Add `run_tracking_scan.py` to sweep the tracking benchmark over angle and multiplicity grids
* Add charge-ID efficiency metric to the tracking benchmark
* Add iron material definition and simplified SiTarget digitization in the MTC, with strawtubes gating in the reconstruction flow

### Changed

* Flatten field-map storage and make the field evaluator reentrant

### Fixed

* Remove duplicated 4232 pdg code in extractNeutrinosAndUpdateWeight
* Update charm and beauty over mbias cross sections in run_fixedTarget
* Fix pot branch in Decay tree from makeDecay
* Fix check of existing particle pdg in makeCascade
* Restore `tPythia6Generator` instantiation from Python — broken since 26.02 by the `SHiP::Generator` base-class refactor leaving the file-based `Init` overloads pure virtual without a stub override (#1272)
* Fix call to next Pythia event generation
* Eliminate redundant hadron absorber field map
* Fix Magnet MS5 and MS6 to store new SND conceptual design
* Fix a batch of generator bugs: null-pointer dereferences and vertex fallback, mother/vertex/energy bookkeeping, RNG-selection and engine member initialisation, charm interaction-point sampling in geometry-coordinates mode, and assorted low-severity issues
* Plug `HNLPythia8Generator` memory leaks
* Fix scintillator tile hit processing
* Exclude clone tracks from tracking metrics and guard the scan sort, and improve error handling in the tracking scan
* Skip RMSE fill when there are no matched extrapolations
* Correct MC-track checkbox state and truth/fit pairing in the event display
* Give `shipVertex` `VertexError` a uniform 3-tuple return
* Don't crash on unreadable ROOT files where a skip was intended
* Match `run_simScript` output `TFile` by full path
* Correct return types in `compute_total_br` and `compute_max_total_br`

### Removed

* Remove unused legacy `Pythia6Generator` (custom text-format event-record reader from 2008, zero callsites anywhere in the tree). `tPythia6Generator` is unaffected.

## 26.06 - 2026-06-18

### Added

* Add experimental script to import Muons and Matter pkl files
* Added GenieOption to read simulations with the GENIE Geometry Driver (i.e. gevgen_fnal)
* Add `TTreeGenerator` to read events from ROOT TTrees (including the converted M&M ntuples)
* Add `--ttree` option to `run_simScript.py` for ROOT TTree input
* Add `--target_composition` option to `makeDecay`, defaulting to Tungsten and mirroring the `makeCascade.py` flag
* Add `--validation` flag to `run_simScript.py` and `ShipReco.py` that prints generator, output, pattern-recognition, and fit counters
* Add `--remote-input` flag to `run_simScript.py` for direct `root://…` input without local download
* Add `--reproducible` mode and explicit, reusable run IDs in `run_simScript.py` / `run_fixedTarget.py`, with consistent metadata written into output headers
* Add pixi environment (`pixi.toml`) and pixi-based CI build workflow as the new primary build path
* Add CI sim-chain tasks driven by pixi
* Add CI workflow to build and publish pixi-based container images on release
* Add REUSE compliance badge to README
* Add pixi installation instructions to README

### Changed

* Change A scaling in makeDecay
* Rewrite README to be pixi-first
* Derive project version from git tags via `git describe` instead of hardcoded `0.0.0`
* Migrate CI to shared `ShipSoft/.github` reusable workflows

### Fixed

* Validate `-A` choice for `--DarkPhoton` runs; previously silently misconfigured (#1166)
* Always allocate `validation_stats` dict and fix `GetHitID` typo in `shipDigiReco`
* Harden generator input handling: fail-fast on missing files, trees, branches, and out-of-range start events, and switch to `TFile::Open` for remote-input compatibility
* Prevent MuonBack post-processing double-free of output `TFile` at interpreter shutdown (#1226)
* Null-init `MuonBackGenerator` pointers and drop dead `CloseFile` path
* Keep `BranchList` `TObjStrings` alive under ROOT 6.40 PyROOT ownership changes
* Load `libEGPythia6` in `shipRoot_conf`
* Remove unnecessary `libG4clhep` loads
* Chain `Initialize` through immediate parent in `exitHadronAbsorber`
* Address real bugs surfaced by `pyrefly` static type-checking
* Remove throwing static initializers
* Initialise variables before conditional branches
* Replace `atof`/`atoi` with `std::stod`/`std::stoi` for proper error handling
* Replace floating-point loop counters with integers
* Use `size_t` for `ShipMuonShield` corner-index loop
* Use `git rev-parse` in `retrieveGitTags` for Python 3 compatibility
* Correct DOI badge link in README
* Fix help-message text in `makeDecay`

### Removed

* Drop unused HepMC dependency
* Retire aliBuild-driven `build-run.yml`; replaced by `pixi-build.yml`

## 26.05 - 2026-05-25

### Added

* Added ParticleGunGenerator #1183
* Add time window event overlay script (`macro/make_time_window.py`) for constructing realistic pileup from MC truth events
* Add `SetStartT` and `GetEventID` accessors to `ShipMCTrack`
* Add beam smearing and painting support to `DPPythia8Generator`

### Changed

* Update default spectrometer field map to 2025 MgB2 map (`2025_02_12_SHiP_SpectrometerField_ECN3_MgB2.root`)
* Replace incorrectly oriented spectrometer field maps with corrected versions (2026_05_07)

### Fixed

* Import EGPythia6 library from basiclibs in makeMuonDIS
* Remove deprecated attribute syntax in the GST TTree copy within GENIE run_simScript option
* Keep FixedTargetGenerator retrying if Pythia fails to generate an event, until a max number of retries is reached
* Recompute the two-track DOCA at the chi^2-optimal vertex (`HNLPosFit`) instead of the iterative geometric one. The geometric DOCA was evaluated with tangent-line linearisations at the geometric iteration's converged z and overestimated the line-to-line distance wherever Migrad shifted the vertex; re-extrapolating the genfit states the small residual dz to `HNLPosFit.Z()` recovers a substantial fraction of signal at the standard DOCA preselection cut on HNL signal MC.
* Anchor `Chamber1.z` to the decay vessel geometry so the HNL minimum decay length and the muon-DIS start position track the upstream end of the decay vessel; the legacy formula in `geometry_config.py` left both ~1.8 m too far downstream after the March 2025 coordinate-system change, reducing HNL generation acceptance by about 3.6 % of the decay vessel volume.
* Work around ROOT 6.40 GIL bug that crashes on `TH1::Fit()` warnings by guarding with `GetEntries() > 0`
* Prevent double-delete segfaults with ROOT 6.40 PyROOT ownership changes by transferring ownership to C++ for objects managed by FairRoot, genfit, and Geant4
* Guard meson-production chain export for proton-bremsstrahlung mode in `DPPythia8Generator`, fixing duplicated dark photon and spurious Pythia system entry
* Support both old (2018) and new MuonBack production files by detecting `PlaneHAPoint` branch and setting correct z-offset (#1181)
* Guard vertex fit against unconverged Migrad and failed HESSE to prevent unreliable vertex positions
* Restore chi2 assignment in vertex fit TMinuit callback (`f.value` instead of local rebind)
* Keep ROOT streamers (`+` LinkDef flag) for `MTCDetector` and `strawtubes`, needed for dynamic downcasting via `run.GetListOfModules()`
* Remove unused ROOT streamers from other detector classes
* Check if `inputfile` is a list or single string in `run_simScript.py`
* Show full path format in `--field_map` help text
* Make sumw cache unique per file and fail fast on unknown Point class in time window overlay script

### Removed

* Remove duplicate `makeMuonDIS.py` from `muonShieldOptimization/` (canonical version is in `muonDIS/`)
* Remove incorrectly oriented field maps added in 26.04

## 26.04 - 2026-04-30

### Added

* Add angular acceptance cut in HNL and DP generators to skip events outside the decay vessel
* Add FileSummary to run_fixedTarget.py to save all the options for reference (#1140)
* Add new 2026_04_01_SHiP_MainSpectrometerField_V13.root fieldmap
* Add GenFit unbiased hit residuals and pulls to tracking benchmark
* Add type stubs for ROOT, XRootD, acts, and genfit
* Add CI workflow to publish plots to GitHub Pages and embed in PR comments

### Changed

* Make artificial retina the baseline option for pattern recognition
* `nrOfRetries()` in HNL and DP generators now counts only production failures; geometric acceptance rejections are tracked separately via `nrOfGeoRejections()`
* Read vessel end dimensions from veto YAML config instead of hardcoding in `geometry_config.py`
* Replace uproot with PyROOT in compare_histograms

### Fixed

* Add missing SetPaintRadius method and proper beam smearing in DPPythia8Generator class.
* Fix vertex finding for upstream vertices by using stepwise extrapolation
* Derive track fit seed from pattern recognition and first hit position instead of hard-coded coordinate (#763)
* Replace obsolete elliptical acceptance cut with rectangular acceptance in track pattern recognition
* Fix CI build warnings: add missing `override` specifiers, fix `Print()` and `Init()` virtual hiding, remove unused `FairShipFields` LinkDef entry
* Remove no-effect statements (unused object creation, bare index accesses) from Python scripts
* Determine track charge from pattern recognition slope bending and fit both charge hypotheses
* Skip inconsistent track hypothesis after fit
* Improve track fitting loop robustness and add convergence check
* Replace `from ROOT import` with namespace-qualified access
* Update references to removed muon shield configurations

### Removed

* Remove fake pattern recognition fallback

## 26.03 - 2026-03-31

### Added

* Tracking performance benchmark for straw tube spectrometer (`python/tracking_benchmark.py`, `macro/run_tracking_benchmark.py`): measures efficiency, clone rate, ghost rate, and momentum/position/angular resolution using particle gun events with template matching pattern recognition
* Add Findgenfit2.cmake module to support both upstream GenFit and the fork
* New warm MS option TRY_2025 (Stellatryon v.2) and its field map
* Add GENIE configs for Pythia8 instead of Pythia6 (#1054)
* Add `SHiP::DetectorPoint` base class with EventID for all detector points (#1059, #1075)
* Add file glob and `nEvents=-1` support to `run_simScript.py` input files (#1041)
* Store coordinates of MTC hits (#1026)

### Changed

* Implement `SHiP::Detector` base class; veto detector now uses doubles (#1079)
* Migrate SND detectors (MTCDetector, SiliconTarget, Target, TargetTracker) and exitHadronAbsorber to `SHiP::Detector` base class
* Rename `ShipHit` to `SHiP::DetectorHit` and clean up subclass hierarchy
* Extract duplicated `InitMedium` into `ShipGeo::InitMedium` free function
* Make `SHiP::Generator` base class for all generators (#1047); change `const char*` to `optional<string>` (#1053)
* Input file reading uses TChain; `run_simScript.py` accepts list of files (#1027)
* Make MTC scintillating tile size configurable; change default field (-1.2 T to -1.7 T) and tile size (1 cm to 5 cm) (#1091)
* Remove setting of FairMC links (#1109)
* Change passive SiliconTarget material from tungstenalloySND to pure tungsten
* Change naming convention for simulation files to `{sim,geo,params}_{uuid4}.root`, with optional `--tag` parameter
* Change ShipMuonShield to accept new magnet configuration: no fixed number of magnets and variable z-gap between them
* Disable magnetic field in the MS and remove field map upload in `run_fixedTarget.py`
* Update `run_fixedTarget` to save tracks for hits in post-target sensitive plane
* Change function SND in `shipDet_conf.py`
* UseGeneralProcess only set to false when cross-sections need changing
* `makeGenieEvents`: automatically set GXMLPATH to genie_config folder; remove `--nudet` option
* Only get evtNo in ShipStack if there are tracks (#1051)
* Turn warning to debug in MuonBackGenerator (#1036)
* Bump minimum ROOT to 6.36, CMake to 3.20, C++ standard to C++20
* Remove outdated dependency version gates for Pythia8 < 8.300, ROOT < 6.32, and old Geant4VMC
* Modernise C++: use C++20 features (`map::contains`, `ranges`, structured bindings), `std::span`, nullptr, override, `= delete`
* Expand ruff lint rules and fix Python code quality issues; replace bare `except:` with specific exception types

### Fixed

* Fix pattern recognition producing far fewer tracks than expected after geometry change from 2 planes to 1 plane per view (#580)
* Fix `StrawDecode` Python indexing: change return type from `std::tuple` to `std::array` so cppyy maps `operator[]` to `__getitem__`
* Fix EventDisplay "Branch not found" errors for MC point branches after `std::vector` migration (#1126)
* Fix EventDisplay errors for nonexistent MC point branches (#900)
* Fix EventDisplay initialisation order for FairRunAna/FairEventManager
* Fix EventDisplay handling of reco files using native `AddFriend`
* Fix GenFit 02-03-00 compatibility: replace removed `genfit::BellField` with `ShipBellField`; explicitly parse genfit2 headers for 26.03 stack
* Fix generator Python bindings by removing `//!` directives from public method declarations
* Fix `MuonBackGenerator` off-by-one at last event; gracefully stop via `gMC->StopRun()` instead of FairRoot's `exit(0)`
* Fix `MuonBackGenerator` to support both TClonesArray and std::vector input formats
* Fix duplicate `SHiP::Detector<vetoPoint>` rootmap entry warning
* Fix TStreamerInfo warnings for `SHiP::Detector` instantiations, generators, and ISTLPointContainer
* Fix uninitialised `fDetPoints` pointer in `SHiP::Detector` base class
* Fix NaN mass/energy for photons in ShipMCTrack due to floating-point rounding (#384)
* Move TimeDetHit v_drift and par[] to static constexpr, saving 40 bytes per serialised hit (#685)
* Fix digitisation crash when optional detector branches are missing (#738)
* Fix splitcalHit dropping MC point arrival time in digitisation (#925)
* Fix argparse -f/subparser conflict in run_simScript.py (#1044)
* Fix duplicated events in digitisation output (#1028)
* Fix file-filtering logic to support STL branches
* Fix `SetPhiRandom` to `SetPhiRandomize` in run_simScript.py
* Clamp random seed to PYTHIA8's maximum allowed value (900000000)
* Set correct trackIDs for exitHadronAbsorber class
* Disable multi-threading explicitly, as it is not supported in FairShip
* Fix pickle serialisation file modes in ShipGeoConfig (text to binary)
* Fix type annotations for physics quantities from int to float
* Fix null dereferences in ShipFieldMaker, FairShipFields, and FixedTargetGenerator
* Fix uninitialised members in vetoHit, strawtubesHit, ShipMuonShield; change flag from Float_t to Bool_t
* Fix off-by-one in FixedTargetGenerator target node access
* Fix `errorSummary`/`reportError` logging issues in rootUtils
* Fix closure variable binding bug in event display toggle callbacks
* Fix unclosed file handles in readDecayTable, pythia8_conf, and pythia8darkphoton_conf
* Fix mutable default arguments in `rootUtils.readHists()` and `geomGeant4.printWeightsandFields()`

### Removed

* Remove g4Ex scripts
* Remove old (CDR) target configuration; Jun25 is now the only supported target
* Remove unused ShipStyle, run_simEcal.py, and flux_map.py
* Remove unused functions and dead code from rootUtils
* Remove unused rootUtils imports from `dumpEvent.py` and `extractMuonsAndUpdateWeight.py`
* Remove TDirectory pythonisation backport (now provided by ROOT >= 6.32)
* Remove unused legacy ShipGeo.py and create_field_perturbation.py
* Remove SND@LHC leftover code from event display (#900)
* New_HA_Design and warm_opt muon shield configurations no longer supported

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
* Add SST frame option (4 = Aluminium, 10 = steel [default])
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
* Store channel coordinates in the digi containers to avoid reading geofile

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

* Add prototype of a new analysis toolkit in the `experimental` package.
* Add a simple analysis example script in the `examples/` directory.

### Changed

* Update cavern dimensions, including TCC8 and ECN3, and add a step in ECN3. The absorber coat has been removed, and the dimensions of the HA and absorber have been modified. For further details, see the presentation [here](https://indico.cern.ch/event/1507466/contributions/6345273/attachments/3003438/5293503/Quick%20Update%20on%20FAIRSHIP%20geometry-1.pdf).
* Set the decay volume medium to helium by default, with an option to switch to vacuum using the `--vacuums` flag.
* The medium of the SST boxes now matches the decay volume medium.
* Disable track pruning (see #533).
* Accommodate generic N-body LLP decays in the EventCalc interface.

### Fixed

* Use `ConstructedAt` and `std::swap` to replace removed pythonization for `TClonesArray`.
* Correct B_z octant symmetry for field maps.
* Correct time-of-flight calculation in `GenieGenerator.cxx` by using correct units.
* Ensure Genfit measurements provide the correct detector ID.
* Fix `TEvePointSetPrintOut`.
* Fix drawing of Monte Carlo and geometry tracks in the event display.
* Replace outdated `AddressOf` ROOT function with `addressof` in the `field/` directory.

### Removed

* Remove Millepede.
* Remove the outdated `shipEvent_ex.py` example.
* Remove the ALPACA generator.

## 24.11

This release follows the first round of breaking changes and is tagged for the launch of background simulations. It requires a CVMFS release of 24.10 or later.

### Added

* Introduce the EventCalc LLP event generator, a decay event sampler for inclusive final states. For further details, consult the dedicated presentation at the 30th SHiP CM [here](https://indico.cern.ch/event/1448055/contributions/6142341/attachments/2939894/5165450/SHiP_collaboration_meeting_talk_MFerrillo.pdf). See also #528.
* Add a conversion script, `FairShip/macro/convertEvtCalc.py`, to convert EventCalc's output kinematics to a format compatible with the simulation script.

### Changed

* Migrate `shipStrawTracking` to use `argparse`.
* Update CMake to use an external `genfit2`.
* Ensure `shipStrawTracking`, `shipDigiReco`, and `shipVertex` are compatible with the current version of `genfit`.

### Fixed

* Add missing includes in `ecalMatch` and `ecalReco`.
* Fix compilation warnings for unused or uninitialized variables (see #481).

### Removed

* Remove obsolete renaming scripts.
* Remove the `online` directory. For respective versions, see the `charmdet` and `muflux` branches.
* Remove the `charmdet` directory. For the latest version, see the `charmdet` branch.
* Remove the preshower and CaloDesign 1 (TP+Preshower).
* Remove the bundled `genfit`.
* Remove the conditions database.

## 24.10 - Freiburg

This release prepares for breaking changes and is the last to include charm cross-section measurement code and obsolete detector configurations.

### Added

* Add an option for a helium-filled decay volume.
* Add a pre-commit configuration to improve code quality and identify issues early.
* Add a `CHANGELOG.md` file.
* Add a `.git-blame-ignore-revs` file to ignore automatic reformatting in git blame.
* Add automatically built documentation using Doxygen.
* Add a `CODEOWNERS` file to automate review requests.
* Add separate configuration files for vacuum and helium in the decay vessel.
* Add an option to enable or disable the SND.

### Changed

* Update the `getGeoInformation` command-line interface.
* Update SST geometry constants (see #483).
* Use the same `clang-format` and `clang-tidy` configurations as FairRoot.
* Import the decay vessel configuration from a YAML file.
* Update the decay vessel geometry to the new design.
* Increase the minimum required CMake version to 3.12.
* Use FairRoot's `find_package2` to find ROOT, VMC, and fmt.
* Increase the minimum required ROOT version to 6.26.
* Use `find_package` to find Boost.
* Set the FairLogger dependency instead of using manual includes.

### Fixed

* Remove trailing whitespace and fix line endings.
* Fix compilation warnings from deprecations (see #469).
* Fix an issue with SST parameters (see #489).
* Clean up the Veto implementation.
* Fix a crash in the event display and PID when the entrance lid is missing.
* Ensure the `ShipReco.py` output file is closed correctly.
* Remove an unused argument for `MuDISGenerator::SetPositions`.

### Removed

* Remove obsolete installation and testing files.
* Remove uses of `future` and `past` modules (see #473).
* Remove the Geant3 dependency.
* Remove unimplemented event display functions (see #497).
* Disable the SND by default.
* Remove CMake commands no longer provided by FairRoot 19.
* Remove old CMake files for ROOT 5.
* Remove an old, outdated tracking script.
