# setenv LD_LIBRARY_PATH ${LD_LIBRARY_PATH}:/media/ShipSoft/genfit-build/lib
debug = False
withNoAmbiguities = None  #  True   for debugging purposes
inputFile    = 'ship.Pythia8-TGeant4_HNL.root'
eventDisplay = False
nEvents      = 10000
withHists    = True
withOutput   = False

import ROOT,os,sys,getopt
try:
        opts, args = getopt.getopt(sys.argv[1:], "o:D:FHPu:n:x:f:hqv:sl:A",["inputFile=","nEvents=",
                                                 "ambiguities","hists","display","store"])
except getopt.GetoptError:
        # print help information and exit:
        print ' enter --inputFile=  --nEvents= number of events to process, ambiguities wire ambiguities default none' 
        print ' outputfile will have same name with _rec added'   
        sys.exit()
for o, a in opts:
        if o in ("ambiguities"):
            withNoAmbiguities = True
        if o in ("hists"):
            withHists = True
        if o in ("-f", "--inputFile"):
            inputFile = a
        if o in ("-f", "--store"):
            withOutput = True
        if o in ("-n", "--nEvents="):
            nEvents = int(a)
        if o in ("--display"):
            eventDisplay = True
outFile = inputFile
if withOutput:
 outFile = inputFile.replace('.root','_rec.root') 
 os.system('cp '+inputFile+' '+outFile)

#-----prepare python exit-----------------------------------------------
def pyExit():
 global fitter
 del fitter
import atexit
atexit.register(pyExit)

from array import array
import shipunit as u
import rootUtils as ut
import ShipGeoConfig
ShipGeo = ShipGeoConfig.Config().loadpy("$FAIRSHIP/geometry/geometry_config.py")


def makePlots():
   ut.bookCanvas(h,key='fitresults',title='Fit Results',nx=1600,ny=1200,cx=2,cy=2)
   cv = h['fitresults'].cd(1)
   h['delPOverP'].Draw('box')
   cv = h['fitresults'].cd(2)
   cv.SetLogy(1)
   h['chi2'].Draw()
   cv = h['fitresults'].cd(3)
   h['delPOverP_proj'] = h['delPOverP'].ProjectionY()
   ROOT.gStyle.SetOptFit(11111)
   h['delPOverP_proj'].Draw()
   h['delPOverP_proj'].Fit('gaus')
   cv = h['fitresults'].cd(4)
   h['delPOverP2_proj'] = h['delPOverP2'].ProjectionY()
   h['delPOverP2_proj'].Draw()
   h['delPOverP2_proj'].Fit('gaus')  
   h['fitresults'].Print('fitresults.gif')
   ut.bookCanvas(h,key='fitresults2',title='Fit Results',nx=1600,ny=1200,cx=2,cy=2)
   cv = h['fitresults2'].cd(1)
   h['Doca'].Draw()
   cv = h['fitresults2'].cd(2)
   h['IP0'].Draw()
   cv = h['fitresults2'].cd(3)
   h['HNL'].Draw()
   h['HNL'].Fit('gaus') 
   cv = h['fitresults2'].cd(4)
   h['IP0/mass'].Draw('box')
   h['fitresults2'].Print('fitresults2.gif')

if withHists:
 h={}
 ut.bookHist(h,'delPOverP','delP / P',100,0.,50.,100,-0.2,0.2)
 ut.bookHist(h,'delPOverP2','delP / P chi2<25',100,0.,50.,100,-0.2,0.2)
 ut.bookHist(h,'chi2','chi2 after trackfit',100,0.,1000.)
 ut.bookHist(h,'IP','Impact Parameter',100,0.,10.)
 ut.bookHist(h,'Doca','Doca between two tracks',100,0.,10.)
 ut.bookHist(h,'IP0','Impact Parameter to target',100,0.,100.)
 ut.bookHist(h,'IP0/mass','Impact Parameter to target vs mass',100,0.,2.,100,0.,100.)
 ut.bookHist(h,'HNL','reconstructed Mass',100,0.,2.)

# did not worked, unfortunately, had to write C++ code for BellField in genfit
class ShipBfield(ROOT.genfit.AbsBField):
 sB = ROOT.ShipBellField("ShipB", ShipGeo.Bfield.max, 40.*u.m )
 def get(self, x,y=None,z=None,Bx=None,By=None,Bz=None):
   print "my field called ",y
   if not y: 
     Bx = self.sB.GetBx(x.x(),x.y(),x.z())
     By = self.sB.GetBy(x.x(),x.y(),x.z())
     Bz = self.sB.GetBz(x.x(),x.y(),x.z())
     Bvec = ROOT.TVector3(Bx,By,Bz)
     return Bvec
   else:
    Bx = self.sB.GetBx(x,y,z)
    By = self.sB.GetBy(x,y,z)
    Bz = self.sB.GetBz(x,y,z)

class makeHitList:
 " convert FairSHiP MC hits to measurements"
 def __init__(self,fn='ship.Pythia8-TGeant4.root'):
  if withOutput: self.f = ROOT.TFile(fn,'update')
  else:          self.f = ROOT.TFile(fn)
  self.sTree     = self.f.cbmsim
  self.nEvents   =  min(self.sTree.GetEntries(),nEvents)
  self.MCTracks       = ROOT.TClonesArray("FairMCTrack")
  self.TrackingHits   = ROOT.TClonesArray("vetoPoint")
# read Ship Geant4 root file with entry/exit points:
  self.sTree.SetBranchAddress("vetoPoint", self.TrackingHits)
  self.sTree.SetBranchAddress("MCTrack", self.MCTracks)
  fGeo = ROOT.gGeoManager  
  self.vols = fGeo.GetListOfVolumes()
  self.layerType = {}  # xuvx , uv=+-5 degrees

  for v in self.vols: 
   nm = v.GetName()
   if nm.find('STr')<0: continue
   if not nm.find('_0')<0 : self.layerType[nm] = 'x0'
   if not nm.find('_3')<0 : self.layerType[nm] = 'x3' 
   if not nm.find('_1')<0 : self.layerType[nm] = 'u' 
   if not nm.find('_2')<0 : self.layerType[nm] = 'v' 
   # print 'debug nm',nm,self.layerType[nm]

  stereoAngle = {'x0':0,'x3':0,'u':ShipGeo.straw.stereoAngle,'v':-ShipGeo.straw.stereoAngle}
  delta       = {'x0':0,'x3':0.5,'u':0.33,'v':0.66}
  self.detinfo     = {}
  for i in ['x0','u','v','x3']:
   self.detinfo[i] = {'pitch':ShipGeo.straw.pitch,
                      'firstWire':(-ShipGeo.straw.length-delta[i])*u.cm,'stereoAngle':stereoAngle[i],'resol':ShipGeo.straw.resol}
  self.random = ROOT.TRandom()
  ROOT.gRandom.SetSeed(13)

 def dorot(self,x,y,xc,yc,alpha):
     #rotate x,y around xc,yc over alpha
     ca   = ROOT.TMath.Cos(alpha)
     sa   = ROOT.TMath.Sin(alpha)
     xout = ca*(x-xc)-sa*(y-yc)+xc
     yout = sa*(x-xc)+ca*(y-yc)+yc
     return xout,yout
 def hit2wire(self,ahit,no_amb=None):
     wl = ShipGeo.straw.length
     detname = self.vols[ahit.GetDetectorID()-1].GetName()   # don't know why -1 is needed, should not, but ... TR 31.5.2014
     nd = self.layerType[detname]
     if no_amb:
      xwire  = self.random.Gaus( ahit.GetX(),self.detinfo[nd]['resol'])
     else:
      nrwire = int( (ahit.GetX()-self.detinfo[nd]['firstWire'])/self.detinfo[nd]['pitch']+0.5)
      xwire  = nrwire*self.detinfo[nd]['pitch'] + self.detinfo[nd]['firstWire']
   #rotate top/bot of wire in xy plane around true hit over angle..
     xt,yt = self.dorot(xwire,wl, ahit.GetX(),ahit.GetY(),self.detinfo[nd]['stereoAngle'])
     xb,yb = self.dorot(xwire,-wl,ahit.GetX(),ahit.GetY(),self.detinfo[nd]['stereoAngle'])
   #distance to wire, and smear it.
     dw    = ROOT.fabs(ahit.GetX()-xwire)
     smear = 0
     if not no_amb: smear = ROOT.fabs(self.random.Gaus(dw,self.detinfo[nd]['resol']))
     smearedHit = {'mcHit':ahit,'xtop':xt,'ytop':yt,'z':ahit.GetZ(),'xbot':xb,'ybot':yb,'z':ahit.GetZ(),'dist':smear}
     return smearedHit
  
 def execute(self,n):
  if n > self.nEvents-1: return None 
  rc    = self.sTree.GetEvent(n) 
  nHits = self.TrackingHits.GetEntriesFast() 
  hitPosLists = {}
  for i in range(nHits):
    ahit = self.TrackingHits.At(i)
    detname = self.vols[ahit.GetDetectorID()-1].GetName()
    # print 'execute',detname,ahit.GetDetectorID()-1
    if detname.find('STr')<0: continue  # not a sensitive detector
    sm   = self.hit2wire(ahit,withNoAmbiguities)
    trID = ahit.GetTrackID()
    if not hitPosLists.has_key(trID):   
      hitPosLists[trID] = ROOT.std.vector('TVectorD')()
    m = array('d',[sm['xtop'],sm['ytop'],sm['z'],sm['xbot'],sm['ybot'],sm['z'],sm['dist']])
    measurement = ROOT.TVectorD(7,m)
    hitPosLists[trID].push_back(measurement)
  return hitPosLists

geoMat =  ROOT.genfit.TGeoMaterialInterface()
PDG = ROOT.TDatabasePDG.Instance()
# init geometry and mag. field
tgeom = ROOT.TGeoManager("Geometry", "Geane geometry")
tgeom.Import("geofile_full.Pythia8-TGeant4.root")
#
bfield = ROOT.genfit.BellField(ShipGeo.Bfield.max ,ShipGeo.Bfield.z )
fM = ROOT.genfit.FieldManager.getInstance()
fM.init(bfield)
 
geoMat =  ROOT.genfit.TGeoMaterialInterface()
ROOT.genfit.MaterialEffects.getInstance().init(geoMat)
# init event display
if eventDisplay: display = ROOT.genfit.EventDisplay.getInstance()

# init fitter
fitter = ROOT.genfit.KalmanFitterRefTrack()
WireMeasurement = ROOT.genfit.WireMeasurement
# access ShipTree
SHiP = makeHitList(outFile)
# main loop
for iEvent in range(0, SHiP.nEvents):
 hitPosLists = SHiP.execute(iEvent)
 if hitPosLists == None : break # end of events
# check if there are enough measurements:
 fitTrack = {}
 for atrack in hitPosLists:
  if atrack < 0: continue # these are hits not assigned to MC track because low E cut
  meas = hitPosLists[atrack]
  nM = meas.size()
  if debug: print iEvent,nM,atrack,SHiP.MCTracks[atrack].GetP()

  if nM < 8 : continue
  pdg    = SHiP.MCTracks[atrack].GetPdgCode()
  charge = PDG.GetParticle(pdg).Charge()/(3.)
  posM = ROOT.TVector3(0, 0, 0)
  momM = ROOT.TVector3(0,0,10.*u.GeV)
# approximate covariance
  covM = ROOT.TMatrixDSym(6)
  resolution = 0.01
  for  i in range(3):   covM[i][i] = resolution*resolution
  for  i in range(3,6): covM[i][i] = ROOT.TMath.pow(resolution / nM / ROOT.TMath.sqrt(3), 2)
# trackrep
  rep = ROOT.genfit.RKTrackRep(pdg)
# smeared start state
  stateSmeared = ROOT.genfit.MeasuredStateOnPlane(rep)
  rep.setPosMomCov(stateSmeared, posM, momM, covM)
# create track
  seedState = ROOT.TVectorD(6)
  seedCov   = ROOT.TMatrixDSym(6)
  rep.get6DStateCov(stateSmeared, seedState, seedCov)
  fitTrack[atrack] = ROOT.genfit.Track(rep, seedState, seedCov)
  for m in meas:
      hitCov = ROOT.TMatrixDSym(7)
      hitCov[6][6] = 0.01*0.01
      tp = ROOT.genfit.TrackPoint() 
      measurement = ROOT.genfit.WireMeasurement(m,hitCov,1,6,tp)
      fitTrack[atrack].insertPoint(ROOT.genfit.TrackPoint(measurement,fitTrack[atrack]))
#check
  if not fitTrack[atrack].checkConsistency():
   print 'Problem with track before fit, not consistent',fitTrack
# do the fit
  try:    fitter.processTrack(fitTrack[atrack])
  except: continue   
#check
  if not fitTrack[atrack].checkConsistency():
   print 'Problem with track after fit, not consistent',fitTrack
   continue
  if not withHists: continue
  # monitoring
  fitStatus   = fitTrack[atrack].getFitStatus()
  chi2 = fitStatus.getChi2()
  h['chi2'].Fill(chi2)
  if chi2>1000 or chi2<0: 
   rc = fitTrack.pop(atrack)
   continue
  try:     fittedState = fitTrack[atrack].getFittedState()
  except:  
   rc = fitTrack.pop(atrack)
   continue  
  P = fittedState.getMomMag()
  Ptruth = SHiP.MCTracks[atrack].GetP()
  delPOverP = (Ptruth - P)/Ptruth
  h['delPOverP'].Fill(Ptruth,delPOverP)
  if chi2<25: h['delPOverP2'].Fill(Ptruth,delPOverP)
# try measure impact parameter
  trackDir = fittedState.getDir()
  trackPos = fittedState.getPos()
  vx = ROOT.TVector3()
  SHiP.MCTracks[atrack].GetStartVertex(vx)
  t = 0
  for i in range(3):   t += trackDir(i)*(vx(i)-trackPos(i)) 
  dist = 0
  for i in range(3):   dist += (vx(i)-trackPos(i)-t*trackDir(i))**2
  dist = ROOT.TMath.Sqrt(dist)
  h['IP'].Fill(dist)  
  if (eventDisplay and iEvent < 100):
# add track to event display
   display.addEvent(fitTrack[atrack])
 if not withHists: continue
 if len(fitTrack)==2:
    LV  = {}
    PosDir = {} 
    for atrack in fitTrack:
     xx  = fitTrack[atrack].getFittedState()
     mom = xx.getMom()   
     PosDir[atrack] = [xx.getPos(),xx.getDir()]
     LV[atrack] = ROOT.TLorentzVector()
     pgdCode = SHiP.MCTracks[atrack].GetPdgCode()
     mass = PDG.GetParticle(pgdCode).Mass()
     E = ROOT.TMath.Sqrt(mom.Mag2()+mass**2) 
     LV[atrack].SetPxPyPzE(mom.x(),mom.y(),mom.z(),E)
    keys = fitTrack.keys()
    t1,t2 = keys[0],keys[1] 
    HNL = LV[t1]+LV[t2]
    h['HNL'].Fill(HNL.M())
# closest distance between two tracks
    V=0
    for i in range(3):   V += PosDir[t1][1](i)*PosDir[t2][1](i)
    S1=0
    for i in range(3):   S1 += (PosDir[t1][0](i)-PosDir[t2][0](i))*PosDir[t1][1](i)
    S2=0
    for i in range(3):   S2 += (PosDir[t1][0](i)-PosDir[t2][0](i))*PosDir[t2][1](i)
    l = (S2-S1*V)/(1-V*V)
    x2 = PosDir[t2][0](0)+l*PosDir[t2][1](0)
    y2 = PosDir[t2][0](1)+l*PosDir[t2][1](1)
    z2 = PosDir[t2][0](2)+l*PosDir[t2][1](2)
    x1 = PosDir[t1][0](0)+l*PosDir[t1][1](0)
    y1 = PosDir[t1][0](1)+l*PosDir[t1][1](1)
    z1 = PosDir[t1][0](2)+l*PosDir[t1][1](2)
    dist = ROOT.TMath.Sqrt((x1-x2)**2+(y1-y2)**2+(z1-z2)**2)
    h['Doca'].Fill(dist)  
    HNLPos = ROOT.TVector3( (x2+x1)/2.,(y2+y1)/2.,(z2+z1)/2.)
    tr = ROOT.TVector3(0,0,ShipGeo.target.z0)
    t = 0
    for i in range(3):   t += HNL(i)/HNL.P()*(tr(i)-HNLPos(i)) 
    dist = 0
    for i in range(3):   dist += (tr(i)-HNLPos(i)-t*HNL(i)/HNL.P())**2
    dist = ROOT.TMath.Sqrt(dist)
    h['IP0'].Fill(dist)  
    h['IP0/mass'].Fill(HNL.M(),dist)
# end loop over events
makePlots()
# open event display
if eventDisplay: display.open() 

