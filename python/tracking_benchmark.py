#!/usr/bin/env python3
# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

"""Tracking performance benchmark metrics for straw tube spectrometer.

Computes track finding efficiency, clone rate, ghost rate, and resolution
metrics by comparing MC truth with reconstructed tracks. Designed to
establish a GenFit baseline and later measure ACTS performance.
"""

from __future__ import annotations

import json
import math
from typing import Any

import ROOT

ROOT.gROOT.SetBatch(True)


def wilson_interval(k: int, n: int) -> float:
    """Wilson score interval half-width for a binomial proportion.

    Parameters
    ----------
    k : int
        Number of successes.
    n : int
        Number of trials.

    Returns
    -------
    float
        Half-width of the 68% Wilson score interval (~1 sigma).
    """
    if n == 0:
        return 0.0
    z = 1.0  # 1-sigma
    p = k / n
    denom = 1 + z**2 / n
    spread = z * math.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / denom
    return spread


class TrackingBenchmark:
    """Compute tracking benchmark metrics from simulation and reconstruction files.

    Parameters
    ----------
    sim_file : str
        Path to MC simulation ROOT file (contains cbmsim tree).
    reco_file : str
        Path to reconstruction ROOT file (contains ship_reco_sim tree).
    geo_file : str
        Path to geometry ROOT file.
    purity_cut : float
        Minimum hit purity fraction for a reco track to be considered matched.
    min_hits : int
        Minimum number of straw hits for reconstructibility.
    min_stations : int
        Minimum number of tracking stations crossed for reconstructibility.
    """

    def __init__(
        self,
        sim_file: str,
        reco_file: str,
        geo_file: str,
        purity_cut: float = 0.70,
        min_hits: int = 25,
        min_stations: int = 3,
    ) -> None:
        self.purity_cut = purity_cut
        self.min_hits = min_hits
        self.min_stations = min_stations

        self.f_sim = ROOT.TFile.Open(sim_file, "read")
        self.sim_tree = self.f_sim["cbmsim"]

        self.f_reco = ROOT.TFile.Open(reco_file, "read")
        self.reco_tree = self.f_reco["ship_reco_sim"]

        self.f_geo = ROOT.TFile.Open(geo_file, "read")

        self.PDG = ROOT.TDatabasePDG.Instance()

        self.metrics: dict[str, Any] = {}
        self._histos: dict[str, Any] = {}

    def _is_reconstructible(self, mc_track_id: int) -> bool:
        """Check if an MC particle meets reconstructibility criteria.

        A particle is reconstructible if it is a charged primary with
        hits in >= min_stations tracking stations and >= min_hits total
        straw hits. This matches the cuts in shipDigiReco.findTracks().
        """
        mc_track = self.sim_tree.MCTrack[mc_track_id]

        # Must be primary (no mother)
        if mc_track.GetMotherId() >= 0:
            return False

        # Must be charged
        pdg_code = mc_track.GetPdgCode()
        particle = self.PDG.GetParticle(pdg_code)
        if particle is None or particle.Charge() == 0:
            return False

        # Count hits per station
        stations: set[int] = set()
        n_hits = 0
        for hit in self.sim_tree.strawtubesPoint:
            if hit.GetTrackID() != mc_track_id:
                continue
            n_hits += 1
            det_id = hit.GetDetectorID()
            station = int(det_id // 1_000_000)
            stations.add(station)

        return n_hits >= self.min_hits and len(stations) >= self.min_stations

    def _get_ptruth_first(self, mc_track_id: int) -> tuple[float, float, float, float]:
        """Get MC truth momentum at the first straw hit.

        Follows the pattern from macro/ShipAna.py:getPtruthFirst().
        """
        for hit in self.sim_tree.strawtubesPoint:
            if hit.GetTrackID() == mc_track_id:
                px, py, pz = hit.GetPx(), hit.GetPy(), hit.GetPz()
                p = math.sqrt(px**2 + py**2 + pz**2)
                return p, px, py, pz
        return -1.0, -1.0, -1.0, -1.0

    def _get_truth_pos_first(self, mc_track_id: int) -> tuple[float, float, float]:
        """Get MC truth position at the first straw hit."""
        for hit in self.sim_tree.strawtubesPoint:
            if hit.GetTrackID() == mc_track_id:
                return hit.GetX(), hit.GetY(), hit.GetZ()
        return 0.0, 0.0, 0.0

    def _get_truth_slopes(self, mc_track_id: int) -> tuple[float, float]:
        """Get MC truth track slopes tx=px/pz, ty=py/pz at first straw hit."""
        for hit in self.sim_tree.strawtubesPoint:
            if hit.GetTrackID() == mc_track_id:
                px, py, pz = hit.GetPx(), hit.GetPy(), hit.GetPz()
                if abs(pz) > 1e-10:
                    return px / pz, py / pz
                return 0.0, 0.0
        return 0.0, 0.0

    def _fracMCsame(self, reco_track_idx: int) -> tuple[float, int]:
        """Get the hit purity and dominant MC track ID for a reco track.

        Uses the Tracklets branch to access hit indices, then checks
        which MC track contributed most hits.
        """
        tracklet = self.reco_tree.Tracklets[reco_track_idx]
        hit_indices = tracklet.getList()

        track_counts: dict[int, int] = {}
        n_hits = 0
        for idx in hit_indices:
            mc_id = self.sim_tree.strawtubesPoint[idx].GetTrackID()
            track_counts[mc_id] = track_counts.get(mc_id, 0) + 1
            n_hits += 1

        if not track_counts:
            return 0.0, -999

        tmax = max(track_counts, key=track_counts.__getitem__)
        frac = track_counts[tmax] / n_hits if n_hits > 0 else 0.0
        return frac, tmax

    def compute_metrics(self) -> dict[str, Any]:
        """Run the full benchmark analysis over all events.

        Returns
        -------
        dict
            Dictionary of metrics compatible with compare_metrics.py format.
        """
        n_events = self.sim_tree.GetEntries()
        n_reco_events = self.reco_tree.GetEntries()
        if n_events != n_reco_events:
            print(f"WARNING: sim has {n_events} events, reco has {n_reco_events}")
        n_events = min(n_events, n_reco_events)

        # Book histograms
        h_dp_over_p = ROOT.TH1D(
            "h_dp_over_p",
            "Momentum resolution;(p_{reco} #minus p_{truth}) / p_{truth};Entries",
            100,
            -0.5,
            0.5,
        )
        h_dp_vs_p = ROOT.TH2D(
            "h_dp_vs_p",
            "Momentum resolution vs p_{truth};p_{truth} [GeV/c];(p_{reco} #minus p_{truth}) / p_{truth}",
            50,
            0,
            120,
            100,
            -0.5,
            0.5,
        )
        h_dx = ROOT.TH1D(
            "h_dx",
            "x resolution at first hit;x_{reco} #minus x_{truth} [cm];Entries",
            100,
            -5.0,
            5.0,
        )
        h_dy = ROOT.TH1D(
            "h_dy",
            "y resolution at first hit;y_{reco} #minus y_{truth} [cm];Entries",
            100,
            -5.0,
            5.0,
        )
        h_dtx = ROOT.TH1D(
            "h_dtx",
            "Slope t_{x} resolution;t_{x,reco} #minus t_{x,truth} (t_{x} = p_{x}/p_{z});Entries",
            100,
            -0.01,
            0.01,
        )
        h_dty = ROOT.TH1D(
            "h_dty",
            "Slope t_{y} resolution;t_{y,reco} #minus t_{y,truth} (t_{y} = p_{y}/p_{z});Entries",
            100,
            -0.01,
            0.01,
        )
        h_hit_residual = ROOT.TH1D(
            "h_hit_residual",
            "Unbiased hit residual;drift distance residual [cm];Entries",
            100,
            -0.2,
            0.2,
        )
        h_hit_pull = ROOT.TH1D(
            "h_hit_pull",
            "Unbiased hit pull;(residual) / #sigma;Entries",
            100,
            -5.0,
            5.0,
        )
        h_chi2ndf = ROOT.TH1D("h_chi2ndf", "#chi^{2}/ndf;#chi^{2}/ndf;Entries", 100, 0, 20)
        h_p_truth = ROOT.TH1D("h_p_truth", "p_{truth} (reconstructible);p [GeV/c];Entries", 50, 0, 120)
        h_p_matched = ROOT.TH1D("h_p_matched", "p_{truth} (matched);p [GeV/c];Entries", 50, 0, 120)

        # Counters
        n_reconstructible = 0
        n_matched_mc = 0  # reconstructible MC particles with >= 1 matched reco track
        n_total_reco = 0
        n_matched_reco = 0  # reco tracks passing purity cut
        n_clone_reco = 0  # extra matches beyond the first for same MC particle

        for i_event in range(n_events):
            self.sim_tree.GetEvent(i_event)
            self.reco_tree.GetEvent(i_event)

            # Find reconstructible MC particles
            reconstructible_ids: set[int] = set()
            n_mc_tracks = len(self.sim_tree.MCTrack)
            for mc_id in range(n_mc_tracks):
                if self._is_reconstructible(mc_id):
                    reconstructible_ids.add(mc_id)
                    p_truth, _, _, _ = self._get_ptruth_first(mc_id)
                    if p_truth > 0:
                        h_p_truth.Fill(p_truth)

            n_reconstructible += len(reconstructible_ids)

            # Match reco tracks to MC
            n_reco = self.reco_tree.FitTracks.size()
            n_total_reco += n_reco

            # Track which MC particles have been matched in this event
            matched_mc_this_event: set[int] = set()

            for i_reco in range(n_reco):
                track = self.reco_tree.FitTracks[i_reco]
                fit_status = track.getFitStatus()
                if not fit_status.isFitConverged():
                    continue

                ndf = fit_status.getNdf()
                if ndf <= 0:
                    continue
                chi2 = fit_status.getChi2() / ndf
                h_chi2ndf.Fill(chi2)

                # Use fitTrack2MC for the MC link (already computed by fracMCsame)
                mc_id = self.reco_tree.fitTrack2MC[i_reco]

                # Recompute purity to apply our cut
                frac, _dominant_id = self._fracMCsame(i_reco)

                if frac < self.purity_cut:
                    # Ghost track
                    continue

                n_matched_reco += 1

                if mc_id in reconstructible_ids:
                    if mc_id not in matched_mc_this_event:
                        matched_mc_this_event.add(mc_id)
                    else:
                        n_clone_reco += 1

                    # Resolution histograms (use first match only for resolution)
                    p_truth, _, _, _ = self._get_ptruth_first(mc_id)
                    x_t, y_t, _ = self._get_truth_pos_first(mc_id)
                    tx_t, ty_t = self._get_truth_slopes(mc_id)

                    if p_truth > 0:
                        try:
                            fitted_state = track.getFittedState()
                            p_reco = fitted_state.getMomMag()
                            mom = fitted_state.getMom()
                            pos = fitted_state.getPos()

                            dp_over_p = (p_reco - p_truth) / p_truth
                            h_dp_over_p.Fill(dp_over_p)
                            h_dp_vs_p.Fill(p_truth, dp_over_p)

                            h_dx.Fill(pos.X() - x_t)
                            h_dy.Fill(pos.Y() - y_t)

                            pz_reco = mom.Z()
                            if abs(pz_reco) > 1e-10:
                                tx_reco = mom.X() / pz_reco
                                ty_reco = mom.Y() / pz_reco
                                h_dtx.Fill(tx_reco - tx_t)
                                h_dty.Fill(ty_reco - ty_t)

                            h_p_matched.Fill(p_truth)
                        except Exception:
                            pass

                    # Per-hit unbiased residuals and pulls
                    n_meas = track.getNumPointsWithMeasurement()
                    for i_hit in range(n_meas):
                        try:
                            tp = track.getPointWithMeasurement(i_hit)
                            fitter_info = tp.getFitterInfo()
                            if fitter_info is None:
                                continue
                            res = fitter_info.getResidual(0, False, False)
                            res_val = res.getState()(0)
                            res_cov = res.getCov()(0, 0)
                            h_hit_residual.Fill(res_val)
                            if res_cov > 0:
                                h_hit_pull.Fill(res_val / math.sqrt(res_cov))
                        except Exception:
                            continue

            n_matched_mc += len(matched_mc_this_event)

        # Compute metrics
        n_ghost_reco = n_total_reco - n_matched_reco

        efficiency = n_matched_mc / n_reconstructible if n_reconstructible > 0 else 0.0
        efficiency_unc = wilson_interval(n_matched_mc, n_reconstructible)

        clone_rate = n_clone_reco / n_matched_reco if n_matched_reco > 0 else 0.0
        clone_rate_unc = wilson_interval(n_clone_reco, n_matched_reco)

        ghost_rate = n_ghost_reco / n_total_reco if n_total_reco > 0 else 0.0
        ghost_rate_unc = wilson_interval(n_ghost_reco, n_total_reco)

        # Fit dp/p with Gaussian
        dp_p_sigma = h_dp_over_p.GetRMS()
        dp_p_sigma_unc = h_dp_over_p.GetRMSError()
        if h_dp_over_p.GetEntries() > 20:
            fit_result = h_dp_over_p.Fit("gaus", "QS")
            if fit_result and int(fit_result) == 0:
                dp_p_sigma = fit_result.Parameter(2)
                dp_p_sigma_unc = fit_result.ParError(2)

        # Fit hit pull with Gaussian
        hit_pull_mean = h_hit_pull.GetMean()
        hit_pull_mean_unc = h_hit_pull.GetMeanError()
        hit_pull_sigma = h_hit_pull.GetRMS()
        hit_pull_sigma_unc = h_hit_pull.GetRMSError()
        if h_hit_pull.GetEntries() > 50:
            pull_fit = h_hit_pull.Fit("gaus", "QS")
            if pull_fit and int(pull_fit) == 0:
                hit_pull_mean = pull_fit.Parameter(1)
                hit_pull_mean_unc = pull_fit.ParError(1)
                hit_pull_sigma = pull_fit.Parameter(2)
                hit_pull_sigma_unc = pull_fit.ParError(2)

        self.metrics = {
            "tracking_benchmark": {
                "n_events": {"value": int(n_events), "compare": "exact"},
                "n_reconstructible": {"value": int(n_reconstructible), "compare": "exact"},
                "n_total_reco": {"value": int(n_total_reco), "compare": "exact"},
                "efficiency": {
                    "value": round(efficiency, 6),
                    "uncertainty": round(efficiency_unc, 6),
                    "compare": "statistical",
                },
                "clone_rate": {
                    "value": round(clone_rate, 6),
                    "uncertainty": round(clone_rate_unc, 6),
                    "compare": "statistical",
                },
                "ghost_rate": {
                    "value": round(ghost_rate, 6),
                    "uncertainty": round(ghost_rate_unc, 6),
                    "compare": "statistical",
                },
                "dp_over_p_sigma": {
                    "value": round(dp_p_sigma, 6),
                    "uncertainty": round(dp_p_sigma_unc, 6),
                    "compare": "statistical",
                },
                "dx_rms": {
                    "value": round(h_dx.GetRMS(), 6),
                    "uncertainty": round(h_dx.GetRMSError(), 6),
                    "compare": "statistical",
                },
                "dy_rms": {
                    "value": round(h_dy.GetRMS(), 6),
                    "uncertainty": round(h_dy.GetRMSError(), 6),
                    "compare": "statistical",
                },
                "dtx_rms": {
                    "value": round(h_dtx.GetRMS(), 6),
                    "uncertainty": round(h_dtx.GetRMSError(), 6),
                    "compare": "statistical",
                },
                "dty_rms": {
                    "value": round(h_dty.GetRMS(), 6),
                    "uncertainty": round(h_dty.GetRMSError(), 6),
                    "compare": "statistical",
                },
                "hit_residual_rms": {
                    "value": round(h_hit_residual.GetRMS(), 6),
                    "uncertainty": round(h_hit_residual.GetRMSError(), 6),
                    "compare": "statistical",
                },
                "hit_pull_mean": {
                    "value": round(hit_pull_mean, 6),
                    "uncertainty": round(hit_pull_mean_unc, 6),
                    "compare": "statistical",
                },
                "hit_pull_sigma": {
                    "value": round(hit_pull_sigma, 6),
                    "uncertainty": round(hit_pull_sigma_unc, 6),
                    "compare": "statistical",
                },
            }
        }

        self._histos = {
            "h_dp_over_p": h_dp_over_p,
            "h_dp_vs_p": h_dp_vs_p,
            "h_dx": h_dx,
            "h_dy": h_dy,
            "h_dtx": h_dtx,
            "h_dty": h_dty,
            "h_hit_residual": h_hit_residual,
            "h_hit_pull": h_hit_pull,
            "h_chi2ndf": h_chi2ndf,
            "h_p_truth": h_p_truth,
            "h_p_matched": h_p_matched,
        }

        return self.metrics

    def save_json(self, output_path: str) -> None:
        """Save metrics to JSON file."""
        with open(output_path, "w") as f:
            json.dump(self.metrics, f, indent=2)
        print(f"Metrics saved to {output_path}")

    def save_histograms(self, output_path: str) -> None:
        """Save detailed histograms to a ROOT file."""
        f_out = ROOT.TFile.Open(output_path, "recreate")
        for name, hist in self._histos.items():
            hist.Write(name)
        f_out.Close()
        print(f"Histograms saved to {output_path}")

    def print_summary(self) -> None:
        """Print a human-readable summary of the benchmark results."""
        if not self.metrics:
            print("No metrics computed yet. Call compute_metrics() first.")
            return
        m = self.metrics["tracking_benchmark"]
        print("\n=== Tracking Benchmark Summary ===")
        print(f"  Events:           {m['n_events']['value']}")
        print(f"  Reconstructible:  {m['n_reconstructible']['value']}")
        print(f"  Total reco:       {m['n_total_reco']['value']}")
        print(f"  Efficiency:       {m['efficiency']['value']:.4f} +/- {m['efficiency']['uncertainty']:.4f}")
        print(f"  Clone rate:       {m['clone_rate']['value']:.4f} +/- {m['clone_rate']['uncertainty']:.4f}")
        print(f"  Ghost rate:       {m['ghost_rate']['value']:.4f} +/- {m['ghost_rate']['uncertainty']:.4f}")
        print(f"  dp/p sigma:       {m['dp_over_p_sigma']['value']:.6f} +/- {m['dp_over_p_sigma']['uncertainty']:.6f}")
        print(f"  dx RMS:           {m['dx_rms']['value']:.4f} +/- {m['dx_rms']['uncertainty']:.4f} cm")
        print(f"  dy RMS:           {m['dy_rms']['value']:.4f} +/- {m['dy_rms']['uncertainty']:.4f} cm")
        print(f"  dtx RMS:          {m['dtx_rms']['value']:.6f} +/- {m['dtx_rms']['uncertainty']:.6f}")
        print(f"  dty RMS:          {m['dty_rms']['value']:.6f} +/- {m['dty_rms']['uncertainty']:.6f}")
        print(
            f"  Hit resid RMS:    {m['hit_residual_rms']['value']:.6f} +/- {m['hit_residual_rms']['uncertainty']:.6f} cm"
        )
        print(f"  Hit pull mean:    {m['hit_pull_mean']['value']:.4f} +/- {m['hit_pull_mean']['uncertainty']:.4f}")
        print(f"  Hit pull sigma:   {m['hit_pull_sigma']['value']:.4f} +/- {m['hit_pull_sigma']['uncertainty']:.4f}")
        print("==================================\n")

    def __del__(self) -> None:
        for f in [self.f_sim, self.f_reco, self.f_geo]:
            if f and f.IsOpen():
                f.Close()
