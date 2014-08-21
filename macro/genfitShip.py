# setenv LD_LIBRARY_PATH ${LD_LIBRARY_PATH}:/media/ShipSoft/genfit-build/lib
inputFile = 'ship.Pythia8-TGeant4.root'
debug = False
withNoAmbiguities = None # True   for debugging purposes
nEvents = 10000

import ROOT,os,sys,getopt

try:
        opts, args = getopt.getopt(sys.argv[1:], "o:D:FHPu:n:f:c:hqv:sl:A",["inputFile=","nEvents=","ambiguities"])
except getopt.GetoptError:
        # print help information and exit:
        print ' enter --inputFile=  --nEvents= number of events to process, ambiguities wire ambiguities default none' 
        print ' outputfile will have same name with _rec added'   
        sys.exit()
for o, a in opts:
        if o in ("ambiguities"):
            withNoAmbiguities = True
        if o in ("-f", "--inputFile"):
            inputFile = a
        if o in ("-n", "--nEvents="):
            nEvents = int(a)

print 'configured to process ',nEvents,' events from ' ,inputFile
outFile = inputFile.replace('.root','_rec.root') 
os.system('cp '+inputFile+' '+outFile)

#-----prepare python exit-----------------------------------------------
def pyExit():
 global fitter
 del fitter
 print "finishing pyExit" 
import atexit
atexit.register(pyExit)

from array import array
import shipunit as u
import rootUtils as ut
import ShipGeoConfig
ShipGeo = ShipGeoConfig.Config().loadpy("$FAIRSHIP/geometry/geometry_config.py")

fout = ROOT.TFile(outFile,'update')

class makeHitList:
 " convert FairSHiP MC hits to measurements"
 def __init__(self,fn):
  self.sTree     = fn.cbmsim
  self.nEvents   = min(self.sTree.GetEntries(),nEvents)
  self.MCTracks       = ROOT.TClonesArray("FairMCTrack")
  self.TrackingHits   = ROOT.TClonesArray("vetoPoint")
# read Ship Geant4 root file with entry/exit points:
  self.sTree.SetBranchAddress("vetoPoint", self.TrackingHits)
  self.sTree.SetBranchAddress("MCTrack", self.MCTracks)
  fGeo = ROOT.gGeoManager  
  self.vols = fGeo.GetListOfVolumes()
  self.layerType = {}  # xuvx , uv=+-5 degrees
# prepare for output
  self.fGenFitArray = ROOT.TClonesArray("genfit::Track") 
  self.fGenFitArray.BypassStreamer(ROOT.kFALSE)
  self.fitTrack2MC  = ROOT.std.vector('int')()
  self.SmearedHits  = ROOT.TClonesArray("TVectorD") 

  if self.sTree.GetBranch("FitTracks"):
   self.sTree.SetBranchAddress("FitTracks", self.fGenFitArray)
   self.sTree.SetBranchAddress("SmearedHits",self.SmearedHits)
   self.fitTracks   = self.sTree.GetBranch("FitTracks")  
   self.SHbranch    = self.sTree.GetBranch("SmearedHits")
   self.mcLink      = self.sTree.GetBranch("fitTrack2MC")
   print "branch already exists !"
  else :
   self.SHbranch    = self.sTree.Branch( "SmearedHits",self.SmearedHits,32000,-1)
   self.fitTracks   = self.sTree.Branch( "FitTracks",self.fGenFitArray,32000,-1)  
   self.mcLink      = self.sTree.Branch( "fitTrack2MC",self.fitTrack2MC,32000,-1)  
#
  for v in self.vols: 
   nm = v.GetName()
   if nm.find('STr')<0 and nm.find('Sv')<0: continue
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
  self.SmearedHits.Clear()
  self.fGenFitArray.Clear()
  self.fitTrack2MC.clear()
  for i in range(nHits):
    ahit = self.TrackingHits.At(i)
    detname = self.vols[ahit.GetDetectorID()-1].GetName()
    # print 'execute',detname,ahit.GetDetectorID()-1
    if detname.find('STr')<0 and detname.find('Sv')<0: 
        print 'unknown sensitive detector',detname 
        continue  # not a sensitive detector
    sm   = self.hit2wire(ahit,withNoAmbiguities)
    m = array('d',[sm['xtop'],sm['ytop'],sm['z'],sm['xbot'],sm['ybot'],sm['z'],sm['dist']])
    measurement = ROOT.TVectorD(7,m)
# copy to branch
    nHits = SHiP.SmearedHits.GetEntries()
    if nHits != i: print 'SmearedHits, counter wrong',i,nHits 
    self.SmearedHits[nHits]=measurement 
    if  detname.find('STr')<0: continue
    # do not use hits in Veto station for track reco  
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

# init fitter
fitter          = ROOT.genfit.KalmanFitterRefTrack()
WireMeasurement = ROOT.genfit.WireMeasurement
# access ShipTree
SHiP = makeHitList(fout)

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
  ROOT.SetOwnership(fitTrack[atrack], False)
  for m in meas:
      hitCov = ROOT.TMatrixDSym(7)
      hitCov[6][6] = 0.01*0.01
      tp = ROOT.genfit.TrackPoint() 
      measurement = ROOT.genfit.WireMeasurement(m,hitCov,1,6,tp)
      fitTrack[atrack].insertPoint(ROOT.genfit.TrackPoint(measurement,fitTrack[atrack]))
#check
  if not fitTrack[atrack].checkConsistency():
   print 'Problem with track before fit, not consistent',fitTrack
  if nM > 8 : 
# do the fit
   try:    fitter.processTrack(fitTrack[atrack])
   except: continue   
#check
   if not fitTrack[atrack].checkConsistency():
    print 'Problem with track after fit, not consistent',fitTrack
    continue
  # monitoring
  fitStatus   = fitTrack[atrack].getFitStatus()
  chi2        = fitStatus.getChi2()
# make track persistent
  nTrack   = SHiP.fGenFitArray.GetEntries()
  theTrack = ROOT.genfit.Track(fitTrack[atrack])
  SHiP.fGenFitArray[nTrack] = theTrack
  SHiP.fitTrack2MC.push_back(atrack)
  if debug: print 'save track',theTrack,chi2
# make tracks persistent
 if debug: print 'call Fill', len(SHiP.fGenFitArray),nTrack,SHiP.fGenFitArray.GetEntries()
 SHiP.fitTracks.Fill()
 SHiP.mcLink.Fill()
 SHiP.SHbranch.Fill()
 if debug: print 'end of event after Fill'
 
# end loop over events
xx = fout.FindObjectAny("cbmsim;1")
xx.Delete()
print 'finished writing tree'
SHiP.sTree.Write()


