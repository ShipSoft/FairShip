import ROOT,os,sys,atexit
from rootpyPickler import Unpickler
import shipRoot_conf
shipRoot_conf.configure()  

def rmxx():
 os.system("rm x.x")
 pass
atexit.register(rmxx)

fname = "geofile_full.10.0.Pythia8-TGeant4.root"
if len(sys.argv)>1: fname=sys.argv[1]

fgeo = ROOT.TFile(fname)
sGeo = fgeo.FAIRGeom
import shipDet_conf
run = ROOT.FairRunSim()
upkl    = Unpickler(fgeo)
ShipGeo = upkl.load('ShipGeo')
modules = shipDet_conf.configure(run,ShipGeo)
run.SetUserConfig("g4Config.C")
run.SetName("TGeant4")
run.SetOutputFile("x.x")
run.Init()
run.Run(0)
import geomGeant4
geomGeant4.printWeightsandFields()


