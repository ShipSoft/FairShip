# example for accessing smeared hits and fitted tracks
import ROOT,os,sys,getopt
import rootUtils as ut
import shipunit as u
from ShipGeoConfig import ConfigRegistry
from rootpyPickler import Unpickler
from decorators import *
import shipRoot_conf
shipRoot_conf.configure()

debug = False
chi2CutOff  = 4.
PDG = ROOT.TDatabasePDG.Instance()
inputFile  = None
geoFile    = None
dy         = None
nEvents    = 9999999
fiducialCut = True
measCutFK = 25
measCutPR = 22
docaCut = 2.
try:
        opts, args = getopt.getopt(sys.argv[1:], "n:f:g:A:Y:i", ["nEvents=","geoFile="])
except getopt.GetoptError:
        # print help information and exit:
        print ' enter file name'
        sys.exit()
for o, a in opts:
        if o in ("-f",):
            inputFile = a
        if o in ("-g", "--geoFile",):
            geoFile = a
        if o in ("-Y",):
            dy = float(a)
        if o in ("-n", "--nEvents=",):
            nEvents = int(a)
eosship = ROOT.gSystem.Getenv("EOSSHIP")
if not inputFile.find(',')<0 :  
  sTree = ROOT.TChain("cbmsim")
  for x in inputFile.split(','):
   if x[0:4] == "/eos":
    sTree.AddFile(eosship+x)
   else: sTree.AddFile(x)
elif inputFile[0:4] == "/eos":
  eospath = eosship+inputFile
  f = ROOT.TFile.Open(eospath)
  sTree = f.cbmsim
else:
  f = ROOT.TFile(inputFile)
  sTree = f.cbmsim

# try to figure out which ecal geo to load
if not geoFile:
 geoFile = inputFile.replace('ship.','geofile_full.').replace('_rec.','.')
if geoFile[0:4] == "/eos":
  eospath = eosship+geoFile
  fgeo = ROOT.TFile.Open(eospath)
else:  
  fgeo = ROOT.TFile(geoFile)

# new geofile, load Shipgeo dictionary written by run_simScript.py
upkl    = Unpickler(fgeo)
ShipGeo = upkl.load('ShipGeo')
ecalGeoFile = ShipGeo.ecal.File
dy = ShipGeo.Yheight/u.m

# -----Create geometry----------------------------------------------
import shipDet_conf
run = ROOT.FairRunSim()
run.SetName("TGeant4")  # Transport engine
run.SetOutputFile(ROOT.TMemFile('output', 'recreate'))  # Output file
run.SetUserConfig("g4Config_basic.C") # geant4 transport not used, only needed for the mag field
rtdb = run.GetRuntimeDb()
# -----Create geometry----------------------------------------------
modules = shipDet_conf.configure(run,ShipGeo)

import geomGeant4
if hasattr(ShipGeo.Bfield,"fieldMap"):
  fieldMaker = geomGeant4.addVMCFields(ShipGeo, '', True, withVirtualMC = False)
else:
  print "no fieldmap given, geofile too old, not anymore support"
  exit(-1)
sGeo   = fgeo.FAIRGeom
geoMat =  ROOT.genfit.TGeoMaterialInterface()
ROOT.genfit.MaterialEffects.getInstance().init(geoMat)
bfield = ROOT.genfit.FairShipFields()
bfield.setField(fieldMaker.getGlobalField())
fM = ROOT.genfit.FieldManager.getInstance()
fM.init(bfield)

volDict = {}
i=0
for x in ROOT.gGeoManager.GetListOfVolumes():
 volDict[i]=x.GetName()
 i+=1

# prepare veto decisions
import shipVeto
veto = shipVeto.Task(sTree)
vetoDets={}
log={}
h = {}
ut.bookHist(h,'delPOverP','delP / P',400,0.,200.,100,-0.5,0.5)
ut.bookHist(h,'pullPOverPx','delPx / sigma',400,0.,200.,100,-3.,3.)
ut.bookHist(h,'pullPOverPy','delPy / sigma',400,0.,200.,100,-3.,3.)
ut.bookHist(h,'pullPOverPz','delPz / sigma',400,0.,200.,100,-3.,3.)
ut.bookHist(h,'delPOverP2','delP / P chi2/nmeas<'+str(chi2CutOff),400,0.,200.,100,-0.5,0.5)
ut.bookHist(h,'delPOverPz','delPz / Pz',400,0.,200.,100,-0.5,0.5)
ut.bookHist(h,'delPOverP2z','delPz / Pz chi2/nmeas<'+str(chi2CutOff),400,0.,200.,100,-0.5,0.5)
ut.bookHist(h,'chi2','chi2/nmeas after trackfit',100,0.,10.)
ut.bookHist(h,'prob','prob(chi2)',100,0.,1.)
ut.bookHist(h,'IP','Impact Parameter',100,0.,10.)
ut.bookHist(h,'Vzresol','Vz reco - true [cm]',100,-50.,50.)
ut.bookHist(h,'Vxresol','Vx reco - true [cm]',100,-10.,10.)
ut.bookHist(h,'Vyresol','Vy reco - true [cm]',100,-10.,10.)
ut.bookHist(h,'Vzpull','Vz pull',100,-5.,5.)
ut.bookHist(h,'Vxpull','Vx pull',100,-5.,5.)
ut.bookHist(h,'Vypull','Vy pull',100,-5.,5.)
ut.bookHist(h,'Doca','Doca between two tracks',100,0.,10.)
for x in ['','_pi0']:
 ut.bookHist(h,'IP0'+x,'Impact Parameter to target',100,0.,100.)
 ut.bookHist(h,'IP0/mass'+x,'Impact Parameter to target vs mass',100,0.,2.,100,0.,100.)
 ut.bookHist(h,'HNL'+x,'reconstructed Mass',500,0.,2.)
ut.bookHist(h,'HNLw','reconstructed Mass with weights',500,0.,2.)
ut.bookHist(h,'meas','number of measurements',40,-0.5,39.5)
ut.bookHist(h,'meas2','number of measurements, fitted track',40,-0.5,39.5)
ut.bookHist(h,'measVSchi2','number of measurements vs chi2/meas',40,-0.5,39.5,100,0.,10.)
ut.bookHist(h,'distu','distance to wire',100,0.,1.)
ut.bookHist(h,'distv','distance to wire',100,0.,1.)
ut.bookHist(h,'disty','distance to wire',100,0.,1.)
ut.bookHist(h,'meanhits','mean number of hits / track',50,-0.5,49.5)
ut.bookHist(h,'ecalClusters','x/y and energy',50,-3.,3.,50,-6.,6.)

ut.bookHist(h,'extrapTimeDetX','extrapolation to TimeDet X',100,-10.,10.)
ut.bookHist(h,'extrapTimeDetY','extrapolation to TimeDet Y',100,-10.,10.)

ut.bookHist(h,'oa','cos opening angle',100,0.999,1.)
# potential Veto detectors
ut.bookHist(h,'nrtracks','nr of tracks in signal selected',10,-0.5,9.5)
ut.bookHist(h,'nrSVT','nr of hits in SVT',10,-0.5,9.5)
ut.bookHist(h,'nrUVT','nr of hits in UVT',100,-0.5,99.5)
ut.bookHist(h,'nrSBT','nr of hits in SBT',100,-0.5,99.5)
ut.bookHist(h,'nrRPC','nr of hits in RPC',100,-0.5,99.5)

import TrackExtrapolateTool

def VertexError(t1,t2,PosDir,CovMat,scalFac):
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

from array import array
def dist2InnerWall(X,Y,Z):
  dist = 0
 # return distance to inner wall perpendicular to z-axis, if outside decayVolume return 0.
  node = sGeo.FindNode(X,Y,Z)
  if ShipGeo.tankDesign < 5:
     if not 'cave' in node.GetName(): return dist  # TP 
  else:
     if not 'decayVol' in node.GetName(): return dist
  start = array('d',[X,Y,Z])
  nsteps = 8
  dalpha = 2*ROOT.TMath.Pi()/nsteps
  rsq = X**2+Y**2
  minDistance = 100 *u.m
  for n in range(nsteps):
    alpha = n * dalpha
    sdir  = array('d',[ROOT.TMath.Sin(alpha),ROOT.TMath.Cos(alpha),0.])
    node = sGeo.InitTrack(start, sdir)
    nxt = sGeo.FindNextBoundary()
    if ShipGeo.tankDesign < 5 and nxt.GetName().find('I')<0: return 0    
    distance = sGeo.GetStep()
    if distance < minDistance  : minDistance = distance
  return minDistance

def isInFiducial(X,Y,Z):
   if Z > ShipGeo.TrackStation1.z : return False
   if Z < ShipGeo.vetoStation.z+100.*u.cm : return False
   # typical x,y Vx resolution for exclusive HNL decays 0.3cm,0.15cm (gaussian width)
   if dist2InnerWall(X,Y,Z)<5*u.cm: return False
   return True 
#
def ImpactParameter(point,tPos,tMom):
  t = 0
  if hasattr(tMom,'P'): P = tMom.P()
  else:                 P = tMom.Mag()
  for i in range(3):   t += tMom(i)/P*(point(i)-tPos(i)) 
  dist = 0
  for i in range(3):   dist += (point(i)-tPos(i)-t*tMom(i)/P)**2
  dist = ROOT.TMath.Sqrt(dist)
  return dist
#
def checkHNLorigin(sTree):
 flag = True
 if not fiducialCut: return flag
 flag = False
# only makes sense for signal == HNL
 hnlkey = -1
 for n in range(sTree.MCTrack.GetEntries()):
   mo = sTree.MCTrack[n].GetMotherId()
   if mo <0: continue
   if abs(sTree.MCTrack[mo].GetPdgCode()) == 9900015: 
       hnlkey = n
       break
 if hnlkey<0 : 
  ut.reportError("ShipAna: checkHNLorigin, no HNL found")
 else:
  # MCTrack after HNL should be first daughter
  theHNLVx = sTree.MCTrack[hnlkey]
  X,Y,Z =  theHNLVx.GetStartX(),theHNLVx.GetStartY(),theHNLVx.GetStartZ()
  if isInFiducial(X,Y,Z): flag = True
 return flag 

def checkFiducialVolume(sTree,tkey,dy):
# extrapolate track to middle of magnet and check if in decay volume
   inside = True
   if not fiducialCut: return True
   fT = sTree.FitTracks[tkey]
   rc,pos,mom = TrackExtrapolateTool.extrapolateToPlane(fT,ShipGeo.Bfield.z)
   if not rc: return False
   if not dist2InnerWall(pos.X(),pos.Y(),pos.Z())>0: return False
   return inside
def getPtruthFirst(sTree,mcPartKey):
   Ptruth,Ptruthx,Ptruthy,Ptruthz = -1.,-1.,-1.,-1.
   for ahit in sTree.strawtubesPoint:
     if ahit.GetTrackID() == mcPartKey:
        Ptruthx,Ptruthy,Ptruthz = ahit.GetPx(),ahit.GetPy(),ahit.GetPz()
        Ptruth  = ROOT.TMath.Sqrt(Ptruthx**2+Ptruthy**2+Ptruthz**2)
        break
   return Ptruth,Ptruthx,Ptruthy,Ptruthz

def access2SmearedHits():
 key = 0
 for ahit in ev.SmearedHits.GetObject():
   print ahit[0],ahit[1],ahit[2],ahit[3],ahit[4],ahit[5],ahit[6]
   # follow link to true MCHit
   mchit   = TrackingHits[key]
   mctrack =  MCTracks[mchit.GetTrackID()]
   print mchit.GetZ(),mctrack.GetP(),mctrack.GetPdgCode()
   key+=1

def myVertex(t1,t2,PosDir):
 # closest distance between two tracks
    # d = |pq . u x v|/|u x v|
   a = ROOT.TVector3(PosDir[t1][0](0) ,PosDir[t1][0](1), PosDir[t1][0](2))
   u = ROOT.TVector3(PosDir[t1][1](0),PosDir[t1][1](1),PosDir[t1][1](2))
   c = ROOT.TVector3(PosDir[t2][0](0) ,PosDir[t2][0](1), PosDir[t2][0](2))
   v = ROOT.TVector3(PosDir[t2][1](0),PosDir[t2][1](1),PosDir[t2][1](2))
   pq = a-c
   uCrossv = u.Cross(v)
   dist  = pq.Dot(uCrossv)/(uCrossv.Mag()+1E-8)
   # u.a - u.c + s*|u|**2 - u.v*t    = 0
   # v.a - v.c + s*v.u    - t*|v|**2 = 0
   E = u.Dot(a) - u.Dot(c) 
   F = v.Dot(a) - v.Dot(c) 
   A,B = u.Mag2(), -u.Dot(v) 
   C,D = u.Dot(v), -v.Mag2()
   t = -(C*E-A*F)/(B*C-A*D)
   X = c.x()+v.x()*t
   Y = c.y()+v.y()*t
   Z = c.z()+v.z()*t
   return X,Y,Z,abs(dist)
def  RedoVertexing(t1,t2):    
     PosDir = {} 
     for tr in [t1,t2]:
      xx  = sTree.FitTracks[tr].getFittedState()
      PosDir[tr] = [xx.getPos(),xx.getDir()]
     xv,yv,zv,doca = myVertex(t1,t2,PosDir)
# as we have learned, need iterative procedure
     dz = 99999.
     reps,states,newPosDir = {},{},{}
     parallelToZ = ROOT.TVector3(0., 0., 1.)
     rc = True 
     step = 0
     while dz > 0.1:
      zBefore = zv
      newPos = ROOT.TVector3(xv,yv,zv)
     # make a new rep for track 1,2
      for tr in [t1,t2]:     
       xx = sTree.FitTracks[tr].getFittedState()
       reps[tr]   = ROOT.genfit.RKTrackRep(xx.getPDG())
       states[tr] = ROOT.genfit.StateOnPlane(reps[tr])
       reps[tr].setPosMom(states[tr],xx.getPos(),xx.getMom())
       try:
        reps[tr].extrapolateToPoint(states[tr], newPos, False)
       except:
        print 'SHiPAna: extrapolation did not worked'
        rc = False  
        break
       newPosDir[tr] = [reps[tr].getPos(states[tr]),reps[tr].getDir(states[tr])]
      if not rc: break
      xv,yv,zv,doca = myVertex(t1,t2,newPosDir)
      dz = abs(zBefore-zv)
      step+=1
      if step > 10:  
         print 'abort iteration, too many steps, pos=',xv,yv,zv,' doca=',doca,'z before and dz',zBefore,dz
         rc = False
         break 
     if not rc: return xv,yv,zv,doca,-1 # extrapolation failed, makes no sense to continue
     LV={}
     for tr in [t1,t2]:       
      mom = reps[tr].getMom(states[tr])
      pid = abs(states[tr].getPDG()) 
      if pid == 2212: pid = 211
      mass = PDG.GetParticle(pid).Mass()
      E = ROOT.TMath.Sqrt( mass*mass + mom.Mag2() )
      LV[tr] = ROOT.TLorentzVector()
      LV[tr].SetPxPyPzE(mom.x(),mom.y(),mom.z(),E)
     HNLMom = LV[t1]+LV[t2]
     return xv,yv,zv,doca,HNLMom
def fitSingleGauss(x,ba=None,be=None):
    name    = 'myGauss_'+x 
    myGauss = h[x].GetListOfFunctions().FindObject(name)
    if not myGauss:
       if not ba : ba = h[x].GetBinCenter(1) 
       if not be : be = h[x].GetBinCenter(h[x].GetNbinsX()) 
       bw    = h[x].GetBinWidth(1) 
       mean  = h[x].GetMean()
       sigma = h[x].GetRMS()
       norm  = h[x].GetEntries()*0.3
       myGauss = ROOT.TF1(name,'[0]*'+str(bw)+'/([2]*sqrt(2*pi))*exp(-0.5*((x-[1])/[2])**2)+[3]',4)
       myGauss.SetParameter(0,norm)
       myGauss.SetParameter(1,mean)
       myGauss.SetParameter(2,sigma)
       myGauss.SetParameter(3,1.)
       myGauss.SetParName(0,'Signal')
       myGauss.SetParName(1,'Mean')
       myGauss.SetParName(2,'Sigma')
       myGauss.SetParName(3,'bckgr')
    h[x].Fit(myGauss,'','',ba,be) 

def match2HNL(p):
    matched = False
    hnlKey  = []
    for t in [p.GetDaughter(0),p.GetDaughter(1)]: 
      mcp = sTree.fitTrack2MC[t]
      while mcp > -0.5:
        mo = sTree.MCTrack[mcp]
        if abs(mo.GetPdgCode()) == 9900015:
           hnlKey.append(mcp)
           break  
        mcp = mo.GetMotherId()
    if len(hnlKey) == 2: 
       if hnlKey[0]==hnlKey[1]: matched = True
    return matched
def ecalCluster2MC(aClus):
 # return MC track most contributing, and its fraction of energy
  trackid    = ROOT.Long()
  energy_dep = ROOT.Double()
  mcLink = {}
  for i in range( aClus.Size() ):
    mccell = ecalStructure.GetHitCell(aClus.CellNum(i))  # Get i'th cell of the cluster.
    for n in range( mccell.TrackEnergySize()):
      mccell.GetTrackEnergySlow(n, trackid, energy_dep)
      if not abs(trackid)<sTree.MCTrack.GetEntries(): tid = -1
      else: tid = int(trackid)
      if not mcLink.has_key(tid): mcLink[tid]=0
      mcLink[tid]+=energy_dep
# find trackid most contributing
  eMax,mMax = 0,-1
  for m in mcLink:
     if mcLink[m]>eMax:
        eMax = mcLink[m]
        mMax = m
  return mMax,eMax/aClus.Energy()

def makePlots():
   ut.bookCanvas(h,key='ecalanalysis',title='cluster map',nx=800,ny=600,cx=1,cy=1)
   cv = h['ecalanalysis'].cd(1)
   h['ecalClusters'].Draw('colz')
   ut.bookCanvas(h,key='ecalCluster2Track',title='Ecal cluster distances to track impact',nx=1600,ny=800,cx=4,cy=2)
   if h.has_key("ecalReconstructed_dist_mu+"):
    cv = h['ecalCluster2Track'].cd(1)
    h['ecalReconstructed_distx_mu+'].Draw()
    cv = h['ecalCluster2Track'].cd(2)
    h['ecalReconstructed_disty_mu+'].Draw()
   if h.has_key("ecalReconstructed_dist_pi+"):
    cv = h['ecalCluster2Track'].cd(3)
    h['ecalReconstructed_distx_pi+'].Draw()
    cv = h['ecalCluster2Track'].cd(4)
    h['ecalReconstructed_disty_pi+'].Draw()
   if h.has_key("ecalReconstructed_dist_mu-"):
    cv = h['ecalCluster2Track'].cd(5)
    h['ecalReconstructed_distx_mu-'].Draw()
    cv = h['ecalCluster2Track'].cd(6)
    h['ecalReconstructed_disty_mu-'].Draw()
   if h.has_key("ecalReconstructed_dist_pi-"):
    cv = h['ecalCluster2Track'].cd(7)
    h['ecalReconstructed_distx_pi-'].Draw()
    cv = h['ecalCluster2Track'].cd(8)
    h['ecalReconstructed_disty_pi-'].Draw()

   ut.bookCanvas(h,key='strawanalysis',title='Distance to wire and mean nr of hits',nx=1200,ny=600,cx=3,cy=1)
   cv = h['strawanalysis'].cd(1)
   h['disty'].Draw()
   h['distu'].Draw('same')
   h['distv'].Draw('same')
   cv = h['strawanalysis'].cd(2)
   h['meanhits'].Draw()
   cv = h['strawanalysis'].cd(3)
   h['meas2'].Draw()
   ut.bookCanvas(h,key='fitresults',title='Fit Results',nx=1600,ny=1200,cx=2,cy=2)
   cv = h['fitresults'].cd(1)
   h['delPOverPz'].Draw('box')
   cv = h['fitresults'].cd(2)
   cv.SetLogy(1)
   h['prob'].Draw()
   cv = h['fitresults'].cd(3)
   h['delPOverPz_proj'] = h['delPOverPz'].ProjectionY()
   ROOT.gStyle.SetOptFit(11111)
   h['delPOverPz_proj'].Draw()
   h['delPOverPz_proj'].Fit('gaus')
   cv = h['fitresults'].cd(4)
   h['delPOverP2z_proj'] = h['delPOverP2z'].ProjectionY()
   h['delPOverP2z_proj'].Draw()
   fitSingleGauss('delPOverP2z_proj')
   h['fitresults'].Print('fitresults.gif')
   for x in ['','_pi0']:
    ut.bookCanvas(h,key='fitresults2'+x,title='Fit Results '+x,nx=1600,ny=1200,cx=2,cy=2)
    cv = h['fitresults2'+x].cd(1)
    if x=='': 
     h['Doca'].SetXTitle('closest distance between 2 tracks   [cm]')
     h['Doca'].SetYTitle('N/1mm')
     h['Doca'].Draw()
    else:
     h['pi0Mass'].SetXTitle('#gamma #gamma invariant mass   [GeV/c^{2}]')
     h['pi0Mass'].SetYTitle('N/'+str(int(h['pi0Mass'].GetBinWidth(1)*1000))+'MeV')
     h['pi0Mass'].Draw()
     fitResult = h['pi0Mass'].Fit('gaus','S','',0.08,0.19)
    cv = h['fitresults2'+x].cd(2)
    h['IP0'+x].SetXTitle('impact parameter to p-target   [cm]')
    h['IP0'+x].SetYTitle('N/1cm')
    h['IP0'+x].Draw()
    cv = h['fitresults2'+x].cd(3)
    h['HNL'+x].SetXTitle('inv. mass  [GeV/c^{2}]')
    h['HNL'+x].SetYTitle('N/4MeV/c2')
    h['HNL'+x].Draw()
    fitSingleGauss('HNL'+x,0.9,1.1)
    cv = h['fitresults2'+x].cd(4)
    h['IP0/mass'+x].SetXTitle('inv. mass  [GeV/c^{2}]')
    h['IP0/mass'+x].SetYTitle('IP [cm]')
    h['IP0/mass'+x].Draw('colz')
    h['fitresults2'+x].Print('fitresults2'+x+'.gif')
   ut.bookCanvas(h,key='vxpulls',title='Vertex resol and pulls',nx=1600,ny=1200,cx=3,cy=2)
   cv = h['vxpulls'].cd(4)
   h['Vxpull'].Draw()
   cv = h['vxpulls'].cd(5)
   h['Vypull'].Draw()
   cv = h['vxpulls'].cd(6)
   h['Vzpull'].Draw()
   cv = h['vxpulls'].cd(1)
   h['Vxresol'].Draw()
   cv = h['vxpulls'].cd(2)
   h['Vyresol'].Draw()
   cv = h['vxpulls'].cd(3)
   h['Vzresol'].Draw()
   ut.bookCanvas(h,key='trpulls',title='momentum pulls',nx=1600,ny=600,cx=3,cy=1)
   cv = h['trpulls'].cd(1)
   h['pullPOverPx_proj']=h['pullPOverPx'].ProjectionY()
   h['pullPOverPx_proj'].Draw()
   cv = h['trpulls'].cd(2)
   h['pullPOverPy_proj']=h['pullPOverPy'].ProjectionY()
   h['pullPOverPy_proj'].Draw()
   cv = h['trpulls'].cd(3)
   h['pullPOverPz_proj']=h['pullPOverPz'].ProjectionY()
   h['pullPOverPz_proj'].Draw()
   ut.bookCanvas(h,key='vetodecisions',title='Veto Detectors',nx=1600,ny=600,cx=5,cy=1)
   cv = h['vetodecisions'].cd(1)
   cv.SetLogy(1)
   h['nrtracks'].Draw()
   cv = h['vetodecisions'].cd(2)
   cv.SetLogy(1)
   h['nrSVT'].Draw()
   cv = h['vetodecisions'].cd(3)
   cv.SetLogy(1)
   h['nrUVT'].Draw()
   cv = h['vetodecisions'].cd(4)
   cv.SetLogy(1)
   h['nrSBT'].Draw()
   cv = h['vetodecisions'].cd(5)
   cv.SetLogy(1)
   h['nrRPC'].Draw()
#
   print 'finished making plots'
# calculate z front face of ecal, needed later
top = ROOT.gGeoManager.GetTopVolume()
ecal = None
if top.GetNode('Ecal_1'):
 ecal = top.GetNode('Ecal_1')
 z_ecal = ecal.GetMatrix().GetTranslation()[2]
elif top.GetNode('SplitCalDetector_1'):
 ecal = top.GetNode('SplitCalDetector_1')
 z_ecal = ecal.GetMatrix().GetTranslation()[2]

# start event loop
def myEventLoop(n):
  global ecalReconstructed
  rc = sTree.GetEntry(n)
# check if tracks are made from real pattern recognition
  measCut = measCutFK
  if sTree.GetBranch("FitTracks_PR"):    
    sTree.FitTracks = sTree.FitTracks_PR
    measCut = measCutPR
  if sTree.GetBranch("fitTrack2MC_PR"):  sTree.fitTrack2MC = sTree.fitTrack2MC_PR
  if sTree.GetBranch("Particles_PR"):    sTree.Particles   = sTree.Particles_PR
  if not checkHNLorigin(sTree): return
  if not sTree.MCTrack.GetEntries()>1: wg = 1.
  else:   wg = sTree.MCTrack[1].GetWeight()
  if not wg>0.: wg=1.

# make some ecal cluster analysis if exist
  if hasattr(sTree,"EcalClusters"):
   if calReco:  ecalReconstructed.Delete()
   else:        ecalReconstructed = sTree.EcalReconstructed
   for x in caloTasks: 
    if x.GetName() == 'ecalFiller': x.Exec('start',sTree.EcalPointLite)
    elif x.GetName() == 'ecalMatch':  x.Exec('start',ecalReconstructed,sTree.MCTrack)
    else : x.Exec('start')
   for aClus in ecalReconstructed:
    mMax = aClus.MCTrack()
    if mMax <0 or mMax > sTree.MCTrack.GetEntries(): 
     aP = None # this should never happen, otherwise the ECAL MC matching has a bug
    else: aP = sTree.MCTrack[mMax]
    if aP:    
      tmp = PDG.GetParticle(aP.GetPdgCode())
      if tmp: pName = 'ecalReconstructed_'+tmp.GetName()
      else: pName = 'ecalReconstructed_'+str(aP.GetPdgCode())
    else:
      pName = 'ecalReconstructed_unknown' 
    if not h.has_key(pName): 
      ut.bookHist(h,pName,'x/y and energy for '+pName.split('_')[1],50,-3.,3.,50,-6.,6.)
    rc = h[pName].Fill(aClus.X()/u.m,aClus.Y()/u.m,aClus.RecoE()/u.GeV)
# look at distance to tracks 
    for fT in sTree.FitTracks:
     rc,pos,mom = TrackExtrapolateTool.extrapolateToPlane(fT,z_ecal)
     if rc:
      pdgcode = fT.getFittedState().getPDG()
      tmp = PDG.GetParticle(pdgcode)
      if tmp: tName = 'ecalReconstructed_dist_'+tmp.GetName()
      else: tName = 'ecalReconstructed_dist_'+str(aP.GetPdgCode())
      if not h.has_key(tName): 
       p = tName.split('dist_')[1]
       ut.bookHist(h,tName,'Ecal cluster distance t0 '+p,100,0.,100.*u.cm)
       ut.bookHist(h,tName.replace('dist','distx'),'Ecal cluster distance to '+p+' in X ',100,-50.*u.cm,50.*u.cm)
       ut.bookHist(h,tName.replace('dist','disty'),'Ecal cluster distance to '+p+' in Y ',100,-50.*u.cm,50.*u.cm)
      dist = ROOT.TMath.Sqrt( (aClus.X()-pos.X())**2+(aClus.Y()-pos.Y())**2 )
      rc = h[tName].Fill(dist)
      rc = h[tName.replace('dist','distx')].Fill( aClus.X()-pos.X() )
      rc = h[tName.replace('dist','disty')].Fill( aClus.Y()-pos.Y() )
# compare with old method
   for aClus in sTree.EcalClusters:
     rc = h['ecalClusters'].Fill(aClus.X()/u.m,aClus.Y()/u.m,aClus.Energy()/u.GeV)
     mMax,frac = ecalCluster2MC(aClus)
# return MC track most contributing, and its fraction of energy
     if mMax>0:    
      aP = sTree.MCTrack[mMax]   
      tmp = PDG.GetParticle(aP.GetPdgCode())
      if tmp: pName = 'ecalClusters_'+tmp.GetName()
      else: pName = 'ecalClusters_'+str(aP.GetPdgCode())
     else:
      pName = 'ecalClusters_unknown' 
     if not h.has_key(pName): ut.bookHist(h,pName,'x/y and energy for '+pName.split('_')[1],50,-3.,3.,50,-6.,6.)
     rc = h[pName].Fill(aClus.X()/u.m,aClus.Y()/u.m,aClus.Energy()/u.GeV)
     
# make some straw hit analysis
  hitlist = {}
  for ahit in sTree.strawtubesPoint:
     detID = ahit.GetDetectorID()
     top = ROOT.TVector3()
     bot = ROOT.TVector3()
     modules["Strawtubes"].StrawEndPoints(detID,bot,top)
     dw  = ahit.dist2Wire()
     if detID < 50000000 : 
      if abs(top.y())==abs(bot.y()): h['disty'].Fill(dw)
      if abs(top.y())>abs(bot.y()): h['distu'].Fill(dw)
      if abs(top.y())<abs(bot.y()): h['distv'].Fill(dw)
#
     trID = ahit.GetTrackID()
     if not trID < 0 :
      if hitlist.has_key(trID):  hitlist[trID]+=1
      else:  hitlist[trID]=1
  for tr in hitlist:  h['meanhits'].Fill(hitlist[tr])
  key = -1
  fittedTracks = {}
  for atrack in sTree.FitTracks:
   key+=1
# kill tracks outside fiducial volume
   if not checkFiducialVolume(sTree,key,dy): continue
   fitStatus   = atrack.getFitStatus()
   nmeas = fitStatus.getNdf()
   h['meas'].Fill(nmeas)
   if not fitStatus.isFitConverged() : continue
   h['meas2'].Fill(nmeas)
   if nmeas < measCut: continue
   fittedTracks[key] = atrack
# needs different study why fit has not converged, continue with fitted tracks
   rchi2 = fitStatus.getChi2()
   prob = ROOT.TMath.Prob(rchi2,int(nmeas))
   h['prob'].Fill(prob)
   chi2 = rchi2/nmeas
   fittedState = atrack.getFittedState()
   h['chi2'].Fill(chi2,wg)
   h['measVSchi2'].Fill(atrack.getNumPoints(),chi2)
   P = fittedState.getMomMag()
   Px,Py,Pz = fittedState.getMom().x(),fittedState.getMom().y(),fittedState.getMom().z()
   cov = fittedState.get6DCov()
   if len(sTree.fitTrack2MC)-1<key: continue
   mcPartKey = sTree.fitTrack2MC[key]
   mcPart    = sTree.MCTrack[mcPartKey]
   if not mcPart : continue
   Ptruth_start     = mcPart.GetP()
   Ptruthz_start    = mcPart.GetPz()
   # get p truth from first strawpoint
   Ptruth,Ptruthx,Ptruthy,Ptruthz = getPtruthFirst(sTree,mcPartKey)
   delPOverP = (Ptruth - P)/Ptruth
   h['delPOverP'].Fill(Ptruth,delPOverP)
   delPOverPz = (1./Ptruthz - 1./Pz) * Ptruthz
   h['pullPOverPx'].Fill( Ptruth,(Ptruthx-Px)/ROOT.TMath.Sqrt(cov[3][3]) )   
   h['pullPOverPy'].Fill( Ptruth,(Ptruthy-Py)/ROOT.TMath.Sqrt(cov[4][4]) )   
   h['pullPOverPz'].Fill( Ptruth,(Ptruthz-Pz)/ROOT.TMath.Sqrt(cov[5][5]) )   
   h['delPOverPz'].Fill(Ptruthz,delPOverPz)
   if chi2>chi2CutOff: continue
   h['delPOverP2'].Fill(Ptruth,delPOverP)
   h['delPOverP2z'].Fill(Ptruth,delPOverPz)
# try measure impact parameter
   trackDir = fittedState.getDir()
   trackPos = fittedState.getPos()
   vx = ROOT.TVector3()
   mcPart.GetStartVertex(vx)
   t = 0
   for i in range(3):   t += trackDir(i)*(vx(i)-trackPos(i)) 
   dist = 0
   for i in range(3):   dist += (vx(i)-trackPos(i)-t*trackDir(i))**2
   dist = ROOT.TMath.Sqrt(dist)
   h['IP'].Fill(dist) 
# ---
# loop over particles, 2-track combinations
  for HNL in sTree.Particles:
    t1,t2 = HNL.GetDaughter(0),HNL.GetDaughter(1) 
# kill tracks outside fiducial volume, if enabled
    if not checkFiducialVolume(sTree,t1,dy) or not checkFiducialVolume(sTree,t2,dy) : continue
    checkMeasurements = True
# cut on nDOF
    for tr in [t1,t2]:
      fitStatus  = sTree.FitTracks[tr].getFitStatus()
      nmeas = fitStatus.getNdf()
      if nmeas < measCut: checkMeasurements = False
    if not checkMeasurements: continue
# check mc matching 
    if not match2HNL(HNL): continue
    HNLPos = ROOT.TLorentzVector()
    HNL.ProductionVertex(HNLPos)
    HNLMom = ROOT.TLorentzVector()
    HNL.Momentum(HNLMom)
# check if DOCA info exist
    if hasattr(HNL,"GetDoca"):
      doca  =  HNL.GetDoca()
    elif HNL.GetMother(1)==99 :
      doca  =  HNLPos.T()
    else:
# redo doca calculation
     xv,yv,zv,doca,HNLMom  = RedoVertexing(t1,t2)
     if HNLMom == -1: continue
 # check if decay inside decay volume
    if not isInFiducial(HNLPos.X(),HNLPos.Y(),HNLPos.Z()): continue  
    h['Doca'].Fill(doca) 
    if  doca > docaCut : continue
    tr = ROOT.TVector3(0,0,ShipGeo.target.z0)

# look for pi0
    for pi0 in pi0Reco.findPi0(sTree,HNLPos):
       rc = h['pi0Mass'].Fill(pi0.M())
       if abs(pi0.M()-0.135)>0.02: continue 
# could also be used for eta, by changing cut
       HNLwithPi0 =  HNLMom + pi0
       dist = ImpactParameter(tr,HNLPos,HNLwithPi0)
       mass = HNLwithPi0.M()
       h['IP0_pi0'].Fill(dist)  
       h['IP0/mass_pi0'].Fill(mass,dist)
       h['HNL_pi0'].Fill(mass)

    dist = ImpactParameter(tr,HNLPos,HNLMom)
    mass = HNLMom.M()
    h['IP0'].Fill(dist)  
    h['IP0/mass'].Fill(mass,dist)
    h['HNL'].Fill(mass)
    h['HNLw'].Fill(mass,wg)
#
    vetoDets['SBT'] = veto.SBT_decision()
    vetoDets['SVT'] = veto.SVT_decision()
    vetoDets['UVT'] = veto.UVT_decision()
    vetoDets['RPC'] = veto.RPC_decision()
    vetoDets['TRA'] = veto.Track_decision()
    h['nrtracks'].Fill(vetoDets['TRA'][2])
    h['nrSVT'].Fill(vetoDets['SVT'][2])
    h['nrUVT'].Fill(vetoDets['UVT'][2])
    h['nrSBT'].Fill(vetoDets['SBT'][2])
    h['nrRPC'].Fill(vetoDets['RPC'][2])
#   HNL true
    mctrack = sTree.MCTrack[sTree.fitTrack2MC[t1]]
    h['Vzresol'].Fill( (mctrack.GetStartZ()-HNLPos.Z())/u.cm )
    h['Vxresol'].Fill( (mctrack.GetStartX()-HNLPos.X())/u.cm )
    h['Vyresol'].Fill( (mctrack.GetStartY()-HNLPos.Y())/u.cm )
    PosDir,newPosDir,CovMat,scalFac = {},{},{},{}
# opening angle at vertex
    newPos = ROOT.TVector3(HNLPos.X(),HNLPos.Y(),HNLPos.Z())
    st1,st2 = sTree.FitTracks[t1].getFittedState(),sTree.FitTracks[t2].getFittedState()
    PosDir[t1] = {'position':st1.getPos(),'direction':st1.getDir(),'momentum':st1.getMom()}
    PosDir[t2] = {'position':st2.getPos(),'direction':st2.getDir(),'momentum':st2.getMom()}
    CovMat[t1] = st1.get6DCov() 
    CovMat[t2] = st2.get6DCov() 
    rep1,rep2 = ROOT.genfit.RKTrackRep(st1.getPDG()),ROOT.genfit.RKTrackRep(st2.getPDG())  
    state1,state2 = ROOT.genfit.StateOnPlane(rep1),ROOT.genfit.StateOnPlane(rep2)
    rep1.setPosMom(state1,st1.getPos(),st1.getMom())
    rep2.setPosMom(state2,st2.getPos(),st2.getMom())
    try:
     rep1.extrapolateToPoint(state1, newPos, False)
     rep2.extrapolateToPoint(state2, newPos, False)
     mom1,mom2 = rep1.getMom(state1),rep2.getMom(state2)
    except:
     mom1,mom2 = st1.getMom(),st2.getMom()
    newPosDir[t1] = {'position':rep1.getPos(state1),'direction':rep1.getDir(state1),'momentum':mom1}
    newPosDir[t2] = {'position':rep2.getPos(state2),'direction':rep2.getDir(state2),'momentum':mom2}
    oa = mom1.Dot(mom2)/(mom1.Mag()*mom2.Mag()) 
    h['oa'].Fill(oa)
#
    covX = HNL.GetCovV()
    dist = HNL.GetDoca()
    h['Vzpull'].Fill( (mctrack.GetStartZ()-HNLPos.Z())/ROOT.TMath.Sqrt(covX[2][2]) )
    h['Vxpull'].Fill( (mctrack.GetStartX()-HNLPos.X())/ROOT.TMath.Sqrt(covX[0][0]) )
    h['Vypull'].Fill( (mctrack.GetStartY()-HNLPos.Y())/ROOT.TMath.Sqrt(covX[1][1]) )

# check extrapolation to TimeDet if exists
  if hasattr(ShipGeo,"TimeDet"):
   for fT in sTree.FitTracks:
     rc,pos,mom = TrackExtrapolateTool.extrapolateToPlane(fT,ShipGeo.TimeDet.z)
     if rc:
      for aPoint in sTree.TimeDetPoint:
       h['extrapTimeDetX'].Fill(pos.X()-aPoint.GetX())
       h['extrapTimeDetY'].Fill(pos.Y()-aPoint.GetY())
#
def HNLKinematics():
 HNLorigin={}
 ut.bookHist(h,'HNLmomNoW','momentum unweighted',100,0.,300.)
 ut.bookHist(h,'HNLmom','momentum',100,0.,300.)
 ut.bookHist(h,'HNLPtNoW','Pt unweighted',100,0.,10.)
 ut.bookHist(h,'HNLPt','Pt',100,0.,10.)
 ut.bookHist(h,'HNLmom_recTracks','momentum',100,0.,300.)
 ut.bookHist(h,'HNLmomNoW_recTracks','momentum unweighted',100,0.,300.)
 for n in range(sTree.GetEntries()): 
  rc = sTree.GetEntry(n)
  for hnlkey in [1,2]: 
   if abs(sTree.MCTrack[hnlkey].GetPdgCode()) == 9900015: 
    theHNL = sTree.MCTrack[hnlkey]
    wg = theHNL.GetWeight()
    if not wg>0.: wg=1.
    idMother = abs(sTree.MCTrack[hnlkey-1].GetPdgCode())
    if not HNLorigin.has_key(idMother): HNLorigin[idMother]=0
    HNLorigin[idMother]+=wg
    P = theHNL.GetP()
    Pt = theHNL.GetPt()
    h['HNLmom'].Fill(P,wg) 
    h['HNLmomNoW'].Fill(P) 
    h['HNLPt'].Fill(Pt,wg) 
    h['HNLPtNoW'].Fill(Pt) 
    for HNL in sTree.Particles:
     t1,t2 = HNL.GetDaughter(0),HNL.GetDaughter(1) 
     for tr in [t1,t2]:
      xx  = sTree.FitTracks[tr].getFittedState()
      Prec = xx.getMom().Mag()
      h['HNLmom_recTracks'].Fill(Prec,wg) 
      h['HNLmomNoW_recTracks'].Fill(Prec)
 theSum = 0
 for x in HNLorigin: theSum+=HNLorigin[x]   
 for x in HNLorigin: print "%4i : %5.4F relative fraction: %5.4F "%(x,HNLorigin[x],HNLorigin[x]/theSum)
#
# initialize ecalStructure
caloTasks = []
calReco = False
sTree.GetEvent(0)
if ecal:
 ecalGeo = ecalGeoFile+'z'+str(ShipGeo.ecal.z)+".geo"
 if not ecalGeo in os.listdir(os.environ["FAIRSHIP"]+"/geometry"): shipDet_conf.makeEcalGeoFile(ShipGeo.ecal.z,ShipGeo.ecal.File)
 ecalFiller = ROOT.ecalStructureFiller("ecalFiller", 0,ecalGeo)
 ecalFiller.SetUseMCPoints(ROOT.kTRUE)
 ecalFiller.StoreTrackInformation()
 ecalStructure = ecalFiller.InitPython(sTree.EcalPointLite)
 caloTasks.append(ecalFiller)
 
 if hasattr(sTree,"EcalReconstructed"):
  calReco = False
  ecalReconstructed = sTree.EcalReconstructed
 else:
  calReco = True
  print "setup calo reconstruction of ecalReconstructed objects"
# Calorimeter reconstruction
 #GeV -> ADC conversion
  ecalDigi=ROOT.ecalDigi("ecalDigi",0)
  ecalPrepare=ROOT.ecalPrepare("ecalPrepare",0)
  ecalStructure     = ecalFiller.InitPython(sTree.EcalPointLite)
  ecalDigi.InitPython(ecalStructure)
  caloTasks.append(ecalDigi)
  ecalPrepare.InitPython(ecalStructure)
  caloTasks.append(ecalPrepare)
 # Cluster calibration
  ecalClusterCalib=ROOT.ecalClusterCalibration("ecalClusterCalibration", 0)
 #4x4 cm cells
  ecalCl3PhS=ROOT.TFormula("ecalCl3PhS", "[0]+x*([1]+x*([2]+x*[3]))")
  ecalCl3PhS.SetParameters(6.77797e-04, 5.75385e+00, 3.42690e-03, -1.16383e-04)
  ecalClusterCalib.SetStraightCalibration(3, ecalCl3PhS)
  ecalCl3Ph=ROOT.TFormula("ecalCl3Ph", "[0]+x*([1]+x*([2]+x*[3]))+[4]*x*y+[5]*x*y*y")
  ecalCl3Ph.SetParameters(0.000750975, 5.7552, 0.00282783, -8.0025e-05, -0.000823651, 0.000111561)
  ecalClusterCalib.SetCalibration(3, ecalCl3Ph)
#6x6 cm cells
  ecalCl2PhS=ROOT.TFormula("ecalCl2PhS", "[0]+x*([1]+x*([2]+x*[3]))")
  ecalCl2PhS.SetParameters(8.14724e-04, 5.67428e+00, 3.39030e-03, -1.28388e-04)
  ecalClusterCalib.SetStraightCalibration(2, ecalCl2PhS)
  ecalCl2Ph=ROOT.TFormula("ecalCl2Ph", "[0]+x*([1]+x*([2]+x*[3]))+[4]*x*y+[5]*x*y*y")
  ecalCl2Ph.SetParameters(0.000948095, 5.67471, 0.00339177, -0.000122629, -0.000169109, 8.33448e-06)
  ecalClusterCalib.SetCalibration(2, ecalCl2Ph)
  caloTasks.append(ecalClusterCalib)
  ecalReco=ROOT.ecalReco('ecalReco',0)
  caloTasks.append(ecalReco)
# Match reco to MC
  ecalMatch=ROOT.ecalMatch('ecalMatch',0)
  caloTasks.append(ecalMatch)
  ecalCalib         = ecalClusterCalib.InitPython()
  ecalReconstructed = ecalReco.InitPython(sTree.EcalClusters, ecalStructure, ecalCalib)
  ecalMatch.InitPython(ecalStructure, ecalReconstructed, sTree.MCTrack)

nEvents = min(sTree.GetEntries(),nEvents)

import pi0Reco
ut.bookHist(h,'pi0Mass','gamma gamma inv mass',100,0.,0.5)

for n in range(nEvents): 
 myEventLoop(n)
 sTree.FitTracks.Delete()
makePlots()
# output histograms
hfile = inputFile.split(',')[0].replace('_rec','_ana')
if hfile[0:4] == "/eos" or not inputFile.find(',')<0:
# do not write to eos, write to local directory 
  tmp = hfile.split('/')
  hfile = tmp[len(tmp)-1] 
ROOT.gROOT.cd()
ut.writeHists(h,hfile)


