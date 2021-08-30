import ROOT
import rootUtils as ut
h={}

geoFile = "geofile_full.Ntuple-TGeant4.root"
fgeo = ROOT.TFile.Open(geoFile)
from ShipGeoConfig import ConfigRegistry
from rootpyPickler import Unpickler
#load geo dictionary
upkl    = Unpickler(fgeo)
snd_geo = upkl.load('ShipGeo')
 
# -----Create geometry----------------------------------------------
import shipLHC_conf as sndDet_conf

run = ROOT.FairRunSim()
run.SetName("TGeant4")  # Transport engine
run.SetOutputFile(ROOT.TMemFile('output', 'recreate'))  # Output file
run.SetUserConfig("g4Config_basic.C") # geant4 transport not used
rtdb = run.GetRuntimeDb()
modules = sndDet_conf.configure(run,snd_geo)
sGeo = fgeo.FAIRGeom
top = sGeo.GetTopVolume()

ut.bookHist(h,'S','stations',7,-0.5,6.5)
ut.bookHist(h,'O','orientation',7,-0.5,6.5)
ut.bookHist(h,'M','orientation',7,-0.5,6.5)
ut.bookHist(h,'R','row',7,-0.5,6.5)
ut.bookHist(h,'N','fibre',1000,-0.5,999.5)
ut.bookHist(h,'E','dE',100,0.0,1000.)

f = ROOT.TFile.Open("sndLHC.Ntuple-TGeant4.root")
for sTree in f.cbmsim:
   for p in sTree.ScifiPoint:
      print(p.GetDetectorID(),':',p.station(),p.orientation())
      rc = h['S'].Fill(p.station())
      rc = h['O'].Fill(p.orientation())
      rc = h['M'].Fill(p.mat())
      rc = h['R'].Fill(p.row())
      rc = h['N'].Fill(p.fibreN())
      rc = h['E'].Fill(p.GetEnergyLoss()*1E6)
