// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration
//
// The model behind the J/psi generator's data map (jpsi::DataMap) and its
// fits, minimised with Minuit2 (ROOT::Math::Minimizer). Used by
// macro/jpsi/JpsiDataMap.C; tested by tests/test_jpsi_datamap_fit.cxx.
//
// Model for the corrected data in cell i, per POT:
//   P_i = N * sum_{generator events in i} w_ev * exp(d (b1 + b2 d) + c d q)
// with d = DataMapDy(y_true), q = min(pT_true^2, qMax) - q0 per event.
// Parameters: 0 b1, 1 b2, 2 c, 3 ln N. Any subset can be fixed.
// FitResid: chi2 = sum of the squared residuals the caller builds from this
// model (data, its errors and the generator statistics).
// FitTail: the exponent of the forward (1 - |xF|)^n continuation (below).

#ifndef SHIPGEN_JPSIDATAMAPFIT_H_
#define SHIPGEN_JPSIDATAMAPFIT_H_

#include <algorithm>
#include <cmath>
#include <functional>
#include <memory>
#include <stdexcept>
#include <string>
#include <vector>

#include "Math/Factory.h"
#include "Math/Functor.h"
#include "Math/Minimizer.h"

namespace jdm {

struct Ev {
  int cell;  ///< fit cell (-1: none)
  double d;
  double q;
  double w;
};
struct Result {
  std::vector<double> par;
  std::vector<double> err;
  std::vector<std::vector<double>> cov;
  double chi2 = NAN;
  int ndf = 0;
  int nCalls = 0;
  bool ok = false;  ///< converged, with an accurate covariance
};

inline double EvWeight(const Ev& e, const std::vector<double>& p) {
  return e.w * std::exp(e.d * (p[0] + p[1] * e.d) + p[2] * e.d * e.q);
}

// per cell: S (prediction without N), its derivatives, and the generator
// variance
inline void Sums(const std::vector<Ev>& ev, int nCell,
                 const std::vector<double>& p, std::vector<double>& S,
                 std::vector<std::vector<double>>& dS, std::vector<double>& V) {
  S.assign(nCell, 0.);
  V.assign(nCell, 0.);
  dS.assign(nCell, std::vector<double>(3, 0.));
  for (const Ev& e : ev) {
    if (e.cell < 0 || e.cell >= nCell) continue;
    const double x = EvWeight(e, p);
    S[e.cell] += x;
    V[e.cell] += x * x;
    dS[e.cell][0] += x * e.d;
    dS[e.cell][1] += x * e.d * e.d;
    dS[e.cell][2] += x * e.d * e.q;
  }
}

/// Minuit2 for a chi2 (error definition 1).
inline std::unique_ptr<ROOT::Math::Minimizer> NewMinimizer() {
  std::unique_ptr<ROOT::Math::Minimizer> m(
      ROOT::Math::Factory::CreateMinimizer("Minuit2", "Migrad"));
  if (!m) throw std::runtime_error("JpsiDataMapFit: Minuit2 not available");
  m->SetErrorDef(1.);
  m->SetPrintLevel(0);
  m->SetStrategy(1);
  m->SetMaxFunctionCalls(100000);
  return m;
}

/// chi2 = sum r_i^2 of the residual vector resid(p), minimised with Migrad;
/// errors and covariance from Hesse. ndf = residuals - free parameters.
inline Result FitResid(
    const std::function<std::vector<double>(const std::vector<double>&)>& resid,
    const std::vector<double>& p0, const std::vector<bool>& fixed) {
  const unsigned n = p0.size();
  auto chi2 = [&](const double* x) {
    double c = 0;
    for (double r : resid(std::vector<double>(x, x + n))) c += r * r;
    return std::isfinite(c) ? c : 1e300;
  };
  ROOT::Math::Functor fcn(chi2, n);
  auto m = NewMinimizer();
  m->SetFunction(fcn);
  int nFree = 0;
  for (unsigned k = 0; k < n; ++k) {
    const std::string name = "p" + std::to_string(k);
    if (fixed[k]) {
      m->SetFixedVariable(k, name, p0[k]);
    } else {
      m->SetVariable(k, name, p0[k], 0.1);
      ++nFree;
    }
  }
  Result res;
  const bool converged = nFree == 0 || m->Minimize();
  const bool hesse = nFree == 0 || m->Hesse();
  res.par = nFree == 0 ? p0 : std::vector<double>(m->X(), m->X() + n);
  res.err.assign(n, 0.);
  res.cov.assign(n, std::vector<double>(n, 0.));
  res.ok = converged && hesse && (nFree == 0 || m->CovMatrixStatus() == 3);
  if (nFree > 0)
    for (unsigned i = 0; i < n; ++i) {
      if (fixed[i]) continue;
      res.err[i] = m->Errors()[i];
      for (unsigned j = 0; j < n; ++j)
        if (!fixed[j]) res.cov[i][j] = m->CovMatrix(i, j);
    }
  res.chi2 = chi2(res.par.data());
  res.ndf = static_cast<int>(resid(res.par).size()) - nFree;
  res.nCalls = nFree == 0 ? 0 : m->NCalls();
  return res;
}

// ---------------------------------------------------------------------------
// Forward tail: the exponent n of dN/dxF ~ (1 - |xF|)^n fitted to the
// corrected y distribution above the map (JpsiDataMap.C, key tail_n).
//
// The generator events of each y bin j carry b = w * J_tail(n0) / J_base,
// the reweighting of the base to the tail model with a reference exponent n0,
// and L = ln(1 - |xF|). The model for another n is
//   P_j(n) = N * sum b exp((n - n0) L),
// N free (the shape only). The events are grouped in fine L cells per bin
// (the mean L of each cell is kept, so the grouping is exact to second order
// in (n - n0) dL); N is solved for each n, n is fitted with Minuit2.

struct TailBin {
  double D = 0;            ///< corrected data per POT
  double eD = 0;           ///< its error
  std::vector<double> b;   ///< per L cell: sum b
  std::vector<double> b2;  ///< per L cell: sum b^2
  std::vector<double> L;   ///< per L cell: mean L
};

struct TailResult {
  double n = NAN;   ///< best exponent
  double en = NAN;  ///< Delta chi2 = 1 half width
  double enLo = NAN;
  double enHi = NAN;
  double N = NAN;
  double chi2 = NAN;
  int ndf = 0;
  bool ok = false;
};

/// Group events (bin index, b, L) into TailBins with nL cells in L between
/// lMin and 0. Events outside 0 <= bin < nBin are ignored.
inline std::vector<TailBin> GroupTail(const std::vector<int>& bin,
                                      const std::vector<double>& b,
                                      const std::vector<double>& L, int nBin,
                                      int nL = 4000, double lMin = -6.) {
  std::vector<TailBin> out(nBin);
  std::vector<std::vector<double>> sl(nBin, std::vector<double>(nL, 0.));
  for (TailBin& t : out) {
    t.b.assign(nL, 0.);
    t.b2.assign(nL, 0.);
  }
  for (size_t i = 0; i < bin.size(); ++i) {
    if (bin[i] < 0 || bin[i] >= nBin || !(b[i] > 0)) continue;
    const double l = std::max(lMin, std::min(0., L[i]));
    const int k = std::min(nL - 1, static_cast<int>((l - lMin) / -lMin * nL));
    out[bin[i]].b[k] += b[i];
    out[bin[i]].b2[k] += b[i] * b[i];
    sl[bin[i]][k] += b[i] * l;
  }
  for (int j = 0; j < nBin; ++j) {
    TailBin& t = out[j];
    std::vector<double> bb;
    std::vector<double> bb2;
    std::vector<double> ll;
    for (int k = 0; k < nL; ++k)
      if (t.b[k] > 0) {
        bb.push_back(t.b[k]);
        bb2.push_back(t.b2[k]);
        ll.push_back(sl[j][k] / t.b[k]);
      }
    t.b.swap(bb);
    t.b2.swap(bb2);
    t.L.swap(ll);
  }
  return out;
}

/// prediction without N and its generator variance, for exponent n
inline void TailSums(const TailBin& t, double n, double n0, double& S,
                     double& V) {
  S = 0.;
  V = 0.;
  for (size_t k = 0; k < t.b.size(); ++k) {
    const double e = std::exp((n - n0) * t.L[k]);
    S += t.b[k] * e;
    V += t.b2[k] * e * e;
  }
}

/// chi2 for exponent n with N solved (sigma^2 = eD^2 + (sys D)^2 + N^2 V)
inline double TailChi2(const std::vector<TailBin>& bins, double n, double n0,
                       double sys, double& N) {
  std::vector<double> S(bins.size());
  std::vector<double> V(bins.size());
  for (size_t j = 0; j < bins.size(); ++j) TailSums(bins[j], n, n0, S[j], V[j]);
  N = 1.;
  double chi2 = NAN;
  for (int it = 0; it < 6; ++it) {  // sigma depends on N through V
    double a = 0.;
    double c = 0.;
    for (size_t j = 0; j < bins.size(); ++j) {
      const TailBin& t = bins[j];
      const double s2 = t.eD * t.eD + std::pow(sys * t.D, 2) + N * N * V[j];
      if (!(s2 > 0)) continue;
      a += S[j] * t.D / s2;
      c += S[j] * S[j] / s2;
    }
    if (!(c > 0)) return NAN;
    N = a / c;
  }
  chi2 = 0.;
  for (size_t j = 0; j < bins.size(); ++j) {
    const TailBin& t = bins[j];
    const double s2 = t.eD * t.eD + std::pow(sys * t.D, 2) + N * N * V[j];
    if (s2 > 0) chi2 += std::pow(N * S[j] - t.D, 2) / s2;
  }
  return chi2;
}

/// n fitted in [nLo, nHi] (Migrad, N solved for each n), its Delta chi2 = 1
/// errors from Minos
inline TailResult FitTail(const std::vector<TailBin>& bins, double n0,
                          double sys, double nLo = 1., double nHi = 25.) {
  TailResult r;
  int nUsed = 0;
  for (const TailBin& t : bins) nUsed += (t.eD > 0 && !t.b.empty());
  r.ndf = nUsed - 2;
  if (nUsed < 2) return r;
  auto chi2 = [&](const double* x) {
    double N;
    const double c = TailChi2(bins, x[0], n0, sys, N);
    return std::isfinite(c) ? c : 1e300;
  };
  ROOT::Math::Functor fcn(chi2, 1);
  auto m = NewMinimizer();
  m->SetFunction(fcn);
  m->SetLimitedVariable(0, "n", std::clamp(n0, nLo, nHi), 0.1, nLo, nHi);
  const bool converged = m->Minimize();
  r.n = m->X()[0];
  r.chi2 = TailChi2(bins, r.n, n0, sys, r.N);
  double lo = NAN;
  double hi = NAN;
  const bool minos = converged && m->GetMinosError(0, lo, hi);
  r.enLo = -lo;
  r.enHi = hi;
  r.en = 0.5 * (r.enLo + r.enHi);
  r.ok = minos && std::isfinite(r.en) && r.en > 0;
  return r;
}

}  // namespace jdm

#endif  // SHIPGEN_JPSIDATAMAPFIT_H_
