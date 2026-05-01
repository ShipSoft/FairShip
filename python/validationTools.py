# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration


def container_size(container):
    if container is None:
        return None
    try:
        return len(container)
    except TypeError:
        return None


def format_mean_std(count, total, total_sq):
    if count <= 0:
        return "n/a"
    mean = total / count
    variance = max(0.0, total_sq / count - mean * mean)
    std = variance**0.5
    return f"{mean:.4g} +- {std:.4g}"


def safe_fraction(numerator, denominator):
    if denominator == 0:
        return "n/a"
    return f"{100.0 * numerator / denominator:.2f}%"


def print_section(title):
    print(" ")
    print(f"[{title}]")


def print_kv(label, value, width=28, separator=" : "):
    print(f"  {label:<{width}}{separator}{value}")


def update_numeric_stat(stats, value):
    stats["count"] += 1
    stats["sum"] += value
    stats["sum_sq"] += value * value
    if stats["min"] is None or value < stats["min"]:
        stats["min"] = value
    if stats["max"] is None or value > stats["max"]:
        stats["max"] = value


def format_stat_summary(stats):
    return (
        f"{format_mean_std(stats['count'], stats['sum'], stats['sum_sq'])}"
        f"  [min={stats['min']:.4g}, max={stats['max']:.4g}]"
    )


def make_numeric_stats():
    return {"count": 0, "sum": 0.0, "sum_sq": 0.0, "min": None, "max": None}


def make_reco_validation_stats():
    return {
        "events_digitized": 0,
        "events_reconstructed": 0,
        "events_with_hits": 0,
        "events_with_candidates": 0,
        "events_with_fitted_tracks": 0,
        "events_with_good_tracks": 0,
        "smeared_hits_total": 0,
        "track_candidates_total": 0,
        "track_candidates_rejected_hits": 0,
        "track_candidates_rejected_stations": 0,
        "fit_hypotheses_tried": 0,
        "fit_hypotheses_converged": 0,
        "tracks_failed_consistency": 0,
        "tracks_failed_fit": 0,
        "tracks_failed_state_access": 0,
        "fitted_tracks_total": 0,
        "good_tracks_total": 0,
        "vertexing_calls": 0,
        "veto_links_total": 0,
        "event_track_candidates_sum": 0.0,
        "event_track_candidates_sum_sq": 0.0,
        "event_fitted_tracks_sum": 0.0,
        "event_fitted_tracks_sum_sq": 0.0,
        "event_good_tracks_sum": 0.0,
        "event_good_tracks_sum_sq": 0.0,
        "event_veto_links_sum": 0.0,
        "event_veto_links_sum_sq": 0.0,
        "chi2_sum": 0.0,
        "chi2_sum_sq": 0.0,
        "chi2_count": 0,
        "ndf_sum": 0.0,
        "ndf_sum_sq": 0.0,
        "ndf_count": 0,
        "candidate_hits_sum": 0.0,
        "candidate_hits_sum_sq": 0.0,
        "candidate_hits_count": 0,
        "candidate_stations_sum": 0.0,
        "candidate_stations_sum_sq": 0.0,
        "candidate_stations_count": 0,
        "veto_link_distance_sum": 0.0,
        "veto_link_distance_sum_sq": 0.0,
        "veto_link_distance_count": 0,
    }


def record_event_stat(stats, key, value):
    stats[f"{key}_sum"] += value
    stats[f"{key}_sum_sq"] += value * value


def print_reco_validation_summary(stats, has_veto_detector=False):
    print_section("Reco Validation")
    for label in [
        "events_digitized",
        "events_reconstructed",
        "events_with_hits",
        "events_with_candidates",
        "events_with_fitted_tracks",
        "events_with_good_tracks",
        "smeared_hits_total",
        "track_candidates_total",
        "track_candidates_rejected_hits",
        "track_candidates_rejected_stations",
        "fit_hypotheses_tried",
        "fit_hypotheses_converged",
        "tracks_failed_consistency",
        "tracks_failed_fit",
        "tracks_failed_state_access",
        "fitted_tracks_total",
        "good_tracks_total",
        "vertexing_calls",
        "veto_links_total",
    ]:
        print_kv(label, stats[label], width=40)
    if stats["events_reconstructed"] > 0:
        n_events = stats["events_reconstructed"]
        print_kv(
            "track_candidates_per_event",
            format_mean_std(n_events, stats["event_track_candidates_sum"], stats["event_track_candidates_sum_sq"]),
            width=40,
        )
        print_kv(
            "fitted_tracks_per_event",
            format_mean_std(n_events, stats["event_fitted_tracks_sum"], stats["event_fitted_tracks_sum_sq"]),
            width=40,
        )
        print_kv(
            "good_tracks_per_event",
            format_mean_std(n_events, stats["event_good_tracks_sum"], stats["event_good_tracks_sum_sq"]),
            width=40,
        )
        if has_veto_detector:
            print_kv(
                "veto_links_per_event",
                format_mean_std(n_events, stats["event_veto_links_sum"], stats["event_veto_links_sum_sq"]),
                width=40,
            )
    if stats["candidate_hits_count"] > 0:
        print_kv(
            "hits_per_candidate",
            format_mean_std(stats["candidate_hits_count"], stats["candidate_hits_sum"], stats["candidate_hits_sum_sq"]),
            width=40,
        )
    if stats["candidate_stations_count"] > 0:
        print_kv(
            "stations_per_candidate",
            format_mean_std(
                stats["candidate_stations_count"], stats["candidate_stations_sum"], stats["candidate_stations_sum_sq"]
            ),
            width=40,
        )
    if stats["veto_link_distance_count"] > 0:
        print_kv(
            "veto_link_distance",
            format_mean_std(
                stats["veto_link_distance_count"], stats["veto_link_distance_sum"], stats["veto_link_distance_sum_sq"]
            ),
            width=40,
        )
    if stats["chi2_count"] > 0:
        print_kv("fit_chi2_over_ndf", format_mean_std(stats["chi2_count"], stats["chi2_sum"], stats["chi2_sum_sq"]), width=40)
    if stats["ndf_count"] > 0:
        print_kv("fit_ndf", format_mean_std(stats["ndf_count"], stats["ndf_sum"], stats["ndf_sum_sq"]), width=40)
    if stats["fit_hypotheses_tried"] > 0:
        print_kv(
            "fit_convergence_fraction",
            f"{100.0 * stats['fit_hypotheses_converged'] / stats['fit_hypotheses_tried']:.2f}%",
            width=40,
        )
    if stats["track_candidates_total"] > 0:
        print_kv(
            "candidate_to_fit_fraction",
            f"{100.0 * stats['fitted_tracks_total'] / stats['track_candidates_total']:.2f}%",
            width=40,
        )
    if stats["fitted_tracks_total"] > 0:
        print_kv(
            "good_track_fraction",
            f"{100.0 * stats['good_tracks_total'] / stats['fitted_tracks_total']:.2f}%",
            width=40,
        )


def _collect_generator_stats(flags, generators):
    generator_stats = []
    p8gen = generators.get("P8gen")
    if p8gen is not None:
        if flags["HNL"]:
            generator_stats.append(("HNL retries", p8gen.nrOfRetries()))
            generator_stats.append(("Geometry rejections", p8gen.nrOfGeoRejections()))
            generator_stats.append(("HNL candidates", p8gen.GetCounter("hnl_candidates")))
            generator_stats.append(("Accepted HNL candidates", p8gen.GetCounter("hnl_accepted_candidates")))
            generator_stats.append(("Multi-HNL tries", p8gen.GetCounter("hnl_multi_candidate_tries")))
            generator_stats.append(("Stored decay products", p8gen.GetCounter("hnl_stored_decay_products")))
        elif flags["DarkPhoton"]:
            generator_stats.append(("DP retries", p8gen.nrOfRetries()))
            generator_stats.append(("Geometry rejections", p8gen.nrOfGeoRejections()))
            generator_stats.append(("Total dark photons", p8gen.nrOfDP()))
        elif flags["fixedTarget"]:
            generator_stats.append(("Generated events", p8gen.GetCounter("generated_events")))
            generator_stats.append(("G4-only events", p8gen.GetCounter("g4only_events")))
            generator_stats.append(("Charm input pairs", p8gen.GetCounter("charm_input_pairs")))
            generator_stats.append(("Stored tracks", p8gen.GetCounter("stored_tracks")))
            generator_stats.append(("Tracked final-state particles", p8gen.GetCounter("tracked_final_state_particles")))
            generator_stats.append(("Skipped final-state particles", p8gen.GetCounter("skipped_final_state_particles")))
    muon_back_gen = generators.get("MuonBackgen")
    if muon_back_gen is not None:
        generator_stats.append(("Scanned input entries", muon_back_gen.GetCounter("scanned_entries")))
        generator_stats.append(("Accepted input entries", muon_back_gen.GetCounter("accepted_entries")))
        generator_stats.append(("Selected muons", muon_back_gen.GetCounter("selected_muons")))
        generator_stats.append(("Transported tracks", muon_back_gen.GetCounter("transported_tracks")))
    ntuple_gen = generators.get("Ntuplegen")
    if ntuple_gen is not None:
        generator_stats.append(("Scanned ntuple entries", ntuple_gen.GetCounter("scanned_entries")))
        generator_stats.append(("Accepted ntuple entries", ntuple_gen.GetCounter("accepted_entries")))
        generator_stats.append(("Rejected ntuple entries", ntuple_gen.GetCounter("rejected_entries")))
    dis_gen = generators.get("DISgen")
    if dis_gen is not None:
        generator_stats.append(("Generated DIS events", dis_gen.GetCounter("generated_events")))
        generator_stats.append(("Interaction sampling trials", dis_gen.GetCounter("interaction_sampling_trials")))
        generator_stats.append(("Stored DIS particles", dis_gen.GetCounter("dis_particles_stored")))
        generator_stats.append(("Stored soft particles", dis_gen.GetCounter("soft_particles_stored")))
        generator_stats.append(("Skipped soft particles", dis_gen.GetCounter("soft_particles_skipped")))
    genie_gen = generators.get("Geniegen")
    if genie_gen is not None:
        generator_stats.append(("Generated GENIE events", genie_gen.GetCounter("generated_events")))
        generator_stats.append(("CC events", genie_gen.GetCounter("cc_events")))
        generator_stats.append(("nu-e elastic events", genie_gen.GetCounter("nue_elastic_events")))
        generator_stats.append(("Interaction sampling trials", genie_gen.GetCounter("interaction_sampling_trials")))
        generator_stats.append(("Stored outgoing leptons", genie_gen.GetCounter("outgoing_leptons_stored")))
        generator_stats.append(("Stored outgoing hadrons", genie_gen.GetCounter("outgoing_hadrons_stored")))
    return generator_stats


def print_simulation_output_summary(ROOT, output_filename, requested_events, flags, generators):
    generator_stats = _collect_generator_stats(flags, generators)
    if generator_stats:
        print_section("Generator Validation")
        for label, value in generator_stats:
            print_kv(label, value)

    with ROOT.TFile.Open(output_filename, "READ") as summary_file:
        if not summary_file or summary_file.IsZombie():
            print("Could not reopen output file for summary:", output_filename)
            return

        keys = list(summary_file.GetListOfKeys())
        print_section("Tree Validation")
        print_kv("Requested events", requested_events)

        tree = summary_file.Get("cbmsim")
        if not tree:
            print("No cbmsim tree found in output file.")
            return

        n_entries = tree.GetEntries()
        print_kv("Final cbmsim entries", n_entries)
        print_kv("Kept fraction", safe_fraction(n_entries, requested_events))

        branch_names = [branch.GetName() for branch in tree.GetListOfBranches()]
        print_kv("Branches in cbmsim", len(branch_names))
        print_kv("ROOT objects", len(keys))

        if n_entries <= 0:
            print("cbmsim tree is empty.")
            return

        scalar_stats = {}
        branch_stats = {}
        track_stats = {
            "total_tracks": 0,
            "primary_tracks": 0,
            "secondary_tracks": 0,
            "weight_sum": 0.0,
            "weight_sq_sum": 0.0,
            "weight_min": None,
            "weight_max": None,
            "p": make_numeric_stats(),
            "energy": make_numeric_stats(),
            "start_z": make_numeric_stats(),
            "pdg_counts": {},
        }

        for branch_name in branch_names:
            branch_stats[branch_name] = {"total": 0, "nonzero": 0, "max": 0, "sum_sq": 0.0}

        for event_index in range(n_entries):
            tree.GetEntry(event_index)
            for branch_name in branch_names:
                container = getattr(tree, branch_name, None)
                count = container_size(container)
                if count is None:
                    try:
                        value = float(container)
                    except (TypeError, ValueError):
                        continue
                    if branch_name not in scalar_stats:
                        scalar_stats[branch_name] = make_numeric_stats()
                    update_numeric_stat(scalar_stats[branch_name], value)
                    continue

                stats = branch_stats[branch_name]
                stats["total"] += count
                if count > 0:
                    stats["nonzero"] += 1
                if count > stats["max"]:
                    stats["max"] = count
                stats["sum_sq"] += count * count

                if branch_name == "MCTrack" and count > 0:
                    for track in container:
                        track_stats["total_tracks"] += 1
                        if track.GetMotherId() < 0:
                            track_stats["primary_tracks"] += 1
                        else:
                            track_stats["secondary_tracks"] += 1
                        weight = float(track.GetWeight())
                        track_stats["weight_sum"] += weight
                        track_stats["weight_sq_sum"] += weight * weight
                        if track_stats["weight_min"] is None or weight < track_stats["weight_min"]:
                            track_stats["weight_min"] = weight
                        if track_stats["weight_max"] is None or weight > track_stats["weight_max"]:
                            track_stats["weight_max"] = weight
                        update_numeric_stat(track_stats["p"], float(track.GetP()))
                        update_numeric_stat(track_stats["energy"], float(track.GetEnergy()))
                        update_numeric_stat(track_stats["start_z"], float(track.GetStartZ()))
                        pdg = int(track.GetPdgCode())
                        track_stats["pdg_counts"][pdg] = track_stats["pdg_counts"].get(pdg, 0) + 1

        countable_branches = [name for name, stats in branch_stats.items() if stats["total"] > 0 or stats["nonzero"] > 0]
        print_kv("Countable branches", len(countable_branches))

        if track_stats["total_tracks"] > 0:
            print_section("MCTrack Validation")
            print_kv("Total tracks", track_stats["total_tracks"])
            print_kv("Primary tracks", track_stats["primary_tracks"])
            print_kv("Secondary tracks", track_stats["secondary_tracks"])
            print_kv("Tracks per event", f"{track_stats['total_tracks'] / n_entries:.4g}")
            print_kv("Track momentum", format_stat_summary(track_stats["p"]))
            print_kv("Track energy", format_stat_summary(track_stats["energy"]))
            print_kv("Track start Z", format_stat_summary(track_stats["start_z"]))
            top_pdgs = sorted(track_stats["pdg_counts"].items(), key=lambda item: (-item[1], abs(item[0]), item[0]))[:10]
            print_kv("Top PDG counts", ", ".join(f"{pdg}:{count}" for pdg, count in top_pdgs))

        if scalar_stats:
            print_section("Scalar Branch Validation")
            for branch_name in sorted(scalar_stats):
                print_kv(branch_name, format_stat_summary(scalar_stats[branch_name]))

        print_section("Branch Multiplicity")
        for branch_name in sorted(countable_branches):
            stats = branch_stats[branch_name]
            active = 100.0 * stats["nonzero"] / n_entries
            print_kv(
                branch_name,
                f"total={stats['total']}, mean/event={format_mean_std(n_entries, stats['total'], stats['sum_sq'])},"
                f" active={stats['nonzero']}/{n_entries} ({active:5.1f}%), max={stats['max']}",
                width=22,
            )
