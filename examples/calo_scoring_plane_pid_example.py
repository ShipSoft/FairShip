#!/usr/bin/env python
# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration
"""Apply CaloScoringPlanePID to the CaloScoringPlanePoints of a simulation file.

python examples/calo_scoring_plane_pid_example.py -f sim.root -p $FAIRSHIP/geometry/caloScoringPlane_pid_provided.yaml
"""

import argparse
from collections import Counter

import ROOT

parser = argparse.ArgumentParser()
parser.add_argument("-f", "--sim", required=True, help="simulation file")
parser.add_argument("-p", "--pid", default="", help="PID YAML file (default: perfect PID)")
args = parser.parse_args()

pid = ROOT.CaloScoringPlanePID(args.pid) if args.pid else ROOT.CaloScoringPlanePID()
pid.Print()

tree = ROOT.TFile.Open(args.sim)["cbmsim"]
table = Counter()  # (true species, identified species) -> count
for event in tree:
    for point in event.CaloScoringPlanePoint:
        true_species = pid.TrueSpecies(point.PdgCode())
        table[(true_species, pid.Identify(point))] += 1

name = ROOT.CaloScoringPlanePID.SpeciesName
print("true -> identified: count")
for (t, r), n in sorted(table.items()):
    print(f"  {name(t):>8} -> {name(r):<8}: {n}")
