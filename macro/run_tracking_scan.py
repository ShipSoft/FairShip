#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

"""Scan tracking benchmark over a grid of polar angles and multiplicities.

Calls run_tracking_benchmark.py for each (theta, nTracks) point, collects
metrics into a combined JSON, and produces summary plots with matplotlib.

Example usage:
    # 1D theta scan at single-track multiplicity
    python macro/run_tracking_scan.py -n 200 --scan-mode theta

    # 1D multiplicity scan at theta=0
    python macro/run_tracking_scan.py -n 200 --scan-mode nTracks

    # Full 2D grid
    python macro/run_tracking_scan.py -n 500 --scan-mode grid

    # Custom theta values, keep intermediate files
    python macro/run_tracking_scan.py -n 200 --thetas 0,5,15,30 --keep-files
"""

from __future__ import annotations

import glob
import json
import os
import subprocess
import sys
from argparse import ArgumentParser
from collections import defaultdict

parser = ArgumentParser(description="Scan tracking benchmark over angle and multiplicity")
parser.add_argument("-n", "--nEvents", type=int, default=500, help="Events per scan point (default: 500)")
parser.add_argument(
    "--thetas",
    default="0,1,2,3,5,7,10,15,20,30",
    help="Comma-separated fixed theta values in degrees (default: 0,1,2,3,5,7,10,15,20,30)",
)
parser.add_argument(
    "--nTracksList",
    default="1,2,5,10,20",
    help="Comma-separated multiplicities (default: 1,2,5,10,20)",
)
parser.add_argument(
    "--scan-mode",
    choices=["theta", "nTracks", "grid"],
    default="grid",
    help="Scan mode: theta (fixed theta per point), nTracks (vary multiplicity at thetaRange), grid (full 2D)",
)
parser.add_argument(
    "--thetaRange",
    default=None,
    help="Theta range 'min,max' in degrees for nTracks scan mode (default: 0,10). "
    "Tracks are generated uniformly in this range. Ignored in theta scan mode.",
)
parser.add_argument("--pID", type=int, default=13, help="Particle PDG ID (default: 13, mu-)")
parser.add_argument("--Estart", type=float, default=1.0, help="Start of energy range in GeV (default: 1)")
parser.add_argument("--Eend", type=float, default=100.0, help="End of energy range in GeV (default: 100)")
parser.add_argument("--seed", type=int, default=42, help="Base random seed (default: 42)")
parser.add_argument("-o", "--outputDir", default="./scan_results", help="Base output directory")
parser.add_argument("--mixCharges", action="store_true", help="Generate equal mix of particle and antiparticle")
parser.add_argument("--keep-files", action="store_true", help="Keep intermediate sim/reco ROOT files")
parser.add_argument(
    "--debug",
    type=int,
    default=0,
    choices=range(0, 4),
    help="FairLogger verbosity: 0=info, 1=debug, 2=debug1, 3=debug2",
)

options = parser.parse_args()

thetas = [float(x) for x in options.thetas.split(",")]
n_tracks_list = [int(x) for x in options.nTracksList.split(",")]

# Parse theta range for nTracks mode
if options.thetaRange:
    tr_min, tr_max = (float(x) for x in options.thetaRange.split(","))
else:
    tr_min, tr_max = 0.0, 10.0

# Build scan grid: each point is (thetaMin, thetaMax, nTracks, label_theta)
# In theta mode: fixed theta per point (thetaMin == thetaMax)
# In nTracks mode: uniform theta range, vary multiplicity
# In grid mode: fixed theta per point, vary both
if options.scan_mode == "theta":
    scan_points = [(t, t, 1, t) for t in thetas]
elif options.scan_mode == "nTracks":
    scan_points = [(tr_min, tr_max, n, f"{tr_min}-{tr_max}") for n in n_tracks_list]
else:  # grid
    scan_points = [(t, t, n, t) for t in thetas for n in n_tracks_list]

os.makedirs(options.outputDir, exist_ok=True)

# Gun position spread [cm]; single source of truth passed to the benchmark below.
GUN_DX = 200.0
GUN_DY = 300.0
GUN_AREA_M2 = GUN_DX * GUN_DY * 1e-4

fairship = os.environ.get("FAIRSHIP", "")
benchmark_script = (
    os.path.join(fairship, "macro", "run_tracking_benchmark.py") if fairship else "macro/run_tracking_benchmark.py"
)

all_results: list[dict] = []
n_total = len(scan_points)

for i, (theta_min, theta_max, n_tracks, label_theta) in enumerate(scan_points):
    tag = f"scan_theta{label_theta}_nTr{n_tracks}"
    point_dir = os.path.join(options.outputDir, tag)
    json_path = os.path.join(point_dir, "tracking_metrics.json")
    histo_path = os.path.join(point_dir, "tracking_benchmark_histos.root")

    theta_desc = f"{theta_min}°" if theta_min == theta_max else f"[{theta_min},{theta_max}]°"
    print(f"\n{'=' * 60}")
    print(f"Scan point {i + 1}/{n_total}: theta={theta_desc}, nTracks={n_tracks}")
    print(f"{'=' * 60}")

    cmd = [
        sys.executable,
        benchmark_script,
        "-n",
        str(options.nEvents),
        "--thetaMin",
        str(theta_min),
        "--thetaMax",
        str(theta_max),
        "--nTracks",
        str(n_tracks),
        "--Dx",
        str(GUN_DX),
        "--Dy",
        str(GUN_DY),
        "--tag",
        tag,
        "--seed",
        str(options.seed + i),
        "-o",
        point_dir,
        "--output-json",
        json_path,
        "--pID",
        str(options.pID),
        "--Estart",
        str(options.Estart),
        "--Eend",
        str(options.Eend),
        "--debug",
        str(options.debug),
    ]
    if options.mixCharges:
        cmd.append("--mixCharges")

    result = subprocess.run(cmd, check=False)
    if result.returncode != 0:
        print(f"WARNING: scan point theta={theta_desc}, nTracks={n_tracks} failed (exit code {result.returncode})")
        continue

    try:
        with open(json_path) as f:
            metrics = json.load(f)
        benchmark_metrics = metrics["tracking_benchmark"]
    except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
        print(f"WARNING: failed to read results from {json_path}: {e}")
        continue

    all_results.append(
        {
            "theta": label_theta,
            "thetaMin": theta_min,
            "thetaMax": theta_max,
            "nTracks": n_tracks,
            "density_per_m2": round(n_tracks / GUN_AREA_M2, 4),
            "metrics": benchmark_metrics,
        }
    )

    # Clean up intermediate ROOT files
    if not options.keep_files:
        for pattern in [f"sim_{tag}.root", f"geo_{tag}.root", f"params_{tag}.root", f"sim_{tag}_rec*.root"]:
            for fpath in glob.glob(os.path.join(point_dir, pattern)):
                os.remove(fpath)
                print(f"  Cleaned up {fpath}")

# Save combined results
combined = {
    "scan_config": {
        "scan_mode": options.scan_mode,
        "thetas": thetas,
        "nTracksList": n_tracks_list,
        "nEvents": options.nEvents,
        "pID": options.pID,
        "Estart": options.Estart,
        "Eend": options.Eend,
        "seed": options.seed,
    },
    "scan_results": all_results,
}

combined_json = os.path.join(options.outputDir, "scan_results.json")
with open(combined_json, "w") as f:
    json.dump(combined, f, indent=2)
print(f"\nCombined results saved to {combined_json}")

# Save TGraphErrors to ROOT file
import ROOT

ROOT.gROOT.SetBatch(True)

metric_names = [
    "efficiency",
    "ghost_rate",
    "clone_rate",
    "dp_over_p_sigma",
    "n_reconstructible",
    "charge_id_efficiency",
]
metric_titles = {
    "efficiency": "Tracking efficiency",
    "ghost_rate": "Ghost rate",
    "clone_rate": "Clone rate",
    "dp_over_p_sigma": "#Deltap/p resolution (#sigma)",
    "n_reconstructible": "Reconstructible tracks",
    "charge_id_efficiency": "Charge-ID efficiency",
}

# Group results — only include numeric theta values for "vs theta" graphs
by_nTracks: dict[int, list[tuple[float, dict]]] = defaultdict(list)
by_theta: dict[str, list[tuple[int, dict]]] = defaultdict(list)

for r in all_results:
    theta_label = r["theta"]
    if isinstance(theta_label, (int, float)):
        by_nTracks[r["nTracks"]].append((float(theta_label), r["metrics"]))
    by_theta[str(theta_label)].append((r["nTracks"], r["metrics"]))

summary_root = os.path.join(options.outputDir, "scan_summary.root")
f_out = ROOT.TFile.Open(summary_root, "recreate")

for metric in metric_names:
    for n_tr, points in sorted(by_nTracks.items()):
        points.sort()
        valid = [(x, m) for x, m in points if m[metric]["value"] is not None]
        if not valid:
            continue
        gr = ROOT.TGraphErrors(len(valid))
        gr.SetName(f"g_{metric}_vs_theta_nTr{n_tr}")
        gr.SetTitle(f"{metric_titles[metric]}, nTracks={n_tr};#theta [deg];{metric_titles[metric]}")
        for j, (theta_val, m) in enumerate(valid):
            gr.SetPoint(j, theta_val, m[metric]["value"])
            gr.SetPointError(j, 0, m[metric].get("uncertainty") or 0)
        gr.Write()

    for theta_label, points in sorted(by_theta.items()):
        points.sort()
        valid = [(x, m) for x, m in points if m[metric]["value"] is not None]
        if not valid:
            continue
        gr = ROOT.TGraphErrors(len(valid))
        gr.SetName(f"g_{metric}_vs_nTracks_theta{theta_label}")
        gr.SetTitle(f"{metric_titles[metric]}, #theta={theta_label}#circ;nTracks;{metric_titles[metric]}")
        for j, (n_tr_val, m) in enumerate(valid):
            gr.SetPoint(j, n_tr_val, m[metric]["value"])
            gr.SetPointError(j, 0, m[metric].get("uncertainty") or 0)
        gr.Write()

f_out.Close()
print(f"ROOT summary saved to {summary_root}")

# Generate matplotlib plots
try:
    import matplotlib.pyplot as plt
    import numpy as np

    # Axis limits: rates are bounded to [0, max], efficiency to [min, 1.05]
    metric_ylimits: dict[str, tuple[float | None, float | None]] = {
        "efficiency": (None, 1.05),
        "ghost_rate": (0, None),
        "clone_rate": (0, None),
        "dp_over_p_sigma": (0, None),
        "n_reconstructible": (0, None),
        "charge_id_efficiency": (None, 1.05),
    }

    metric_ylabels = {
        "efficiency": "Efficiency",
        "ghost_rate": "Ghost rate",
        "clone_rate": "Clone rate",
        "dp_over_p_sigma": r"$\Delta p / p$ resolution ($\sigma$)",
        "n_reconstructible": f"Reconstructible tracks (out of {options.nEvents})",
        "charge_id_efficiency": "Charge-ID efficiency",
    }

    def _save_fig(fig: plt.Figure, base_path: str) -> None:
        """Save figure as both PDF and PNG."""
        fig.savefig(base_path + ".pdf")
        fig.savefig(base_path + ".png", dpi=150)

    def _get_values(points: list, metric: str) -> tuple[list, list, list]:
        """Extract x, y, yerr from sorted scan points, skipping None values."""
        x, y, yerr = [], [], []
        for p in points:
            val = p[1][metric]["value"]
            if val is None:
                continue
            x.append(p[0])
            y.append(val)
            yerr.append(p[1][metric].get("uncertainty") or 0)
        return x, y, yerr

    n_curves_theta = max(len(by_nTracks), 1)
    n_curves_mult = max(len(by_theta), 1)
    colours_theta = plt.cm.viridis(np.linspace(0, 0.9, n_curves_theta))
    colours_mult = plt.cm.plasma(np.linspace(0, 0.9, n_curves_mult))

    for metric in metric_names:
        ymin, ymax = metric_ylimits.get(metric, (None, None))
        ylabel = metric_ylabels.get(metric, metric)

        # Plots vs theta
        if len(by_nTracks) > 0 and any(len(pts) > 1 for pts in by_nTracks.values()):
            fig, ax = plt.subplots(figsize=(8, 5))
            for idx, (n_tr, points) in enumerate(sorted(by_nTracks.items())):
                points.sort()
                x, y, yerr = _get_values(points, metric)
                if not x:
                    continue
                ax.errorbar(
                    x,
                    y,
                    yerr=yerr,
                    marker="o",
                    linestyle="none",
                    capsize=3,
                    label=f"nTracks={n_tr}",
                    color=colours_theta[idx],
                )
            ax.set_xlabel(r"$\theta$ [deg]")
            ax.set_ylabel(ylabel)
            ax.set_title(f"{ylabel} vs polar angle")
            if ymin is not None:
                ax.set_ylim(bottom=ymin)
            if ymax is not None:
                ax.set_ylim(top=ymax)
            ax.legend()
            ax.grid(True, alpha=0.3)
            fig.tight_layout()
            _save_fig(fig, os.path.join(options.outputDir, f"scan_{metric}_vs_theta"))
            plt.close(fig)

        # Plots vs nTracks
        if len(by_theta) > 0 and any(len(pts) > 1 for pts in by_theta.values()):
            fig, ax = plt.subplots(figsize=(8, 5))
            for idx, (theta_label, points) in enumerate(sorted(by_theta.items())):
                points.sort()
                x, y, yerr = _get_values(points, metric)
                if not x:
                    continue
                try:
                    theta_legend = rf"$\theta$={float(theta_label):.0f}°"
                except ValueError:
                    theta_legend = rf"$\theta \in [{theta_label}]$°"
                ax.errorbar(
                    x,
                    y,
                    yerr=yerr,
                    marker="s",
                    linestyle="none",
                    capsize=3,
                    label=theta_legend,
                    color=colours_mult[idx],
                )
            ax.set_xlabel("Tracks per event")
            ax.set_ylabel(ylabel)
            ax.set_title(f"{ylabel} vs multiplicity (gun area = {GUN_AREA_M2:.1f} m²)")
            if ymin is not None:
                ax.set_ylim(bottom=ymin)
            if ymax is not None:
                ax.set_ylim(top=ymax)
            ax.legend()
            ax.grid(True, alpha=0.3)
            fig.tight_layout()
            _save_fig(fig, os.path.join(options.outputDir, f"scan_{metric}_vs_nTracks"))
            plt.close(fig)

    print(f"Plots saved to {options.outputDir}/scan_*.{{pdf,png}}")

except ImportError:
    print("matplotlib not available — skipping plots (ROOT summary file still produced)")

print(f"\nScan complete: {len(all_results)}/{n_total} points succeeded.")
