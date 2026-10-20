#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration
"""Check that MuonBack continues run_fixedTarget muons from the scoring plane.

Compares a stage-2 output of run_simScript.py --MuonBack with its stage-1 input
(run_fixedTarget.py). Every tracked plane copy (procID kPTransportation) has to
start where a muon of the input entered PlaneHA, with the same momentum, time
and weight, and its mother has to be the untracked origin entry of that muon.
The start points also have to lie outside dense material in the stage-2
geometry. Stage 2 drops events without hits, so copies are matched against the
hits of the whole input rather than event by event.

With --from-origin the stage-2 output comes from --MuonBackFromOrigin instead:
there must be no plane copies, and the scored muons have to start again at
their production vertex with their production momentum.
"""

import argparse
import sys

import ROOT
import shipRoot_conf

shipRoot_conf.configure()

TOL = 1e-4  # relative, for the float storage of the hits


def close(a, b, tol=TOL):
    return all(abs(x - y) <= tol * max(1.0, abs(y)) for x, y in zip(a, b))


def input_muons(tree):
    """The muons MuonBack starts: the first PlaneHA hit of each muon track."""
    muons = []
    for ev in tree:
        seen = set()
        for h in ev.PlaneHAPoint:
            i = h.GetTrackID()
            if abs(h.PdgCode()) != 13 or i in seen:
                continue
            seen.add(i)
            trk = ev.MCTrack[i]
            muons.append(
                {
                    "pdg": h.PdgCode(),
                    "pos": (h.GetX(), h.GetY(), h.GetZ()),
                    "mom": (h.GetPx(), h.GetPy(), h.GetPz()),
                    "time": h.GetTime(),
                    "weight": trk.GetWeight(),
                    "origin": (trk.GetStartX(), trk.GetStartY(), trk.GetStartZ()),
                    "origin_mom": (trk.GetPx(), trk.GetPy(), trk.GetPz()),
                }
            )
    return muons


def check_from_origin(muons, tree) -> int:
    """Every scored muon starts at its production vertex, and nothing at the plane."""
    failures = []
    nmatched = 0
    for n, ev in enumerate(tree):
        for j, trk in enumerate(ev.MCTrack):
            if trk.GetProcID() == ROOT.kPTransportation:
                failures.append(f"event {n}, track {j}: plane copy in a from-origin replay")
                continue
            start = (trk.GetStartX(), trk.GetStartY(), trk.GetStartZ())
            mom = (trk.GetPx(), trk.GetPy(), trk.GetPz())
            if any(
                m["pdg"] == trk.GetPdgCode() and close(start, m["origin"]) and close(mom, m["origin_mom"])
                for m in muons
            ):
                nmatched += 1
    print(f"found {nmatched} of {len(muons)} input muons at their production vertex")
    for msg in failures[:20]:
        print("FAIL:", msg)
    if failures:
        print(f"{len(failures)} failures")
        return 1
    if nmatched == 0:
        print("FAIL: no input muon starts at its production vertex")
        return 1
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("stage1", help="run_fixedTarget.py output")
    ap.add_argument("stage2", help="run_simScript.py --MuonBack output (sim_*.root)")
    ap.add_argument("--geo", help="stage-2 geometry file (geo_*.root)")
    ap.add_argument("--max-density", type=float, default=0.01, help="densest material allowed at a start [g/cm3]")
    ap.add_argument("--from-origin", action="store_true", help="stage 2 ran with --MuonBackFromOrigin")
    args = ap.parse_args()

    f1 = ROOT.TFile.Open(args.stage1)
    muons = input_muons(f1["cbmsim"])
    f2 = ROOT.TFile.Open(args.stage2)
    if args.from_origin:
        return check_from_origin(muons, f2["cbmsim"])
    nav = None
    if args.geo:
        ROOT.TGeoManager.Import(args.geo)
        nav = ROOT.gGeoManager.GetCurrentNavigator()

    failures = []
    ncopies = 0
    for n, ev in enumerate(f2["cbmsim"]):
        tracks = ev.MCTrack
        for j, trk in enumerate(tracks):
            if trk.GetProcID() != ROOT.kPTransportation:
                continue
            ncopies += 1
            where = f"event {n}, track {j}"
            start = (trk.GetStartX(), trk.GetStartY(), trk.GetStartZ())
            mom = (trk.GetPx(), trk.GetPy(), trk.GetPz())
            match = [
                m
                for m in muons
                if m["pdg"] == trk.GetPdgCode()
                and close(start, m["pos"])
                and close(mom, m["mom"])
                and close((trk.GetStartT(),), (m["time"],))
                and close((trk.GetWeight(),), (m["weight"],))
            ]
            if not match:
                failures.append(f"{where}: no input hit at {start} with p = {mom}")
                continue
            mother = trk.GetMotherId()
            if mother < 0:
                failures.append(f"{where}: plane copy without origin entry")
                continue
            origin = tracks[mother]
            ostart = (origin.GetStartX(), origin.GetStartY(), origin.GetStartZ())
            if origin.GetPdgCode() != trk.GetPdgCode() or not close(ostart, match[0]["origin"]):
                failures.append(f"{where}: mother {mother} is not the origin entry")
            if nav:
                node = nav.FindNode(*start)
                material = node.GetVolume().GetMaterial()
                if material.GetDensity() > args.max_density:
                    failures.append(
                        f"{where}: starts in {node.GetName()} ({material.GetName()}, {material.GetDensity():.3g} g/cm3)"
                    )

    print(f"checked {ncopies} plane copies against {len(muons)} input muons")
    for msg in failures[:20]:
        print("FAIL:", msg)
    if failures:
        print(f"{len(failures)} failures")
        return 1
    if ncopies == 0:
        print("FAIL: no plane copies found")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
