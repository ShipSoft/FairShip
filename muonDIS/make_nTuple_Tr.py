#!/usr/bin/env python
"""Script to collect muons hitting the 1st Tracking Station (including soft interaction products) to a ROOT file."""

import argparse
<<<<<<< HEAD
import csv
=======
>>>>>>> 7747b728 (Added MuonDIS directory for updated scripts)
import logging
import os

import ROOT as r
import shipunit as u
<<<<<<< HEAD
from tabulate import tabulate

pdg = r.TDatabasePDG.Instance()


logging.basicConfig(level=logging.INFO)


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--test", dest="testing_code", help="Run Test", action="store_true")
=======

# Histogram
hPmuon = r.TH1F(
    "hPmuon", "Momentum of muons hitting the SBT;P [GeV];Entries", 400, 0.0, 400
)

# Argument parser
parser = argparse.ArgumentParser(description=__doc__)
>>>>>>> 7747b728 (Added MuonDIS directory for updated scripts)
parser.add_argument(
    "-o",
    "--outputfile",
    default="muonsProduction_wsoft_Tr.root",
    help="custom outputfile name",
)
parser.add_argument(
<<<<<<< HEAD
    "-p",
    "--path",
    help="path to muon background files",
    default="/eos/experiment/ship/simulation/bkg/MuonBack_2024helium/8070735",
)
args = parser.parse_args()

=======
    "-p", dest="path", help="path to muon background files", required=False
)
parser.add_argument("-test", dest="testing_code", help="Run Test", action="store_true")
args = parser.parse_args()

# Variables
ev = 0
evs = [0, 0, 0]
processed_events = set()


>>>>>>> 7747b728 (Added MuonDIS directory for updated scripts)
if args.testing_code:
    print(
        "test code, output file name overwritten as: muonsProduction_wsoft_Tr_test.root"
    )
    args.outputfile = "muonsProduction_wsoft_Tr_test.root"
    selectedmuons = "SelectedMuonsTr_test.txt"
else:
    selectedmuons = "SelectedMuonsTr.txt"

<<<<<<< HEAD
path = args.path
logging.info(f"Path to MuonBackground : {path}")

fsel = open(selectedmuons, "w")
csvwriter = csv.writer(fsel)

=======
# Output file and tree setup
>>>>>>> 7747b728 (Added MuonDIS directory for updated scripts)
output_file = r.TFile.Open(args.outputfile, "recreate")
output_tree = r.TTree(
    "MuonAndSoftInteractions", "Muon information and soft interaction tracks"
)

<<<<<<< HEAD
imuondata = r.TVectorD(
    10
)  # 10 values: pid, px, py, pz, x, y, z, weight,time_of_hit,nmuons_in_event
=======
imuondata = r.TVectorD(9)  # 9 values: pid, px, py, pz, x, y, z, weight,time_of_hit
>>>>>>> 7747b728 (Added MuonDIS directory for updated scripts)
output_tree.Branch("imuondata", imuondata)

track_array = r.TObjArray()
output_tree.Branch("tracks", track_array)

muon_vetoPoints = r.TClonesArray("vetoPoint")
output_tree.Branch("muon_vetoPoints", muon_vetoPoints)

<<<<<<< HEAD

h = {}
h["PvPt_muon"] = r.TH2F(
    "PvPt_muon",
    "The momentum of the muons hitting Tracking Station 1 (unweighted);P(GeV/c);Pt(GeV/c)",
    200,
    0.0,
    400,
    40,
    0.0,
    20,
)
h["n_muon"] = r.TH2I(
    "n_muon",
    "Number of muons hitting the Tracking Station 1 per Event;number of mu- per event (unweighted) bin width =1;number of mu+ per event (unweighted) bin width=1",
    6,
    0.0,
    6,
    6,
    0.0,
    6,
)
h["n_softtracks"] = r.TH1I(
    "n_softtracks", "Number of soft tracks per muon;;(unweighted)", 200, 0, 2000
)


def printMCTrack(n, MCTrack):
    """Print MCTrack truth."""
    mcp = MCTrack[n]

    RED = "\033[91m"  # ANSI code Red
    RESET = "\033[0m"  # ANSI code Reset to default

    try:
        particle_name = pdg.GetParticle(mcp.GetPdgCode()).GetName()

        if particle_name == "mu+" or particle_name == "mu-":
            particle_name = (
                f"{RED}{particle_name}{RESET}       "  # Highlight muons in red
            )

        print(
            " %6s %-10s %10i %6.3F %6.3F %7.3F %7.3F %7.3F %7.3F %6s %10.3F %28s"
            % (
                n,
                particle_name,
                mcp.GetPdgCode(),
                mcp.GetPx() / u.GeV,
                mcp.GetPy() / u.GeV,
                mcp.GetPz() / u.GeV,
                mcp.GetStartX() / u.m,
                mcp.GetStartY() / u.m,
                mcp.GetStartZ() / u.m,
                mcp.GetMotherId(),
                mcp.GetWeight(),
                mcp.GetProcName().Data(),
            )
        )
    except Exception:
        print(
            " %6s %-10s %10i %6.3F %6.3F %7.3F %7.3F %7.3F %7.3F %6s %10.3F %28s"
            % (
                n,
                "----",
                mcp.GetPdgCode(),
                mcp.GetPx() / u.GeV,
                mcp.GetPy() / u.GeV,
                mcp.GetPz() / u.GeV,
                mcp.GetStartX() / u.m,
                mcp.GetStartY() / u.m,
                mcp.GetStartZ() / u.m,
                mcp.GetMotherId(),
                mcp.GetWeight(),
                mcp.GetProcName().Data(),
            )
        )


def dump(event, pcut=0, print_whole_event=True):
    """Dump the whole event."""
    if print_whole_event:
        print(
            "\n %6s %-10s %10s %6s %6s %7s %7s %7s %7s %6s %10s %18s"
            % (
                "#",
                "particle",
                "pid",
                "px",
                "py",
                "pz",
                "vx",
                "vy",
                "vz",
                "mid",
                "w",
                "Process",
            )
        )
        print(
            " %6s %10s %10s %6s %6s %7s %7s %7s %7s %6s %10s %18s\n "
            % (
                " ",
                "--------",
                "---",
                "--",
                "--",
                "--",
                "--",
                "--",
                "--",
                "---",
                "---",
                "-------",
            )
        )
    n = -1
    for mcp in event.MCTrack:
        n += 1
        if mcp.GetP() / u.GeV < pcut:
            continue
        if print_whole_event:
            printMCTrack(n, event.MCTrack)

    return


events_ = {"Tr": {}, "Tr_SBT": {}, "Tr_noSBT": {}}
global_event_nr = 0
processed_events = {}

P_threshold = 3

headers = [
    f"nMuons in event>{P_threshold}GeV",
    "Muon PID",
    "Momentum[GeV/c]",
    "x[m]",
    "y[m]",
    "z[m]",
    "t_muon [ns]",
    "nSoft Tracks",
    "nSBT Hits",
    "Weight_muon",
]
csvwriter.writerow(headers)

for inputFolder in os.listdir(path):
    if not os.path.isdir(os.path.join(path, inputFolder)):
        continue

    if args.testing_code and len(events_["Tr_noSBT"]) >= 5:
        break

    logging.info(f"Processing folder: {inputFolder}")
    f = None
    try:
        f = r.TFile.Open(
            os.path.join(path, inputFolder, "ship.conical.MuonBack-TGeant4.root"),
            "read",
        )
        tree = f.cbmsim
    except Exception as e:
        print(f"Error :{e}")

        if f:
            f.Close()
        continue

    for event in tree:
        nmu = {"mu+": 0, "mu-": 0}

        muon_table = []
        global_event_nr += 1

        muon_ids = []

        # Collect track IDs of muons which hit the Tracking Station
        for hit in event.strawtubesPoint:
            detID = hit.GetDetectorID()
            trackingstation_id = (
                detID // 10000000
            )  # will need to update if strawtubes detID is changed
            pid = hit.PdgCode()
            P = r.TMath.Sqrt(hit.GetPx() ** 2 + hit.GetPy() ** 2 + hit.GetPz() ** 2)
            if abs(pid) == 13 and trackingstation_id == 1 and P > P_threshold / u.GeV:
                track_id = hit.GetTrackID()
                particle_name = pdg.GetParticle(hit.PdgCode()).GetName()
                if track_id not in muon_ids:
                    muon_ids.append(track_id)

                if global_event_nr not in events_["Tr"]:
                    events_["Tr"][global_event_nr] = set()

                events_["Tr"][global_event_nr].add(track_id)

        if not len(muon_ids):
            continue
        # dump(event)

        for muon_ in muon_ids:
            muon_vetoPoints.Clear()

            if global_event_nr not in events_["Tr_SBT"]:
                events_["Tr_SBT"][global_event_nr] = set()

            for hit in event.vetoPoint:
                detID = hit.GetDetectorID()
                pid = hit.PdgCode()
                track_id = hit.GetTrackID()
                P = r.TMath.Sqrt(hit.GetPx() ** 2 + hit.GetPy() ** 2 + hit.GetPz() ** 2)

                if track_id == muon_:
                    events_["Tr_SBT"][global_event_nr].add(track_id)
                    continue

                    # if muon_vetoPoints.GetSize() == index:
                    #    muon_vetoPoints.Expand(index + 1)
                    # muon_vetoPoints[index] = hit # this should be zero if the code is correct
                    # index += 1

            if muon_ in events_["Tr_SBT"][global_event_nr]:
                continue

            track_array.Clear()
            for track in event.MCTrack:
                if track.GetMotherId() == muon_ and (
=======
if args.path:
    path = args.path
else:
    path = "/eos/experiment/ship/simulation/bkg/MuonBack_2024helium/sc_v6_10_spills"

fsel = open(selectedmuons, "w")

logging.basicConfig(level=logging.INFO)

for inputFolder in os.listdir(path):
    for subFolder in os.listdir(os.path.join(path, inputFolder)):
        if not os.path.isdir(os.path.join(path, inputFolder, subFolder)):
            continue

        if args.testing_code and evs[2] >= 2:
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
>>>>>>> 7747b728 (Added MuonDIS directory for updated scripts)
                    not track.GetProcName().Data() == "Muon nuclear interaction"
                ):
                    track_array.Add(track)

<<<<<<< HEAD
            for hit in event.strawtubesPoint:
                detID = hit.GetDetectorID()
                track_id = hit.GetTrackID()
                pid = hit.PdgCode()

                P = r.TMath.Sqrt(hit.GetPx() ** 2 + hit.GetPy() ** 2 + hit.GetPz() ** 2)
                Pt = r.TMath.Sqrt(hit.GetPx() ** 2 + hit.GetPy() ** 2)

                trackingstation_id = (
                    detID // 10000000
                )  # will need to update if strawtubes detID is changed

                if (
                    abs(hit.PdgCode()) == 13
                    and trackingstation_id == 1
                    and P > P_threshold / u.GeV
                ):
                    if global_event_nr not in events_["Tr_noSBT"]:
                        events_["Tr_noSBT"][global_event_nr] = set()

                    events_["Tr_noSBT"][global_event_nr].add(track_id)

                    if global_event_nr not in processed_events:
                        processed_events[global_event_nr] = []

                    if (
                        track_id not in processed_events[global_event_nr]
                    ):  # only save the info of first SBT hit
                        processed_events[global_event_nr].append(track_id)

                        particle_name = pdg.GetParticle(hit.PdgCode()).GetName()

                        nmu[particle_name] += 1

                        weight = event.MCTrack[track_id].GetWeight()

                        # Fill imuondata
                        imuondata[0] = float(hit.PdgCode())
                        imuondata[1] = float(hit.GetPx() / u.GeV)
                        imuondata[2] = float(hit.GetPy() / u.GeV)
                        imuondata[3] = float(hit.GetPz() / u.GeV)
                        imuondata[4] = float(hit.GetX() / u.m)
                        imuondata[5] = float(hit.GetY() / u.m)
                        imuondata[6] = float(hit.GetZ() / u.m)
                        imuondata[7] = float(weight)
                        imuondata[8] = float(hit.GetTime())
                        imuondata[9] = len(muon_ids)
                        muon_table.append(
                            [
                                track_id,
                                len(muon_ids),
                                imuondata[0],
                                P,
                                imuondata[4],
                                imuondata[5],
                                imuondata[6],
                                imuondata[8],
                                len(track_array),
                                len(muon_vetoPoints),
                                imuondata[7],
                            ]
                        )
                        h["PvPt_muon"].Fill(P, Pt)
                        h["n_softtracks"].Fill(len(track_array))
            output_tree.Fill()

        if len(muon_table):
            h["n_muon"].Fill(nmu["mu-"], nmu["mu+"])
            csvwriter.writerows(row[1:] for row in muon_table)
            logging.debug(
                f"EVENT ID:{global_event_nr}\n\tMuon Summary:\n{tabulate(muon_table, headers=headers, tablefmt='grid')}\n\n"
            )

for type_ in events_:
    # Calculate total number of muons
    total_muons = sum(len(muons) for muons in events_[type_].values())
    print(
        f"{type_}, \tnEvents:{sum(bool(len(muons)) for muons in events_[type_].values())}, \tnMuons:{total_muons}"
    )
output_file.cd()
output_tree.Write()
for histname in h:
    h[histname].Write()
output_file.Close()
=======
            # saving the incoming muon's veto response
            index = 0
            muon_vetoPoints.Clear()
            for hit in event.vetoPoint:
                detID = hit.GetDetectorID()
                pid = hit.PdgCode()
                if 1000 < detID < 999999 and abs(pid) == 13:
                    if muon_vetoPoints.GetSize() == index:
                        muon_vetoPoints.Expand(index + 1)
                    muon_vetoPoints[index] = hit
                    index += 1

            strawDic, trackDic = [], []

            # Process straw tube hits
            for strawHit in event.strawtubesPoint:
                P = r.TMath.Sqrt(
                    strawHit.GetPx() ** 2
                    + strawHit.GetPy() ** 2
                    + strawHit.GetPz() ** 2
                )
                if P > 3:
                    detIDmuonS = (
                        strawHit.GetDetectorID() // 10000000
                    )  # will need to update if strawtubes detID is changed
                    if abs(strawHit.PdgCode()) == 13 and detIDmuonS == 1:
                        # print(detIDmuonS,strawHit.GetTrackID())
                        if strawHit.GetTrackID() not in strawDic:
                            strawDic.append(strawHit.GetTrackID())
                            evs[0] += 1
                            if evs[0] % 100 == 0:
                                print(f"evs0: {evs[0]}")

            # Process vetoPoint hits
            for hit in event.vetoPoint:
                detID = hit.GetDetectorID()
                pid = hit.PdgCode()
                trackID = hit.GetTrackID()
                if 1000 < detID < 999999 and abs(pid) == 13:
                    if trackID not in trackDic:
                        trackDic.append(trackID)
                        evs[1] += 1
                        if evs[1] % 100 == 0:
                            print(f"evs1: {evs[1]}")

            # Check for muons hitting Tr but not SBT and only save them
            for m in strawDic:
                if m not in trackDic:
                    for Hit in event.strawtubesPoint:
                        if m == Hit.GetTrackID() and ev not in processed_events:
                            processed_events.add(ev)
                            evs[2] += 1
                            print(f"evs2: {evs[2]}")
                            P = r.TMath.Sqrt(
                                Hit.GetPx() ** 2 + Hit.GetPy() ** 2 + Hit.GetPz() ** 2
                            )
                            weight = tree.MCTrack[m].GetWeight()
                            hPmuon.Fill(P, weight)

                            # Fill imuondata
                            imuondata[0] = float(Hit.PdgCode())
                            imuondata[1] = float(Hit.GetPx() / u.GeV)
                            imuondata[2] = float(Hit.GetPy() / u.GeV)
                            imuondata[3] = float(Hit.GetPz() / u.GeV)
                            imuondata[4] = float(Hit.GetX() / u.m)
                            imuondata[5] = float(Hit.GetY() / u.m)
                            imuondata[6] = float(Hit.GetZ() / u.m)
                            imuondata[7] = float(weight)
                            imuondata[8] = float(hit.GetTime())

                            output_tree.Fill()

                            fsel.write(
                                f"{Hit.PdgCode()} {Hit.GetPx() / u.GeV} {Hit.GetPy() / u.GeV} "
                                f"{Hit.GetPz() / u.GeV} {Hit.GetX() / u.m} {Hit.GetY() / u.m} "
                                f"{Hit.GetZ() / u.m} {weight}\n"
                            )

output_file.cd()
output_tree.Write()
hPmuon.Write()
output_file.Close()
print("Finish:", evs)
>>>>>>> 7747b728 (Added MuonDIS directory for updated scripts)
fsel.close()


print(
    "------------------------------------------------------file saved, reading",
    args.outputfile,
    " now----------------------------------------------------------------",
)
<<<<<<< HEAD
event_data = []
=======

>>>>>>> 7747b728 (Added MuonDIS directory for updated scripts)
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
<<<<<<< HEAD

        weight = imuondata[7]
        time_hit = imuondata[8]
        nmuons = imuondata[9]

        num_tracks = len(event.tracks)
        num_muonhits = len(event.muon_vetoPoints)

        P = r.TMath.Sqrt(px**2 + py**2 + pz**2)

        event_data.append(
            [nmuons, pid, P, x, y, z, time_hit, num_tracks, num_muonhits, weight]
        )
print(tabulate(event_data, headers=headers, tablefmt="grid"))
=======
        weight = imuondata[7]
        time_hit = imuondata[8]
        num_tracks = len(event.tracks)
        num_muonhits = len(event.muon_vetoPoints)

        print(
            f"Muon PID: {pid},  x: {x}, y: {y}, z: {z}, t_muon: {time_hit}, "
            f"Number of soft tracks in this event: {num_tracks}, "
            f"Number of SBT hits from the muon: {num_muonhits}"
        )
>>>>>>> 7747b728 (Added MuonDIS directory for updated scripts)
