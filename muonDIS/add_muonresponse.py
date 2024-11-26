#!/usr/bin/env python
"""Script to add the incoming muon's MC hits in the SBT to the simulation file."""

import argparse
import logging

import ROOT as r
<<<<<<< HEAD
from tabulate import tabulate

logging.basicConfig(level=logging.DEBUG)
=======
>>>>>>> 7747b728 (Added MuonDIS directory for updated scripts)

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
<<<<<<< HEAD
headers = [
    "Event",
    "Muon vetoPoints Available",
    "Original VetoPoint Count",
    "Muon vetoPoints Added",
    "Combined VetoPoint Count",
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
        table_data.append(
            [
                i,
                muon_hits,
                len(input_event.vetoPoint) - muoncount,
                muoncount,
                len(input_event.vetoPoint),
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
        f"vetoPoints from the incoming muon (saved in {muonfile}) will be added to {inputfile}."
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
=======


def inspect_file(inputfile):
    """Inspecting the produced file for successfully added muon veto points."""
    input_file = r.TFile.Open(inputfile, "READ")
    input_tree = input_file.cbmsim
    input_tree.GetEntry(0)

    muons = False
    for hit in input_tree.vetoPoint:
        if hit.GetTrackID() == 0:
            muons = True
    input_file.Close()

    if muons:
        print("File is already updated with incoming muon info. Nothing to do.")
        return False
    else:
        print(
            "Incoming muon's vetopoint info missing in file, proceeding with modification"
        )
        return True


def modify_file(inputfile, muonfile):
    """Add information from original muon to input simulation file."""
    logging.warning(f"{inputfile} will be opened for modification")

    input_file = r.TFile.Open(inputfile, "UPDATE")
    try:
        input_tree = input_file.cbmsim
    except Exception as e:
        print(f"Error: {e}")
        input_file.Close()
        exit(1)

    # Open the external file with additional vetoPoints
    muon_file = r.TFile.Open(muonfile, "READ")
    try:
        muon_tree = muon_file.DIS
    except Exception as e:
        print(f"Error: {e}")
        muon_file.Close()
        exit(1)

<<<<<<< HEAD
    inputFile.cd()
>>>>>>> 7747b728 (Added MuonDIS directory for updated scripts)
=======
    input_file.cd()
>>>>>>> e494e97a (Avoid listdir for non-directory case)
    output_tree = input_tree.CloneTree(
        0
    )  # Clone the structure of the existing tree, but do not copy the entries

<<<<<<< HEAD
    combined_vetoPoint = r.TClonesArray("vetoPoint")

    output_tree.SetBranchAddress("vetoPoint", combined_vetoPoint)
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

        table_data.append(
            [
                i,
                len(muon_event.muon_vetoPoints),
                len(input_event.vetoPoint),
                muoncount,
                len(combined_vetoPoint),
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
        "Incoming muon's vetopoint info missing in file, proceeding with modification"
    )
    modify_file(args.inputfile, args.muonfile)
else:
    print("File is already updated with incoming muon info. Nothing to do.")
    muons_found = inspect_file(args.inputfile, args.muonfile, print_table=True)
=======
    # Access the vetoPoint branch in the original and external trees
    original_vetoPoint = r.TClonesArray("vetoPoint")
    muon_vetoPoint = r.TClonesArray("vetoPoint")
    combined_vetoPoint = r.TClonesArray("vetoPoint")

    input_tree.SetBranchAddress("vetoPoint", original_vetoPoint)
    muon_tree.SetBranchAddress("muon_vetoPoints", muon_vetoPoint)
    output_tree.SetBranchAddress("vetoPoint", combined_vetoPoint)

    for input_event, muon_event in zip(input_tree, muon_tree):
        interaction_point = r.TVector3()
        input_event.MCTrack[0].GetStartVertex(interaction_point)

        combined_vetoPoint.Clear()

        index = 0

        for hit in original_vetoPoint:
            if combined_vetoPoint.GetSize() == index:
                combined_vetoPoint.Expand(index + 1)
            combined_vetoPoint[index] = hit  # pending fix to support ROOT 6.32+
            index += 1

        for hit in muon_vetoPoint:
            if hit.GetZ() < interaction_point.Z():
                if combined_vetoPoint.GetSize() == index:
                    combined_vetoPoint.Expand(index + 1)
                combined_vetoPoint[index] = hit  # pending fix to support ROOT 6.32+
                index += 1

        output_tree.Fill()

    # Write the updated tree back to the same file
    input_file.cd()
    output_tree.Write("cbmsim", r.TObject.kOverwrite)
    input_file.Close()
    muon_file.Close()

    print(f"File updated with incoming muon info as {inputfile}")


add_muons = inspect_file(args.inputfile)

if add_muons:
<<<<<<< HEAD
    modify_file()
>>>>>>> 7747b728 (Added MuonDIS directory for updated scripts)
=======
    modify_file(args.inputfile, args.muonfile)
>>>>>>> e494e97a (Avoid listdir for non-directory case)
