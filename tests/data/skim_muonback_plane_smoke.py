#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration
"""Create the run_fixedTarget skim for the ci-sim-muonback-plane smoke test.

Keeps only the events with a muon in PlaneHA from one or more
run_fixedTarget.py outputs (simulated with the hadron absorber field) and
writes them, with the FileSummary of the first input, to
tests/data/muonback_plane_smoke.root. Muons behind the absorber are rare, so
the inputs need a few 10k protons on target in total, e.g.

    python macro/run_fixedTarget.py -n 5000 -e 0.5 -r <run> --AddHadronAbsorberOnly

for a few runs. Re-run only if the output format of run_fixedTarget changes.
"""

import argparse
from pathlib import Path

import ROOT
import shipRoot_conf

shipRoot_conf.configure()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", nargs="+", help="run_fixedTarget.py output files")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).with_name("muonback_plane_smoke.root"),
        help="Output skim file",
    )
    args = parser.parse_args()

    chain = ROOT.TChain("cbmsim")
    for f in args.inputs:
        chain.Add(f)
    with ROOT.TFile.Open(args.inputs[0]) as first:
        summary = str(first.Get("FileSummary"))

    out = ROOT.TFile.Open(str(args.output), "RECREATE")
    skim = chain.CopyTree("Sum$(abs(PlaneHAPoint.fPdgCode) == 13) > 0")
    skim.Write()
    out.WriteObject(ROOT.TString(summary), "FileSummary")
    n = skim.GetEntries()
    out.Close()
    print(f"Wrote {n} events to {args.output} ({args.output.stat().st_size} B)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
