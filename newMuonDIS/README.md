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
- Output: tree "MuonDIS" with the initial muon information, hits in veto detectors and SST, soft particles emitted by the muon along its initial path, and daughters from DIS events in several volumes with random vertex positions within each volume, and associated probability weight.
  - Soft tracks are for all processes except destructive "Muon nuclear interaction". The first one is the initial input muon.
  - UBT, SBT, SST and TD hits are all hits with a GetTrackID() equal to the input muon track ID. Older inputs without TD branches are supported.
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
`startEvent`) is a zero-based **muon entry** in the supplied `MuonDIS` tree
or chain. In filtered files this indexes the retained muons, not their original
entry numbers. All retained DIS interactions of that muon and subsequent muons
are available, in material order. `-n` limits the number of input muon entries
(`-n -1`: all remaining; `-n 0`: none), including muons with no DIS interactions.
All DIS interactions of the selected muons are simulated. In C++, call
`SetNevents(nMuons)` before `Init` to select this limit; `GetNevents()` returns
the resulting number of DIS interactions for the FairRoot event loop.
A start equal to the number of muon entries gives zero events; negative starts
and starts beyond the end are rejected.

Replay uses each material's stored `muon_nDISevt_<VOL>` count and
`mudis_nDISdaughters_<VOL>` daughter ranges. Filtering updates both, so replay
does not need the original number of generated DIS interactions. After all
materials in one muon entry are exhausted, replay advances to the next muon.
Inconsistent vector lengths, negative counts, missing muon tracks and daughter
totals that disagree with the stored particles reject initialization. Replay
also validates each loaded muon before adding any tracks and returns `kFALSE`
on inconsistent input.

The main simulation macro selects this generator via `--NewMuDIS`
(`--MuDIS` there still selects the legacy generator):

```bash
python macro/run_simScript.py --NewMuDIS -f selected.root -i 0 -n 10 --tag dis
```

The simulation macro calls `python/MuDISGenerator_postProcessing.py` after simulation.
It appends the original muon's UBT, SBT, SST and TD points to each event's
corresponding detector branches, retaining only points with `GetZ() < DISvz`.
Points at the DIS vertex or downstream are excluded. Copied points refer to
`MCTrack[0]` (the incoming muon) and the new event ID; simulated points and file
metadata are preserved. Older input files without TD points are supported.
The helper matches the generator's input order, material counts and starting
muon entry, including filtered inputs and runs ending partway through a muon.
It must run before any output event skimming or reordering.

## Overview of classes:


- prepareEvents.py: python macro with argument parameters to pass to the main processor.
- filterEvents.py: filter prepared DIS interactions; see [README.filter.md](README.filter.md) for selection, histogram and plotting details.
- class MuDISProcessor: main processor, reading input and creating output, and calling the others.
- class MuGeoProcessor: class defining the interface with the geometry. A map of objects of type "MuonPath" is filled, for each input muons, with the specific volumes traversed by the muon. This info will be used to generate vertices for DIS in each specific material, separately, and associate a random vertex position within each of these volumes.
- class MuonPath: to go along the input muon trajectory, and distribute the path along the list of separate materials defined in MuDISDefs.h. The linear extrapolation hypothesis using points-of-closest-approaches between available hit measurements has been checked against propagation in magnetic field, and found to be a good approximation.
- class DISparticle: DIS particle pid and 4-vector momentum.
- header file MuDISDefs.h: all helper classes and struct being used.
- class MuDISFilter: filter events using an extrapolation of the charged daughters, with B field effects, up to the TD.
- class NewMuDISGenerator: FairGenerator to read again the MuonDIS tree and process particles again through Geant4 to give cbmsim tree.


## Path to volumes

The path uses the MC start and the first recorded muon hit in UBT, SBT,
each of Tr1--Tr4, and TD, omitting missing measurements. The available hits
are ordered in z. A non-forward (`pz <= 0`) selected measurement rejects the
muon. POCAs between adjacent measurements set the z planes at which the
momentum direction changes; each segment remains anchored to its own measured
position, momentum and time. Geometry navigation and DIS vertex positions use
these same straight segments. Times before a reference measurement are
extrapolated backwards. DIS vertices are sampled uniformly in segment length,
using a cached cumulative length and binary search. The existing shield
restriction to the last 20 cm in accumulated z is retained.

Transverse gaps at the switching planes are excluded from the path length.
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


## Structure of output tree:

- branches muon_* : input muon information. Size: number of entries processed.
- branches muon_nDISevt_* : number of DIS interactions generated for each volume. Should be input parameter nDIS, but real number generated (in case some Pythia6 evt fail). Size: number of entries processed.
- branches mudis_*: DIS events information for each material. The vector size is variable and is determined by the actual per-entry `muon_nDISevt_<VOL>` count.
- branches mudis_DISproducts_* : all DIS daughters in each material <VOL>, with all DIS events stored together. Use `mudis_nDISdaughters_<VOL>` to determine the actual daughter ranges per DIS event.
