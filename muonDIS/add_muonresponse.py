#!/usr/bin/env python
"""Script to add the incoming muon's MC hits in the SBT to the simulation file."""

import argparse
import logging
import os

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


def read_file():
    """Inspecting the produced file for successfully added muon veto points."""
    inputFile = r.TFile.Open(args.inputfile, "READ")
    input_tree = inputFile.cbmsim
    input_tree.GetEntry(0)

    muons = False
    for hit in input_tree.vetoPoint:
        if hit.GetTrackID() == 0:
            muons = True
    inputFile.Close()

    if muons:
        print("File is already updated with incoming muon info. Nothing to do.")
        return False
    else:
        print(
            "Incoming muon's vetopoint info missing in file, proceeding with modification"
        )
        return True


def modify_file():
    """Modify the input file with muon info."""
    if args.inputfile[0:4] == "/eos":
        args.inputfile = os.environ["EOSSHIP"] + args.inputfile

    logging.warning(f"{args.inputfile} opened for modification")

    inputFile = r.TFile.Open(args.inputfile, "UPDATE")
    try:
        input_tree = inputFile.cbmsim
    except Exception as e:
        print(f"Error: {e}")
        inputFile.Close()
        exit(1)

    # Open the external file with additional vetoPoints
    muonFile = r.TFile.Open(args.muonfile, "READ")
    try:
        muon_tree = muonFile.DIS
    except Exception as e:
        print(f"Error: {e}")
        muonFile.Close()
        exit(1)

    inputFile.cd()
    output_tree = input_tree.CloneTree(
        0
    )  # Clone the structure of the existing tree, but do not copy the entries

    # Access the vetoPoint branch in the original and external trees
    originalVetoPoints = r.TClonesArray("vetoPoint")
    muonVetoPoints = r.TClonesArray("vetoPoint")
    combinedVetoPoints = r.TClonesArray("vetoPoint")

    input_tree.SetBranchAddress("vetoPoint", originalVetoPoints)
    muon_tree.SetBranchAddress("muon_vetoPoints", muonVetoPoints)
    output_tree.SetBranchAddress("vetoPoint", combinedVetoPoints)

    for input_event, muon_event in zip(input_tree, muon_tree):
        interaction_point = r.TVector3()
        input_event.MCTrack[0].GetStartVertex(interaction_point)

        combinedVetoPoints.Clear()

        index = 0

        for hit in originalVetoPoints:
            if combinedVetoPoints.GetSize() == index:
                combinedVetoPoints.Expand(index + 1)
            combinedVetoPoints[index] = hit
            index += 1

        for hit in muonVetoPoints:
            if hit.GetZ() < interaction_point.Z():
                if combinedVetoPoints.GetSize() == index:
                    combinedVetoPoints.Expand(index + 1)
                combinedVetoPoints[index] = hit
                index += 1

        output_tree.Fill()

    # Write the updated tree back to the same file
    inputFile.cd()
    output_tree.Write("cbmsim", r.TObject.kOverwrite)
    inputFile.Close()
    muonFile.Close()

    print(f"File updated with incoming muon info as {args.inputfile}")


add_muons = read_file()

if add_muons:
    modify_file()
