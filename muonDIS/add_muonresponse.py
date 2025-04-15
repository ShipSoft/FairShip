#!/usr/bin/env python
"""Script to add the incoming muon's MC hits in the SBT to the simulation file."""

import argparse
import logging
import os

import ROOT as r
from tabulate import tabulate

logging.basicConfig(level=logging.DEBUG)

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument(
    "-f",
    "--inputfile",
    required=True,
    help="Simulation file produced from DIS, WARNING: File will be modified.",
)
parser.add_argument(
    "-m",
    "--muonfile",
    required=True,
    help="Muon file used for DIS production (muonDis_<>.root)",
)
args = parser.parse_args()
headers = [
    "Event",
    "Muon vetoPoints Available",
    "Original VetoPoint Count",
    "Muon vetoPoints Added",
    "Combined VetoPoint Count",
    "Muon UBTPoints Available",
    "Original UBTPoint Count",
    "Muon UBTPoints Added",
    "Combined UBTPoint Count",
]


def inspect_file(inputfile, muonfile, print_table=False):
    """Inspecting the produced file for successfully added muon veto points."""
    input_file = r.TFile.Open(inputfile, "read")
    input_tree = input_file.cbmsim

    muon_file = r.TFile.Open(muonfile, "read")
    muon_tree = muon_file.DIS

    muons_found = False

    table_data = []

    for i, (muon_event, input_event) in enumerate(zip(muon_tree, input_tree)):
        muon_hits = len(muon_event.muon_vetoPoints)
        muoncount = 0
        if muon_hits:
            for hit in input_event.vetoPoint:
                if hit.GetTrackID() == 0:
                    muons_found = True
                    muoncount += 1

        muon_ubthits = len(muon_event.muon_UpstreamTaggerPoints)
        muon_ubtcount = 0
        if muon_ubthits:
            for hit in input_event.UpstreamTaggerPoint:
                if hit.GetTrackID() == 0:
                    muon_ubtcount += 1

        table_data.append(
            [
                i,
                muon_hits,
                len(input_event.vetoPoint) - muoncount,
                muoncount,
                len(input_event.vetoPoint),
                muon_ubthits,
                len(input_event.UpstreamTaggerPoint) - muon_ubtcount,
                muon_ubtcount,
                len(input_event.UpstreamTaggerPoint),
            ]
        )

    if print_table:
        print(tabulate(table_data, headers=headers, tablefmt="grid"))

    input_file.Close()
    muon_file.Close()

    return muons_found


def modify_file(inputfile, muonfile):
    """Add information from original muon to input simulation file."""
    logging.warning(
        f"vetoPoints & UpstreamTaggerPoints from the incoming muon (saved in {muonfile}) will be added to {inputfile}."
    )

    input_file = r.TFile.Open(inputfile, "read")
    try:
        input_tree = input_file.cbmsim
    except Exception as e:
        print(f"Error: {e}")
        input_file.Close()
        exit(1)

    # Open the external file with additional vetoPoints
    muon_file = r.TFile.Open(muonfile, "read")
    try:
        muon_tree = muon_file.DIS
    except Exception as e:
        print(f"Error: {e}")
        muon_file.Close()
        exit(1)

    temp_filename = inputfile.replace(".root", ".tmp")
    temp_file = r.TFile.Open(temp_filename, "recreate")
    output_tree = input_tree.CloneTree(
        0
    )  # Clone the structure of the existing tree, but do not copy the entries

    combined_vetoPoint = r.TClonesArray("vetoPoint")
    output_tree.SetBranchAddress("vetoPoint", combined_vetoPoint)

    combined_UpstreamTaggerPoint = r.TClonesArray("UpstreamTaggerPoint")
    output_tree.SetBranchAddress("UpstreamTaggerPoint", combined_UpstreamTaggerPoint)

    table_data = []

    for i, (input_event, muon_event) in enumerate(zip(input_tree, muon_tree)):
        interaction_point = r.TVector3()
        input_event.MCTrack[0].GetStartVertex(interaction_point)

        combined_vetoPoint.Clear()

        index = 0

        for hit in input_event.vetoPoint:
            if combined_vetoPoint.GetSize() == index:
                combined_vetoPoint.Expand(index + 1)
            combined_vetoPoint[index] = hit  # pending fix to support ROOT 6.32+
            index += 1

        muoncount = 0
        for hit in muon_event.muon_vetoPoints:
            if hit.GetZ() < interaction_point.Z():
                if combined_vetoPoint.GetSize() == index:
                    combined_vetoPoint.Expand(index + 1)
                combined_vetoPoint[index] = hit  # pending fix to support ROOT 6.32+
                index += 1
                muoncount += 1

        combined_UpstreamTaggerPoint.Clear()

        ubt_index = 0

        for hit in input_event.UpstreamTaggerPoint:
            if combined_UpstreamTaggerPoint.GetSize() == ubt_index:
                combined_UpstreamTaggerPoint.Expand(ubt_index + 1)
            combined_UpstreamTaggerPoint[ubt_index] = (
                hit  # pending fix to support ROOT 6.32+
            )
            ubt_index += 1

        muon_ubtcount = 0
        for hit in muon_event.muon_UpstreamTaggerPoints:
            if hit.GetZ() < interaction_point.Z():
                if combined_UpstreamTaggerPoint.GetSize() == ubt_index:
                    combined_UpstreamTaggerPoint.Expand(ubt_index + 1)
                combined_UpstreamTaggerPoint[ubt_index] = (
                    hit  # pending fix to support ROOT 6.32+
                )
                ubt_index += 1
                muon_ubtcount += 1

        table_data.append(
            [
                i,
                len(muon_event.muon_vetoPoints),
                len(input_event.vetoPoint),
                muoncount,
                len(combined_vetoPoint),
                len(muon_event.muon_UpstreamTaggerPoints),
                len(input_event.UpstreamTaggerPoint),
                muon_ubtcount,
                len(combined_UpstreamTaggerPoint),
            ]
        )
        output_tree.Fill()

    output_tree.Write("cbmsim", r.TObject.kOverwrite)
    temp_file.Close()
    input_file.Close()
    muon_file.Close()

    os.remove(inputfile)
    os.rename(temp_filename, inputfile)
    print(f"File updated with incoming muon info as {inputfile}")
    print(tabulate(table_data, headers=headers, tablefmt="grid"))


muons_found = inspect_file(args.inputfile, args.muonfile)

if not muons_found:
    print(
        "Incoming muon's vetoPoints & UpstreamTaggerPoints inf missing in file, proceeding with modification"
    )
    modify_file(args.inputfile, args.muonfile)
else:
    print("File is already updated with incoming muon info. Nothing to do.")
    muons_found = inspect_file(args.inputfile, args.muonfile, print_table=True)
