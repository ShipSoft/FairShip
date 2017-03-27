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
  t2LiSc = fGeo.GetVolume('T2LiSc')
  if not t2LiSc: t2LiSc = fGeo.GetVolume('T2LiSc_1')
  T2Shape = t2LiSc.GetShape()
  self.a = T2Shape.GetDX() - 15 # 15cm = half size of liquid, was not able to figure out how to retrieve from geometry
  self.b = T2Shape.GetDY() - 15
  t1LiSc = fGeo.GetVolume('T1LiSc')
  if not t1LiSc: t1LiSc = fGeo.GetVolume('T1LiSc_1')
  T1Shape = t1LiSc.GetShape()
  self.asmall = T1Shape.GetDX() - 15
  return detList 

 def SBT_decision(self,sTree,mcParticle=None):
  # if mcParticle >0, only count hits with this particle
  # if mcParticle <0, do not count hits with this particle
  hitSegments = 0
  index = -1
  for aDigi in sTree.Digi_SBTHits:
     index+=1 
     if mcParticle:
        found = False
        for mcParticle in sTree.digiSBT2MC[index]: 
         if mcParticle>0 and mcParticle != ahit.GetTrackID() : found=True
         if mcParticle<0 and abs(mcParticle) == ahit.GetTrackID() : found=True
        if found: continue
     detID    = aDigi.GetDetectorID()
     position = aDigi.GetXYZ()
     ELoss    = aDigi.GetEloss()
     if aDigi.isValid(): hitSegments += 1 #threshold of 45 MeV per segment
  w = (1-self.SBTefficiency)**hitSegments  
  veto = self.random.Rndm() > w
  #print 'SBT :',hitSegments
  return veto, w, hitSegments
 def UVT_decision(self,sTree,mcParticle=None):
  nHits = 0
  for ahit in sTree.vetoPoint:
     detID   = ahit.GetDetectorID()
     if detID>100000: continue  # this is a LiSc detector
     if mcParticle: 
        if mcParticle>0 and mcParticle != ahit.GetTrackID() : continue
        if mcParticle<0 and abs(mcParticle) == ahit.GetTrackID() : continue
     detName = self.detList[detID]
     if not detName == "VetoTimeDet": continue
     nHits+=1
  w = (1-self.UVTefficiency)**nHits
  veto = self.random.Rndm() > w
  #print 'UVT :',nHits
  return veto, w,nHits
 def SVT_decision(self,sTree,mcParticle=None):
  nHits = 0
  for ahit in sTree.strawtubesPoint:
     if mcParticle: 
        if mcParticle>0 and mcParticle != ahit.GetTrackID() : continue
        if mcParticle<0 and abs(mcParticle) == ahit.GetTrackID() : continue
     detID   = ahit.GetDetectorID()
     if detID<50000000: continue  # StrawVeto station = 5
     nHits+=1
  w = (1-self.SVTefficiency)**nHits
  veto = self.random.Rndm() > w
  # print 'SVT :',nHits
  return veto,w,nHits
 def RPC_decision(self,sTree,mcParticle=None):
  nHits = 0
  mom = ROOT.TVector3()
  for ahit in sTree.ShipRpcPoint:
   if mcParticle: 
        if mcParticle>0 and mcParticle != ahit.GetTrackID() : continue
        if mcParticle<0 and abs(mcParticle) == ahit.GetTrackID() : continue
   ahit.Momentum(mom)
   if mom.Mag() > 0.1: nHits+=1
  w = 1
  veto = nHits > 0 # 10  change to >0 since neutrino background ntuple not possible otherwise
  if veto: w = 0.
  #print 'RPC :',nHits
  return veto,w,nHits
 def Track_decision(self,sTree,mcParticle=None):
  nMultCon = 0
  k = -1
  for aTrack in sTree.FitTracks:
     k+=1 
     if mcParticle: 
        if mcParticle>0 and mcParticle != ahit.GetTrackID() : continue
        if mcParticle<0 and abs(mcParticle) == ahit.GetTrackID() : continue
     fstatus =  aTrack.getFitStatus()
     if not fstatus.isFitConverged() : continue
     if fstatus.getNdf() < 25: continue
     nMultCon+=1
  w = 1
  veto = nMultCon > 2
  if veto: w = 0.
  return veto,w,nMultCon

#usage
# import shipVeto
# veto = shipVeto.Task()
# veto,w = veto.SBT_decision(sTree)
# if veto: continue # reject event
# or
# continue using weight w 
