#!/usr/bin/env python
# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

"""Momentum spectrum at a scoring plane with event-level uncertainties.

Example for weighted samples with split branches, e.g. run_fixedTarget.py with
--kaon-pion-splits: the clones of one decay are correlated, so the error of a
bin has to come from the spread of per-event weight sums rather than from
sqrt(sum w^2) over hits. The table compares both and lists the effective number
of independent events per bin; below about 20 the error itself is unreliable.

    python examples/split_weight_uncertainties.py -f out/*/pythia8_*.root -o spectrum.root

The output holds only the accumulator, so outputs of several jobs can be merged
with hadd. Get the per-event spectrum from the (merged) file with
EventHistogram.from_root(f, name).values() and .errors(), or in C++ with
EventHistogram::Read(f, name)->MakeResult().

split_weight_uncertainties_rdf.py does the same with RDataFrame and the C++
class, also multithreaded.
"""

import argparse
import math

import numpy as np
import ROOT
from event_histogram import EventHistogram, generated_events, make_event_key


def make_parser(description):
    """Options shared with split_weight_uncertainties_rdf.py."""
    ap = argparse.ArgumentParser(description=description)
    ap.add_argument("-f", "--files", nargs="+", required=True, help="simulation output files")
    ap.add_argument("-o", "--output", default="split_weight_uncertainties.root")
    ap.add_argument("--branch", default="PlaneHAPoint", help="point branch of the scoring plane")
    ap.add_argument("--pdg", type=int, default=13, help="|PDG code| to select, 0 for all")
    ap.add_argument("--bins", default="5,400,20", help="log-spaced momentum bins: low,high,n (GeV/c)")
    ap.add_argument("--replicas", type=int, default=0, help="bootstrap replicas (0 = none)")
    ap.add_argument("--name", default="p_plane")
    return ap


def log_edges(spec):
    low, high, n = spec.split(",")
    return np.geomspace(float(low), float(high), int(n) + 1)


def print_table(args, n_generated, edges, values, errors, naive, n_eff):
    print(f"{n_generated} generated events, {args.branch}, |pdg| = {args.pdg or 'all'}")
    print(f"{'p (GeV/c)':>15} {'per event':>11} {'error':>10} {'sqrt(Σw²)':>10} {'ratio':>6} {'n_eff':>7}")
    for b in range(len(values)):
        if values[b] == 0 and errors[b] == 0:
            continue
        ratio = errors[b] / naive[b] if naive[b] > 0 else float("nan")
        flag = "  <- unreliable" if n_eff[b] < 20 else ""
        print(
            f"{edges[b]:7.1f}–{edges[b + 1]:<7.1f} {values[b]:11.4e} {errors[b]:10.3e} {naive[b]:10.3e}"
            f" {ratio:6.1f} {n_eff[b]:7.1f}{flag}"
        )


def main():
    args = make_parser(__doc__.splitlines()[0]).parse_args()
    edges = log_edges(args.bins)
    h = EventHistogram(
        args.name, edges, title=f"{args.branch};p (GeV/c);per event", covariance=True, n_replicas=args.replicas
    )

    n_generated = 0
    for name in args.files:
        f = ROOT.TFile.Open(name)
        n_generated += generated_events(f)
        tree = f.Get("cbmsim")
        tree.SetBranchStatus("*", 0)
        for branch in ("MCEventHeader", "MCTrack", args.branch):
            tree.SetBranchStatus(f"{branch}*", 1)
        for event in tree:
            header = event.MCEventHeader
            tracks = event.MCTrack
            momenta, weights = [], []
            for point in getattr(event, args.branch):
                if args.pdg and abs(point.PdgCode()) != args.pdg:
                    continue
                momenta.append(math.hypot(point.GetPx(), point.GetPy(), point.GetPz()))
                weights.append(tracks[point.GetTrackID()].GetWeight())
            h.fill(momenta, weights)
            h.end_event(make_event_key(header.GetRunID(), header.GetEventID()))
        f.Close()
    h.add_empty_events(n_generated - h.n_events)

    print_table(args, n_generated, edges, h.values(), h.errors(), h.naive_errors(), h.n_eff())

    out = ROOT.TFile(args.output, "RECREATE")
    h.to_root(out)
    out.Close()
    print(f"written to {args.output}")


if __name__ == "__main__":
    main()
