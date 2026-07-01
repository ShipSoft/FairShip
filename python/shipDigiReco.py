# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

import logging
import os
from array import array

import acts
import acts.examples
import global_variables
import ROOT
import rootUtils as ut
import shipPatRec
import shipunit as u
import validationTools as validation_tools
from detectors.MTCDetector import MTCDetector
from detectors.SBTDetector import SBTDetector
from detectors.SiliconTargetDetector import SiliconTargetDetector
from detectors.splitcalDetector import splitcalDetector
from detectors.strawtubesDetector import strawtubesDetector
from detectors.timeDetector import timeDetector
from detectors.UpstreamTaggerDetector import UpstreamTaggerDetector
from strawReco import calculateSBTDOCA, runTracking

logger = logging.getLogger(__name__)

ROOT.gSystem.Load("libActsExamplesSHiP")
ROOT.gInterpreter.Declare('#include "ActsExamples/SHiP/RecoTrack.hpp"')
ROOT.gInterpreter.Declare('#include "ActsExamples/SHiP/RecoVertex.hpp"')

class ShipDigiReco:
    "convert FairSHiP MC hits / digitized hits to measurements"

    def __init__(self, finput, fout, fgeo, validation: bool = False) -> None:
        self.validation = validation
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

        # fitted tracks
        self.fACTSArray = ROOT.std.vector("ActsExamples::RecoTrack")()
        self.fitACTSTracks = self.recoTree.Branch("RecoTracks", self.fACTSArray, 32000, -1)
        self.fACTSVertexArray = ROOT.std.vector("ActsExamples::RecoVertex")()
        self.fitACTSVertices = self.recoTree.Branch("RecoVertices", self.fACTSVertexArray, 32000, -1)

        #
        if "strawtubes" in global_variables.modules:
            self.strawtubes = strawtubesDetector("strawtubes", self.sTree, outtree=self.recoTree)
        ##Vectors of MCTracks/Strawtube hits to pass to ACTS EventData
        self.strawHits = ROOT.std.vector(ROOT.std.vector("float"))()

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

        # setup random number generator
        self.random = ROOT.TRandom()
        ROOT.gRandom.SetSeed(13)
        self.PDG = ROOT.TDatabasePDG.Instance()
        # access ShipTree
        self.sTree.GetEvent(0)
        #
        # for 'real' PatRec
        shipPatRec.initialize(fgeo)

        ##Set up ACTS tracking geometry and magnetic field
        cfg = acts.examples.StrawtubeDetector.Config()
        self.detector = acts.examples.StrawtubeDetector(cfg)
        self.trackingGeometry = self.detector.trackingGeometry()

        # Read the root file containing spectrometer B field
        field_map_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", global_variables.ShipGeo.Bfield.fieldMap)
        )
        uu = acts.UnitConstants
        self.actsFieldMap = acts.createShipFieldProvider(field_map_path, uu.T)

    def reconstruct(self) -> None:


        output_tracks, vertices = self.actsTracks()

        self.fACTSArray.clear()
        self.fACTSVertexArray.clear()
        geo_ctx = acts.GeometryContext()

        vector_ptr = ROOT.addressof(self.fACTSArray)
        vertex_vector_ptr = ROOT.addressof(self.fACTSVertexArray)

        for track in output_tracks:
            acts.pushRecoTrack(vector_ptr, track, geo_ctx)

        for vtx in vertices:
            acts.pushRecoVertex(vertex_vector_ptr, vtx)

        if hasattr(self, "digiSBT"):
            veto_results = calculateSBTDOCA(output_tracks, self.digiSBT.det, self.trackingGeometry, self.actsFieldMap)
            self.vetoHitOnTrackArray.clear()
            for hitID, distMin in veto_results:
                self.vetoHitOnTrackArray.push_back(ROOT.vetoHitOnTrack(hitID, distMin))

    def actsTracks(self) -> list:
        self.strawHits.clear()

        if global_variables.withT0:
            self.SmearedHits = self.strawtubes.withT0Estimate()
        else:
            self.SmearedHits = self.strawtubes.smearHits(global_variables.withNoStrawSmearing)

        for sm in self.SmearedHits:
            station = self.strawtubes.det[sm["digiHit"]].GetStationNumber()
            view = self.strawtubes.det[sm["digiHit"]].GetViewNumber()
            layer = self.strawtubes.det[sm["digiHit"]].GetLayerNumber()
            straw = self.strawtubes.det[sm["digiHit"]].GetStrawNumber()
            time = self.strawtubes.det[sm["digiHit"]].GetTDC()
            drift = sm["dist"]
            xtop = sm["xtop"]
            ytop = sm["ytop"]
            xbot = sm["xbot"]
            ybot = sm["ybot"]
            trID = self.sTree.strawtubesPoint[sm["digiHit"]].GetTrackID()
            x = self.sTree.strawtubesPoint[sm["digiHit"]].GetX()
            y = self.sTree.strawtubesPoint[sm["digiHit"]].GetY()
            z = self.sTree.strawtubesPoint[sm["digiHit"]].GetZ()
            deltaE = self.sTree.strawtubesPoint[sm["digiHit"]].GetEnergyLoss()

            # Structure of hit vector (detector [straw=0], station, layer, view, straw, track_id, x,y,z,t, E, drift, wire-xtop, ytop, xbot, ybot )
            iHit = ROOT.std.vector("float")()
            iHit += [0, station, layer, view, straw, trID, x, y, z, time, deltaE, drift, xtop, ytop, xbot, ybot]
            self.strawHits.push_back(iHit)

        candidates = []


        if global_variables.patRec == "AR":
            # PatRec Source
            raw_candidates = self.findTracks()
            for cand in raw_candidates:
                candidates.append(cand)
        elif global_variables.patRec == "Truth":
            # Truth Source
            for trID, tr in enumerate(self.sTree.MCTrack):
                indices = [i for i, h in enumerate(self.strawHits) if int(h[5]) == trID]
                if not indices:
                    continue
                unique_indices = []
                seen_layers = set()
                # Sort indices by Z-position to find the first straw hit
                # iHit[8] is the Z-coordinate
                indices.sort(key=lambda idx: self.strawHits[idx][8])
                for idx in indices:
                    h = self.strawHits[idx]

                    # We want to keep only one straw per unique station/layer/view combination
                    # our Kalman filter cant handle more than 1 measurement per acts::layer
                    layer_key = (int(h[1]), int(h[2]), int(h[3]))

                    if layer_key not in seen_layers:
                        unique_indices.append(idx)
                        seen_layers.add(layer_key)
                first_idx = unique_indices[0]
                first_hit = self.strawHits[first_idx]

                # Create Seed from the first straw hit
                # Position from the straw hit truth (indices 6, 7, 8)
                pos = ROOT.TVector3(first_hit[6], first_hit[7], first_hit[8])

                # Momentum from MCTrack
                mom = ROOT.TVector3(tr.GetPx(), tr.GetPy(), tr.GetPz())

                particle = self.PDG.GetParticle(tr.GetPdgCode())
                if particle is None:
                    logger.warning("Skipping MCTrack %d with unknown PDG code %d", trID, tr.GetPdgCode())
                    continue
                charge = particle.Charge() / 3.0

                candidates.append({"pos": pos, "mom": mom, "indices": unique_indices, "charge": charge})

        output_tracks = runTracking(candidates, self.trackingGeometry, self.actsFieldMap, self.strawHits)

        return output_tracks

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
                local_hit_index = self.SmearedHits.index(sm)
                listOfIndices[trID].append(local_hit_index)

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
            # dk > 0 → positive charge (mu+, pi+), dk < 0 → negative charge (mu-, pi-)
            params = trackParams.get(atrack, {})
            k_y12 = params.get("k_y12")
            k_y34 = params.get("k_y34")
            if k_y12 is not None and k_y34 is not None:
                charge = -1 if k_y34 > k_y12 else 1
            else:
                charge = 1
            meas = hitPosLists[atrack]
            nM = len(meas)
            n_stations_crossed = len(stationCrossed[atrack])
            if self.validation:
                self.validation_stats["candidate_hits_sum"] += nM
                self.validation_stats["candidate_hits_sum_sq"] += nM * nM
                self.validation_stats["candidate_hits_count"] += 1
                self.validation_stats["candidate_stations_sum"] += n_stations_crossed
                self.validation_stats["candidate_stations_sum_sq"] += n_stations_crossed * n_stations_crossed
                self.validation_stats["candidate_stations_count"] += 1
            if nM < 13:
                n_too_few_hits += 1
                continue  # not enough hits to make a good trackfit
            if n_stations_crossed < 3:
                n_too_few_stations += 1
                continue  # not enough stations crossed to make a good trackfit
            if global_variables.debug:
                self.sTree.MCTrack[atrack]

            posM, momM = self._compute_seed_state(atrack, hitPosLists[atrack], trackParams)

            indices = listOfIndices[atrack]

            track_candidates.append({"pos": posM, "mom": momM, "indices": indices, "charge": charge})

        return track_candidates

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

    def finish(self) -> None:
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
