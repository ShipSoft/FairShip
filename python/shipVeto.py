# utility to simulate response of the veto systems
import ROOT
import shipunit as u

class Task:
 "initialize and give response of the veto systems"
 def __init__(self):
 # needs to be done better
  self.N = 16  #number of segments in X-Y
  self.dphi = 2*ROOT.TMath.Pi()/self.N
  self.phistart = self.dphi/2
  self.UVTefficiency = 0.999 # Upstream Veto tagger: 99.9% efficiency picked up from TP
  self.SBTefficiency = 0.99  # Surrounding Background tagger: 99% efficiency picked up from TP
  self.SVTefficiency = 0.995 # Straw Veto tagger: guestimate, including dead channels
  self.detList  = self.detMap()
  self.random = ROOT.TRandom()
  ROOT.gRandom.SetSeed(13)

 def detMap(self):
  fGeo = ROOT.gGeoManager  
  detList = {}
  for v in fGeo.GetListOfVolumes():
   nm = v.GetName()
   i  = fGeo.FindVolumeFast(nm).GetNumber()
   detList[i] = nm
  T2Shape = fGeo.GetVolume('T2LiSc').GetShape()
  self.a = T2Shape.GetDX() - 15 # 15cm = half size of liquid, was not able to figure out how to retrieve from geometry
  self.b = T2Shape.GetDY() - 15
  T1Shape = fGeo.GetVolume('T1LiSc').GetShape()
  self.asmall = T1Shape.GetDX() - 15
  return detList 

 def SBT_decision(self,sTree):
  ELOSS = {} 
  for i in self.detList: 
    if not self.detList[i].find('LiSc')<0: 
       ELOSS[self.detList[i]] = [0]*self.N 
  for ahit in sTree.vetoPoint:
     detID   = ahit.GetDetectorID()
     detName = self.detList[detID]
     if not detName in ELOSS: continue
     x,y,z = (ahit.GetX(), ahit.GetY(), ahit.GetZ())
     ELoss = ahit.GetEnergyLoss()
     if not detName.find("T1")<0:   t = ROOT.TMath.ATan2(self.a*y,self.b*x)
     else:                          t = ROOT.TMath.ATan2(self.asmall*y,self.b*x)
     phisegment = ROOT.TMath.FloorNint((t+2*ROOT.TMath.Pi()+self.phistart)/self.dphi)%self.N
     ELOSS[detName][phisegment] += ELoss
  hitSegments = 0
  for detName in ELOSS:
    for seg in range(len(ELOSS[detName])):
      if ELOSS[detName][seg] > 0.045: hitSegments += 1 #threshold of 45 MeV per segment
  w = (1-self.SBTefficiency)**hitSegments  
  veto = self.random.Rndm() > w
  return veto, w 
 def UVT_decision(self,sTree):
  nHits = 0
  for ahit in sTree.vetoPoint:
     detID   = ahit.GetDetectorID()
     detName = self.detList[detID]
     if not detName == "VetoTimeDet": continue
     nHits+=1
  w = (1-self.UVTefficiency)**nHits
  veto = self.random.Rndm() > w
  return veto, w
 def SVT_decision(self,sTree):
  nHits = 0
  for ahit in sTree.strawtubesPoint:
     detID   = ahit.GetDetectorID()
     if detID<50000000: continue  # StrawVeto station = 5
     nHits+=1
  w = (1-self.SVTefficiency)**nHits
  veto = self.random.Rndm() > w
  return veto,w

#usage
# import shipVeto
# veto = shipVeto.Task()
# veto,w = veto.SBT_decision(sTree)
# if veto: continue # reject event
# or
# continue using weight w 
