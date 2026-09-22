// SPDX-License-Identifier: LGPL-3.0-or-later
//
// Self-test for JpsiSampler:
//   g++ -O2 -std=c++17 test_JpsiSampler.cxx JpsiSampler.cxx -o test_jpsi
//   ./test_jpsi

#include <cmath>
#include <cstdio>
#include <map>
#include <string>
#include <vector>

#include "JpsiSampler.h"

using namespace jpsi;

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
  cfg.nEvents = 1000000;
  Sampler s(cfg);
  std::printf("%s\n\n", s.Summary().c_str());
  const auto& n = s.GetNormalisation();

  std::printf("Normalisation\n");
  Check("f_y near 0.45", std::abs(n.fY - 0.45) < 0.02,
        "f_y = " + std::to_string(n.fY));
  Check("chi_mumu near 1.9e-6", Close(n.chiMuMu, 1.9e-6, 0.05),
        "chi = " + std::to_string(n.chiMuMu));
  Check("chi_Jpsi = chi_mumu / BR", Close(n.chiJpsi * kBrMuMu, n.chiMuMu, 1e-12));
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
  const long nGen = 300000;
  double sumW = 0., sumW2 = 0., sumPtSq = 0.;
  long nMuMu = 0;
  bool xfOk = true;
  std::map<int, long> yHist;
  double maxMassDev = 0.;
  for (long i = 0; i < nGen; ++i) {
    Event e = s.Next();
    ++nMuMu;
    sumW += e.weight;
    sumW2 += e.weight * e.weight;
    sumPtSq += e.jpsi.Pt() * e.jpsi.Pt();
    yHist[static_cast<int>(std::floor(e.yCM * 10))]++;
    const double ex = e.mup.E + e.mum.E, px = e.mup.px + e.mum.px,
                 py = e.mup.py + e.mum.py, pz = e.mup.pz + e.mum.pz;
    maxMassDev = std::max(
        maxMassDev,
        std::abs(std::sqrt(ex * ex - px * px - py * py - pz * pz) - kMJpsi));
    if (std::abs(e.xF) >= 1.0) xfOk = false;
  }
  Check("all events inside |x_F| < 1", xfOk);
  Check("nominal weights identical (N_eff = N)",
        Close(sumW * sumW / sumW2, nMuMu, 1e-9));
  Check("dimuon momenta sum to the J/psi mass", maxMassDev < 1e-6);
  Check("sampled <pT^2> matches the model",
        Close(sumPtSq / nMuMu, n.meanPtSq, 0.02));

  std::printf("\nRapidity shape vs SHiP Table 2 (normalised to the 0.4 bin)\n");
  const std::vector<std::pair<int, double>> table = {
      {4, 375.56}, {7, 240.60}, {10, 135.93}, {13, 53.78}, {16, 12.84}};
  const double ref = yHist[4] / 375.56;
  bool shapeOk = true;
  for (const auto& entry : table) {
    const double ratio = yHist[entry.first] / entry.second / ref;
    std::printf("    y = %.1f : sampled/table = %.3f\n", entry.first * 0.1, ratio);
    if (std::abs(ratio - 1) > 0.08) shapeOk = false;
  }
  Check("data shape reproduced within 8%", shapeOk);

  const double eps = 2e-3;
  const double dLo =
      std::abs(s.YDensity(cfg.dataLo - eps) / s.YDensity(cfg.dataLo + eps) - 1);
  const double dHi =
      std::abs(s.YDensity(cfg.dataHi - eps) / s.YDensity(cfg.dataHi + eps) - 1);
  Check("density continuous at the joins", dLo < 0.03 && dHi < 0.03,
        "jumps " + std::to_string(dLo) + ", " + std::to_string(dHi));

  // ---------------------------------------- polarisation
  std::printf("\nPolarisation\n");
  Check("f_cos(0.11) = 0.4867", Close(CosAcceptance(0.11), 0.48674, 1e-4));
  Check("f_cos(0) = 0.5", Close(CosAcceptance(0.0), 0.5, 1e-12));
  for (double lambda : {-0.5, -0.14, 0.3, 1.0}) {
    Config c = cfg;
    c.lambdaPol = lambda;
    Sampler sp(c);
    const bool normOk = Close(
        sp.GetNormalisation().chiMuMu * CosAcceptance(lambda), n.chiMuMu * 0.5,
        1e-9);
    const int kBins = 10;
    std::vector<long> hist(kBins, 0);
    const long nn = 200000;
    for (long i = 0; i < nn; ++i) {
      const double c2 = sp.Next().cosThetaCS;
      hist[std::min(kBins - 1, static_cast<int>((c2 + 1) * kBins / 2))]++;
    }
    double maxDev = 0.;
    for (int b = 0; b < kBins; ++b) {
      const double lo = -1 + 2.0 * b / kBins, hi = lo + 2.0 / kBins;
      const double expect =
          ((hi - lo) + lambda * (hi * hi * hi - lo * lo * lo) / 3) /
          (2 + 2 * lambda / 3);
      maxDev = std::max(maxDev, std::abs(hist[b] / double(nn) / expect - 1));
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

  // ---------------------------------------- shapes
  std::printf("\nRapidity models\n");
  for (auto shape : {YShape::Gauss, YShape::Hybrid, YShape::Data}) {
    Config c = cfg;
    c.yShape = shape;
    Sampler ss(c);
    long above = 0;
    const long nn = 100000;
    for (long i = 0; i < nn; ++i) {
      if (ss.Next().jpsi.P() > 200) ++above;
    }
    std::printf("    %-6s : f_y = %.3f, chi = %.3e, chi*P(p>200) = %.2e\n",
                shape == YShape::Gauss
                    ? "gauss"
                    : (shape == YShape::Hybrid ? "hybrid" : "data"),
                ss.GetNormalisation().fY, ss.GetNormalisation().chiMuMu,
                ss.GetNormalisation().chiMuMu * above / double(nn));
  }

  // ---------------------------------------- target model: vertex AND rate
  std::printf("\nTarget model\n");
  Config wOnly = cfg;
  wOnly.layers = {Layer{TungstenNA50(), 150.0}};
  Sampler sW(wOnly);
  const double pW = sW.GetNormalisation().probMuMuPerPot;
  std::printf("    thick W (150 cm) : P/POT = %.4e, chi = %.4e, ratio %.4f\n", pW,
              n.chiMuMu, pW / n.chiMuMu);
  Check("thick W: P/POT approaches chi_mumu",
        pW / n.chiMuMu > 0.99 && pW / n.chiMuMu <= 1.0001);

  Config mixed = cfg;
  mixed.layers = {Layer{MolybdenumScaled(), 58.0}, Layer{TungstenNA50(), 92.0}};
  Sampler sMix(mixed);
  const double pMix = sMix.GetNormalisation().probMuMuPerPot;
  std::printf("    Mo 58 cm + W 92 cm : P/POT = %.4e (%.1f%% of pure W)\n", pMix,
              100 * pMix / pW);
  Check("mixed target rate differs from pure W", pMix < pW && pMix > 0.5 * pW);
  Check("mixed target weight uses the integrated rate",
        Close(sMix.GetNormalisation().weight, cfg.nPot * pMix / cfg.nEvents,
              1e-9));
  double zSum = 0.;
  const long nz = 50000;
  for (long i = 0; i < nz; ++i) zSum += sMix.Next().z_cm;
  std::printf("    <z> = %.1f cm of 150 cm\n", zSum / nz);
  Check("vertex concentrated upstream", zSum / nz > 0 && zSum / nz < 40);

  // ---------------------------------------- validation and reproducibility
  std::printf("\nValidation and reproducibility\n");
  auto throws = [](Config c) {
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

  Config a = cfg, b = cfg;
  a.seed = 7;
  b.seed = 7;
  Sampler sa(a), sb(b);
  Event ea = sa.Next(), eb = sb.Next();
  Check("same seed reproduces the same event",
        ea.jpsi.px == eb.jpsi.px && ea.mup.pz == eb.mup.pz);

  std::printf("\n%s (%d failures)\n", gFailures ? "FAILED" : "ALL PASSED",
              gFailures);
  return gFailures ? 1 : 0;
}
