import ROOT,shipVertex,shipPatRec 
import shipunit as u
import rootUtils as ut
from array import array

stop  = ROOT.TVector3()
start = ROOT.TVector3()

class ShipDigiReco:
 " convert FairSHiP MC hits / digitized hits to measurements"
 def __init__(self,fout,fgeo):
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
    if sTree.GetBranch("EcalReconstructed"): sTree.SetBranchStatus("EcalReconstructed",0)     
    if sTree.GetBranch("Pid"): sTree.SetBranchStatus("Pid",0)     
    if sTree.GetBranch("Digi_StrawtubesHits"): sTree.SetBranchStatus("Digi_StrawtubesHits",0)     
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
# prepare for output
  self.fGenFitArray = ROOT.TClonesArray("genfit::Track") 
  self.fGenFitArray.BypassStreamer(ROOT.kFALSE)
  self.fitTrack2MC  = ROOT.std.vector('int')()
  self.mcLink      = self.sTree.Branch("fitTrack2MC"+realPR,self.fitTrack2MC,32000,-1)
  self.fitTracks   = self.sTree.Branch("FitTracks"+realPR,  self.fGenFitArray,32000,-1)
#
  self.SmearedHits  = ROOT.TClonesArray("TVectorD") 
  self.SHbranch     = self.sTree.Branch("SmearedHits",self.SmearedHits,32000,-1)
  self.digiStraw    = ROOT.TClonesArray("strawtubesHit")
  self.digiStrawBranch   = self.sTree.Branch("Digi_StrawtubesHits",self.digiStraw,32000,-1)
# for the digitizing step
  self.v_drift = 1./(30*u.ns/u.mm) # for baseline NA62 5mm radius straws)
  self.sigma_spatial = 120*u.micrometer
# setup ecal reconstruction
  self.caloTasks = []  
  if self.sTree.GetBranch("EcalPoint"):
# Creates. exports and fills calorimeter structure
   dflag = 0
   if debug: dflag = 10
   ecalGeo = ecalGeoFile+'z'+str(ShipGeo.ecal.z)+".geo"
   ecalFiller=ROOT.ecalStructureFiller("ecalFiller", dflag,ecalGeo)
   ecalFiller.SetUseMCPoints(ROOT.kTRUE)
   ecalFiller.StoreTrackInformation()
   self.caloTasks.append(ecalFiller)
 #GeV -> ADC conversion
   ecalDigi=ROOT.ecalDigi("ecalDigi",0)
   self.caloTasks.append(ecalDigi)
 #ADC -> GeV conversion
   ecalPrepare=ROOT.ecalPrepare("ecalPrepare",0)
   self.caloTasks.append(ecalPrepare)
 # Maximums locator
   ecalMaximumFind=ROOT.ecalMaximumLocator("maximumFinder",dflag)
   self.caloTasks.append(ecalMaximumFind)
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
   self.caloTasks.append(ecalClusterCalib)
# Cluster finder
   ecalClusterFind=ROOT.ecalClusterFinder("clusterFinder",dflag)
   self.caloTasks.append(ecalClusterFind)
# Calorimeter reconstruction
   ecalReco=ROOT.ecalReco('ecalReco',0)
   self.caloTasks.append(ecalReco)
# Match reco to MC
   ecalMatch=ROOT.ecalMatch('ecalMatch',0)
   self.caloTasks.append(ecalMatch)
   if EcalDebugDraw:
 # ecal drawer: Draws calorimeter structure, incoming particles, clusters, maximums
    ecalDrawer=ROOT.ecalDrawer("clusterFinder",10)
    self.caloTasks.append(ecalDrawer)
 # add pid reco
   import shipPid
   self.caloTasks.append(shipPid.Task(h,self))
# prepare vertexing
  self.Vertexing = shipVertex.Task(h,self)
# setup random number generator 
  self.random = ROOT.TRandom()
  ROOT.gRandom.SetSeed(13)
  self.PDG = ROOT.TDatabasePDG.Instance()
# access ShipTree
  self.sTree.GetEvent(0)
  if len(self.caloTasks)>0:
   print "** initialize Calo reconstruction **" 
   self.ecalStructure     = ecalFiller.InitPython(self.sTree.EcalPointLite)
   ecalDigi.InitPython(self.ecalStructure)
   ecalPrepare.InitPython(self.ecalStructure)
   self.ecalMaximums      = ecalMaximumFind.InitPython(self.ecalStructure)
   self.ecalCalib         = ecalClusterCalib.InitPython()
   self.ecalClusters      = ecalClusterFind.InitPython(self.ecalStructure, self.ecalMaximums, self.ecalCalib)
   self.EcalClusters = self.sTree.Branch("EcalClusters",self.ecalClusters,32000,-1)
   self.ecalReconstructed = ecalReco.InitPython(self.sTree.EcalClusters, self.ecalStructure, self.ecalCalib)
   self.EcalReconstructed = self.sTree.Branch("EcalReconstructed",self.ecalReconstructed,32000,-1)
   ecalMatch.InitPython(self.ecalStructure, self.ecalReconstructed, self.sTree.MCTrack)
   if EcalDebugDraw: ecalDrawer.InitPython(self.sTree.MCTrack, self.sTree.EcalPoint, self.ecalStructure, self.ecalClusters)
  else:
   ecalClusters      = ROOT.TClonesArray("ecalCluster") 
   ecalReconstructed = ROOT.TClonesArray("ecalReconstructed") 
   self.EcalClusters = self.sTree.Branch("EcalClusters",self.ecalClusters,32000,-1)
   self.EcalReconstructed = self.sTree.Branch("EcalReconstructed",self.ecalReconstructed,32000,-1)
#
  self.geoMat =  ROOT.genfit.TGeoMaterialInterface()
# init geometry and mag. field
  gMan  = ROOT.gGeoManager
#
  self.bfield = ROOT.genfit.BellField(ShipGeo.Bfield.max ,ShipGeo.Bfield.z,2, ShipGeo.Yheight/2.*u.m)
  self.fM = ROOT.genfit.FieldManager.getInstance()
  self.fM.init(self.bfield)
  ROOT.genfit.MaterialEffects.getInstance().init(self.geoMat)

 # init fitter, to be done before importing shipPatRec
  #fitter          = ROOT.genfit.KalmanFitter()
  #fitter          = ROOT.genfit.KalmanFitterRefTrack()
  self.fitter      = ROOT.genfit.DAF()
  if debug: self.fitter.setDebugLvl(1) # produces lot of printout
  #set to True if "real" pattern recognition is required also
  if debug == True: shipPatRec.debug = 1

# for 'real' PatRec
  shipPatRec.initialize(fgeo)

 def reconstruct(self):
   ntracks = self.findTracks()
   for x in self.caloTasks: 
    if hasattr(x,'execute'): x.execute()
    elif x.GetName() == 'ecalFiller': x.Exec('start',self.sTree.EcalPointLite)
    elif x.GetName() == 'ecalMatch':  x.Exec('start',self.ecalReconstructed, self.sTree.MCTrack)
    else : x.Exec('start')
   self.EcalClusters.Fill()
   self.EcalReconstructed.Fill()
   if vertexing:
# now go for 2-track combinations
    self.Vertexing.execute()

 def digitize(self):
   self.sTree.t0 = self.random.Rndm()*1*u.microsecond
   self.digiStraw.Delete()
   self.digitizeStrawTubes()
   self.digiStrawBranch.Fill()
     
 def digitizeStrawTubes(self):
 # digitize FairSHiP MC hits  
   index = 0
   for aMCPoint in self.sTree.strawtubesPoint:
     detID = aMCPoint.GetDetectorID()
     modules["Strawtubes"].StrawEndPoints(detID,start,stop)
     t_drift = abs(self.random.Gaus(aMCPoint.dist2Wire()/self.v_drift, self.sigma_spatial/self.v_drift ) )
     tdc = self.sTree.t0 + aMCPoint.GetTime() + t_drift + ( abs(stop[0]-start[0])-abs(aMCPoint.GetX() ) )/ u.speedOfLight
     aHit = ROOT.strawtubesHit(detID, tdc)
     if self.digiStraw.GetSize() == index: self.digiStraw.Expand(index+1000)
     self.digiStraw[index]=aHit
     index+=1

 def hit2wire(self,ahit,no_amb=None):
     detID = ahit.GetDetectorID()
     top = ROOT.TVector3()
     bot = ROOT.TVector3()
     modules["Strawtubes"].StrawEndPoints(detID,bot,top)
   #distance to wire, and smear it.
     dw  = ahit.dist2Wire()
     smear = dw
     if not no_amb: smear = abs(self.random.Gaus(dw,ShipGeo.straw.resol))
     smearedHit = {'mcHit':ahit,'xtop':top.x(),'ytop':top.y(),'z':top.z(),'xbot':bot.x(),'ybot':bot.y(),'dist':smear}
     # Note: top.z()==bot.z() unless misaligned, so only add key 'z' to smearedHit
     if abs(top.y())==abs(bot.y()): h['disty'].Fill(dw)
     if abs(top.y())>abs(bot.y()): h['distu'].Fill(dw)
     if abs(top.y())<abs(bot.y()): h['distv'].Fill(dw)
     return smearedHit
  
 def findTracks(self):
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
  trackCandidates = []
  if realPR:
     fittedtrackids=shipPatRec.execute(self.SmearedHits,self.sTree,shipPatRec.ReconstructibleMCTracks)
     if fittedtrackids:
       tracknbr=0
       for ids in fittedtrackids:
         trackCandidates.append( [shipPatRec.theTracks[tracknbr],ids] )
	 tracknbr+=1
  else: # do fake pattern reco	 
   for atrack in hitPosLists:
    if atrack < 0: continue # these are hits not assigned to MC track because low E cut
    pdg    = self.sTree.MCTrack[atrack].GetPdgCode()
    if not self.PDG.GetParticle(pdg): continue # unknown particle
    meas = hitPosLists[atrack]
    nM = meas.size()
    if nM < 25 : continue                          # not enough hits to make a good trackfit 
    if len(stationCrossed[atrack]) < 3 : continue  # not enough stations crossed to make a good trackfit 
    if debug: 
       mctrack = self.sTree.MCTrack[atrack]
    charge = self.PDG.GetParticle(pdg).Charge()/(3.)
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
    trackCandidates.append([theTrack,atrack])
  for entry in trackCandidates:
#check
    atrack = entry[1]
    theTrack = entry[0]
    if not theTrack.checkConsistency():
     print 'Problem with track before fit, not consistent',atrack,theTrack
     continue
# do the fit
    try:  self.fitter.processTrack(theTrack) # processTrackWithRep(theTrack,rep,True)
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
    nTrack   = self.fGenFitArray.GetEntries()
    if not debug: theTrack.prune("CFL")  #  http://sourceforge.net/p/genfit/code/HEAD/tree/trunk/core/include/Track.h#l280 
    self.fGenFitArray[nTrack] = theTrack
    self.fitTrack2MC.push_back(atrack)
    if debug: 
     print 'save track',theTrack,chi2,nM,fitStatus.isFitConverged()
  self.fitTracks.Fill()
  self.mcLink.Fill()
  self.SHbranch.Fill()
  return nTrack+1
 def finish(self):
  del self.fitter
  print 'finished writing tree'
  self.sTree.Write()
  ut.errorSummary()
  ut.writeHists(h,"recohists.root")
  if realPR: ut.writeHists(shipPatRec.h,"recohists_patrec.root")


