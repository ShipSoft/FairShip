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
scifi = modules['Scifi']

ut.bookHist(h,'S','stations',7,-0.5,6.5)
ut.bookHist(h,'O','orientation',7,-0.5,6.5)
ut.bookHist(h,'M','mat',7,-0.5,6.5)
ut.bookHist(h,'R','row',7,-0.5,6.5)
ut.bookHist(h,'N','fibre',1000,-0.5,999.5)

for s in range(1,6):
    ut.bookHist(h,'Sxy'+str(s),'XY',50,-50.,0.,50,10.,60.)
    for o in range(2):
      for m in range(1,4):
          for r in range(1,7):
               ut.bookHist(h,'N'+str(s)+str(o)+str(m)+str(r),'fibre',1000,-0.5,999.5)
ut.bookHist(h,'E','dE',100,0.0,1000.)
ut.bookHist(h,'nhits','hits per event',100,0.0,1000.)

f = ROOT.TFile.Open("sndLHC.Ntuple-TGeant4.root")
for x in h: h[x].Reset()
for sTree in f.cbmsim:
   rc = h['nhits'].Fill(sTree.ScifiPoint.GetEntries())
   w = sTree.MCTrack[0].GetWeight() # assume these are muon background events.
   for p in sTree.ScifiPoint:
      if p.GetDetectorID()==0: continue
      rc = h['S'].Fill(p.station(),w)
      rc = h['O'].Fill(p.orientation(),w)
      rc = h['M'].Fill(p.mat(),w)
      rc = h['R'].Fill(p.row(),w)
      rc = h['N'].Fill(p.fibreN(),w)
      rc = h['Sxy'+str(p.station())].Fill(p.GetX(),p.GetY(),w)
      rc = h['N'+str(p.GetDetectorID()//1000)].Fill(p.fibreN(),w)
      rc = h['E'].Fill(p.GetEnergyLoss()*1E6,w)

# test position
A,B=ROOT.TVector3(),ROOT.TVector3()
scifi.GetPosition(1011001,A,B)
print("horizontal mat")
A.Print()
B.Print()
print("vertical mat")
scifi.GetPosition(1111001,A,B)
A.Print()
B.Print()

