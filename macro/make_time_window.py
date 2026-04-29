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

Performance:
- Weight extraction uses RDataFrame (C++ columnar, with progress bar)
- Event caching and time window construction use generated C++ code
  compiled at runtime via gInterpreter, avoiding Python event loops
"""

import argparse
import logging
import subprocess
import sys
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
            if not remote_path.endswith(".root"):
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
    """Get the C++ element class name for a Point branch."""
    branch = chain.GetBranch(branch_name)
    if branch:
        class_name = branch.GetClassName()
        if class_name.startswith("vector<"):
            return class_name[7:-1]
        return class_name
    return None


def pre_generate_selections(n_windows, n_events, lam, probs):
    """Pre-generate all time window event selections.

    Returns list of (event_indices, time_offsets) tuples and the sorted
    array of unique event indices needed.
    """
    all_windows = []
    all_indices = []

    for _ in range(n_windows):
        n_sub = np.random.poisson(lam)
        if n_sub == 0:
            all_windows.append((np.array([], dtype=np.int32), np.array([])))
            continue
        indices = np.random.choice(n_events, size=n_sub, replace=True, p=probs).astype(np.int32)
        offsets = np.random.uniform(0, TIME_WINDOW, size=n_sub)
        all_windows.append((indices, offsets))
        all_indices.append(indices)

    if all_indices:
        unique_indices = np.unique(np.concatenate(all_indices))
    else:
        unique_indices = np.array([], dtype=np.int32)

    total_draws = sum(len(w[0]) for w in all_windows)
    log.info(
        f"Pre-generated {n_windows} windows: {total_draws} total event draws, {len(unique_indices)} unique events to cache"
    )

    return all_windows, unique_indices


def generate_cpp(point_class_names):
    """Generate C++ build_time_windows() function.

    The generated code handles caching and merging for the specific set
    of Point branch types discovered in the input files.
    """
    # --- #include directives for all types used ---
    includes = '#include "ShipMCTrack.h"\n'
    for class_name in sorted(set(point_class_names.values())):
        includes += f'#include "{class_name}.h"\n'

    # --- EventCache struct members ---
    cache_members = ""
    for branch_name, class_name in point_class_names.items():
        cache_members += f"    std::vector<{class_name}> {branch_name};\n"

    # --- Input branch address setup ---
    branch_addr_setup = ""
    for branch_name, class_name in point_class_names.items():
        branch_addr_setup += f"    std::vector<{class_name}>* in_{branch_name} = nullptr;\n"
        branch_addr_setup += f'    chain.SetBranchAddress("{branch_name}", &in_{branch_name});\n'

    # --- Cache copy from input ---
    cache_copy = ""
    for branch_name in point_class_names:
        cache_copy += f"        ec.{branch_name} = *in_{branch_name};\n"

    # --- Output vector declarations and branches ---
    out_decl = ""
    for branch_name, class_name in point_class_names.items():
        out_decl += f"    std::vector<{class_name}> out_{branch_name};\n"
        out_decl += f'    out_tree.Branch("{branch_name}", &out_{branch_name});\n'

    # --- Clear output vectors per window ---
    out_clear = ""
    for branch_name in point_class_names:
        out_clear += f"        out_{branch_name}.clear();\n"

    # --- Merge points from cache ---
    merge_points = ""
    for branch_name in point_class_names:
        merge_points += f"""
            for (const auto& pt : cached.{branch_name}) {{
                auto p = pt;
                p.SetTime(pt.GetTime() + t_offset);
                p.SetTrackID(pt.GetTrackID() + track_offset);
                out_{branch_name}.push_back(std::move(p));
            }}
            total_points += cached.{branch_name}.size();"""

    return f"""{includes}
struct EventCache {{
    std::vector<ShipMCTrack> tracks;
{cache_members}}};

int build_time_windows(
    TChain& chain,
    const std::vector<int>& window_sizes,
    const std::vector<int>& all_event_indices,
    const std::vector<double>& all_time_offsets,
    const char* output_path
) {{
    int n_windows = static_cast<int>(window_sizes.size());

    // Collect unique event indices
    std::set<int> unique_set(all_event_indices.begin(), all_event_indices.end());
    std::vector<int> unique_sorted(unique_set.begin(), unique_set.end());
    int n_unique = static_cast<int>(unique_sorted.size());

    std::cout << "Caching " << n_unique << " unique events..." << std::endl;

    // Set up input branch addresses
    std::vector<ShipMCTrack>* in_tracks = nullptr;
    chain.SetBranchAddress("MCTrack", &in_tracks);
{branch_addr_setup}

    // Cache events in sorted order (sequential I/O)
    std::map<int, EventCache> cache;
    for (int i = 0; i < n_unique; ++i) {{
        chain.GetEntry(unique_sorted[i]);
        EventCache ec;
        ec.tracks = *in_tracks;
{cache_copy}
        cache[unique_sorted[i]] = std::move(ec);

        if ((i + 1) % 100 == 0 || i == n_unique - 1) {{
            std::cout << "\\rCaching events: " << (i + 1) << "/" << n_unique
                      << " (" << (100 * (i + 1) / n_unique) << "%)" << std::flush;
        }}
    }}
    std::cout << std::endl;

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

    // Build time windows from cache
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
            int evt_idx = all_event_indices[offset + k];
            double t_offset = all_time_offsets[offset + k];
            const auto& cached = cache.at(evt_idx);
            int nt = static_cast<int>(cached.tracks.size());

            // Merge MCTracks with time offset and re-indexing
            for (int i = 0; i < nt; ++i) {{
                auto t = cached.tracks[i];
                t.SetStartT(cached.tracks[i].GetStartT() + t_offset);
                if (cached.tracks[i].GetMotherId() >= 0)
                    t.SetMotherId(cached.tracks[i].GetMotherId() + track_offset);
                t.SetTrackID(i + track_offset);
                t.SetEventID(k);
                out_tracks.push_back(std::move(t));
            }}

            // Merge Point branches{merge_points}

            sub_time_offsets_v.push_back(t_offset);
            sub_n_tracks_v.push_back(nt);
            sub_original_indices_v.push_back(evt_idx);

            track_offset += nt;
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
    if not input_files:
        log.error("No input files found")
        sys.exit(1)

    # Build input chain and discover branches
    chain = ROOT.TChain("cbmsim")
    for f in input_files:
        chain.Add(f)
    log.info(f"Added {len(input_files)} files to chain")

    n_events = chain.GetEntries()
    if n_events == 0:
        log.error("No events found in input files")
        sys.exit(1)

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
    point_class_names = {b: c for b, c in point_class_names.items() if b in point_branches}

    # --- Phase A: Extract weights via RDataFrame ---
    log.info("--- Phase A: Extracting weights via RDataFrame ---")
    # Ensure Cling has full class definitions (not just forward declarations
    # from dictionary payload) before RDataFrame instantiates RVec<T> templates
    ROOT.gInterpreter.Declare('#include "ShipMCTrack.h"')
    file_vec = ROOT.std.vector("string")()
    for f in input_files:
        file_vec.push_back(f)
    rdf = ROOT.RDataFrame("cbmsim", file_vec)
    try:
        ROOT.RDF.Experimental.AddProgressBar(rdf)
    except AttributeError:
        log.warning("RDF.Experimental.AddProgressBar not available, no progress bar for weight extraction")
    rdf_w = rdf.Define("w", "MCTrack.empty() ? 0.0 : MCTrack[0].GetWeight()")
    weights = rdf_w.AsNumpy(columns=["w"])["w"]

    sum_weights = np.sum(weights)
    scale = (TIME_WINDOW / SPILL_DURATION) * (FULL_SPILL_POT / SIM_POT)
    lam = sum_weights * scale

    log.info(f"Total input events: {n_events}")
    log.info(f"Sum of weights: {sum_weights:.6g}")
    log.info(f"Scale factor: {scale:.6g}")
    log.info(f"Expected interactions per {TIME_WINDOW / u.microsecond:.0f} us time window (lambda): {lam:.4f}")

    if sum_weights <= 0:
        log.error("Sum of weights is zero or negative, cannot sample")
        sys.exit(1)
    probs = weights / sum_weights

    # --- Phase B: Pre-generate all selections ---
    log.info("--- Phase B: Pre-generating time window selections ---")
    all_windows, _unique_indices = pre_generate_selections(args.n_windows, n_events, lam, probs)

    # Flatten window specs into vectors for C++
    window_sizes = ROOT.std.vector("int")()
    all_event_indices = ROOT.std.vector("int")()
    all_time_offsets = ROOT.std.vector("double")()

    for indices, offsets in all_windows:
        window_sizes.push_back(len(indices))
        for idx in indices:
            all_event_indices.push_back(int(idx))
        for off in offsets:
            all_time_offsets.push_back(float(off))

    # --- Phases C+D: Generate C++, compile, and run ---
    log.info("--- Phases C+D: Caching events and building time windows (C++) ---")
    cpp_code = generate_cpp(point_class_names)
    log.info("Compiling generated C++ code...")
    if not ROOT.gInterpreter.Declare(cpp_code):
        log.error("Failed to compile generated C++ code")
        log.error("Generated code:\n" + cpp_code)
        sys.exit(1)

    ROOT.build_time_windows(chain, window_sizes, all_event_indices, all_time_offsets, args.output)

    log.info("Done.")


if __name__ == "__main__":
    main()
