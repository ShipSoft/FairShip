# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

import logging
from array import array

import global_variables
import ROOT
import rootUtils as ut
import shipPatRec
import shipunit as u
import shipVertex
from detectors.MTCDetector import MTCDetector
from detectors.SBTDetector import SBTDetector
from detectors.splitcalDetector import splitcalDetector
from detectors.strawtubesDetector import strawtubesDetector
from detectors.timeDetector import timeDetector
from detectors.UpstreamTaggerDetector import UpstreamTaggerDetector

logger = logging.getLogger(__name__)


class ShipDigiReco:
    "convert FairSHiP MC hits / digitized hits to measurements"

    def __init__(self, finput, fout, fgeo) -> None:
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
        self.strawtubes = strawtubesDetector("strawtubes", self.sTree, outtree=self.recoTree)

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
        self.Vertexing = shipVertex.Task(global_variables.h, self.recoTree, self.sTree)
        # setup random number generator
        self.random = ROOT.TRandom()
        ROOT.gRandom.SetSeed(13)
        self.PDG = ROOT.TDatabasePDG.Instance()
        # access ShipTree
        self.sTree.GetEvent(0)
        #
        # init geometry and mag. field
        self.geoMat = ROOT.genfit.TGeoMaterialInterface()
        #
        self.bfield = ROOT.genfit.FairShipFields()
        self.bfield.setField(global_variables.fieldMaker.getGlobalField())
        self.fM = ROOT.genfit.FieldManager.getInstance()
        self.fM.init(self.bfield)
        ROOT.genfit.MaterialEffects.getInstance().init(self.geoMat)

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
        self.findTracks()
        self.findGoodTracks()
        if hasattr(self, "digiSBT"):
            self.linkVetoOnTracks()
        if global_variables.vertexing:
            # now go for 2-track combinations
            self.Vertexing.execute()

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
                pdg = -13 if k_y34 > k_y12 else 13
            else:
                pdg = 13
            meas = hitPosLists[atrack]
            detIDs = hit_detector_ids[atrack]
            nM = len(meas)
            if nM < 13:
                n_too_few_hits += 1
                continue  # not enough hits to make a good trackfit
            if len(stationCrossed[atrack]) < 3:
                n_too_few_stations += 1
                continue  # not enough stations crossed to make a good trackfit
            if global_variables.debug:
                self.sTree.MCTrack[atrack]

            # Seed state: use PatRec track parameters when available
            posM, momM = self._compute_seed_state(atrack, meas, trackParams)

            # Try both charge hypotheses, keep the one with better chi2/NDF
            best_track = None
            best_chi2ndf = float("inf")
            for try_pdg in [pdg, -pdg]:
                # approximate covariance
                covM = ROOT.TMatrixDSym(6)
                resolution = self.sigma_spatial
                if global_variables.withT0:
                    resolution *= 1.4  # worse resolution due to t0 estimate
                for i in range(3):
                    covM[i][i] = resolution * resolution
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
                hitCov = ROOT.TMatrixDSym(7)
                hitCov[6][6] = resolution * resolution
                hitID = 0
                for m, detID in zip(meas, detIDs):
                    tp = ROOT.genfit.TrackPoint(theTrack)
                    measurement = ROOT.genfit.WireMeasurement(m, hitCov, detID, hitID, tp)
                    measurement.setMaxDistance(
                        global_variables.ShipGeo.strawtubes_geo.outer_straw_diameter / 2.0
                        - global_variables.ShipGeo.strawtubes_geo.wall_thickness
                    )
                    tp.addRawMeasurement(measurement)
                    theTrack.insertPoint(tp)
                    hitID += 1
                # Fit this hypothesis
                try:
                    theTrack.checkConsistency()
                except ROOT.genfit.Exception:
                    continue
                try:
                    self.fitter.processTrack(theTrack)
                except Exception:
                    continue
                try:
                    theTrack.checkConsistency()
                except ROOT.genfit.Exception:
                    logger.debug("Track inconsistent after fit for hypothesis %d", try_pdg)
                try:
                    fittedState = theTrack.getFittedState()
                    fittedState.getMomMag()
                except Exception:
                    continue
                fitStatus = theTrack.getFitStatus()
                if not fitStatus.isFitConverged():
                    continue
                nmeas = fitStatus.getNdf()
                if nmeas <= 0:
                    continue
                chi2ndf = fitStatus.getChi2() / nmeas
                if chi2ndf < best_chi2ndf:
                    best_chi2ndf = chi2ndf
                    best_track = theTrack
            if best_track is not None:
                trackCandidates.append([best_track, atrack])

        for entry in trackCandidates:
            # Tracks are already fitted from the dual-hypothesis loop above
            atrack = entry[1]
            theTrack = entry[0]
            fitStatus = theTrack.getFitStatus()
            nmeas = fitStatus.getNdf()  # guaranteed > 0 by hypothesis loop filter
            global_variables.h["nmeas"].Fill(nmeas)
            chi2 = fitStatus.getChi2() / nmeas
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
            for index in listOfIndices[atrack]:
                ahit = self.sTree.strawtubesPoint[index]
                track_ids += [ahit.GetTrackID()]
            _frac, tmax = self.fracMCsame(track_ids)
            self.fitTrack2MC.push_back(tmax)
            # Save hits indexes of the the fitted tracks
            indices = ROOT.std.vector("unsigned int")()
            for index in listOfIndices[atrack]:
                indices.push_back(index)
            aTracklet = ROOT.Tracklet(1, indices)
            self.fTrackletsArray.push_back(aTracklet)

        logger.debug(
            "findTracks: %d candidates, %d too few hits, %d too few stations, %d fitted tracks saved",
            len(hitPosLists),
            n_too_few_hits,
            n_too_few_stations,
            len(self.fGenFitArray),
        )

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
        and momentum direction. Otherwise fall back to the default seed
        at the decay vessel centre.
        """
        params = trackParams.get(atrack)
        if params and params.get("k_y12") is not None:
            # Use station 1-2 parameters to seed near the first measurement
            k_y = params["k_y12"]
            b_y = params["b_y12"]
            # Seed Z at the first measurement's Z coordinate
            z_seed = meas[0][2]  # z is the 3rd element of the TVectorD
            y_seed = k_y * z_seed + b_y
            posM = ROOT.TVector3(0, y_seed, z_seed)
            # Use slope as py/pz ratio; assume 3 GeV total momentum
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
            posM = ROOT.TVector3(0, 0, 5812.0)  # decay vessel centre
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
            self.vetoHitOnTrackArray.push_back(self.findVetoHitOnTrack(track))

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
        del self.fitter
        print("finished writing tree")
        self.outputFile.cd()
        self.recoTree.Write()
        ut.errorSummary()
        ut.writeHists(global_variables.h, "recohists.root")
        shipPatRec.finalize()
        self.outputFile.Close()
        self.inputFile.Close()
