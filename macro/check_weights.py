#!/usr/bin/env python
"""Check which MCTrack carries the per-spill weight."""

import sys

import ROOT

ROOT.gSystem.Load("libShipData")

ROOT.gInterpreter.Declare("""
struct WeightInfo {
    double w_track0;      // MCTrack[0] weight
    double w_first_muon;  // first muon's weight (-1 if no muon)
    double w_max;         // max weight across all tracks
    int first_muon_idx;   // index of first muon (-1 if none)
};

WeightInfo extract_weights(const std::vector<ShipMCTrack>& tracks) {
    WeightInfo info{0, -1, 0, -1};
    if (tracks.empty()) return info;
    info.w_track0 = tracks[0].GetWeight();
    for (int i = 0; i < (int)tracks.size(); ++i) {
        double w = tracks[i].GetWeight();
        if (w > info.w_max) info.w_max = w;
        if (info.first_muon_idx < 0 && abs(tracks[i].GetPdgCode()) == 13) {
            info.first_muon_idx = i;
            info.w_first_muon = w;
        }
    }
    return info;
}
""")

f = sys.argv[1] if len(sys.argv) > 1 else "concat.root"
rdf = ROOT.RDataFrame("cbmsim", f)
rdf2 = (
    rdf.Define("wi", "extract_weights(MCTrack)")
    .Define("w0", "wi.w_track0")
    .Define("w_mu", "wi.w_first_muon")
    .Define("w_max", "wi.w_max")
    .Define("mu_idx", "wi.first_muon_idx")
)

stats_w0 = rdf2.Stats("w0")
stats_wmu = rdf2.Stats("w_mu")
stats_wmax = rdf2.Stats("w_max")
h_wmu = rdf2.Filter("mu_idx >= 0").Histo1D(("h_wmu", "First muon weight;weight;events", 100, 0, 1000), "w_mu")

print(f"\n{'MCTrack[0] weight':30s}: mean={stats_w0.GetValue().GetMean():.4f}  rms={stats_w0.GetValue().GetRMS():.4f}")
print(f"{'First muon weight':30s}: mean={stats_wmu.GetValue().GetMean():.4f}  rms={stats_wmu.GetValue().GetRMS():.4f}")
print(f"{'Max weight in event':30s}: mean={stats_wmax.GetValue().GetMean():.4f}  rms={stats_wmax.GetValue().GetRMS():.4f}")

# Print a few example values
sample = rdf2.Range(10).AsNumpy(columns=["w0", "w_mu", "w_max", "mu_idx"])
print("\nFirst 10 events:")
print(f"  {'w0':>10s} {'w_mu':>10s} {'w_max':>10s} {'mu_idx':>8s}")
for i in range(len(sample["w0"])):
    print(f"  {sample['w0'][i]:10.2f} {sample['w_mu'][i]:10.2f} {sample['w_max'][i]:10.2f} {sample['mu_idx'][i]:8.0f}")
