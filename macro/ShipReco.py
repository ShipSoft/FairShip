inputFile = 'ship.Pythia8-TGeant4.root'
geoFile   = None
debug = False
EcalDebugDraw = False
withNoStrawSmearing = None # True   for debugging purposes
nEvents    = 999999
firstEvent = 0
withHists = True
vertexing = True
dy  = None
saveDisk  = False # remove input file
pidProton = False # if true, take truth, if False fake with pion mass
realPR = ''

import resource
def mem_monitor():
 # Getting virtual memory size 
    pid = os.getpid()
    with open(os.path.join("/proc", str(pid), "status")) as f:
        lines = f.readlines()
    _vmsize = [l for l in lines if l.startswith("VmSize")][0]
    vmsize = int(_vmsize.split()[1])
    #Getting physical memory size  
    pmsize = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    print "memory: virtuell = %5.2F MB  physical = %5.2F MB"%(vmsize/1.0E3,pmsize/1.0E3)

from array import array
import ROOT,os,sys,getopt
import __builtin__ as builtin
from pythia8_conf import addHNLtoROOT
import rootUtils as ut
import shipunit as u
import shipRoot_conf

shipRoot_conf.configure()
# init fitter, to be done before importing shipPatRec
#fitter          = ROOT.genfit.KalmanFitter()
#fitter          = ROOT.genfit.KalmanFitterRefTrack()
fitter           = ROOT.genfit.DAF()
import shipPatRec 
#set to True if "real" pattern recognition is required also

if debug == True: shipPatRec.debug = 1

try:
        opts, args = getopt.getopt(sys.argv[1:], "o:D:FHPu:n:f:g:c:hqv:sl:A:Y:i:",\
           ["ecalDebugDraw","inputFile=","geoFile=","nEvents=","noStrawSmearing","noVertexing","saveDisk","realPR"])
except getopt.GetoptError:
        # print help information and exit:
        print ' enter --inputFile=  --geoFile= --nEvents=  --firstEvent=,' 
        print ' noStrawSmearing: no smearing of distance to wire, default on' 
        print ' outputfile will have same name with _rec added'   
        sys.exit()
for o, a in opts:
        if o in ("noVertexing"):
            vertexing = False
        if o in ("noStrawSmearing"):
            withNoStrawSmearing = True
        if o in ("-f", "--inputFile"):
            inputFile = a
        if o in ("-g", "--geoFile"):
            geoFile = a
        if o in ("-n", "--nEvents="):
            nEvents = int(a)
        if o in ("-Y"): 
            dy = float(a)
        if o in ("--ecalDebugDraw"):
            EcalDebugDraw = True
        if o in ("--saveDisk"):
            saveDisk = True
	if o in ("--realPR"):
            realPR = "_PR"
if EcalDebugDraw: ROOT.gSystem.Load("libASImage")

# need to figure out which geometry was used
if not dy:
  # try to extract from input file name
  tmp = inputFile.split('.')
  try:
    dy = float( tmp[1]+'.'+tmp[2] )
  except:
    dy = None
print 'configured to process ',nEvents,' events from ' ,inputFile, \
      ' starting with event ',firstEvent, ' with option Yheight = ',dy,' with vertexing',vertexing,' and real pattern reco',realPR=="_PR"
if not inputFile.find('_rec.root') < 0: 
  outFile   = inputFile
  inputFile = outFile.replace('_rec.root','.root') 
else:
  outFile = inputFile.replace('.root','_rec.root') 
# outfile should be in local directory
  tmp = outFile.split('/')
  outFile = tmp[len(tmp)-1]
  if saveDisk: os.system('mv '+inputFile+' '+outFile)
  else :       os.system('cp '+inputFile+' '+outFile)

if not geoFile:
 tmp = inputFile.replace('ship.','geofile_full.')
 geoFile = tmp.replace('_rec','')
# try to figure out which ecal geo to load
fgeo = ROOT.TFile(geoFile)
sGeo = fgeo.FAIRGeom

from ShipGeoConfig import ConfigRegistry
from rootpyPickler import Unpickler

if not fgeo.FindKey('ShipGeo'):
 # old geofile, missing Shipgeo dictionary
 if sGeo.GetVolume('EcalModule3') :  ecalGeoFile = "ecal_ellipse6x12m2.geo"
 else: ecalGeoFile = "ecal_ellipse5x10m2.geo" 
 print 'found ecal geo for ',ecalGeoFile
 if dy: 
  ShipGeo = ConfigRegistry.loadpy("$FAIRSHIP/geometry/geometry_config.py", Yheight = dy, EcalGeoFile = ecalGeoFile)
 else:
  ShipGeo = ConfigRegistry.loadpy("$FAIRSHIP/geometry/geometry_config.py", EcalGeoFile = ecalGeoFile) 
else: 
 # new geofile, load Shipgeo dictionary
  upkl    = Unpickler(fgeo)
  ShipGeo = upkl.load('ShipGeo')
  ecalGeoFile = ShipGeo.ecal.File

ps = 0
if sGeo.GetVolume('PreshowerDetector'):ps = 1

h={}
log={}
if withHists:
 ut.bookHist(h,'distu','distance to wire',100,0.,5.)
 ut.bookHist(h,'distv','distance to wire',100,0.,5.)
 ut.bookHist(h,'disty','distance to wire',100,0.,5.)
 ut.bookHist(h,'nmeas','nr measuerements',100,0.,50.)
 ut.bookHist(h,'chi2','Chi2/DOF',100,0.,20.)

#-----prepare python exit-----------------------------------------------
def pyExit():
 global fitter
 del fitter
 print "finishing pyExit" 
import atexit
atexit.register(pyExit)

# -----Create geometry----------------------------------------------
import shipDet_conf
run = ROOT.FairRunSim()
modules = shipDet_conf.configure(run,ShipGeo)
builtin.debug    = debug
builtin.fitter   = fitter
builtin.ship_geo = ShipGeo # for shipPatRec
builtin.pidProton = pidProton

# import reco tasks
import shipPid
import shipVertex
PDG = ROOT.TDatabasePDG.Instance()
addHNLtoROOT()

class ShipReco:
 " convert FairSHiP MC hits to measurements"
 def __init__(self,fout):
  self.fn = ROOT.TFile(fout,'update')
  self.sTree     = self.fn.cbmsim
  if self.sTree.GetBranch("SmearedHits"):
    print "remove RECO branches and rerun reconstruction"
    self.fn.Close()    
    # make a new file without reco branches
    f = ROOT.TFile(fout)
    sTree = f.cbmsim
    sTree.SetBranchStatus("SmearedHits",0)
    if sTree.GetBranch("FitTracks"): sTree.SetBranchStatus("FitTracks",0)
    if sTree.GetBranch("Particles"): sTree.SetBranchStatus("Particles",0)
    if sTree.GetBranch("fitTrack2MC"): sTree.SetBranchStatus("fitTrack2MC",0)
    if sTree.GetBranch("FitTracks_PR"): sTree.SetBranchStatus("FitTracks_PR",0)
    if sTree.GetBranch("Particles_PR"): sTree.SetBranchStatus("Particles_PR",0)
    if sTree.GetBranch("fitTrack2MC_PR"): sTree.SetBranchStatus("fitTrack2MC_PR",0)
    if sTree.GetBranch("EcalClusters"): sTree.SetBranchStatus("EcalClusters",0)     
    rawFile = fout.replace("_rec.root","_raw.root")
    recf = ROOT.TFile(rawFile,"recreate")
    newTree = sTree.CloneTree(0)
    for n in range(sTree.GetEntries()):
      sTree.GetEntry(n)
      rc = newTree.Fill()
    sTree.Clear()
    newTree.AutoSave()
    f.Close() 
    recf.Close() 
    os.system('cp '+rawFile +' '+fout)
    self.fn = ROOT.TFile(fout,'update')
    self.sTree     = self.fn.cbmsim     
#  check that all containers are present, otherwise create dummy version
  self.dummyContainers={}
  branch_class = {"vetoPoint":"vetoPoint","ShipRpcPoint":"ShipRpcPoint","TargetPoint":"TargetPoint",\
                  "strawtubesPoint":"strawtubesPoint","EcalPointLite":"ecalPoint","HcalPointLite":"hcalPoint"}
  for x in branch_class:
    if not self.sTree.GetBranch(x):
     self.dummyContainers[x+"_array"] = ROOT.TClonesArray(branch_class[x])
     self.dummyContainers[x] = self.sTree.Branch(x,self.dummyContainers[x+"_array"],32000,-1) 
     setattr(self.sTree,x,self.dummyContainers[x+"_array"])
     self.dummyContainers[x].Fill()
#   
  if self.sTree.GetBranch("GeoTracks"): self.sTree.SetBranchStatus("GeoTracks",0)
  self.nEvents   = min(self.sTree.GetEntries(),nEvents)
# prepare for output
  self.fGenFitArray = ROOT.TClonesArray("genfit::Track") 
  self.fGenFitArray.BypassStreamer(ROOT.kFALSE)
  self.fitTrack2MC  = ROOT.std.vector('int')()
  self.mcLink      = self.sTree.Branch("fitTrack2MC"+realPR,self.fitTrack2MC,32000,-1)
  self.fitTracks   = self.sTree.Branch("FitTracks"+realPR,  self.fGenFitArray,32000,-1)
#
  self.SmearedHits     = ROOT.TClonesArray("TVectorD") 
  self.SHbranch       = self.sTree.Branch("SmearedHits",self.SmearedHits,32000,-1)
#
  self.random = ROOT.TRandom()
  ROOT.gRandom.SetSeed(13)
#
  self.Vertexing = shipVertex.Task(h,self)
  self.Pid       = shipPid.Task(h,self)

 def hit2wire(self,ahit,no_amb=None):
     detID = ahit.GetDetectorID()
     top = ROOT.TVector3()
     bot = ROOT.TVector3()
     modules["Strawtubes"].StrawEndPoints(detID,bot,top)
   #distance to wire, and smear it.
     dw  = ahit.dist2Wire()
     smear = dw
     if not no_amb: smear = abs(self.random.Gaus(dw,ShipGeo.straw.resol))
     smearedHit = {'mcHit':ahit,'xtop':top.x(),'ytop':top.y(),'z':top.z(),'xbot':bot.x(),'ybot':bot.y(),'z':bot.z(),'dist':smear}
     if abs(top.y())==abs(bot.y()): h['disty'].Fill(dw)
     if abs(top.y())>abs(bot.y()): h['distu'].Fill(dw)
     if abs(top.y())<abs(bot.y()): h['distv'].Fill(dw)
     return smearedHit
  
 def findTracks(self,n):
  if n > self.nEvents-1: return None 
  rc    = self.sTree.GetEvent(n) 
  if n%1000==0: print "==> event ",n
  nShits = self.sTree.strawtubesPoint.GetEntriesFast() 
  hitPosLists    = {}
  stationCrossed = {}
  fittedtrackids=[]
  self.SmearedHits.Delete()
  self.fGenFitArray.Delete()
  self.fitTrack2MC.clear()
#   
  for i in range(nShits):
    ahit = self.sTree.strawtubesPoint.At(i)
    sm   = self.hit2wire(ahit,withNoStrawSmearing)
    m = array('d',[i,sm['xtop'],sm['ytop'],sm['z'],sm['xbot'],sm['ybot'],sm['z'],sm['dist'],ahit.GetDetectorID()])
    measurement = ROOT.TVectorD(9,m)
# copy to branch
    nHits = self.SmearedHits.GetEntries()
    if self.SmearedHits.GetSize() == nHits: self.SmearedHits.Expand(nHits+1000)
    self.SmearedHits[nHits] = measurement
    station = int(ahit.GetDetectorID()/10000000)
    if station > 4 : continue
    # do not use hits in Veto station for track reco   
    trID = ahit.GetTrackID()
    if not hitPosLists.has_key(trID):   
      hitPosLists[trID]     = ROOT.std.vector('TVectorD')()
      stationCrossed[trID]  = {}
    m = array('d',[sm['xtop'],sm['ytop'],sm['z'],sm['xbot'],sm['ybot'],sm['z'],sm['dist']])
    hitPosLists[trID].push_back(ROOT.TVectorD(7,m))
    if not stationCrossed[trID].has_key(station): stationCrossed[trID][station]=0
    stationCrossed[trID][station]+=1   
  nTrack = -1
  if realPR:
     fittedtrackids=shipPatRec.execute(n,self.SmearedHits,self.sTree,shipPatRec.ReconstructibleMCTracks)
     if fittedtrackids:
       tracknbr=0
       for ids in fittedtrackids:
	 nTrack   = SHiP.fGenFitArray.GetEntries()
         theTrack = shipPatRec.theTracks[tracknbr]
         if not debug: theTrack.prune("CFL")  #  http://sourceforge.net/p/genfit/code/HEAD/tree/trunk/core/include/Track.h#l280 
         self.fGenFitArray[nTrack] = theTrack
         self.fitTrack2MC.push_back(ids) 
	 tracknbr+=1
  else: # do fake pattern reco	 
   for atrack in hitPosLists:
    if atrack < 0: continue # these are hits not assigned to MC track because low E cut
    pdg    = self.sTree.MCTrack[atrack].GetPdgCode()
    if not PDG.GetParticle(pdg): continue # unknown particle
    meas = hitPosLists[atrack]
    nM = meas.size()
    if nM < 25 : continue                          # not enough hits to make a good trackfit 
    if len(stationCrossed[atrack]) < 3 : continue  # not enough stations crossed to make a good trackfit 
    if debug: 
       mctrack = self.sTree.MCTrack[atrack]
    charge = PDG.GetParticle(pdg).Charge()/(3.)
    posM = ROOT.TVector3(0, 0, 0)
    momM = ROOT.TVector3(0,0,3.*u.GeV)
# approximate covariance
    covM = ROOT.TMatrixDSym(6)
    resolution = ShipGeo.straw.resol
    for  i in range(3):   covM[i][i] = resolution*resolution
    covM[0][0]=resolution*resolution*100.
    for  i in range(3,6): covM[i][i] = ROOT.TMath.Power(resolution / nM / ROOT.TMath.Sqrt(3), 2)
# trackrep
    rep = ROOT.genfit.RKTrackRep(pdg)
# smeared start state
    stateSmeared = ROOT.genfit.MeasuredStateOnPlane(rep)
    rep.setPosMomCov(stateSmeared, posM, momM, covM)
# create track
    seedState = ROOT.TVectorD(6)
    seedCov   = ROOT.TMatrixDSym(6)
    rep.get6DStateCov(stateSmeared, seedState, seedCov)
    theTrack = ROOT.genfit.Track(rep, seedState, seedCov)
    hitCov = ROOT.TMatrixDSym(7)
    hitCov[6][6] = resolution*resolution
    for m in meas:
      tp = ROOT.genfit.TrackPoint(theTrack) # note how the point is told which track it belongs to 
      measurement = ROOT.genfit.WireMeasurement(m,hitCov,1,6,tp) # the measurement is told which trackpoint it belongs to
      # print measurement.getMaxDistance()
      measurement.setMaxDistance(0.5*u.cm)
      # measurement.setLeftRightResolution(-1)
      tp.addRawMeasurement(measurement) # package measurement in the TrackPoint                                          
      theTrack.insertPoint(tp)  # add point to Track
   # print "debug meas",atrack,nM,stationCrossed[atrack],self.sTree.MCTrack[atrack],pdg
#check
    if not theTrack.checkConsistency():
     print 'Problem with track before fit, not consistent',atrack,theTrack
     continue
# do the fit
    try:  fitter.processTrack(theTrack) # processTrackWithRep(theTrack,rep,True)
    except: 
       print "genfit failed to fit track"
       continue
#check
    if not theTrack.checkConsistency():
     print 'Problem with track after fit, not consistent',atrack,theTrack
     continue
    fitStatus   = theTrack.getFitStatus()
    nmeas = fitStatus.getNdf()   
    chi2        = fitStatus.getChi2()/nmeas   
    h['chi2'].Fill(chi2)
# make track persistent
    nTrack   = SHiP.fGenFitArray.GetEntries()
    if not debug: theTrack.prune("CFL")  #  http://sourceforge.net/p/genfit/code/HEAD/tree/trunk/core/include/Track.h#l280 
    self.fGenFitArray[nTrack] = theTrack
    self.fitTrack2MC.push_back(atrack)
    if debug: 
     print 'save track',theTrack,chi2,nM,fitStatus.isFitConverged()
  self.fitTracks.Fill()
  self.mcLink.Fill()
  self.SHbranch.Fill()
  return nTrack+1
#
SHiP = ShipReco(outFile)
caloTasks = []  
if SHiP.sTree.GetBranch("EcalPoint"):
# -----Calorimeter part --------------------------------------------
# Creates. exports and fills calorimeter structure
 dflag = 0
 if debug: dflag = 10
 ecalGeo = ecalGeoFile+'z'+str(ShipGeo.ecal.z)+".geo"
 ecalFiller=ROOT.ecalStructureFiller("ecalFiller", dflag,ecalGeo)
 ecalFiller.SetUseMCPoints(ROOT.kTRUE)
 ecalFiller.StoreTrackInformation()
 caloTasks.append(ecalFiller)
 #GeV -> ADC conversion
 ecalDigi=ROOT.ecalDigi("ecalDigi",0)
 caloTasks.append(ecalDigi)
 #ADC -> GeV conversion
 ecalPrepare=ROOT.ecalPrepare("ecalPrepare",0)
 caloTasks.append(ecalPrepare)
 # Maximums locator
 ecalMaximumFind=ROOT.ecalMaximumLocator("maximumFinder",dflag)
 caloTasks.append(ecalMaximumFind)
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
# Cluster finder
 ecalClusterFind=ROOT.ecalClusterFinder("clusterFinder",dflag)
 caloTasks.append(ecalClusterFind)
# Calorimeter reconstruction
 ecalReco=ROOT.ecalReco('ecalReco',0)
 caloTasks.append(ecalReco)
# Match reco to MC
 ecalMatch=ROOT.ecalMatch('ecalMatch',0)
 caloTasks.append(ecalMatch)
 if EcalDebugDraw:
 # ecal drawer: Draws calorimeter structure, incoming particles, clusters, maximums
  ecalDrawer=ROOT.ecalDrawer("clusterFinder",10)
  caloTasks.append(ecalDrawer)

geoMat =  ROOT.genfit.TGeoMaterialInterface()
# init geometry and mag. field
gMan  = ROOT.gGeoManager
#
bfield = ROOT.genfit.BellField(ShipGeo.Bfield.max ,ShipGeo.Bfield.z,2, ShipGeo.Yheight/2.*u.m)
fM = ROOT.genfit.FieldManager.getInstance()
fM.init(bfield)
 
geoMat =  ROOT.genfit.TGeoMaterialInterface()
ROOT.genfit.MaterialEffects.getInstance().init(geoMat)

if debug: fitter.setDebugLvl(1) # produces lot of printout
WireMeasurement = ROOT.genfit.WireMeasurement

# access ShipTree
SHiP.sTree.GetEvent(0)
if len(caloTasks)>0:
 print "** initialize Calo reconstruction **" 
 ecalStructure     = ecalFiller.InitPython(SHiP.sTree.EcalPointLite)
 ecalDigi.InitPython(ecalStructure)
 ecalPrepare.InitPython(ecalStructure)
 ecalMaximums      = ecalMaximumFind.InitPython(ecalStructure)
 ecalCalib         = ecalClusterCalib.InitPython()
 ecalClusters      = ecalClusterFind.InitPython(ecalStructure, ecalMaximums, ecalCalib)
 SHiP.EcalClusters = SHiP.sTree.Branch("EcalClusters",ecalClusters,32000,-1)
 ecalReconstructed = ecalReco.InitPython(SHiP.sTree.EcalClusters, ecalStructure, ecalCalib)
 SHiP.EcalReconstructed = SHiP.sTree.Branch("EcalReconstructed",ecalReconstructed,32000,-1)
 ecalMatch.InitPython(ecalStructure, ecalReconstructed, SHiP.sTree.MCTrack)
 if EcalDebugDraw: ecalDrawer.InitPython(SHiP.sTree.MCTrack, SHiP.sTree.EcalPoint, ecalStructure, ecalClusters)
else:
  ecalClusters      = ROOT.TClonesArray("ecalCluster") 
  ecalReconstructed = ROOT.TClonesArray("ecalReconstructed") 
  SHiP.EcalClusters = SHiP.sTree.Branch("EcalClusters",ecalClusters,32000,-1)
  SHiP.EcalReconstructed = SHiP.sTree.Branch("EcalReconstructed",ecalReconstructed,32000,-1)
# for 'real' PatRec
shipPatRec.initialize(fgeo)

# main loop
for iEvent in range(firstEvent, SHiP.nEvents):
 if debug: print 'event ',iEvent
 ntracks = SHiP.findTracks(iEvent)
 SHiP.EcalClusters.Fill()
 SHiP.EcalReconstructed.Fill()
 SHiP.Pid.execute()
 if vertexing:
# now go for 2-track combinations
   SHiP.Vertexing.execute()
 for x in caloTasks: 
   if x.GetName() == 'ecalFiller': x.Exec('start',SHiP.sTree.EcalPointLite)
   elif x.GetName() == 'ecalMatch':  x.Exec('start',ecalReconstructed, SHiP.sTree.MCTrack)
   else : x.Exec('start')

 if debug: print 'end of event after Fill'
 # memory monitoring
 # mem_monitor() 

# end loop over events

print 'finished writing tree'
SHiP.sTree.Write()

ut.writeHists(h,"recohists.root")
if realPR: ut.writeHists(shipPatRec.h,"recohists_patrec.root")

ut.errorSummary()

