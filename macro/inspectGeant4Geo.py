import sys
import ROOT
from rootpyPickler import Unpickler
import shipRoot_conf
shipRoot_conf.configure()

fname = 'geofile_full.10.0.Pythia8-TGeant4.root'
if len(sys.argv) > 1:
    fname = sys.argv[1]

fgeo = ROOT.TFile(fname)
sGeo = fgeo.Get("FAIRGeom")
import shipDet_conf

run = ROOT.FairRunSim()
upkl = Unpickler(fgeo)
ShipGeo = upkl.load('ShipGeo')
modules = shipDet_conf.configure(run, ShipGeo)
# Use SHiP::VMCConfig for YAML configuration
ROOT.gInterpreter.ProcessLine('FairRunSim::Instance()->SetSimulationConfig(std::make_unique<SHiP::VMCConfig>("g4Config", "g4Config.yaml"));')
run.SetName('TGeant4')
run.SetSink(ROOT.FairRootFileSink(ROOT.TMemFile('output', 'recreate')))
# ShipStack is now automatically created by SHiP::VMCConfig
run.Init()
run.Run(0)
import geomGeant4

geomGeant4.printVMCFields()
geomGeant4.printWeightsandFields()
