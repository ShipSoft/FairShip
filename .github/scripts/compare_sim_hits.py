#!/usr/bin/env python
# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

"""Check that two simulation outputs have the same hits, event by event.

Used to check that a simulation on a geometry loaded from file
(run_simScript.py -g) reproduces the simulation that built the geometry, with
the same seed. Both files must have the same number of events, and every MC
track and every point of every detector must be the same (track, detector ID,
position, momentum, time, energy loss, PDG code).

With --expect-different BRANCH, the events must have the same structure and
the points of BRANCH must differ instead; this checks that a change of the
geometry shows up in the hits.
"""

import argparse
import math
import sys

import ROOT

# Values compared for the tracks and for the points of every detector
TRACK_GETTERS = ("GetPdgCode", "GetMotherId", "GetPx", "GetPy", "GetPz", "GetStartX", "GetStartY", "GetStartZ")
POINT_GETTERS = (
    "GetTrackID",
    "GetDetectorID",
    "PdgCode",
    "GetX",
    "GetY",
    "GetZ",
    "GetPx",
    "GetPy",
    "GetPz",
    "GetTime",
    "GetEnergyLoss",
)


def read_events(path: str) -> list[dict[str, list[tuple]]]:
    """For every event, the values of every MC track and point, by branch."""
    f = ROOT.TFile.Open(path)
    tree = f["cbmsim"]
    branches = sorted(
        b.GetName() for b in tree.GetListOfBranches() if b.GetName() == "MCTrack" or b.GetName().endswith("Point")
    )
    events = []
    for event in tree:
        content = {}
        for branch in branches:
            getters = TRACK_GETTERS if branch == "MCTrack" else POINT_GETTERS
            content[branch] = [tuple(getattr(item, g)() for g in getters) for item in getattr(event, branch)]
        events.append(content)
    f.Close()
    return events


def same_value(a, b) -> bool:
    if isinstance(a, float) or isinstance(b, float):
        return math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-9)
    return a == b


def structure_problem(reference: list, new: list) -> str | None:
    """Why the events of new cannot be compared with those of reference, if they cannot."""
    if not new:
        return "no events in the new file"
    if len(new) != len(reference):
        return f"{len(new)} events in the new file, {len(reference)} in the reference"
    if new[0].keys() != reference[0].keys():
        return f"different branches: {sorted(reference[0].keys() ^ new[0].keys())}"
    return None


def compare(reference: list, new: list, max_report: int = 20) -> list[tuple[str, str]]:
    """(branch, description) of the differences between the events of new and those of reference."""
    differences = []
    for i, (ref_event, new_event) in enumerate(zip(reference, new)):
        for branch, ref_items in ref_event.items():
            new_items = new_event[branch]
            if len(ref_items) != len(new_items):
                differences.append(
                    (branch, f"event {i}, {branch}: {len(ref_items)} in reference, {len(new_items)} in new")
                )
                continue
            for j, (a, b) in enumerate(zip(ref_items, new_items)):
                if not all(same_value(x, y) for x, y in zip(a, b)):
                    differences.append((branch, f"event {i}, {branch}[{j}]: {a} in reference, {b} in new"))
                    break
    for _, line in differences[:max_report]:
        print(line)
    if len(differences) > max_report:
        print(f"... and {len(differences) - max_report} more")
    return differences


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("reference", help="simulation output of the reference run")
    parser.add_argument("new", help="simulation output to compare with it")
    parser.add_argument(
        "--expect-different",
        metavar="BRANCH",
        help="fail unless the events have the same structure and the points of BRANCH differ",
    )
    args = parser.parse_args()

    reference = read_events(args.reference)
    new = read_events(args.new)
    totals = {b: sum(len(event[b]) for event in new) for b in new[0]} if new else {}
    print(f"{args.new}: {len(new)} events, totals {totals}")
    problem = structure_problem(reference, new)
    if problem:
        print(f"ERROR: cannot compare {args.new} with {args.reference}: {problem}")
        return 1
    differences = compare(reference, new)
    if args.expect_different:
        if args.expect_different not in new[0]:
            print(f"ERROR: no branch {args.expect_different} in {args.new}")
            return 1
        if any(branch == args.expect_different for branch, _ in differences):
            print(f"OK: the {args.expect_different} of {args.reference} and {args.new} differ, as expected")
            return 0
        print(f"ERROR: {args.reference} and {args.new} have the same {args.expect_different}, but should differ")
        return 1
    if differences:
        print(f"ERROR: {len(differences)} differences between {args.reference} and {args.new}")
        return 1
    print(f"OK: same hits in all {len(new)} events")
    return 0


if __name__ == "__main__":
    sys.exit(main())
