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
from detectors.MTCDetector import MTCDetector
from detectors.SBTDetector import SBTDetector
from detectors.splitcalDetector import splitcalDetector
from detectors.strawtubesDetector import strawtubesDetector
from detectors.timeDetector import timeDetector
from detectors.UpstreamTaggerDetector import UpstreamTaggerDetector
from strawReco import calculate_sbt_doca, runTracking

logger = logging.getLogger(__name__)


class ShipDigiReco:
    "convert FairSHiP MC hits / digitized hits to measurements"

    def __init__(self, finput, fout, fgeo) -> None:
        # Open input file (read-only) and get the MC tree
        self.inputFile = ROOT.TFile.Open(finput, "read")
        self.sTree = self.inputFile["cbmsim"]

        # Create output file and new tree for digi/reco branches only
        self.outputFile = ROOT.TFile.Open(fout, "recreate")
        # self.recoTree = ROOT.TTree("ship_reco_sim", "Digitization and Reconstruction")
        self.recoTree = ROOT.TTree("ship_reco_sim", "Digitization and Reconstruction")

        # Disable GeoTracks branch if present in input
        if self.sTree.GetBranch("GeoTracks"):
            self.sTree.SetBranchStatus("GeoTracks", 0)
        # prepare for output
        # event header
        self.header = ROOT.FairEventHeader()
        self.eventHeader = self.recoTree.Branch("ShipEventHeader", self.header, 32000, -1)
        # fitted tracks
        self.fitTrack2MC = ROOT.std.vector("int")()
        self.goodTracksVect = ROOT.std.vector("int")()
        self.mcLink = self.recoTree.Branch("fitTrack2MC", self.fitTrack2MC, 32000, -1)

        self.fACTSArray = ROOT.std.vector("ActsExamples::RecoTrack")()
        self.fitACTSTracks = self.recoTree.Branch("RecoTracks", self.fACTSArray, 32000, -1)
        self.fACTSVertexArray = ROOT.std.vector("ActsExamples::RecoVertex")()
        self.fitACTSVertices = self.recoTree.Branch("RecoVertices", self.fACTSVertexArray, 32000, -1)

        self.goodTracksBranch = self.recoTree.Branch("goodTracks", self.goodTracksVect, 32000, -1)
        self.fTrackletsArray = ROOT.std.vector("Tracklet")()
        self.Tracklets = self.recoTree.Branch("Tracklets", self.fTrackletsArray, 32000, -1)
        #
        self.strawtubes = strawtubesDetector("strawtubes", self.sTree, outtree=self.recoTree)
        ##Vectors of MCTracks/Strawtube hits to pass to ACTS EventData
        self.strawHits = ROOT.std.vector(ROOT.std.vector("float"))()

        if self.sTree.GetBranch("MTCDetPoint"):
            self.digiMTC = MTCDetector("MTCDet", self.sTree, "MTC", outtree=self.recoTree)
        if self.sTree.GetBranch("vetoPoint"):
            self.digiSBT = SBTDetector("veto", self.sTree, "SBT", mcBranchName="digiSBT2MC", outtree=self.recoTree)
            self.vetoHitOnTrackArray = ROOT.std.vector("vetoHitOnTrack")()
            self.vetoHitOnTrackBranch = self.recoTree.Branch("VetoHitOnTrack", self.vetoHitOnTrackArray)
        if self.sTree.GetBranch("TimeDetPoint"):
            self.timeDetector = timeDetector("TimeDet", self.sTree, outtree=self.recoTree)
        if self.sTree.GetBranch("UpstreamTaggerPoint"):
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
        # self.Vertexing = shipVertex.Task(global_variables.h, self.recoTree, self.sTree)
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
        self.detector = acts.examples.StrawtubeBuilder()
        self.trackingGeometry = detector.trackingGeometry()

        # Read the root file containing spectrometer B field
        u = acts.UnitConstants
        currentPath = os.path.dirname(__file__)
        sourcePath = os.path.abspath(os.path.join(currentPath, ".."))
        self.actsFieldMap = acts.examples.MagneticFieldMapXyz(
            file=str(sourcePath + "/" + global_variables.ShipGeo.Bfield.fieldMap),
            tree="Data",
            lengthUnit=u.cm,
            BFieldUnit=u.T,
            translateToGlobal=acts.Vector3(
                global_variables.ShipGeo.Bfield.x, global_variables.ShipGeo.Bfield.y, global_variables.ShipGeo.Bfield.z
            ),
            rotateAxis=True,
            firstOctant=False,
        )

    def reconstruct(self) -> None:
        self.actsTracks()
        if hasattr(self, "digiSBT"):
            calculate_sbt_doca(self, output_tracks, self.digiSBT.det)

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
            trID = self.sTree.strawtubesPoint[sm["digiHit"]].GetTrackID()
            px = self.sTree.strawtubesPoint[sm["digiHit"]].GetPx()
            py = self.sTree.strawtubesPoint[sm["digiHit"]].GetPy()
            pz = self.sTree.strawtubesPoint[sm["digiHit"]].GetPz()
            x = self.sTree.strawtubesPoint[sm["digiHit"]].GetX()
            y = self.sTree.strawtubesPoint[sm["digiHit"]].GetY()
            z = self.sTree.strawtubesPoint[sm["digiHit"]].GetZ()
            deltaE = self.sTree.strawtubesPoint[sm["digiHit"]].GetEnergyLoss()

            # Structure of hit vector (station, layer, view, straw, track_id, Hx,Hy,Hz,Ht, Px,Py,Pz,E, deltaPx, deltaPy, deltaPz, deltaE )
            iHit = ROOT.std.vector("float")()
            iHit += [station, layer, view, straw, trID, x, y, z, time, px, py, pz, 0, 0, 0, 0, deltaE]
            self.strawHits.push_back(iHit)

        candidates = []

        if global_variables.patRec == "AR":
            # PatRec Source
            raw_candidates = self.findTracks()
            for cand in raw_candidates:
                candidates.append(cand)
        elif globa_variables.patRec == "Truth":
            # Truth Source
            for trID, tr in enumerate(self.sTree.MCTrack):
                indices = [i for i, h in enumerate(self.strawHits) if int(h[4]) == trID]
                pos = ROOT.TVector3(tr.GetStartX(), tr.GetStartY(), tr.GetStartZ())
                mom = ROOT.TVector3(tr.GetPx(), tr.GetPy(), tr.GetPz())
                charge = self.PDG.GetParticle(tr.GetPdgCode()).Charge() / 3.0

                candidates.append({"pos": pos, "mom": mom, "indices": indices, "charge": charge})

        output_tracks = runTracking(candidates)

        return output_tracks

    def digitize(self) -> None:
        self.sTree.t0 = self.random.Rndm() * 1 * u.microsecond
        self.header.SetEventTime(self.sTree.t0)
        self.header.SetRunId(self.sTree.MCEventHeader.GetRunID())
        self.header.SetMCEntryNumber(self.sTree.MCEventHeader.GetEventID())  # counts from 1
        if hasattr(self, "digiSBT"):
            self.digiSBT.process()
        self.strawtubes.process()
        if hasattr(self, "timeDetector"):
            self.timeDetector.process()
        if hasattr(self, "upstreamTaggerDetector"):
            self.upstreamTaggerDetector.process()
        if hasattr(self, "digiMTC"):
            self.digiMTC.process()
        if self.sTree.GetBranch("splitcalPoint"):
            self.splitcalDetector.process()

    def findTracks(self) -> int:
        hitPosLists = {}
        hit_detector_ids = {}
        stationCrossed: dict[int, dict[int, int]] = {}
        listOfIndices: dict[int, list[int]] = {}
        trackParams: dict[int, dict] = {}
        self.fitTrack2MC.clear()

        #
        if global_variables.withT0:
            self.SmearedHits = self.strawtubes.withT0Estimate()
        # old procedure, not including estimation of t0
        else:
            self.SmearedHits = self.strawtubes.smearHits(global_variables.withNoStrawSmearing)

        trackCandidates = []

        # Do pattern recognition
        track_hits = shipPatRec.execute(self.SmearedHits, global_variables.ShipGeo, global_variables.patRec)
        logger.debug("PatRec returned %d track candidates", len(track_hits))
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
                continue

            posM, momM = self._compute_seed_state(atrack, hitPosLists[atrack], trackParams)

            indices = listOfIndices[atrack]

            track_candidates.append(
                {
                    "pos": posM,
                    "mom": momM,
                    "indices": indices,
                    "charge": 1.0,  # Assuming muons
                }
            )

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

    def fracMCsame(self, trackids):
        track = {}
        nh = len(trackids)
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
        frac = 0.0
        if nh > 0:
            frac = float(track[tmax]) / float(nh)
        return frac, tmax

    def finish(self) -> None:
        print("finished writing tree")
        self.outputFile.cd()
        self.recoTree.Write()
        ut.errorSummary()
        ut.writeHists(global_variables.h, "recohists.root")
        shipPatRec.finalize()
        self.outputFile.Close()
        self.inputFile.Close()
