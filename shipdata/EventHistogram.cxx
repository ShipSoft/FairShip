// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#include "EventHistogram.h"

#include <algorithm>
#include <cmath>
#include <string>

#include "FairLogger.h"
#include "TArrayD.h"
#include "TAxis.h"
#include "TParameter.h"

namespace {

std::vector<Double_t> AxisEdges(const TAxis* axis) {
  std::vector<Double_t> edges;
  for (Int_t i = 1; i <= axis->GetNbins(); ++i) {
    edges.push_back(axis->GetBinLowEdge(i));
  }
  edges.push_back(axis->GetBinUpEdge(axis->GetNbins()));
  return edges;
}

std::string Suffixed(const char* name, const char* suffix) {
  return std::string(name) + suffix;
}

template <class T>
std::unique_ptr<T> DetachedClone(const T* h) {
  std::unique_ptr<T> clone(static_cast<T*>(h->Clone()));
  clone->SetDirectory(nullptr);
  return clone;
}

ULong64_t SplitMix64(ULong64_t x) {
  x += 0x9E3779B97F4A7C15ULL;
  x = (x ^ (x >> 30U)) * 0xBF58476D1CE4E5B9ULL;
  x = (x ^ (x >> 27U)) * 0x94D049BB133111EBULL;
  return x ^ (x >> 31U);
}

}  // namespace

EventHistogram::EventHistogram(const char* name, const char* title, Int_t nbins,
                               Double_t xlow, Double_t xup, Bool_t covariance,
                               Int_t nReplicas)
    : fSum(new TH1D(name, title, nbins, xlow, xup)) {
  Init(covariance, nReplicas);
}

EventHistogram::EventHistogram(const char* name, const char* title, Int_t nbins,
                               const Double_t* edges, Bool_t covariance,
                               Int_t nReplicas)
    : fSum(new TH1D(name, title, nbins, edges)) {
  Init(covariance, nReplicas);
}

EventHistogram::~EventHistogram() = default;

void EventHistogram::Init(Bool_t covariance, Int_t nReplicas) {
  fSum->SetDirectory(nullptr);
  fSum->Sumw2();
  const std::string name = fSum->GetName();
  fNaive.reset(dynamic_cast<TH1D*>(
      fSum->Clone(Suffixed(name.c_str(), "_naive").c_str())));
  fNaive->SetDirectory(nullptr);
  const Int_t nbins = fSum->GetNbinsX();
  const std::vector<Double_t> edges = AxisEdges(fSum->GetXaxis());
  if (covariance) {
    fCov = std::make_unique<TH2D>(Suffixed(name.c_str(), "_cov").c_str(),
                                  "sum over events of t_a t_b", nbins,
                                  edges.data(), nbins, edges.data());
    fCov->SetDirectory(nullptr);
  }
  if (nReplicas > 0) {
    fBoot = std::make_unique<TH2D>(Suffixed(name.c_str(), "_boot").c_str(),
                                   "bootstrap replicas;;replica", nbins,
                                   edges.data(), nReplicas, 0., nReplicas);
    fBoot->SetDirectory(nullptr);
  }
  InitEventBuffers();
}

void EventHistogram::InitEventBuffers() {
  fCurrent.assign(fSum->GetNbinsX() + 2, 0.);
  fIsTouched.assign(fSum->GetNbinsX() + 2, false);
}

void EventHistogram::Fill(Double_t x, Double_t w) {
  const Int_t bin = fSum->GetXaxis()->FindFixBin(x);
  if (!fIsTouched[bin]) {
    fIsTouched[bin] = true;
    fTouched.push_back(bin);
  }
  fCurrent[bin] += w;
  fNaive->AddBinContent(bin, w);
  (*fNaive->GetSumw2())[bin] += w * w;
}

void EventHistogram::EndEvent(ULong64_t eventKey) {
  TArrayD& sumw2 = *fSum->GetSumw2();
  const Int_t nbins = fSum->GetNbinsX();
  for (const Int_t b : fTouched) {
    const Double_t t = fCurrent[b];
    // AddBinContent leaves the sum of squared weights alone, so the per-event
    // square is added by hand: this is what makes the stored error per event.
    fSum->AddBinContent(b, t);
    sumw2[b] += t * t;
  }
  // Covariance and bootstrap cover the in-range bins, moved to the front.
  const auto begin = fTouched.begin();
  const auto end =
      std::partition(fTouched.begin(), fTouched.end(),
                     [nbins](Int_t b) { return b >= 1 && b <= nbins; });
  if (fCov) {
    for (auto a = begin; a != end; ++a) {
      for (auto b = begin; b != end; ++b) {
        fCov->AddBinContent(fCov->GetBin(*a, *b), fCurrent[*a] * fCurrent[*b]);
      }
    }
  }
  if (fBoot && begin != end) {
    for (Int_t r = 0; r < fBoot->GetNbinsY(); ++r) {
      const Int_t k = ReplicaWeight(eventKey, r);
      if (k == 0) continue;
      for (auto b = begin; b != end; ++b) {
        fBoot->AddBinContent(fBoot->GetBin(*b, r + 1), k * fCurrent[*b]);
      }
    }
  }
  for (const Int_t b : fTouched) {
    fCurrent[b] = 0.;
    fIsTouched[b] = false;
  }
  fTouched.clear();
  ++fNEvents;
  fSum->SetEntries(fNEvents);
}

void EventHistogram::AddEmptyEvents(Long64_t n) {
  fNEvents += n;
  fSum->SetEntries(fNEvents);
}

void EventHistogram::Add(const EventHistogram& other) {
  CheckClosed("Add");
  other.CheckClosed("Add");
  const char* problem = nullptr;
  if (AxisEdges(other.fSum->GetXaxis()) != AxisEdges(fSum->GetXaxis())) {
    problem = "binning";
  } else if (!fCov != !other.fCov) {
    problem = "covariance";
  } else if (!fBoot != !other.fBoot ||
             (fBoot && fBoot->GetNbinsY() != other.fBoot->GetNbinsY())) {
    problem = "number of bootstrap replicas";
  }
  if (problem) {
    LOG(error) << "EventHistogram::Add: " << problem << " of "
               << other.fSum->GetName() << " differs from " << fSum->GetName()
               << ", not merged";
    return;
  }
  fSum->Add(other.fSum.get());
  fNaive->Add(other.fNaive.get());
  if (fCov) fCov->Add(other.fCov.get());
  if (fBoot) fBoot->Add(other.fBoot.get());
  fNEvents += other.fNEvents;
  fSum->SetEntries(fNEvents);
}

void EventHistogram::CheckClosed(const char* where) const {
  if (HasOpenEvent()) {
    LOG(warning) << "EventHistogram::" << where << " on " << fSum->GetName()
                 << " with an open event; call EndEvent() first";
  }
}

TH1D* EventHistogram::MakePerEvent(const char* name, const char* suffix) const {
  const std::string newName =
      name ? std::string(name) : Suffixed(fSum->GetName(), suffix);
  auto* h = dynamic_cast<TH1D*>(fSum->Clone(newName.c_str()));
  h->SetDirectory(nullptr);
  h->Reset();
  return h;
}

TH1D* EventHistogram::MakeResult(const char* name) const {
  CheckClosed("MakeResult");
  TH1D* h = MakePerEvent(name, "_result");
  if (fNEvents <= 0) return h;
  const Double_t n = fNEvents;
  const TArrayD& sumw2 = *fSum->GetSumw2();
  for (Int_t b = 0; b <= fSum->GetNbinsX() + 1; ++b) {
    const Double_t mean = fSum->GetBinContent(b) / n;
    const Double_t var =
        n > 1 ? (sumw2[b] / n - mean * mean) / (n - 1) : sumw2[b] / (n * n);
    h->SetBinContent(b, mean);
    h->SetBinError(b, std::sqrt(std::max(var, 0.)));
  }
  h->SetEntries(fNEvents);
  return h;
}

TH1D* EventHistogram::MakeNaive(const char* name) const {
  CheckClosed("MakeNaive");
  TH1D* h = MakePerEvent(name, "_naive_result");
  if (fNEvents <= 0) return h;
  const Double_t n = fNEvents;
  const TArrayD& sumw2 = *fNaive->GetSumw2();
  for (Int_t b = 0; b <= fSum->GetNbinsX() + 1; ++b) {
    h->SetBinContent(b, fNaive->GetBinContent(b) / n);
    h->SetBinError(b, std::sqrt(sumw2[b]) / n);
  }
  return h;
}

TH1D* EventHistogram::MakeNeff(const char* name) const {
  CheckClosed("MakeNeff");
  TH1D* h = MakePerEvent(name, "_neff");
  const TArrayD& sumw2 = *fSum->GetSumw2();
  for (Int_t b = 0; b <= fSum->GetNbinsX() + 1; ++b) {
    const Double_t s = fSum->GetBinContent(b);
    h->SetBinContent(b, sumw2[b] > 0 ? s * s / sumw2[b] : 0.);
  }
  return h;
}

TMatrixDSym EventHistogram::GetCovariance() const {
  CheckClosed("GetCovariance");
  const Int_t nbins = fSum->GetNbinsX();
  TMatrixDSym cov(nbins);
  if (!fCov) {
    LOG(error) << "EventHistogram " << fSum->GetName()
               << " was created without covariance";
    return cov;
  }
  const Double_t n = fNEvents;
  if (n < 2) return cov;
  for (Int_t a = 1; a <= nbins; ++a) {
    for (Int_t b = 1; b <= nbins; ++b) {
      const Double_t ma = fSum->GetBinContent(a) / n;
      const Double_t mb = fSum->GetBinContent(b) / n;
      cov(a - 1, b - 1) = (fCov->GetBinContent(a, b) / n - ma * mb) / (n - 1);
    }
  }
  return cov;
}

std::vector<Double_t> EventHistogram::GetBootstrapErrors() const {
  CheckClosed("GetBootstrapErrors");
  const Int_t nbins = fSum->GetNbinsX();
  std::vector<Double_t> errors(nbins, 0.);
  if (!fBoot || fBoot->GetNbinsY() < 2 || fNEvents <= 0) {
    LOG(error) << "EventHistogram " << fSum->GetName()
               << " has fewer than two bootstrap replicas";
    return errors;
  }
  const Int_t nrep = fBoot->GetNbinsY();
  for (Int_t b = 1; b <= nbins; ++b) {
    Double_t sum = 0., sum2 = 0.;
    for (Int_t r = 1; r <= nrep; ++r) {
      const Double_t v = fBoot->GetBinContent(b, r) / fNEvents;
      sum += v;
      sum2 += v * v;
    }
    const Double_t mean = sum / nrep;
    errors[b - 1] =
        std::sqrt(std::max((sum2 - nrep * mean * mean) / (nrep - 1), 0.));
  }
  return errors;
}

void EventHistogram::Write(TDirectory* dir) const {
  CheckClosed("Write");
  dir->WriteTObject(fSum.get(), fSum->GetName(), "Overwrite");
  dir->WriteTObject(fNaive.get(), fNaive->GetName(), "Overwrite");
  if (fCov) dir->WriteTObject(fCov.get(), fCov->GetName(), "Overwrite");
  if (fBoot) dir->WriteTObject(fBoot.get(), fBoot->GetName(), "Overwrite");
  const std::string key = Suffixed(fSum->GetName(), "_nevents");
  TParameter<Long64_t> nevents(key.c_str(), fNEvents, '+');
  dir->WriteTObject(&nevents, key.c_str(), "Overwrite");
}

std::unique_ptr<EventHistogram> EventHistogram::Read(TDirectory* dir,
                                                     const char* name) {
  auto* sum = dir->Get<TH1D>(name);
  auto* naive = dir->Get<TH1D>(Suffixed(name, "_naive").c_str());
  auto* nevents =
      dir->Get<TParameter<Long64_t>>(Suffixed(name, "_nevents").c_str());
  if (!sum || !naive || !nevents) {
    LOG(error) << "EventHistogram::Read: " << name << " not found in "
               << dir->GetName();
    return nullptr;
  }
  std::unique_ptr<EventHistogram> h(new EventHistogram());
  h->fSum = DetachedClone(sum);
  h->fNaive = DetachedClone(naive);
  if (auto* cov = dir->Get<TH2D>(Suffixed(name, "_cov").c_str())) {
    h->fCov = DetachedClone(cov);
  }
  if (auto* boot = dir->Get<TH2D>(Suffixed(name, "_boot").c_str())) {
    h->fBoot = DetachedClone(boot);
  }
  h->fNEvents = nevents->GetVal();
  h->InitEventBuffers();
  return h;
}

Int_t EventHistogram::ReplicaWeight(ULong64_t key, Int_t replica) {
  const ULong64_t x = SplitMix64(
      key ^ (static_cast<ULong64_t>(replica + 1) * 0xD1B54A32D192ED03ULL));
  const Double_t u = static_cast<Double_t>(x >> 11U) * 0x1.0p-53;
  // Inversion of the Poisson(1) distribution function.
  static const Double_t p0 = std::exp(-1.);
  Double_t p = p0;
  Double_t cdf = p;
  Int_t k = 0;
  while (u > cdf && k < 20) {
    ++k;
    p /= k;
    cdf += p;
  }
  return k;
}
