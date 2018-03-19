import os,ROOT,shipVertex,shipDet_conf
if realPR == "Prev": import shipPatRec_prev as shipPatRec # The previous version of the pattern recognition
else: import shipPatRec
import shipunit as u
import rootUtils as ut
from array import array
import sys 
stop  = ROOT.TVector3()
start = ROOT.TVector3()

class ShipDigiReco:
 " convert FairSHiP MC hits / digitized hits to measurements"
 def __init__(self,fout,fgeo):
  self.fn = ROOT.TFile.Open(fout,'update')
  self.sTree     = self.fn.cbmsim
  if self.sTree.GetBranch("FitTracks"):
    print "remove RECO branches and rerun reconstruction"
    self.fn.Close()    
    # make a new file without reco branches
    f = ROOT.TFile(fout)
    sTree = f.cbmsim
    if sTree.GetBranch("FitTracks"): sTree.SetBranchStatus("FitTracks",0)
    if sTree.GetBranch("goodTracks"): sTree.SetBranchStatus("goodTracks",0)
    if sTree.GetBranch("VetoHitOnTrack"): sTree.SetBranchStatus("VetoHitOnTrack",0)
    if sTree.GetBranch("Particles"): sTree.SetBranchStatus("Particles",0)
    if sTree.GetBranch("fitTrack2MC"): sTree.SetBranchStatus("fitTrack2MC",0)
    if sTree.GetBranch("EcalClusters"): sTree.SetBranchStatus("EcalClusters",0)     
    if sTree.GetBranch("EcalReconstructed"): sTree.SetBranchStatus("EcalReconstructed",0)     
    if sTree.GetBranch("Pid"): sTree.SetBranchStatus("Pid",0)  
    if sTree.GetBranch("Digi_StrawtubesHits"): sTree.SetBranchStatus("Digi_StrawtubesHits",0)
    if sTree.GetBranch("Digi_SBTHits"): sTree.SetBranchStatus("Digi_SBTHits",0)
    if sTree.GetBranch("digiSBT2MC"):   sTree.SetBranchStatus("digiSBT2MC",0)
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
                  "strawtubesPoint":"strawtubesPoint","EcalPointLite":"ecalPoint","HcalPointLite":"hcalPoint","splitcalPoint":"splitcalPoint"}
  for x in branch_class:
    if not self.sTree.GetBranch(x):
     self.dummyContainers[x+"_array"] = ROOT.TClonesArray(branch_class[x])
     self.dummyContainers[x] = self.sTree.Branch(x,self.dummyContainers[x+"_array"],32000,-1) 
     setattr(self.sTree,x,self.dummyContainers[x+"_array"])
     self.dummyContainers[x].Fill()
#   
  if self.sTree.GetBranch("GeoTracks"): self.sTree.SetBranchStatus("GeoTracks",0)
# prepare for output
# event header
  self.header  = ROOT.FairEventHeader()
  self.eventHeader  = self.sTree.Branch("ShipEventHeader",self.header,32000,-1)
# fitted tracks
  self.fGenFitArray = ROOT.TClonesArray("genfit::Track") 
  self.fGenFitArray.BypassStreamer(ROOT.kFALSE)
  self.fitTrack2MC  = ROOT.std.vector('int')()
  self.goodTracksVect  = ROOT.std.vector('int')()
  self.mcLink      = self.sTree.Branch("fitTrack2MC",self.fitTrack2MC,32000,-1)
  self.fitTracks   = self.sTree.Branch("FitTracks",  self.fGenFitArray,32000,-1)
  self.goodTracksBranch      = self.sTree.Branch("goodTracks",self.goodTracksVect,32000,-1)
  self.fTrackletsArray = ROOT.TClonesArray("Tracklet") 
  self.Tracklets   = self.sTree.Branch("Tracklets",  self.fTrackletsArray,32000,-1)
#
  self.digiStraw    = ROOT.TClonesArray("strawtubesHit")
  self.digiStrawBranch   = self.sTree.Branch("Digi_StrawtubesHits",self.digiStraw,32000,-1)
  self.digiSBT    = ROOT.TClonesArray("vetoHit")
  self.digiSBTBranch=self.sTree.Branch("Digi_SBTHits",self.digiSBT,32000,-1)
  self.vetoHitOnTrackArray    = ROOT.TClonesArray("vetoHitOnTrack")
  self.vetoHitOnTrackBranch=self.sTree.Branch("VetoHitOnTrack",self.vetoHitOnTrackArray,32000,-1)
  self.digiSBT2MC  = ROOT.std.vector('std::vector< int >')()
  self.mcLinkSBT   = self.sTree.Branch("digiSBT2MC",self.digiSBT2MC,32000,-1)
# for the digitizing step
  self.v_drift = modules["Strawtubes"].StrawVdrift()
  self.sigma_spatial = modules["Strawtubes"].StrawSigmaSpatial()

# setup ecal reconstruction
  self.caloTasks = []  
  if self.sTree.GetBranch("EcalPoint"):
# Creates. exports and fills calorimeter structure
   dflag = 0
   if debug: dflag = 10
   ecalGeo = ecalGeoFile+'z'+str(ShipGeo.ecal.z)+".geo"
   if not ecalGeo in os.listdir(os.environ["FAIRSHIP"]+"/geometry"): shipDet_conf.makeEcalGeoFile(ShipGeo.ecal.z,ShipGeo.ecal.File)
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
   self.caloTasks.append(shipPid.Task(self))
# prepare vertexing
  self.Vertexing = shipVertex.Task(h,self.sTree)
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
   self.EcalClusters = self.sTree.Branch("EcalClusters",ecalClusters,32000,-1)
   self.EcalReconstructed = self.sTree.Branch("EcalReconstructed",ecalReconstructed,32000,-1)
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
  self.fitter.setMaxIterations(50)
  if debug: self.fitter.setDebugLvl(1) # produces lot of printout
  #set to True if "real" pattern recognition is required also
  if debug == True: shipPatRec.debug = 1

# for 'real' PatRec
  shipPatRec.initialize(fgeo)

 def reconstruct(self):
   ntracks = self.findTracks()
   nGoodTracks = self.findGoodTracks()
   self.linkVetoOnTracks()
   for x in self.caloTasks: 
    if hasattr(x,'execute'): x.execute()
    elif x.GetName() == 'ecalFiller': x.Exec('start',self.sTree.EcalPointLite)
    elif x.GetName() == 'ecalMatch':  x.Exec('start',self.ecalReconstructed, self.sTree.MCTrack)
    else : x.Exec('start')
   if len(self.caloTasks)>0:
    self.EcalClusters.Fill()
    self.EcalReconstructed.Fill()
   if vertexing:
# now go for 2-track combinations
    self.Vertexing.execute()

 def digitize(self):
   self.sTree.t0 = self.random.Rndm()*1*u.microsecond
   self.header.SetEventTime( self.sTree.t0 )
   self.header.SetRunId( self.sTree.MCEventHeader.GetRunID() )
   self.header.SetMCEntryNumber( self.sTree.MCEventHeader.GetEventID() )  # counts from 1
   self.eventHeader.Fill()
   self.digiSBT.Delete()
   self.digiSBT2MC.clear()
   self.digitizeSBT()
   self.digiSBTBranch.Fill()
   self.mcLinkSBT.Fill()
   self.digiStraw.Delete()
   self.digitizeStrawTubes()
   self.digiStrawBranch.Fill()
 def digitizeSBT(self):
     ElossPerDetId    = {}
     tOfFlight        = {}
     listOfVetoPoints = {}
     key=-1
     for aMCPoint in self.sTree.vetoPoint:
       key+=1
       detID=aMCPoint.GetDetectorID()
       if not detID>100000: continue  # not a LiSc or plastic detector
       Eloss=aMCPoint.GetEnergyLoss()
       if not ElossPerDetId.has_key(detID): 
        ElossPerDetId[detID]=0
        listOfVetoPoints[detID]=[]
        tOfFlight[detID]=[]
       ElossPerDetId[detID] += Eloss
       listOfVetoPoints[detID].append(key)
       tOfFlight[detID].append(aMCPoint.GetTime())
     index=0
     for seg in ElossPerDetId:
       aHit = ROOT.vetoHit(seg,ElossPerDetId[seg])
       aHit.SetTDC(min( tOfFlight[seg] ) + self.sTree.t0 )
       if self.digiSBT.GetSize() == index: 
          self.digiSBT.Expand(index+1000)
       if seg<999999 and ElossPerDetId[seg]<0.045:    aHit.setInvalid()  # threshold for liquid scintillator, source Berlin group
       if seg>999999 and ElossPerDetId[seg]<0.001:    aHit.setInvalid()  # precise threshold for plastic to be determined 
       self.digiSBT[index] = aHit
       v = ROOT.std.vector('int')()
       for x in listOfVetoPoints[seg]:
           v.push_back(x)
       self.digiSBT2MC.push_back(v)
       index=index+1
 def digitizeStrawTubes(self):
 # digitize FairSHiP MC hits  
   index = 0
   hitsPerDetId = {}
   for aMCPoint in self.sTree.strawtubesPoint:
     aHit = ROOT.strawtubesHit(aMCPoint,self.sTree.t0)
     if self.digiStraw.GetSize() == index: self.digiStraw.Expand(index+1000)
     self.digiStraw[index]=aHit
     detID = aHit.GetDetectorID() 
     if hitsPerDetId.has_key(detID):
       if self.digiStraw[hitsPerDetId[detID]].GetTDC() > aHit.GetTDC():
 # second hit with smaller tdc
        self.digiStraw[hitsPerDetId[detID]].setInvalid()
        hitsPerDetId[detID] = index
     else:
       hitsPerDetId[detID] = index         
     index+=1

 def withT0Estimate(self):
 # loop over all straw tdcs and make average, correct for ToF
  n = 0
  t0 = 0.
  key = -1
  SmearedHits = []
  v_drift = modules["Strawtubes"].StrawVdrift()
  modules["Strawtubes"].StrawEndPoints(10002001,start,stop)
  z1 = stop.z()
  for aDigi in self.digiStraw:
    key+=1
    if not aDigi.isValid: continue
    detID = aDigi.GetDetectorID()
# don't use hits from straw veto
    station = int(detID/10000000)
    if station > 4 : continue
    modules["Strawtubes"].StrawEndPoints(detID,start,stop)
    delt1 = (start[2]-z1)/u.speedOfLight
    t0+=aDigi.GetDigi()-delt1
    SmearedHits.append( {'digiHit':key,'xtop':stop.x(),'ytop':stop.y(),'z':stop.z(),'xbot':start.x(),'ybot':start.y(),'dist':aDigi.GetDigi()} )
    n+=1  
  if n>0: t0 = t0/n - 73.2*u.ns
  for s in SmearedHits:
    delt1 = (s['z']-z1)/u.speedOfLight
    s['dist'] = (s['dist'] -delt1 -t0)*v_drift 
  return SmearedHits

 def smearHits(self,no_amb=None):
 # smear strawtube points
  SmearedHits = []
  key = -1
  v_drift = modules["Strawtubes"].StrawVdrift()
  modules["Strawtubes"].StrawEndPoints(10002001,start,stop)
  z1 = stop.z()
  for aDigi in self.digiStraw:
     key+=1
     if not aDigi.isValid: continue
     detID = aDigi.GetDetectorID()
# don't use hits from straw veto
     station = int(detID/10000000)
     if station > 4 : continue
     modules["Strawtubes"].StrawEndPoints(detID,start,stop)
   #distance to wire
     delt1 = (start[2]-z1)/u.speedOfLight
     p=self.sTree.strawtubesPoint[key]
     # use true t0  construction: 
     #     fdigi = t0 + p->GetTime() + t_drift + ( stop[0]-p->GetX() )/ speedOfLight;
     smear = (aDigi.GetDigi() - self.sTree.t0  - p.GetTime() - ( stop[0]-p.GetX() )/ u.speedOfLight) * v_drift
     if no_amb: smear = p.dist2Wire()
     SmearedHits.append( {'digiHit':key,'xtop':stop.x(),'ytop':stop.y(),'z':stop.z(),'xbot':start.x(),'ybot':start.y(),'dist':smear} )
     # Note: top.z()==bot.z() unless misaligned, so only add key 'z' to smearedHit
     if abs(stop.y())==abs(start.y()): h['disty'].Fill(smear)
     if abs(stop.y())>abs(start.y()): h['distu'].Fill(smear)
     if abs(stop.y())<abs(start.y()): h['distv'].Fill(smear)

  return SmearedHits
  
 def findTracks(self):
  hitPosLists    = {}
  stationCrossed = {}
  fittedtrackids=[]
  listOfIndices  = {}
  self.fGenFitArray.Delete()
  self.fTrackletsArray.Delete()
  self.fitTrack2MC.clear()

#   
  if withT0:  self.SmearedHits = self.withT0Estimate()
  # old procedure, not including estimation of t0 
  else:       self.SmearedHits = self.smearHits(withNoStrawSmearing)

  nTrack = -1
  trackCandidates = []
  
  if realPR:
     if realPR == "Prev": # Runs previously used pattern recognition
        fittedtrackids=shipPatRec.execute(self.SmearedHits,self.sTree,shipPatRec.ReconstructibleMCTracks)
        if fittedtrackids:
           tracknbr=0
           for ids in fittedtrackids:
              trackCandidates.append( [shipPatRec.theTracks[tracknbr],ids] )
              tracknbr+=1
     else: # Runs new pattern recognition
        fittedtrackids, reco_tracks = shipPatRec.execute(self.SmearedHits,self.sTree,shipPatRec.ReconstructibleMCTracks, method=realPR)
         # Save hit ids of recognized tracks
        for atrack in reco_tracks.values():
            nTracks   = self.fTrackletsArray.GetEntries()
            aTracklet  = self.fTrackletsArray.ConstructedAt(nTracks)
            listOfHits = aTracklet.getList()
            aTracklet.setType(atrack['flag'])
            for index in atrack['hits']:
                listOfHits.push_back(index)
        if fittedtrackids:
            tracknbr=0
            for ids in fittedtrackids:
                trackCandidates.append( [shipPatRec.theTracks[tracknbr],ids] )
                tracknbr+=1
  else: # do fake pattern recognition
   for sm in self.SmearedHits:
    detID = self.digiStraw[sm['digiHit']].GetDetectorID()
    station = int(detID/10000000)
    trID = self.sTree.strawtubesPoint[sm['digiHit']].GetTrackID()
    if not hitPosLists.has_key(trID):   
      hitPosLists[trID]     = ROOT.std.vector('TVectorD')()
      listOfIndices[trID] = [] 
      stationCrossed[trID]  = {}
    m = array('d',[sm['xtop'],sm['ytop'],sm['z'],sm['xbot'],sm['ybot'],sm['z'],sm['dist']])
    hitPosLists[trID].push_back(ROOT.TVectorD(7,m))
    listOfIndices[trID].append(sm['digiHit'])
    if not stationCrossed[trID].has_key(station): stationCrossed[trID][station]=0
    stationCrossed[trID][station]+=1
#
   for atrack in listOfIndices:
     # make tracklets out of trackCandidates, just for testing, should be output of proper pattern recognition
    nTracks   = self.fTrackletsArray.GetEntries()
    aTracklet  = self.fTrackletsArray.ConstructedAt(nTracks)
    listOfHits = aTracklet.getList()
    aTracklet.setType(3)
    for index in listOfIndices[atrack]:
      listOfHits.push_back(index)
#  
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
    resolution = self.sigma_spatial
    if withT0: resolution = resolution*1.4 # worse resolution due to t0 estimate
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
      measurement.setMaxDistance(ShipGeo.strawtubes.InnerStrawDiameter/2.)
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
      if debug: print "genfit failed to fit track"
      error = "genfit failed to fit track"
      ut.reportError(error)
      continue
#check
    if not theTrack.checkConsistency():
     if debug: print 'Problem with track after fit, not consistent',atrack,theTrack
     error = "Problem with track after fit, not consistent"
     ut.reportError(error)
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
     print 'save track',theTrack,chi2,nmeas,fitStatus.isFitConverged()
  self.Tracklets.Fill()
  self.fitTracks.Fill()
  self.mcLink.Fill()
# debug 
  if debug:
   print 'save tracklets:' 
   for x in self.sTree.Tracklets:
    print x.getType(),x.getList().size()
  return nTrack+1

 def findGoodTracks(self):
   self.goodTracksVect.clear()
   nGoodTracks = 0
   for i,track in enumerate(self.fGenFitArray):
    fitStatus = track.getFitStatus()
    if not fitStatus.isFitConverged(): continue
    nmeas = fitStatus.getNdf()
    chi2  = fitStatus.getChi2()/nmeas
    if chi2<50 and not chi2<0:
      self.goodTracksVect.push_back(i)
      nGoodTracks+=1
   self.goodTracksBranch.Fill()
   return nGoodTracks

 def findVetoHitOnTrack(self,track):
   distMin = 99999.
   vetoHitOnTrack = ROOT.vetoHitOnTrack()
   xx  = track.getFittedState()
   rep   = ROOT.genfit.RKTrackRep(xx.getPDG())
   state = ROOT.genfit.StateOnPlane(rep)
   rep.setPosMom(state,xx.getPos(),xx.getMom())
   for i,vetoHit in enumerate(self.digiSBT):
     vetoHitPos = vetoHit.GetXYZ()
     try:
      rep.extrapolateToPoint(state,vetoHitPos,False)
     except:
      error =  "shipDigiReco::findVetoHitOnTrack extrapolation did not worked"
      ut.reportError(error)
      if debug: print error
      continue
     dist = (rep.getPos(state) - vetoHitPos).Mag()
     if dist < distMin:
       distMin = dist
       vetoHitOnTrack.SetDist(distMin)
       vetoHitOnTrack.SetHitID(i)
   return vetoHitOnTrack
 
 def linkVetoOnTracks(self):
   self.vetoHitOnTrackArray.Delete()
   index = 0
   for goodTrak in self.goodTracksVect:
     track = self.fGenFitArray[goodTrak]
     if self.vetoHitOnTrackArray.GetSize() == index: self.vetoHitOnTrackArray.Expand(index+1000)
     self.vetoHitOnTrackArray[index] = self.findVetoHitOnTrack(track)
     index+=1
   self.vetoHitOnTrackBranch.Fill()

 def finish(self):
  del self.fitter
  print 'finished writing tree'
  self.sTree.Write()
  ut.errorSummary()
  ut.writeHists(h,"recohists.root")
  if realPR: shipPatRec.finalize()
