# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

import logging
import math
from array import array
from collections import Counter, defaultdict

import global_variables
import numpy as np
import ROOT
import rootUtils as ut
import shipPatRec
import shipunit as u
import shipVertex
import validationTools as validation_tools
from detectors.CaloScoringPlaneDetector import CaloScoringPlaneDetector
from detectors.MTCDetector import MTCDetector
from detectors.SBTDetector import SBTDetector
from detectors.SiliconTargetDetector import SiliconTargetDetector
from detectors.strawtubesDetector import strawtubesDetector
from detectors.timeDetector import timeDetector
from detectors.UpstreamTaggerDetector import UBTGeometryMismatch, UpstreamTaggerDetector
from recoConstants import MIN_HITS_PER_TRACK
from strawReco import StrawHit, calculateSBTDOCA, make_tracker, runTracking

logger = logging.getLogger(__name__)


# Minimum number of stations a candidate has to cross to be fittable.
MIN_STATIONS_CROSSED = 3

# Mass assumed for the daughters of ACTS vertex candidates (GeV)
MUON_MASS = 0.1056583755


class ShipDigiReco:
    "convert FairSHiP MC hits / digitized hits to measurements"

    def __init__(self, finput, fout, fgeo, validation: bool = False) -> None:
        self.validation = validation
        self.trackFitter = getattr(global_variables, "trackFitter", "genfit")
        # Always allocate the counter dict so static analysis sees it as
        # subscriptable; entries are only updated when self.validation is true,
        # so a non-validation run still ends with the zeroed defaults.
        self.validation_stats = validation_tools.make_reco_validation_stats()
        # Open input file (read-only) and get the MC tree
        self.inputFile = ROOT.TFile.Open(finput, "read")
        self.sTree = self.inputFile["cbmsim"]

        # Create output file and new tree for digi/reco branches only
        self.outputFile = ROOT.TFile.Open(fout, "recreate")
        self.recoTree = ROOT.TTree("ship_reco_sim", "Digitization and Reconstruction")

        # Disable GeoTracks branch if present in input
        if self.sTree.GetBranch("GeoTracks"):
            self.sTree.SetBranchStatus("GeoTracks", 0)
        # prepare for output
        # event header
        self.header = ROOT.FairEventHeader()
        self.eventHeader = self.recoTree.Branch("ShipEventHeader", self.header, 32000, -1)
        if self.trackFitter == "acts":
            # ACTS event model: fitted tracks, vertices and candidate particles
            self.fPartArray = ROOT.std.vector("ShipParticle")()
            self.Particles = self.recoTree.Branch("Particles", self.fPartArray, 32000, -1)
            self.fACTSArray = ROOT.std.vector("SHiP::RecoTrack")()
            self.fitACTSTracks = self.recoTree.Branch("RecoTracks", self.fACTSArray, 32000, -1)
            self.fACTSVertexArray = ROOT.std.vector("SHiP::RecoVertex")()
            self.fitACTSVertices = self.recoTree.Branch("RecoVertices", self.fACTSVertexArray, 32000, -1)
            self.fitTrack2MC = ROOT.std.vector("int")()
            self.mcLink = self.recoTree.Branch("fitTrack2MC", self.fitTrack2MC, 32000, -1)
            self.goodTracksVect = ROOT.std.vector("int")()
            self.goodTracksBranch = self.recoTree.Branch("goodTracks", self.goodTracksVect, 32000, -1)
            self.fTrackletsArray = ROOT.std.vector("Tracklet")()
            self.Tracklets = self.recoTree.Branch("Tracklets", self.fTrackletsArray, 32000, -1)
            # smeared straw hits of the current event, as strawReco.StrawHit
            self.strawHits: list[StrawHit] = []
        else:
            # fitted tracks
            # Must use pointer storage: genfit::Track has circular references with TrackPoint
            # requiring stable memory addresses (value storage would invalidate back-pointers on vector resize)
            self.fGenFitArray = ROOT.std.vector("genfit::Track*")()
            self.fitTrack2MC = ROOT.std.vector("int")()
            self.goodTracksVect = ROOT.std.vector("int")()
            self.mcLink = self.recoTree.Branch("fitTrack2MC", self.fitTrack2MC, 32000, -1)
            self.fitTracks = self.recoTree.Branch("FitTracks", self.fGenFitArray, 32000, -1)
            self.goodTracksBranch = self.recoTree.Branch("goodTracks", self.goodTracksVect, 32000, -1)
            self.fTrackletsArray = ROOT.std.vector("Tracklet")()
            self.Tracklets = self.recoTree.Branch("Tracklets", self.fTrackletsArray, 32000, -1)
        #
        if "strawtubes" in global_variables.modules:
            self.strawtubes = strawtubesDetector("strawtubes", self.sTree, outtree=self.recoTree)

        if self.sTree.GetBranch("MTCDetPoint"):
            self.digiMTC = MTCDetector("MTCDet", self.sTree, "MTC", outtree=self.recoTree)
        if self.sTree.GetBranch("SiliconTargetPoint"):
            self.digiSiliconTarget = SiliconTargetDetector(
                "SiliconTarget", self.sTree, "SiliconTarget", outtree=self.recoTree
            )
        if self.sTree.GetBranch("vetoPoint"):
            self.digiSBT = SBTDetector("veto", self.sTree, "SBT", mcBranchName="digiSBT2MC", outtree=self.recoTree)
            self.vetoHitOnTrackArray = ROOT.std.vector("vetoHitOnTrack")()
            self.vetoHitOnTrackBranch = self.recoTree.Branch("VetoHitOnTrack", self.vetoHitOnTrackArray)
        if self.sTree.GetBranch("TimeDetPoint"):
            self.timeDetector = timeDetector("TimeDet", self.sTree, outtree=self.recoTree)
        if self.sTree.GetBranch("UpstreamTaggerPoint"):
            try:
                self.upstreamTaggerDetector = UpstreamTaggerDetector(
                    "UpstreamTagger", self.sTree, mcBranchName="digiUBT2MC", outtree=self.recoTree
                )
            except UBTGeometryMismatch as error:
                logger.warning("%s: %s; the UBT is not digitized.", fgeo.GetName(), error)
        if self.sTree.GetBranch("CaloScoringPlanePoint"):
            self.caloScoringPlaneDetector = CaloScoringPlaneDetector(
                "CaloScoringPlane", self.sTree, outtree=self.recoTree
            )
        elif getattr(global_variables, "caloScoringPlanePIDFile", None):
            logger.warning(
                "--caloScoringPlanePID was given, but the input has no CaloScoringPlanePoint branch "
                "(simulated before the scoring plane existed?); it is ignored and no scoring-plane hits are made."
            )

        # for the digitizing step
        if hasattr(self, "strawtubes"):
            self.v_drift = global_variables.modules["strawtubes"].StrawVdrift()
            self.sigma_spatial = global_variables.modules["strawtubes"].StrawSigmaSpatial()

        if self.trackFitter != "acts":
            # prepare vertexing; creates the Particles branch bound to its own container
            self.Vertexing = shipVertex.Task(global_variables.h, self.recoTree, self.sTree)
        # setup random number generator
        self.random = ROOT.TRandom()
        ROOT.gRandom.SetSeed(13)
        self.PDG = ROOT.TDatabasePDG.Instance()
        # access ShipTree
        self.sTree.GetEvent(0)
        #
        if self.trackFitter == "acts":
            # straw surfaces from the loaded geometry, and the simulation field
            self.actsTracker = make_tracker(ROOT.gGeoManager, global_variables.fieldMaker.getGlobalField())
        else:
            # init geometry and mag. field
            self.geoMat = ROOT.genfit.TGeoMaterialInterface()
            #
            self.bfield = ROOT.genfit.FairShipFields()
            self.bfield.setField(global_variables.fieldMaker.getGlobalField())
            self.fM = ROOT.genfit.FieldManager.getInstance()
            self.fM.init(self.bfield)
            ROOT.SetOwnership(self.bfield, False)  # genfit::FieldManager singleton takes ownership
            ROOT.genfit.MaterialEffects.getInstance().init(self.geoMat)
            ROOT.SetOwnership(self.geoMat, False)  # genfit::MaterialEffects singleton takes ownership

            # init fitter, to be done before importing shipPatRec
            # fitter          = ROOT.genfit.KalmanFitter()
            # fitter          = ROOT.genfit.KalmanFitterRefTrack()
            self.fitter = ROOT.genfit.DAF()
            self.fitter.setMaxIterations(50)
            if global_variables.debug:
                self.fitter.setDebugLvl(1)  # produces lot of printout
        # set to True if "real" pattern recognition is required also

        # for 'real' PatRec
        shipPatRec.initialize(fgeo)

    def reconstruct(self) -> None:
        if not hasattr(self, "strawtubes"):
            return
        if self.trackFitter == "acts":
            self.reconstructActs()
            return
        candidates = self.findTracks()
        n_tracks = self.fitTracksGenfit(candidates)
        n_good_tracks = self.findGoodTracks()
        if hasattr(self, "digiSBT"):
            self.linkVetoOnTracks()
        if global_variables.vertexing:
            # now go for 2-track combinations
            if self.validation:
                self.validation_stats["vertexing_calls"] += 1
            self.Vertexing.execute()
        if self.validation:
            self.validation_stats["events_reconstructed"] += 1
            self.validation_stats["fitted_tracks_total"] += n_tracks
            self.validation_stats["good_tracks_total"] += n_good_tracks
            if n_tracks > 0:
                self.validation_stats["events_with_fitted_tracks"] += 1
            if n_good_tracks > 0:
                self.validation_stats["events_with_good_tracks"] += 1
            validation_tools.record_event_stat(self.validation_stats, "event_fitted_tracks", n_tracks)
            validation_tools.record_event_stat(self.validation_stats, "event_good_tracks", n_good_tracks)
            if hasattr(self, "digiSBT"):
                validation_tools.record_event_stat(
                    self.validation_stats, "event_veto_links", len(self.vetoHitOnTrackArray)
                )

    def reconstructActs(self) -> None:
        """Fit tracks and vertices with ACTS and persist them.

        Fills the RecoTracks/RecoVertices/Particles branches, the MC link
        and Tracklets, and the SBT veto links.
        """
        self.fACTSArray.clear()
        self.fACTSVertexArray.clear()
        self.fitTrack2MC.clear()
        self.goodTracksVect.clear()
        self.fPartArray.clear()
        self.fTrackletsArray.clear()

        tracks, vertices, track_hit_indices = self.actsTracks()

        for track, hit_indices in zip(tracks, track_hit_indices, strict=True):
            self.fACTSArray.push_back(track)

            nmeas = track.nDoF()
            if nmeas > 0:
                global_variables.h["nmeas"].Fill(nmeas)
                global_variables.h["chi2"].Fill(track.chi2() / nmeas)

            # Save MC link: majority MC track over the hits used in the fit
            _frac, tmax = self.fracMCsame([self.strawHits[i].track_id for i in hit_indices])
            self.fitTrack2MC.push_back(tmax)

            # Save digi-hit indices of the fitted track
            indices_vector = ROOT.std.vector("unsigned int")()
            for index in hit_indices:
                indices_vector.push_back(self.strawHitToDigi[index])
            self.fTrackletsArray.push_back(ROOT.Tracklet(1, indices_vector))

        n_good_tracks = self.findGoodActsTracks()

        for vtx in vertices:
            self.fACTSVertexArray.push_back(vtx)

            # Create a ShipParticle from the vertex fit from 2 track vertices
            if len(vtx.trackIds()) != 2:
                logger.debug("Skipping vertex with %d tracks (expected 2)", len(vtx.trackIds()))
                continue
            t1, t2 = vtx.trackIds()
            # The daughters are taken to be muons, as in the GenFit vertexing
            P = ROOT.TLorentzVector()
            covP = np.zeros((4, 4))
            for i in range(2):
                p = np.array([vtx.trackPx()[i], vtx.trackPy()[i], vtx.trackPz()[i]])
                energy = math.hypot(np.linalg.norm(p), MUON_MASS)
                P += ROOT.TLorentzVector(float(p[0]), float(p[1]), float(p[2]), energy)
                cov = np.zeros((3, 3))
                cov[np.triu_indices(3)] = list(vtx.GetTrackMomentumCovariance(i))
                cov = cov + np.triu(cov, 1).T
                # (px, py, pz, E) from (px, py, pz)
                jacobian = np.vstack([np.eye(3), p / energy])
                covP += jacobian @ cov @ jacobian.T
            vertex_position_4d = ROOT.TLorentzVector(vtx.x(), vtx.y(), vtx.z(), 0.0)
            particle = ROOT.ShipParticle(9900015, 0, -1, -1, t1, t2, P, vertex_position_4d)

            # ShipParticle::SetCovP takes the upper triangle of the 4x4 (px, py,
            # pz, E) covariance, row by row.
            particle.SetCovP(list(covP[np.triu_indices(4)]))
            particle.SetCovV(list(vtx.GetCovarianceElements()))
            particle.SetDoca(vtx.doca())
            self.fPartArray.push_back(particle)

        if hasattr(self, "digiSBT"):
            # As in the GenFit linkVetoOnTracks, the veto links are built for the
            # selected tracks only: entry k of the VetoHitOnTrack branch belongs
            # to track goodTracks[k], and its hitID indexes the SBT digi hits.
            veto_results = calculateSBTDOCA(self.actsTracker, self.digiSBT.det, list(self.goodTracksVect))
            self.vetoHitOnTrackArray.clear()
            for hitID, distMin in veto_results:
                self.vetoHitOnTrackArray.push_back(ROOT.vetoHitOnTrack(hitID, float(distMin)))
                if self.validation and hitID >= 0:  # Only record real matches
                    self.validation_stats["veto_link_distance_sum"] += distMin
                    self.validation_stats["veto_link_distance_sum_sq"] += distMin * distMin
                    self.validation_stats["veto_link_distance_count"] += 1

        n_tracks = len(self.fACTSArray)
        if self.validation:
            self.validation_stats["events_reconstructed"] += 1
            self.validation_stats["fitted_tracks_total"] += n_tracks
            self.validation_stats["good_tracks_total"] += n_good_tracks
            if n_tracks > 0:
                self.validation_stats["events_with_fitted_tracks"] += 1
            if n_good_tracks > 0:
                self.validation_stats["events_with_good_tracks"] += 1
            validation_tools.record_event_stat(self.validation_stats, "event_fitted_tracks", n_tracks)
            validation_tools.record_event_stat(self.validation_stats, "event_good_tracks", n_good_tracks)
            if hasattr(self, "digiSBT"):
                self.validation_stats["veto_links_total"] += len(self.vetoHitOnTrackArray)
                validation_tools.record_event_stat(
                    self.validation_stats, "event_veto_links", len(self.vetoHitOnTrackArray)
                )

    def actsTracks(self) -> tuple:
        """Collect this event's straw hits and fit track candidates with ACTS.

        Returns (fitted tracks, vertices, per-track hit indices into
        self.strawHits).
        """
        if global_variables.patRec in ("Truth", "Segments"):
            # Truth hit assignment, or the ACTS tracker's own pattern
            # recognition, need only the smeared hits
            candidates = None
            if global_variables.withT0:
                self.SmearedHits = self.strawtubes.withT0Estimate()
            else:
                self.SmearedHits = self.strawtubes.smearHits(global_variables.withNoStrawSmearing)
        else:
            candidates = self.findTracks()

        # Collect the hits from this event's smeared hits (single smearing,
        # done above or inside findTracks).
        self.strawHits = []
        self.strawHitToDigi = []
        digi_to_straw = {}
        for k, sm in enumerate(self.SmearedHits):
            digiHit = int(sm["digiHit"])
            digi = self.strawtubes.det[digiHit]
            point = self.sTree.strawtubesPoint[digiHit]
            self.strawHits.append(
                StrawHit(
                    detector_id=digi.GetDetectorID(),
                    station=digi.GetStationNumber(),
                    view=digi.GetViewNumber(),
                    layer=digi.GetLayerNumber(),
                    track_id=point.GetTrackID(),
                    z=sm["z"],
                    drift=sm["dist"],
                )
            )
            self.strawHitToDigi.append(digiHit)
            digi_to_straw[digiHit] = k

        if global_variables.patRec == "Truth":
            candidates = self._truthCandidates()
        elif candidates is not None:
            # Candidate hit indices refer to digi hits; remap them to positions
            # in self.strawHits as expected by runTracking.
            for cand in candidates:
                cand["indices"] = [digi_to_straw[i] for i in cand["indices"] if i in digi_to_straw]

        return runTracking(
            self.actsTracker,
            candidates,
            self.strawHits,
            self.sigma_spatial,
            fit_vertex=global_variables.vertexing,
            vertex_all_tracks=getattr(global_variables, "vertexAllTracks", False),
        )

    def _truthCandidates(self) -> list[dict]:
        """Build track candidates from MC truth: the straw hits of each charged MC track.

        Only the hit assignment comes from the truth; the fit starts from the
        hits alone, as for any other pattern recognition.
        """
        hits_by_track = defaultdict(list)
        for i, h in enumerate(self.strawHits):
            hits_by_track[h.track_id].append(i)
        candidates = []
        for trID, indices in sorted(hits_by_track.items()):
            particle = self.PDG.GetParticle(self.sTree.MCTrack[trID].GetPdgCode()) if trID >= 0 else None
            # PyROOT returns a null proxy, not None, for an unknown PDG code
            if not particle or particle.Charge() == 0:
                continue
            candidates.append({"indices": indices})
        return candidates

    def digitize(self) -> None:
        self.sTree.t0 = self.random.Rndm() * 1 * u.microsecond
        self.header.SetEventTime(self.sTree.t0)
        self.header.SetRunId(self.sTree.MCEventHeader.GetRunID())
        self.header.SetMCEntryNumber(self.sTree.MCEventHeader.GetEventID())  # counts from 1
        if hasattr(self, "digiSBT"):
            self.digiSBT.process()
        if hasattr(self, "strawtubes"):
            self.strawtubes.process()
        if hasattr(self, "timeDetector"):
            self.timeDetector.process()
        if hasattr(self, "upstreamTaggerDetector"):
            self.upstreamTaggerDetector.process()
        if hasattr(self, "caloScoringPlaneDetector"):
            self.caloScoringPlaneDetector.process()
        if hasattr(self, "digiMTC"):
            self.digiMTC.process()
        if hasattr(self, "digiSiliconTarget"):
            self.digiSiliconTarget.process()
        if self.validation:
            self.validation_stats["events_digitized"] += 1

    def findTracks(self) -> list[dict]:
        """Digitize, run pattern recognition and build fitter-agnostic track candidates.

        Each candidate holds the seed state, hit measurements and indices;
        fitting is done separately (e.g. by fitTracksGenfit).
        """
        hitPosLists = {}
        hit_detector_ids = {}
        stationCrossed: dict[int, dict[int, int]] = {}
        listOfIndices: dict[int, list[int]] = {}
        trackParams: dict[int, dict] = {}

        #
        if global_variables.withT0:
            self.SmearedHits = self.strawtubes.withT0Estimate()
        # old procedure, not including estimation of t0
        else:
            self.SmearedHits = self.strawtubes.smearHits(global_variables.withNoStrawSmearing)
        if self.validation:
            self.validation_stats["smeared_hits_total"] += len(self.SmearedHits)
            if len(self.SmearedHits) > 0:
                self.validation_stats["events_with_hits"] += 1

        # Do pattern recognition
        track_hits = shipPatRec.execute(self.SmearedHits, global_variables.ShipGeo, global_variables.patRec)
        logger.debug("PatRec returned %d track candidates", len(track_hits))
        if self.validation:
            self.validation_stats["track_candidates_total"] += len(track_hits)
            if len(track_hits) > 0:
                self.validation_stats["events_with_candidates"] += 1
            validation_tools.record_event_stat(self.validation_stats, "event_track_candidates", len(track_hits))
        # Create hitPosLists for track fit
        for i_track in track_hits:
            atrack = track_hits[i_track]
            atrack_y12 = atrack["y12"]
            atrack_stereo12 = atrack["stereo12"]
            atrack_y34 = atrack["y34"]
            atrack_stereo34 = atrack["stereo34"]
            atrack_smeared_hits = list(atrack_y12) + list(atrack_stereo12) + list(atrack_y34) + list(atrack_stereo34)
            # Store PatRec track parameters for seeding the fitter
            trackParams[i_track] = {
                "k_y12": atrack.get("k_y12"),
                "b_y12": atrack.get("b_y12"),
                "k_y34": atrack.get("k_y34"),
                "b_y34": atrack.get("b_y34"),
            }
            for sm in atrack_smeared_hits:
                detID = sm["detID"]
                station = self.strawtubes.det[sm["digiHit"]].GetStationNumber()
                trID = i_track
                # Collect hits for track fit
                if trID not in hitPosLists:
                    hitPosLists[trID] = ROOT.std.vector("TVectorD")()
                    listOfIndices[trID] = []
                    stationCrossed[trID] = {}
                    hit_detector_ids[trID] = ROOT.std.vector("int")()
                hit_detector_ids[trID].push_back(detID)
                m = array("d", [sm["xtop"], sm["ytop"], sm["z"], sm["xbot"], sm["ybot"], sm["z"], sm["dist"]])
                hitPosLists[trID].push_back(ROOT.TVectorD(7, m))
                listOfIndices[trID].append(sm["digiHit"])
                if station not in stationCrossed[trID]:
                    stationCrossed[trID][station] = 0
                stationCrossed[trID][station] += 1

        n_too_few_hits = 0
        n_too_few_stations = 0
        track_candidates = []

        for atrack in hitPosLists:
            if atrack < 0:
                continue  # these are hits not assigned to MC track because low E cut
            # Determine charge sign from bending between stations 1-2 and 3-4.
            # The slope difference dk = k_y34 - k_y12 encodes the charge:
            # dk > 0 → negative charge (mu-, pi-), dk <= 0 → positive charge (mu+, pi+)
            params = trackParams.get(atrack, {})
            k_y12 = params.get("k_y12")
            k_y34 = params.get("k_y34")
            if k_y12 is not None and k_y34 is not None:
                # The slope difference between the two station pairs gives the
                # bending sense, and with it the charge.
                pdg = 13 if k_y34 > k_y12 else -13
            else:
                pdg = 13
            # GenFit is seeded with the PDG code, ACTS with the charge, so the two
            # have to agree: mu- (pdg 13) carries charge -1, mu+ (pdg -13) carries +1.
            charge = -1 if pdg > 0 else 1
            meas = hitPosLists[atrack]
            detIDs = hit_detector_ids[atrack]
            nM = len(meas)
            n_stations_crossed = len(stationCrossed[atrack])
            if self.validation:
                self.validation_stats["candidate_hits_sum"] += nM
                self.validation_stats["candidate_hits_sum_sq"] += nM * nM
                self.validation_stats["candidate_hits_count"] += 1
                self.validation_stats["candidate_stations_sum"] += n_stations_crossed
                self.validation_stats["candidate_stations_sum_sq"] += n_stations_crossed * n_stations_crossed
                self.validation_stats["candidate_stations_count"] += 1
            if nM < MIN_HITS_PER_TRACK:
                n_too_few_hits += 1
                continue  # not enough hits for a good trackfit
            if n_stations_crossed < MIN_STATIONS_CROSSED:
                n_too_few_stations += 1
                continue  # not enough stations crossed to make a good trackfit
            if global_variables.debug:
                self.sTree.MCTrack[atrack]

            # Seed state: use PatRec track parameters when available
            posM, momM = self._compute_seed_state(atrack, meas, trackParams)

            track_candidates.append(
                {
                    "pos": posM,
                    "mom": momM,
                    "pdg": pdg,
                    "charge": charge,
                    "meas": meas,
                    "detIDs": detIDs,
                    "indices": listOfIndices[atrack],
                }
            )

        logger.debug(
            "findTracks: %d candidates, %d too few hits, %d too few stations, %d candidates kept for fitting",
            len(hitPosLists),
            n_too_few_hits,
            n_too_few_stations,
            len(track_candidates),
        )
        if self.validation:
            self.validation_stats["track_candidates_rejected_hits"] += n_too_few_hits
            self.validation_stats["track_candidates_rejected_stations"] += n_too_few_stations

        return track_candidates

    def fitTracksGenfit(self, candidates) -> int:
        """Fit track candidates with GenFit and persist the fitted tracks."""
        self.fGenFitArray.clear()
        self.fTrackletsArray.clear()
        self.fitTrack2MC.clear()

        fittedTracks = []
        for cand in candidates:
            pdg = cand["pdg"]
            meas = cand["meas"]
            detIDs = cand["detIDs"]
            nM = len(meas)
            posM, momM = cand["pos"], cand["mom"]

            # Try both charge hypotheses, keep the one with better chi2/NDF
            best_track = None
            best_chi2ndf = float("inf")
            for try_pdg in [pdg, -pdg]:
                if self.validation:
                    self.validation_stats["fit_hypotheses_tried"] += 1
                # approximate covariance
                covM = ROOT.TMatrixDSym(6)
                resolution = self.sigma_spatial
                if global_variables.withT0:
                    resolution *= 1.4  # worse resolution due to t0 estimate
                for i in range(3):
                    covM[i][i] = resolution * resolution
                # x is only measured by the small-angle stereo views, so give
                # the seed a ~10x larger x uncertainty than y
                covM[0][0] = resolution * resolution * 100.0
                for i in range(3, 6):
                    covM[i][i] = ROOT.TMath.Power(resolution / nM / ROOT.TMath.Sqrt(3), 2)
                rep = ROOT.genfit.RKTrackRep(try_pdg)
                stateSmeared = ROOT.genfit.MeasuredStateOnPlane(rep)
                rep.setPosMomCov(stateSmeared, posM, momM, covM)
                seedState = ROOT.TVectorD(6)
                seedCov = ROOT.TMatrixDSym(6)
                rep.get6DStateCov(stateSmeared, seedState, seedCov)
                theTrack = ROOT.genfit.Track(rep, seedState, seedCov)
                ROOT.SetOwnership(rep, False)  # genfit::Track takes ownership
                hitCov = ROOT.TMatrixDSym(7)
                hitCov[6][6] = resolution * resolution
                hitID = 0
                for m, detID in zip(meas, detIDs, strict=True):
                    tp = ROOT.genfit.TrackPoint(theTrack)
                    measurement = ROOT.genfit.WireMeasurement(m, hitCov, detID, hitID, tp)
                    measurement.setMaxDistance(
                        global_variables.ShipGeo.strawtubes_geo.outer_straw_diameter / 2.0
                        - global_variables.ShipGeo.strawtubes_geo.wall_thickness
                    )
                    tp.addRawMeasurement(measurement)
                    ROOT.SetOwnership(measurement, False)  # TrackPoint takes ownership
                    theTrack.insertPoint(tp)
                    ROOT.SetOwnership(tp, False)  # genfit::Track takes ownership
                    hitID += 1
                # Fit this hypothesis
                try:
                    theTrack.checkConsistency()
                except ROOT.genfit.Exception:
                    if self.validation:
                        self.validation_stats["tracks_failed_consistency"] += 1
                    continue
                try:
                    self.fitter.processTrack(theTrack)
                except Exception as e:
                    logger.debug("Failed to processTrack for hypothesis %d: %s", try_pdg, e)
                    if self.validation:
                        self.validation_stats["tracks_failed_fit"] += 1
                    continue
                try:
                    theTrack.checkConsistency()
                except ROOT.genfit.Exception:
                    logger.debug("Track inconsistent after fit for hypothesis %d", try_pdg)
                    if self.validation:
                        self.validation_stats["tracks_failed_consistency"] += 1
                    continue
                try:
                    fittedState = theTrack.getFittedState()
                    fittedState.getMomMag()
                except Exception as e:
                    logger.debug("Failed to getFittedState/getMomMag for hypothesis %d: %s", try_pdg, e)
                    if self.validation:
                        self.validation_stats["tracks_failed_state_access"] += 1
                    continue
                fitStatus = theTrack.getFitStatus()
                if not fitStatus.isFitConverged():
                    continue
                if self.validation:
                    self.validation_stats["fit_hypotheses_converged"] += 1
                nmeas = fitStatus.getNdf()
                if nmeas <= 0:
                    continue
                chi2ndf = fitStatus.getChi2() / nmeas
                if chi2ndf < best_chi2ndf:
                    best_chi2ndf = chi2ndf
                    best_track = theTrack
            if best_track is not None:
                fittedTracks.append((best_track, cand))

        for theTrack, cand in fittedTracks:
            # Tracks are already fitted from the dual-hypothesis loop above
            fitStatus = theTrack.getFitStatus()
            nmeas = fitStatus.getNdf()  # guaranteed > 0 by hypothesis loop filter
            global_variables.h["nmeas"].Fill(nmeas)
            chi2 = fitStatus.getChi2() / nmeas
            if self.validation:
                self.validation_stats["chi2_sum"] += chi2
                self.validation_stats["chi2_sum_sq"] += chi2 * chi2
                self.validation_stats["chi2_count"] += 1
                self.validation_stats["ndf_sum"] += nmeas
                self.validation_stats["ndf_sum_sq"] += nmeas * nmeas
                self.validation_stats["ndf_count"] += 1
            global_variables.h["chi2"].Fill(chi2)
            # make track persistent
            # Store pointer - make a copy and let ROOT manage lifetime
            trackCopy = ROOT.genfit.Track(theTrack)
            ROOT.SetOwnership(trackCopy, False)  # ROOT TTree owns the track
            self.fGenFitArray.push_back(trackCopy)
            if global_variables.debug:
                print("save track", theTrack, chi2, nmeas, fitStatus.isFitConverged())
            # Save MC link
            track_ids = []
            for index in cand["indices"]:
                ahit = self.sTree.strawtubesPoint[index]
                track_ids += [ahit.GetTrackID()]
            _frac, tmax = self.fracMCsame(track_ids)
            self.fitTrack2MC.push_back(tmax)
            # Save hits indexes of the the fitted tracks
            indices = ROOT.std.vector("unsigned int")()
            for index in cand["indices"]:
                indices.push_back(index)
            aTracklet = ROOT.Tracklet(1, indices)
            self.fTrackletsArray.push_back(aTracklet)

        logger.debug("fitTracksGenfit: %d fitted tracks saved", len(self.fGenFitArray))

        # debug
        if global_variables.debug:
            print("save tracklets:")
            for x in self.recoTree.Tracklets:
                print(x.getType(), len(x.getList()))
        return len(self.fGenFitArray)

    def _compute_seed_state(self, atrack, meas, trackParams):
        """Compute seed position and momentum for the track fitter.

        When PatRec track parameters (k_y, b_y) are available, use them
        to place the seed at the first hit's Z with the correct Y position
        and momentum direction. Prefers station 1-2 parameters, falls back
        to station 3-4, then to a geometry-free default at the first hit.
        """
        params = trackParams.get(atrack)
        k_y = None
        b_y = None
        if params:
            if params.get("k_y12") is not None and params.get("b_y12") is not None:
                k_y = params["k_y12"]
                b_y = params["b_y12"]
            elif params.get("k_y34") is not None and params.get("b_y34") is not None:
                k_y = params["k_y34"]
                b_y = params["b_y34"]

        z_seed = meas[0][2]  # z is the 3rd element of the TVectorD
        if k_y is not None:
            y_seed = k_y * z_seed + b_y
            posM = ROOT.TVector3(0, y_seed, z_seed)
            p_total = 3.0 * u.GeV
            pz = p_total / ROOT.TMath.Sqrt(1.0 + k_y * k_y)
            py = k_y * pz
            momM = ROOT.TVector3(0, py, pz)
            logger.debug(
                "seed from PatRec: z=%.1f y=%.1f k_y=%.4f p=(0, %.2f, %.2f)",
                z_seed,
                y_seed,
                k_y,
                py,
                pz,
            )
        else:
            posM = ROOT.TVector3(0, 0, z_seed)
            momM = ROOT.TVector3(0, 0, 3.0 * u.GeV)
        return posM, momM

    def findGoodTracks(self) -> int:
        self.goodTracksVect.clear()
        nGoodTracks = 0
        for i, track in enumerate(self.fGenFitArray):
            fitStatus = track.getFitStatus()
            if not fitStatus.isFitConverged():
                continue
            nmeas = fitStatus.getNdf()
            chi2 = fitStatus.getChi2() / nmeas
            if chi2 < 50 and not chi2 < 0:
                self.goodTracksVect.push_back(i)
                nGoodTracks += 1
        return nGoodTracks

    def findGoodActsTracks(self) -> int:
        """ACTS counterpart of findGoodTracks.

        Applies the same chi2/ndf < 50 criterion as the GenFit selection, so the
        goodTracks branch means the same thing whichever fitter produced the
        file. Only converged ACTS fits are persisted, which stands in for
        GenFit's isFitConverged.
        """
        self.goodTracksVect.clear()
        nGoodTracks = 0
        for i, track in enumerate(self.fACTSArray):
            ndf = track.nDoF()
            if ndf <= 0:
                continue
            chi2 = track.chi2() / ndf
            if chi2 < 50 and not chi2 < 0:
                self.goodTracksVect.push_back(i)
                nGoodTracks += 1
        return nGoodTracks

    def findVetoHitOnTrack(self, track):
        distMin = 99999.0
        hitID = -1
        xx = track.getFittedState()
        rep = ROOT.genfit.RKTrackRep(xx.getPDG())
        state = ROOT.genfit.StateOnPlane(rep)
        rep.setPosMom(state, xx.getPos(), xx.getMom())
        for i, vetoHit in enumerate(self.digiSBT.det):
            vetoHitPos = vetoHit.GetXYZ()
            try:
                rep.extrapolateToPoint(state, vetoHitPos, False)
            except Exception:
                error = "shipDigiReco::findVetoHitOnTrack extrapolation did not worked"
                ut.reportError(error)
                if global_variables.debug:
                    print(error)
                continue
            dist = (rep.getPos(state) - vetoHitPos).Mag()
            if dist < distMin:
                distMin = dist
                hitID = i
        return ROOT.vetoHitOnTrack(hitID, distMin)

    def linkVetoOnTracks(self) -> None:
        self.vetoHitOnTrackArray.clear()
        for good_track in self.goodTracksVect:
            track = self.fGenFitArray[good_track]
            veto_link = self.findVetoHitOnTrack(track)
            self.vetoHitOnTrackArray.push_back(veto_link)
            if self.validation:
                if veto_link.GetHitID() >= 0:  # Only record real matches
                    dist = float(veto_link.GetDist())
                    self.validation_stats["veto_link_distance_sum"] += dist
                    self.validation_stats["veto_link_distance_sum_sq"] += dist * dist
                    self.validation_stats["veto_link_distance_count"] += 1
        if self.validation:
            self.validation_stats["veto_links_total"] += len(self.vetoHitOnTrackArray)

    def fracMCsame(self, trackids):
        """Find the majority MC track ID and its purity fraction."""
        if not trackids:
            return 0.0, -999
        counts = Counter(trackids)
        tmax, max_count = counts.most_common(1)[0]
        return float(max_count) / len(trackids), tmax

    def finish(self) -> None:
        if hasattr(self, "fitter"):
            del self.fitter
        if self.validation:
            validation_tools.print_reco_validation_summary(
                self.validation_stats, has_veto_detector=hasattr(self, "digiSBT")
            )
        print("finished writing tree")
        self.outputFile.cd()
        self.recoTree.Write()
        ut.errorSummary()
        ut.writeHists(global_variables.h, "recohists.root")
        shipPatRec.finalize()
        self.outputFile.Close()
        self.inputFile.Close()
