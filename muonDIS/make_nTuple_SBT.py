#!/usr/bin/env python
"""Script to collect muons hitting the SBT (including soft interaction products) to a ROOT file."""

import argparse
import csv
import logging
import os

import ROOT as r
import shipunit as u
from tabulate import tabulate

pdg = r.TDatabasePDG.Instance()


logging.basicConfig(level=logging.INFO)


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--test", dest="testing_code", help="Run Test", action="store_true")
parser.add_argument(
    "-o",
    "--outputfile",
    default="muonsProduction_wsoft_SBT.root",
    help="custom outputfile name",
)
parser.add_argument(
    "-p",
    "--path",
    help="path to muon background files",
    default="/eos/experiment/ship/simulation/bkg/MuonBack_2024helium/8070735",
)
args = parser.parse_args()

if args.testing_code:
    logging.info(
        "test code, output file name overwritten as: muonsProduction_wsoft_SBT_test.root"
    )
    args.outputfile = "muonsProduction_wsoft_SBT_test.root"
    selectedmuons = "SelectedMuonsSBT_test.txt"
else:
    selectedmuons = "SelectedMuonsSBT.txt"

path = args.path
logging.info(f"Path to MuonBackground : {path}")

fsel = open(selectedmuons, "w")
csvwriter = csv.writer(fsel)

output_file = r.TFile.Open(args.outputfile, "recreate")
output_tree = r.TTree(
    "MuonAndSoftInteractions", "Muon information and soft interaction tracks"
)

imuondata = r.TVectorD(
    10
)  # 10 values: pid, px, py, pz, x, y, z, weight,time_of_hit,nmuons_in_event
output_tree.Branch("imuondata", imuondata)

track_array = r.TObjArray()
output_tree.Branch("tracks", track_array)

muon_vetoPoints = r.TClonesArray("vetoPoint")
output_tree.Branch("muon_vetoPoints", muon_vetoPoints)

muon_UpstreamTaggerPoints = r.TClonesArray("UpstreamTaggerPoint")
output_tree.Branch("muon_UpstreamTaggerPoints", muon_UpstreamTaggerPoints)

h = {}
h["PvPt_muon"] = r.TH2F(
    "PvPt_muon",
    "The momentum of the muons hitting the SBT(unweighted);P(GeV/c);Pt(GeV/c)",
    200,
    0.0,
    400,
    40,
    0.0,
    20,
)
h["n_muon"] = r.TH2I(
    "n_muon",
    "Number of muons hitting the SBT per Event;number of mu- per event (unweighted) bin width =1;number of mu+ per event (unweighted) bin width=1",
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
h["n_sbthits"] = r.TH1I(
    "n_sbthits", "Number of SBT hits per muon;n_sbthits(unweighted);", 900, 0, 900
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
    "nSBT Hits(muon)",
    "nUBT Hits(muon)",
    "Weight_muon",
]

csvwriter.writerow(headers)

for inputFolder in os.listdir(path):
    if not os.path.isdir(os.path.join(path, inputFolder)):
        continue

    if args.testing_code and global_event_nr >= 100000:
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
        logging.debug(f"Error :{e}")

        if f:
            f.Close()
        continue

    for eventNr, event in enumerate(tree):
        global_event_nr += 1

        muon_table = []

        nmu = {"mu+": 0, "mu-": 0}

        muon_ids = []
        muon_hits = {}
        # Collect track IDs of muons which hit the SBT
        for hit in event.vetoPoint:
            detID = hit.GetDetectorID()
            pid = hit.PdgCode()
            track_id = hit.GetTrackID()
            P = r.TMath.Sqrt(hit.GetPx() ** 2 + hit.GetPy() ** 2 + hit.GetPz() ** 2)

            if 1000 < detID < 999999 and abs(pid) == 13 and P > P_threshold / u.GeV:
                particle_name = pdg.GetParticle(hit.PdgCode()).GetName()
                if track_id not in muon_ids:
                    muon_ids.append(track_id)
                    muon_hits[track_id] = 0
                    nmu[particle_name] += 1
                muon_hits[track_id] += 1

        if not len(muon_ids):
            continue

        logging.debug(f"\n\nEVENT ID:{global_event_nr}")
        logging.debug(
            f"Muon Track Available:{muon_hits.keys()}\n Number of SBT hits within:{muon_hits}"
        )

        for muon_ in muon_ids:
            imuondata.Zero()

            # saving soft tracks
            track_array.Clear()

            for track in event.MCTrack:
                if track.GetMotherId() == muon_ and (
                    not track.GetProcName().Data() == "Muon nuclear interaction"
                ):
                    track_array.Add(track)

            # saving the muon info

            muon_UpstreamTaggerPoints.Clear()

            ubt_index = 0

            for hit in event.UpstreamTaggerPoint:
                track_id = hit.GetTrackID()

                if not (track_id == muon_):
                    continue

                if muon_UpstreamTaggerPoints.GetSize() == ubt_index:
                    muon_UpstreamTaggerPoints.Expand(ubt_index + 1)
                muon_UpstreamTaggerPoints[ubt_index] = hit

                ubt_index += 1

            index = 0

            muon_vetoPoints.Clear()

            for hit in event.vetoPoint:
                detID = hit.GetDetectorID()
                pid = hit.PdgCode()
                track_id = hit.GetTrackID()

                P = r.TMath.Sqrt(hit.GetPx() ** 2 + hit.GetPy() ** 2 + hit.GetPz() ** 2)
                Pt = r.TMath.Sqrt(hit.GetPx() ** 2 + hit.GetPy() ** 2)

                if (
                    1000 < detID < 999999
                    and track_id == muon_
                    and P > P_threshold / u.GeV
                ):
                    if global_event_nr not in processed_events:
                        processed_events[global_event_nr] = []

                    if muon_vetoPoints.GetSize() == index:
                        muon_vetoPoints.Expand(index + 1)
                    muon_vetoPoints[index] = hit

                    index += 1

                    weight = event.MCTrack[track_id].GetWeight()

                    if (
                        track_id not in processed_events[global_event_nr]
                    ):  # only save the info of first SBT hit
                        processed_events[global_event_nr].append(track_id)

                        imuondata[0] = float(pid)
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
                                len(muon_UpstreamTaggerPoints),
                                imuondata[7],
                            ]
                        )

                        h["PvPt_muon"].Fill(P, Pt)
                        h["n_softtracks"].Fill(len(track_array))

                    muon_table[-1][-2] = len(muon_vetoPoints)

            h["n_sbthits"].Fill(len(muon_vetoPoints))

            output_tree.Fill()

        h["n_muon"].Fill(nmu["mu-"], nmu["mu+"])
        csvwriter.writerows(row[1:] for row in muon_table)
        # dump(event)
        logging.debug(
            f"Muon Summary:\n{tabulate(muon_table, headers=headers, tablefmt='grid')}\n\n"
        )

    f.Close()


total_muons = sum(len(values) for values in processed_events.values())
print(f"nMuons saved: {total_muons}, File: {args.outputfile}")

output_file.cd()
output_tree.Write()
for histname in h:
    h[histname].Write()
output_file.Close()
fsel.close()

print(
    "------------------------------------------------------file saved, inspecting",
    args.outputfile,
    "now----------------------------------------------------------------",
)

event_data = []
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
        nmuons = imuondata[9]

        num_tracks = len(event.tracks)
        num_muonhits = len(event.muon_vetoPoints)
        num_ubthits = len(event.muon_UpstreamTaggerPoints)

        P = r.TMath.Sqrt(px**2 + py**2 + pz**2)

        event_data.append(
            [
                nmuons,
                pid,
                P,
                x,
                y,
                z,
                time_hit,
                num_tracks,
                num_muonhits,
                num_ubthits,
                weight,
            ]
        )

print(tabulate(event_data, headers=headers, tablefmt="grid"))
