#!/usr/bin/env python
# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

"""Momentum spectrum at a scoring plane with event-level uncertainties, using RDataFrame.

RDataFrame version of split_weight_uncertainties.py, with the same options,
table and output. The selection runs as compiled RDataFrame columns, and the
C++ EventHistogram accumulates with one instance per processing slot, merged
with Add() at the end. That makes it safe to run multithreaded (-j). The
bootstrap replicas depend only on run and event number, so the result does not
depend on the number of threads or the order of events.

    python examples/split_weight_uncertainties_rdf.py -f out/*/pythia8_*.root -o spectrum.root -j 8
"""

import numpy as np
import ROOT
from event_histogram import generated_events
from split_weight_uncertainties import log_edges, make_parser, print_table

ROOT.gSystem.Load("libShipData")
ROOT.gInterpreter.Declare(
    """
#include "EventHistogram.h"

// EventHistogram is not thread safe, so every slot fills its own.
void FillEventHistograms(ROOT::RDF::RNode df, std::vector<EventHistogram*>& slots) {
  df.ForeachSlot(
      [&slots](unsigned slot, const ROOT::RVecD& p, const ROOT::RVecD& w, ULong64_t key) {
        for (std::size_t i = 0; i < p.size(); ++i) slots[slot]->Fill(p[i], w[i]);
        slots[slot]->EndEvent(key);
      },
      {"p", "w", "key"});
}
"""
)


def complete_element_class(df, column):
    """Expressions on the elements of a vector column need their full class, but
    the dictionaries only forward declare it. Looking the class up from Python
    makes Cling parse its header."""
    vector_class = ROOT.TClass.GetClass(df.GetColumnType(column))
    getattr(ROOT, vector_class.GetCollectionProxy().GetValueClass().GetName())


def main():
    ap = make_parser(__doc__.splitlines()[0])
    ap.add_argument("-j", "--threads", type=int, default=1, help="threads, 0 for all cores")
    args = ap.parse_args()
    if args.threads != 1:
        ROOT.EnableImplicitMT(args.threads)
    edges = log_edges(args.bins)

    def per_point(expr, mask=""):
        """expr for each point v of the scoring plane, as an RVec. The lambda has a
        return statement, so RDataFrame takes the string as a function body."""
        return f"return Map({args.branch}, [&](const auto& v) {{ return {expr}; }}){mask};"

    df = ROOT.RDataFrame("cbmsim", ROOT.std.vector["std::string"](args.files))
    for column in (args.branch, "MCTrack"):
        complete_element_class(df, column)
    df = (
        df.Define("sel", per_point(f"{args.pdg} == 0 || std::abs(v.PdgCode()) == {args.pdg}"))
        .Define("p", per_point("std::hypot(v.GetPx(), v.GetPy(), v.GetPz())", "[sel]"))
        .Define("w", per_point("MCTrack[v.GetTrackID()].GetWeight()", "[sel]"))
        .Define("key", "EventHistogram::MakeEventKey(MCEventHeader.fRunId, MCEventHeader.fEventId)")
    )

    title = f"{args.branch};p (GeV/c);per event"
    slots = [
        ROOT.EventHistogram(args.name, title, len(edges) - 1, edges, True, args.replicas) for _ in range(df.GetNSlots())
    ]
    pointers = ROOT.std.vector["EventHistogram*"](slots)
    ROOT.FillEventHistograms(ROOT.RDF.AsRNode(df), pointers)
    h = slots[0]
    for other in slots[1:]:
        h.Add(other)

    n_generated = 0
    for name in args.files:
        f = ROOT.TFile.Open(name)
        n_generated += generated_events(f)
        f.Close()
    h.AddEmptyEvents(n_generated - h.GetNEvents())

    result, naive = h.MakeResult(), h.MakeNaive()
    errors, naive_errors = np.sqrt(result.variances()), np.sqrt(naive.variances())
    print_table(args, n_generated, edges, result.values(), errors, naive_errors, h.MakeNeff().values())

    out = ROOT.TFile(args.output, "RECREATE")
    h.Write(out)
    out.Close()
    print(f"written to {args.output}")


if __name__ == "__main__":
    main()
