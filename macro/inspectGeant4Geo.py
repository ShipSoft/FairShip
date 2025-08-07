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
run.SetUserConfig('g4Config.yaml')
run.SetName('TGeant4')
run.SetSink(ROOT.FairRootFileSink(ROOT.TMemFile('output', 'recreate')))
# Create and set custom ShipStack for YAML config compatibility
stack = ROOT.ShipStack(1000)
stack.StoreSecondaries(ROOT.kTRUE)
stack.SetMinPoints(0)
# Get the Geant4 VMC instance and set our custom stack
geant4 = ROOT.TVirtualMC.GetMC()
if geant4:
    geant4.SetStack(stack)
run.Init()
run.Run(0)
import geomGeant4
geomGeant4.printVMCFields()
geomGeant4.printWeightsandFields()
