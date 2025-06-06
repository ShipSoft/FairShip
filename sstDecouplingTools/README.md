### Geometry tuning

To set geometrical parameters from user csv file run 'python run\_simScript.py --useCSV'

### 

To run simulation with events from file 'python run\_simScript.py --MyGen -f _filename_'.
'_filename_' can be produced from 'ship.conical.Pythia8-TGeant4.root' with sstDecouplingTools/produce\_ttree.C

### SST decoupling

To run simulation on the decoupled SST (with magnet and prestrawdetector) 'python run\_simScript.py --decouple'


So, the pipeline is the following:

1. Generate events using Pythia and store them with prestrawdetector
'python $FAIRSHIP/macro/run\_simScript.py --useCSV'

2. Make input file to MyGenerator
'root $FAIRSHIP/sstDecouplingTools/produce\_ttree.C'

3. Run simulation on the decoupled SST using stored events
'python $FAIRSHIP/macro/run\_simScript.py --useCSV --decouple --MyGen -f ./inputfile.root'



