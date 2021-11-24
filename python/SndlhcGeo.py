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
   self.snd_geo = upkl.load('ShipGeo')
# -----Create geometry----------------------------------------------
   run = "notNeeded"
   self.modules = sndDet_conf.configure(run,self.snd_geo)
   self.sGeo = self.fgeo.FAIRGeom
   self.modules['Scifi'].SiPMmapping()
   lsOfGlobals = ROOT.gROOT.GetListOfGlobals()
   for m in self.modules: lsOfGlobals.Add(self.modules[m])

   temp = {}
   for o1 in self.snd_geo:
     key = o1
     x = self.snd_geo[o1]
     if not hasattr(x,'items'):       temp[key] = x
     else:
        for o2 in x:
            key = o1 + '/' +o2
            y = x[o2]
            if not  hasattr(y,'items'):         temp[key] = y
            else:
                for o3 in y:
                   key = o1 + '/' +o2+ '__' +o3
                   z = y[o3]
                   if not  hasattr(z,'items'):        temp[key] = z
   for key in temp:
       if not key.find('MuFilter')<0:
            self.modules['MuFilter'].SetConfPar(key,temp[key])
       if not key.find('Scifi')<0:
            self.modules['Scifi'].SetConfPar(key,temp[key])

 def FinishEvent(self):
  pass
