#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

"""Run a full tracking benchmark: simulation -> reconstruction -> metrics.

Fires a particle gun upstream of the straw tube spectrometer (T1-T4),
runs digitisation and reconstruction with template matching pattern
recognition, then computes tracking performance metrics.

Each phase (sim, reco) runs as a subprocess because FairRoot singletons
prevent creating multiple FairRunSim instances in the same process.

Example usage:
    python macro/run_tracking_benchmark.py -n 200 --seed 42 --tag test
    python macro/run_tracking_benchmark.py -n 1000 --nTracks 5 --tag multi
"""

from __future__ import annotations

import os
import subprocess
import sys
from argparse import ArgumentParser

parser = ArgumentParser(description="Tracking performance benchmark for straw tube spectrometer")
parser.add_argument("-n", "--nEvents", type=int, default=1000, help="Number of events (default: 1000)")
parser.add_argument("--pID", type=int, default=13, help="Particle PDG ID (default: 13, mu-)")
parser.add_argument("--Estart", type=float, default=1.0, help="Start of energy range in GeV (default: 1)")
parser.add_argument("--Eend", type=float, default=100.0, help="End of energy range in GeV (default: 100)")
parser.add_argument("--Vz", type=float, default=8300.0, help="Gun z-position in cm (default: 8300, ~1m upstream of T1)")
parser.add_argument("--Dx", type=float, default=200.0, help="Position spread in x [cm] (default: 200)")
parser.add_argument("--Dy", type=float, default=300.0, help="Position spread in y [cm] (default: 300)")
parser.add_argument("--nTracks", type=int, default=1, help="Tracks per event (default: 1)")
parser.add_argument("--tag", default="benchmark", help="Output file tag (default: benchmark)")
parser.add_argument("--output-json", default=None, help="JSON metrics output path")
parser.add_argument("--seed", type=int, default=42, help="Random seed (default: 42)")
parser.add_argument("-o", "--outputDir", default=".", help="Output directory (default: .)")
parser.add_argument(
    "--debug",
    type=int,
    default=0,
    choices=range(0, 4),
    help="FairLogger verbosity: 0=info, 1=debug, 2=debug1, 3=debug2",
)

options = parser.parse_args()

if not os.path.exists(options.outputDir):
    os.makedirs(options.outputDir)

tag = options.tag
sim_file = f"{options.outputDir}/sim_{tag}.root"
geo_file = f"{options.outputDir}/geo_{tag}.root"
reco_file = f"{options.outputDir}/sim_{tag}_rec.root"
json_file = options.output_json or f"{options.outputDir}/tracking_metrics.json"
histo_file = f"{options.outputDir}/tracking_benchmark_histos.root"

fairship = os.environ.get("FAIRSHIP", "")


def run_phase(description: str, cmd: list[str]) -> None:
    """Run a subprocess phase, raising on failure."""
    print("=" * 60)
    print(f"{description}")
    print("=" * 60)
    result = subprocess.run(cmd, check=False)
    if result.returncode != 0:
        print(f"FAILED: {description} (exit code {result.returncode})")
        sys.exit(result.returncode)


# ============================================================
# Phase 1: Simulation via run_simScript.py
# ============================================================
sim_script = os.path.join(fairship, "macro", "run_simScript.py") if fairship else "macro/run_simScript.py"
sim_cmd = [
    sys.executable,
    sim_script,
    "-n",
    str(options.nEvents),
    "-s",
    str(options.seed),
    "--debug",
    str(options.debug),
    "--vacuums",
    "--SND",
    "--SND_design",
    "2",
    "--shieldName",
    "TRY_2025",
    "--tag",
    tag,
    "-o",
    options.outputDir,
    "PG",
    "--pID",
    str(options.pID),
    "--Estart",
    str(options.Estart),
    "--Eend",
    str(options.Eend),
    "--Vz",
    str(options.Vz),
    "--multiplePG",
    "--Dx",
    str(options.Dx),
    "--Dy",
    str(options.Dy),
]

run_phase("Phase 1: Simulation", sim_cmd)

if not os.path.exists(sim_file):
    print(f"ERROR: Simulation output {sim_file} not found")
    sys.exit(1)

# ============================================================
# Phase 2: Reconstruction via ShipReco.py
# ============================================================
reco_script = os.path.join(fairship, "macro", "ShipReco.py") if fairship else "macro/ShipReco.py"
reco_cmd = [
    sys.executable,
    reco_script,
    "-f",
    sim_file,
    "-g",
    geo_file,
    "-n",
    str(options.nEvents),
    "--patRec",
    "AR",
]
if options.debug > 0:
    reco_cmd.append("--Debug")

run_phase("Phase 2: Reconstruction", reco_cmd)

if not os.path.exists(reco_file):
    print(f"ERROR: Reconstruction output {reco_file} not found")
    sys.exit(1)

# ============================================================
# Phase 3: Metrics (runs in this process — no FairRunSim needed)
# ============================================================
print("=" * 60)
print("Phase 3: Benchmark Metrics")
print("=" * 60)

import tracking_benchmark

bench = tracking_benchmark.TrackingBenchmark(sim_file, reco_file, geo_file)
bench.compute_metrics()
bench.print_summary()
bench.save_json(json_file)
bench.save_histograms(histo_file)

print("=" * 60)
print("Tracking benchmark complete.")
print(f"  Metrics:    {json_file}")
print(f"  Histograms: {histo_file}")
print("=" * 60)
