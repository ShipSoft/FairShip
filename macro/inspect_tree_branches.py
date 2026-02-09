#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration
"""
Inspect TTree branches to find which ones use TObjArray or other unsupported types.

This helps identify branches that would prevent RNTuple conversion.
"""

import argparse
import sys

import ROOT


def inspect_tree_branches(input_file, tree_name):
    """
    Inspect all branches in a TTree and report their types.

    Args:
        input_file: Path to input ROOT file
        tree_name: Name of the TTree to inspect
    """
    print(f"Inspecting TTree: {input_file}:{tree_name}")
    print("=" * 80)
    print()

    with ROOT.TFile.Open(input_file, "READ") as f:
        tree = f.Get(tree_name)
        if not tree:
            print(f"ERROR: Tree '{tree_name}' not found")
            return False

        branches = tree.GetListOfBranches()
        print(f"Found {branches.GetEntries()} branches\n")

        problematic_branches = []

        for i in range(branches.GetEntries()):
            branch = branches.At(i)
            branch_name = branch.GetName()
            class_name = branch.GetClassName()

            is_problematic = False
            reason = ""

            if "TObjArray" in class_name:
                is_problematic = True
                reason = "TObjArray not supported in RNTuple"
            elif "TClonesArray" in class_name:
                is_problematic = True
                reason = "TClonesArray not supported in RNTuple"
            elif class_name and "TObject" in class_name and "std::" not in class_name:
                # Other legacy ROOT types might be problematic
                is_problematic = True
                reason = "Legacy ROOT container"

            status = "⚠️  PROBLEM" if is_problematic else "✓  OK"
            print(f"{status:12} {branch_name:40} {class_name}")

            if is_problematic:
                problematic_branches.append((branch_name, class_name, reason))

        print()
        print("=" * 80)

        if problematic_branches:
            print(f"\n❌ Found {len(problematic_branches)} problematic branch(es):\n")
            for name, cls, reason in problematic_branches:
                print(f"  • {name}")
                print(f"    Type: {cls}")
                print(f"    Issue: {reason}")
                print()

            print("These branches prevent RNTuple conversion.")
            print("Consider migrating to std::vector or other supported types.")
            return False
        else:
            print("\n✓ All branches appear to be RNTuple-compatible!")
            return True


def main():
    """Parse arguments and run the TTree branch inspection."""
    parser = argparse.ArgumentParser(description="Inspect TTree branches for RNTuple compatibility")
    parser.add_argument("-f", "--input-file", required=True, help="Input ROOT file")
    parser.add_argument(
        "-t",
        "--tree-name",
        default="cbmsim",
        help="Name of TTree to inspect (default: cbmsim)",
    )

    args = parser.parse_args()

    success = inspect_tree_branches(args.input_file, args.tree_name)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
