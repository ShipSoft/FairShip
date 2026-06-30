# Muon DIS simulation
## Introduction

This folder contains the necessary processors to create DIS events from input muons.

- Input: root files with cbmsim tree with muons from FairShip Particle Gun or MuonBack generators.
  - assumes muons are available at about the z position of the last interaction length of the muon shield.
  - To do 1: provide this position from MuonBack generator.
  - To do 2: process several muons from the same "event" = pot interaction.
- Output: tree "MuonDIS" with the initial muon information, hits in veto detectors and SST, soft particles emitted by the muon along its initial path, and daughters from DIS events in several volumes with random vertex positions within each volume, and associated probability weight.
  - Soft tracks are for all processes except destructive "Muon nuclear interaction". The first one is the initial input muon.
  - UBT, SBT and SST hits are all hits with a GetTrackID() equal to the input muon track ID.
  - The separate volumes are:
    - muon shied "MS"
    - UBT detector "UBT" (now just a dummy plane)
    - SBT detector "SBT"
      - to do: separate into different materials
    - SST straws and gas for tracker station 1 only
      - to do : add frame, not there in latest FairShip master as of Jun8th 2026
    - Helium "He"
    - Air "Air" from before and after UBT, after balloon, cavern, SST.
    - The rest "REST" anything not taken into account in the previous categories.


## Quick recipe

```bash
cd FairShip
pixi run build
pixi shell
cd <your_workdir>
python3 <relative_path_to_FairShip>/FairShip/muonDIS/prepareEvents.py -f <your_sim_input_root_file.root> -o <your_output_root_file_name>.root -n <number_of_initial_p.o.t./muon_events_to_process> -d <number_of_DIS_per_muon_per_volume> -g <your_geometry_file.root>
```

## Overview of classes:


- prepareEvents.py: python macro with argument parameters to pass to the main processor.
- class MuDISProcessor: main processor, reading input and creating output, and calling the others.
- class MuGeoProcessor: class defining the interface with the geometry. A map of objects of type "Path" is filled, for each input muons, with the specific volumes traversed by the muon. This info will be used to generate vertices for DIS in each specific material, separately, and associate a random vertex position within each of these volumes.
- class DISparticle: to define the output tree branch with DIS particle information, i.e.
- header file MuDISDefs.h: all helper classes and struct being used.



## Path to volumes

To do: to be improved by config instead of hardcoded.

## DIS events settings

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
- branches muon_nDISevt_* : number of DIS interactions generated for each volume. SHould be input parameter nDIS, but real number generated (in case some Pythia6 evt fail). Size: number of entries processed.
- branches mudis_*: DIS events information for each material. Size: nDIS*nEntries.
- branches mudis_DISproducts_* : all DIS daughters in each material <VOL>, DIS events put all together. Size = nEntries*nDIS*mudis_nDISdaughters_VOL.
