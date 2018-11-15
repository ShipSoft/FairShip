# Simulation for Charm cross section and Muon flux measurements

# Geometry classes
This folder contains the geometry classes for the detectors used in charm cross section and Muon flux measurements.

Classes currently used by charm simulation:

* Box class: Emulsion Target 
* Spectrometer class: Pixel and SciFi detectors
* MufluxSpectrometer class: Goliath structure and Drift Tubes T3 and T4  
* MuonTagger class: RPCs for muon identification  


Classes currently used by muonflux simulation:  

* MufluxSpectrometer class  
* MuonTagger class  
* Scintillator class  
* ReProcessAbsorber  

Point classes are used for True MonteCarlo simulations, Hit class when present are used for digitization and reconstruction (used for MuonFlux measurement, still absent for Charm cross section)  

# Simulations for charm cross section measurement  
In general: 
 option --CharmdetSetup 1 activates charm cross section geometry  
        --CharmdetSetup 0 activates muon flux geometry  
Only the most useful options have been explained here, for the complete list of available options refer to the related script

Charm production simulations is done from macro/run_simScript.py. Example of syntax:  
 python $FAIRSHIP/macro/run_simScript.py --charm 1 -A charmonly --CharmdetSetup 1 -f Cascadefile -n 1000 -o outputfolder

 useful options:  
 --charm 1 : activates charmdet configuration instead of SHiP standard (both for charm cross section and muon flux measurements)  
 -A charmonly : activates charm production simulation  
 -f : input file with charm vertices (if on lxplus, will be taken directly from /eos/ship/data/Charm/Cascade-parp16-MSTP82-1-MSEL4-978Bpot.root)  
 -n : number of events  
 -o : output of folder where geometry and output of simulation will be saved  

General POT simulations are done from muonShieldOptimization/run_MufluxfixedTarget.py. Example of syntax:  
 
 python $FAIRSHIP/muonShieldOptimization/run_MufluxfixedTarget.py --CharmdetSetup 1 -G -e 0.001 -n 1000 -o outputfolder  
 
 It is a derivation of the FixedTarget simulation used in SHiP, applied to charmdet geometry.  
 useful options:  
  -e : Energy cut for adding tracks to Geant4 propagation (choosing a high cut allows to save memory for larger simulations)  
  -n : Number of events  
  -o : output of folder where geometry and output of simulation will be saved  
  -r : number of run (can be used as folder naming if -o option is not used)  
  -f : force overwriting of directory (DANGEROUS: if used in a wrong directory, it will delete it. DO NOT USE IT together with -o option)  


 different options for proton generation:  
  -V : default one, proton interactions generated with Pythia and EvtGen is used for decays  
  -P : both proton interactions and decays handled with Pythia  
  -G : most basic simulation: one 400 GeV proton directly sent to Geant4  
  
  Details can be found here: https://cds.cern.ch/record/2280572?ln=it  
  All simulations then use Geant4 for propagation.  
  IMPORTANT: Both -V and -P generate all interactions in target. Due to small dimensions of target used in charmdet measurement, many protons pass through without interacting. To correctly simulate surviving protons and their tracks in detectors, use -G option  

For any question or doubt about these simulations, contact Thomas Ruf (thomas.ruf@cern.ch) or Antonio Iuliano (antonio.iuliano@cern.ch)  

# Simulations for muon flux measurements  


# Checking geometry output  
Event display can be launched in the following way:  
 python -i $FAIRSHIP/macro/eventDisplay.py -f simulationfile.root -g geofile.root  
  
 (actual names of simulationfile.root and geofile.root depend on the launched simulation)  

Positions and dimensions of volumes can be checked in the following way:  
 python $FAIRSHIP/macro/getGeoInformation.py -g geofile.root  
 
 useful options:  
 -v : name of the volume to expand (see list of volume daughters)  
 -l : 'depth' level of the subnode expansion (how many daughters are showed)  
