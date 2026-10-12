// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration
//
// JpsiDataMap.C: fits the J/psi generator's optional data map (jpsi::DataMap)
// to corrected dimuon data in (y, p_T) cells, such as the SHiP 2018
// muon-flux data. The map file it writes is used with "data_map <file>" in a
// configuration file (run_fixedTarget.py --jpsi-config). The chain is
// described in macro/jpsi/README.md.
//
//   root -l -b -q 'macro/jpsi/JpsiDataMap.C+("acceptance_sel0.root",
//       "gen_2018_mapbase.root", "jpsi_datamap.txt", "jpsi_datamap",
//       "acceptance_rpcm5.root")' > jpsi_datamap.log 2>&1
//
// Input:
//   acceptance.root of the 2018 J/psi analysis: corrected fiducial J/psi in
//     y x p_T cells (corr_cell2, the fit input) and p_z x p_T cells
//     (corr_cell1, the check), both for 0.6 < y < 1.6, corr_y, the POT, the
//     cell edges and the fiducial definition (both muons p > 20 GeV,
//     theta < 0.08).
//   the map base on the 2018 target (makeJpsiNtuple --layers target_2018.txt
//     --mu-pmin 20 --mu-thmax 0.1 --map-base: NA50 shape, the map with zero
//     parameters).
//   optionally a variation of the acceptance (accVar: the same analysis with
//     the RPC-1 window shrunk by 5 cm). A cell is used only if its corrected
//     value agrees between the two within tolVar (30%).
// Fit: the y distribution (corr_y, 0.2-wide bins over 0.6-1.6) fixes the y
//   shape and N; the p_T fractions inside each y slice of the cells
//   (normalised per slice, full covariance) fix the y-p_T correlation c.
// Model (jpsi::DataMap): the base (NA50) times
//     w(y, pT) = exp(D (b1 + b2 D) + c D (pT^2 - q0)), D = clamp(y - 0.6, 0, 1)
//   in the true J/psi y_cm and p_T. The fit reweights the base generator event
//   by event and applies the fiducial cut to the muons. By default the data
//   only fix the shape (N free, reported, not applied): the absolute rate stays
//   NA50 at the join y = 0.6. absolute = 1 fixes N = 1 instead. Nested fits
//   are reported (N only, + b1, + b2, + c).
// Forward tail: dN/dxF ~ (1 - |xF|)^n fitted to the corrected y distribution
//   from tailLo (1.0) to its last bin, N free (shape only). The base events
//   are reweighted with the sampler's own joint density (tail model / base),
//   so the fit uses the generator's p_T spectrum and kinematic limit. The
//   result (tail_n) makes the generator continue the map from its end with
//   this exponent instead of the SHiP table (forward_tail map). Printed:
//   n for tailLo 0.8, 1.0, 1.2, and the generator with the map and either
//   continuation against the corrected data in every y bin.
// Checks: the p_z x p_T cells, <p_T^2> per y and p_z slice, the absolute
//   y x p_T cells, before and after the map.
// Output: the map file (key value), outdir/datamap.root, outdir/*.png.
//
// JpsiSampler is compiled with the macro (it needs ROOT only), so no FairShip
// library has to be loaded; the sources are found
// relative to this file. Run it with ACLiC (the "+").

#include <algorithm>
#include <cinttypes>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <fstream>
#include <memory>
#include <stdexcept>
#include <string>
#include <vector>

#include "../../shipgen/JpsiDataMapFit.h"
#include "../../shipgen/JpsiSampler.h"
// the sampler itself, for the joint densities of the tail fit
#include "../../shipgen/JpsiSampler.cxx"  // NOLINT(build/include)
#include "TCanvas.h"
#include "TDecompChol.h"
#include "TFile.h"
#include "TH1D.h"
#include "TLegend.h"
#include "TLine.h"
#include "TLorentzVector.h"
#include "TMath.h"
#include "TMatrixD.h"
#include "TMatrixDSym.h"
#include "TNamed.h"
#include "TNtuple.h"
#include "TParameter.h"
#include "TROOT.h"
#include "TStyle.h"
#include "TSystem.h"
#include "TVectorD.h"

namespace jdmc {
const double kYBeamAna = 3.374;  // as in the analysis macros
double PairY(const TLorentzVector& p) {
  const double e = std::sqrt(p.P() * p.P() + jpsi::kMJpsi * jpsi::kMJpsi);
  return 0.5 * std::log((e + p.Pz()) / (e - p.Pz())) - kYBeamAna;
}
double PzOf(double y, double pt) {
  return std::sqrt(jpsi::kMJpsi * jpsi::kMJpsi + pt * pt) *
         std::sinh(y + kYBeamAna);
}
int Slot(const std::vector<double>& e, double v) {
  for (size_t i = 0; i + 1 < e.size(); ++i)
    if (v >= e[i] && v < e[i + 1]) return static_cast<int>(i);
  return -1;
}
double Par(TFile* f, const char* n, double d = NAN) {
  auto* p = f ? dynamic_cast<TParameter<double>*>(f->Get(n)) : nullptr;
  return p ? p->GetVal() : d;
}
std::vector<double> Edges(TFile* f, const char* n) {
  auto* v = f ? dynamic_cast<TVectorD*>(f->Get(n)) : nullptr;
  std::vector<double> e;
  if (v)
    for (int i = 0; i < v->GetNrows(); ++i) e.push_back((*v)[i]);
  return e;
}
// binned <p_T^2> of slice s of a flattened (slice x nPt) vector, same estimator
// as JpsiPlots.C
void PtSq(const std::vector<double>& v, const std::vector<double>& ev,
          const std::vector<double>& ptS, int s, double& m, double& e) {
  const int n = ptS.size() - 1;
  double sum = 0;
  double sq = 0;
  std::vector<double> q(n);
  for (int j = 0; j < n; ++j) {
    q[j] =
        (ptS[j] * ptS[j] + ptS[j] * ptS[j + 1] + ptS[j + 1] * ptS[j + 1]) / 3.;
    sum += v[s * n + j];
    sq += v[s * n + j] * q[j];
  }
  m = sum > 0 ? sq / sum : NAN;
  double e2 = 0;
  for (int j = 0; j < n; ++j)
    e2 += std::pow((q[j] - m) / sum * (ev.empty() ? 0. : ev[s * n + j]), 2);
  e = std::sqrt(e2);
}
}  // namespace jdmc

void JpsiDataMap(const char* accFile = "jpsi_acceptance_sel0/acceptance.root",
                 const char* genFile = "gen_2018_mapbase.root",
                 const char* outMap = "jpsi_datamap.txt",
                 const char* outdir = "jpsi_datamap", const char* accVar = "",
                 double tolVar = 0.30, double sysFrac = 0.05, int absolute = 0,
                 double q0 = 1.5, double qMax = 16., double tailLo = 1.0) {
  using namespace jdmc;
  gROOT->SetBatch(true);
  gStyle->SetOptStat(0);
  gSystem->mkdir(outdir, true);
  const std::string dir(outdir);

  // ------------------------------------------------------------ corrected data
  TFile* fa = TFile::Open(accFile);
  if (!fa || fa->IsZombie()) {
    printf("cannot open %s\n", accFile);
    return;
  }
  const std::vector<double> ySl = Edges(fa, "cell_y_edges");
  const std::vector<double> pzS = Edges(fa, "cell_pz_edges");
  const std::vector<double> ptS = Edges(fa, "cell_pt_edges");
  TH1D* c2 = dynamic_cast<TH1D*>(fa->Get("corr_cell2"));
  TH1D* c1 = dynamic_cast<TH1D*>(fa->Get("corr_cell1"));
  TH1D* cy = dynamic_cast<TH1D*>(fa->Get("corr_y"));
  const double pot = Par(fa, "pot_data");
  const double pMin = Par(fa, "p_min_fid", 20.);
  const double thMax = Par(fa, "th_max_fid", 0.08);
  const double yLo = Par(fa, "cell_y_lo");
  const double yHi = Par(fa, "cell_y_hi");
  if (ySl.size() < 2 || pzS.size() < 2 || ptS.size() < 2 || !c2 || !c1 ||
      !(pot > 0) || !std::isfinite(yLo)) {
    printf(
        "%s has no cell edges, cells or POT: not an acceptance file of the "
        "2018 J/psi analysis with the data-map grid\n",
        accFile);
    return;
  }
  const int nY = ySl.size() - 1;
  const int nPz = pzS.size() - 1;
  const int nPt = ptS.size() - 1;
  const int nC = nY * nPt;
  const int nC1 = nPz * nPt;
  const int selMode = static_cast<int>(Par(fa, "sel_mode", -1));
  printf(
      "corrected 2018 data: %s (selection %d), POT %.4g, fiducial p > %.0f "
      "GeV, theta < %.3f\n",
      accFile, selMode, pot, pMin, thMax);
  printf("  fit cells: y x p_T, y edges");
  for (double v : ySl) printf(" %.2f", v);
  printf(", p_T edges");
  for (double v : ptS) printf(" %.2f", v);
  printf("\n  check cells: p_z x p_T (%.1f < y < %.1f), p_z edges", yLo, yHi);
  for (double v : pzS) printf(" %.0f", v);
  printf("\n");
  std::vector<double> d2(nC);
  std::vector<double> e2(nC);
  std::vector<double> d1(nC1);
  std::vector<double> e1(nC1);
  for (int i = 0; i < nC; ++i) {
    d2[i] = c2->GetBinContent(i + 1) / pot;
    e2[i] = c2->GetBinError(i + 1) / pot;
  }
  for (int i = 0; i < nC1; ++i) {
    d1[i] = c1->GetBinContent(i + 1) / pot;
    e1[i] = c1->GetBinError(i + 1) / pot;
  }

  // ------------------------------------------------------------ cells
  // validated by the acceptance variation
  std::vector<int> use2(nC, 1);
  std::vector<int> use1(nC1, 1);
  std::vector<double> rv2(nC, NAN);
  std::vector<double> rv1(nC1, NAN);
  if (accVar && accVar[0]) {
    TFile* fv = TFile::Open(accVar);
    TH1D* v2 = fv ? dynamic_cast<TH1D*>(fv->Get("corr_cell2")) : nullptr;
    TH1D* v1 = fv ? dynamic_cast<TH1D*>(fv->Get("corr_cell1")) : nullptr;
    const std::vector<double> ySv = Edges(fv, "cell_y_edges");
    const std::vector<double> ptSv = Edges(fv, "cell_pt_edges");
    if (!v2 || !v1 || ySv != ySl || ptSv != ptS) {
      printf(
          "%s: no cells or a different grid than the nominal acceptance file\n",
          accVar);
      return;
    }
    // A whole y slice moving together is a normalisation effect, which the
    // p_T-shape fit does not see (and which the map fitted on the variation
    // file quantifies). A single cell far off means its acceptance or one of
    // its two mass fits failed: such cells are not used.
    auto check = [&](TH1D* hn, TH1D* hv, int n, std::vector<int>& use,
                     std::vector<double>& rv) {
      for (int i = 0; i < n; ++i) {
        const double a = hn->GetBinContent(i + 1);
        const double b = hv->GetBinContent(i + 1);
        if (!(a > 0 && b > 0)) {
          use[i] = a > 0 ? 0 : use[i];
          continue;
        }
        rv[i] = b / a;
        use[i] = std::fabs(rv[i] - 1.) < tolVar;
      }
    };
    check(c2, v2, nC, use2, rv2);
    check(c1, v1, nC1, use1, rv1);
    int n2 = 0;
    for (int i = 0; i < nC; ++i) n2 += use2[i];
    printf(
        "acceptance check with %s (a cell is used if variation / nominal is "
        "within %.0f%%): %d of %d y x p_T cells used\n",
        accVar, 100 * tolVar, n2, nC);
    printf("    y          p_T [GeV]    variation / nominal   used\n");
    for (int i = 0; i < nC; ++i)
      printf("    %.2f-%.2f  %4.2f-%-4.2f     %6.3f              %s\n",
             ySl[i / nPt], ySl[i / nPt + 1], ptS[i % nPt], ptS[i % nPt + 1],
             rv2[i], use2[i] ? "yes" : "NO (acceptance or mass fit unstable)");
  } else {
    printf(
        "WARNING: no acceptance variation given: every cell is fitted, "
        "including cells whose acceptance is not validated\n");
  }

  // ------------------------------------------------------------ base generator
  TFile* fg = TFile::Open(genFile);
  TNtuple* nt = fg ? dynamic_cast<TNtuple*>(fg->Get("jpsi")) : nullptr;
  if (!nt) {
    printf("no generator ntuple in %s\n", genFile);
    return;
  }
  const double nPot = Par(fg, "n_pot");
  const double hasMap = Par(fg, "data_map", 0.);
  const double mb1 = Par(fg, "map_b1", 0.);
  const double mb2 = Par(fg, "map_b2", 0.);
  const double mc = Par(fg, "map_c", 0.);
  const double mJoin = Par(fg, "map_y_join", NAN);
  const double mHi = Par(fg, "map_y_hi", NAN);
  const double pBeam = Par(fg, "p_beam", 400.);
  const double muP = Par(fg, "mu_pmin", 0.);
  const double muTh = Par(fg, "mu_thmax", 10.);
  const double meanPtSq = Par(fg, "mean_pt_sq");
  const double ptSqSlope = Par(fg, "pt_sq_slope");
  const double lambda = Par(fg, "lambda_pol", 0.);
  const double nLayers = Par(fg, "n_layers", 0.);
  if (hasMap != 1. || mb1 != 0. || mb2 != 0. || mc != 0.) {
    printf(
        "%s is not the map base (data map %.0f, b1 %.3f b2 %.3f c %.3f): "
        "generate it with\n"
        "  makeJpsiNtuple --layers macro/jpsi/target_2018.txt --mu-pmin 20 "
        "--mu-thmax 0.1 --map-base\n",
        genFile, hasMap, mb1, mb2, mc);
    return;
  }
  if (std::fabs(mJoin - yLo) > 1e-6 || std::fabs(mHi - yHi) > 1e-6) {
    printf(
        "the map base has y_join %.2f, y_hi %.2f but the data cells cover "
        "%.2f-%.2f\n",
        mJoin, mHi, yLo, yHi);
    return;
  }
  if (muP > pMin + 1e-6 || muTh < thMax - 1e-9) {
    printf(
        "%s has a muon pre-selection (p > %.1f, theta < %.3f) tighter than the "
        "fiducial region\n",
        genFile, muP, muTh);
    return;
  }
  if (!(nLayers > 0))
    printf(
        "WARNING: %s is not in layer mode: weights per interacting proton, not "
        "per POT\n",
        genFile);
  const double eB = std::hypot(pBeam, jpsi::kMProton);
  const double yShift = std::atanh(pBeam / (eB + jpsi::kMProton));
  printf(
      "base generator: %s, %.3g protons, <pT^2>(y=0) %.3f, pT^2 slope %.2f, "
      "lambda %.2f, beam rapidity %.4f\n",
      genFile, nPot, meanPtSq, ptSqSlope, lambda, yShift);

  jpsi::DataMap m;  // for D and the cap; the parameters are fitted
  m.on = true;
  m.yJoin = yLo;
  m.yHi = yHi;
  m.q0 = q0;
  m.qMax = qMax;
  std::vector<jdm::Ev> ev2;
  std::vector<jdm::Ev> ev1;  // fit cells, check cells
  std::vector<double> yb;  // corr_y bins inside the cell range, for the y check
  std::vector<int> ybIdx;
  if (cy)
    for (int i = 1; i <= cy->GetNbinsX(); ++i)
      if (cy->GetXaxis()->GetBinLowEdge(i) > yLo - 1e-6 &&
          cy->GetXaxis()->GetBinUpEdge(i) < yHi + 1e-6)
        ybIdx.push_back(i);
  std::vector<jdm::Ev> evY;
  // every fiducial event, for the forward tail and the generator check: true
  // y_cm and p_T, weight, corr_y bin (any bin, 0-based; -1 outside)
  std::vector<double> allY;
  std::vector<double> allPt;
  std::vector<double> allW;
  std::vector<int> allBin;
  int64_t nFid = 0;
  for (Long64_t k = 0; k + 1 < nt->GetEntries(); k += 2) {
    nt->GetEntry(k);
    float* r = nt->GetArgs();
    TLorentzVector a;
    TLorentzVector b;
    TLorentzVector J(r[7], r[8], r[9], r[10]);
    a.SetXYZM(r[1], r[2], r[3], jpsi::kMMu);
    const double w = r[11] / nPot;
    nt->GetEntry(k + 1);
    r = nt->GetArgs();
    b.SetXYZM(r[1], r[2], r[3], jpsi::kMMu);
    if (!(a.P() > pMin && a.Theta() < thMax && b.P() > pMin &&
          b.Theta() < thMax))
      continue;
    const TLorentzVector P = a + b;
    const double yA = PairY(P);
    const double ptA = P.Pt();
    const double yT = J.Rapidity() - yShift;
    const double ptT = J.Pt();
    const double d = jpsi::DataMapDy(m, yT);
    const double q = std::min(ptT * ptT, qMax) - q0;
    ++nFid;
    const int iy = Slot(ySl, yA);
    const int ip = Slot(ptS, ptA);
    ev2.push_back({(iy >= 0 && ip >= 0) ? iy * nPt + ip : -1, d, q, w});
    const int iz = (yA > yLo && yA < yHi) ? Slot(pzS, PzOf(yA, ptA)) : -1;
    ev1.push_back({(iz >= 0 && ip >= 0) ? iz * nPt + ip : -1, d, q, w});
    int jy = -1;
    for (size_t j = 0; j < ybIdx.size(); ++j)
      if (yA >= cy->GetXaxis()->GetBinLowEdge(ybIdx[j]) &&
          yA < cy->GetXaxis()->GetBinUpEdge(ybIdx[j]))
        jy = j;
    evY.push_back({jy, d, q, w});
    if (cy) {
      const int kb = cy->GetXaxis()->FindFixBin(yA) - 1;
      allY.push_back(yT);
      allPt.push_back(ptT);
      allW.push_back(w);
      allBin.push_back(kb >= 0 && kb < cy->GetNbinsX() ? kb : -1);
    }
  }
  printf("  %" PRId64 " fiducial generator J/psi\n", nFid);

  // ------------------------------------------------------------ the fit: y
  // distribution + p_T shape per y slice The y shape and the normalisation come
  // from the 1D analysis (corr_y, 0.2-wide bins, the validated yields); the
  // y-p_T correlation from the p_T fractions inside each y slice of the cells.
  // Normalising the cells per slice removes any y-dependent normalisation
  // (acceptance at low y, the RPC-margin shift of whole slices), so c measures
  // only how the p_T SHAPE changes with y.
  if (!cy || ybIdx.empty()) {
    printf("no corr_y in the acceptance file\n");
    return;
  }
  const int nYb = ybIdx.size();
  std::vector<double> yD(nYb);
  std::vector<double> yE(nYb);
  for (int j = 0; j < nYb; ++j) {
    yD[j] = cy->GetBinContent(ybIdx[j]) / pot;
    yE[j] = cy->GetBinError(ybIdx[j]) / pot;
  }
  // per y slice: the used cells, the data fractions and the whitening (Cholesky
  // of their covariance, one fraction dropped since they sum to 1)
  struct Slice {
    std::vector<int> cells;
    std::vector<double> f;
    std::vector<double> ef;
    TMatrixD W;  // inverse of the Cholesky factor of the covariance
    bool ok = false;
  };
  std::vector<Slice> sl(nY);
  for (int s = 0; s < nY; ++s) {
    Slice& S = sl[s];
    double sum = 0;
    double v2 = 0;
    for (int j = 0; j < nPt; ++j) {
      const int i = s * nPt + j;
      if (use2[i] && d2[i] > 0 && e2[i] > 0) {
        S.cells.push_back(i);
        sum += d2[i];
      }
    }
    if (S.cells.size() < 2) continue;
    std::vector<double> sg2;
    for (int i : S.cells) {
      sg2.push_back(e2[i] * e2[i] + std::pow(sysFrac * d2[i], 2));
      v2 += sg2.back();
    }
    for (size_t a = 0; a < S.cells.size(); ++a)
      S.f.push_back(d2[S.cells[a]] / sum);
    for (size_t a = 0; a < S.cells.size(); ++a)
      S.ef.push_back(std::sqrt(std::max(0., sg2[a] * (1 - 2 * S.f[a]) +
                                                S.f[a] * S.f[a] * v2)) /
                     sum);
    const int k = S.cells.size() - 1;
    TMatrixDSym C(k);
    for (int a = 0; a < k; ++a)
      for (int b = 0; b < k; ++b)
        C(a, b) = ((a == b ? sg2[a] : 0.) - S.f[b] * sg2[a] - S.f[a] * sg2[b] +
                   S.f[a] * S.f[b] * v2) /
                  (sum * sum);
    // C = U^T U: the residuals (U^T)^-1 d have unit covariance
    TDecompChol chol(C);
    S.ok = chol.Decompose();
    if (S.ok) {
      S.W.ResizeTo(k, k);
      S.W.Transpose(chol.GetU());
      S.W.Invert();
    }
  }
  auto slicePred = [&](const std::vector<double>& P, const Slice& S) {
    double t = 0;
    for (int i : S.cells) t += P[i];
    std::vector<double> f;
    for (int i : S.cells) f.push_back(t > 0 ? P[i] / t : 0.);
    return f;
  };
  int nResY = 0;
  int nResS = 0;
  std::vector<double> chiParts(2, 0.);
  auto resid = [&](const std::vector<double>& p) {
    std::vector<double> r;
    std::vector<double> S;
    std::vector<double> V;
    std::vector<double> P;
    std::vector<double> VP;
    std::vector<std::vector<double>> dS;
    jdm::Sums(evY, nYb, p, S, dS, V);
    const double N = std::exp(p[3]);
    double cy2 = 0;
    double cs2 = 0;
    for (int j = 0; j < nYb; ++j) {
      const double sg = std::sqrt(yE[j] * yE[j] + std::pow(sysFrac * yD[j], 2) +
                                  N * N * V[j]);
      r.push_back((N * S[j] - yD[j]) / sg);
      cy2 += r.back() * r.back();
    }
    nResY = r.size();
    jdm::Sums(ev2, nC, p, P, dS, VP);
    for (const Slice& Sl : sl) {
      if (!Sl.ok) continue;
      const std::vector<double> f = slicePred(P, Sl);
      TVectorD d(Sl.cells.size() - 1);
      for (size_t a = 0; a + 1 < Sl.cells.size(); ++a) d[a] = f[a] - Sl.f[a];
      const TVectorD x = Sl.W * d;
      for (int a = 0; a < x.GetNrows(); ++a) {
        r.push_back(x[a]);
        cs2 += x[a] * x[a];
      }
    }
    nResS = r.size() - nResY;
    chiParts[0] = cy2;
    chiParts[1] = cs2;
    return r;
  };
  struct Model {
    const char* name;
    std::vector<bool> fixed;
  };
  const bool fixN = absolute != 0;
  const std::vector<Model> models = {
      {"no correction (N only)", {true, true, true, fixN}},
      {"+ b1 (y slope)", {false, true, true, fixN}},
      {"+ b2 (y curvature)", {false, false, true, fixN}},
      {"+ c (y-pT correlation) = the map", {false, false, false, fixN}}};
  printf(
      "\nfit: y distribution (corr_y, %d bins, %s) + p_T shape inside the %d y "
      "slices (fractions)\n"
      "     per-bin systematic %.0f%% added in quadrature\n",
      nYb, fixN ? "absolute, N = 1" : "N free, not applied", nY, 100 * sysFrac);
  printf(
      "    model                                   chi2 / ndf  (y + shape)     "
      "  p        b1              b2              c               N\n");
  std::vector<jdm::Result> fits;
  std::vector<std::vector<double>> parts;
  std::vector<double> start = {0., 0., 0., 0.};
  for (const Model& md : models) {
    jdm::Result r = jdm::FitResid(resid, start, md.fixed);
    resid(r.par);
    parts.push_back(chiParts);
    fits.push_back(r);
    start = r.par;
    auto pe = [&](int k) {
      return md.fixed[k]
                 ? std::string("       -       ")
                 : std::string(Form("%6.3f+-%5.3f", r.par[k], r.err[k]));
    };
    printf(
        "    %-38s %6.1f / %-3d (%5.1f + %5.1f)  %8.2g   %s  %s  %s  "
        "%5.3f+-%5.3f\n",
        md.name, r.chi2, r.ndf, chiParts[0], chiParts[1],
        TMath::Prob(r.chi2, r.ndf), pe(0).c_str(), pe(1).c_str(), pe(2).c_str(),
        std::exp(r.par[3]), std::exp(r.par[3]) * r.err[3]);
    if (!r.ok)
      printf("    WARNING: %s: covariance not invertible, no uncertainties\n",
             md.name);
  }
  const jdm::Result& F = fits.back();
  const jdm::Result& F0 = fits.front();
  printf("    residuals: %d y bins, %d shape fractions\n", nResY, nResS);
  for (size_t k = 1; k < fits.size(); ++k)
    printf(
        "    delta chi2 adding %-28s %6.1f  (%.1f sigma for one parameter)\n",
        models[k].name + 2, fits[k - 1].chi2 - fits[k].chi2,
        std::sqrt(std::max(0., fits[k - 1].chi2 - fits[k].chi2)));
  if (F.ok)
    printf(
        "    correlation of the map parameters: b1-b2 %+.2f, b1-c %+.2f, b2-c "
        "%+.2f\n",
        F.cov[0][1] / std::max(1e-30, F.err[0] * F.err[1]),
        F.cov[0][2] / std::max(1e-30, F.err[0] * F.err[2]),
        F.cov[1][2] / std::max(1e-30, F.err[1] * F.err[2]));
  if (!fixN)
    printf(
        "    N = %.3f +- %.3f: corrected data / generator at the join (y = "
        "%.1f), per POT; 1 = NA50 normalisation holds\n",
        std::exp(F.par[3]), std::exp(F.par[3]) * F.err[3], yLo);

  // ------------------------------------------------------------ tables: y, p_T
  // shape per slice, cells
  const double N = std::exp(F.par[3]);
  auto predict = [&](const std::vector<jdm::Ev>& ev, int n,
                     const std::vector<double>& p) {
    std::vector<double> S;
    std::vector<double> V;
    std::vector<std::vector<double>> dS;
    jdm::Sums(ev, n, p, S, dS, V);
    for (double& v : S) v *= std::exp(p[3]);
    return S;
  };
  const std::vector<double> p0 = {0., 0., 0., F.par[3]};
  const std::vector<double> yB = predict(evY, nYb, p0);
  const std::vector<double> yF = predict(evY, nYb, F.par);
  printf(
      "\ny distribution (fit input), per POT (generator x N = %.3f)\n"
      "    y            data                    NA50 base    map gen      "
      "data/base        data/map\n",
      N);
  for (int j = 0; j < nYb; ++j)
    printf(
        "    %.1f-%.1f    %9.3e +- %8.2e   %9.3e    %9.3e    %5.3f +- %5.3f    "
        "%5.3f +- %5.3f\n",
        cy->GetXaxis()->GetBinLowEdge(ybIdx[j]),
        cy->GetXaxis()->GetBinUpEdge(ybIdx[j]), yD[j], yE[j], yB[j], yF[j],
        yB[j] > 0 ? yD[j] / yB[j] : NAN, yB[j] > 0 ? yE[j] / yB[j] : NAN,
        yF[j] > 0 ? yD[j] / yF[j] : NAN, yF[j] > 0 ? yE[j] / yF[j] : NAN);
  const std::vector<double> base = predict(ev2, nC, p0);
  const std::vector<double> fit = predict(ev2, nC, F.par);
  printf(
      "\np_T shape inside each y slice (fit input): fraction of the slice in "
      "each p_T bin\n"
      "    y          p_T [GeV]     data               NA50 base    map        "
      "pull(map)\n");
  for (int s = 0; s < nY; ++s) {
    const Slice& S = sl[s];
    if (!S.ok) {
      printf("    %.2f-%.2f  (fewer than 2 usable cells)\n", ySl[s],
             ySl[s + 1]);
      continue;
    }
    const std::vector<double> fb = slicePred(base, S);
    const std::vector<double> ff = slicePred(fit, S);
    for (size_t a = 0; a < S.cells.size(); ++a) {
      const int i = S.cells[a];
      printf(
          "    %.2f-%.2f  %4.2f-%-4.2f     %6.3f +- %5.3f     %6.3f      %6.3f "
          "    %+5.2f\n",
          ySl[s], ySl[s + 1], ptS[i % nPt], ptS[i % nPt + 1], S.f[a], S.ef[a],
          fb[a], ff[a], S.ef[a] > 0 ? (S.f[a] - ff[a]) / S.ef[a] : NAN);
    }
  }
  printf(
      "\ny x p_T cells, absolute per POT (not fitted as such; generator x N = "
      "%.3f)\n",
      N);
  printf(
      "    y          p_T [GeV]     data                    NA50 base    map "
      "gen      data/base        data/map%s\n",
      accVar && accVar[0] ? "        variation/nominal" : "");
  for (int i = 0; i < nC; ++i) {
    const int iy = i / nPt;
    const int ip = i % nPt;
    const double s = std::sqrt(e2[i] * e2[i] + std::pow(sysFrac * d2[i], 2));
    printf(
        "    %.2f-%.2f  %4.2f-%-4.2f   %9.3e +- %8.2e   %9.3e    %9.3e    "
        "%5.3f +- %5.3f    %5.3f +- %5.3f   %6.3f%s\n",
        ySl[iy], ySl[iy + 1], ptS[ip], ptS[ip + 1], d2[i], e2[i], base[i],
        fit[i], base[i] > 0 ? d2[i] / base[i] : NAN,
        base[i] > 0 ? s / base[i] : NAN, fit[i] > 0 ? d2[i] / fit[i] : NAN,
        fit[i] > 0 ? s / fit[i] : NAN, rv2[i], use2[i] ? "" : "   not used");
  }

  // ------------------------------------------------------------ checks
  const std::vector<double> b1v = predict(ev1, nC1, p0);
  const std::vector<double> f1v = predict(ev1, nC1, F.par);
  auto chi2Of = [&](const std::vector<double>& d, const std::vector<double>& e,
                    const std::vector<double>& g) {
    double c = 0;
    int n = 0;
    for (size_t i = 0; i < d.size(); ++i)
      if (use1[i] && d[i] > 0 && e[i] > 0) {
        c += std::pow(d[i] - g[i], 2) /
             (e[i] * e[i] + std::pow(sysFrac * d[i], 2));
        ++n;
      }
    return std::make_pair(c, n);
  };
  const auto cb1 = chi2Of(d1, e1, b1v);
  const auto cf1 = chi2Of(d1, e1, f1v);  // validated cells only
  printf(
      "\ncheck: p_z x p_T cells (not fitted; the same events as the fit, so "
      "not independent), per POT\n");
  printf(
      "    p_z [GeV]  p_T [GeV]     data                    NA50 base    map "
      "gen      data/base        data/map\n");
  for (int i = 0; i < nC1; ++i) {
    const int iz = i / nPt;
    const int ip = i % nPt;
    const double s = std::sqrt(e1[i] * e1[i] + std::pow(sysFrac * d1[i], 2));
    printf(
        "    %3.0f-%-4.0f   %4.2f-%-4.2f   %9.3e +- %8.2e   %9.3e    %9.3e    "
        "%5.3f +- %5.3f    %5.3f +- %5.3f%s\n",
        pzS[iz], pzS[iz + 1], ptS[ip], ptS[ip + 1], d1[i], e1[i], b1v[i],
        f1v[i], b1v[i] > 0 ? d1[i] / b1v[i] : NAN,
        b1v[i] > 0 ? s / b1v[i] : NAN, f1v[i] > 0 ? d1[i] / f1v[i] : NAN,
        f1v[i] > 0 ? s / f1v[i] : NAN,
        use1[i] ? "" : "   acceptance not validated");
  }
  printf(
      "    chi2 over the validated cells: NA50 base %.1f / %d, map %.1f / %d\n",
      cb1.first, cb1.second, cf1.first, cf1.second);

  printf(
      "\ncheck: binned <p_T^2> [GeV^2] per slice (same estimator for data and "
      "generator; * = the slice has cells\n"
      "       whose acceptance is not validated, so the data value there is "
      "not reliable)\n");
  printf("    slice               data               base      map\n");
  for (int g = 0; g < 2; ++g) {
    const std::vector<double>& ed = g == 0 ? ySl : pzS;
    const std::vector<double>& dd = g == 0 ? d2 : d1;
    const std::vector<double>& ee = g == 0 ? e2 : e1;
    const std::vector<double>& bb = g == 0 ? base : b1v;
    const std::vector<double>& ff = g == 0 ? fit : f1v;
    for (size_t s = 0; s + 1 < ed.size(); ++s) {
      double md;
      double emd;
      double mb;
      double eb;
      double mf;
      double ef;
      PtSq(dd, ee, ptS, s, md, emd);
      PtSq(bb, {}, ptS, s, mb, eb);
      PtSq(ff, {}, ptS, s, mf, ef);
      bool all = true;
      for (int j = 0; j < nPt; ++j)
        all &= (g == 0 ? use2 : use1)[s * nPt + j] != 0;
      printf("    %s %6.2f-%-6.2f %s %6.3f +- %5.3f     %6.3f    %6.3f\n",
             g == 0 ? "y  " : "p_z", ed[s], ed[s + 1], all ? " " : "*", md, emd,
             mb, mf);
    }
  }
  printf(
      "\nthe map at a few points: w(y, p_T) relative to the base generator (N "
      "not included)\n    y      ");
  const double ptPts[] = {0., 1., 1.5, 2., 3., 4.};
  for (double pt : ptPts) printf("  p_T %3.1f", pt);
  printf("\n");
  jpsi::DataMap mf = m;
  mf.b1 = F.par[0];
  mf.b2 = F.par[1];
  mf.c = F.par[2];
  for (double y : {0.6, 0.8, 1.0, 1.2, 1.4, 1.6, 1.8}) {
    printf("    %.1f   ", y);
    for (double pt : ptPts) printf("  %7.3f", jpsi::DataMapWeight(mf, y, pt));
    printf("\n");
  }

  // ------------------------------------------------------------ forward tail
  // The base generator is rebuilt from the settings stored with the sample:
  // its joint density J_base(y, p_T) is what the events were drawn from. A
  // model is applied to the events with the weight J_model / J_base.
  jpsi::Config bc;
  bc.pBeam = pBeam;
  bc.yShape =
      static_cast<jpsi::YShape>(static_cast<int>(Par(fg, "y_shape", 2.)));
  bc.tailN = Par(fg, "tail_n", 5.5);
  bc.dataLo = Par(fg, "data_lo", 0.4);
  bc.dataHi = Par(fg, "data_hi", 2.0);
  bc.yGauss0 = Par(fg, "y_gauss_mean", bc.yGauss0);
  bc.yGaussSigma = Par(fg, "y_gauss_sigma", bc.yGaussSigma);
  bc.T = Par(fg, "T", bc.T);
  bc.p0 = Par(fg, "p0", bc.p0);
  bc.nPow = Par(fg, "pt_pow_n", bc.nPow);
  bc.ptSq = Par(fg, "pt_sq", -1.);
  bc.fHard = Par(fg, "f_hard", bc.fHard);
  bc.ptSqSlope = ptSqSlope;
  bc.thermalJacobian = Par(fg, "thermal_jacobian", 1.) != 0.;
  bc.lambdaPol = lambda;
  bc.dataMap.on = true;
  bc.dataMap.yJoin = mJoin;
  bc.dataMap.yHi = mHi;
  bc.dataMap.q0 = Par(fg, "map_ptsq_ref", q0);
  bc.dataMap.qMax = Par(fg, "map_ptsq_max", qMax);
  bc.forwardTail = static_cast<jpsi::ForwardTail>(
      static_cast<int>(Par(fg, "forward_tail", 0.)));
  bc.nEvents = 1;
  const double tailN0 = 5.5;  // reference exponent (the SHiP table's)
  const std::vector<double> loScan = {0.8, 1.0, 1.2};
  struct TailOut {
    double lo = NAN;
    double hi = NAN;
    std::vector<int> bins;  // corr_y bins (0-based)
    std::vector<jdm::TailBin> tb;
    jdm::TailResult r;
    double chi2Ref = NAN;
    double nRef = NAN;  // n = tailN0, N refitted
  };
  std::vector<TailOut> tails;
  TailOut tail;  // the one written to the map file (tailLo)
  bool tailOk = false;
  std::vector<double> gBase;
  std::vector<double> gTable;
  std::vector<double> gTail;  // generator per corr_y bin
  std::string tailWhy;
  try {
    if (!cy || allY.empty()) throw std::runtime_error("no corr_y");
    if (Par(fg, "alpha_xf1", 0.) != 0. || Par(fg, "alpha_xf2", 0.) != 0.)
      throw std::runtime_error(
          "the map base has the nuclear x_F factor on: generate it without");
    const jpsi::Sampler base(bc);
    const double rPt = base.GetNormalisation().meanPtSq / meanPtSq;
    const double rFy = base.GetNormalisation().fY / Par(fg, "f_y", NAN);
    printf(
        "\nforward tail: base generator rebuilt from %s: <pT^2> and f_y "
        "reproduced to %.1e and %.1e\n",
        genFile, rPt - 1., rFy - 1.);
    if (!(std::fabs(rPt - 1.) < 1e-4 && std::fabs(rFy - 1.) < 1e-4))
      throw std::runtime_error(
          "the base generator could not be rebuilt from its stored settings "
          "(different sampler version?)");
    const double sqrtS = base.SqrtS();
    const int nCy = cy->GetNbinsX();
    std::vector<double> jb(allY.size());
    for (size_t i = 0; i < allY.size(); ++i)
      jb[i] = base.JointDensity(allY[i], allPt[i]);
    auto fitAt = [&](double lo) {
      TailOut t;
      t.lo = lo;
      jpsi::Config tc = bc;
      tc.dataMap = jpsi::DataMap();
      tc.forwardTail = jpsi::ForwardTail::Table;
      tc.yShape = jpsi::YShape::Data;
      tc.dataHi = lo;
      tc.tailN = tailN0;
      const jpsi::Sampler ts(tc);
      std::vector<int> idx(nCy, -1);
      for (int k = 0; k < nCy; ++k)
        if (cy->GetXaxis()->GetBinLowEdge(k + 1) > lo - 1e-6 &&
            cy->GetBinContent(k + 1) > 0 && cy->GetBinError(k + 1) > 0) {
          idx[k] = t.bins.size();
          t.bins.push_back(k);
        }
      if (t.bins.empty()) return t;
      t.hi = cy->GetXaxis()->GetBinUpEdge(t.bins.back() + 1);
      std::vector<int> eb;
      std::vector<double> bw;
      std::vector<double> L;
      for (size_t i = 0; i < allY.size(); ++i) {
        if (allBin[i] < 0 || idx[allBin[i]] < 0 || !(jb[i] > 0)) continue;
        const double xf =
            2 * std::hypot(jpsi::kMJpsi, allPt[i]) * std::sinh(allY[i]) / sqrtS;
        eb.push_back(idx[allBin[i]]);
        bw.push_back(allW[i] * ts.JointDensity(allY[i], allPt[i]) / jb[i]);
        L.push_back(std::log(std::max(1e-300, 1. - std::fabs(xf))));
      }
      t.tb = jdm::GroupTail(eb, bw, L, t.bins.size());
      for (size_t j = 0; j < t.bins.size(); ++j) {
        t.tb[j].D = cy->GetBinContent(t.bins[j] + 1) / pot;
        t.tb[j].eD = cy->GetBinError(t.bins[j] + 1) / pot;
      }
      t.r = jdm::FitTail(t.tb, tailN0, sysFrac);
      t.chi2Ref = jdm::TailChi2(t.tb, tailN0, tailN0, sysFrac, t.nRef);
      return t;
    };
    std::vector<double> los = loScan;
    if (std::find(los.begin(), los.end(), tailLo) == los.end())
      los.push_back(tailLo);
    for (double lo : los) {
      tails.push_back(fitAt(lo));
      if (lo == tailLo) tail = tails.back();
    }
    printf(
        "  dN/dxF ~ (1 - |xF|)^n fitted to corr_y from y_lo to the last bin, "
        "N free; systematic %.0f%% per bin\n"
        "    y_lo  y_hi  bins   n                    chi2 / ndf     chi2 at "
        "n = %.1f (Table 5 fit)\n",
        100 * sysFrac, tailN0);
    for (const TailOut& t : tails)
      printf(
          "    %.1f   %.1f   %zu     %5.2f  -%4.2f +%4.2f      %5.2f / %d    "
          "%6.2f%s\n",
          t.lo, t.hi, t.bins.size(), t.r.n, t.r.enLo, t.r.enHi, t.r.chi2,
          t.r.ndf, t.chi2Ref, t.lo == tailLo ? "   <- used" : "");
    tailOk = tail.r.ok;
    if (!tailOk)
      tailWhy = "Minos found no Delta chi2 = 1 interval for 1 < n < 25";

    // generator with the fitted map, continued with the SHiP table (as
    // before) and with the fitted tail from the end of the map
    jpsi::Config gT = bc;
    gT.dataMap.b1 = F.par[0];
    gT.dataMap.b2 = F.par[1];
    gT.dataMap.c = F.par[2];
    gT.dataMap.q0 = q0;
    gT.dataMap.qMax = qMax;
    gT.forwardTail = jpsi::ForwardTail::Table;
    const jpsi::Sampler sT(gT);
    gBase.assign(nCy, 0.);
    gTable.assign(nCy, 0.);
    gTail.assign(nCy, 0.);
    std::unique_ptr<jpsi::Sampler> sM;
    if (tailOk) {
      jpsi::Config gM = gT;
      gM.forwardTail = jpsi::ForwardTail::MapEnd;
      gM.tailN = gM.dataMap.tailN = tail.r.n;
      sM = std::make_unique<jpsi::Sampler>(gM);
    }
    for (size_t i = 0; i < allY.size(); ++i) {
      if (allBin[i] < 0 || !(jb[i] > 0)) continue;
      gBase[allBin[i]] += N * allW[i];
      gTable[allBin[i]] +=
          N * allW[i] * sT.JointDensity(allY[i], allPt[i]) / jb[i];
      if (sM)
        gTail[allBin[i]] +=
            N * allW[i] * sM->JointDensity(allY[i], allPt[i]) / jb[i];
    }
    printf(
        "\n  generator against the corrected data per y bin, per POT "
        "(generator x N = %.3f)\n"
        "    y          data                    NA50 base   map+table   "
        "map+tail    data/base   data/(map+table)   data/(map+tail)\n",
        N);
    for (int k = 0; k < nCy; ++k) {
      if (cy->GetXaxis()->GetBinLowEdge(k + 1) < yLo - 1e-6) continue;
      const double d = cy->GetBinContent(k + 1) / pot;
      const double e = cy->GetBinError(k + 1) / pot;
      auto rat = [&](double g) {
        return g > 0 ? std::string(Form("%5.3f +- %5.3f", d / g, e / g))
                     : std::string("      -       ");
      };
      printf(
          "    %.1f-%.1f    %9.3e +- %8.2e   %9.3e   %9.3e   %9.3e   %s   %s   "
          "%s\n",
          cy->GetXaxis()->GetBinLowEdge(k + 1),
          cy->GetXaxis()->GetBinUpEdge(k + 1), d, e, gBase[k], gTable[k],
          gTail[k], rat(gBase[k]).c_str(), rat(gTable[k]).c_str(),
          rat(gTail[k]).c_str());
    }
    if (tailOk)
      printf(
          "  the generator with this map file continues the map from y = %.1f "
          "with n = %.2f (forward_tail map)\n",
          yHi, tail.r.n);
  } catch (const std::exception& ex) {
    tailWhy = ex.what();
  }
  if (!tailOk)
    printf("\nforward tail NOT fitted (%s): the map file has no tail_n\n",
           tailWhy.c_str());

  // ------------------------------------------------------------ map file
  {
    std::ofstream o(outMap);
    o << "# J/psi generator data map (JpsiSampler v" << jpsi::kVersion
      << " DataMap), written by JpsiDataMap.C\n"
      << "# w(y, pT) = exp(D (b1 + b2 D) + c D (min(pT^2, ptsq_max) - "
         "ptsq_ref)), D = clamp(y - y_join, 0, y_hi - y_join)\n"
      << "# data: " << accFile << " (selection " << selMode << "), POT " << pot
      << "\n"
      << "# map base: " << genFile << "\n"
      << "# acceptance variation: " << (accVar && accVar[0] ? accVar : "none")
      << ", tolerance " << tolVar << "\n"
      << "# fit: "
      << (fixN ? "absolute (N = 1)" : "shape (N free, not applied)")
      << ", systematic per cell " << sysFrac << "\n";
    o.precision(8);
    o << "y_join " << yLo << "\ny_hi " << yHi << "\nptsq_ref " << q0
      << "\nptsq_max " << qMax << "\n";
    o << "b1 " << F.par[0] << "\nb2 " << F.par[1] << "\nc " << F.par[2] << "\n";
    o << "norm_data_over_gen " << std::exp(F.par[3]) << "\n";
    // uncertainties only from a fit with an invertible covariance
    if (F.ok) {
      o << "b1_err " << F.err[0] << "\nb2_err " << F.err[1] << "\nc_err "
        << F.err[2] << "\n";
      o << "cov_b1_b2 " << F.cov[0][1] << "\ncov_b1_c " << F.cov[0][2]
        << "\ncov_b2_c " << F.cov[1][2] << "\n";
      o << "norm_err " << std::exp(F.par[3]) * F.err[3] << "\n";
    } else {
      o << "# covariance not invertible: no uncertainties\n";
    }
    o << "chi2 " << F.chi2 << "\nndf " << F.ndf << "\nchi2_no_correction "
      << F0.chi2 << "\n";
    int nu = 0;
    for (int i = 0; i < nC; ++i) nu += use2[i];
    o << "n_cells_fitted " << nu << "\nn_cells " << nC << "\n";
    for (int i = 0; i < nC; ++i)
      if (!use2[i])
        o << "# not fitted (acceptance not validated): y " << ySl[i / nPt]
          << "-" << ySl[i / nPt + 1] << ", p_T " << ptS[i % nPt] << "-"
          << ptS[i % nPt + 1] << "\n";
    o << "chi2_check_pz_pt_base " << cb1.first << "\nchi2_check_pz_pt_map "
      << cf1.first << "\nndf_check_pz_pt " << cf1.second << "\n";
    o << "base_mean_pt_sq " << meanPtSq << "\nbase_pt_sq_slope " << ptSqSlope
      << "\nbase_lambda_pol " << lambda << "\n";
    if (tailOk) {
      o << "# forward tail: dN/dxF ~ (1 - |xF|)^n fitted to corr_y over "
        << tail.lo << "-" << tail.hi
        << ", N free; with tail_n the generator continues the map from y_hi\n";
      for (const TailOut& t : tails)
        o << "#   y_lo " << t.lo << ": n " << t.r.n << " -" << t.r.enLo << " +"
          << t.r.enHi << ", chi2 " << t.r.chi2 << " / " << t.r.ndf << "\n";
      o << "tail_n " << tail.r.n << "\ntail_n_err " << tail.r.en
        << "\ntail_fit_lo " << tail.lo << "\ntail_fit_hi " << tail.hi
        << "\ntail_chi2 " << tail.r.chi2 << "\ntail_ndf " << tail.r.ndf
        << "\ntail_ref_n " << tailN0 << "\ntail_chi2_ref " << tail.chi2Ref
        << "\n";
    } else {
      o << "# forward tail not fitted (" << tailWhy
        << "): the SHiP table continues the map\n";
    }
  }
  printf(
      "\nwrote %s: b1 = %.3f +- %.3f, b2 = %.3f +- %.3f, c = %.3f +- %.3f "
      "(chi2 %.1f / %d)\n",
      outMap, F.par[0], F.err[0], F.par[1], F.err[1], F.par[2], F.err[2],
      F.chi2, F.ndf);
  if (tailOk)
    printf("     tail_n = %.2f +- %.2f (fit %.1f-%.1f, chi2 %.1f / %d)\n",
           tail.r.n, tail.r.en, tail.lo, tail.hi, tail.r.chi2, tail.r.ndf);

  // ------------------------------------------------------------ plots
  const int cD = kBlack;
  const int cB = kBlue + 1;
  const int cM = kRed + 1;
  auto slicePlot = [&](const std::string& png, const std::vector<double>& ed,
                       const char* var, const char* unit,
                       const std::vector<double>& dd,
                       const std::vector<double>& ee,
                       const std::vector<double>& bb,
                       const std::vector<double>& ff) {
    TCanvas c(Form("c_%s", png.c_str()), "", 1000, 800);
    c.Divide(2, 2);
    for (int s = 0; s < 4 && s + 1 < (int)ed.size(); ++s) {
      c.cd(s + 1);
      gPad->SetLogy();
      TH1D* h[3];
      const std::vector<double>* src[3] = {&dd, &bb, &ff};
      double lo = 1e300;
      double hi = 0;
      for (int k = 0; k < 3; ++k) {
        h[k] =
            new TH1D(Form("%s_%d_%d", png.c_str(), s, k),
                     Form("%s %.2f-%.2f%s;p_{T} [GeV];J/#psi per POT per GeV",
                          var, ed[s], ed[s + 1], unit),
                     nPt, ptS.data());
        h[k]->SetDirectory(nullptr);
        for (int j = 0; j < nPt; ++j) {
          const double wd = ptS[j + 1] - ptS[j];
          const double v = (*src[k])[s * nPt + j] / wd;
          h[k]->SetBinContent(j + 1, v);
          h[k]->SetBinError(j + 1, k == 0 ? ee[s * nPt + j] / wd : 0.);
          if (v > 0) {
            lo = std::min(lo, v);
            hi = std::max(hi, v + h[k]->GetBinError(j + 1));
          }
        }
      }
      h[1]->SetMaximum(hi * 5);
      h[1]->SetMinimum(lo * 0.3);
      h[1]->SetLineColor(cB);
      h[1]->SetLineStyle(2);
      h[1]->SetLineWidth(2);
      h[1]->Draw("hist");
      h[2]->SetLineColor(cM);
      h[2]->SetLineWidth(2);
      h[2]->Draw("hist same");
      h[0]->SetMarkerStyle(20);
      h[0]->SetMarkerColor(cD);
      h[0]->SetLineColor(cD);
      h[0]->Draw("E1 same");
      TLegend* lg = new TLegend(0.45, 0.7, 0.89, 0.89);
      lg->SetBorderSize(0);
      lg->SetFillStyle(0);
      lg->AddEntry(h[0], "2018 data, corrected", "pe");
      lg->AddEntry(h[1], "generator, NA50 base (no correction)", "l");
      lg->AddEntry(h[2], "generator, data map", "l");
      lg->Draw();
    }
    c.SaveAs((dir + "/" + png + ".png").c_str());
  };
  slicePlot("1_pt_in_y_slices", ySl, "y", "", d2, e2, base, fit);
  slicePlot("2_pt_in_pz_slices", pzS, "p_{z}", " GeV", d1, e1, b1v, f1v);
  if (!yD.empty()) {
    TCanvas c("c_y", "", 800, 600);
    const int n = yD.size();
    std::vector<double> edg;
    for (int j = 0; j < n; ++j)
      edg.push_back(cy->GetXaxis()->GetBinLowEdge(ybIdx[j]));
    edg.push_back(cy->GetXaxis()->GetBinUpEdge(ybIdx[n - 1]));
    TH1D* hd =
        new TH1D("y_d", ";y_{cm};data / generator (per POT)", n, edg.data());
    TH1D* hb = new TH1D("y_b", "", n, edg.data());
    for (int j = 0; j < n; ++j) {
      hd->SetBinContent(j + 1, yF[j] > 0 ? yD[j] / yF[j] : 0.);
      hd->SetBinError(j + 1, yF[j] > 0 ? yE[j] / yF[j] : 0.);
      hb->SetBinContent(j + 1, yB[j] > 0 ? yD[j] / yB[j] : 0.);
      hb->SetBinError(j + 1, yB[j] > 0 ? yE[j] / yB[j] : 0.);
    }
    double hi = 0;
    for (TH1D* h : {hd, hb})
      for (int j = 1; j <= n; ++j)
        hi = std::max(hi, h->GetBinContent(j) + h->GetBinError(j));
    hd->SetMinimum(0.);
    hd->SetMaximum(1.4 * std::max(hi, 1.2));
    hd->SetMarkerStyle(20);
    hd->SetMarkerColor(cM);
    hd->SetLineColor(cM);
    hd->Draw("E1");
    hb->SetMarkerStyle(24);
    hb->SetMarkerColor(cB);
    hb->SetLineColor(cB);
    hb->Draw("E1 same");
    TLine one(edg.front(), 1., edg.back(), 1.);
    one.SetLineStyle(2);
    one.Draw();
    TLegend* lg = new TLegend(0.45, 0.75, 0.89, 0.89);
    lg->SetBorderSize(0);
    lg->SetFillStyle(0);
    lg->AddEntry(hd, "data / generator with data map", "pe");
    lg->AddEntry(hb, "data / generator, NA50 base", "pe");
    lg->Draw();
    c.SaveAs((dir + "/3_y_ratio.png").c_str());
  }
  if (!gTable.empty()) {
    // corrected y distribution per unit y against the generator variants, and
    // the tail fit in its range
    std::vector<int> ks;
    for (int k = 0; k < cy->GetNbinsX(); ++k)
      if (cy->GetXaxis()->GetBinLowEdge(k + 1) > yLo - 1e-6 &&
          cy->GetBinContent(k + 1) > 0)
        ks.push_back(k);
    if (!ks.empty()) {
      std::vector<double> edg;
      for (int k : ks) edg.push_back(cy->GetXaxis()->GetBinLowEdge(k + 1));
      edg.push_back(cy->GetXaxis()->GetBinUpEdge(ks.back() + 1));
      const int n = ks.size();
      auto mk = [&](const char* nm, int col, int sty) {
        TH1D* h = new TH1D(nm, ";y_{cm};fiducial J/#psi per POT per unit y", n,
                           edg.data());
        h->SetDirectory(nullptr);
        h->SetLineColor(col);
        h->SetMarkerColor(col);
        h->SetLineStyle(sty);
        h->SetLineWidth(2);
        return h;
      };
      TH1D* hd = mk("t_data", cD, 1);
      TH1D* hb = mk("t_base", cB, 2);
      TH1D* ht = mk("t_table", kGreen + 2, 1);
      TH1D* hm = mk("t_tail", cM, 1);
      TH1D* hf = mk("t_fit", kMagenta + 1, 3);
      TH1D* hr = mk("t_ref", kGray + 2, 3);
      for (int j = 0; j < n; ++j) {
        const int k = ks[j];
        const double wd = cy->GetXaxis()->GetBinWidth(k + 1);
        hd->SetBinContent(j + 1, cy->GetBinContent(k + 1) / pot / wd);
        hd->SetBinError(j + 1, cy->GetBinError(k + 1) / pot / wd);
        hb->SetBinContent(j + 1, gBase[k] / wd);
        ht->SetBinContent(j + 1, gTable[k] / wd);
        hm->SetBinContent(j + 1, gTail[k] / wd);
      }
      if (tailOk)
        for (size_t j = 0; j < tail.bins.size(); ++j) {
          const int k = tail.bins[j];
          const auto it = std::find(ks.begin(), ks.end(), k);
          if (it == ks.end()) continue;
          const double wd = cy->GetXaxis()->GetBinWidth(k + 1);
          double S;
          double V;
          jdm::TailSums(tail.tb[j], tail.r.n, tailN0, S, V);
          hf->SetBinContent(it - ks.begin() + 1, tail.r.N * S / wd);
          jdm::TailSums(tail.tb[j], tailN0, tailN0, S, V);
          hr->SetBinContent(it - ks.begin() + 1, tail.nRef * S / wd);
        }
      double lo = 1e300;
      double hi = 0;
      for (TH1D* h : {hd, hb, ht, hm})
        for (int j = 1; j <= n; ++j)
          if (h->GetBinContent(j) > 0) {
            lo = std::min(lo, h->GetBinContent(j));
            hi = std::max(hi, h->GetBinContent(j));
          }
      TCanvas c("c_tail", "", 800, 600);
      gPad->SetLogy();
      hb->SetMinimum(0.3 * lo);
      hb->SetMaximum(3 * hi);
      hb->Draw("hist");
      ht->Draw("hist same");
      if (tailOk) {
        hm->Draw("hist same");
        hf->Draw("hist same");
        hr->Draw("hist same");
      }
      hd->SetMarkerStyle(20);
      hd->Draw("E1 same");
      TLegend* lg = new TLegend(0.12, 0.12, 0.6, 0.38);
      lg->SetBorderSize(0);
      lg->SetFillStyle(0);
      lg->AddEntry(hd, "2018 data, corrected (fiducial)", "pe");
      lg->AddEntry(hb, "generator, NA50 base", "l");
      lg->AddEntry(ht, Form("map, then SHiP table from y = %.1f", yHi), "l");
      if (tailOk) {
        lg->AddEntry(
            hm,
            Form("map, then (1-|x_{F}|)^{%.2f} from y = %.1f", tail.r.n, yHi),
            "l");
        lg->AddEntry(hf,
                     Form("tail fit %.1f-%.1f: n = %.2f #pm %.2f", tail.lo,
                          tail.hi, tail.r.n, tail.r.en),
                     "l");
        lg->AddEntry(hr, Form("same range, n = %.1f", tailN0), "l");
      }
      lg->Draw();
      c.SaveAs((dir + "/4_forward_tail.png").c_str());
    }
  }
  {
    TFile out((dir + "/datamap.root").c_str(), "RECREATE");
    TParameter<double>("b1", F.par[0]).Write();
    TParameter<double>("b2", F.par[1]).Write();
    TParameter<double>("c", F.par[2]).Write();
    if (tailOk) {
      TParameter<double>("tail_n", tail.r.n).Write();
      TParameter<double>("tail_n_err", tail.r.en).Write();
    }
    TParameter<double>("chi2", F.chi2).Write();
    TParameter<double>("ndf", F.ndf).Write();
    TNamed("acceptance_file", accFile).Write();
    TNamed("generator_file", genFile).Write();
    out.Close();
  }
  printf("plots in %s/\n", outdir);
}
