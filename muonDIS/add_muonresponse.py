#!/usr/bin/env python
"""Script to add the incoming muon's MC hits in the SBT to the simulation file."""

import argparse
import logging

import ROOT as r

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

    input_file.cd()
    output_tree = input_tree.CloneTree(
        0
    )  # Clone the structure of the existing tree, but do not copy the entries

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
    modify_file(args.inputfile, args.muonfile)
