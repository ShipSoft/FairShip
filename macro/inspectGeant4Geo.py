import sys
import ROOT

from fairship.ShipGeoConfig import load_from_root_file
from fairship.utils.rootpy_pickler import Unpickler
import fairship.shipRoot_conf as shipRoot_conf

shipRoot_conf.configure()

fname = 'geofile_full.10.0.Pythia8-TGeant4.root'
if len(sys.argv) > 1:
    fname = sys.argv[1]

fgeo = ROOT.TFile(fname)
sGeo = fgeo.Get("FAIRGeom")
import fairship.shipDet_conf as shipDet_conf
run = ROOT.FairRunSim()
ShipGeo = load_from_root_file(fgeo, 'ShipGeo')
modules = shipDet_conf.configure(run, ShipGeo)
run.SetUserConfig('g4Config.C')
run.SetName('TGeant4')
run.SetSink(ROOT.FairRootFileSink(ROOT.TMemFile('output', 'recreate')))
run.Init()
run.Run(0)
import fairship.geomGeant4 as geomGeant4
geomGeant4.printVMCFields()
geomGeant4.printWeightsandFields()
