# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

import array
from collections import defaultdict

import global_variables
import numpy as np
import ROOT
import shipunit as u

PDG = ROOT.TDatabasePDG.Instance()
import acts
import shipDet_conf
from ShipGeoConfig import load_from_root_file


def main():
    inputFile = global_variables.inputFile
    sTree = ROOT.TChain("cbmsim")
    sTree.Add(inputFile)

    geoFile = global_variables.geoFile
    fgeo = ROOT.TFile.Open(geoFile, "READ")

    outFile = global_variables.inputFile.replace(".root", "_ACTS.root")

    # load Shipgeo dictionary
    ShipGeo = load_from_root_file(fgeo, "ShipGeo")
    run = ROOT.FairRunSim()
    run.SetName("TGeant4")  # Transport engine
    run.SetSink(ROOT.FairRootFileSink(ROOT.TMemFile("output", "recreate")))  # Dummy output file
    ROOT.SHiP.SetupVMCConfig("g4Config", "g4Config_basic.yaml")
    # geant4 transport not used, only needed for creating VMC field
    run.GetRuntimeDb()
    shipDet_conf.configure(run, ShipGeo)

    with ROOT.TFile.Open(outFile, "RECREATE") as f:
        # Trees to hold converted data: particles, vertices, SiliconTarget hits, Strawtube hits.
        particleTree = ROOT.TTree("particles", "particles")
        vertexTree = ROOT.TTree("vertices", "vertices")
        siHitTree = ROOT.TTree("siHits", "siHits")
        mtcHitTree = ROOT.TTree("mtcHits", "mtcHits")
        strawHitTree = ROOT.TTree("strawHits", "strawHits")

        # Silicon target hit branches
        # Not all branches are used by ROOTSimHitReader, but must exist nevertheless
        event_id = array.array("i", [0])
        siHitTree.Branch("event_id", event_id, "event_id/i")
        volume_id = array.array("i", [0])
        siHitTree.Branch("volume_id", volume_id, "volume_id/i")
        boundary_id = array.array("i", [0])
        siHitTree.Branch("boundary_id", boundary_id, "boundary_id/i")
        layer_id = array.array("i", [0])
        siHitTree.Branch("layer_id", layer_id, "layer_id/i")
        approach_id = array.array("i", [0])
        siHitTree.Branch("approach_id", approach_id, "approach_id/i")
        sensitive_id = array.array("i", [0])
        siHitTree.Branch("sensitive_id", sensitive_id, "sensitive_id/i")
        geometry_id = array.array("l", [0])
        siHitTree.Branch("geometry_id", geometry_id, "geometry_id/l")
        particle_id = array.array("l", [0])
        siHitTree.Branch("particle_id", particle_id, "particle_id/l")
        index_si = array.array("i", [0])
        siHitTree.Branch("index", index_si, "index/I")
        tx = array.array("f", [0])
        siHitTree.Branch("tx", tx, "tx/F")
        ty = array.array("f", [0])
        siHitTree.Branch("ty", ty, "ty/F")
        tz = array.array("f", [0])
        siHitTree.Branch("tz", tz, "tz/F")
        tt = array.array("f", [0])
        siHitTree.Branch("tt", tt, "tt/F")
        tpx = array.array("f", [0])
        siHitTree.Branch("tpx", tpx, "tpx/F")
        tpy = array.array("f", [0])
        siHitTree.Branch("tpy", tpy, "tpy/F")
        tpz = array.array("f", [0])
        siHitTree.Branch("tpz", tpz, "tpz/F")
        tenergy = array.array("f", [0])
        siHitTree.Branch("te", tenergy, "te/F")
        deltapx = array.array("f", [0])
        siHitTree.Branch("deltapx", deltapx, "deltapx/F")
        deltapy = array.array("f", [0])
        siHitTree.Branch("deltapy", deltapy, "deltapy/F")
        deltapz = array.array("f", [0])
        siHitTree.Branch("deltapz", deltapz, "deltapz/F")
        deltae = array.array("f", [0])
        siHitTree.Branch("deltae", deltae, "deltae/F")

        # MTC hit branches
        event_id_mtc = array.array("i", [0])
        mtcHitTree.Branch("event_id", event_id_mtc, "event_id/i")
        volume_id_mtc = array.array("i", [0])
        mtcHitTree.Branch("volume_id", volume_id_mtc, "volume_id/i")
        boundary_id_mtc = array.array("i", [0])
        mtcHitTree.Branch("boundary_id", boundary_id_mtc, "boundary_id/i")
        layer_id_mtc = array.array("i", [0])
        mtcHitTree.Branch("layer_id", layer_id_mtc, "layer_id/i")
        approach_id_mtc = array.array("i", [0])
        mtcHitTree.Branch("approach_id", approach_id_mtc, "approach_id/i")
        sensitive_id_mtc = array.array("i", [0])
        mtcHitTree.Branch("sensitive_id", sensitive_id_mtc, "sensitive_id/i")
        geometry_id_mtc = array.array("l", [0])
        mtcHitTree.Branch("geometry_id", geometry_id_mtc, "geometry_id/l")
        particle_id_mtc = array.array("l", [0])
        mtcHitTree.Branch("particle_id", particle_id_mtc, "particle_id/l")
        index_mtc = array.array("i", [0])
        mtcHitTree.Branch("index", index_mtc, "index/I")
        tx_mtc = array.array("f", [0])
        mtcHitTree.Branch("tx", tx_mtc, "tx/F")
        ty_mtc = array.array("f", [0])
        mtcHitTree.Branch("ty", ty_mtc, "ty/F")
        tz_mtc = array.array("f", [0])
        mtcHitTree.Branch("tz", tz_mtc, "tz/F")
        tt_mtc = array.array("f", [0])
        mtcHitTree.Branch("tt", tt_mtc, "tt/F")
        tpx_mtc = array.array("f", [0])
        mtcHitTree.Branch("tpx", tpx_mtc, "tpx/F")
        tpy_mtc = array.array("f", [0])
        mtcHitTree.Branch("tpy", tpy_mtc, "tpy/F")
        tpz_mtc = array.array("f", [0])
        mtcHitTree.Branch("tpz", tpz_mtc, "tpz/F")
        te_mtc = array.array("f", [0])
        mtcHitTree.Branch("te", te_mtc, "te/F")
        deltapx_mtc = array.array("f", [0])
        mtcHitTree.Branch("deltapx", deltapx_mtc, "deltapx/F")
        deltapy_mtc = array.array("f", [0])
        mtcHitTree.Branch("deltapy", deltapy_mtc, "deltapy/F")
        deltapz_mtc = array.array("f", [0])
        mtcHitTree.Branch("deltapz", deltapz_mtc, "deltapz/F")
        deltae_mtc = array.array("f", [0])
        mtcHitTree.Branch("deltae", deltae_mtc, "deltae/F")

        # Straw tracker hit branches
        event_id_straw = array.array("i", [0])
        strawHitTree.Branch("event_id", event_id_straw, "event_id/i")
        volume_id_straw = array.array("i", [0])
        strawHitTree.Branch("volume_id", volume_id_straw, "volume_id/i")
        boundary_id_straw = array.array("i", [0])
        strawHitTree.Branch("boundary_id", boundary_id_straw, "boundary_id/i")
        layer_id_straw = array.array("i", [0])
        strawHitTree.Branch("layer_id", layer_id_straw, "layer_id/i")
        approach_id_straw = array.array("i", [0])
        strawHitTree.Branch("approach_id", approach_id_straw, "approach_id/i")
        sensitive_id_straw = array.array("i", [0])
        strawHitTree.Branch("sensitive_id", sensitive_id_straw, "sensitive_id/i")
        geometry_id_straw = array.array("l", [0])
        strawHitTree.Branch("geometry_id", geometry_id_straw, "geometry_id/l")
        particle_id_straw = array.array("l", [0])
        strawHitTree.Branch("particle_id", particle_id_straw, "particle_id/l")
        index_straw = array.array("i", [0])
        strawHitTree.Branch("index", index_straw, "index/I")
        tx_straw = array.array("f", [0])
        strawHitTree.Branch("tx", tx_straw, "tx/F")
        ty_straw = array.array("f", [0])
        strawHitTree.Branch("ty", ty_straw, "ty/F")
        tz_straw = array.array("f", [0])
        strawHitTree.Branch("tz", tz_straw, "tz/F")
        tt_straw = array.array("f", [0])
        strawHitTree.Branch("tt", tt_straw, "tt/F")
        tpx_straw = array.array("f", [0])
        strawHitTree.Branch("tpx", tpx_straw, "tpx/F")
        tpy_straw = array.array("f", [0])
        strawHitTree.Branch("tpy", tpy_straw, "tpy/F")
        tpz_straw = array.array("f", [0])
        strawHitTree.Branch("tpz", tpz_straw, "tpz/F")
        te_straw = array.array("f", [0])
        strawHitTree.Branch("te", te_straw, "te/F")
        deltapx_straw = array.array("f", [0])
        strawHitTree.Branch("deltapx", deltapx_straw, "deltapx/F")
        deltapy_straw = array.array("f", [0])
        strawHitTree.Branch("deltapy", deltapy_straw, "deltapy/F")
        deltapz_straw = array.array("f", [0])
        strawHitTree.Branch("deltapz", deltapz_straw, "deltapz/F")
        deltae_straw = array.array("f", [0])
        strawHitTree.Branch("deltae", deltae_straw, "deltae/F")

        # Vertex branches
        event_id_vertex = array.array("i", [0])
        vertexTree.Branch("event_id", event_id_vertex, "event_id/i")
        vertex_id = ROOT.std.vector("unsigned long")([0])
        vertexTree.Branch("vertex_id", vertex_id)
        process_vtx = ROOT.std.vector("int")([0])
        vertexTree.Branch("process", process_vtx)
        vx_vtx = ROOT.std.vector("float")([0])
        vertexTree.Branch("vx", vx_vtx)
        vy_vtx = ROOT.std.vector("float")([0])
        vertexTree.Branch("vy", vy_vtx)
        vz_vtx = ROOT.std.vector("float")([0])
        vertexTree.Branch("vz", vz_vtx)
        vt_vtx = ROOT.std.vector("float")([0])
        vertexTree.Branch("vt", vt_vtx)
        outgoing_particlesVec = ROOT.std.vector("unsigned long")()
        outgoing_particles = ROOT.std.vector(ROOT.std.vector("unsigned long"))()
        vertexTree.Branch("outgoing_particles", outgoing_particles)
        vertex_primary_vtx = ROOT.std.vector("int")([0])
        vertexTree.Branch("vertex_primary", vertex_primary_vtx)
        vertex_secondary_vtx = ROOT.std.vector("int")([0])
        vertexTree.Branch("vertex_secondary", vertex_secondary_vtx)
        generation_vtx = ROOT.std.vector("int")([0])
        vertexTree.Branch("generation", generation_vtx)

        # Particle branches
        event_id_particle = array.array("i", [0])
        particleTree.Branch("event_id", event_id_particle, "event_id/i")
        particle_id_particle = ROOT.std.vector("unsigned long")()
        particleTree.Branch("particle_id", particle_id_particle)
        particle_type = ROOT.std.vector("int")()
        particleTree.Branch("particle_type", particle_type)
        process = ROOT.std.vector("int")()
        particleTree.Branch("process", process)
        vx = ROOT.std.vector("float")()
        particleTree.Branch("vx", vx)
        vy = ROOT.std.vector("float")()
        particleTree.Branch("vy", vy)
        vz = ROOT.std.vector("float")()
        particleTree.Branch("vz", vz)
        vt = ROOT.std.vector("float")()
        particleTree.Branch("vt", vt)
        pp = ROOT.std.vector("float")()
        particleTree.Branch("p", pp)
        px = ROOT.std.vector("float")()
        particleTree.Branch("px", px)
        py = ROOT.std.vector("float")()
        particleTree.Branch("py", py)
        pz = ROOT.std.vector("float")()
        particleTree.Branch("pz", pz)
        m = ROOT.std.vector("float")()
        particleTree.Branch("m", m)
        q = ROOT.std.vector("float")()
        particleTree.Branch("q", q)
        eta = ROOT.std.vector("float")()
        particleTree.Branch("eta", eta)
        phi = ROOT.std.vector("float")()
        particleTree.Branch("phi", phi)
        pt = ROOT.std.vector("float")()
        particleTree.Branch("pt", pt)
        vertex_primary = ROOT.std.vector("int")()
        particleTree.Branch("vertex_primary", vertex_primary)
        vertex_secondary = ROOT.std.vector("int")()
        particleTree.Branch("vertex_secondary", vertex_secondary)
        particle = ROOT.std.vector("int")()
        particleTree.Branch("particle", particle)
        generation_particle = ROOT.std.vector("int")()
        particleTree.Branch("generation", generation_particle)
        sub_particle = ROOT.std.vector("float")()
        particleTree.Branch("sub_particle", sub_particle)
        e_loss = ROOT.std.vector("float")()
        particleTree.Branch("e_loss", e_loss)
        total_x0 = ROOT.std.vector("float")()
        particleTree.Branch("total_x0", total_x0)
        total_l0 = ROOT.std.vector("float")()
        particleTree.Branch("total_l0", total_l0)
        number_of_hits = ROOT.std.vector("int")()
        particleTree.Branch("number_of_hits", number_of_hits)
        outcome = ROOT.std.vector("float")()
        particleTree.Branch("outcome", outcome)

        for ievent, event in enumerate(sTree):
            motherMap = defaultdict(list)
            motherMapVal = defaultdict(list)
            detHitMap = defaultdict(list)
            detHitArray = []
            strawHitArr = []
            trID = []

            if global_variables.detector == "SiliconTarget" or global_variables.detector == "SND":
                detHitArray.clear()
                trID.clear()
                detHitMap.clear()
                pointsDict = defaultdict(list)
                for index, point in enumerate(event.SiliconTargetPoint):
                    detID = point.GetDetectorID()
                    pointsDict[detID].append(point)

                for index, detID in enumerate(pointsDict):
                    allPoints = ROOT.std.vector("SiliconTargetPoint*")()
                    trID.clear()
                    for p in pointsDict[detID]:
                        allPoints.push_back(p)
                        trID.append(p.GetTrackID())
                    detHitArray.append([ROOT.SiliconTargetHit(detID, allPoints), trID[0]])
                for index, hit in enumerate(detHitArray):
                    trackID = hit[1]
                    detHitMap[trackID].append([hit[0].GetDetectorID(), hit[0]])
                for i in detHitMap:
                    detHitMap[i].sort(key=lambda x: x[0])

                for iTrack in detHitMap:
                    for index, hit in enumerate(detHitMap[iTrack]):
                        if iTrack < -1:  # If track id == -2 barcode will fail
                            continue
                        hit = hit[1]
                        layerID = (
                            6 * hit.GetLayer() + 2 * hit.GetPlane() + 4
                        )  # Layers correspond to planes, including W planes and navigation layers in between
                        event_id[0] = ievent
                        volume_id[0] = 1
                        boundary_id[0] = 0
                        layer_id[0] = layerID
                        approach_id[0] = 0
                        sens = hit.GetModule()
                        sensitive_id[0] = sens
                        geometry_id[0] = acts.GeometryIdentifier(volume=1, layer=layerID, sensitive=sens).value
                        barVal = acts.Barcode(primaryVertex=1, secondaryVertex=0, part=iTrack, gen=0, subpart=0).value
                        particle_id[0] = barVal
                        index_si[0] = index

                        # SHiP coordinate system translated to reconstruction coord system
                        # z -> x
                        # y -> y
                        # x -> -z
                        tx[0] = hit.GetZ() * 10  # Units cm -> mm
                        ty[0] = hit.GetY() * 10
                        tz[0] = -hit.GetX() * 10
                        tt[0] = 0
                        tpx[0] = 0.0
                        tpy[0] = 0.0
                        tpz[0] = 0.0
                        tenergy[0] = 0.0
                        deltapx[0] = 0.0
                        deltapy[0] = 0.0
                        deltapz[0] = 0.0
                        deltae[0] = -hit.GetSignal()

                        siHitTree.Fill()

            if global_variables.detector == "MTC" or global_variables.detector == "SND":
                detHitArray.clear()
                trID.clear()
                detHitMap.clear()
                pointsDict = defaultdict(list)
                for index, point in enumerate(event.MTCPoint):
                    detID = point.GetDetectorID()
                    pointsDict[detID].append(point)

                for index, detID in enumerate(pointsDict):
                    allPoints = ROOT.std.vector("MTCPoint*")()
                    trID.clear()
                    for p in pointsDict[detID]:
                        allPoints.push_back(p)
                        trID.append(p.GetTrackID())
                    detHitArray.append([ROOT.MTCHit(detID, allPoints), trID[0]])
                for index, hit in enumerate(detHitArray):
                    trackID = hit[1]
                    detHitMap[trackID].append([hit[0].GetDetectorID(), hit[0]])
                for i in detHitMap:
                    detHitMap[i].sort(key=lambda x: x[0])

                for iTrack in detHitMap:
                    for index, hit in enumerate(detHitMap[iTrack]):
                        if iTrack < -1:  # If track id == -2 barcode will fail
                            continue
                        hit = hit[1]
                        layerID = (
                            6 * hit.GetLayer() + 2 * hit.GetPlane() + 4
                        )  # Layers correspond to SciFi planes, including Fe planes and navigation layers in between
                        event_id[0] = ievent
                        volume_id[0] = 1
                        boundary_id[0] = 0
                        layer_id[0] = layerID
                        approach_id[0] = 0
                        sens = hit.GetChannelID()  # Does this work properly?
                        sensitive_id[0] = sens
                        if global_variables.detector == "SND":
                            volumeVar = 2
                        else:
                            volumeVar = 1
                        geometry_id[0] = acts.GeometryIdentifier(volume=volumeVar, layer=layerID, sensitive=sens).value
                        barVal = acts.Barcode(primaryVertex=1, secondaryVertex=0, part=iTrack, gen=0, subpart=0).value
                        particle_id[0] = barVal
                        index_mtc[0] = index

                        # SHiP coordinate system translated to reconstruction coord system
                        # z -> x
                        # y -> y
                        # x -> -z
                        tx_mtc[0] = hit.GetZ() * 10  # Units cm -> mm
                        ty_mtc[0] = hit.GetY() * 10
                        tz_mtc[0] = -hit.GetX() * 10
                        tt_mtc[0] = 0
                        tpx_mtc[0] = 0.0
                        tpy_mtc[0] = 0.0
                        tpz_mtc[0] = 0.0
                        te_mtc[0] = 0.0
                        deltapx_mtc[0] = 0.0
                        deltapy_mtc[0] = 0.0
                        deltapz_mtc[0] = 0.0
                        deltae_mtc[0] = -hit.GetSignal()

                        mtcHitTree.Fill()

            if global_variables.detector == "StrawTracker":
                # Follow shipDigiReco method of only selecting the point with the earliest time
                ROOT.gRandom.SetSeed(13)
                t0 = ROOT.TRandom().Rndm() * 1 * u.microsecond
                strawHitArr.clear()
                earliestHitPerDet = {}
                for index, point in enumerate(event.strawtubesPoint):
                    hit = ROOT.strawtubesHit(point, t0)
                    strawHitArr.append([hit, point, point.GetTrackID()])
                    if hit.isValid():
                        detID = hit.GetDetectorID()
                        if detID in earliestHitPerDet:
                            earliest = earliestHitPerDet[detID]
                            if strawHitArr[earliest][0].GetTDC() > hit.GetTDC():
                                strawHitArr[earliest][0].setInvalid()
                                earliestHitPerDet[detID] = index
                            else:
                                strawHitArr[index][0].setInvalid()
                        else:
                            earliestHitPerDet[detID] = index

                # Loop through earliest hit in each straw
                for index, hit in enumerate(strawHitArr):
                    if hit[0].isValid():
                        ##Fill dictionary of tracks with valid hits and detectorID
                        detHitMap[hit[2]].append([hit[0].GetDetectorID(), hit[0], hit[1]])

                for i in detHitMap:
                    ##Ordered hit array for each track
                    detHitMap[i].sort(key=lambda x: x[0])

                for iTrack in detHitMap:
                    for index, hit in enumerate(detHitMap[iTrack]):
                        if iTrack < -1:  # If track id == -2 barcode will fail
                            continue
                        point = hit[2]
                        hit = hit[1]
                        layerID = 8 * hit.GetStationNumber() + 2 * hit.GetViewNumber() - 6

                        event_id_straw[0] = ievent
                        volume_id_straw[0] = 1  # Will only change when we have multiple tracking volumes built in geom
                        boundary_id_straw[0] = 0
                        layer_id_straw[0] = layerID
                        approach_id_straw[0] = 0
                        # Sensitive surface depends on view and layer
                        if hit.GetViewNumber() == 0 or hit.GetViewNumber() == 3:
                            sens = hit.GetStrawNumber() + hit.GetLayerNumber() * 300
                        else:
                            sens = hit.GetStrawNumber() + hit.GetLayerNumber() * 315

                        sensitive_id_straw[0] = sens

                        geometry_id_straw[0] = acts.GeometryIdentifier(volume=1, layer=layerID, sensitive=sens).value
                        particle_id_straw[0] = acts.Barcode(
                            primaryVertex=1, secondaryVertex=0, part=iTrack, gen=0, subpart=0
                        ).value
                        index_straw[0] = index

                        # SHiP coordinate system translated to reconstruction coord system
                        # z -> x
                        # y -> y
                        # x -> -z
                        tx_straw[0] = point.GetZ() * 10  # Units cm -> mm
                        ty_straw[0] = point.GetY() * 10
                        tz_straw[0] = -point.GetX() * 10
                        tt_straw[0] = hit.GetTDC()  # In microseconds
                        tpx_straw[0] = point.GetPz()
                        tpy_straw[0] = point.GetPy()
                        tpz_straw[0] = -point.GetPx()
                        te_straw[0] = 0.0
                        deltapx_straw[0] = 0.0
                        deltapy_straw[0] = 0.0
                        deltapz_straw[0] = 0.0
                        deltae_straw[0] = -point.GetEnergyLoss()  # Energy for only a single point

                        strawHitTree.Fill()

            ##Convert SHiP MCTrack into ACTS MC particle style EDM
            for count, part in enumerate(event.MCTrack):
                # He3, alpha, deutron, triton not in database, $ROOTSYS/etc/pdg_table.txt
                if part.GetPdgCode() >= 1000010020:
                    continue
                event_id_particle[0] = ievent
                generation_particle.push_back(0)
                barVal = acts.Barcode(primaryVertex=1, secondaryVertex=0, part=count, gen=0, subpart=0).value
                particle_id_particle.push_back(barVal)
                particle_type.push_back(part.GetPdgCode())
                process.push_back(0)  # Process not recorded, fill with zeros
                # SHiP coordinate system translated to reconstruction coord system
                # z -> x
                # y -> y
                # x -> -z
                fourVec = ROOT.Math.LorentzVector("ROOT::Math::PxPyPzE4D<double>")(
                    part.GetPz(), part.GetPy(), -part.GetPx(), part.GetEnergy()
                )
                vx.push_back(part.GetStartZ() * 10)  # Units mm
                vy.push_back(part.GetStartY() * 10)
                vz.push_back(-part.GetStartX() * 10)
                vt.push_back(part.GetStartT())
                px.push_back(part.GetPz())
                py.push_back(part.GetPy())
                pz.push_back(-part.GetPx())
                pp.push_back(part.GetP())
                m.push_back(part.GetMass())
                charge = PDG.GetParticle(part.GetPdgCode()).Charge()
                q.push_back(np.sign(charge))
                eta.push_back(fourVec.Eta())
                phi.push_back(fourVec.Phi())
                pt.push_back(fourVec.Pt())
                particle.push_back(count)
                sub_particle.push_back(0)
                vertex_primary.push_back(1)
                vertex_secondary.push_back(0)
                number_of_hits.push_back(len(detHitMap[count]))
                total_x0.push_back(0)
                total_l0.push_back(0)
                outcome.push_back(0)

                ## Fill Vertex tree here ##
                motherID = part.GetMotherId()
                motherMap[str(motherID)].append(count)  # Vector of particles grouped by mother
                motherMapVal[str(motherID)].append(barVal)  # Vector of particles grouped by mother

            particleTree.Fill()
            particle_id_particle.clear()
            particle_type.clear()
            process.clear()
            vx.clear()
            vy.clear()
            vz.clear()
            vt.clear()
            px.clear()
            py.clear()
            pz.clear()
            pp.clear()
            m.clear()
            q.clear()
            eta.clear()
            phi.clear()
            pt.clear()
            particle.clear()
            sub_particle.clear()
            generation_particle.clear()
            vertex_primary.clear()
            vertex_secondary.clear()
            number_of_hits.clear()
            total_x0.clear()
            total_l0.clear()
            outcome.clear()

            for c, i in enumerate(motherMap):
                particleCodes = motherMapVal[str(i)]
                # If there are not at least 2 tracks at decay vtx, do not write
                if len(particleCodes) < 2:
                    continue
                event_id_vertex[0] = ievent
                vertexVal = acts.Barcode(primaryVertex=1, secondaryVertex=0, part=0, gen=0, subpart=0).value
                vertex_id.push_back(vertexVal)
                particle_0ID = motherMap[str(i)]
                particle_0 = event.MCTrack[particle_0ID[0]]
                # SHiP coordinate system translated to reconstruction coord system
                # z -> x
                # y -> y
                # x -> -z
                vx_vtx.push_back(particle_0.GetStartZ() * 10)
                vy_vtx.push_back(particle_0.GetStartY() * 10)
                vz_vtx.push_back(-particle_0.GetStartX() * 10)
                vt_vtx.push_back(0)
                vertex_primary_vtx.push_back(1)
                vertex_secondary_vtx.push_back(0)
                generation_vtx.push_back(0)
                process_vtx.push_back(0)
                for j in particleCodes:
                    outgoing_particlesVec.push_back(j)
                outgoing_particles.push_back(outgoing_particlesVec)

            vertexTree.Fill()
            outgoing_particles.clear()
            outgoing_particlesVec.clear()
            vertex_id.clear()
            vx_vtx.clear()
            vy_vtx.clear()
            vz_vtx.clear()
            vt_vtx.clear()
            vertex_primary_vtx.clear()
            vertex_secondary_vtx.clear()
            generation_vtx.clear()
            process_vtx.clear()
            motherMap.clear()
            motherMapVal.clear()

        f.WriteObject(siHitTree, "siHits")
        f.WriteObject(mtcHitTree, "mtcHits")
        f.WriteObject(strawHitTree, "strawHits")
        f.WriteObject(particleTree, "particles")
        f.WriteObject(vertexTree, "vertices")


if __name__ == "__main__":
    ROOT.gErrorIgnoreLevel = ROOT.kWarning
    ROOT.gROOT.SetBatch(True)
    main()
