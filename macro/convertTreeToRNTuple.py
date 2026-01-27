#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration
"""
Convert TTree to RNTuple using ROOT's RNTupleImporter.

This script imports TTrees from ROOT files and converts them to RNTuple format,
which provides better compression, faster I/O, and modern columnar storage.

Usage:
    python convertTreeToRNTuple.py -f input.root -t cbmsim -o output.root -n fairdata
    python convertTreeToRNTuple.py -f input.root  # Uses default tree/ntuple names

Note:
    RNTuple has some limitations compared to TTree:
    - TObjArray and other legacy ROOT containers cannot be stored natively
    - Use std::vector instead of TObjArray for RNTuple compatibility
    - TClonesArray is also not supported; migrate to std::vector
"""

import argparse
import sys

import ROOT


def convert_tree_to_rntuple(input_file, tree_name, output_file, ntuple_name):
    """
    Convert a TTree to RNTuple format.

    Args:
        input_file: Path to input ROOT file containing TTree
        tree_name: Name of the TTree to convert
        output_file: Path to output ROOT file for RNTuple
        ntuple_name: Name for the output RNTuple
    """
    print("Converting TTree → RNTuple")
    print(f"  Input:  {input_file}:{tree_name}")
    print(f"  Output: {output_file}:{ntuple_name}")
    print()

    with ROOT.TFile.Open(input_file, "READ") as input_root_file:
        tree = input_root_file.Get(tree_name)
        if not tree:
            print(f"ERROR: Tree '{tree_name}' not found in {input_file}")
            print("Available trees:")
            for key in input_root_file.GetListOfKeys():
                obj = key.ReadObj()
                if obj.InheritsFrom("TTree"):
                    print(f"  - {key.GetName()}")
            return False

        num_entries = tree.GetEntries()
        print(f"Found TTree '{tree_name}' with {num_entries} entries")
        print()

    # Convert using RNTupleImporter
    try:
        importer = ROOT.ROOT.Experimental.RNTupleImporter.Create(input_file, tree_name, output_file)

        if not importer:
            print("ERROR: Failed to create RNTupleImporter")
            return False

        # Set the RNTuple name (defaults to tree name if not set)
        importer.SetNTupleName(ntuple_name)

        # Optional: Configure import options
        # importer.SetMaxUnzippedPageSize(...)  # Adjust page size if needed
        # importer.SetCompressionSettings(...)  # Adjust compression (default: zstd)

        print("Starting conversion...")
        importer.Import()  # Import() throws exception on failure

        print("✓ Conversion complete!")
        print()

        # Verify output
        with ROOT.TFile.Open(output_file, "READ"):
            reader = ROOT.ROOT.RNTupleReader.Open(ntuple_name, output_file)
            num_rntuple_entries = reader.GetNEntries()

            print("Verification:")
            print(f"  TTree entries:   {num_entries}")
            print(f"  RNTuple entries: {num_rntuple_entries}")

            if num_entries == num_rntuple_entries:
                print("  ✓ Entry count matches")
            else:
                print("  ✗ WARNING: Entry count mismatch!")

        return True

    except Exception as e:
        print(f"ERROR: Exception during conversion: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Parse arguments and run the TTree to RNTuple conversion."""
    parser = argparse.ArgumentParser(
        description="Convert TTree to RNTuple using ROOT's RNTupleImporter",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert cbmsim tree to fairdata RNTuple
  %(prog)s -f ship.conical.Pythia8-TGeant4.root -t cbmsim -o output.root -n fairdata

  # Use defaults (cbmsim → fairdata)
  %(prog)s -f ship.conical.Pythia8-TGeant4.root

  # Convert custom tree
  %(prog)s -f mydata.root -t mytree -o converted.root -n myntuple
        """,
    )

    parser.add_argument("-f", "--input-file", required=True, help="Input ROOT file containing TTree")
    parser.add_argument(
        "-t",
        "--tree-name",
        default="cbmsim",
        help="Name of TTree to convert (default: cbmsim)",
    )
    parser.add_argument(
        "-o",
        "--output-file",
        default=None,
        help="Output ROOT file for RNTuple (default: <input>_rntuple.root)",
    )
    parser.add_argument(
        "-n",
        "--ntuple-name",
        default="fairdata",
        help="Name for output RNTuple (default: fairdata)",
    )

    args = parser.parse_args()

    if args.output_file is None:
        if args.input_file.endswith(".root"):
            args.output_file = args.input_file.replace(".root", "_rntuple.root")
        else:
            args.output_file = args.input_file + "_rntuple.root"

    success = convert_tree_to_rntuple(args.input_file, args.tree_name, args.output_file, args.ntuple_name)

    if success:
        print()
        print("Success! RNTuple file created:")
        print(f"  {args.output_file}")
        return 0
    else:
        print()
        print("Conversion failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
