# simple vertex reconstruction with errors
import ROOT,sys
import shipunit as u
import rootUtils as ut


class Task:
 "initialize"
 def __init__(self,hp,main):
  self.sTree = main.sTree
  self.fPartArray  = ROOT.TClonesArray("TParticle")
  if not self.sTree.GetBranch("Particles"):
   self.Particles   = self.sTree.Branch("Particles",  self.fPartArray,32000,-1)
  else: 
   self.Particles = self.sTree.Particles
  self.reps,self.states,self.newPosDir = {},{},{}
  self.LV={1:ROOT.TLorentzVector(),2:ROOT.TLorentzVector()}
  self.h = hp
  self.PDG = ROOT.TDatabasePDG.Instance()
  self.fitTrackLoc = "FitTracks"
  self.goodTracksLoc = "GoodTracks"
  ut.bookHist(self.h,'Vzpull','Vz pull',100,-3.,3.)
  ut.bookHist(self.h,'Vxpull','Vx pull',100,-3.,3.)
  ut.bookHist(self.h,'Vypull','Vy pull',100,-3.,3.)
 def execute(self):
  # make particles persistent
  self.TwoTrackVertex()
  self.Particles.Fill()
 def TwoTrackVertex(self):
  self.fPartArray.Delete()
  fittedTracks = getattr(self.sTree,self.fitTrackLoc)
  goodTracks = getattr(self.sTree,self.goodTracksLoc)
  if goodTracks.size() < 2: return
  particles    = self.fPartArray
  PosDirCharge,CovMat,scalFac = {},{},{}
  for tr in goodTracks:
   fitStatus = fittedTracks[tr].getFitStatus()
   xx  = fittedTracks[tr].getFittedState()
   pid   = xx.getPDG()
   if not pidProton and abs(pid) == 2212:
     pid = int(ROOT.TMath.Sign(211,pid))
   rep   = ROOT.genfit.RKTrackRep(xx.getPDG())  
   state = ROOT.genfit.StateOnPlane(rep)
   rep.setPosMom(state,xx.getPos(),xx.getMom())
   PosDirCharge[tr] = {'position':xx.getPos(),'direction':xx.getDir(),\
                          'momentum':xx.getMom(),'charge':xx.getCharge(),'pdgCode':pid,'state':xx,'rep':rep,'newstate':state}
   CovMat[tr] = xx.get6DCov() 
#
  if len(PosDirCharge) < 2: return
  if len(PosDirCharge) > 4: return # abort too busy events
  for t1 in PosDirCharge:
   c1  = PosDirCharge[t1]['charge'] 
   for t2 in PosDirCharge:
     if not t2>t1: continue
     # ignore this for background studies 
     if PosDirCharge[t2]['charge'] == c1 : continue
     newPos,doca    = self.VertexError(t1,t2,PosDirCharge)
# as we have learned, need iterative procedure
# as we have learned, need iterative procedure
     dz = 99999.
     rc = True 
     step = 0
     while dz > 0.01:
      zBefore = newPos[2]
     # make a new rep for track 1,2
      for tr in [t1,t2]:     
       try:
        PosDirCharge[tr]['rep'].extrapolateToPoint(PosDirCharge[tr]['newstate'], newPos, False)
       except:
        # print 'SHiPReco: extrapolation did not worked'
        ut.reportError('SHiPReco: extrapolation did not worked')
        rc = False  
        break
       self.newPosDir[tr] = {'position':PosDirCharge[tr]['rep'].getPos(PosDirCharge[tr]['newstate']),\
                             'direction':PosDirCharge[tr]['rep'].getDir(PosDirCharge[tr]['newstate']),\
                             'momentum':PosDirCharge[tr]['rep'].getMom(PosDirCharge[tr]['newstate'])}
      if not rc: break
      newPos,doca = self.VertexError(t1,t2,self.newPosDir)
      dz = abs(zBefore-newPos[2])
      step+=1
      if step > 10:  
         print 'abort iteration, too many steps, pos=',newPos[0],newPos[1],newPos[2],' doca=',doca,'z before and dz',zBefore,dz
         rc = False
         break 
#       
     if not rc: continue # extrapolation failed, makes no sense to continue
# now go for the last step and vertex error
     scalFac[t1] = (PosDirCharge[t1]['position'][2]-newPos[2])/PosDirCharge[t1]['direction'][2]/PosDirCharge[t1]['momentum'].Mag()
     scalFac[t2] = (PosDirCharge[t2]['position'][2]-newPos[2])/PosDirCharge[t2]['direction'][2]/PosDirCharge[t2]['momentum'].Mag()
     HNLPos,covX,dist = self.VertexError(t1,t2,self.newPosDir,CovMat,scalFac)
# monitor Vx resolution and pulls
     #print "DEBUG",HNLPos[0],HNLPos[1],HNLPos[2],dist,covX[0][0],covX[1][1],covX[2][2]
     #print "     ",mctrack.GetStartX(),mctrack.GetStartY(),mctrack.GetStartZ()
#   HNL true
     if  self.sTree.GetBranch("fitTrack2MC"):
      mctrack = self.sTree.MCTrack[self.sTree.fitTrack2MC[t1]]
      self.h['Vzpull'].Fill( (mctrack.GetStartZ()-HNLPos[2])/ROOT.TMath.Sqrt(covX[2][2]) )
      self.h['Vxpull'].Fill( (mctrack.GetStartX()-HNLPos[0])/ROOT.TMath.Sqrt(covX[0][0]) )
      self.h['Vypull'].Fill( (mctrack.GetStartY()-HNLPos[1])/ROOT.TMath.Sqrt(covX[1][1]) )
#
     pid = PosDirCharge[t1]['pdgCode']
     mass = self.PDG.GetParticle(pid).Mass()
     mom  = self.newPosDir[t1]['momentum']
     E = ROOT.TMath.Sqrt( mass*mass + mom.Mag2() )
     self.LV[1].SetPxPyPzE(mom.x(),mom.y(),mom.z(),E)
     pid = PosDirCharge[t2]['pdgCode']
     mass = self.PDG.GetParticle(pid).Mass()
     mom  = self.newPosDir[t2]['momentum']
     E = ROOT.TMath.Sqrt( mass*mass + mom.Mag2() )
     self.LV[2].SetPxPyPzE(mom.x(),mom.y(),mom.z(),E)
     HNL = self.LV[1]+self.LV[2]
# try to make it persistent
     vx = ROOT.TLorentzVector(HNLPos,doca)  # misuse time as DOCA  
     particle = ROOT.TParticle(9900015,0,-1,-1,t1,t2,HNL,vx)
     particle.SetMother(1,99) # as marker to remember doca is set
     nParts   = particles.GetEntries()
     particles[nParts] = particle

 def VertexError(self,t1,t2,PosDir,CovMat=None,scalFac=None):
# with improved Vx x,y resolution
   a,u = PosDir[t1]['position'],PosDir[t1]['direction']
   c,v = PosDir[t2]['position'],PosDir[t2]['direction']
   Vsq = v.Dot(v)
   Usq = u.Dot(u)
   UV  = u.Dot(v)
   ca  = c-a
   denom = Usq*Vsq-UV**2
   tmp2 = Vsq*u-UV*v
   Va = ca.Dot(tmp2)/denom
   tmp2 = UV*u-Usq*v
   Vb = ca.Dot(tmp2)/denom
   X = (a+c+Va*u+Vb*v) * 0.5
   l1 = a - X + u*Va  # l2 = c - X + v*Vb
   dist = 2. * ROOT.TMath.Sqrt( l1.Dot(l1) )
   if not CovMat: return X,dist
   T = ROOT.TMatrixD(3,12)
   for i in range(3):
     for k in range(4):
       for j in range(3): 
        KD = 0
        if i==j: KD = 1
        if k==0 or k==2:
       # cova and covc
         temp  = ( u[j]*Vsq - v[j]*UV )*u[i] + (u[j]*UV-v[j]*Usq)*v[i]
         sign = -1
         if k==2 : sign = +1
         T[i][3*k+j] = 0.5*( KD + sign*temp/denom )
        elif k==1:
       # covu
         aNAZ = denom*( ca[j]*Vsq-v.Dot(ca)*v[j] )
         aZAN = ( ca.Dot(u)*Vsq-ca.Dot(v)*UV )*2*( u[j]*Vsq-v[j]*UV )
         bNAZ = denom*( ca[j]*UV+(u.Dot(ca)*v[j]) - 2*ca.Dot(v)*u[j] )
         bZAN = ( ca.Dot(u)*UV-ca.Dot(v)*Usq )*2*( u[j]*Vsq-v[j]*UV )
         T[i][3*k+j] = 0.5*( Va*KD + u[i]/denom**2*(aNAZ-aZAN) + v[i]/denom**2*(bNAZ-bZAN) )
        elif k==3:
       # covv
         aNAZ = denom*( 2*ca.Dot(u)*v[j] - ca.Dot(v)*u[j] - ca[j]*UV )
         aZAN = ( ca.Dot(u)*Vsq-ca.Dot(v)*UV )*2*( v[j]*Usq-u[j]*UV )
         bNAZ = denom*( ca.Dot(u)*u[j]-ca[j]*Usq ) 
         bZAN = ( ca.Dot(u)*UV-ca.Dot(v)*Usq )*2*( v[j]*Usq-u[j]*UV )
         T[i][3*k+j] = 0.5*(Vb*KD + u[i]/denom**2*(aNAZ-aZAN) + v[i]/denom**2*(bNAZ-bZAN) ) 
   transT = ROOT.TMatrixD(12,3)
   transT.Transpose(T)
   CovTracks = ROOT.TMatrixD(12,12)
   tlist = [t1,t2]
   for k in range(2):
     for i in range(6):
       for j in range(6): 
        xfac = 1.
        if i>2: xfac = scalFac[tlist[k]]  
        if j>2: xfac = xfac * scalFac[tlist[k]]
        CovTracks[i+k*6][j+k*6] = CovMat[tlist[k]][i][j] * xfac
        # if i==5 or j==5 :  CovMat[tlist[k]][i][j] = 0 # ignore error on z-direction
   tmp   = ROOT.TMatrixD(3,12)
   tmp.Mult(T,CovTracks)
   covX  = ROOT.TMatrixD(3,3)
   covX.Mult(tmp,transT)
   return X,covX,dist

#usage
# import shipVertex
# VertexError = shipVertex.Task()
# newPos,doca = myVertexError(t1,t2,PosDirCharge)
