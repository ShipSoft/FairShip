# example for accessing smeared hits and fitted tracks
import ROOT,os,sys,getopt
import rootUtils as ut
import shipunit as u
from ShipGeoConfig import ConfigRegistry
chi2CutOff  = 4.
PDG = ROOT.TDatabasePDG.Instance()
inputFile  = None
geoFile    = None
dy         = None
nEvents    = 99999
fiducialCut = False
measCut = 25
docaCut = 2.
try:
        opts, args = getopt.getopt(sys.argv[1:], "n:f:g:A:Y:i", ["nEvents=","geoFile="])
except getopt.GetoptError:
        # print help information and exit:
        print ' enter file name'
        sys.exit()
for o, a in opts:
        if o in ("-f"):
            inputFile = a
        if o in ("-g", "--geoFile"):
            geoFile = a
        if o in ("-Y"): 
            dy = float(a)
        if o in ("-n", "--nEvents="):
            nEvents = int(a)

if not dy:
  # try to extract from input file name
  tmp = inputFile.split('.')
  try:
    dy = float( tmp[1]+'.'+tmp[2] )
  except:
    dy = None
else:
 inputFile = 'ship.'+str(dy)+'.Pythia8-TGeant4_rec.root'
  
f     = ROOT.TFile(inputFile)
sTree = f.cbmsim

# try to figure out which ecal geo to load
if not geoFile:
 geoFile = inputFile.replace('ship.','geofile_full.').replace('_rec.','.')
fgeo = ROOT.TFile(geoFile)
sGeo = fgeo.FAIRGeom
if sGeo.GetVolume('EcalModule3') :  ecalGeoFile = "ecal_ellipse6x12m2.geo"
else: ecalGeoFile = "ecal_ellipse5x10m2.geo" 
fgeo.Close()
ROOT.gGeoManager.Delete()
print 'found ecal geo for ',ecalGeoFile

# init geometry and mag. field
ShipGeo = ConfigRegistry.loadpy("$FAIRSHIP/geometry/geometry_config.py", Yheight = dy, EcalGeoFile = ecalGeoFile )
# -----Create geometry----------------------------------------------
import shipDet_conf
run = ROOT.FairRunSim()
modules = shipDet_conf.configure(run,ShipGeo)

tgeom = ROOT.TGeoManager("Geometry", "Geane geometry")
gMan  = tgeom.Import(geoFile)
geoMat =  ROOT.genfit.TGeoMaterialInterface()
ROOT.genfit.MaterialEffects.getInstance().init(geoMat)
volDict = {}
i=0
for x in ROOT.gGeoManager.GetListOfVolumes():
 volDict[i]=x.GetName()
 i+=1

bfield = ROOT.genfit.BellField(ShipGeo.Bfield.max ,ShipGeo.Bfield.z,2, ShipGeo.Yheight/2.)
fM = ROOT.genfit.FieldManager.getInstance()
fM.init(bfield)

# prepare veto decisions
import shipVeto
veto = shipVeto.Task()

h = {}
ut.bookHist(h,'delPOverP','delP / P',100,0.,50.,100,-0.5,0.5)
ut.bookHist(h,'delPOverP2','delP / P chi2/nmeas<'+str(chi2CutOff),100,0.,50.,100,-0.5,0.5)
ut.bookHist(h,'delPOverPz','delPz / Pz',100,0.,50.,100,-0.5,0.5)
ut.bookHist(h,'delPOverP2z','delPz / Pz chi2/nmeas<'+str(chi2CutOff),100,0.,50.,100,-0.5,0.5)
ut.bookHist(h,'chi2','chi2/nmeas after trackfit',100,0.,10.)
ut.bookHist(h,'prob','prob(chi2)',100,0.,1.)
ut.bookHist(h,'IP','Impact Parameter',100,0.,10.)
ut.bookHist(h,'Doca','Doca between two tracks',100,0.,10.)
ut.bookHist(h,'IP0','Impact Parameter to target',100,0.,100.)
ut.bookHist(h,'IP0/mass','Impact Parameter to target vs mass',100,0.,2.,100,0.,100.)
ut.bookHist(h,'HNL','reconstructed Mass',500,0.,2.)
ut.bookHist(h,'meas','number of measurements',40,-0.5,39.5)
ut.bookHist(h,'meas2','number of measurements, fitted track',40,-0.5,39.5)
ut.bookHist(h,'measVSchi2','number of measurements vs chi2/meas',40,-0.5,39.5,100,0.,10.)
ut.bookHist(h,'distu','distance to wire',100,0.,1.)
ut.bookHist(h,'distv','distance to wire',100,0.,1.)
ut.bookHist(h,'disty','distance to wire',100,0.,1.)
ut.bookHist(h,'meanhits','mean number of hits / track',50,-0.5,49.5)
ut.bookHist(h,'ecalClusters','x/y and energy',50,-3.,3.,50,-6.,6.)

def checkHNLorigin(sTree):
 flag = True 
 if not fiducialCut: return flag
 theHNLVx = sTree.MCTrack[2]
 if theHNLVx.GetStartZ() < ShipGeo.vetoStation.z+100.*u.cm : flag = False
 if theHNLVx.GetStartZ() > ShipGeo.TrackStation1.z : flag = False
 X,Y =  theHNLVx.GetStartX(),theHNLVx.GetStartY()
 Rsq = (X/(2.45*u.m) )**2 + (Y/((dy/2.-0.05)*u.m) )**2
 if Rsq>1: flag = False
 return flag 
def checkFiducialVolume(sTree,tkey,dy):
# to be replaced later with using track extrapolator,
# for now use MC truth
   inside = True
   if not fiducialCut: return inside 
   mcPartKey = sTree.fitTrack2MC[tkey]
   for ahit in sTree.strawtubesPoint:
     if ahit.GetTrackID() == mcPartKey:
        X,Y = ahit.GetX(),ahit.GetY()
        Rsq = (X/(2.45*u.m) )**2 + (Y/((dy/2.-0.05)*u.m) )**2
        if Rsq > 1:
         inside = False    
         break
   return inside
def getPtruthFirst(sTree,mcPartKey):
   Ptruth,Ptruthz = -1.,-1.
   for ahit in sTree.strawtubesPoint:
     if ahit.GetTrackID() == mcPartKey:
        Ptruthz = ahit.GetPz()
        Ptruth  = ROOT.TMath.Sqrt(ahit.GetPx()**2+ahit.GetPy()**2+Ptruthz**2)
        break
   return Ptruth,Ptruthz

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


def makePlots():
   ut.bookCanvas(h,key='ecalanalysis',title='cluster map',nx=800,ny=600,cx=1,cy=1)
   cv = h['ecalanalysis'].cd(1)
   h['ecalClusters'].Draw('colz')
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
   ut.bookCanvas(h,key='fitresults2',title='Fit Results',nx=1600,ny=1200,cx=2,cy=2)
   print 'finished with first canvas'
   cv = h['fitresults2'].cd(1)
   h['Doca'].SetXTitle('closest distance between 2 tracks   [cm]')
   h['Doca'].SetYTitle('N/1mm')
   h['Doca'].Draw()
   cv = h['fitresults2'].cd(2)
   h['IP0'].SetXTitle('impact parameter to p-target   [cm]')
   h['IP0'].SetYTitle('N/1cm')
   h['IP0'].Draw()
   cv = h['fitresults2'].cd(3)
   h['HNL'].SetXTitle('inv. mass  [GeV/c2]')
   h['HNL'].SetYTitle('N/4MeV/c2')
   h['HNL'].Draw()
   fitSingleGauss('HNL',0.9,1.1)
   cv = h['fitresults2'].cd(4)
   h['IP0/mass'].SetXTitle('inv. mass  [GeV/c2]')
   h['IP0/mass'].SetYTitle('IP [cm]')
   h['IP0/mass'].Draw('colz')
   h['fitresults2'].Print('fitresults2.gif')
   print 'finished making plots'

# start event loop
def myEventLoop(n):
  rc = sTree.GetEntry(n)
  if not checkHNLorigin(sTree): return
  wg = sTree.MCTrack[1].GetWeight()
  if not wg>0.: wg=1.
# 
  flag,w = veto.SBT_decision(sTree)
  print "veto decision for SBT",flag,w
  wg = wg*w
  flag,w = veto.SVT_decision(sTree)
  print "veto decision for SVT",flag,w
  wg = wg*w
  flag,w = veto.UVT_decision(sTree)
  print "veto decision for UVT",flag,w
  wg = wg*w
#
# make some ecal cluster analysis if exist
  if sTree.FindBranch("EcalClusters"):
   for aClus in sTree.EcalClusters:
     h['ecalClusters'].Fill(aClus.X()/u.m,aClus.Y()/u.m,aClus.Energy()/u.GeV)
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
   Pz = fittedState.getMom().z()
   mcPartKey = sTree.fitTrack2MC[key]
   mcPart    = sTree.MCTrack[mcPartKey]
   if not mcPart : continue
   Ptruth_start     = mcPart.GetP()
   Ptruthz_start    = mcPart.GetPz()
   # get p truth from first strawpoint
   Ptruth,Ptruthz = getPtruthFirst(sTree,mcPartKey)
   delPOverP = (Ptruth - P)/Ptruth
   h['delPOverP'].Fill(Ptruth,delPOverP)
   delPOverPz = (1./Ptruthz - 1./Pz) * Ptruthz
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
    HNLPos = ROOT.TLorentzVector()
    HNL.ProductionVertex(HNLPos)
    HNLMom = ROOT.TLorentzVector()
    HNL.Momentum(HNLMom)
# check if DOCA info exist
    if HNL.GetMother(1)==99 :
      xv,yv,zv,doca  =  HNLPos.X(),HNLPos.Y(),HNLPos.Z(),HNLPos.T()
    else:
# redo doca calculation
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
     if not rc: continue # extrapolation failed, makes no sense to continue
     LV={}
     for tr in [t1,t2]:       
      mom = reps[tr].getMom(states[tr])
      pid = abs(states[tr].getPDG()) 
      if pid == 2212: pid = 211
      mass = PDG.GetParticle(pid).Mass()
      E = ROOT.TMath.Sqrt( mass*mass + mom.Mag2() )
      LV[tr].SetPxPyPzE(mom.x(),mom.y(),mom.z(),E)
     HNLMom = LV[t1]+LV[t2]
 # check if decay inside decay volume
    Rsq = (xv/(2.45*u.m) )**2 + (yv/((dy/2.-0.05)*u.m) )**2
    if Rsq > 1 : continue
    if zv < ShipGeo['vetoStation'].z : continue  
    h['Doca'].Fill(doca) 
    if  doca > docaCut : continue
    tr = ROOT.TVector3(0,0,ShipGeo.target.z0)
    t = 0
    for i in range(3):   t += HNLMom(i)/HNLMom.P()*(tr(i)-HNLPos(i)) 
    dist = 0
    for i in range(3):   dist += (tr(i)-HNLPos(i)-t*HNLMom(i)/HNLMom.P())**2
    dist = ROOT.TMath.Sqrt(dist)
    mass = HNLMom.M()
    h['IP0'].Fill(dist)  
    h['IP0/mass'].Fill(mass,dist)
    h['HNL'].Fill(mass)
#
def HNLKinematics():
 ut.bookHist(h,'HNLmomNoW','momentum unweighted',100,0.,300.)
 ut.bookHist(h,'HNLmom','momentum',100,0.,300.)
 ut.bookHist(h,'HNLmom_recTracks','momentum',100,0.,300.)
 ut.bookHist(h,'HNLmomNoW_recTracks','momentum unweighted',100,0.,300.)
 for n in range(sTree.GetEntries()): 
  rc = sTree.GetEntry(n)
  wg = sTree.MCTrack[1].GetWeight()
  if not wg>0.: wg=1.
  P = sTree.MCTrack[1].GetP()
  h['HNLmom'].Fill(P,wg) 
  h['HNLmomNoW'].Fill(P) 
  for HNL in sTree.Particles:
     t1,t2 = HNL.GetDaughter(0),HNL.GetDaughter(1) 
     for tr in [t1,t2]:
      xx  = sTree.FitTracks[tr].getFittedState()
      Prec = xx.getMom().Mag()
      h['HNLmom_recTracks'].Fill(Prec,wg) 
      h['HNLmomNoW_recTracks'].Fill(Prec) 
#
 
nEvents = min(sTree.GetEntries(),nEvents)
for n in range(nEvents): 
 myEventLoop(n)
 sTree.FitTracks.Delete()
makePlots()
# output histograms
hfile = inputFile.replace('_rec','_ana')
ROOT.gROOT.cd()
ut.writeHists(h,hfile)


