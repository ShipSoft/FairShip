import os,ROOT,shipPatRec,charmDet_conf
import shipunit as u
import rootUtils as ut

from array import array
import sys, os


stop  = ROOT.TVector3()
start = ROOT.TVector3()

geoFile   = 'geofile_full.conical.PGplus-TGeant4.root'
fgeo = ROOT.TFile(geoFile)
sGeo = fgeo.FAIRGeom


class MufluxDigiReco:
 " convert FairSHiP MC hits / digitized hits to measurements"
 def __init__(self,fout,fgeo):
  outdir=os.getcwd()
  outfile=outdir+"/"+fout
  self.fn = ROOT.TFile(fout,'update')
  self.sTree     = self.fn.cbmsim
  if self.sTree.GetBranch("FitTracks"):
    print "remove RECO branches and rerun reconstruction"
    self.fn.Close()    
    # make a new file without reco branches
    f = ROOT.TFile(fout)
    sTree = f.cbmsim
    if sTree.GetBranch("FitTracks"): sTree.SetBranchStatus("FitTracks",0)
    if sTree.GetBranch("Particles"): sTree.SetBranchStatus("Particles",0)
    if sTree.GetBranch("fitTrack2MC"): sTree.SetBranchStatus("fitTrack2MC",0)
    if sTree.GetBranch("FitTracks_PR"): sTree.SetBranchStatus("FitTracks_PR",0)
    if sTree.GetBranch("Particles_PR"): sTree.SetBranchStatus("Particles_PR",0)
    if sTree.GetBranch("fitTrack2MC_PR"): sTree.SetBranchStatus("fitTrack2MC_PR",0)
  
    if sTree.GetBranch("Digi_MufluxSpectrometerHits"): sTree.SetBranchStatus("Digi_MufluxSpectrometerHits",0)     
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
#  branch_class = {"vetoPoint":"vetoPoint","ShipRpcPoint":"ShipRpcPoint","TargetPoint":"TargetPoint",\
#                  "strawtubesPoint":"strawtubesPoint","EcalPointLite":"ecalPoint","HcalPointLite":"hcalPoint"}
  branch_class = {"MufluxSpectrometerPoint":"MufluxSpectrometerPoint","MuonTaggerPoint":"MuonTaggerPoint"}		  
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
  self.mcLink      = self.sTree.Branch("fitTrack2MC"+realPR,self.fitTrack2MC,32000,-1)
  self.fitTracks   = self.sTree.Branch("FitTracks"+realPR,  self.fGenFitArray,32000,-1)
#

  self.digiMufluxSpectrometer    = ROOT.TClonesArray("MufluxSpectrometerHit")
  self.digiMufluxSpectrometerBranch   = self.sTree.Branch("Digi_MufluxSpectrometerHits",self.digiMufluxSpectrometer,32000,-1)
# for the digitizing step
  self.v_drift = modules["MufluxSpectrometer"].TubeVdrift()
  self.sigma_spatial = modules["MufluxSpectrometer"].TubeSigmaSpatial()
  self.viewangle = modules["MufluxSpectrometer"].ViewAngle()
   
# setup random number generator 
  self.random = ROOT.TRandom()
  ROOT.gRandom.SetSeed(13)
  self.PDG = ROOT.TDatabasePDG.Instance()
# 
 # access ShipTree
  self.sTree.GetEvent(0)
  self.geoMat =  ROOT.genfit.TGeoMaterialInterface()
# init geometry and mag. field
  gMan  = ROOT.gGeoManager
  #import geomGeant4
  #fieldMaker = geomGeant4.addVMCFields('field/GoliathBFieldSetup.txt', False)
  #geomGeant4.printVMCFields()
  self.bfield = ROOT.genfit.FairShipFields()
  self.fM = ROOT.genfit.FieldManager.getInstance()
  self.fM.init(self.bfield) 
  
  ROOT.genfit.MaterialEffects.getInstance().init(self.geoMat)

 # init fitter, to be done before importing shipPatRec
  self.fitter      = ROOT.genfit.DAF()
  if debug: self.fitter.setDebugLvl(1) # produces lot of printout
  #set to True if "real" pattern recognition is required also
  #if debug == True: shipPatRec.debug = 1

# for 'real' PatRec
  #shipPatRec.initialize(fgeo)

 def reconstruct(self):
   ntracks = self.findTracks()

 def digitize(self):

   self.sTree.t0 = self.random.Rndm()*1*u.microsecond
   self.header.SetEventTime( self.sTree.t0 )
   self.header.SetRunId( self.sTree.MCEventHeader.GetRunID() )
   self.header.SetMCEntryNumber( self.sTree.MCEventHeader.GetEventID() )  # counts from 1
   self.eventHeader.Fill()
   self.digiMufluxSpectrometer.Delete()
   self.digitizeMufluxSpectrometer()
   self.digiMufluxSpectrometerBranch.Fill()     

   
 def digitizeMufluxSpectrometer(self):
 # digitize FairSHiP MC hits  
   
   index = 0
   hitsPerDetId = {}

   for aMCPoint in self.sTree.MufluxSpectrometerPoint:
     aHit = ROOT.MufluxSpectrometerHit(aMCPoint,self.sTree.t0)
     if self.digiMufluxSpectrometer.GetSize() == index: self.digiMufluxSpectrometer.Expand(index+1000)
     self.digiMufluxSpectrometer[index]=aHit
     detID = aHit.GetDetectorID() 
     if hitsPerDetId.has_key(detID):
       if self.digiMufluxSpectrometer[hitsPerDetId[detID]].tdc() > aHit.tdc():
 # second hit with smaller tdc
        self.digiMufluxSpectrometer[hitsPerDetId[detID]].setInvalid()
        hitsPerDetId[detID] = index
     else:
       hitsPerDetId[detID] = index         
     index+=1
     
   T1_entries_px = {}    
   T4_entries_px = {}   
   nMufluxHits = self.sTree.MufluxSpectrometerPoint.GetEntriesFast()        
   for i in range(nMufluxHits):
     MufluxHit = self.sTree.MufluxSpectrometerPoint[i]
     detector = sGeo.FindNode(MufluxHit.GetX(),MufluxHit.GetY(),MufluxHit.GetZ()).GetName()
     MufluxTrackId = MufluxHit.GetTrackID()  
     pid = MufluxHit.PdgCode()
     xcoord = MufluxHit.GetX()
     ycoord = MufluxHit.GetY()
     if abs(pid)==13:  
       if (detector[0:8]=="gas_12_1"):      	 
          rc=h['hits-T1'].Fill(xcoord,ycoord) 
       if (detector[0:9]=="gas_12_10"):      
	  rc=h['hits-T1x'].Fill(xcoord,ycoord)
       if (detector[0:9]=="gas_12_11"):      	 
          rc=h['hits-T1u'].Fill(xcoord,ycoord)
       if (detector[0:8]=="gas_12_2"):      	 
          rc=h['hits-T2'].Fill(xcoord,ycoord) 
       if (detector[0:9]=="gas_12_20"):      
	  rc=h['hits-T2v'].Fill(xcoord,ycoord)
       if (detector[0:9]=="gas_12_21"):      	 
          rc=h['hits-T2x'].Fill(xcoord,ycoord)   
       if (detector[0:5]=="gas_3"):      	 
          rc=h['hits-T3'].Fill(xcoord,ycoord) 	  
       if (detector[0:5]=="gas_4"):      	 
          rc=h['hits-T4'].Fill(xcoord,ycoord) 	
	  	       
     if (detector[0:9]=="gas_12_10"): 
          if T1_entries_px.has_key(MufluxTrackId):	   
	     continue
          else:	
             if abs(pid)==13 :  	   	
	        T1_entries_px[MufluxTrackId]=[MufluxHit.GetPx()]
	 
     if (detector[0:5]=="gas_4"):  
         if T4_entries_px.has_key(MufluxTrackId):	   
	     continue
         else:		
	     pid = MufluxHit.PdgCode() 
         if abs(pid)==13 :  	   
	        T4_entries_px[MufluxTrackId]=[MufluxHit.GetPx()]

   for i in range(nMufluxHits):
     MufluxHit = self.sTree.MufluxSpectrometerPoint[i]
     MufluxTrackId = MufluxHit.GetTrackID() 
     if (T1_entries_px.get(MufluxTrackId) is None or T4_entries_px.get(MufluxTrackId) is None) :
       continue
     else:
      rc=h['pt-kick'].Fill(T1_entries_px.get(MufluxTrackId)[0]-T4_entries_px.get(MufluxTrackId)[0])
    
 def withT0Estimate(self):
 # loop over all straw tdcs and make average, correct for ToF
  n = 0
  t0 = 0.
  key = -1
  SmearedHits = []
  v_drift = modules["MufluxSpectrometer"].TubeVdrift()
  #modules["MufluxSpectrometer"].TubeEndPoints(10000001,start,stop)
  modules["MufluxSpectrometer"].TubeEndPoints(10002001,start,stop)
  z1 = stop.z()
  for aDigi in self.digiMufluxSpectrometer:
    key+=1
    if not aDigi.isValid: continue
    detID = aDigi.GetDetectorID()
# don't use hits from straw veto
    station = int(detID/10000000)
    if station > 4 : continue
    modules["MufluxSpectrometer"].TubeEndPoints(detID,start,stop)
    delt1 = (start[2]-z1)/u.speedOfLight
    t0+=aDigi.GetDigi()-delt1
    SmearedHits.append( {'digiHit':key,'xtop':stop.x(),'ytop':stop.y(),'z':stop.z(),'xbot':start.x(),'ybot':start.y(),'dist':aDigi.GetDigi()} )
    n+=1  
  if n>0: 
     t0 = t0/n - 73.2*u.ns
     print "t0 ",t0
  for s in SmearedHits:
    delt1 = (s['z']-z1)/u.speedOfLight
    s['dist'] = (s['dist'] -delt1 -t0)*v_drift 
    print "s['dist']",s['dist']
  return SmearedHits

 def smearHits(self,no_amb=None):
 # smear strawtube points
  SmearedHits = []
  key = -1
  for ahit in self.sTree.MufluxSpectrometerPoint:
     key+=1
     detID = ahit.GetDetectorID()
     top = ROOT.TVector3()
     bot = ROOT.TVector3()
     modules["MufluxSpectrometer"].TubeEndPoints(detID,bot,top)
   #distance to wire, and smear it.
     dw  = ahit.dist2Wire()
     smear = dw
     if not no_amb: 
        #print "detID ",detID," viewangle ",self.viewangle
        #if ((str(detID)[0:1]=="3") or (str(detID)[0:1]=="4")):
           #smear = abs(self.random.Gaus(dw,8*self.sigma_spatial))
	#else: 
	   smear = abs(self.random.Gaus(dw,self.sigma_spatial))
     #print "smear",smear
     SmearedHits.append( {'digiHit':key,'xtop':top.x(),'ytop':top.y(),'z':top.z(),'xbot':bot.x(),'ybot':bot.y(),'dist':smear} )
     # Note: top.z()==bot.z() unless misaligned, so only add key 'z' to smearedHit
     if abs(top.y())==abs(bot.y()): h['disty'].Fill(dw)
     if abs(top.y())>abs(bot.y()): h['distu'].Fill(dw)
     if abs(top.y())<abs(bot.y()): h['distv'].Fill(dw)

  return SmearedHits
  
 def getPtruthFirst(self,mcPartKey):
   Ptruth,Ptruthx,Ptruthy,Ptruthz = -1.,-1.,-1.,-1.
   for ahit in self.sTree.MufluxSpectrometerPoint:
     if ahit.GetTrackID() == mcPartKey:
        Ptruthx,Ptruthy,Ptruthz = ahit.GetPx(),ahit.GetPy(),ahit.GetPz()
        Ptruth  = ROOT.TMath.Sqrt(Ptruthx**2+Ptruthy**2+Ptruthz**2)
        break
   return Ptruth,Ptruthx,Ptruthy,Ptruthz  
   
 def getPtruthAtOrigin(self,mcPartKey):
   Ptruth,Ptruthx,Ptruthy,Ptruthz = -1.,-1.,-1.,-1.
   atrack=self.sTree.MCTrack[mcPartKey]
   Ptruthx= atrack.GetPx()
   Ptruthy= atrack.GetPy()  
   Ptruthz= atrack.GetPz()      
   Ptruth  = ROOT.TMath.Sqrt(Ptruthx**2+Ptruthy**2+Ptruthz**2)
   return Ptruth,Ptruthx,Ptruthy,Ptruthz  
   
 def findTracks(self):
  hitPosLists    = {}
  hitPosLists_noT4    = {}
  stationCrossed = {}
  stationCrossed_noT4 = {}
  fittedtrackids=[]
  self.fGenFitArray.Delete()
  self.fitTrack2MC.clear()
#   
  if withT0:  self.SmearedHits = self.withT0Estimate()
  # old procedure, not including estimation of t0 
  else:       self.SmearedHits = self.smearHits(withNoStrawSmearing)

  nTrack = -1
  trackCandidates = []
  trackCandidates_noT4 = []
  if realPR:
     fittedtrackids=shipPatRec.execute(self.SmearedHits,self.sTree,shipPatRec.ReconstructibleMCTracks)
     if fittedtrackids:
       tracknbr=0
       for ids in fittedtrackids:
         trackCandidates.append( [shipPatRec.theTracks[tracknbr],ids] )
	 tracknbr+=1
  else: # do fake pattern reco	 
   for sm in self.SmearedHits:
    detID = self.digiMufluxSpectrometer[sm['digiHit']].GetDetectorID()
    station = int(detID/10000000)

    trID = self.sTree.MufluxSpectrometerPoint[sm['digiHit']].GetTrackID()
    if not hitPosLists.has_key(trID):   
      hitPosLists[trID]     = ROOT.std.vector('TVectorD')()
      stationCrossed[trID]  = {}
    m = array('d',[sm['xtop'],sm['ytop'],sm['z'],sm['xbot'],sm['ybot'],sm['z'],sm['dist']])
    hitPosLists[trID].push_back(ROOT.TVectorD(7,m))
    if (int(detID/1000000)!=40): 
       if not hitPosLists_noT4.has_key(trID):   
          hitPosLists_noT4[trID]     = ROOT.std.vector('TVectorD')()
          stationCrossed_noT4[trID]  = {}	  
       m_noT4 = array('d',[sm['xtop'],sm['ytop'],sm['z'],sm['xbot'],sm['ybot'],sm['z'],sm['dist']])             
       hitPosLists_noT4[trID].push_back(ROOT.TVectorD(7,m_noT4))
       if not stationCrossed_noT4[trID].has_key(station): stationCrossed_noT4[trID][station]=0
       stationCrossed_noT4[trID][station]+=1         
    # comment next 3 lines for hits in t1-3
    #print "debug detid ",detID," m ",m
    if not stationCrossed[trID].has_key(station): stationCrossed[trID][station]=0
    stationCrossed[trID][station]+=1    
       
     
    #uncomment next 4 lines for hits in t1-3    
    #if station<4 : 
    #   hitPosLists[trID].push_back(ROOT.TVectorD(7,m))    
    #   if not stationCrossed[trID].has_key(station): stationCrossed[trID][station]=0
    #   stationCrossed[trID][station]+=1   
       
   for atrack in hitPosLists:
    if atrack < 0: continue # these are hits not assigned to MC track because low E cut
    pdg    = self.sTree.MCTrack[atrack].GetPdgCode()
    #if not self.PDG.GetParticle(pdg): continue # unknown particle
    if not abs(pdg)==13: continue # only keep muons
    meas = hitPosLists[atrack]
    nM = meas.size()

    #if nM < 12 : continue                          # not enough hits to make a good trackfit 
    #comment for hits in t1-3
    if len(stationCrossed[atrack]) < 4 : continue  # not enough stations crossed to make a good trackfit 
    
    #uncomment for hits in t1-3
    #if len(stationCrossed[atrack]) < 3 : continue  # not enough stations crossed to make a good trackfit 
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
      #measurement.setMaxDistance(0.5*u.cm)
      measurement.setMaxDistance(1.85*u.cm)
      # measurement.setLeftRightResolution(-1)
      tp.addRawMeasurement(measurement) # package measurement in the TrackPoint                                          
      theTrack.insertPoint(tp)  # add point to Track
   # print "debug meas",atrack,nM,stationCrossed[atrack],self.sTree.MCTrack[atrack],pdg
    trackCandidates.append([theTrack,atrack])
    
   #if 1==0:
  for atrack in hitPosLists_noT4:
    if atrack < 0: continue # these are hits not assigned to MC track because low E cut
    pdg    = self.sTree.MCTrack[atrack].GetPdgCode()
    #if not self.PDG.GetParticle(pdg): continue # unknown particle
    if not abs(pdg)==13: continue # only keep muons
    meas = hitPosLists_noT4[atrack]
    nM = meas.size()

    #if nM < 6 : continue                          # not enough hits to make a good trackfit 
    #comment for hits in t1-3

    #if len(stationCrossed_noT4[atrack]) < 4 : continue  # not enough stations crossed to make a good trackfit 
    
    #uncomment for hits in t1-3
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
      #measurement.setMaxDistance(0.5*u.cm)
      measurement.setMaxDistance(1.85*u.cm)
      # measurement.setLeftRightResolution(-1)
      tp.addRawMeasurement(measurement) # package measurement in the TrackPoint                                          
      theTrack.insertPoint(tp)  # add point to Track
      #print "debug meas",atrack,nM,stationCrossed[atrack],self.sTree.MCTrack[atrack],pdg
    trackCandidates_noT4.append([theTrack,atrack])
  #print len(trackCandidates)," trackCandidates ",len(trackCandidates_noT4)," trackCandidates_noT4)"
  
  for entry in trackCandidates:
#check
    #print "fitting with stereo"
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
     #print 'Problem with track after fit, not consistent',atrack,theTrack
     continue
    fitStatus   = theTrack.getFitStatus()
    nmeas = fitStatus.getNdf()   
    chi2        = fitStatus.getChi2()/nmeas  
    pvalue = fitStatus.getPVal()
    #if pvalue < 0.05:
    #  print "P value too low. Rejecting track."
    #  continue
    h['nmeas'].Fill(nmeas)    
    h['chi2'].Fill(chi2)
    h['p-value'].Fill(pvalue)
    try:

      fittedState = theTrack.getFittedState()
      fittedMom = fittedState.getMomMag()
      h['p-fittedtracks'].Fill(fittedMom)
      h['1/p-fittedtracks'].Fill(1./fittedMom)
      Px,Py,Pz = fittedState.getMom().x(),fittedState.getMom().y(),fittedState.getMom().z()
      P = fittedMom
      Ptruth,Ptruthx,Ptruthy,Ptruthz = self.getPtruthFirst(atrack)
      Pgun,Pgunx,Pguny,Pgunz = self.getPtruthAtOrigin(atrack)
      if Pz !=0: 
        pxpzfitted = Px/Pz
        pypzfitted = Py/Pz	
	if Ptruthz !=0:
          pxpztrue = Ptruthx/Ptruthz
          pypztrue = Ptruthy/Ptruthz	  
	  h['Px/Pzfitted'].Fill(pxpzfitted)
          h['Py/Pzfitted'].Fill(pypzfitted)
	  h['Px/Pztrue'].Fill(pxpztrue)
          h['Py/Pztrue'].Fill(pypztrue)		
          h['Px/Pzfitted-Px/Pztruth'].Fill(Ptruth,pxpzfitted-pxpztrue)
          h['Py/Pzfitted-Py/Pztruth'].Fill(Ptruth,pypzfitted-pypztrue)	  
      h['ptruth'].Fill(Ptruth)  
      delPOverP = (P/Ptruth)-1
      invdelPOverP = (Ptruth/P)-1
      if 1==0:
       if invdelPOverP < -0.8:
         print "invdelPOverP = ",invdelPOverP
         print "Ptruth =",Ptruth," Pfitted =",P
	 for n in range(hitPosLists[atrack].size()):	 
	    print "hit=",n," x(top) ",hitPosLists[atrack][n][0]," y(top) ",hitPosLists[atrack][n][1]," z ",hitPosLists[atrack][n][2]," x(bot) ",hitPosLists[atrack][n][3]," y(bot) ", hitPosLists[atrack][n][4], " dist ", hitPosLists[atrack][n][6]            
            nMufluxHits = self.sTree.MufluxSpectrometerPoint.GetEntriesFast()    
            for i in range(nMufluxHits):
              MufluxHit = self.sTree.MufluxSpectrometerPoint[i]
	      if ((hitPosLists[atrack][n][0]+1.8 > MufluxHit.GetX()) or(hitPosLists[atrack][n][3]+1.8 > MufluxHit.GetX())) and ((hitPosLists[atrack][n][0]-1.8<MufluxHit.GetX()) or (hitPosLists[atrack][n][3]-1.8<MufluxHit.GetX())) and (hitPosLists[atrack][n][2]+1.>MufluxHit.GetZ()) and (hitPosLists[atrack][n][2]-1.<MufluxHit.GetZ()):
	        print "hit x=",MufluxHit.GetX()," y=",MufluxHit.GetY()," z=",MufluxHit.GetZ()
     
     
      h['delPOverP'].Fill(Ptruth,delPOverP)  
      h['invdelPOverP'].Fill(Ptruth,invdelPOverP)  
      h['deltaPOverP'].Fill(Ptruth,delPOverP)   
      h['Pfitted-Pgun'].Fill(Pgun,P)  
      #print "end fitting with stereo"
        
    except: 
       print "problem with fittedstate"
       continue    

   #if 1==0:
  for entry in trackCandidates_noT4:
#check
    #print "fitting without stereo hits"
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
    pvalue = fitStatus.getPVal()
    #if pvalue < 0.05:
    #  print "P value too low. Rejecting track."
    #  continue
    h['nmeas-noT4'].Fill(nmeas)    
    h['chi2-noT4'].Fill(chi2)
    h['p-value-noT4'].Fill(pvalue)
    try:

      fittedState = theTrack.getFittedState()
      fittedMom = fittedState.getMomMag()
      h['p-fittedtracks-noT4'].Fill(fittedMom)
      h['1/p-fittedtracks-noT4'].Fill(1./fittedMom)
      Px,Py,Pz = fittedState.getMom().x(),fittedState.getMom().y(),fittedState.getMom().z()
      P = fittedMom
      Ptruth,Ptruthx,Ptruthy,Ptruthz = self.getPtruthFirst(atrack)
      Pgun,Pgunx,Pguny,Pgunz = self.getPtruthAtOrigin(atrack)     
      if Pz !=0: 
        pxpzfitted = Px/Pz
        pypzfitted = Py/Pz	
	if Ptruthz !=0:
          pxpztrue = Ptruthx/Ptruthz
          pypztrue = Ptruthy/Ptruthz	  
          h['Px/Pzfitted-Px/Pztruth-noT4'].Fill(Ptruth,pxpzfitted-pxpztrue)
          h['Py/Pzfitted-Py/Pztruth-noT4'].Fill(Ptruth,pypzfitted-pypztrue)	       
	  h['Px/Pzfitted-noT4'].Fill(pxpzfitted)
          h['Py/Pzfitted-noT4'].Fill(pypzfitted)
	  h['Px/Pztrue-noT4'].Fill(pxpztrue)
          h['Py/Pztrue-noT4'].Fill(pypztrue)      
      
      h['ptruth-noT4'].Fill(Ptruth) 
      delPOverP = (P/Ptruth)-1
      invdelPOverP = (Ptruth/P)-1
      h['delPOverP-noT4'].Fill(Ptruth,delPOverP) 
      h['invdelPOverP-noT4'].Fill(Ptruth,invdelPOverP)    
      h['deltaPOverP-noT4'].Fill(Ptruth,delPOverP)    
      h['Pfitted-Pgun-noT4'].Fill(Pgun,P)  
      #print "end fitting without stereo hits"        
    except: 
       print "noT4 track: problem with fittedstate"
       continue           
      
# make track persistent
    nTrack   = self.fGenFitArray.GetEntries()
    if not debug: theTrack.prune("CFL")  #  http://sourceforge.net/p/genfit/code/HEAD/tree/trunk/core/include/Track.h#l280 
    self.fGenFitArray[nTrack] = theTrack
    self.fitTrack2MC.push_back(atrack)
    if debug: 
        print 'save track',theTrack,chi2,nM,fitStatus.isFitConverged()
  self.fitTracks.Fill()
  self.mcLink.Fill()
  return nTrack+1
  
 def finish(self):
  del self.fitter
  print 'finished writing tree'
  self.sTree.Write()
  ut.errorSummary()
  ut.writeHists(h,"recohists.root")
  if realPR: ut.writeHists(shipPatRec.h,"recohists_patrec.root")


