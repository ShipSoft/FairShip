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

The output holds the accumulator (hadd-mergeable, readable with
EventHistogram.from_root or the C++ EventHistogram::Read) and the per-event
spectrum <name>_result with event-level errors.
"""

import argparse

import numpy as np
import ROOT
from event_histogram import EventHistogram, generated_events, make_event_key


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("-f", "--files", nargs="+", required=True, help="simulation output files")
    ap.add_argument("-o", "--output", default="split_weight_uncertainties.root")
    ap.add_argument("--branch", default="PlaneHAPoint", help="point branch of the scoring plane")
    ap.add_argument("--pdg", type=int, default=13, help="|PDG code| to select, 0 for all")
    ap.add_argument("--bins", default="5,400,20", help="log-spaced momentum bins: low,high,n (GeV/c)")
    ap.add_argument("--replicas", type=int, default=0, help="bootstrap replicas (0 = none)")
    ap.add_argument("--name", default="p_plane")
    args = ap.parse_args()

    low, high, n = args.bins.split(",")
    edges = np.geomspace(float(low), float(high), int(n) + 1)
    h = EventHistogram(
        args.name, edges, title=f"{args.branch};p (GeV/c);per event", covariance=True, n_replicas=args.replicas
    )

    n_generated = 0
    for name in args.files:
        f = ROOT.TFile.Open(name)
        n_generated += generated_events(f)
        for event in f.Get("cbmsim"):
            header = event.MCEventHeader
            tracks = event.MCTrack
            momenta, weights = [], []
            for point in getattr(event, args.branch):
                if args.pdg and abs(point.PdgCode()) != args.pdg:
                    continue
                momenta.append(np.sqrt(point.GetPx() ** 2 + point.GetPy() ** 2 + point.GetPz() ** 2))
                weights.append(tracks[point.GetTrackID()].GetWeight())
            h.fill(momenta, weights)
            h.end_event(make_event_key(header.GetRunID(), header.GetEventID()))
        f.Close()
    h.add_empty_events(n_generated - h.n_events)

    values, errors, naive, n_eff = h.values(), h.errors(), h.naive_errors(), h.n_eff()
    print(f"{n_generated} generated events, {args.branch}, |pdg| = {args.pdg or 'all'}")
    print(f"{'p (GeV/c)':>15} {'per event':>11} {'error':>10} {'sqrt(Σw²)':>10} {'ratio':>6} {'n_eff':>7}")
    for b in range(len(values)):
        if values[b] == 0:
            continue
        ratio = errors[b] / naive[b] if naive[b] > 0 else float("nan")
        flag = "  <- unreliable" if n_eff[b] < 20 else ""
        print(
            f"{edges[b]:7.1f}–{edges[b + 1]:<7.1f} {values[b]:11.4e} {errors[b]:10.3e} {naive[b]:10.3e}"
            f" {ratio:6.1f} {n_eff[b]:7.1f}{flag}"
        )

    out = ROOT.TFile(args.output, "RECREATE")
    h.to_root(out)
    result = ROOT.TH1D(args.name + "_result", h.title, len(values), edges)
    for b in range(len(values)):
        result.SetBinContent(b + 1, values[b])
        result.SetBinError(b + 1, errors[b])
    out.WriteTObject(result)
    out.Close()
    print(f"written to {args.output}")


if __name__ == "__main__":
    main()
