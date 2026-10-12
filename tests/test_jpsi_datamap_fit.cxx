// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

// Closure of the data-map fit (JpsiDataMapFit.h): pseudo-data in y x p_T
// cells are made from a generator sample with a known map, and the map is
// fitted back on an independent sample of the map base (the map switched off,
// as macro/jpsi/JpsiDataMap.C does with the base generator). The fit
// (FitResid, Minuit2) must recover the input within its errors. The
// forward-tail fit (FitTail) must recover the exponent of (1 - |xF|)^n
// pseudo-data from a sample made with another n.

#include <cmath>
#include <cstdint>
#include <cstdio>
#include <string>
#include <vector>

#include "JpsiDataMapFit.h"
#include "JpsiSampler.h"

namespace {

int gFailures = 0;

void Check(const std::string& what, bool ok, const std::string& detail = "") {
  std::printf("  [%s] %s%s%s\n", ok ? "PASS" : "FAIL", what.c_str(),
              detail.empty() ? "" : " : ", detail.c_str());
  if (!ok) ++gFailures;
}

std::string Num(double x) {
  char b[32];
  std::snprintf(b, sizeof b, "%.4g", x);
  return b;
}

// cells: 5 y slices from 0.6 to 1.6 times 4 p_T bins, true kinematics
const std::vector<double> kY = {0.6, 0.8, 1.0, 1.2, 1.4, 1.6};
const std::vector<double> kPt = {0., 0.75, 1.5, 2.5, 4.0};

int Slot(const std::vector<double>& e, double v) {
  for (std::size_t i = 0; i + 1 < e.size(); ++i)
    if (v >= e[i] && v < e[i + 1]) return static_cast<int>(i);
  return -1;
}

/// corrected data per POT in a cell and its error
struct Cell {
  double D = 0;
  double eD = 0;
};

int CellOf(double y, double pt) {
  const int iy = Slot(kY, y);
  const int ip = Slot(kPt, pt);
  return (iy < 0 || ip < 0) ? -1 : iy * (static_cast<int>(kPt.size()) - 1) + ip;
}

}  // namespace

int main() {
  const int nCell = (kY.size() - 1) * (kPt.size() - 1);
  // the map base: the default configuration with the map on at zero
  jpsi::Config base = jpsi::NominalConfig();
  base.dataMap = jpsi::DataMap();
  base.dataMap.on = true;
  base.physicsWeight = false;
  base.nEvents = 400000;
  // the "truth" for the pseudo-data: an invented map
  const double b1 = -0.8;
  const double b2 = 0.3;
  const double c = 0.05;
  jpsi::DataMap truth = base.dataMap;
  truth.b1 = b1;
  truth.b2 = b2;
  truth.c = c;

  // pseudo-data: the base sample reweighted with the truth map (seed 1)
  std::vector<Cell> cells(nCell);
  {
    jpsi::Config cd = base;
    cd.seed = 1;
    jpsi::Sampler s(cd);
    for (int64_t i = 0; i < cd.nEvents; ++i) {
      const jpsi::Event ev = s.Next();
      const int k = CellOf(ev.yCM, ev.jpsi.Pt());
      if (k >= 0)
        cells[k].D +=
            ev.weight * jpsi::DataMapWeight(truth, ev.yCM, ev.jpsi.Pt());
    }
    for (auto& cell : cells) cell.eD = 0.02 * cell.D;  // 2% per cell
  }
  // the fit sample: an independent base sample (seed 2)
  std::vector<jdm::Ev> ev;
  {
    jpsi::Config cf = base;
    cf.seed = 2;
    jpsi::Sampler s(cf);
    for (int64_t i = 0; i < cf.nEvents; ++i) {
      const jpsi::Event e = s.Next();
      const double pt = e.jpsi.Pt();
      ev.push_back({CellOf(e.yCM, pt), jpsi::DataMapDy(base.dataMap, e.yCM),
                    std::min(pt * pt, base.dataMap.qMax) - base.dataMap.q0,
                    e.weight});
    }
  }

  const std::vector<double> want = {b1, b2, c, 0.};
  const char* name[4] = {"b1", "b2", "c", "ln N"};
  auto report = [&](const char* fit, const jdm::Result& r) {
    std::printf("%s: chi2 %.1f / %d, %d function calls\n", fit, r.chi2, r.ndf,
                r.nCalls);
    Check(std::string(fit) + " converged", r.ok);
    for (int k = 0; k < 4; ++k) {
      const double pull = r.err[k] > 0 ? (r.par[k] - want[k]) / r.err[k] : NAN;
      Check(std::string(fit) + ": " + name[k] + " recovered within 3 sigma",
            std::fabs(pull) < 3.,
            Num(r.par[k]) + " +- " + Num(r.err[k]) + " (input " + Num(want[k]) +
                ")");
    }
    Check(std::string(fit) + ": chi2 / ndf below 3", r.chi2 < 3. * r.ndf,
          Num(r.chi2) + " / " + std::to_string(r.ndf));
  };

  std::printf("Data-map fit closure (%d cells, 2%% errors)\n", nCell);
  auto resid = [&](const std::vector<double>& p) {
    std::vector<double> S;
    std::vector<double> V;
    std::vector<double> r;
    std::vector<std::vector<double>> dS;
    jdm::Sums(ev, nCell, p, S, dS, V);
    const double N = std::exp(p[3]);
    for (int i = 0; i < nCell; ++i) {
      if (!(cells[i].D > 0)) continue;
      const double sg = std::sqrt(cells[i].eD * cells[i].eD + N * N * V[i]);
      r.push_back((N * S[i] - cells[i].D) / sg);
    }
    return r;
  };
  const jdm::Result residFit =
      jdm::FitResid(resid, {0., 0., 0., 0.}, {false, false, false, false});
  report("FitResid", residFit);
  // a parameter held fixed keeps its value and gets no error
  const jdm::Result fixedFit =
      jdm::FitResid(resid, {0., 0., 0.05, 0.}, {false, false, true, false});
  Check("fixed parameter kept, without error",
        fixedFit.par[2] == 0.05 && fixedFit.err[2] == 0. &&
            fixedFit.cov[2][0] == 0. && fixedFit.ndf == residFit.ndf + 1);

  // forward tail: pseudo-data with (1 - |xF|)^8 above y = 1.0, fitted back on
  // an independent sample made with the reference exponent 5.5
  {
    const double nTrue = 8.0;
    const double n0 = 5.5;
    const std::vector<double> yE = {1.0, 1.2, 1.4, 1.6, 1.8};
    const int nB = yE.size() - 1;
    auto sample = [&](double n, std::uint64_t seed, std::vector<int>& bin,
                      std::vector<double>& w, std::vector<double>& L) {
      jpsi::Config c = jpsi::NominalConfig();
      c.dataHi = 1.0;
      c.tailN = n;
      c.nEvents = 600000;
      c.seed = seed;
      c.output = jpsi::Output::Jpsi;
      jpsi::Sampler s(c);
      for (int64_t i = 0; i < s.NEvents(); ++i) {
        const jpsi::Event e = s.Next();
        int b = -1;
        for (int j = 0; j < nB; ++j)
          if (e.yCM >= yE[j] && e.yCM < yE[j + 1]) b = j;
        if (b < 0) continue;
        bin.push_back(b);
        w.push_back(e.weight);
        L.push_back(std::log(1. - std::fabs(e.xF)));
      }
    };
    std::vector<int> bD;
    std::vector<int> bG;
    std::vector<double> wD;
    std::vector<double> lD;
    std::vector<double> wG;
    std::vector<double> lG;
    sample(nTrue, 11, bD, wD, lD);
    sample(n0, 12, bG, wG, lG);
    std::vector<jdm::TailBin> bins = jdm::GroupTail(bG, wG, lG, nB);
    for (size_t i = 0; i < bD.size(); ++i) bins[bD[i]].D += wD[i];
    for (jdm::TailBin& t : bins) t.eD = 0.02 * t.D;
    // the grouping in L is exact to second order
    double S;
    double V;
    double direct = 0.;
    jdm::TailSums(bins[3], nTrue, n0, S, V);
    for (size_t i = 0; i < bG.size(); ++i)
      if (bG[i] == 3) direct += wG[i] * std::exp((nTrue - n0) * lG[i]);
    Check("tail: grouped sums equal the event sums",
          std::fabs(S / direct - 1.) < 1e-4, Num(S / direct - 1.));
    const jdm::TailResult t = jdm::FitTail(bins, n0, 0.);
    std::printf(
        "\nForward tail closure: n = %.3f -%.3f +%.3f, chi2 %.2f / %d\n", t.n,
        t.enLo, t.enHi, t.chi2, t.ndf);
    Check("tail fit converged", t.ok);
    Check("tail: n recovered within 3 sigma",
          std::fabs(t.n - nTrue) < 3. * t.en,
          Num(t.n) + " +- " + Num(t.en) + " (input " + Num(nTrue) + ")");
    // N is free: it absorbs the change of the tail level with n
    Check("tail: chi2 / ndf below 5", t.chi2 < 5. * t.ndf,
          Num(t.chi2) + " / " + std::to_string(t.ndf));
    double Nref;
    Check("tail: the reference exponent is excluded",
          jdm::TailChi2(bins, n0, n0, 0., Nref) - t.chi2 > 25.);
  }

  std::printf("\n%s (%d failures)\n", gFailures ? "FAILED" : "ALL PASSED",
              gFailures);
  return gFailures ? 1 : 0;
}
