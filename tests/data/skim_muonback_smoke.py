#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration
"""Create a tiny pythia8-Geant4 muon-back skim for the ci-sim-muonback smoke test.

Reads the full muon-back background sample (via xrootd with a Kerberos token,
or the public HTTPS link), copies the first N entries of the pythia8-Geant4
TTree into tests/data/muonback_smoke.root, and exits. Re-run only if the
sample format changes.
"""

import argparse
from pathlib import Path

import ROOT
import shipRoot_conf

shipRoot_conf.configure()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        help="Input file (HTTPS public link or root:// URL)",
        required=True,
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).with_name("muonback_smoke.root"),
        help="Output skim file",
    )
    parser.add_argument(
        "--entries",
        type=int,
        default=200,
        help="Number of entries to copy from the pythia8-Geant4 tree",
    )
    args = parser.parse_args()

    src = ROOT.TFile.Open(args.source, "READ")
    tree = src.Get("pythia8-Geant4") or src.Get("cbmsim")
    if not tree:
        raise SystemExit("Neither pythia8-Geant4 nor cbmsim tree found in source")

    out = ROOT.TFile.Open(str(args.output), "RECREATE")
    skim = tree.CopyTree("", "", args.entries, 0)
    skim.Write()
    out.Close()
    src.Close()
    print(f"Wrote {args.entries} entries to {args.output} ({args.output.stat().st_size} B)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
