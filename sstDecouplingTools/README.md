### Geometry tuning

To set geometrical parameters from user csv file run the macro with `--useCSV`

###

To run simulation with events from file `--MyGen -f filename`.
`filename` can be produced from `ship.conical.Pythia8-TGeant4.root` with `sstDecouplingTools/produce_ttree.C`

### SST decoupling

To run simulation on the decoupled SST (also with magnet and prestrawdetector) `--decouple`


So, the pipeline is the following:

1. Generate events using Pythia and store them with prestrawdetector
```
python $FAIRSHIP/macro/run_simScript.py --useCSV
```

2. Make input file to MyGenerator
```
root $FAIRSHIP/sstDecouplingTools/produce_ttree.C
```

3. Run simulation on the decoupled SST using stored events
```
python $FAIRSHIP/macro/run_simScript.py --useCSV --decouple --MyGen -f ./inputfile.root
```
