# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

import logging
import os
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
from detectors.MTCDetector import MTCDetector
from detectors.SBTDetector import SBTDetector
from detectors.SiliconTargetDetector import SiliconTargetDetector
from detectors.splitcalDetector import splitcalDetector
from detectors.strawtubesDetector import strawtubesDetector
from detectors.timeDetector import timeDetector
from detectors.UpstreamTaggerDetector import UpstreamTaggerDetector

logger = logging.getLogger(__name__)


# Minimum straw layers for a fittable track candidate; the threshold is tuned to
# the 1-plane-per-view geometry (#552). Must match strawReco.MIN_HITS_PER_TRACK,
# which applies the same cut on the ACTS side.
MIN_HITS_PER_TRACK = 13

# Minimum number of stations a candidate has to cross to be fittable.
MIN_STATIONS_CROSSED = 3


def _cov_element(cov, row, col):
    """Read one element of an ACTS vertex-track covariance.

    The binding hands back a numpy array, but an unfitted track has no
    covariance at all. Missing or unindexable data reads as zero.
    """
    if cov is None:
        return 0.0
    try:
        return cov[row, col]
    except (TypeError, IndexError, KeyError):
        pass
    try:
        return cov[row][col]
    except (TypeError, IndexError, KeyError):
        return 0.0


def _track_vector(track, name, fallback):
    """Return an ACTS vertex-track 3-vector as a numpy array.

    Falls back to ``fallback`` when the preferred attribute is unset, and to
    the origin when neither is available.
    """
    value = getattr(track, name, None)
    if value is None:
        value = getattr(track, fallback, None)
    if value is None:
        value = (0.0, 0.0, 0.0)
    return np.array(value, dtype=float)


def _extrapolate_to_x(point, direction, x_target):
    """Propagate a straight line to a plane of constant x, or None if parallel."""
    dx = direction[0]
    if abs(dx) < 1e-12:
        return None
    return point + direction * ((x_target - point[0]) / dx)


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
            self.fACTSArray = ROOT.std.vector("ActsExamples::RecoTrack")()
            self.fitACTSTracks = self.recoTree.Branch("RecoTracks", self.fACTSArray, 32000, -1)
            self.fACTSVertexArray = ROOT.std.vector("ActsExamples::RecoVertex")()
            self.fitACTSVertices = self.recoTree.Branch("RecoVertices", self.fACTSVertexArray, 32000, -1)
            self.fitTrack2MC = ROOT.std.vector("int")()
            self.mcLink = self.recoTree.Branch("fitTrack2MC", self.fitTrack2MC, 32000, -1)
            self.goodTracksVect = ROOT.std.vector("int")()
            self.goodTracksBranch = self.recoTree.Branch("goodTracks", self.goodTracksVect, 32000, -1)
            self.fTrackletsArray = ROOT.std.vector("Tracklet")()
            self.Tracklets = self.recoTree.Branch("Tracklets", self.fTrackletsArray, 32000, -1)
            # per-hit vectors handed to ACTS event data (not persisted)
            self.strawHits = ROOT.std.vector(ROOT.std.vector("float"))()
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
            self.upstreamTaggerDetector = UpstreamTaggerDetector("UpstreamTagger", self.sTree, outtree=self.recoTree)

        # for the digitizing step
        if hasattr(self, "strawtubes"):
            self.v_drift = global_variables.modules["strawtubes"].StrawVdrift()
            self.sigma_spatial = global_variables.modules["strawtubes"].StrawSigmaSpatial()
        # optional if present, splitcalCluster
        if self.sTree.GetBranch("splitcalPoint"):
            self.splitcalDetector = splitcalDetector("splitcal", self.sTree, outtree=self.recoTree)
            # Keep references for backward compatibility
            self.digiSplitcal = self.splitcalDetector.det
            self.recoSplitcal = self.splitcalDetector.reco

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
            # imported lazily so a GenFit run never touches ACTS
            import acts
            import acts.examples

            # set up ACTS tracking geometry and magnetic field
            cfg = acts.examples.StrawtubeDetector.Config()
            self.detector = acts.examples.StrawtubeDetector(cfg)
            self.trackingGeometry = self.detector.trackingGeometry()

            # read the root file containing the spectrometer B field
            field_map_path = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "..", global_variables.ShipGeo.Bfield.fieldMap)
            )
            if not os.path.exists(field_map_path):
                raise FileNotFoundError(f"ACTS magnetic field map not found: {field_map_path}")
            uu = acts.UnitConstants
            self.actsFieldMap = acts.createShipFieldProvider(field_map_path, uu.T)
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
        import acts
        import acts.examples
        from strawReco import calculateSBTDOCA

        geo_ctx = acts.GeometryContext()
        self.fACTSArray.clear()
        self.fACTSVertexArray.clear()
        self.fitTrack2MC.clear()
        self.goodTracksVect.clear()
        self.fPartArray.clear()
        self.fTrackletsArray.clear()

        output_tracks, vertices, track_hit_indices = self.actsTracks()

        vector_ptr = ROOT.addressof(self.fACTSArray)
        vertex_vector_ptr = ROOT.addressof(self.fACTSVertexArray)

        for i, (_, hit_indices) in enumerate(zip(output_tracks, track_hit_indices, strict=True)):
            acts.examples.pushRecoTrack(vector_ptr, geo_ctx, i, output_tracks)

            nmeas = output_tracks.ndf[i]
            if nmeas > 0:
                global_variables.h["nmeas"].Fill(nmeas)
                global_variables.h["chi2"].Fill(output_tracks.chi2[i] / nmeas)

            # Save MC link: majority MC track over the hits used in the fit
            track_ids = []
            for index in hit_indices:
                if 0 <= index < len(self.strawHits):
                    ahit = self.strawHits[index]
                    track_ids.append(int(ahit[5]))

            _frac, tmax = self.fracMCsame(track_ids)
            self.fitTrack2MC.push_back(tmax)

            # Save digi-hit indices of the fitted track
            indices_vector = ROOT.std.vector("unsigned int")()
            for index in hit_indices:
                if 0 <= index < len(self.strawHitToDigi):
                    indices_vector.push_back(self.strawHitToDigi[index])

            aTracklet = ROOT.Tracklet(1, indices_vector)
            self.fTrackletsArray.push_back(aTracklet)

        n_good_tracks = self.findGoodActsTracks(output_tracks)

        # acts-ship only exposes a process-global "last extracted params"
        # pointer, so it can be attributed to a vertex unambiguously only when
        # the event holds a single one.
        input_addr = 0
        if len(vertices) == 1 and hasattr(acts, "get_last_extracted_params_addr"):
            try:
                input_addr = int(acts.get_last_extracted_params_addr())
            except (TypeError, ValueError):
                logger.warning("Could not read the ACTS extracted-parameters address", exc_info=True)

        for vtx in vertices:
            acts.pushRecoVertex(vertex_vector_ptr, vtx, output_tracks, input_addr)

            vtx_tracks = vtx.tracks()

            # Create a ShipParticle from the vertex fit from 2 track vertices
            if len(vtx_tracks) != 2:
                logger.debug("Skipping vertex with %d tracks (expected 2)", len(vtx_tracks))
                continue

            vertex_pos = vtx.position()

            # ACTS reco frame is in mm, the SHiP frame in cm
            length_scale = 0.1  # mm -> cm
            area_scale = 0.01  # mm^2 -> cm^2 (covariances)

            # Scale units to cm and rotate
            vx = ROOT.TVector3(
                -vertex_pos[2] * length_scale, vertex_pos[1] * length_scale, vertex_pos[0] * length_scale
            )

            t1 = int(vtx_tracks[0].trackIndex)
            t2 = int(vtx_tracks[1].trackIndex)

            mom_daughter1 = tuple(vtx_tracks[0].momentum) if vtx_tracks[0].momentum is not None else (0.0, 0.0, 0.0)
            mom_daughter2 = tuple(vtx_tracks[1].momentum) if vtx_tracks[1].momentum is not None else (0.0, 0.0, 0.0)
            px_mother = mom_daughter1[0] + mom_daughter2[0]
            py_mother = mom_daughter1[1] + mom_daughter2[1]
            pz_mother = mom_daughter1[2] + mom_daughter2[2]
            # Rotate into SHiP frame
            P = ROOT.TLorentzVector(-pz_mother, py_mother, px_mother, 0)

            acts_covV = vtx.covariance()  # 3x3 Eigen matrix in mm^2 (ACTS reco frame)
            covV = ROOT.TMatrixDSym(3)

            covV[0][0] = acts_covV[2, 2] * area_scale
            covV[1][1] = acts_covV[1, 1] * area_scale
            covV[2][2] = acts_covV[0, 0] * area_scale

            covV[0][1] = -acts_covV[1, 2] * area_scale
            covV[1][0] = covV[0][1]

            covV[0][2] = -acts_covV[0, 2] * area_scale
            covV[2][0] = covV[0][2]

            covV[1][2] = acts_covV[0, 1] * area_scale
            covV[2][1] = covV[1][2]

            cov_daughter1 = getattr(vtx_tracks[0], "covariance", None)
            cov_daughter2 = getattr(vtx_tracks[1], "covariance", None)

            raw_covP = ROOT.TMatrixDSym(3)
            for ii in range(3):
                for jj in range(3):
                    raw_covP[ii][jj] = _cov_element(cov_daughter1, ii + 3, jj + 3) + _cov_element(
                        cov_daughter2, ii + 3, jj + 3
                    )

            covP = ROOT.TMatrixDSym(3)
            covP[0][0] = raw_covP[2][2]
            covP[1][1] = raw_covP[1][1]
            covP[2][2] = raw_covP[0][0]

            covP[0][1] = -raw_covP[1][2]
            covP[1][0] = covP[0][1]

            covP[0][2] = -raw_covP[0][2]
            covP[2][0] = covP[0][2]

            covP[1][2] = raw_covP[0][1]
            covP[2][1] = covP[1][2]

            vertex_position_4d = ROOT.TLorentzVector(vx, 0.0)

            particle = ROOT.ShipParticle(9900015, 0, -1, -1, t1, t2, P, vertex_position_4d)
            covV_list = [covV[0][0], covV[0][1], covV[0][2], covV[1][1], covV[1][2], covV[2][2]]

            # Extract 6 upper-triangular elements for momentum covariance
            covP_list = [covP[0][0], covP[0][1], covP[0][2], 0.0, covP[1][1], covP[1][2], 0.0, covP[2][2], 0.0, 0.0]

            # Track extrapolation and DOCA calculation, preferring the
            # pre-fit track state where the vertex fit kept one
            p1 = _track_vector(vtx_tracks[0], "originalPosition", "position")
            p2 = _track_vector(vtx_tracks[1], "originalPosition", "position")
            d1 = _track_vector(vtx_tracks[0], "originalMomentum", "momentum")
            d2 = _track_vector(vtx_tracks[1], "originalMomentum", "momentum")

            # normalize direction
            n1 = np.linalg.norm(d1)
            n2 = np.linalg.norm(d2)
            if not (n1 > 0 and n2 > 0):
                # Without a direction for both daughters the DOCA below collapses
                # to zero, i.e. a perfect vertex, which would sail through every
                # signal selection. Drop the candidate instead, as the GenFit
                # path does when the extrapolation to the fitted vertex fails.
                logger.warning("Skipping ACTS vertex candidate: daughter track without momentum")
                continue
            d1 = d1 / n1
            d2 = d2 / n2

            # target plane x in ACTS frame (mm)
            target_x = float(vtx.position()[0])

            p1_x_tmp = _extrapolate_to_x(p1, d1, target_x)
            p1_x = p1_x_tmp if p1_x_tmp is not None else p1
            p2_x_tmp = _extrapolate_to_x(p2, d2, target_x)
            p2_x = p2_x_tmp if p2_x_tmp is not None else p2
            delta = p1_x - p2_x
            n = np.cross(d1, d2)
            n_norm = np.linalg.norm(n)
            if n_norm > 1e-12:
                doca_mm = abs(np.dot(delta, n)) / n_norm
            else:
                # Nearly parallel tracks: perpendicular component of delta
                # (d1 is a unit vector, so no further normalisation is needed).
                doca_mm = np.linalg.norm(np.cross(delta, d1))
            doca = float(doca_mm) / 10.0  # mm -> cm

            particle.SetCovP(covP_list)
            particle.SetCovV(covV_list)
            particle.SetDoca(doca)
            self.fPartArray.push_back(particle)

        if hasattr(self, "digiSBT"):
            # As in the GenFit linkVetoOnTracks, the veto links are built for the
            # selected tracks only: entry k of the VetoHitOnTrack branch belongs
            # to track goodTracks[k], and its hitID indexes the SBT digi hits.
            veto_results = calculateSBTDOCA(
                output_tracks,
                self.digiSBT.det,
                self.trackingGeometry,
                self.actsFieldMap,
                selected_indices=list(self.goodTracksVect),
            )
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
        """Build per-hit ACTS event data and fit track candidates with ACTS.

        Returns (fitted track container, vertices, per-track hit indices into
        self.strawHits).
        """
        from strawReco import runTracking

        if global_variables.patRec == "Truth":
            # MC truth seeding needs no pattern recognition, only smeared hits
            candidates = None
            if global_variables.withT0:
                self.SmearedHits = self.strawtubes.withT0Estimate()
            else:
                self.SmearedHits = self.strawtubes.smearHits(global_variables.withNoStrawSmearing)
        else:
            candidates = self.findTracks()

        # Build the flat per-hit vectors handed to ACTS from this event's
        # smeared hits (single smearing, done above or inside findTracks).
        # Structure of hit vector (detector [straw=0], station, layer, view,
        # straw, track_id, x, y, z, t, E, drift, wire-xtop, ytop, xbot, ybot)
        self.strawHits.clear()
        self.strawHitToDigi = []
        digi_to_straw = {}
        for k, sm in enumerate(self.SmearedHits):
            digiHit = int(sm["digiHit"])
            station = self.strawtubes.det[digiHit].GetStationNumber()
            view = self.strawtubes.det[digiHit].GetViewNumber()
            layer = self.strawtubes.det[digiHit].GetLayerNumber()
            straw = self.strawtubes.det[digiHit].GetStrawNumber()
            time = self.strawtubes.det[digiHit].GetTDC()
            drift = sm["dist"]
            xtop = sm["xtop"]
            ytop = sm["ytop"]
            xbot = sm["xbot"]
            ybot = sm["ybot"]
            point = self.sTree.strawtubesPoint[digiHit]
            trID = point.GetTrackID()
            x = point.GetX()
            y = point.GetY()
            z = point.GetZ()
            deltaE = point.GetEnergyLoss()

            iHit = ROOT.std.vector("float")()
            for value in (0, station, layer, view, straw, trID, x, y, z, time, deltaE, drift, xtop, ytop, xbot, ybot):
                iHit.push_back(value)
            self.strawHits.push_back(iHit)
            self.strawHitToDigi.append(digiHit)
            digi_to_straw[digiHit] = k

        if candidates is None:
            candidates = self._truthCandidates()
        else:
            # Candidate hit indices refer to digi hits; remap them to positions
            # in self.strawHits as expected by runTracking.
            for cand in candidates:
                cand["indices"] = [digi_to_straw[i] for i in cand["indices"] if i in digi_to_straw]

        return runTracking(
            candidates,
            self.trackingGeometry,
            self.actsFieldMap,
            self.strawHits,
            fit_vertex=global_variables.vertexing,
        )

    def _truthCandidates(self) -> list[dict]:
        """Build track candidates from MC truth: one per MC track with straw hits."""
        candidates = []
        # Bucket the straw hits by MC track in one pass; iHit[5] is the track ID
        hits_by_track = defaultdict(list)
        for i, h in enumerate(self.strawHits):
            hits_by_track[int(h[5])].append(i)
        for trID, tr in enumerate(self.sTree.MCTrack):
            indices = hits_by_track.get(trID)
            if not indices:
                continue
            unique_indices = []
            seen_layers = set()
            # Sort indices by Z-position to find the first straw hit; iHit[8] is Z
            indices.sort(key=lambda idx: self.strawHits[idx][8])
            for idx in indices:
                h = self.strawHits[idx]
                # Keep only one straw per unique station/layer/view combination:
                # the Kalman filter can't handle more than 1 measurement per acts layer
                layer_key = (int(h[1]), int(h[2]), int(h[3]))
                if layer_key not in seen_layers:
                    unique_indices.append(idx)
                    seen_layers.add(layer_key)
            first_hit = self.strawHits[unique_indices[0]]

            # Seed position from the first straw hit truth (indices 6, 7, 8)
            pos = ROOT.TVector3(first_hit[6], first_hit[7], first_hit[8])

            # Momentum from MCTrack
            mom = ROOT.TVector3(tr.GetPx(), tr.GetPy(), tr.GetPz())

            particle = self.PDG.GetParticle(tr.GetPdgCode())
            if particle is None:
                logger.warning("Skipping MCTrack %d with unknown PDG code %d", trID, tr.GetPdgCode())
                continue
            charge = particle.Charge() / 3.0

            candidates.append({"pos": pos, "mom": mom, "indices": unique_indices, "charge": charge})
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
        if hasattr(self, "digiMTC"):
            self.digiMTC.process()
        if hasattr(self, "digiSiliconTarget"):
            self.digiSiliconTarget.process()
        if self.sTree.GetBranch("splitcalPoint"):
            self.splitcalDetector.process()
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

    def findGoodActsTracks(self, output_tracks) -> int:
        """ACTS counterpart of findGoodTracks.

        Applies the same chi2/ndf < 50 criterion as the GenFit selection, so the
        goodTracks branch means the same thing whichever fitter produced the
        file. A usable reference surface stands in for GenFit's isFitConverged:
        only successful ACTS fits are persisted in the first place, but a track
        without a reference surface cannot be extrapolated either.
        """
        self.goodTracksVect.clear()
        nGoodTracks = 0
        n_persisted = len(self.fACTSArray)
        for i, track in enumerate(output_tracks):
            if i >= n_persisted:
                break
            if not track.referenceSurface:
                continue
            ndf = output_tracks.ndf[i]
            if ndf <= 0:
                continue
            chi2 = output_tracks.chi2[i] / ndf
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
