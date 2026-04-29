#!/usr/bin/env python
# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

"""Construct realistic time windows by overlaying MC truth events.

Reads simulation output from a set of ROOT files, computes the expected
number of interactions per time window, and produces merged events where
multiple sub-events are overlaid with Poisson-distributed multiplicity
and uniform time offsets.

Assumptions (documented here and printed at runtime):
- Full spill: 4e13 protons on target (PoT) in 1 second
- Simulation sample: ~1e11 PoT
- Time window duration: 1 microsecond
- Uniform distribution of interactions in time
- Number of interactions per window: Poisson distributed
- Events sampled proportional to weight (with replacement)

Performance notes:
- Weight collection reads only the MCTrack branch (~1% of data)
- All time window selections are pre-generated, then unique events
  are read in sorted order (sequential I/O) and cached in memory
- Time window construction is pure in-memory, no further I/O
"""

import argparse
import logging
import subprocess
import sys
from array import array
from urllib.parse import urlparse

import numpy as np
import ROOT
import shipunit as u

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)

# Physics parameters
FULL_SPILL_POT = 4e13  # protons on target per spill
SPILL_DURATION = 1.0 * u.second  # 1 second in ns
SIM_POT = 1e11  # approximate PoT in simulation sample
TIME_WINDOW = 1.0 * u.microsecond  # 1 microsecond in ns


def resolve_input_files(paths):
    """Resolve input file paths, expanding xrootd directories.

    For xrootd URIs (root://...) that point to a directory rather than
    a specific file, use xrdfs to list .root files within.
    """
    resolved = []
    for path in paths:
        parsed = urlparse(path)
        if parsed.scheme == "root":
            server = parsed.netloc
            remote_path = parsed.path
            # Check if this looks like a directory (no .root extension)
            if not remote_path.endswith(".root"):
                # Strip trailing glob pattern if present
                remote_path = remote_path.rstrip("/*")
                log.info(f"Listing xrootd directory (recursive): {server}{remote_path}")
                result = subprocess.run(
                    ["xrdfs", server, "ls", "-R", remote_path],
                    capture_output=True,
                    text=True,
                )
                if result.returncode != 0:
                    log.error(f"xrdfs ls failed: {result.stderr.strip()}")
                    sys.exit(1)
                for line in result.stdout.strip().splitlines():
                    if line.endswith(".root") and line.rsplit("/", 1)[-1].startswith("sim_"):
                        resolved.append(f"root://{server}/{line}")
                log.info(f"  Found {len(resolved)} ROOT files")
            else:
                resolved.append(path)
        else:
            resolved.append(path)
    return resolved


def discover_point_branches(tree):
    """Return list of branch names containing 'Point'."""
    branches = []
    for branch in tree.GetListOfBranches():
        name = branch.GetName()
        if "Point" in name:
            branches.append(name)
    return branches


def get_point_class_name(chain, branch_name):
    """Get the C++ class name for a Point branch."""
    branch = chain.GetBranch(branch_name)
    if branch:
        class_name = branch.GetClassName()
        # For vector<X>, extract X
        if class_name.startswith("vector<"):
            return class_name[7:-1]
        return class_name
    return None


def compute_lambda(chain, n_events):
    """Compute expected interactions per time window from event weights.

    Only reads the MCTrack branch to minimise I/O.
    Returns (lambda, weights_array).
    """
    chain.SetBranchStatus("*", 0)
    chain.SetBranchStatus("MCTrack*", 1)

    weights = np.empty(n_events)
    for i in range(n_events):
        chain.GetEntry(i)
        if len(chain.MCTrack) > 0:
            weights[i] = chain.MCTrack[0].GetWeight()
        else:
            weights[i] = 0.0

    # Re-enable all branches for subsequent reads
    chain.SetBranchStatus("*", 1)

    sum_weights = np.sum(weights)
    lam = sum_weights * (TIME_WINDOW / SPILL_DURATION) * (FULL_SPILL_POT / SIM_POT)

    log.info(f"Total input events: {n_events}")
    log.info(f"Sum of weights: {sum_weights:.6g}")
    log.info(
        "Scale factor: (TIME_WINDOW/SPILL_DURATION) * (FULL_SPILL_POT/SIM_POT)"
        f" = {(TIME_WINDOW / SPILL_DURATION) * (FULL_SPILL_POT / SIM_POT):.6g}"
    )
    log.info(f"Expected interactions per {TIME_WINDOW / u.microsecond:.0f} us time window (lambda): {lam:.4f}")

    return lam, weights


def pre_generate_selections(n_windows, n_events, lam, probs):
    """Pre-generate all time window event selections.

    Returns list of (event_indices, time_offsets) tuples and the set of
    unique event indices needed.
    """
    all_windows = []
    all_indices = []

    for _ in range(n_windows):
        n_sub = np.random.poisson(lam)
        if n_sub == 0:
            all_windows.append((np.array([], dtype=int), np.array([])))
            continue
        indices = np.random.choice(n_events, size=n_sub, replace=True, p=probs)
        offsets = np.random.uniform(0, TIME_WINDOW, size=n_sub)
        all_windows.append((indices, offsets))
        all_indices.append(indices)

    if all_indices:
        unique_indices = np.unique(np.concatenate(all_indices))
    else:
        unique_indices = np.array([], dtype=int)

    total_draws = sum(len(w[0]) for w in all_windows)
    log.info(
        f"Pre-generated {n_windows} windows: {total_draws} total event draws, {len(unique_indices)} unique events to cache"
    )

    return all_windows, unique_indices


def deep_copy_event(chain, point_branches):
    """Deep-copy MCTrack and Point data from current chain entry into Python lists."""
    tracks = [ROOT.ShipMCTrack(chain.MCTrack[i]) for i in range(len(chain.MCTrack))]

    points = {}
    for branch_name in point_branches:
        branch_data = getattr(chain, branch_name)
        points[branch_name] = [type(branch_data[i])(branch_data[i]) for i in range(len(branch_data))]

    return {"tracks": tracks, "points": points}


def cache_events(chain, unique_indices, point_branches):
    """Read unique events in sorted order and cache in memory.

    Sequential access pattern enables ROOT's TTreeCache prefetch.
    """
    cache = {}
    n_total = len(unique_indices)

    for i, evt_idx in enumerate(unique_indices):
        chain.GetEntry(int(evt_idx))
        cache[int(evt_idx)] = deep_copy_event(chain, point_branches)

        if (i + 1) % 1000 == 0 or i == n_total - 1:
            log.info(f"  Cached {i + 1}/{n_total} events")

    return cache


def merge_from_cache(cache, event_indices, time_offsets, point_branches, out_tracks, out_points):
    """Merge sub-events from cache into output vectors.

    Pure in-memory operation — no I/O.
    """
    track_offset = 0
    sub_event_info = []

    for k, (evt_idx, t_offset) in enumerate(zip(event_indices, time_offsets)):
        cached = cache[int(evt_idx)]
        cached_tracks = cached["tracks"]
        n_tracks = len(cached_tracks)

        info = {
            "original_event": int(evt_idx),
            "time_offset_ns": float(t_offset),
            "n_tracks": n_tracks,
        }

        # Merge MCTracks
        for track in cached_tracks:
            new_track = ROOT.ShipMCTrack(track)
            new_track.SetStartT(track.GetStartT() + t_offset)
            mother_id = track.GetMotherId()
            if mother_id >= 0:
                new_track.SetMotherId(mother_id + track_offset)
            new_track.SetTrackID(track.GetTrackID() + track_offset)
            new_track.SetEventID(k)
            out_tracks.push_back(new_track)

        # Merge Point branches
        n_points_total = 0
        for branch_name in point_branches:
            cached_points = cached["points"][branch_name]
            n_points_total += len(cached_points)
            for point in cached_points:
                new_point = type(point)(point)
                new_point.SetTime(point.GetTime() + t_offset)
                new_point.SetTrackID(point.GetTrackID() + track_offset)
                out_points[branch_name].push_back(new_point)

        info["n_points"] = n_points_total
        sub_event_info.append(info)
        track_offset += n_tracks

    return sub_event_info


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("input_files", nargs="+", help="Input ROOT files (local paths or xrootd URIs)")
    parser.add_argument(
        "-n", "--n-windows", type=int, default=100, help="Number of time windows to generate (default: 100)"
    )
    parser.add_argument(
        "-o", "--output", default="time_windows.root", help="Output ROOT file (default: time_windows.root)"
    )
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducibility")
    args = parser.parse_args()

    if args.seed is not None:
        np.random.seed(args.seed)

    log.info("=== Time Window Event Overlay ===")
    log.info(f"Full spill PoT: {FULL_SPILL_POT:.0e}")
    log.info(f"Simulation PoT: {SIM_POT:.0e}")
    log.info(f"Time window: {TIME_WINDOW / u.microsecond:.1f} us")
    log.info(f"Output: {args.output}")
    log.info(f"Number of time windows: {args.n_windows}")

    # Resolve xrootd directories to individual files
    input_files = resolve_input_files(args.input_files)

    # Build input chain
    chain = ROOT.TChain("cbmsim")
    for f in input_files:
        chain.Add(f)
    log.info(f"Added {len(input_files)} files to chain")

    n_events = chain.GetEntries()
    if n_events == 0:
        log.error("No events found in input files")
        sys.exit(1)

    # Discover Point branches (need one full entry for branch info)
    chain.GetEntry(0)
    point_branches = discover_point_branches(chain)
    log.info(f"Point branches: {point_branches}")

    point_class_names = {}
    for branch_name in point_branches:
        class_name = get_point_class_name(chain, branch_name)
        if class_name:
            point_class_names[branch_name] = class_name
            log.info(f"  {branch_name} -> {class_name}")
        else:
            log.warning(f"  {branch_name}: could not determine class, skipping")
    point_branches = [b for b in point_branches if b in point_class_names]

    # --- Phase A: Weight collection (MCTrack branch only) ---
    log.info("--- Phase A: Collecting weights (MCTrack branch only) ---")
    lam, weights = compute_lambda(chain, n_events)
    probs = weights / np.sum(weights)

    # --- Phase B: Pre-generate all selections (pure CPU) ---
    log.info("--- Phase B: Pre-generating time window selections ---")
    all_windows, unique_indices = pre_generate_selections(args.n_windows, n_events, lam, probs)

    # --- Phase C: Cache unique events (sorted sequential I/O) ---
    log.info(f"--- Phase C: Caching {len(unique_indices)} unique events ---")
    cache = cache_events(chain, unique_indices, point_branches)
    log.info(f"  Cache complete ({len(cache)} events in memory)")

    # --- Phase D: Build time windows from cache (in-memory) ---
    log.info("--- Phase D: Building time windows from cache ---")

    out_file = ROOT.TFile(args.output, "RECREATE")

    # Main cbmsim tree with vector branches
    out_tree = ROOT.TTree("cbmsim", "Time window overlay")
    out_tracks = ROOT.std.vector("ShipMCTrack")()
    out_tree.Branch("MCTrack", out_tracks)

    out_points = {}
    for branch_name in point_branches:
        class_name = point_class_names[branch_name]
        vec = ROOT.std.vector(class_name)()
        out_points[branch_name] = vec
        out_tree.Branch(branch_name, vec)

    # Debug/metadata tree
    meta_tree = ROOT.TTree("timewindow_meta", "Time window metadata")
    n_overlaid = array("i", [0])
    n_total_tracks = array("i", [0])
    n_total_points = array("i", [0])
    meta_tree.Branch("n_overlaid", n_overlaid, "n_overlaid/I")
    meta_tree.Branch("n_total_tracks", n_total_tracks, "n_total_tracks/I")
    meta_tree.Branch("n_total_points", n_total_points, "n_total_points/I")

    sub_time_offsets = ROOT.std.vector("double")()
    sub_n_tracks = ROOT.std.vector("int")()
    sub_original_indices = ROOT.std.vector("int")()
    meta_tree.Branch("sub_time_offsets", sub_time_offsets)
    meta_tree.Branch("sub_n_tracks", sub_n_tracks)
    meta_tree.Branch("sub_original_indices", sub_original_indices)

    for window_idx, (event_indices, time_offsets) in enumerate(all_windows):
        out_tracks.clear()
        for vec in out_points.values():
            vec.clear()
        sub_time_offsets.clear()
        sub_n_tracks.clear()
        sub_original_indices.clear()

        n_sub = len(event_indices)

        if n_sub == 0:
            n_overlaid[0] = 0
            n_total_tracks[0] = 0
            n_total_points[0] = 0
            out_tree.Fill()
            meta_tree.Fill()
            continue

        sub_info = merge_from_cache(cache, event_indices, time_offsets, point_branches, out_tracks, out_points)

        n_overlaid[0] = n_sub
        n_total_tracks[0] = out_tracks.size()
        total_points = sum(vec.size() for vec in out_points.values())
        n_total_points[0] = total_points

        for info in sub_info:
            sub_time_offsets.push_back(info["time_offset_ns"])
            sub_n_tracks.push_back(info["n_tracks"])
            sub_original_indices.push_back(info["original_event"])

        out_tree.Fill()
        meta_tree.Fill()

        if (window_idx + 1) % 10 == 0 or window_idx == 0:
            log.info(
                f"Window {window_idx + 1}/{args.n_windows}: "
                f"{n_sub} sub-events, {out_tracks.size()} tracks, {total_points} points"
            )

    out_file.Write()
    out_file.Close()
    log.info(f"Output written to {args.output}")
    log.info(f"  cbmsim tree: {args.n_windows} time window events")
    log.info("  timewindow_meta tree: per-window metadata")


if __name__ == "__main__":
    main()
