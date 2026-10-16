<!--
SPDX-License-Identifier: LGPL-3.0-or-later
SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration
-->

# Muon DIS simulation
## Introduction

This folder contains the necessary processors to create DIS events from input muons, and the generator to replay the created daughters with Geant4.

- Input: root files with cbmsim tree with muons from FairShip Particle Gun or MuonBack generators.
  - assumes muons are available at a z position before the last interaction length of the muon shield.
  - `--muon-selection` chooses the muon tracks of each input event, see [Selecting the input muons](#selecting-the-input-muons). By default this is `MCTrack[0]` for particle-gun input and every muon with detector hits for muon background replays, which can have several muons per event.
- Output: tree "MuonDIS" with the initial muon information, hits in veto detectors, SST and TD, soft particles emitted by the muon along its initial path, and daughters from DIS events in several volumes with random vertex positions within each volume, and associated probability weight.
  - Soft tracks are for all processes except destructive "Muon nuclear interaction". The first one is the initial input muon.
  - UBT, SBT, SST and TD hits are all hits with a GetTrackID() equal to the input muon track ID.
  - The separate volumes are:
    - muon shield "MS"
    - UBT detector "UBT" (now just a dummy plane)
    - SBT detector "SBTsens" for liquid scintillator and "SBTfr" for frame material
    - SST detector "SSTsens" for the straw-tracker sensitive volume and "SSTfr" for frame material
    - Helium "HE"
    - Air "AIR" from before and after UBT, after balloon, cavern, SST
    - the He balloon liner "HeBalloon"
    - The rest "REST" anything not taken into account in the previous categories. No DIS events are made in REST.
    - to add material or change categories, edit top part of MuDISDefs.h file, and method GetLabel() in MuonPath.cxx
  - the weight wDIS does not include the cross section. It is defined as (muon_initial_weight * density * length / number_of_DIS_events_per_input), in g/cm². The replay output combines it with the stored cross section into `muDIS_weight` (see below).
- Replay: NewMuDISGenerator class, called from the main macro/run_simScript.py file with option NewMuDIS, and using a postprocessor file in python/MuDISGenerator_postProcessing.py script to add the initial muon hits back in the output, up to the disappearance of the muon track at DIS vertex.



## Quick recipe

```bash
cd FairShip
pixi run build
pixi shell
cd <your_workdir>
python3 <relative_path_to_FairShip>/FairShip/newMuonDIS/prepareEvents.py -f <your_sim_input_root_file.root> -o <your_output_root_file_name>.root -n <number_of_initial_p.o.t./muon_events_to_process> -d <number_of_DIS_per_muon_per_volume> -g <your_geometry_file.root>
python3 <path_to_FairShip>/newMuonDIS/filterEvents.py -f <your_output_root_file_name>.root -o selected.root -g <your_geometry_file.root>
python3 <path_to_FairShip>/macro/run_simScript.py -f selected.root --tag <your_tag> --NewMuDIS --debug 1 -n 10
```

For this generator, `-i/--firstEvent` (or `NewMuDISGenerator::Init`'s
`startEvent`) is a zero-based **muon entry** in the supplied `MuonDIS`
tree or chain. In filtered files this indexes the retained muons, not
their original entry numbers. All retained DIS interactions of that
muon and subsequent muons are available, in material order. `-n`
limits the number of input muon entries (`-n -1`: all remaining; `-n
0`: none), including muons with no DIS interactions.  If no -n or
--nEvents option is given, it will default to 100 DIS interactions, as
100 input muons could represent a very large number of DIS
interactions to process.  All DIS interactions of the selected muons
are simulated. In C++, call `SetNevents(nMuons)` before `Init` to
select this limit; `GetNevents()` returns the resulting number of DIS
interactions for the FairRoot event loop.  A start equal to the number
of muon entries gives zero events; negative starts and starts beyond
the end are rejected.

Replay uses each material's stored `muon_nDISevt_<VOL>` count and
`mudis_nDISdaughters_<VOL>` daughter ranges. Filtering updates both, so replay
does not need the original number of generated DIS interactions. After all
materials in one muon entry are exhausted, replay advances to the next muon.
Inconsistent vector lengths, negative counts, missing muon tracks and daughter
totals that disagree with the stored particles reject initialization. Replay
also validates each loaded muon before adding any tracks and returns `kFALSE`
on inconsistent input.

The weight of the MCTracks associated with the daughters, MCTrack.fW,
is the wDIS, i.e. input muon weight (also in MCTrack[0].fW) times
density times length, divided by number of DIS events generated per
input muon (also saved in a separate branch). The event weight
`muDIS_weight` multiplies it by the stored Pythia6 cross section; to
evaluate the cross section differently, use the muon momentum of each
DIS interaction, saved in `muDIS_pPythia`.

The main simulation macro selects this generator via `--NewMuDIS`
(`--MuDIS` there still selects the legacy generator):

```bash
python macro/run_simScript.py --NewMuDIS -f selected.root -i 0 -n 10 --tag dis
```

The simulation macro calls `RegisterOutputBranches(sink.GetOutTree())` after
`run.Init()` and before replay. Other drivers can use the same method; the
generator must outlive the output tree. Each simulated `cbmsim` event contains:

| Branch | Type | Meaning |
| --- | --- | --- |
| `muDIS_material` | `TString` | Material label of the replayed interaction; replaces `DISMaterial`, so analysis need not translate an enum from another software version. |
| `muDIS_muEntry` | `Int_t` | Zero-based input muon entry across the input chain, including the start offset. For filtered input this refers to the filtered tree. |
| `muDIS_disIndex` | `Int_t` | Zero-based DIS index within that muon's current material in the input tree (`fnmuDis` before advancement). |
| `muDIS_genIndex` | `Int_t` | Zero-based DIS index within that muon and material in the `prepareEvents.py` output, from `mudis_DISgenIndex_<material>`. Equal to `muDIS_disIndex` for unfiltered input; unchanged by filtering. `-1` for input written before this branch existed. |
| `muDIS_xsec` | `Double_t` | Pythia6 cross section for this muon, material and target nucleon, from `muon_xsecByTarget_<material>`, in mb per nucleon; see [Cross section and weight](#cross-section-and-weight). For input without that branch, the running estimate `muDIS_xsecEvent`, with a warning. |
| `muDIS_xsecEvent` | `Double_t` | Running estimate stored with the interaction (`mudis_DISxsec_<material>`), in mb. For reference only. |
| `muDIS_xsecAccepted`, `muDIS_xsecTried` | `Int_t` | Accepted and tried Pythia6 events behind `muDIS_xsec`, from `muon_xsecAccepted_<material>` and `muon_xsecTried_<material>`; `0` for input without them. |
| `muDIS_target` | `Int_t` | Pythia6 target nucleon from `mudis_DIStarget_<material>`: `1` proton, `0` neutron. |
| `muDIS_wDIS` | `Double_t` | `muon_wDIS_<material>`, the weight also stored on the DIS daughters, in g/cm². |
| `muDIS_weight` | `Double_t` | Event weight `muDIS_wDIS * muDIS_xsec * N_A * 1e-27`, see [Cross section and weight](#cross-section-and-weight). `-1` if the cross section is negative. |
| `muDIS_pPythia` | `Double_t` | Beam momentum from `muon_pPythia_<material>`, in GeV/c. |
| `muDIS_nGenerated` | `std::vector<Int_t>` | Actual counts before filtering from `muon_nDISGenerated_<material>`, in `MatTypeStr` order: MS, UBT, SBTsens, SBTfr, SSTsens, SSTfr, HE, AIR, HeBalloon, REST. `-1` means not crossed; `0` means crossed but no interactions generated. |
| `muDIS_srcFile`, `muDIS_srcEntry`, `muDIS_srcTrackID`, `muDIS_srcRunID`, `muDIS_srcEventID` | `Int_t`, `Long64_t`, `Int_t`, `Long64_t`, `Long64_t` | Origin of the muon, copied from the `muon_src*` branches, see [Provenance](#provenance). `-1` for input written before these branches existed. |
| `muDIS_potRunID`, `muDIS_potEventID` | `Long64_t` | `muon_potRunID` and `muon_potEventID`, see [Provenance](#provenance). |

`GetMaterial()` still exposes the enum value after a successful `ReadEvent()`.

### Cross section and weight

For an interaction in material `<VOL>`, `wDIS = w_mu * X / n`, with `w_mu` the
weight of the input muon (its `fW`, `muon_MCTracks[0]` in the output), `X` the
integral of the density over the sampled path in g/cm²
(`muon_path_length_<VOL>` times the densities crossed) and `n` the number of interactions generated for that muon in that
material before filtering (`muon_nDISGenerated_<VOL>`). Filtering keeps `wDIS`,
so the weights of the surviving interactions still refer to `n`.

Pythia6 is initialised again for every muon and material, and for the second,
neutron half of its interactions. Its cross-section estimate `PARI(1)` is a
running Monte Carlo estimate over the events generated since the last
initialisation, summed over the photon components of the `gamma/mu` beam.
`prepareEvents.py` stores two values:

- `mudis_DISxsec_<VOL>`: `PARI(1)` after each interaction. The first
  interactions of each half carry a poorly converged value. In a test with
  1000 interactions per muon and material, single values ranged from 0.03 to
  6.8 µb where the converged value was about 2 µb.
- `muon_xsecByTarget_<VOL>`: `PARI(1)` after the last interaction of each half,
  indexed by `muDIS_target` (0 neutron, 1 proton), with the number of
  accepted and tried events behind it in `muon_xsecAccepted_<VOL>` and
  `muon_xsecTried_<VOL>` (`NGEN(0,3)` and `NGEN(0,1)`, summed over the photon
  components). It is `-1` for a half without interactions.

`muDIS_xsec` is the second, the estimate after all `n/2` interactions on that
nucleon. Pythia6 gives no uncertainty for it. Its precision was measured by
comparing the materials of one muon, which share the beam momentum to within
5%: the relative spread of the per-material estimates was 35-60% for
`--nDIS 20` (10 interactions per nucleon), 2-7% for 200 and 1.3-3.2% for 1000,
about half of `1/sqrt(muon_xsecAccepted)`. Use the default `--nDIS 1000`, or
average the estimates over muons of similar momentum, when the cross section
matters.

These numbers describe the statistical precision of Pythia6's own estimate.
Whether Pythia6, with `MSEL=2` and the photon flux of the muon, gives the
physical muon-nucleon cross section has not been validated against an
independent calculation, and the proton and neutron values agree within their
precision.

Input written before `muon_xsecByTarget_<VOL>` existed falls back to the
running estimate of each interaction, and `NewMuDISGenerator` warns once.
Summed over all generated interactions of a material, the running estimates
average out (0.88 of the converged value for `--nDIS 20`, 0.99 for 1000), but
after filtering, the weight of a single interaction can be off by a large
factor.

The event weight is

    muDIS_weight = muDIS_wDIS * muDIS_xsec * N_A * 1e-27

with `N_A = TMath::Na()` per gram (nucleons per gram, neglecting the binding
energy) and `1e-27` cm² per mb. `X * sigma * N_A` is the probability that the
muon interacts in the sampled path, to first order in the interaction length,
and for a cross section per nucleon without nuclear effects. Half of the
interactions use a proton target and half a neutron target, independently of
the material's composition. `muDIS_weight` is dimensionless and already
contains `w_mu`: summed over selected events and divided by the number of
protons on target behind the muon sample, it gives the expected number of
selected interactions per proton on target.

## Provenance

Every stage records where its output comes from, so that an interaction can be
traced back to the input muon and grouped with the others sharing its history.

`prepareEvents.py` stores, for each muon:

| Branch | Type | Meaning |
| --- | --- | --- |
| `muon_srcFile` | `Int_t` | Index of the input file in the `FileSummary` key `inputFiles`, in the order the input chain was built (input directories are searched in sorted order). |
| `muon_srcEntry` | `Long64_t` | Entry of the muon's event in that file's `cbmsim` tree. |
| `muon_srcTrackID` | `Int_t` | Index of the muon in that event's `MCTrack` (`0` for particle-gun input). Muons selected from one input event share all other `muon_src*` and `muon_pot*` values. |
| `muon_srcRunID`, `muon_srcEventID` | `Long64_t` | `RunID` and `EventID` of that event's `MCEventHeader`, or `-1` if the input has none. These identify the event of the simulation that produced the input muon (e.g. the muon background simulation), not a proton on target. |
| `muon_potRunID`, `muon_potEventID` | `Long64_t` | `muBack_srcRunID` and `muBack_srcEventID` of that event, or `-1` if the input has none. `run_simScript.py --MuonBack` writes these: the `MCEventHeader` `RunID` and `EventID` of the event `MuonBackGenerator` read. When that input is the output of `run_fixedTarget.py` in its default (minimum-bias) or `--G4only` mode, which simulate one proton per event, they identify the proton on target. In `--charm` and `--beauty` runs an event is one heavy-flavour production event read from a cascade file and normalised through cross-section ratios, so it does not stand for one proton. Inputs in the `pythia8-Geant4` ntuple format carry no event identity, so they give `-1`. |

and, for each DIS interaction, `mudis_DISgenIndex_<VOL>`, its position in the
`prepareEvents.py` output. `filterEvents.py` copies all of these unchanged, and
`NewMuDISGenerator` writes them to each simulated event (see the table above).
Interactions with equal `(muon_srcFile, muon_srcEntry, muon_srcTrackID)` in one
`prepareEvents.py` output come from the same input muon and are alternatives of
each other. Across outputs, compare `inputFiles[muon_srcFile]` and
`muon_srcEntry`, or `(muon_srcRunID, muon_srcEventID, muon_srcTrackID)` if the
run IDs of the input production are unique. Muons with equal
`(muon_potRunID, muon_potEventID)` come from the same proton on target.

Each stage writes a `FileSummary`: a JSON `TString` with the merged `PoT`,
`EnergyCut` and `prodSite` of its inputs, `inputFiles`, and the summaries of the
inputs themselves in `inputFileSummaries`, so the whole chain is kept in the
final file. `PoT` refers to the input files as a whole, also when only part of
their entries was processed. In addition:

- `prepareEvents.py`: `stage`, the random `seed` actually used and whether it
  was taken from the time (`seedFromTime`), `nDIS`, `minPythiaP`, the number of
  `inputEntries`, the `entryRange` processed (first, end), `muonsWritten`,
  `zMin`, `zMax`, `geoFile`, `muonShieldFieldMap`, `pocaJumpThreshold` and the
  software `versions`.
- `filterEvents.py`: `stage`, `inputEntries`, `entryRange`, `muonsWritten`, the
  filter options, the field maps, the Pythia8 decay seed actually used
  (`pythiaDecaySeed`, `null` without `--pythia-decays`) and `versions`.
- `run_simScript.py`: its `seed`, `firstEvent` and `nEvents` (for `--NewMuDIS`,
  the number of DIS interactions replayed).

The simulation macro calls `python/MuDISGenerator_postProcessing.py` after simulation.
It appends the original muon's UBT, SBT, SST and TD points to each event's
corresponding detector branches, retaining only points with `GetZ() < DISvz`.
Points at the DIS vertex or downstream are excluded. Copied points refer to
`MCTrack[0]` (the incoming muon) and the new event ID; simulated points and file
metadata are preserved.
The helper matches the generator's input order, material counts and starting
muon entry, including filtered inputs and runs ending partway through a muon.
For every output event it checks that `muDIS_muEntry`, `muDIS_material` and
`muDIS_disIndex` match the interaction it is about to use, and stops with an
error, leaving the output unchanged, if they differ.
It must run before any output event skimming or reordering.

## Overview of classes:


- prepareEvents.py: python macro with argument parameters to pass to the main processor.
- filterEvents.py: filter prepared DIS interactions; see [README.filter.md](README.filter.md) for selection and histogram details.
- class MuDISProcessor: main processor, reading input and creating output, and calling the others.
- class MuGeoProcessor: class defining the interface with the geometry. A map of objects of type "MuonPath" is filled, for each input muons, with the specific volumes traversed by the muon. This info will be used to generate vertices for DIS in each specific material, separately, and associate a random vertex position within each of these volumes.
- class MuonPath: to go along the input muon trajectory, and distribute the path along the list of separate materials defined in MuDISDefs.h. Shield paths use UBT backward extrapolation or magnetic transport; downstream paths use POCAs between detector measurements.
- class DISparticle: DIS particle pid and 4-vector momentum.
- header file MuDISDefs.h: all helper classes and struct being used.
- class MuDISFilter: filter events using an extrapolation of the charged daughters, with B field effects, up to the TD.
- class NewMuDISGenerator: FairGenerator to read again the MuonDIS tree and process particles again through Geant4 to give cbmsim tree.


## Selecting the input muons

`prepareEvents.py --muon-selection` (`MuDISProcessor::SetMuonSelection` in
C++) chooses which tracks of each input `cbmsim` event are processed:

- `first`: `MCTrack[0]`, which must be a muon; otherwise the event is skipped
  with a warning. This is the particle-gun case.
- `hits`: every muon track (`|PDG| = 13`) with at least one UBT, SBT, SST or
  TD point, the detectors the path is anchored on. This is for muon
  background replays (`run_simScript.py --MuonBack`), where `MCTrack[0]` is
  the primary proton or the muon's parent and an event can hold several
  muons, including secondary muons from decays in flight.
- `all`: every muon track, also those without any of these points. Their path
  is extrapolated from the start of the track only, and there can be many of
  them.
- `auto` (default): `first` if `MCTrack[0]` is a muon, `hits` otherwise.
  Particle-gun input is processed as before.

The legacy chain (`muonDIS/make_nTuple_SBT.py`) takes every muon with an SBT
point above 3 GeV. Here the momentum cut is the Pythia6 minimum (2 GeV/c at
the start of the track), applied to every selected muon.

Each selected muon becomes one entry of the output tree, with its own soft
tracks and hits, and `muon_MCTracks[0]` is that muon. `-n` still counts input
events. The muons of one event share `muon_srcFile`, `muon_srcEntry`,
`muon_srcRunID`, `muon_srcEventID` and the `muon_pot*` IDs, and differ in
`muon_srcTrackID`; `run_simScript.py --NewMuDIS` writes the same values as
`muDIS_*`. The muons of one input event, and through the `muon_pot*` IDs those
of one proton on target, can therefore be grouped, for example for the
uncertainty of the background estimate.

## Path to volumes

Path discovery uses the MC start and the first recorded muon hit in UBT,
SBT, each of Tr1--Tr4, and TD. Available hits are ordered in z. A non-forward
(`pz <= 0`) selected measurement rejects the muon.

- A muon with a UBT hit always starts at UBT, independently of the MC start
  position or magnet shapes. It is traced backwards along the UBT direction
  through material, stopping after 20 cm of accumulated MS z, excluding gaps,
  or at the shield entrance. These slices use the UBT momentum and time and
  are stored in increasing z. The forward path starts at UBT and uses POCAs
  with subsequent detector hits. Backward lines that miss MS are counted
  separately in the diagnostic summary; their start and UBT measurements
  are logged at `debug` level.
- Without UBT, a start in a field-free region is extrapolated linearly.
  If it enters a nonzero field region, propagation continues with magnetic
  bending. Classification uses the interpolated field at the start position.
- Without UBT, a start in field is propagated magnetically until it leaves
  the field, then linearly, with bending resumed on any later field entry.
  The propagated trajectory, including fringes and its straight continuation,
  determines the POCA with the first SBT, SST or TD hit. The detector line
  takes over at that POCA, which can also lie inside the field. Magnetic
  transport models bending, without energy loss or scattering. Turning or
  unconverged trajectories are rejected.

`prepareEvents.py` loads the shield map from the geometry's `shieldName`
and `muShield.Entrance[0]`. Explicit maps can be supplied with
`--muon-shield-field-map` and `--muon-shield-field-z`. C++ callers configure
`MuDISProcessor::SetMuonShieldField(map, geometry)` (or the same method on
`MuGeoProcessor`) and retain ownership of both objects. A missing map is an
error for a muon without UBT in a geometry containing shield magnets, since
the field cannot be inferred from material shapes. Geometries with
`muShield.WithConstField` are refused, as the simulation then does not use the
map. Muons starting upstream of `--z_min` (default 2500 cm) are only counted in
the end-of-run summary; their paths are built as described above.

Only magnet volumes inside `MuonShieldArea` contribute to MS. Magnetic
trajectories are navigated as chords refined to a 0.0001 cm interpolation
deviation tolerance; geometry navigation and DIS vertex sampling use the same chords.
POCAs between measurements set switching z planes; each line remains anchored
to its own position, momentum and time. Times before a reference measurement
are extrapolated backwards. DIS vertices are sampled uniformly in path length.
MS sampling uses at most the last 20 cm of accumulated material z, excluding
gaps, converted to actual trajectory length.

Transverse gaps at the switching planes are excluded from the path length.
The diagnostic summary counts the routes prepared during initialization:
UBT backward extrapolation, an MC start in field, and an MC start in a
field-free region (which can subsequently enter field). These are mutually exclusive
counts per initialized muon, before material navigation; failed magnetic
transport remains in the rejected-muon count. Starts at or beyond the maximum
z are counted separately as skipped. All counts reset for each processing run.
At the end of processing, `LOG(info)` reports rejected muons, the number of
switches and muons with a transverse gap above the configured threshold, and
the largest gap. Set the threshold with `--poca-jump-threshold <cm>` in
`prepareEvents.py`, or `MuDISProcessor::SetPocaJumpThreshold(cm)` in C++.
The default is 1 cm, and a gap equal to the threshold is not counted.

The end-of-run summary also reports sums of the muon weight `fW` (via
`GetWeight()`) for the muon counters, including geometry routes, rejections,
and muons with large POCA jumps. Each muon contributes its weight once to
each applicable count, independent of the number of generated DIS events.
Charge counts use the existing momentum cut; the no-hit count is diagnostic
and does not reject the muon. The weighted skipped-path count includes
muons with invalid or empty paths. Unreadable entries, missing tracks and
non-muon entries in the general skipped-event count have no corresponding
muon weight and are not included in that weighted count.

Each output muon has `muon_path_length`, the sum of the path intervals used
for DIS vertex sampling, excluding `REST`, and `muon_path_length_<MatType>`
branches for `MS`, `UBT`, `SBTsens`, `SBTfr`, `SSTsens`, `SSTfr`, `HE`, `AIR`,
`HeBalloon`, and `REST`. These
lengths are in cm and exclude transverse POCA jumps. The MS length uses only
the last 20 cm in accumulated z (or the full MS path if shorter), converted
to trajectory length, matching the vertex sampling and DIS weight interval.
The full REST length is saved separately in `muon_path_length_REST`.

The end-of-run `Muon path totals` lines accumulate these same lengths,
once per output muon, independently of the number of DIS interactions.
Each category (including `REST`) reports `sum(L)` and `sum(fW*L)` in cm,
plus the count and `sum(fW)` of crossing muons (positive path length).
The overall line excludes `REST` from the lengths and counts all output
muons, including those with zero total DIS path length. Totals reset each run
and are printed with 17 significant digits for combining jobs.

Sum the printed quantities across jobs before dividing: use `sum(L)` divided
by the crossing count for a conditional mean, or `sum(fW*L) / sum(fW)` for
its MC-weighted counterpart. For means over all output muons, including
zero lengths, use the overall line's count or weight sum as the denominator.
A weighted mean is undefined when its weight sum is zero. These are DIS
material categories, not individual geometry material names; the MS total
uses the restricted sampling interval, not the full shield trajectory.

`HeBalloon` groups the helium balloon liner walls and both lids. In the veto
geometry these are the skin of the `HeBalloon` volume around `decay_medium`;
the helium gas remains in `HE`. The liner has its own DIS branches and filter
histograms. `REST` remains the last category and is excluded from DIS generation.

## DIS events settings

`prepareEvents.py --seed INTEGER` seeds both Pythia6 and ROOT. Seeds wrap into
[1, 899999999]; without this option a nanosecond-resolution time seed is used.
The effective seed is logged and stored in the output `FileSummary` (`seed`,
with `seedFromTime` true if it came from the time), so any output can be
reproduced with `--seed`. `--check-all-volumes` enables the optional inclusive
geometry scan (also available as `MuDISProcessor::CheckAllVolumes()`).

- Pythia6 initialised with
  ```bash
  //set process 1=QCD, 2=DY/others
  fPythia->SetMSEL(2);
  //set min hard scale: 2 GeV --->try 1.5 for soft muons ?
  fPythia->SetPARP(2, 2);
  ```

- first nDIS/2 events are with proton target, second half with neutron target.
  - To do: understand why no difference between p and n target at the moment.

- The muon momentum used in the initialisation of the Pythia6 muon
  beam is approximated at the value found for the first slice of the
  muon path found in the given material. This means that for example
  for the muon shield, the value will be overestimated when reaching
  the end of the magnet if its start position is much further upstream
  and the muon would have lost energy in the iron before the DIS takes
  place. This effect can be estimated offline by varying the cross
  section using the two closest momentum values recorded for the event
  (e.g. start and UBT for the MS).

## Structure of output tree:

- branches muon_* : input muon information. Size: number of entries processed.
- branches `muon_srcFile`, `muon_srcEntry`, `muon_srcTrackID`, `muon_srcRunID`, `muon_srcEventID`, `muon_potRunID`, `muon_potEventID`: origin of the muon, see [Provenance](#provenance).
- branch `mudis_DISgenIndex_<VOL>`: position of each interaction in the `prepareEvents.py` output, kept by the filter.
- branch `muon_nDISevt_<VOL>`: number of DIS interactions stored for each volume; after filtering, this is the number of surviving interactions.
- branch `muon_nDISGenerated_<VOL>`: actual number of generated interactions before filtering, copied unchanged by the filter (including repeated filtering). `-1` means the muon never crossed the material; `0` means it crossed but no interactions were generated (including REST, where generation is disabled).
- branch `muon_pPythia_<VOL>`: scalar beam momentum passed to Pythia6 in GeV/c, taken from the first path slice in that material. Set to `-1` when Pythia is not initialized for that material.
- branches `muon_xsecByTarget_<VOL>[2]`, `muon_xsecAccepted_<VOL>[2]` and `muon_xsecTried_<VOL>[2]`: Pythia6 cross section in mb after all interactions on the neutron (index 0) and the proton (index 1), and the accepted and tried events behind it; see [Cross section and weight](#cross-section-and-weight). Copied by the filter.
- vector branches mudis_*: DIS events information for each material. The vector size is variable and is determined by the actual per-entry `muon_nDISevt_<VOL>` count.
- branches mudis_DISproducts_* : all DIS daughters in each material <VOL>, with all DIS events stored together. Use `mudis_nDISdaughters_<VOL>` to determine the actual daughter ranges per DIS event.

The filter preserves both generation metadata values for every material,
even when none of that material's DIS events survive.
