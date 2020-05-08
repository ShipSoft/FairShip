from __future__ import print_function
from __future__ import division
# simple vertex reconstruction with errors
import ROOT,sys,os
import global_variables
import shipunit as u
import rootUtils as ut
import numpy as np
import math
import ctypes
from array import array

class Task:
 "initialize"
 def __init__(self,hp,sTree):
  self.sTree = sTree
  self.fPartArray  = ROOT.TClonesArray("ShipParticle")
  if not self.sTree.GetBranch("Particles"):
   self.Particles   = self.sTree.Branch("Particles",  self.fPartArray,32000,-1)
  else: 
   self.Particles = self.sTree.Particles
  self.reps,self.states,self.newPosDir = {},{},{}
  self.LV={1:ROOT.TLorentzVector(),2:ROOT.TLorentzVector()}
  self.h = hp
  self.PDG = ROOT.TDatabasePDG.Instance()
  self.fitTrackLoc = "FitTracks"
  self.goodTracksLoc = "goodTracks"
  #ut.bookHist(self.h,'Vzpull','Vz pull',100,-3.,3.)
  #ut.bookHist(self.h,'Vxpull','Vx pull',100,-3.,3.)
  #ut.bookHist(self.h,'Vypull','Vy pull',100,-3.,3.)
  
  #ut.bookHist(self.h,'dVx','vertex X residual;X^{RECO}-X^{MC}, cm',400,-10.,10.)
  #ut.bookHist(self.h,'dVy','vertex Y residual;Y^{RECO}-Y^{MC}, cm',400,-10.,10.)
  #ut.bookHist(self.h,'dVz','vertex Z residual;Z^{RECO}-Z^{MC}, cm',500,-50.,50.)
  #ut.bookHist(self.h,'VzpullFit','Vz pull, chi2 fit',100,-3.,3.)
  #ut.bookHist(self.h,'VxpullFit','Vx pull, chi2 fit',100,-3.,3.)
  #ut.bookHist(self.h,'VypullFit','Vy pull, chi2 fit',100,-3.,3.)
  #ut.bookHist(self.h,'dVxFit','vertex X residual, chi2 fit;X^{RECO}-X^{MC}, cm',400,-10.,10.)
  #ut.bookHist(self.h,'dVyFit','vertex Y residual, chi2 fit;Y^{RECO}-Y^{MC}, cm',400,-10.,10.)
  #ut.bookHist(self.h,'dVzFit','vertex Z residual, chi2 fit;Z^{RECO}-Z^{MC}, cm',500,-50.,50.)
  #ut.bookHist(self.h,'dMFit','HNL mass resolution, chi2 fit;M^{RECO}-M^{MC}, GeV',2000,-1.,1.)
  #ut.bookHist(self.h,'MpullFit','M pull, chi2 fit',100,-3.,3.)

  #ut.bookHist(self.h,'N_raveVtx','Number of RAVE vtx',5,-0.5,4.5)
  #ut.bookHist(self.h,'N_Vtx','Number of vtx',5,-0.5,4.5)
  
 def execute(self):
  # make particles persistent
  self.TwoTrackVertex()
  self.Particles.Fill()
 #define global data and functions for vertex fit with TMinuit
 y_data = np.array([0.,0.,0.,0.,0.,0.,0.,0.,0.,0.])
 z0 = 0
 Vy = np.zeros(100)    
 def chi2(self,res,Vy):       
  s=0
  for i in range(100):
    s+=Vy[i]*res[i//10]*res[i%10]
  return s
 def residuals(self,y_data,a,z0):
  res = np.zeros(10)
  res[0] = abs(y_data[0]) - a[5]
  res[1] = y_data[1] - a[3] 
  res[2] = y_data[2] - a[4] 
  res[3] = y_data[3] - a[0] - a[3]*(a[2] - z0)
  res[4] = y_data[4] - a[1] - a[4]*(a[2] - z0)
  res[5] = abs(y_data[5]) - a[8] 
  res[6] = y_data[6] - a[6] 
  res[7] = y_data[7] - a[7] 
  res[8] = y_data[8] - a[0] - a[6]*(a[2] - z0)
  res[9] = y_data[9] - a[1] - a[7]*(a[2] - z0)
  return res
 def f_chi2_0(self,*a):
  v = self.chi2(self.residuals(self.y_data,a,self.z0),self.Vy)
  return v
 def f_chi2(self,a):
  v = self.chi2(self.residuals(self.y_data,a,self.z0),self.Vy)
  return v
 def fcn(self,npar, gin, f, par, iflag):
  f[0] = self.f_chi2(par)
  return
 
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
   if not global_variables.pidProton and abs(pid) == 2212:
     pid = int(math.copysign(211,pid))
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
        ut.reportError('shipVertex: extrapolation did not worked')
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
         ut.reportError("shipVertex::abort iteration, too many steps")
         if global_variables.debug:
          print('abort iteration, too many steps, pos=',newPos[0],newPos[1],newPos[2],' doca=',doca,'z before and dz',zBefore,dz)
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
      mctrack2 = self.sTree.MCTrack[self.sTree.fitTrack2MC[t2]]
      mcHNL = self.sTree.MCTrack[mctrack.GetMotherId()]
      #print "true vtx: ",mctrack.GetStartX(),mctrack.GetStartY(),mctrack.GetStartZ()
      #print "reco vtx: ",HNLPos[0],HNLPos[1],HNLPos[2]
      #self.h['Vzpull'].Fill( (mctrack.GetStartZ()-HNLPos[2])/ROOT.TMath.Sqrt(covX[2][2]) )
      #self.h['Vxpull'].Fill( (mctrack.GetStartX()-HNLPos[0])/ROOT.TMath.Sqrt(covX[0][0]) )
      #self.h['Vypull'].Fill( (mctrack.GetStartY()-HNLPos[1])/ROOT.TMath.Sqrt(covX[1][1]) )
      #self.h['dVx'].Fill( (mctrack.GetStartX()-HNLPos[0]) )
      #self.h['dVy'].Fill( (mctrack.GetStartY()-HNLPos[1]) )
      #self.h['dVz'].Fill( (mctrack.GetStartZ()-HNLPos[2]) )
      
     
     #print "*********************************** vertex fit precise   ******************************************** "
     
     detPlane = ROOT.genfit.DetPlane(ROOT.TVector3(0,0,HNLPos[2]),ROOT.TVector3(1,0,0),ROOT.TVector3(0,1,0))
     plane = ROOT.genfit.RKTrackRep().makePlane(ROOT.TVector3(0,0,HNLPos[2]),ROOT.TVector3(1,0,0),ROOT.TVector3(0,1,0))
     st1  = fittedTracks[t1].getFittedState()
     st2  = fittedTracks[t2].getFittedState()
     try:
      st1.extrapolateToPlane(plane)
     except:
      ut.reportError("shipVertex::TwoTrackVertex: extrapolation does not worked")
      continue
     try:
      st2.extrapolateToPlane(plane)
     except:
      ut.reportError("shipVertex::TwoTrackVertex: extrapolation does not worked")
      continue
     mom1 = st1.getMom()
     mom2 = st2.getMom()
     cov1 = st1.getCov()
     cov2 = st2.getCov()
     cov = ROOT.TMatrixDSym(10)
     for i in range(10):
       for j in range(10):
         if i<5 and j<5: cov[i][j]=cov1[i][j]
         if i>4 and j>4: cov[i][j]=cov2[i-5][j-5]
     covInv = ROOT.TMatrixDSym()
     ROOT.genfit.tools.invertMatrix(cov,covInv)
     
     self.y_data = np.array([0.,0.,0.,0.,0.,0.,0.,0.,0.,0.])
     stVal1 = st1.getState()
     stVal2 = st2.getState()
     for i in range(5):
      self.y_data[i]=stVal1[i]
      self.y_data[i+5]=stVal2[i]
     self.z0 = HNLPos[2]
     self.Vy = np.zeros(100)
     for i in range(100):
       self.Vy[i] = covInv[i//10][i%10]
     
     f=np.array([0.])
     gMinuit = ROOT.TMinuit(9)
     gMinuit.SetFCN(self.fcn)
     gMinuit.SetPrintLevel(-1)#minute quiet mode
     rc = gMinuit.DefineParameter(0, 'X pos',HNLPos[0], 0.1,0,0)
     rc = gMinuit.DefineParameter(1, 'Y pos',HNLPos[1], 0.1,0,0)
     rc = gMinuit.DefineParameter(2, 'Z pos',HNLPos[2], 0.1,0,0)
     rc = gMinuit.DefineParameter(3, 'tan1X',mom1[0]/mom1[2], 0.1,0,0)
     rc = gMinuit.DefineParameter(4, 'tan1Y',mom1[1]/mom1[2], 0.1,0,0)
     rc = gMinuit.DefineParameter(5, '1/mom1',1./mom1.Mag(), 0.1,0,0)
     rc = gMinuit.DefineParameter(6, 'tan2X',mom2[0]/mom2[2], 0.1,0,0)
     rc = gMinuit.DefineParameter(7, 'tan2Y',mom2[1]/mom2[2], 0.1,0,0)
     rc = gMinuit.DefineParameter(8, '1/mom2',1./mom2.Mag(), 0.1,0,0)
     gMinuit.Clear()
     gMinuit.Migrad()
     try:
      tmp = array('d',[0])
      err = array('i',[0])
      gMinuit.mnexcm( "HESSE", tmp, -1, err )
      #gMinuit.mnexcm( "MINOS", tmp, -1, err )
     except:
       ut.reportError("shipVertex::minos does not work")
       continue
     #get results from TMinuit:
     emat = array('d',[0,]*81)
     gMinuit.mnemat(emat,9)
     values = array('d',[0,]*9)
     errors = array('d',[0,]*9)
     dValue = ctypes.c_double()
     dError = ctypes.c_double()
     rc = gMinuit.GetParameter(0, dValue, dError)
     values[0]=dValue.value
     errors[0]=dError.value
     rc = gMinuit.GetParameter(1, dValue, dError)
     values[1]=dValue.value
     errors[1]=dError.value
     rc = gMinuit.GetParameter(2, dValue, dError)
     values[2]=dValue.value
     errors[2]=dError.value
     rc = gMinuit.GetParameter(3, dValue, dError)
     values[3]=dValue.value
     errors[3]=dError.value
     rc = gMinuit.GetParameter(4, dValue, dError)
     values[4]=dValue.value
     errors[4]=dError.value
     rc = gMinuit.GetParameter(5, dValue, dError)
     values[5]=dValue.value
     errors[5]=dError.value
     rc = gMinuit.GetParameter(6, dValue, dError)
     values[6]=dValue.value
     errors[6]=dError.value
     rc = gMinuit.GetParameter(7, dValue, dError)
     values[7]=dValue.value
     errors[7]=dError.value
     rc = gMinuit.GetParameter(8, dValue, dError)
     values[8]=dValue.value
     errors[8]=dError.value

     xFit = values[0]
     yFit = values[1]
     zFit = values[2]
     HNLPosFit =  ROOT.TVector3(xFit,yFit,zFit)
     xFitErr = errors[0]
     yFitErr = errors[1]
     zFitErr = errors[2]
     
     #fixme: mass from track reconstraction needed 
     m1 = self.PDG.GetParticle(PosDirCharge[t1]['pdgCode']).Mass()
     m2 = self.PDG.GetParticle(PosDirCharge[t2]['pdgCode']).Mass()
     
     #self.h['VxpullFit'].Fill( (mctrack.GetStartX()-xFit)/xFitErr )
     #self.h['VypullFit'].Fill( (mctrack.GetStartY()-yFit)/yFitErr )
     #self.h['VzpullFit'].Fill( (mctrack.GetStartZ()-zFit)/zFitErr )
     #self.h['dVxFit'].Fill( (mctrack.GetStartX()-xFit) )
     #self.h['dVyFit'].Fill( (mctrack.GetStartY()-yFit) )
     #self.h['dVzFit'].Fill( (mctrack.GetStartZ()-zFit) )
     
     def getP(fitValues,cov,m1,m2):
       a3=fitValues[3]
       a4=fitValues[4]
       a5=fitValues[5]
       a6=fitValues[6]
       a7=fitValues[7]
       a8=fitValues[8]
       px1 = a3/(a5*ROOT.TMath.Sqrt(1 + a3**2 + a4**2))
       py1 = a4/(a5*ROOT.TMath.Sqrt(1 + a3**2 + a4**2))
       pz1 = 1/(a5*ROOT.TMath.Sqrt(1 + a3**2 + a4**2))
       px2 = a6/(a8*ROOT.TMath.Sqrt(1 + a6**2 + a7**2))
       py2 = a7/(a8*ROOT.TMath.Sqrt(1 + a6**2 + a7**2))
       pz2 = 1/(a8*ROOT.TMath.Sqrt(1 + a6**2 + a7**2))
       Px = px1 + px2
       Py = py1 + py2
       Pz = pz1 + pz2
       E1 = ROOT.TMath.Sqrt(px1**2 + py1**2 + pz1**2 + m1**2)
       E2 = ROOT.TMath.Sqrt(px2**2 + py2**2 + pz2**2 + m2**2)
       M = ROOT.TMath.Sqrt(2*E1*E2+m1**2+m2**2-2*pz1*pz2*(1+a3*a6+a4*a7))
       MM = 2*M
       A5 = 1 + a3**2 + a4**2
       A8 = 1 + a6**2 + a7**2
       M_AtoP = ROOT.TMatrixD(4,6)
       MT_AtoP = ROOT.TMatrixD(6,4)
       covA = ROOT.TMatrixD(6,6)
       M_AtoP[0][0] = (1.-a3*a3/A5)/(a5*ROOT.TMath.Sqrt(A5))
       M_AtoP[0][1] = (-a3*a4/A5)/(a5*ROOT.TMath.Sqrt(A5))
       M_AtoP[0][2] = (-a3)/(a5*a5*ROOT.TMath.Sqrt(A5))
       M_AtoP[0][3] = (1.-a6*a6/A8)/(a8*ROOT.TMath.Sqrt(A8))
       M_AtoP[0][4] = (-a6*a7/A8)/(a8*ROOT.TMath.Sqrt(A8))
       M_AtoP[0][5] = (-a6)/(a8*a8*ROOT.TMath.Sqrt(A8))
       
       M_AtoP[1][0] = (-a3*a4/A5)/(a5*ROOT.TMath.Sqrt(A5))
       M_AtoP[1][1] = (1.-a4*a4/A5)/(a5*ROOT.TMath.Sqrt(A5))
       M_AtoP[1][2] = (-a4)/(a5*a5*ROOT.TMath.Sqrt(A5))
       M_AtoP[1][3] = (-a6*a7/A8)/(a8*ROOT.TMath.Sqrt(A8))
       M_AtoP[1][4] = (1.-a7*a7/A8)/(a8*ROOT.TMath.Sqrt(A8))
       M_AtoP[1][5] = (-a7)/(a8*a8*ROOT.TMath.Sqrt(A8))
       
       M_AtoP[2][0] = (-a3/A5)/(a5*ROOT.TMath.Sqrt(A5))
       M_AtoP[2][1] = (-a4/A5)/(a5*ROOT.TMath.Sqrt(A5))
       M_AtoP[2][2] = (-1.)/(a5*a5*ROOT.TMath.Sqrt(A5))
       M_AtoP[2][3] = (-a6/A8)/(a8*ROOT.TMath.Sqrt(A8))
       M_AtoP[2][4] = (-a7/A8)/(a8*ROOT.TMath.Sqrt(A8))
       M_AtoP[2][5] = (-1.)/(a8*a8*ROOT.TMath.Sqrt(A8))
       
       a5a8 = a5*a8*ROOT.TMath.Sqrt(A5)*ROOT.TMath.Sqrt(A8)
       
       M_AtoP[3][0] = (-2*a6/a5a8 + 2*a3*E2/(a5*a5*A5*E1))/MM
       M_AtoP[3][1] = (-2*a7/a5a8 + 2*a4*E2/(a5*a5*A5*E1))/MM
       M_AtoP[3][2] = (2*(1+a3*a6+a4*a7)/(a5*a5a8) - 2*(1.+a3*a3+a4*a4)*E2/(a5*a5*a5*A5*E1))/MM
       M_AtoP[3][3] = (-2*a3/a5a8 + 2*a6*E1/(a8*a8*A8*E2))/MM
       M_AtoP[3][4] = (-2*a4/a5a8 + 2*a7*E1/(a8*a8*A8*E2))/MM
       M_AtoP[3][5] = (2*(1+a3*a6+a4*a7)/(a8*a5a8) - 2*(1.+a6*a6+a7*a7)*E1/(a8*a8*a8*A8*E2))/MM
       
       for i in range(4):
         for j in range(6):
           MT_AtoP[j][i] = M_AtoP[i][j]
       
       for i in range(36):
         covA[i//6][i%6] = cov[i//6+3+(i%6+3)*9]
       
       tmp   = ROOT.TMatrixD(4,6)
       tmp.Mult(M_AtoP,covA)
       covP  = ROOT.TMatrixD(4,4)
       covP.Mult(tmp,MT_AtoP)
       P = ROOT.TLorentzVector()
       P.SetXYZM(Px,Py,Pz,M)
       return P,covP
      
     P,covP = getP(values,emat,m1,m2)
     #print "******************************************************************************* "
     
     #create ship particle
     #notes:
     #P-TLorentzVector of fitted HNL prticle
     #covP - covariance matrix of HNL four-vector (Px,Py,Pz,M)
     #HNLPosFit - fited position of HNL
     #covV - comariance matrix of the vtx position
     covV = array('d',[emat[0],emat[1],emat[2],emat[1+9],emat[2+9],emat[2+2*9]])
     covP = array('d',[covP[0][0],covP[0][1],covP[0][2],covP[0][3],covP[1][1],covP[1][2],covP[1][3],covP[2][2],covP[2][3],covP[3][3]])
          
# try to make it persistent
     vx = ROOT.TLorentzVector(HNLPosFit,0)  # time at vertex still needs to be evaluated from time of tracks and time of flight
     particle = ROOT.ShipParticle(9900015,0,-1,-1,t1,t2,P,vx)
     particle.SetCovV(covV)
     particle.SetCovP(covP)
     particle.SetDoca(doca)
     nParts   = particles.GetEntries()
     particles[nParts] = particle
     
     #self.h['dMFit'].Fill( (1.-P.M()) )
     #self.h['MpullFit'].Fill( (1.-P.M())/ROOT.TMath.Sqrt(covP[3][3]) )

  #self.h['N_Vtx'].Fill(hasVertex)

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
