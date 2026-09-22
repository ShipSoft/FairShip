#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-3.0-or-later
"""Check the weights written by a data-driven J/psi run.

Every muon whose mother is the truth-level J/psi must carry exactly the event
weight reported by JpsiGenerator. The expected weight is read from the
FileSummary that run_simScript.py writes into the output (--JpsiData), or from
the JSON side file that run_fixedTarget.py writes (--jpsi-data):

    python check_jpsi_weights.py sim_jpsi_test.root
    python check_jpsi_weights.py pythia8_Geant4_1_0.5.root --metadata jpsi_generator_metadata.json

run_fixedTarget.py with --kaon-pion-splits 1 is the configuration that switches
on ShipStack splitting, i.e. the w -> w^2 regression test.
"""

import argparse
import json
import sys

import ROOT

ap = argparse.ArgumentParser()
ap.add_argument("simfile")
ap.add_argument("--metadata", default=None, help="jpsi_generator_metadata.json (run_fixedTarget.py only)")
ap.add_argument("--tolerance", type=float, default=1e-9)
args = ap.parse_args()

f = ROOT.TFile.Open(args.simfile)
if args.metadata:
    expected = json.load(open(args.metadata))["weight"]
else:
    summary = f.Get("FileSummary")
    if not summary:
        sys.exit("no FileSummary in the file and no --metadata given")
    expected = json.loads(str(summary))["JpsiGenerator"]["weight"]
tree = f.Get("cbmsim")

n_mu, n_bad, n_jpsi = 0, 0, 0
worst = 0.0
for event in tree:
    tracks = event.MCTrack
    for i in range(tracks.GetEntriesFast()):
        t = tracks[i]
        pdg = t.GetPdgCode()
        if pdg == 443 and t.GetMotherId() < 0:
            n_jpsi += 1
            continue
        if abs(pdg) != 13:
            continue
        mother = t.GetMotherId()
        if mother < 0 or tracks[mother].GetPdgCode() != 443:
            continue  # secondary muons, e.g. from pair production, are not checked
        n_mu += 1
        rel = abs(t.GetWeight() / expected - 1.0)
        worst = max(worst, rel)
        if rel > args.tolerance:
            n_bad += 1

print(f"J/psi mothers: {n_jpsi}, J/psi muons: {n_mu}, expected weight {expected:.6g}")
print(f"worst relative deviation {worst:.3g}, muons outside tolerance: {n_bad}")
if n_mu == 0:
    print("no J/psi muons found: check the output mode and the file")
    sys.exit(2)
sys.exit(1 if n_bad else 0)
