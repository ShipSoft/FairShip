from __future__ import print_function
from __future__ import division
from past.builtins import cmp
import ROOT
import shipunit as u

minNdf = 20
parallelToZ = ROOT.TVector3(0., 0., 1.) 
top = ROOT.gGeoManager.GetTopVolume()
if top.GetNode('Ecal_1'): z_ecal = top.GetNode('Ecal_1').GetMatrix().GetTranslation()[2]
elif top.GetNode('SplitCalDetector_1'):    z_ecal = top.GetNode('SplitCalDetector_1').GetMatrix().GetTranslation()[2]
else:
  print("TrackExtraploate tool: Error, no calo present")
  z_ecal = 100*u.m
def extrapolateToPlane(fT,z):
# etrapolate to a plane perpendicular to beam direction (z)
  rc,pos,mom = False,None,None
  fst = fT.getFitStatus()
  if fst.isFitConverged() and fst.getNdf() > minNdf:
# test for fit status for each point
   if fT.getPoint(0).getFitterInfo() and fT.getPoint(1).getFitterInfo():
    fstate0,fstate1 = fT.getFittedState(0),fT.getFittedState(1) 
    fPos0,fPos1     = fstate0.getPos(),fstate1.getPos()
    if abs(z-fPos0.z()) <  abs(z-fPos1.z()): fstate = fstate0
    else:                                    fstate = fstate1
    zs = min(z,z_ecal)
    NewPosition = ROOT.TVector3(0., 0., zs) 
    rep    = ROOT.genfit.RKTrackRep(13*cmp(fstate.getPDG(),0) ) 
    state  = ROOT.genfit.StateOnPlane(rep) 
    pos,mom = fstate.getPos(),fstate.getMom()
    rep.setPosMom(state,pos,mom) 
    try:    
      rep.extrapolateToPlane(state, NewPosition, parallelToZ )
      pos,mom = state.getPos(),state.getMom()
      rc = True 
    except: 
      # print 'error with extrapolation: z=',z/u.m,'m',pos.X(),pos.Y(),pos.Z(),mom.X(),mom.Y(),mom.Z()
      pass
    if not rc or z>z_ecal:
     # use linear extrapolation
     px,py,pz  = mom.X(),mom.Y(),mom.Z()
     lam = (z-pos.Z())/pz
     pos = ROOT.TVector3( pos.X()+lam*px, pos.Y()+lam*py, z )
  return rc,pos,mom
