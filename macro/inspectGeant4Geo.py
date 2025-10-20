import sys
import ROOT
from ShipGeoConfig import load_from_root_file
import shipRoot_conf
shipRoot_conf.configure()

fname = 'geofile_full.10.0.Pythia8-TGeant4.root'
if len(sys.argv) > 1:
    fname = sys.argv[1]

fgeo = ROOT.TFile(fname)
sGeo = fgeo.Get("FAIRGeom")
import shipDet_conf
run = ROOT.FairRunSim()
ShipGeo = load_from_root_file(fgeo, 'ShipGeo')
modules = shipDet_conf.configure(run, ShipGeo)
run.SetUserConfig('g4Config.C')
run.SetName('TGeant4')
run.SetSink(ROOT.FairRootFileSink(ROOT.TMemFile('output', 'recreate')))
run.Init()
run.Run(0)
import geomGeant4
geomGeant4.printVMCFields()
geomGeant4.printWeightsandFields()
