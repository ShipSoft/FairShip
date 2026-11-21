// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration
//
// Self-test for JpsiSampler:
//   built by ctest as testJpsiSampler; standalone:
//   g++ -O2 -std=c++20 -I shipgen tests/test_jpsi_sampler.cxx
//   shipgen/JpsiSampler.cxx -o test_jpsi
//   ./test_jpsi

#include <unistd.h>

#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <map>
#include <string>
#include <vector>

#include "JpsiSampler.h"

using jpsi::ApplyConfigFile;
using jpsi::Config;
using jpsi::CosAcceptance;
using jpsi::Event;
using jpsi::kBrMuMu;
using jpsi::kMJpsi;
using jpsi::kVersionMinor;
using jpsi::Layer;
using jpsi::MolybdenumScaled;
using jpsi::NominalConfig;
using jpsi::Normalisation;
using jpsi::Output;
using jpsi::Sampler;
using jpsi::TungstenNA50;
using jpsi::YShape;

namespace {

int gFailures = 0;

void Check(const std::string& what, bool ok, const std::string& detail = "") {
  std::printf("  [%s] %s%s%s\n", ok ? "PASS" : "FAIL", what.c_str(),
              detail.empty() ? "" : " : ", detail.c_str());
  if (!ok) ++gFailures;
}

bool Close(double a, double b, double relTol) {
  return std::abs(a - b) <= relTol * std::abs(b);
}

}  // namespace

int main() {
  Config cfg;
  cfg.ptSq = 1.9;
  cfg.ptSqSlope = 0.;  // the factorised case; a slope has its own test
  // the closure tests below compare with NA50, a thin target, so no secondary
  // factor
  cfg.secondaryFactor = 1.0;
  cfg.nEvents = 1000000;
  Sampler s(cfg);
  std::printf("%s\n\n", s.Summary().c_str());
  const auto& n = s.GetNormalisation();

  std::printf("Normalisation\n");
  Check("f_y near 0.45", std::abs(n.fY - 0.45) < 0.02,
        "f_y = " + std::to_string(n.fY));
  Check("chi_mumu (thin target, NA50) near 1.9e-6",
        Close(n.chiMuMuPrimary, 1.9e-6, 0.05),
        "chi = " + std::to_string(n.chiMuMu));
  Check("chi_Jpsi = chi_mumu / BR",
        Close(n.chiJpsi * kBrMuMu, n.chiMuMu, 1e-12));
  Check("weight = nPot*chi/N",
        Close(n.weight, cfg.nPot * n.chiMuMu / cfg.nEvents, 1e-12),
        "w = " + std::to_string(n.weight));
  Check("<pT^2> = requested", Close(n.meanPtSq, 1.9, 1e-3));

  // ---------------------------------------- deterministic normalisation
  std::printf("\nSeed independence of the normalisation\n");
  bool identical = true;
  for (unsigned seed : {1u, 2u, 999u}) {
    Config c = cfg;
    c.seed = seed;
    Sampler ss(c);
    if (ss.GetNormalisation().fY != n.fY ||
        ss.GetNormalisation().chiMuMu != n.chiMuMu ||
        ss.GetNormalisation().weight != n.weight) {
      identical = false;
    }
  }
  Check("f_y, chi and weight bit-identical across seeds", identical);

  // ---------------------------------------- inclusive J/psi output
  std::printf("\nInclusive J/psi normalisation\n");
  Config incl = cfg;
  incl.output = Output::Jpsi;
  Sampler sIncl(incl);
  const auto& ni = sIncl.GetNormalisation();
  Check("inclusive weight = nPot*chi_Jpsi/N",
        Close(ni.weight, cfg.nPot * ni.chiJpsi / cfg.nEvents, 1e-12),
        "w = " + std::to_string(ni.weight));
  Check("ratio to the dimuon weight is 1/BR",
        Close(ni.weight / n.weight, 1.0 / kBrMuMu, 1e-9),
        "ratio = " + std::to_string(ni.weight / n.weight));
  Event ei = sIncl.Next();
  Check("no muons produced in Jpsi mode", !ei.hasDimuon);

  // ---------------------------------------- event sample
  std::printf("\nEvent sample\n");
  const int64_t nGen = 300000;
  double sumW = 0.;
  double sumW2 = 0.;
  double sumPtSq = 0.;
  int64_t nMuMu = 0;
  bool xfOk = true;
  std::map<int, int64_t> yHist;
  double maxMassDev = 0.;
  for (int64_t i = 0; i < nGen; ++i) {
    Event e = s.Next();
    ++nMuMu;
    sumW += e.weight;
    sumW2 += e.weight * e.weight;
    sumPtSq += e.jpsi.Pt() * e.jpsi.Pt();
    yHist[static_cast<int>(std::floor(e.yCM * 10))]++;
    maxMassDev = std::max(maxMassDev, std::abs((e.mup + e.mum).M() - kMJpsi));
    if (std::abs(e.xF) >= 1.0) xfOk = false;
  }
  Check("all events inside |x_F| < 1", xfOk);
  Check("nominal weights identical (N_eff = N)",
        Close(sumW * sumW / sumW2, nMuMu, 1e-9));
  Check("dimuon momenta sum to the J/psi mass", maxMassDev < 1e-6);
  Check("sampled <pT^2> matches the model",
        Close(sumPtSq / nMuMu, n.meanPtSq, 0.02));

  std::printf("\nRapidity shape vs SHiP Table 5 (normalised to the 0.4 bin)\n");
  const std::vector<std::pair<int, double>> table = {
      {4, 375.56}, {7, 240.60}, {10, 135.93}, {13, 53.78}, {16, 12.84}};
  const double ref = yHist[4] / 375.56;
  bool shapeOk = true;
  for (const auto& entry : table) {
    const double ratio = yHist[entry.first] / entry.second / ref;
    std::printf("    y = %.1f : sampled/table = %.3f\n", entry.first * 0.1,
                ratio);
    if (std::abs(ratio - 1) > 0.08) shapeOk = false;
  }
  Check("data shape reproduced within 8%", shapeOk);

  const double eps = 2e-3;
  const double dLo =
      std::abs(s.YDensity(cfg.dataLo - eps) / s.YDensity(cfg.dataLo + eps) - 1);
  // the tail falls by ~25 per unit y at y = 2.0, so look closer there
  const double epsHi = 3e-4;
  const double dHi = std::abs(
      s.YDensity(cfg.dataHi - epsHi) / s.YDensity(cfg.dataHi + epsHi) - 1);
  Check("density continuous at the Gaussian-table join", dLo < 0.03,
        "jump " + std::to_string(dLo));
  Check("density continuous at the table-tail join (y = 2.0)", dHi < 0.03,
        "jump " + std::to_string(dHi));

  // ---------------------------------------- polarisation
  std::printf("\nPolarisation\n");
  Check("f_cos(0.11) = 0.4867", Close(CosAcceptance(0.11), 0.48674, 1e-4));
  Check("f_cos(0) = 0.5", Close(CosAcceptance(0.0), 0.5, 1e-12));
  for (double lambda : {-0.5, -0.14, 0.3, 1.0}) {
    Config c = cfg;
    c.lambdaPol = lambda;
    Sampler sp(c);
    const bool normOk =
        Close(sp.GetNormalisation().chiMuMu * CosAcceptance(lambda),
              n.chiMuMu * 0.5, 1e-9);
    const int kBins = 10;
    std::vector<int64_t> hist(kBins, 0);
    const int64_t nn = 200000;
    for (int64_t i = 0; i < nn; ++i) {
      const double c2 = sp.Next().cosThetaCS;
      hist[std::min(kBins - 1, static_cast<int>((c2 + 1) * kBins / 2))]++;
    }
    double maxDev = 0.;
    for (int b = 0; b < kBins; ++b) {
      const double lo = -1 + 2.0 * b / kBins;
      const double hi = lo + 2.0 / kBins;
      const double expect =
          ((hi - lo) + lambda * (hi * hi * hi - lo * lo * lo) / 3) /
          (2 + 2 * lambda / 3);
      maxDev = std::max(
          maxDev, std::abs(hist[b] / static_cast<double>(nn) / expect - 1));
    }
    std::printf("    lambda = %+.2f : f_cos = %.4f, max bin deviation %.3f\n",
                lambda, CosAcceptance(lambda), maxDev);
    Check("normalisation scales as 1/f_cos", normOk);
    Check("cos Theta_CS follows 1 + lambda cos^2", maxDev < 0.03);
  }

  // ---------------------------------------- composition knob
  std::printf("\nEnhancement\n");
  Config enh = cfg;
  enh.enhancement = 1.0;
  Sampler sEnh(enh);
  Check("enhancement 1 gives weight 1",
        Close(sEnh.GetNormalisation().weight, 1.0, 1e-3),
        "N = " + std::to_string(sEnh.NEvents()));
  enh.enhancement = 1000.0;
  Sampler sEnh1k(enh);
  Check("enhancement 1000 gives weight 1e-3",
        Close(sEnh1k.GetNormalisation().weight, 1e-3, 1e-3));

  // ---------------------------------------- rapidity-dependent pT
  std::printf("\nRapidity-dependent transverse momentum\n");
  {
    Config c = cfg;
    c.ptSq = 2.1;
    c.ptSqSlope = -0.4;  // falling with |y|, as near the kinematic limit
    Sampler sp(c);
    // <pT^2> in rapidity slices must follow the requested straight line
    const double edges[5] = {0.2, 0.6, 1.0, 1.4, 1.8};
    double sum[4] = {0, 0, 0, 0};
    double sum2[4] = {0, 0, 0, 0};
    int64_t cnt[4] = {0, 0, 0, 0};
    for (int64_t i = 0; i < 2000000; ++i) {
      const Event e = sp.Next();
      for (int b = 0; b < 4; ++b)
        if (e.yCM > edges[b] && e.yCM < edges[b + 1]) {
          const double pt2 = e.jpsi.Pt() * e.jpsi.Pt();
          sum[b] += pt2;
          sum2[b] += pt2 * pt2;
          ++cnt[b];
        }
    }
    bool follows = true;
    for (int b = 0; b < 4; ++b) {
      if (cnt[b] < 1000) continue;
      const double yc = 0.5 * (edges[b] + edges[b + 1]);
      const double want = c.ptSq + c.ptSqSlope * yc;
      const double got = sum[b] / cnt[b];
      const double err =
          std::sqrt(std::max(0.0, sum2[b] / cnt[b] - got * got) / cnt[b]);
      std::printf(
          "    %.1f < y < %.1f : <pT^2> = %.3f +- %.3f, requested %.3f\n",
          edges[b], edges[b + 1], got, err, want);
      if (std::abs(got - want) > std::max(0.03, 5 * err)) follows = false;
    }
    Check("sampled <pT^2> follows the requested slope", follows);
    Config flat = cfg;
    flat.ptSq = 2.1;
    Sampler sf(flat);
    Check("slope 0 reproduces the flat case",
          Close(sf.GetNormalisation().meanPtSq, 2.1, 1e-3) &&
              Close(sp.GetNormalisation().meanPtSq, 2.1,
                    1e-3),  // both quoted at y = 0
          "flat " + std::to_string(sf.GetNormalisation().meanPtSq) +
              ", sloped at y=0 " +
              std::to_string(sp.GetNormalisation().meanPtSq));
    // the normalisation must stay consistent: weights identical, f_y sane
    Check("f_y still near 0.45 with a pT slope",
          std::abs(sp.GetNormalisation().fY - 0.45) < 0.03,
          "f_y = " + std::to_string(sp.GetNormalisation().fY));
  }

  // ---------------------------------------- p_T spectrum and tail against y
  std::printf("\np_T spectrum against rapidity (JointDensity)\n");
  {
    // conditional p_T at fixed y from the joint density the sampler uses
    struct Cond {
      double norm = 0.;
      double ptSq = 0.;
      double above2 = 0.;
      double above3 = 0.;
    };
    auto conditional = [](const Sampler& sp, double y) {
      Cond c;
      const int kPt = 4000;
      const double h = sp.PtMaxAt(y) / kPt;
      for (int i = 0; i <= kPt; ++i) {
        const double pt = i * h;
        const double f =
            (i == 0 || i == kPt ? 0.5 : 1.0) * sp.JointDensity(y, pt) * h;
        c.norm += f;
        c.ptSq += f * pt * pt;
        if (pt > 2) c.above2 += f;
        if (pt > 3) c.above3 += f;
      }
      c.ptSq /= c.norm;
      c.above2 /= c.norm;
      c.above3 /= c.norm;
      return c;
    };
    Config c = cfg;
    c.ptSqSlope = -0.4;  // crosses the mixture's floor near |y| = 1.3
    Sampler sp(c);
    const auto& np = sp.GetNormalisation();
    Check("nodes below the mixture's floor reported in the summary",
          np.ptNodesSoftened > 0 &&
              sp.Summary().find("softer component rescaled") !=
                  std::string::npos);
    // The tail probabilities must change smoothly with y, also where <pT^2>(y)
    // crosses the floor of the thermal + power-law mixture (v1.7 switched to
    // a pure thermal spectrum there: P(pT > 3) fell by x2.8 within 0.03 in y).
    double worst2 = 0.;
    double worst3 = 0.;
    double worstNorm = 0.;
    Cond prev = conditional(sp, 0.);
    for (int k = 1; k <= 160; ++k) {
      const double y = 0.01 * k;
      const Cond cur = conditional(sp, y);
      worst2 = std::max(worst2, std::abs(std::log(cur.above2 / prev.above2)));
      worst3 = std::max(worst3, std::abs(std::log(cur.above3 / prev.above3)));
      worstNorm = std::max(worstNorm, std::abs(cur.norm / sp.YDensity(y) - 1));
      prev = cur;
    }
    for (double y : {1.9, 2.05, 2.1}) {
      worstNorm = std::max(
          worstNorm, std::abs(conditional(sp, y).norm / sp.YDensity(y) - 1));
    }
    std::printf(
        "    largest step in ln P(pT > 2 | y), ln P(pT > 3 | y) per 0.01 in y: "
        "%.4f, %.4f\n",
        worst2, worst3);
    Check("P(pT > 2 | y) and P(pT > 3 | y) continuous in y (0 < y < 1.6)",
          worst2 < 0.05 && worst3 < 0.1);
    Check("integral of JointDensity over pT = YDensity", worstNorm < 2e-3,
          "worst " + std::to_string(worstNorm));
    const Cond at0 = conditional(sp, 0.);
    const Cond at14 = conditional(sp, 1.4);
    Check("<pT^2>(y) from JointDensity follows the request",
          Close(at0.ptSq, 1.9, 2e-3) && Close(at14.ptSq, 1.9 - 0.4 * 1.4, 5e-3),
          std::to_string(at0.ptSq) + ", " + std::to_string(at14.ptSq));

    // Forward tail: the p_T drawn at a given y must follow the same joint
    // density as the rapidity density, f(pT|y) (1-|xF|)^n |dxF/dy|. A low
    // dataHi puts many events into the tail.
    Config t = c;
    t.dataHi = 1.0;
    Sampler st(t);
    const double lo[2] = {1.2, 1.5};
    const double hi[2] = {1.3, 1.6};
    double cnt[2] = {0, 0};
    double sum[2] = {0, 0};
    double sum2[2] = {0, 0};
    for (int64_t i = 0; i < 1500000; ++i) {
      const Event e = st.Next();
      for (int b = 0; b < 2; ++b)
        if (e.yCM >= lo[b] && e.yCM < hi[b]) {
          const double pt2 = e.jpsi.Pt() * e.jpsi.Pt();
          ++cnt[b];
          sum[b] += pt2;
          sum2[b] += pt2 * pt2;
        }
    }
    bool tailOk = true;
    for (int b = 0; b < 2; ++b) {
      double w = 0.;
      double m = 0.;
      for (int j = 0; j < 100; ++j) {
        const double y = lo[b] + (j + 0.5) * (hi[b] - lo[b]) / 100;
        const Cond cy = conditional(st, y);
        w += cy.norm;
        m += cy.norm * cy.ptSq;
      }
      const double want = m / w;
      const double got = sum[b] / cnt[b];
      const double err = std::sqrt((sum2[b] / cnt[b] - got * got) / cnt[b]);
      const double flat = conditional(sp, 0.5 * (lo[b] + hi[b])).ptSq;
      std::printf(
          "    tail %.1f < y < %.1f: <pT^2> sampled %.3f +- %.3f, joint %.3f "
          "(f(pT|y) alone %.3f)\n",
          lo[b], hi[b], got, err, want, flat);
      if (std::abs(got - want) > 5 * err || std::abs(flat - want) < 0.1)
        tailOk = false;
    }
    Check("tail p_T sampled from the joint density", tailOk);
  }

  // ---------------------------------------- injection into a host production
  std::printf("\nInjection mode\n");
  {
    Config inj = cfg;
    inj.injection = true;
    inj.enhancement = 1.0;
    Sampler sInj(inj);
    const auto& nj = sInj.GetNormalisation();
    Check("E = 1: physical rate per host event, weight 1",
          Close(nj.weight, 1.0, 1e-12) &&
              Close(nj.meanPerEvent, n.chiMuMu, 1e-12),
          "mu = " + std::to_string(nj.meanPerEvent));

    inj.enhancement = 3.0e5;  // mu = 0.57 per event
    Sampler sInj2(inj);
    const auto& n2 = sInj2.GetNormalisation();
    int64_t total = 0;
    const int64_t nHost = 400000;
    for (int64_t i = 0; i < nHost; ++i) total += sInj2.NumberToInject();
    const double muObs = total / static_cast<double>(nHost);
    Check("mean J/psi per host event = mu",
          std::abs(muObs - n2.meanPerEvent) <
              5 * std::sqrt(n2.meanPerEvent / nHost),
          "observed " + std::to_string(muObs) + ", expected " +
              std::to_string(n2.meanPerEvent));
    Check("weight = 1/E", Close(n2.weight, 1.0 / 3.0e5, 1e-12));
    Check("expectation preserved: mu * w = rate per POT",
          Close(n2.meanPerEvent * n2.weight, n.chiMuMu, 1e-12));

    Config inj3 = cfg;
    inj3.injection = true;
    inj3.meanPerEvent = 2.5;  // more than one per event
    Sampler sInj3(inj3);
    total = 0;
    int maxK = 0;
    for (int64_t i = 0; i < 100000; ++i) {
      const int k = sInj3.NumberToInject();
      total += k;
      maxK = std::max(maxK, k);
    }
    Check("mu = 2.5 gives 2 or 3 per event, mean 2.5",
          maxK == 3 && std::abs(total / 1e5 - 2.5) < 0.01);
    Check("mu = 2.5 weight = rate/2.5",
          Close(sInj3.GetNormalisation().weight, n.chiMuMu / 2.5, 1e-12));

    Config bad2 = cfg;
    bad2.injection = true;
    bad2.enhancement = -1;
    bad2.meanPerEvent = -1;
    bool threw = false;
    try {
      Sampler probe(bad2);
    } catch (const std::exception&) {
      threw = true;
    }
    Check("injection without a rate knob is rejected", threw);
  }

  // ---------------------------------------- shapes
  std::printf("\nRapidity models\n");
  for (auto shape : {YShape::Gauss, YShape::Data}) {
    Config c = cfg;
    c.yShape = shape;
    Sampler ss(c);
    int64_t above = 0;
    const int64_t nn = 100000;
    for (int64_t i = 0; i < nn; ++i) {
      if (ss.Next().jpsi.P() > 200) ++above;
    }
    std::printf(
        "    %-6s : f_y = %.3f, chi = %.3e, chi*P(p>200) = %.2e\n",
        shape == YShape::Gauss ? "gauss" : "data", ss.GetNormalisation().fY,
        ss.GetNormalisation().chiMuMu,
        ss.GetNormalisation().chiMuMu * above / static_cast<double>(nn));
  }

  // ---------------------------------------- target model: vertex AND rate
  std::printf("\nTarget model\n");
  Config wOnly = cfg;
  wOnly.layers = {Layer{TungstenNA50(), 150.0}};
  Sampler sW(wOnly);
  const double pW = sW.GetNormalisation().probMuMuPerPot;
  std::printf("    thick W (150 cm) : P/POT = %.4e, chi = %.4e, ratio %.4f\n",
              pW, n.chiMuMu, pW / n.chiMuMu);
  Check("thick W: P/POT approaches chi_mumu",
        pW / n.chiMuMu > 0.99 && pW / n.chiMuMu <= 1.0001);

  Config mixed = cfg;
  mixed.layers = {Layer{MolybdenumScaled(), 58.0}, Layer{TungstenNA50(), 92.0}};
  Sampler sMix(mixed);
  const double pMix = sMix.GetNormalisation().probMuMuPerPot;
  std::printf("    Mo 58 cm + W 92 cm : P/POT = %.4e (%.1f%% of pure W)\n",
              pMix, 100 * pMix / pW);
  Check("mixed target rate differs from pure W", pMix < pW && pMix > 0.5 * pW);
  Check("mixed target weight uses the integrated rate",
        Close(sMix.GetNormalisation().weight, cfg.nPot * pMix / cfg.nEvents,
              1e-9));
  double zSum = 0.;
  const int64_t nz = 50000;
  for (int64_t i = 0; i < nz; ++i) zSum += sMix.Next().z_cm;
  std::printf("    <z> = %.1f cm of 150 cm\n", zSum / nz);
  Check("vertex concentrated upstream", zSum / nz > 0 && zSum / nz < 40);

  // ---------------------------------------- validation and reproducibility
  std::printf("\nValidation and reproducibility\n");
  auto throws = [](const Config& c) {
    try {
      Sampler probe(c);
      (void)probe;
    } catch (const std::exception&) {
      return true;
    }
    return false;
  };
  Config bad = cfg;
  bad.ptSq = -1;
  bad.fHard = 1.5;
  Check("rejects fHard > 1", throws(bad));
  bad = cfg;
  bad.lambdaPol = -1.5;
  Check("rejects lambda < -1", throws(bad));
  bad = cfg;
  bad.T = 0;
  Check("rejects T = 0", throws(bad));
  bad = cfg;
  bad.enhancement = -1;
  bad.nEvents = 0;
  Check("rejects nEvents = 0", throws(bad));

  Config a = cfg;
  Config b = cfg;
  a.seed = 7;
  b.seed = 7;
  Sampler sa(a);
  Sampler sb(b);
  Event ea = sa.Next();
  Event eb = sb.Next();
  Check("same seed reproduces the same event",
        ea.jpsi.Px() == eb.jpsi.Px() && ea.mup.Pz() == eb.mup.Pz());

  // ---------------------------------------- nominal configuration,
  // configuration files, physics weights
  std::printf("\nNominal configuration and testing path\n");
  {
    Config nom = NominalConfig();
    nom.nEvents = 1000;
    Sampler sn(nom);
    const Normalisation& nn = sn.GetNormalisation();
    Check("nominal: SHiP Table 5 shape (no data map), <pT^2> = 1.9 flat",
          !nom.dataMap.on && nom.yShape == YShape::Data &&
              Close(nn.meanPtSq, 1.9, 1e-3) && nom.ptSqSlope == 0.);
    Check("nominal: physics weight = rate per POT",
          nom.physicsWeight && nn.weight == nn.rate);
    // polarisation: the SHiP value; the total rate follows from the NA50
    // window |cos theta_CS| < 0.5 through f_cos
    Config unpol = nom;
    unpol.lambdaPol = 0.;
    Sampler su(unpol);
    Check("nominal: lambda = 0.11 (SHiP), rate x f_cos(0) / f_cos(0.11)",
          nom.lambdaPol == 0.11 &&
              Close(nn.rate / su.GetNormalisation().rate,
                    CosAcceptance(0.) / CosAcceptance(0.11), 1e-9),
          std::to_string(nn.rate / su.GetNormalisation().rate));
    Config big = nom;
    big.nEvents = 5000000;
    Sampler sbig(big);
    Check("physics weight independent of nEvents",
          sbig.GetNormalisation().weight == nn.weight);
    Config inc = nom;
    inc.output = Output::Jpsi;
    Sampler sinc(inc);
    Check("physics weight, inclusive: 1/BR larger",
          Close(sinc.GetNormalisation().weight * kBrMuMu, nn.weight, 1e-12));
    Config inj = nom;
    inj.injection = true;
    inj.meanPerEvent = 0.5;
    Sampler sinj(inj);
    Check("injection: weight = rate / mu",
          Close(sinj.GetNormalisation().weight, nn.rate / 0.5, 1e-12));
    bool version = false;
    for (const auto& kv : sn.Metadata())
      version |= kv.first == "version_minor" && kv.second == kVersionMinor;
    Check("version stored as major and minor", version);

    // files in a directory of their own; the configuration names the map by a
    // relative path, resolved against the configuration's directory
    const char* tmp = std::getenv("TMPDIR");
    std::string dir = std::string(tmp ? tmp : "/tmp") + "/jpsi_sampler_XXXXXX";
    if (!mkdtemp(dir.data())) {
      std::printf("cannot create a temporary directory\n");
      return 1;
    }
    std::vector<std::string> written;
    auto write = [&dir, &written](const char* name, const std::string& text) {
      const std::string f = dir + "/" + name;
      std::ofstream(f) << text;
      written.push_back(f);
      return f;
    };
    // an invented map (not a fit result), on the nominal base
    write("map.txt",
          "y_join 0.6\ny_hi 1.6\nptsq_ref 1.5\nptsq_max 16\n"
          "b1 -0.5\nb2 0.1\nc 0\nb1_err 0.2\n"
          "base_mean_pt_sq 1.9\nbase_pt_sq_slope 0\nbase_lambda_pol 0.11\n");
    const std::string cfgMap =
        write("map.cfg",
              "# map from a file, relative to this file\n"
              "data_map map.txt\n");
    Config f = NominalConfig();
    f.nEvents = 1000;
    std::vector<std::string> keys;
    ApplyConfigFile(f, cfgMap, &keys);
    Check("relative data_map path resolved against the configuration file",
          f.dataMap.on && f.dataMap.source == dir + "/map.txt");
    Check("keys reported", keys.size() == 1 && keys[0] == "data_map");
    Check("configuration and map text kept for provenance",
          f.provenance.find("data_map map.txt") != std::string::npos &&
              f.dataMap.text.find("b1 -0.5") != std::string::npos);
    Config base = NominalConfig();
    ApplyConfigFile(base, write("base.cfg", "data_map base\n"));
    Sampler sMap(f);
    Sampler sBase(base);
    // c = 0: the map multiplies the y density by exp(D (b1 + b2 D))
    const double d = 1.1 - 0.6;
    const double want = std::exp(d * (-0.5 + 0.1 * d));
    const double got = (sMap.YDensity(1.1) / sMap.YDensity(0.3)) /
                       (sBase.YDensity(1.1) / sBase.YDensity(0.3));
    Check("map from a file reweights the y density as specified",
          Close(got, want, 1e-3),
          std::to_string(got) + " vs " + std::to_string(want));
    Config v = NominalConfig();
    ApplyConfigFile(v, write("ptsq.cfg", "data_map map.txt\nptsq 1.6\n"));
    Check("map refused on another p_T base", throws(v));
    Config v2 = NominalConfig();
    ApplyConfigFile(v2,
                    write("ptsq_free.cfg",
                          "data_map map.txt\nptsq 1.6\nmap_base_check 0\n"));
    Check("map_base_check 0 allows the variation", !throws(v2));
    // the order of the lines does not matter
    Config o1 = NominalConfig();
    ApplyConfigFile(
        o1,
        write("order.cfg", "map_base_check 0\nptsq 1.6\ndata_map map.txt\n"));
    Check("map_base_check before data_map still applies", !throws(o1));
    Config o2 = NominalConfig();
    ApplyConfigFile(o2,
                    write("order_b1.cfg", "map_b1 -0.3\ndata_map map.txt\n"));
    Check("map_b1 before data_map changes the map", o2.dataMap.b1 == -0.3);
    auto rejects = [&](const char* name, const char* text) {
      try {
        Config u = NominalConfig();
        ApplyConfigFile(u, write(name, text));
      } catch (const std::exception&) {
        return true;
      }
      return false;
    };
    Check("repeated key rejected",
          rejects("twice.cfg", "ptsq 1.6\nlambda 0\nptsq 1.7\n"));
    Check("ptsq together with fhard rejected",
          rejects("ptsq_fhard.cfg", "fhard 0.5\nptsq 1.6\n"));
    Check("map_b1 without a data map rejected",
          rejects("b1_nomap.cfg", "map_b1 -0.3\n"));
    Check("non-numeric optional value rejected",
          rejects("alpha_word.cfg", "alpha_xf 0.1 0.2 Mo\n"));
    Config v3 = NominalConfig();
    ApplyConfigFile(v3,
                    write("slope.cfg", "data_map map.txt\npt_sq_slope -0.2\n"));
    Check("map refused on another p_T slope", throws(v3));
    Config v4 = NominalConfig();
    ApplyConfigFile(v4, write("lambda.cfg", "data_map map.txt\nlambda 0\n"));
    Check("map refused on another polarisation", throws(v4));
    // forward continuation from the map file: the map ends at y = 1.6 and the
    // (1-|xF|)^n tail with the file's exponent starts there
    write("map_tail.txt",
          "y_join 0.6\ny_hi 1.6\nptsq_ref 1.5\nptsq_max 16\n"
          "b1 -0.5\nb2 0.1\nc 0\ntail_n 7.5\ntail_n_err 0.8\n"
          "base_mean_pt_sq 1.9\nbase_pt_sq_slope 0\nbase_lambda_pol 0.11\n");
    Config ft = NominalConfig();
    ApplyConfigFile(ft, write("tail.cfg", "data_map map_tail.txt\n"));
    Check("map file with tail_n: continuation at the end of the map",
          ft.forwardTail == jpsi::ForwardTail::MapEnd && ft.tailN == 7.5);
    Sampler sft(ft);
    const double jump = sft.YDensity(1.6 - 3e-4) / sft.YDensity(1.6 + 3e-4);
    Check("density continuous where the tail joins the map",
          std::abs(jump - 1) < 0.02, "ratio " + std::to_string(jump));
    Config ft2 = ft;
    ApplyConfigFile(ft2,
                    write("tail_table.cfg", "forward_tail table\ntail 5.5\n"));
    Sampler sft2(ft2);
    Config ft3 = NominalConfig();
    ApplyConfigFile(ft3, write("tail_first.cfg",
                               "forward_tail table\ntail 5.5\n"
                               "data_map map_tail.txt\n"));
    Check("forward_tail before data_map overrides the map's continuation",
          ft3.forwardTail == jpsi::ForwardTail::Table && ft3.tailN == 5.5);
    Check("a steeper exponent gives fewer J/psi above the map (y = 1.9)",
          sft.YDensity(1.9) < sft2.YDensity(1.9));
    // nuclear x_F factor: 1 at x_F = 0, softer forward on W than on the shape's
    // Mo
    Config nw = NominalConfig();
    nw.layers = {Layer{TungstenNA50(), 150.0}};
    Config nw2 = nw;
    ApplyConfigFile(nw2, write("alpha.cfg", "alpha_xf 0 -0.4 95.95\n"));
    Sampler sn1(nw);
    Sampler sn2(nw2);
    const double r0 = sn2.YDensity(0.) / sn1.YDensity(0.);
    const double r16 = sn2.YDensity(1.6) / sn1.YDensity(1.6);
    Check("nuclear x_F factor: unchanged at y = 0, lower at y = 1.6 on W",
          std::abs(r0 - 1) < 2e-3 && r16 < 0.97 && r16 > 0.85,
          std::to_string(r0) + ", " + std::to_string(r16));
    Config nm = nw2;
    nm.layers = {Layer{MolybdenumScaled(), 150.0}};
    nm.shapeA = MolybdenumScaled().A;
    Config nm0 = nm;
    nm0.alphaXf2 = 0.;
    Sampler sm1(nm);
    Sampler sm0(nm0);
    bool sameMo = true;
    for (double yy : {0., 0.8, 1.6, 2.0})
      sameMo =
          sameMo && std::abs(sm1.YDensity(yy) / sm0.YDensity(yy) - 1) < 1e-9;
    Check("nuclear x_F factor is 1 on the shape's own nucleus", sameMo);
    bool removed = false;
    try {
      Config u = NominalConfig();
      ApplyConfigFile(u, write("hybrid.cfg", "shape hybrid\n"));
    } catch (const std::exception&) {
      removed = true;
    }
    Check("removed rapidity model rejected", removed);
    // secondary depth variation: same rate, deeper vertices
    Config sd = NominalConfig();
    sd.layers = {Layer{MolybdenumScaled(), 58.0}, Layer{TungstenNA50(), 92.0}};
    Config sd2 = sd;
    ApplyConfigFile(sd2, write("depth.cfg", "secondary_depth 10\n"));
    Sampler sSd(sd);
    Sampler sSd2(sd2);
    double z1 = 0.;
    double z2 = 0.;
    for (int i = 0; i < 100000; ++i) {
      z1 += sSd.Next().z_cm;
      z2 += sSd2.Next().z_cm;
    }
    Check(
        "secondary depth: rate unchanged, vertices deeper",
        sSd.GetNormalisation().weight == sSd2.GetNormalisation().weight &&
            z2 > z1 + 0.05 * 100000,
        "<z> " + std::to_string(z1 / 1e5) + " -> " + std::to_string(z2 / 1e5));
    bool unknown = false;
    try {
      Config u = NominalConfig();
      ApplyConfigFile(u, write("typo.cfg", "ptsqq 1.6\n"));
    } catch (const std::exception&) {
      unknown = true;
    }
    Check("unknown configuration key rejected", unknown);
    for (const auto& file : written) std::remove(file.c_str());
    rmdir(dir.c_str());
  }

  std::printf("\n%s (%d failures)\n", gFailures ? "FAILED" : "ALL PASSED",
              gFailures);
  return gFailures ? 1 : 0;
}
