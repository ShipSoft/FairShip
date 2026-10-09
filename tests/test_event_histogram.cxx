// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

// EventHistogram must give event-level errors: per-event bin sums are the
// observations, and the stored objects must merge like the events they hold.

#include <TFile.h>
#include <TFileMerger.h>
#include <TH1D.h>
#include <TRandom3.h>

#include <cmath>
#include <cstdio>
#include <iostream>
#include <memory>
#include <vector>

#include "EventHistogram.h"

namespace {

int failures = 0;

void Check(bool ok, const char* what, double got, double want) {
  if (!ok) {
    std::cerr << "FAIL " << what << ": got " << got << ", want " << want
              << std::endl;
    ++failures;
  }
}

void CheckClose(double got, double want, double rel, const char* what) {
  const double scale = std::max(std::abs(want), 1e-300);
  Check(std::abs(got - want) <= rel * scale, what, got, want);
}

// Events with n clones of weight 1/n near a common x: the clones of an event
// are maximally correlated, as for split decays.
struct Sample {
  std::vector<std::vector<std::pair<double, double>>> events;
};

Sample MakeSample(unsigned seed, int nEvents) {
  TRandom3 rng(seed);
  Sample s;
  for (int e = 0; e < nEvents; ++e) {
    std::vector<std::pair<double, double>> branches;
    if (rng.Uniform() < 0.3) {
      const int n = 20;
      const double x0 = rng.Uniform(0., 10.);
      for (int i = 0; i < n; ++i) {
        branches.emplace_back(x0 + rng.Gaus(0., 0.3), 1. / n);
      }
    }
    s.events.push_back(branches);
  }
  return s;
}

void FillSample(EventHistogram& h, const Sample& s, unsigned run) {
  for (size_t e = 0; e < s.events.size(); ++e) {
    if (s.events[e].empty()) {
      h.AddEmptyEvents(1);
      continue;
    }
    for (const auto& [x, w] : s.events[e]) h.Fill(x, w);
    h.EndEvent(EventHistogram::MakeEventKey(run, e));
  }
}

}  // namespace

int main() {
  const int nbins = 10;
  const Sample a = MakeSample(1, 4000);
  const Sample b = MakeSample(2, 3000);

  // Expected per-event sums, by hand.
  TH1D binning("binning", "", nbins, 0., 10.);
  std::vector<double> sumT(nbins + 2, 0.), sumT2(nbins + 2, 0.),
      sumW2(nbins + 2, 0.);
  for (const auto& ev : a.events) {
    std::vector<double> t(nbins + 2, 0.);
    for (const auto& [x, w] : ev) {
      const int bin = binning.GetXaxis()->FindFixBin(x);
      t[bin] += w;
      sumW2[bin] += w * w;
    }
    for (int i = 0; i < nbins + 2; ++i) {
      sumT[i] += t[i];
      sumT2[i] += t[i] * t[i];
    }
  }

  EventHistogram ha("x", "test;x", nbins, 0., 10., kTRUE, 200);
  FillSample(ha, a, 1);
  Check(ha.GetNEvents() == 4000, "event count", ha.GetNEvents(), 4000);

  std::unique_ptr<TH1D> res(ha.MakeResult());
  std::unique_ptr<TH1D> naive(ha.MakeNaive());
  const double n = 4000.;
  double maxRatio = 0.;
  for (int i = 1; i <= nbins; ++i) {
    const double mean = sumT[i] / n;
    const double err = std::sqrt((sumT2[i] / n - mean * mean) / (n - 1));
    CheckClose(res->GetBinContent(i), mean, 1e-12, "content");
    CheckClose(res->GetBinError(i), err, 1e-9, "per-event error");
    CheckClose(naive->GetBinError(i), std::sqrt(sumW2[i]) / n, 1e-9,
               "naive error");
    maxRatio = std::max(maxRatio, res->GetBinError(i) / naive->GetBinError(i));
  }
  // 20 clones per event, mostly in one or two bins: the naive error is far
  // too small.
  Check(maxRatio > 2.5, "per-event / naive error ratio", maxRatio, 2.5);

  // Covariance: diagonal equals the squared errors, neighbours are positive.
  const TMatrixDSym cov = ha.GetCovariance();
  for (int i = 1; i <= nbins; ++i) {
    CheckClose(cov(i - 1, i - 1), std::pow(res->GetBinError(i), 2), 1e-9,
               "covariance diagonal");
  }
  Check(cov(4, 5) > 0., "neighbour covariance positive", cov(4, 5), 0.);

  // Bootstrap reproduces the per-event errors within its own precision.
  const std::vector<double> boot = ha.GetBootstrapErrors();
  for (int i = 1; i <= nbins; ++i) {
    CheckClose(boot[i - 1], res->GetBinError(i), 0.3, "bootstrap error");
  }

  // Replica weights are Poisson(1) and depend only on key and replica.
  double s1 = 0., s2 = 0.;
  const int nk = 200000;
  for (int k = 0; k < nk; ++k) {
    const double r = EventHistogram::ReplicaWeight(k, 3);
    s1 += r;
    s2 += r * r;
  }
  CheckClose(s1 / nk, 1., 0.01, "replica weight mean");
  CheckClose(s2 / nk - std::pow(s1 / nk, 2), 1., 0.02, "replica weight var");
  Check(EventHistogram::ReplicaWeight(42, 7) ==
            EventHistogram::ReplicaWeight(42, 7),
        "replica weight deterministic", 0, 0);

  // Add() and a file merge (as hadd does) give the same as one accumulator.
  EventHistogram hb("x", "test;x", nbins, 0., 10., kTRUE, 200);
  FillSample(hb, b, 2);
  EventHistogram hab("x", "test;x", nbins, 0., 10., kTRUE, 200);
  FillSample(hab, a, 1);
  FillSample(hab, b, 2);
  {
    TFile fa("test_event_histogram_a.root", "RECREATE");
    ha.Write(&fa);
    TFile fb("test_event_histogram_b.root", "RECREATE");
    hb.Write(&fb);
  }
  ha.Add(hb);
  {
    TFileMerger merger(kFALSE);
    merger.OutputFile("test_event_histogram_ab.root", "RECREATE");
    merger.AddFile("test_event_histogram_a.root");
    merger.AddFile("test_event_histogram_b.root");
    Check(merger.Merge(), "file merge", 0, 1);
  }
  TFile fab("test_event_histogram_ab.root");
  std::unique_ptr<EventHistogram> merged = EventHistogram::Read(&fab, "x");
  Check(merged != nullptr, "read merged", 0, 1);
  if (merged) {
    Check(merged->GetNEvents() == 7000, "merged event count",
          merged->GetNEvents(), 7000);
    std::unique_ptr<TH1D> rAdd(ha.MakeResult("rAdd"));
    std::unique_ptr<TH1D> rAll(hab.MakeResult("rAll"));
    std::unique_ptr<TH1D> rMerged(merged->MakeResult("rMerged"));
    const std::vector<double> bAll = hab.GetBootstrapErrors();
    const std::vector<double> bMerged = merged->GetBootstrapErrors();
    for (int i = 1; i <= nbins; ++i) {
      CheckClose(rAdd->GetBinError(i), rAll->GetBinError(i), 1e-9,
                 "Add() error");
      CheckClose(rMerged->GetBinContent(i), rAll->GetBinContent(i), 1e-9,
                 "merged content");
      CheckClose(rMerged->GetBinError(i), rAll->GetBinError(i), 1e-9,
                 "merged error");
      CheckClose(bMerged[i - 1], bAll[i - 1], 1e-9, "merged bootstrap");
    }
  }
  fab.Close();
  std::remove("test_event_histogram_a.root");
  std::remove("test_event_histogram_b.root");
  std::remove("test_event_histogram_ab.root");

  if (failures) {
    std::cerr << failures << " check(s) failed" << std::endl;
    return 1;
  }
  return 0;
}
