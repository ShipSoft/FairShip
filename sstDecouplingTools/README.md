### Geometry tuning

To set geometrical parameters from user json file run the macro with `--useJSON`

###

To run simulation with events from file `--ttreegen -f filename`.
`filename` can be produced from `ship.conical.Pythia8-TGeant4.root` with `sstDecouplingTools/produce_ttree.C`

Events are stored using a thin sensetive plane just in front of 1st SST station (prestrawdetector). To turn it on use flag  `--prestraw`
### SST decoupling

To run simulation on the decoupled SST (also with magnet and prestrawdetector) `--decouple`


So, the pipeline is the following:

1. Generate events using Pythia and store them with prestrawdetector
```
python $FAIRSHIP/macro/run_simScript.py --prestraw --useJSON
```

2. Make input file to MyGenerator
```
root $FAIRSHIP/sstDecouplingTools/produce_ttree.C
```

3. Run simulation on the decoupled SST using stored events
```
python $FAIRSHIP/macro/run_simScript.py --prestraw --useJSON --decouple --ttreegen -f ./inputfile.root
```

4. Run reduced reconstraction (in fact, only digitization)
```
python $FAIRSHIP/macro/ShipReco.py -f ship.conical.Ttreegen-TGeant4.root -g geofile_full.conical.Pythia8-TGeant4.root
```
