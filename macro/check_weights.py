#!/usr/bin/env python
"""Check which MCTrack carries the per-spill weight."""

import sys

import ROOT

f = ROOT.TFile.Open(sys.argv[1] if len(sys.argv) > 1 else "concat.root")
tree = f.Get("cbmsim")
n = min(20, tree.GetEntries())

print(f"Checking first {n} events")
print(f"  {'event':>6s} {'w_track0':>10s} {'w_first_mu':>10s} {'mu_idx':>8s} {'w_max':>10s} {'max_idx':>8s}")

for i in range(n):
    tree.GetEntry(i)
    tracks = tree.MCTrack

    w0 = tracks[0].GetWeight() if len(tracks) > 0 else 0

    w_mu, mu_idx = -1.0, -1
    w_max, max_idx = 0.0, -1
    for j in range(len(tracks)):
        w = tracks[j].GetWeight()
        if w > w_max:
            w_max = w
            max_idx = j
        if mu_idx < 0 and abs(tracks[j].GetPdgCode()) == 13:
            mu_idx = j
            w_mu = w

    print(f"  {i:6d} {w0:10.2f} {w_mu:10.2f} {mu_idx:8d} {w_max:10.2f} {max_idx:8d}")

f.Close()
