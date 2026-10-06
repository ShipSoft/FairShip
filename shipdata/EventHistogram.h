// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#ifndef SHIPDATA_EVENTHISTOGRAM_H_
#define SHIPDATA_EVENTHISTOGRAM_H_

#include <memory>
#include <vector>

#include "Rtypes.h"
#include "TDirectory.h"
#include "TH1D.h"
#include "TH2D.h"
#include "TMatrixDSym.h"

/**
 * Histogram with event-level uncertainties for weighted samples whose entries
 * are correlated within an event, such as the split kaon/pion clones of
 * exitHadronAbsorber.
 *
 * Every branch of an event (clones, split decays, their secondaries) shares
 * the history of the primary interaction, so the branches are not independent
 * entries and sqrt(sum w^2) underestimates the error. The independent unit is
 * the event: the weights of an event are summed per bin first,
 *
 *   t_eb = sum_{i in e, x_i in b} w_i,
 *
 * and the per-event sums are treated as the observations. With N generated
 * events (including those that left no entry), the bin content per event and
 * its error are
 *
 *   mu_b = sum_e t_eb / N,  sigma_b^2 = (sum_e t_eb^2 / N - mu_b^2) / (N - 1).
 *
 * Usage:
 *
 *   EventHistogram h("p_mu", "muon momentum;p (GeV/c)", 40, 0., 400.);
 *   for each event:
 *     for each muon: h.Fill(p, w);
 *     h.EndEvent(EventHistogram::MakeEventKey(run, event));
 *   h.AddEmptyEvents(nGenerated - nWritten);
 *   std::unique_ptr<TH1D> result(h.MakeResult());
 *
 * Write() stores plain ROOT objects that hadd merges correctly: a TH1D whose
 * contents are sum_e t_eb and whose sum of squared weights is sum_e t_eb^2,
 * the same for sqrt(sum w^2) for comparison, optional covariance and
 * bootstrap accumulators, and the number of events. Read() restores the
 * accumulator from them.
 */
class EventHistogram {
 public:
  /// @param covariance  also accumulate sum_e t_ea t_eb for the covariance
  /// @param nReplicas   number of Poisson bootstrap replicas (0 = none)
  EventHistogram(const char* name, const char* title, Int_t nbins,
                 Double_t xlow, Double_t xup, Bool_t covariance = kFALSE,
                 Int_t nReplicas = 0);
  EventHistogram(const char* name, const char* title, Int_t nbins,
                 const Double_t* edges, Bool_t covariance = kFALSE,
                 Int_t nReplicas = 0);
  ~EventHistogram();

  EventHistogram(const EventHistogram&) = delete;
  EventHistogram& operator=(const EventHistogram&) = delete;

  /// Add one branch of the current event.
  void Fill(Double_t x, Double_t w = 1.);
  /// Close the current event. The key seeds the bootstrap replica weights; use
  /// MakeEventKey(run, event) so replicas agree across files and jobs.
  void EndEvent(ULong64_t eventKey = 0);
  /// Generated events that left no entry still count in the normalisation.
  void AddEmptyEvents(Long64_t n);
  /// Merge an accumulator filled with independent events and equal binning.
  void Add(const EventHistogram& other);

  Long64_t GetNEvents() const { return fNEvents; }
  Bool_t HasOpenEvent() const { return !fTouched.empty(); }

  /// Contents per generated event with event-level errors.
  TH1D* MakeResult(const char* name = nullptr) const;
  /// Same contents with sqrt(sum w^2)/N errors, for comparison only.
  TH1D* MakeNaive(const char* name = nullptr) const;
  /// Effective number of independent events per bin, (sum t)^2 / sum t^2.
  /// Below about 20 the error estimate itself becomes unreliable.
  TH1D* MakeNeff(const char* name = nullptr) const;
  /// Covariance of the per-event bin contents (in-range bins only).
  TMatrixDSym GetCovariance() const;
  /// Spread of the bootstrap replicas, per generated event (in-range bins).
  std::vector<Double_t> GetBootstrapErrors() const;

  void Write(TDirectory* dir = gDirectory) const;
  static std::unique_ptr<EventHistogram> Read(TDirectory* dir,
                                              const char* name);

  static ULong64_t MakeEventKey(ULong64_t run, ULong64_t event) {
    return (run << 32) ^ event;
  }
  /// Poisson(1) replica weight, a pure function of key and replica so that
  /// the Python implementation (event_histogram.py) gives the same replicas.
  static Int_t ReplicaWeight(ULong64_t key, Int_t replica);

 private:
  EventHistogram() = default;
  void Init(Bool_t covariance, Int_t nReplicas);
  void CheckClosed(const char* where) const;
  TH1D* MakePerEvent(const char* name, const char* suffix) const;

  std::unique_ptr<TH1D> fSum;      ///< contents sum t, sumw2 sum t^2
  std::unique_ptr<TH1D> fNaive;    ///< contents sum w, sumw2 sum w^2
  std::unique_ptr<TH2D> fCov;      ///< optional: sum t_a t_b
  std::unique_ptr<TH2D> fBoot;     ///< optional: (bin, replica) sum r t
  std::vector<Double_t> fCurrent;  ///< t_b of the open event, incl. flows
  std::vector<Int_t> fTouched;     ///< bins filled in the open event
  Long64_t fNEvents = 0;
};

#endif  // SHIPDATA_EVENTHISTOGRAM_H_
