#!/usr/bin/env python
"""Script to collect muons hitting the SBT (including soft interaction products) to a ROOT file."""

import argparse
import logging
import os

import ROOT as r
import shipunit as u

# Argument parser setup
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("-test", dest="testing_code", help="Run Test", action="store_true")
parser.add_argument(
    "-p", dest="path", help="path to muon background files", required=False
)
parser.add_argument(
    "-o",
    "--outputfile",
    default="muonsProduction_wsoft_SBT.root",
    help="custom outputfile name",
)
args = parser.parse_args()

# Histogram setup
hnumSegPermmuon = r.TH1I(
    "hnumSegPermmuon", "Numbers of fired segments per muon", 200, 0.0, 200
)
hPmuon = r.TH1F("hPmuon", "The momentum of the muons hitting the SBT", 400, 0.0, 400)

# Initialize variables
ev = 0
processed_events = set()

if args.testing_code:
    print(
        "test code, output file name overwritten as: muonsProduction_wsoft_SBT_test.root"
    )
    args.outputfile = "muonsProduction_wsoft_SBT_test.root"
    selectedmuons = "SelectedMuonsSBT_test.txt"
else:
    selectedmuons = "SelectedMuonsSBT.txt"

if args.path:
    path = args.path
else:
    path = "/eos/experiment/ship/simulation/bkg/MuonBack_2024helium/sc_v6_10_spills"

fsel = open(selectedmuons, "w")

output_file = r.TFile.Open(args.outputfile, "recreate")
output_tree = r.TTree(
    "MuonAndSoftInteractions", "Muon information and soft interaction tracks"
)

imuondata = r.TVectorD(9)  # 9 values: pid, px, py, pz, x, y, z, weight,time_of_hit
output_tree.Branch("imuondata", imuondata)

track_array = r.TObjArray()
output_tree.Branch("tracks", track_array)

muon_vetoPoints = r.TClonesArray("vetoPoint")
output_tree.Branch("muon_vetoPoints", muon_vetoPoints)

logging.basicConfig(level=logging.INFO)

for inputFolder in os.listdir(path):
    for subFolder in os.listdir(os.path.join(path, inputFolder)):
        if not os.path.isdir(os.path.join(path, inputFolder, subFolder)):
            continue

        if args.testing_code and ev >= 100000:
            break

        logging.info(f"Processing folder: {inputFolder}/{subFolder}")
        f = r.TFile.Open(
            os.path.join(
                path, inputFolder, subFolder, "ship.conical.MuonBack-TGeant4.root"
            ),
            "read",
        )

        try:
            tree = f.cbmsim
        except Exception as e:
            print(f"Error :{e}")
            f.Close()
            continue

        for event in tree:
            ev += 1
            numHitsPermuon = 0

            # saving soft tracks
            track_array.Clear()

            muon_id = None
            for itrk in range(event.MCTrack.GetEntries()):
                # loops through MCTracks to find the incoming Muon's track id.
                if abs(event.MCTrack[itrk].GetPdgCode()) == 13:
                    muon_id = itrk
                    break

            for track in event.MCTrack:
                if track.GetMotherId() == muon_id and (
                    not track.GetProcName().Data() == "Muon nuclear interaction"
                ):
                    track_array.Add(track)

            index = 0
            muon_vetoPoints.Clear()

            # saving the incoming muon's veto response
            for hit in event.vetoPoint:
                detID = hit.GetDetectorID()
                pid = hit.PdgCode()
                if 1000 < detID < 999999 and abs(pid) == 13:
                    if muon_vetoPoints.GetSize() == index:
                        muon_vetoPoints.Expand(index + 1)
                    muon_vetoPoints[index] = hit
                    index += 1

            for hit in event.vetoPoint:
                detID = hit.GetDetectorID()
                pid = hit.PdgCode()
                trackID = hit.GetTrackID()

                if abs(pid) == 13:
                    numHitsPermuon += 1
                    if ev not in processed_events:
                        processed_events.add(ev)
                        P = r.TMath.Sqrt(
                            hit.GetPx() ** 2 + hit.GetPy() ** 2 + hit.GetPz() ** 2
                        )
                        weight = event.MCTrack[trackID].GetWeight()
                        hPmuon.Fill(P, weight)

                        if P > 3 / u.GeV:
                            imuondata[0] = float(pid)
                            imuondata[1] = float(hit.GetPx() / u.GeV)
                            imuondata[2] = float(hit.GetPy() / u.GeV)
                            imuondata[3] = float(hit.GetPz() / u.GeV)
                            imuondata[4] = float(hit.GetX() / u.m)
                            imuondata[5] = float(hit.GetY() / u.m)
                            imuondata[6] = float(hit.GetZ() / u.m)
                            imuondata[7] = float(weight)
                            imuondata[8] = float(hit.GetTime())

                            output_tree.Fill()

                            fsel.write(
                                f"{pid} {hit.GetPx() / u.GeV} {hit.GetPy() / u.GeV} {hit.GetPz() / u.GeV} {hit.GetX() / u.m} {hit.GetY() / u.m} {hit.GetZ() / u.m} {weight}\n"
                            )

            if numHitsPermuon != 0:
                hnumSegPermmuon.Fill(numHitsPermuon)

        f.Close()


output_file.cd()
output_tree.Write()
hnumSegPermmuon.Write()
hPmuon.Write()
output_file.Close()
fsel.close()

print(
    "------------------------------------------------------file saved, reading",
    args.outputfile,
    " now----------------------------------------------------------------",
)

with r.TFile.Open(args.outputfile, "read") as file:
    try:
        tree = file.MuonAndSoftInteractions
    except Exception as e:
        print(f"Error: {e}")
        exit(1)

    print(f"Processing tree: {tree.GetName()}")
    print(f"Total number of entries: {tree.GetEntries()}")

    for event in tree:
        imuondata = event.imuondata
        pid = imuondata[0]
        px = imuondata[1]
        py = imuondata[2]
        pz = imuondata[3]
        x = imuondata[4]
        y = imuondata[5]
        z = imuondata[6]
        weight = imuondata[7]
        time_hit = imuondata[8]
        num_tracks = len(event.tracks)
        num_muonhits = len(event.muon_vetoPoints)

        print(
            f"Muon PID: {pid},  x: {x}, y: {y}, z: {z}, t_muon: {time_hit}, "
            f"Number of soft tracks in this event: {num_tracks}, "
            f"Number of SBT hits from the muon: {num_muonhits}"
        )
