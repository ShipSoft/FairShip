import ROOT
import shipunit as u
import shipLHC_conf as sndDet_conf
from ShipGeoConfig import ConfigRegistry
from rootpyPickler import Unpickler

class GeoInterface():
 " Geometry "
 def __init__(self,geoFile):
   self.fgeo = ROOT.TFile.Open(geoFile)
#load geo dictionary
   upkl    = Unpickler(self.fgeo)
   snd_geo = upkl.load('ShipGeo')
# -----Create geometry----------------------------------------------
   run = "notNeeded"
   self.modules = sndDet_conf.configure(run,snd_geo)
   self.sGeo = self.fgeo.FAIRGeom
   self.modules['Scifi'].SiPMmapping()
   lsOfGlobals = ROOT.gROOT.GetListOfGlobals()
   for m in self.modules: lsOfGlobals.Add(self.modules[m])

 def FinishEvent(self):
  pass
