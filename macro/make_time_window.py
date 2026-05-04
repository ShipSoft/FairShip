#!/usr/bin/env python
# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

"""Construct realistic time windows by overlaying MC truth events.

Reads simulation output from a single ROOT file, computes the expected
number of interactions per time window, and produces merged events where
multiple sub-events are overlaid with Poisson-distributed multiplicity
and uniform time offsets.

Statistical choices (may be refined later):
- All events are treated with equal selection probability.
- Per-event MC weights are used only via their sum to determine the
  Poisson mean (lambda) for the number of interactions per window.
- Events are consumed consecutively from the input file rather than
  sampled randomly.  This is valid because:
  * All events are statistically independent.
  * The event pool is large enough that sampling without replacement
    is equivalent to sampling with replacement.
  * Consecutive reading avoids random-access I/O and caching overhead.

Physics assumptions:
- Event weight = expected occurrences of that interaction per spill
  (i.e. weights already scale to one full spill)
- Time window duration: 1 microsecond
- Uniform distribution of interactions in time
- Number of interactions per window: Poisson distributed
"""

import argparse
import logging
import sys

import numpy as np
import ROOT
import shipunit as u

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)

# Physics parameters
FULL_SPILL_POT = 4e13  # protons on target per spill (for cross-check only)
SPILL_DURATION = 1.0 * u.second  # 1 second in ns
TIME_WINDOW = 1.0 * u.microsecond  # 1 microsecond in ns


def discover_point_branches(tree):
    """Return list of branch names containing 'Point'."""
    return [b.GetName() for b in tree.GetListOfBranches() if "Point" in b.GetName()]


def get_point_class_name(chain, branch_name):
    """Get the C++ element class name for a Point branch."""
    branch = chain.GetBranch(branch_name)
    if not branch:
        return None
    class_name = branch.GetClassName()
    if class_name.startswith("vector<"):
        return class_name[7:-1]
    return class_name


def generate_cpp(point_class_names):
    """Generate C++ build_time_windows() that reads events sequentially."""
    includes = '#include "ShipMCTrack.h"\n'
    for class_name in sorted(set(point_class_names.values())):
        includes += f'#include "{class_name}.h"\n'

    # Input branch address setup
    branch_addr_setup = ""
    for branch_name, class_name in point_class_names.items():
        branch_addr_setup += f"    std::vector<{class_name}>* in_{branch_name} = nullptr;\n"
        branch_addr_setup += f'    chain.SetBranchAddress("{branch_name}", &in_{branch_name});\n'

    # Output vector declarations and branches
    out_decl = ""
    for branch_name, class_name in point_class_names.items():
        out_decl += f"    std::vector<{class_name}> out_{branch_name};\n"
        out_decl += f'    out_tree.Branch("{branch_name}", &out_{branch_name});\n'

    # Clear output vectors per window
    out_clear = ""
    for branch_name in point_class_names:
        out_clear += f"        out_{branch_name}.clear();\n"

    # Merge points from current entry
    merge_points = ""
    for branch_name in point_class_names:
        merge_points += f"""
            for (const auto& pt : *in_{branch_name}) {{
                auto p = pt;
                p.SetTime(pt.GetTime() + t_offset);
                p.SetTrackID(pt.GetTrackID() + track_offset);
                out_{branch_name}.push_back(std::move(p));
            }}
            total_points += in_{branch_name}->size();"""

    return f"""{includes}

int build_time_windows(
    TChain& chain,
    const std::vector<int>& window_sizes,
    const std::vector<double>& all_time_offsets,
    const char* output_path
) {{
    int n_windows = static_cast<int>(window_sizes.size());
    int n_entries = static_cast<int>(chain.GetEntries());

    // Set up input branch addresses
    std::vector<ShipMCTrack>* in_tracks = nullptr;
    chain.SetBranchAddress("MCTrack", &in_tracks);
{branch_addr_setup}

    // Set up output file and trees
    TFile out_file(output_path, "RECREATE");
    TTree out_tree("cbmsim", "Time window overlay");

    std::vector<ShipMCTrack> out_tracks;
    out_tree.Branch("MCTrack", &out_tracks);
{out_decl}

    TTree meta_tree("timewindow_meta", "Time window metadata");
    int n_overlaid = 0, n_total_tracks = 0, n_total_points = 0;
    meta_tree.Branch("n_overlaid", &n_overlaid);
    meta_tree.Branch("n_total_tracks", &n_total_tracks);
    meta_tree.Branch("n_total_points", &n_total_points);

    std::vector<double> sub_time_offsets_v;
    std::vector<int> sub_n_tracks_v, sub_original_indices_v;
    meta_tree.Branch("sub_time_offsets", &sub_time_offsets_v);
    meta_tree.Branch("sub_n_tracks", &sub_n_tracks_v);
    meta_tree.Branch("sub_original_indices", &sub_original_indices_v);

    // Build time windows by reading events sequentially
    int cursor = 0;
    int offset = 0;
    for (int w = 0; w < n_windows; ++w) {{
        int n_sub = window_sizes[w];

        out_tracks.clear();
{out_clear}
        sub_time_offsets_v.clear();
        sub_n_tracks_v.clear();
        sub_original_indices_v.clear();

        int track_offset = 0;
        int total_points = 0;

        for (int k = 0; k < n_sub; ++k) {{
            int evt_idx = cursor % n_entries;
            chain.GetEntry(evt_idx);
            double t_offset = all_time_offsets[offset + k];

            int nt = static_cast<int>(in_tracks->size());

            // Merge MCTracks with time offset and re-indexing
            for (int i = 0; i < nt; ++i) {{
                auto t = (*in_tracks)[i];
                t.SetStartT((*in_tracks)[i].GetStartT() + t_offset);
                if ((*in_tracks)[i].GetMotherId() >= 0)
                    t.SetMotherId((*in_tracks)[i].GetMotherId() + track_offset);
                t.SetTrackID(i + track_offset);
                t.SetEventID(k);
                out_tracks.push_back(std::move(t));
            }}

            // Merge Point branches{merge_points}

            sub_time_offsets_v.push_back(t_offset);
            sub_n_tracks_v.push_back(nt);
            sub_original_indices_v.push_back(evt_idx);

            track_offset += nt;
            ++cursor;
        }}

        n_overlaid = n_sub;
        n_total_tracks = static_cast<int>(out_tracks.size());
        n_total_points = total_points;

        out_tree.Fill();
        meta_tree.Fill();

        offset += n_sub;

        if ((w + 1) % 10 == 0 || w == 0 || w == n_windows - 1) {{
            std::cout << "\\rBuilding windows: " << (w + 1) << "/" << n_windows
                      << " (" << (100 * (w + 1) / n_windows) << "%)" << std::flush;
        }}
    }}
    std::cout << std::endl;

    out_file.Write();
    out_file.Close();

    std::cout << "Output written to " << output_path << std::endl;
    std::cout << "  cbmsim tree: " << n_windows << " time window events" << std::endl;
    std::cout << "  timewindow_meta tree: per-window metadata" << std::endl;

    return 0;
}}
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("input_file", help="Input ROOT file")
    parser.add_argument(
        "-n", "--n-windows", type=int, default=100, help="Number of time windows to generate (default: 100)"
    )
    parser.add_argument(
        "-o", "--output", default="time_windows.root", help="Output ROOT file (default: time_windows.root)"
    )
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducibility")
    parser.add_argument("--sim-pot", type=float, default=1e11, help="Simulated PoT for cross-check (default: 1e11)")
    args = parser.parse_args()

    if args.seed is not None:
        np.random.seed(args.seed)

    log.info("=== Time Window Event Overlay ===")
    log.info(f"Time window: {TIME_WINDOW / u.microsecond:.1f} us")
    log.info(f"Output: {args.output}")
    log.info(f"Number of time windows: {args.n_windows}")

    # Open input
    chain = ROOT.TChain("cbmsim")
    chain.Add(args.input_file)

    n_events = chain.GetEntries()
    if n_events == 0:
        log.error("No events found in input file")
        sys.exit(1)
    log.info(f"Input events: {n_events}")

    # Discover Point branches
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

    # --- Determine total interactions per spill (= sum of event weights) ---
    # Each event's weight (MCTrack[0].GetWeight()) gives the expected number
    # of times that interaction occurs per spill.  The sum over all events
    # is the total interaction rate per spill.
    # Cache the result in a sidecar file to avoid recomputing on subsequent runs.
    sumw_cache = args.input_file + ".sumw"
    try:
        with open(sumw_cache) as f:
            sum_weights = float(f.read().strip())
        log.info(f"Sum of weights (cached): {sum_weights:.6g}")
    except (FileNotFoundError, ValueError):
        log.info("Computing sum of weights via RDataFrame...")
        ROOT.gInterpreter.Declare('#include "ShipMCTrack.h"')
        rdf = ROOT.RDataFrame("cbmsim", args.input_file)
        rdf_w = rdf.Define("w", "MCTrack.empty() ? 0.0 : MCTrack[0].GetWeight()")
        sum_weights = rdf_w.Sum("w").GetValue()
        with open(sumw_cache, "w") as f:
            f.write(f"{sum_weights}\n")
        log.info(f"Sum of weights: {sum_weights:.6g} (saved to {sumw_cache})")

    if sum_weights <= 0:
        log.error("Sum of weights is zero or negative")
        sys.exit(1)

    # Compute Poisson mean (lambda) for interactions per time window.
    # sum_weights = total interactions per spill (weights scale to one spill).
    # Fraction of spill in one time window gives the per-window expectation:
    lam = sum_weights * (TIME_WINDOW / SPILL_DURATION)

    # Cross-check: independent lambda estimate from PoT ratio
    lam_pot = n_events * (FULL_SPILL_POT / args.sim_pot) * (TIME_WINDOW / SPILL_DURATION)
    avg_weight = sum_weights / n_events
    expected_avg_weight = FULL_SPILL_POT / args.sim_pot

    log.info(f"Expected interactions per window (lambda): {lam:.4f}")
    log.info(f"  Cross-check from PoT ratio ({args.sim_pot:.0e} sim PoT): {lam_pot:.4f}")
    log.info(f"  Average weight: {avg_weight:.2f} (expected ~{expected_avg_weight:.0f})")

    # --- Pre-generate window sizes and time offsets ---
    window_sizes_np = np.random.poisson(lam, size=args.n_windows).astype(np.int32)
    total_events_needed = int(window_sizes_np.sum())
    log.info(f"Total events to consume: {total_events_needed}")

    if total_events_needed > n_events:
        log.warning(
            f"Need {total_events_needed} events but only {n_events} available; "
            f"will wrap around (events reused after full pass)."
        )

    # Uniform time offsets for each sub-event
    time_offsets_np = np.random.uniform(0, TIME_WINDOW, size=total_events_needed)

    # Convert to ROOT vectors for C++
    window_sizes_vec = ROOT.std.vector("int")(window_sizes_np.tolist())
    time_offsets_vec = ROOT.std.vector("double")(time_offsets_np.tolist())

    # --- Generate C++, compile, and run ---
    log.info("Compiling generated C++ code...")
    cpp_code = generate_cpp(point_class_names)
    if not ROOT.gInterpreter.Declare(cpp_code):
        log.error("Failed to compile generated C++ code")
        log.error("Generated code:\n" + cpp_code)
        sys.exit(1)

    log.info("Building time windows...")
    ROOT.build_time_windows(chain, window_sizes_vec, time_offsets_vec, args.output)
    log.info("Done.")


if __name__ == "__main__":
    main()
