# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

import os,ROOT,shipVertex,shipDet_conf
import global_variables
import shipPatRec
import shipunit as u
import rootUtils as ut
from array import array
import sys
from math import fabs
from backports import tdirectory634
from detectors.timeDetector import timeDetector
from detectors.MTCDetector import MTCDetector
from detectors.SBTDetector import SBTDetector
from detectors.UpstreamTaggerDetector import UpstreamTaggerDetector
from detectors.strawtubesDetector import strawtubesDetector
from detectors.splitcalDetector import splitcalDetector

class ShipDigiReco:
 " convert FairSHiP MC hits / digitized hits to measurements"
 def __init__(self, finput, fout, fgeo):
  # Open input file (read-only) and get the MC tree
  self.inputFile = ROOT.TFile.Open(finput, 'read')
  self.sTree = self.inputFile["cbmsim"]

  # Create output file and new tree for digi/reco branches only
  self.outputFile = ROOT.TFile.Open(fout, 'recreate')
  self.recoTree = ROOT.TTree("ship_reco_sim", "Digitization and Reconstruction")

  # Disable GeoTracks branch if present in input
  if self.sTree.GetBranch("GeoTracks"):
    self.sTree.SetBranchStatus("GeoTracks", 0)
  # prepare for output
  # event header
  self.header  = ROOT.FairEventHeader()
  self.eventHeader  = self.recoTree.Branch("ShipEventHeader",self.header,32000,-1)
  # fitted tracks
  # Must use pointer storage: genfit::Track has circular references with TrackPoint
  # requiring stable memory addresses (value storage would invalidate back-pointers on vector resize)
  self.fGenFitArray = ROOT.std.vector("genfit::Track*")()
  self.fitTrack2MC  = ROOT.std.vector('int')()
  self.goodTracksVect  = ROOT.std.vector('int')()
  self.mcLink      = self.recoTree.Branch("fitTrack2MC",self.fitTrack2MC,32000,-1)
  self.fitTracks   = self.recoTree.Branch("FitTracks",  self.fGenFitArray,32000,-1)
  self.goodTracksBranch      = self.recoTree.Branch("goodTracks",self.goodTracksVect,32000,-1)
  self.fTrackletsArray = ROOT.std.vector("Tracklet")()
  self.Tracklets   = self.recoTree.Branch("Tracklets",  self.fTrackletsArray,32000,-1)
  #
  self.strawtubes = strawtubesDetector("strawtubes", self.sTree, outtree=self.recoTree)

  self.digiMTC = MTCDetector("MTCDet", self.sTree, 'MTC', outtree=self.recoTree)
  self.digiSBT = SBTDetector("veto", self.sTree, 'SBT', mcBranchName="digiSBT2MC", outtree=self.recoTree)
  self.vetoHitOnTrackArray = ROOT.std.vector("vetoHitOnTrack")()
  self.vetoHitOnTrackBranch = self.recoTree.Branch("VetoHitOnTrack", self.vetoHitOnTrackArray)

  self.timeDetector = timeDetector("TimeDet", self.sTree, outtree=self.recoTree)
  self.upstreamTaggerDetector = UpstreamTaggerDetector("UpstreamTagger", self.sTree, outtree=self.recoTree)


  # for the digitizing step
  self.v_drift = global_variables.modules["strawtubes"].StrawVdrift()
  self.sigma_spatial = global_variables.modules["strawtubes"].StrawSigmaSpatial()
  # optional if present, splitcalCluster
  if self.sTree.GetBranch("splitcalPoint"):
   self.splitcalDetector = splitcalDetector("splitcal", self.sTree, outtree=self.recoTree)
   # Keep references for backward compatibility
   self.digiSplitcal = self.splitcalDetector.det
   self.recoSplitcal = self.splitcalDetector.reco


  # prepare vertexing
  self.Vertexing = shipVertex.Task(global_variables.h, self.recoTree, self.sTree)
  # setup random number generator
  self.random = ROOT.TRandom()
  ROOT.gRandom.SetSeed(13)
  self.PDG = ROOT.TDatabasePDG.Instance()
  # access ShipTree
  self.sTree.GetEvent(0)
  #
  # init geometry and mag. field
  gMan  = ROOT.gGeoManager
  self.geoMat =  ROOT.genfit.TGeoMaterialInterface()
  #
  self.bfield = ROOT.genfit.FairShipFields()
  self.bfield.setField(global_variables.fieldMaker.getGlobalField())
  self.fM = ROOT.genfit.FieldManager.getInstance()
  self.fM.init(self.bfield)
  ROOT.genfit.MaterialEffects.getInstance().init(self.geoMat)

   # init fitter, to be done before importing shipPatRec
  #fitter          = ROOT.genfit.KalmanFitter()
  #fitter          = ROOT.genfit.KalmanFitterRefTrack()
  self.fitter      = ROOT.genfit.DAF()
  self.fitter.setMaxIterations(50)
  if global_variables.debug:
    self.fitter.setDebugLvl(1) # produces lot of printout
  #set to True if "real" pattern recognition is required also

  # for 'real' PatRec
  shipPatRec.initialize(fgeo)

 def reconstruct(self):
   ntracks = self.findTracks()
   nGoodTracks = self.findGoodTracks()
   self.linkVetoOnTracks()
   if global_variables.vertexing:
# now go for 2-track combinations
    self.Vertexing.execute()

 def digitize(self):
   self.sTree.t0 = self.random.Rndm()*1*u.microsecond
   self.header.SetEventTime( self.sTree.t0 )
   self.header.SetRunId( self.sTree.MCEventHeader.GetRunID() )
   self.header.SetMCEntryNumber( self.sTree.MCEventHeader.GetEventID() )  # counts from 1
   self.eventHeader.Fill()
   self.digiSBT.process()
   self.strawtubes.process()
   self.timeDetector.process()
   self.upstreamTaggerDetector.process()
   # adding digitization of SND/MTC
   if self.sTree.GetBranch("MTCDetPoint"):
    self.digiMTC.process()
   if self.sTree.GetBranch("splitcalPoint"):
    self.splitcalDetector.process()

 def findTracks(self):
  hitPosLists    = {}
  hit_detector_ids = {}
  stationCrossed = {}
  fittedtrackids=[]
  listOfIndices  = {}
  self.fGenFitArray.clear()
  self.fTrackletsArray.clear()
  self.fitTrack2MC.clear()

#
  if global_variables.withT0:
    self.SmearedHits = self.strawtubes.withT0Estimate()
  # old procedure, not including estimation of t0
  else:
    self.SmearedHits = self.strawtubes.smearHits(global_variables.withNoStrawSmearing)

  trackCandidates = []

  if global_variables.realPR:
    # Do real PatRec
    track_hits = shipPatRec.execute(self.SmearedHits, global_variables.ShipGeo, global_variables.realPR)
    # Create hitPosLists for track fit
    for i_track in track_hits.keys():
      atrack = track_hits[i_track]
      atrack_y12 = atrack['y12']
      atrack_stereo12 = atrack['stereo12']
      atrack_y34 = atrack['y34']
      atrack_stereo34 = atrack['stereo34']
      atrack_smeared_hits = list(atrack_y12) + list(atrack_stereo12) + list(atrack_y34) + list(atrack_stereo34)
      for sm in atrack_smeared_hits:
        detID = sm['detID']
        station = self.strawtubes.det[sm['digiHit']].GetStationNumber()
        trID = i_track
        # Collect hits for track fit
        if trID not in hitPosLists:
          hitPosLists[trID] = ROOT.std.vector('TVectorD')()
          listOfIndices[trID] = []
          stationCrossed[trID]  = {}
          hit_detector_ids[trID] = ROOT.std.vector('int')()
        hit_detector_ids[trID].push_back(detID)
        m = array('d',[sm['xtop'],sm['ytop'],sm['z'],sm['xbot'],sm['ybot'],sm['z'],sm['dist']])
        hitPosLists[trID].push_back(ROOT.TVectorD(7,m))
        listOfIndices[trID].append(sm['digiHit'])
        if station not in stationCrossed[trID]:
          stationCrossed[trID][station] = 0
        stationCrossed[trID][station] += 1
  else: # do fake pattern recognition
   for sm in self.SmearedHits:
    detID = self.strawtubes.det[sm['digiHit']].GetDetectorID()
    station = self.strawtubes.det[sm['digiHit']].GetStationNumber()
    trID = self.sTree.strawtubesPoint[sm['digiHit']].GetTrackID()
    if trID not in hitPosLists:
      hitPosLists[trID]     = ROOT.std.vector('TVectorD')()
      listOfIndices[trID] = []
      stationCrossed[trID]  = {}
      hit_detector_ids[trID] = ROOT.std.vector('int')()
    hit_detector_ids[trID].push_back(detID)
    m = array('d',[sm['xtop'],sm['ytop'],sm['z'],sm['xbot'],sm['ybot'],sm['z'],sm['dist']])
    hitPosLists[trID].push_back(ROOT.TVectorD(7,m))
    listOfIndices[trID].append(sm['digiHit'])
    if station not in stationCrossed[trID]: stationCrossed[trID][station]=0
    stationCrossed[trID][station]+=1
#
   # for atrack in listOfIndices:
   #   # make tracklets out of trackCandidates, just for testing, should be output of proper pattern recognition
   #  nTracks   = self.fTrackletsArray.GetEntries()
   #  aTracklet  = self.fTrackletsArray.ConstructedAt(nTracks)
   #  listOfHits = aTracklet.getList()
   #  aTracklet.setType(3)
   #  for index in listOfIndices[atrack]:
   #    listOfHits.push_back(index)
#
  for atrack in hitPosLists:
    if atrack < 0: continue # these are hits not assigned to MC track because low E cut
    # pdg    = self.sTree.MCTrack[atrack].GetPdgCode()
    # if not self.PDG.GetParticle(pdg): continue # unknown particle
    pdg = 13 # assume all tracks are muons
    meas = hitPosLists[atrack]
    detIDs = hit_detector_ids[atrack]
    nM = len(meas)
    if nM < 25 : continue                          # not enough hits to make a good trackfit
    if len(stationCrossed[atrack]) < 3 : continue  # not enough stations crossed to make a good trackfit
    if global_variables.debug:
       mctrack = self.sTree.MCTrack[atrack]
    # charge = self.PDG.GetParticle(pdg).Charge()/(3.)
    posM = ROOT.TVector3(0, 0, 5812.0) # seed is at decay vessel centre
    momM = ROOT.TVector3(0,0,3.*u.GeV)
# approximate covariance
    covM = ROOT.TMatrixDSym(6)
    resolution = self.sigma_spatial
    if global_variables.withT0:
      resolution *= 1.4 # worse resolution due to t0 estimate
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
    hitID = 0
    for m, detID in zip(meas, detIDs):
      tp = ROOT.genfit.TrackPoint(theTrack) # note how the point is told which track it belongs to
      measurement = ROOT.genfit.WireMeasurement(
        m,
        hitCov,
        detID,
        hitID,
        tp
      ) # the measurement is told which trackpoint it belongs to
      # print measurement.getMaxDistance()
      measurement.setMaxDistance(global_variables.ShipGeo.strawtubes_geo.outer_straw_diameter / 2. - global_variables.ShipGeo.strawtubes_geo.wall_thickness)
      # measurement.setLeftRightResolution(-1)
      tp.addRawMeasurement(measurement) # package measurement in the TrackPoint
      theTrack.insertPoint(tp)  # add point to Track
      hitID += 1
    # print("debug meas", atrack, nM, stationCrossed[atrack], self.sTree.MCTrack[atrack], pdg)
    trackCandidates.append([theTrack,atrack])

  for entry in trackCandidates:
#check
    atrack = entry[1]
    theTrack = entry[0]
    try:
      theTrack.checkConsistency()
    except ROOT.genfit.Exception as e:
      print('Problem with track before fit, not consistent',atrack,theTrack)
      print(e.what())
      ut.reportError(e)
# do the fit
    try:
      self.fitter.processTrack(theTrack) # processTrackWithRep(theTrack,rep,True)
    except:
      if global_variables.debug:
        print("genfit failed to fit track")
      error = "genfit failed to fit track"
      ut.reportError(error)
      continue
#check
    try:
      theTrack.checkConsistency()
    except ROOT.genfit.Exception as e:
      if global_variables.debug:
        print('Problem with track after fit, not consistent', atrack, theTrack)
        print(e.what())
      error = "Problem with track after fit, not consistent"
      ut.reportError(error)
    try:
      fittedState = theTrack.getFittedState()
      fittedMom = fittedState.getMomMag()
    except:
      error = "Problem with fittedstate"
      ut.reportError(error)
      continue
    fitStatus = theTrack.getFitStatus()
    try:
      fitStatus.isFitConverged()
    except ROOT.genfit.Exception as e:
      error = "Fit not converged"
      ut.reportError(error)
    nmeas = fitStatus.getNdf()
    global_variables.h['nmeas'].Fill(nmeas)
    if nmeas <= 0:
      continue
    chi2 = fitStatus.getChi2() / nmeas
    global_variables.h['chi2'].Fill(chi2)
# make track persistent
    # Store pointer - make a copy and let ROOT manage lifetime
    trackCopy = ROOT.genfit.Track(theTrack)
    ROOT.SetOwnership(trackCopy, False)  # ROOT TTree owns the track
    self.fGenFitArray.push_back(trackCopy)
    # self.fitTrack2MC.push_back(atrack)
    if global_variables.debug:
     print('save track',theTrack,chi2,nmeas,fitStatus.isFitConverged())
    # Save MC link
    track_ids = []
    for index in listOfIndices[atrack]:
      ahit = self.sTree.strawtubesPoint[index]
      track_ids += [ahit.GetTrackID()]
    frac, tmax = self.fracMCsame(track_ids)
    self.fitTrack2MC.push_back(tmax)
    # Save hits indexes of the the fitted tracks
    indices = ROOT.std.vector('unsigned int')()
    for index in listOfIndices[atrack]:
      indices.push_back(index)
    aTracklet = ROOT.Tracklet(1, indices)
    self.fTrackletsArray.push_back(aTracklet)
  self.Tracklets.Fill()
  self.fitTracks.Fill()
  self.mcLink.Fill()
# debug
  if global_variables.debug:
   print('save tracklets:')
   for x in self.recoTree.Tracklets:
    print(x.getType(),len(x.getList()))
  return len(self.fGenFitArray)

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
   hitID = -1
   xx  = track.getFittedState()
   rep   = ROOT.genfit.RKTrackRep(xx.getPDG())
   state = ROOT.genfit.StateOnPlane(rep)
   rep.setPosMom(state,xx.getPos(),xx.getMom())
   for i,vetoHit in enumerate(self.digiSBT.det):
     vetoHitPos = vetoHit.GetXYZ()
     try:
      rep.extrapolateToPoint(state,vetoHitPos,False)
     except:
      error =  "shipDigiReco::findVetoHitOnTrack extrapolation did not worked"
      ut.reportError(error)
      if global_variables.debug:
        print(error)
      continue
     dist = (rep.getPos(state) - vetoHitPos).Mag()
     if dist < distMin:
       distMin = dist
       hitID = i
   return ROOT.vetoHitOnTrack(hitID, distMin)

 def linkVetoOnTracks(self):
   self.vetoHitOnTrackArray.clear()
   for good_track in self.goodTracksVect:
     track = self.fGenFitArray[good_track]
     self.vetoHitOnTrackArray.push_back(self.findVetoHitOnTrack(track))
   self.vetoHitOnTrackBranch.Fill()

 def fracMCsame(self, trackids):
  track={}
  nh=len(trackids)
  for tid in trackids:
    if tid in track:
      track[tid] += 1
    else:
      track[tid] = 1
  if track != {}:
    tmax = max(track, key=track.get)
  else:
    track = {-999: 0}
    tmax = -999
  frac=0.0
  if nh > 0:
    frac = float(track[tmax]) / float(nh)
  return frac, tmax

 def finish(self):
  del self.fitter
  print('finished writing tree')
  self.outputFile.cd()
  self.recoTree.Write()
  ut.errorSummary()
  ut.writeHists(global_variables.h,"recohists.root")
  if global_variables.realPR:
    shipPatRec.finalize()
  self.outputFile.Close()
  self.inputFile.Close()
