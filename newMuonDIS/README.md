<!--
SPDX-License-Identifier: LGPL-3.0-or-later
SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration
-->

# Muon DIS simulation
## Introduction

This folder contains the necessary processors to create DIS events from input muons, and the generator to replay the created daughters with Geant4.

- Input: root files with cbmsim tree with muons from FairShip Particle Gun or MuonBack generators.
  - assumes muons are available at a z position before the last interaction length of the muon shield, will use the very first MCTrack found.
  - To do still: process several muons from the same "event" = pot interaction.
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
  - the weight wDIS does not include the cross section, this will be provided for analysis by an external tool. It is defined as (muon_initial_weight * density * length / number_of_DIS_events_per_input)
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
input muon (also saved in a separate branch). To find the correct
cross section for having a realistic physics weight, one should use
the muon momentum used per DIS interaction, saved as well in a
separate branch.

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
| `muDIS_xsec` | `Double_t` | Always `-1` until the input cross sections are reliable. |
| `muDIS_pPythia` | `Double_t` | Beam momentum from `muon_pPythia_<material>`, in GeV/c. |
| `muDIS_nGenerated` | `std::vector<Int_t>` | Actual counts before filtering from `muon_nDISGenerated_<material>`, in `MatTypeStr` order: MS, UBT, SBTsens, SBTfr, SSTsens, SSTfr, HE, AIR, HeBalloon, REST. `-1` means not crossed; `0` means crossed but no interactions generated. |

`GetMaterial()` still exposes the enum value after a successful `ReadEvent()`.

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

Each output muon has `muon_path_length`, the sum of the path intervals used
for DIS vertex sampling, excluding `REST`, and `muon_path_length_<MatType>`
branches for `MS`, `UBT`, `SBTsens`, `SBTfr`, `SSTsens`, `SSTfr`, `HE`, `AIR`,
`HeBalloon`, and `REST`. These
lengths are in cm and exclude transverse POCA jumps. The MS length uses only
the last 20 cm in accumulated z (or the full MS path if shorter), converted
to trajectory length, matching the vertex sampling and DIS weight interval.
The full REST length is saved separately in `muon_path_length_REST`.

`HeBalloon` groups the helium balloon liner walls and both lids. In the veto
geometry these are the skin of the `HeBalloon` volume around `decay_medium`;
the helium gas remains in `HE`. The liner has its own DIS branches and filter
histograms. `REST` remains the last category and is excluded from DIS generation.

## DIS events settings

`prepareEvents.py --seed INTEGER` seeds both Pythia6 and ROOT. Seeds wrap into
[1, 899999999]; without this option a nanosecond-resolution time seed is used.
The effective seed is logged. `--check-all-volumes` enables the optional inclusive
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
- branch `muon_nDISevt_<VOL>`: number of DIS interactions stored for each volume; after filtering, this is the number of surviving interactions.
- branch `muon_nDISGenerated_<VOL>`: actual number of generated interactions before filtering, copied unchanged by the filter (including repeated filtering). `-1` means the muon never crossed the material; `0` means it crossed but no interactions were generated (including REST, where generation is disabled).
- branch `muon_pPythia_<VOL>`: scalar beam momentum passed to Pythia6 in GeV/c, taken from the first path slice in that material. Set to `-1` when Pythia is not initialized for that material.
- vector branches mudis_*: DIS events information for each material. The vector size is variable and is determined by the actual per-entry `muon_nDISevt_<VOL>` count.
- branches mudis_DISproducts_* : all DIS daughters in each material <VOL>, with all DIS events stored together. Use `mudis_nDISdaughters_<VOL>` to determine the actual daughter ranges per DIS event.

The filter preserves both generation metadata values for every material,
even when none of that material's DIS events survive.
