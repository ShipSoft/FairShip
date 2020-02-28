# utility to simulate response of the veto systems
from __future__ import division
import ROOT
import shipunit as u
from array import array

class Task:
 "initialize and give response of the veto systems"
 def __init__(self,t):
  self.SBTefficiency = 0.99  # Surrounding Background tagger: 99% efficiency picked up from TP
  self.SVTefficiency = 0.995 # Straw Veto tagger: guestimate, including dead channels
  self.random = ROOT.TRandom()
  ROOT.gRandom.SetSeed(13)
  self.detList  = self.detMap()
  self.sTree = t

 def detMap(self):
  fGeo = ROOT.gGeoManager  
  detList = {}
  for v in fGeo.GetListOfVolumes():
   nm = v.GetName()
   i  = fGeo.FindVolumeFast(nm).GetNumber()
   detList[i] = nm
  return detList 

 def SBT_plastic_decision(self,mcParticle=None):
    SBT_decision(self,mcParticle,detector='plastic')
 def SBT_liquid_decision(self,mcParticle=None):
    SBT_decision(self,mcParticle,detector='liquid')
 
 def SBT_decision(self,mcParticle=None,detector='liquid'):
  # if mcParticle >0, only count hits with this particle
  # if mcParticle <0, do not count hits with this particle
  hitSegments = 0
  index = -1
  fdetector = detector=='liquid'
  for aDigi in self.sTree.Digi_SBTHits:
     index+=1 
     detID    = aDigi.GetDetectorID()
     if fdetector and detID > 999999:continue
     if not fdetector and not detID > 999999:continue 
     if mcParticle:
        found = False
        for mcP in self.sTree.digiSBT2MC[index]: 
         if mcParticle>0 and mcParticle != mcP : found=True
         if mcParticle<0 and abs(mcParticle) == mcP : found=True
        if found: continue
     position = aDigi.GetXYZ()
     ELoss    = aDigi.GetEloss()
     if aDigi.isValid(): hitSegments += 1 #threshold of 45 MeV per segment
  w = (1-self.SBTefficiency)**hitSegments  
  veto = self.random.Rndm() > w
  #print 'SBT :',hitSegments
  return veto, w, hitSegments
 def SVT_decision(self,mcParticle=None):
  nHits = 0
  for ahit in self.sTree.strawtubesPoint:
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
 def RPC_decision(self,mcParticle=None):
  nHits = 0
  mom = ROOT.TVector3()
  for ahit in self.sTree.ShipRpcPoint:
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
 def Track_decision(self,mcParticle=None):
  nMultCon = 0
  k = -1
  for aTrack in self.sTree.FitTracks:
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
 def fiducialCheckSignal(self,n):
  hnl = self.sTree.Particles[n]
  aPoint = ROOT.TVector3(hnl.Vx(),hnl.Vy(),hnl.Vz())
  distmin = self.fiducialCheck(aPoint)
  return distmin
 def fiducialCheck(self,aPoint):
  nav = ROOT.gGeoManager.GetCurrentNavigator()
  phi = 0.
  nSteps = 36
  delPhi = 2.*ROOT.TMath.Pi()/nSteps
  distmin = 1E10
  nav.SetCurrentPoint(aPoint.x(),aPoint.y(),aPoint.z())
  cNode = 'outside'
  aNode = nav.FindNode()
  if aNode: cNode = aNode.GetName()
  if cNode != 'T2decayVol_0' and cNode != 'T1decayVol_0': 
   distmin = 0. 
  else:
   for n in range(nSteps):
   # set direction
    xDir = ROOT.TMath.Sin(phi)
    yDir = ROOT.TMath.Cos(phi)
    nav.SetCurrentPoint(aPoint.x(),aPoint.y(),aPoint.z())
    cNode = nav.FindNode().GetName()
    nav.SetCurrentDirection(xDir,yDir,0.)
    rc = nav.FindNextBoundaryAndStep()
    x,y  = nav.GetCurrentPoint()[0],nav.GetCurrentPoint()[1]
    if cNode != nav.GetCurrentNode().GetName():
     dist = ROOT.TMath.Sqrt( (aPoint.x()-x)**2 + (aPoint.y()-y)**2)
     if dist < distmin : distmin = dist  
    phi+=delPhi
# distance to Tr1_x1
   nav.cd("/Tr1_1")
   shape = nav.GetCurrentNode().GetVolume().GetShape()
   origin = array('d',[0,0,shape.GetDZ()])
   master = array('d',[0,0,0])
   nav.LocalToMaster(origin,master)
   dist = master[2] - aPoint.z()  
   if dist < distmin : distmin = dist  
# distance to straw veto:
   nav.cd("/Veto_5")
   shape = nav.GetCurrentNode().GetVolume().GetShape()
   origin = array('d',[0,0,shape.GetDZ()])
   master = array('d',[0,0,0])
   nav.LocalToMaster(origin,master)
   dist = aPoint.z() - master[2]
  return distmin

#usage
# import shipVeto
# veto = shipVeto.Task(sTree)
# veto,w = veto.SBT_decision()
# or for plastic veto,w = veto.SBT_decision(detector='plastic')
# if veto: continue # reject event
# or
# continue using weight w 
