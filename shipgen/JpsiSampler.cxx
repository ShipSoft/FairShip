// SPDX-License-Identifier: LGPL-3.0-or-later

#include "JpsiSampler.h"

#include <algorithm>
#include <cstdlib>
#include <cmath>
#include <sstream>
#include <stdexcept>

namespace jpsi {

namespace {

/// SHiP CERN-SHiP-ANA-2019-002 Table 2: y_low, B*sigma/A [pb/nucleon].
struct ShipBin {
  double yLow, value_pb;
};
constexpr ShipBin kShipTable[] = {
    {0.2, 660.34}, {0.3, 473.61}, {0.4, 375.56}, {0.5, 329.45}, {0.6, 291.41},
    {0.7, 240.60}, {0.8, 205.21}, {0.9, 166.79}, {1.0, 135.93}, {1.1, 104.79},
    {1.2, 75.83},  {1.3, 53.78},  {1.4, 30.94},  {1.5, 22.45},  {1.6, 12.84},
    {1.7, 6.25},   {1.8, 0.94},   {1.9, 0.02}};
constexpr double kShipBinWidth = 0.1;

constexpr double kYWindowLo = -0.425;  // NA50 acceptance window
constexpr double kYWindowHi = 0.575;

/// Asymptotic K1: argument is mT/T >= M/T ~ 10.8, accuracy better than 1e-5.
double BesselK1(double x) {
  return std::exp(-x) * std::sqrt(M_PI / (2 * x)) *
         (1 + 3 / (8 * x) - 15 / (128 * x * x) + 315 / (3072 * x * x * x));
}

double GaussPdf(double y, double mu, double sigma) {
  const double t = (y - mu) / sigma;
  return std::exp(-0.5 * t * t) / (sigma * std::sqrt(2 * M_PI));
}

void MakeCdf(const std::vector<double>& x, const std::vector<double>& pdf,
             std::vector<double>& cdf) {
  cdf.assign(x.size(), 0.);
  for (std::size_t i = 1; i < x.size(); ++i) {
    cdf[i] = cdf[i - 1] + 0.5 * (pdf[i] + pdf[i - 1]) * (x[i] - x[i - 1]);
  }
  if (cdf.back() <= 0.) throw std::runtime_error("JpsiSampler: empty density");
  for (auto& c : cdf) c /= cdf.back();
}

double InvertCdf(const std::vector<double>& x, const std::vector<double>& cdf,
                 double u) {
  const auto it = std::lower_bound(cdf.begin(), cdf.end(), u);
  if (it == cdf.begin()) return x.front();
  if (it == cdf.end()) return x.back();
  const std::size_t i = std::distance(cdf.begin(), it);
  const double den = cdf[i] - cdf[i - 1];
  const double f = den > 0 ? (u - cdf[i - 1]) / den : 0.;
  return x[i - 1] + f * (x[i] - x[i - 1]);
}

double Interpolate(const std::vector<double>& x, const std::vector<double>& y,
                   double xv) {
  if (xv <= x.front()) return y.front();
  if (xv >= x.back()) return y.back();
  const auto it = std::lower_bound(x.begin(), x.end(), xv);
  const std::size_t i = std::distance(x.begin(), it);
  const double f = (xv - x[i - 1]) / (x[i] - x[i - 1]);
  return y[i - 1] + f * (y[i] - y[i - 1]);
}

double Trapezoid(const std::vector<double>& x, const std::vector<double>& f) {
  double sum = 0.;
  for (std::size_t i = 1; i < x.size(); ++i) {
    sum += 0.5 * (f[i] + f[i - 1]) * (x[i] - x[i - 1]);
  }
  return sum;
}

}  // namespace

// ---------------------------------------------------------------- targets

TargetSpec TungstenNA50() { return TargetSpec{}; }

TargetSpec TargetFromA(double A, double density_gcm3, const std::string& name) {
  // Anchored on NA50 tungsten:
  //   B*sigma/A  ~ A^(alpha-1),   sigma_inel ~ A^0.71
  const TargetSpec w = TungstenNA50();
  TargetSpec t;
  t.A = A;
  t.alphaA = w.alphaA;
  t.density_gcm3 = density_gcm3;
  t.name = name;
  t.bSigmaWindow_nb = w.bSigmaWindow_nb * std::pow(A / w.A, w.alphaA - 1.0);
  const double sigmaW_cm2 = w.A / (kAvogadro * w.lambdaInt_gcm2);
  const double sigma_cm2 = sigmaW_cm2 * std::pow(A / w.A, 0.71);
  t.lambdaInt_gcm2 = A / (kAvogadro * sigma_cm2);
  return t;
}

TargetSpec MolybdenumScaled() { return TargetFromA(95.95, 10.22, "Mo"); }

// ---------------------------------------------------------------- helpers

double Vec4::P() const { return std::sqrt(px * px + py * py + pz * pz); }
double Vec4::Pt() const { return std::sqrt(px * px + py * py); }
double Vec4::Rapidity() const { return 0.5 * std::log((E + pz) / (E - pz)); }

double CosAcceptance(double lambda, double cut) {
  const double num = cut + lambda * cut * cut * cut / 3.0;
  const double den = 1.0 + lambda / 3.0;
  return num / den;
}

// ---------------------------------------------------------------- Sampler

Sampler::Sampler(const Config& cfg) : fCfg(cfg), fRng(cfg.seed) {
  Validate();
  const double eBeam = std::hypot(fCfg.pBeam, kMProton);
  fSqrtS = std::sqrt(2 * kMProton * eBeam + 2 * kMProton * kMProton);
  fYShift = std::atanh(fCfg.pBeam / (eBeam + kMProton));

  BuildPtGrid();
  BuildYGrid();
  BuildTargetModel();
  Normalise();
}

void Sampler::Validate() const {
  auto fail = [](const std::string& m) {
    throw std::runtime_error("JpsiSampler: " + m);
  };
  if (fCfg.pBeam <= kMProton) fail("beam momentum must be positive");
  if (fCfg.T <= 0) fail("thermal slope T must be positive");
  if (fCfg.p0 <= 0) fail("power-law scale p0 must be positive");
  if (fCfg.nPow <= 1) fail("power-law exponent must exceed 1");
  if (fCfg.ptMax <= 0) fail("ptMax must be positive");
  if (fCfg.ptSq <= 0 && (fCfg.fHard < 0 || fCfg.fHard > 1)) {
    fail("fHard must lie in [0,1]");
  }
  if (fCfg.yGaussSigma <= 0) fail("Gaussian width must be positive");
  if (fCfg.tailN <= 0) fail("forward tail exponent must be positive");
  if (fCfg.dataHi <= fCfg.dataLo) fail("empty data range");
  if (fCfg.lambdaPol < -1) fail("lambda < -1 makes the decay density negative");
  if (fCfg.injection) {
    if (fCfg.potPerEvent <= 0) fail("potPerEvent must be positive");
    if (fCfg.enhancement <= 0 && fCfg.meanPerEvent <= 0) {
      fail("injection needs an enhancement or a mean number per event");
    }
  } else {
    if (fCfg.nPot <= 0) fail("nPot must be positive");
    if (fCfg.enhancement <= 0 && fCfg.nEvents <= 0) fail("nEvents must be > 0");
  }
  for (const auto& l : fCfg.layers) {
    if (l.length_cm <= 0) fail("layer length must be positive");
    if (l.material.A <= 0 || l.material.density_gcm3 <= 0) {
      fail("layer material is not physical");
    }
  }
}

void Sampler::BuildPtGrid() {
  constexpr int kN = 20001;
  fPtGrid.resize(kN);
  fPtThermal.resize(kN);
  fPtHard.resize(kN);
  for (int i = 0; i < kN; ++i) {
    const double pt = fCfg.ptMax * i / (kN - 1);
    fPtGrid[i] = pt;
    const double mt = std::hypot(kMJpsi, pt);
    const double jac = fCfg.thermalJacobian ? pt : 1.0;
    fPtThermal[i] = jac * mt * BesselK1(mt / fCfg.T);
    fPtHard[i] = pt * std::pow(1 + (pt / fCfg.p0) * (pt / fCfg.p0), -fCfg.nPow);
  }
  auto normalise = [this](std::vector<double>& f) {
    const double integral = Trapezoid(fPtGrid, f);
    for (auto& v : f) v /= integral;
  };
  normalise(fPtThermal);
  normalise(fPtHard);

  const double fHard = fCfg.ptSq > 0 ? SolveFHard(fCfg.ptSq) : fCfg.fHard;
  fNorm.fHard = fHard;
  fPtPdf.resize(kN);
  for (int i = 0; i < kN; ++i) {
    fPtPdf[i] = (1 - fHard) * fPtThermal[i] + fHard * fPtHard[i];
  }
  MakeCdf(fPtGrid, fPtPdf, fPtCdf);
  fNorm.meanPt = PtMoment(fPtPdf, 1);
  fNorm.meanPtSq = PtMoment(fPtPdf, 2);
}

double Sampler::PtMoment(const std::vector<double>& pdf, int k) const {
  std::vector<double> f(pdf.size());
  for (std::size_t i = 0; i < pdf.size(); ++i) {
    f[i] = std::pow(fPtGrid[i], k) * pdf[i];
  }
  return Trapezoid(fPtGrid, f);
}

double Sampler::SolveFHard(double ptSq) const {
  const double a = PtMoment(fPtThermal, 2);
  const double b = PtMoment(fPtHard, 2);
  const double f = (ptSq - a) / (b - a);
  if (f < 0 || f > 1) {
    std::ostringstream os;
    os << "JpsiSampler: <pT^2> = " << ptSq << " not reachable, range ["
       << std::min(a, b) << ", " << std::max(a, b) << "]";
    throw std::runtime_error(os.str());
  }
  return f;
}

double Sampler::PtCdfAt(double pt) const {
  return Interpolate(fPtGrid, fPtCdf, pt);
}

double Sampler::PtMaxAt(double y) const {
  // |x_F| < 1  <=>  2 mT sinh|y| < sqrt(s)
  const double sh = std::abs(std::sinh(y));
  if (sh < 1e-12) return fCfg.ptMax;
  const double mtMax = fSqrtS / (2 * sh);
  if (mtMax <= kMJpsi) return 0.;
  return std::min(fCfg.ptMax, std::sqrt(mtMax * mtMax - kMJpsi * kMJpsi));
}

double Sampler::TailDensity(double y) const {
  // dsigma/dy for dsigma/dxF ~ (1-|xF|)^n, integrated over the pT spectrum
  // rather than evaluated at a reference transverse mass.
  constexpr int kNpt = 400;
  double sum = 0.;
  const double ptMax = PtMaxAt(y);
  if (ptMax <= 0) return 0.;
  for (int i = 0; i <= kNpt; ++i) {
    const double pt = ptMax * i / kNpt;
    const double w = (i == 0 || i == kNpt) ? 0.5 : 1.0;
    const double mt = std::hypot(kMJpsi, pt);
    const double xf = 2 * mt * std::sinh(y) / fSqrtS;
    const double base = std::max(0.0, 1.0 - std::abs(xf));
    const double jac = 2 * mt * std::cosh(y) / fSqrtS;
    sum += w * Interpolate(fPtGrid, fPtPdf, pt) * std::pow(base, fCfg.tailN) *
           jac * (ptMax / kNpt);
  }
  return sum;
}

void Sampler::BuildYGrid() {
  // Grid limit: the largest rapidity still allowed for pT -> 0.
  const double yKin = std::asinh(fSqrtS / (2 * kMJpsi));
  constexpr int kN = 20001;
  fYGrid.resize(kN);
  fYPdf.assign(kN, 0.);
  fYValid.assign(kN, 0.);
  for (int i = 0; i < kN; ++i) fYGrid[i] = -yKin + 2 * yKin * i / (kN - 1);

  auto gauss = [this](double y) {
    return GaussPdf(y, fCfg.yGauss0, fCfg.yGaussSigma);
  };

  if (fCfg.yShape == YShape::Gauss) {
    for (int i = 0; i < kN; ++i) fYPdf[i] = gauss(fYGrid[i]);
  } else if (fCfg.yShape == YShape::Hybrid) {
    // joined exactly at yMatch
    const double tailAtMatch = TailDensity(fCfg.yMatch);
    const double scale = tailAtMatch > 0 ? gauss(fCfg.yMatch) / tailAtMatch : 0.;
    for (int i = 0; i < kN; ++i) {
      const double y = fYGrid[i];
      fYPdf[i] = (y <= fCfg.yMatch) ? gauss(y) : scale * TailDensity(y);
    }
  } else {  // Data
    double firstVal = -1., lastVal = -1.;
    for (const auto& b : kShipTable) {
      if (b.yLow >= fCfg.dataLo - 1e-9 && b.yLow < fCfg.dataHi - 1e-9) {
        if (firstVal < 0) firstVal = b.value_pb / kShipBinWidth;
        lastVal = b.value_pb / kShipBinWidth;
      }
    }
    if (firstVal <= 0) throw std::runtime_error("JpsiSampler: empty data range");
    // Continuations are matched at the boundaries themselves, not at bin
    // centres, so the density is continuous at dataLo and dataHi.
    const double gScale = firstVal / gauss(fCfg.dataLo);
    const double tailAtHi = TailDensity(fCfg.dataHi);
    const double tScale = tailAtHi > 0 ? lastVal / tailAtHi : 0.;
    for (int i = 0; i < kN; ++i) {
      const double y = fYGrid[i];
      if (y < fCfg.dataLo) {
        fYPdf[i] = gScale * gauss(y);
      } else if (y >= fCfg.dataHi) {
        fYPdf[i] = tScale * TailDensity(y);
      } else {
        for (const auto& b : kShipTable) {
          if (y >= b.yLow && y < b.yLow + kShipBinWidth) {
            fYPdf[i] = b.value_pb / kShipBinWidth;
            break;
          }
        }
      }
    }
  }

  // Fold in the exact kinematic limit: at each y only pT < ptMax(y) is allowed.
  // The same factor is used for generation and for f_y, so the normalised
  // density and the generated sample are identical by construction.
  for (int i = 0; i < kN; ++i) {
    fYValid[i] = PtCdfAt(PtMaxAt(fYGrid[i]));
    fYPdf[i] *= fYValid[i];
  }
  MakeCdf(fYGrid, fYPdf, fYCdf);
}

void Sampler::BuildTargetModel() {
  if (fCfg.layers.empty()) return;
  constexpr int kNz = 8001;
  double total = 0.;
  for (const auto& l : fCfg.layers) total += l.length_cm;

  fZGrid.resize(kNz);
  std::vector<double> dens(kNz, 0.);   // vertex density (arbitrary scale)
  std::vector<double> rate(kNz, 0.);   // d(P_mumu/POT)/dz, absolute
  const TargetSpec w = TungstenNA50();
  // B*sigma_Jpsi(A) = c A^alpha with c fixed by the NA50 tungsten point.
  const double cJpsi_nb =
      w.bSigmaWindow_nb / std::pow(w.A, w.alphaA - 1.0);  // nb, per nucleus /A^a

  double tau = 0.;  // interaction lengths traversed
  const double dz = total / (kNz - 1);
  for (int i = 0; i < kNz; ++i) {
    const double z = dz * i;
    fZGrid[i] = fCfg.zStart_cm + z;
    double acc = 0.;
    const Layer* here = &fCfg.layers.back();
    for (const auto& l : fCfg.layers) {
      if (z <= acc + l.length_cm) {
        here = &l;
        break;
      }
      acc += l.length_cm;
    }
    const double invLambda_cm =
        here->material.density_gcm3 / here->material.lambdaInt_gcm2;
    if (i > 0) tau += invLambda_cm * dz;
    const double nA_cm3 =
        here->material.density_gcm3 * kAvogadro / here->material.A;
    // B*sigma(J/psi) for this nucleus, full phase space, in cm^2
    const double bSigma_cm2 =
        cJpsi_nb * std::pow(here->material.A, w.alphaA) * 1e-33;
    dens[i] = std::exp(-tau) * nA_cm3 * bSigma_cm2;
    rate[i] = dens[i];
  }
  MakeCdf(fZGrid, dens, fZCdf);
  // The acceptance division is applied in Normalise(), where f_y and f_cos are
  // known; here we only integrate the window-restricted rate.
  fNorm.probMuMuPerPot = Trapezoid(fZGrid, rate);
}

void Sampler::Normalise() {
  // Deterministic f_y: the rapidity density already contains the kinematic
  // validity factor, so integrating it over the NA50 window is exact.
  const double inWindow =
      Interpolate(fYGrid, fYCdf, kYWindowHi) - Interpolate(fYGrid, fYCdf, kYWindowLo);
  fNorm.fY = inWindow;
  fNorm.fCos = CosAcceptance(fCfg.lambdaPol, 0.5);

  const double acceptance = fNorm.fY * fNorm.fCos;
  fNorm.bSigmaFull_nb = fCfg.target.bSigmaWindow_nb / acceptance;
  const double sigmaInel_cm2 =
      fCfg.target.A / (kAvogadro * fCfg.target.lambdaInt_gcm2);
  fNorm.sigmaInel_mb = sigmaInel_cm2 * 1e27;
  fNorm.chiMuMu = fCfg.target.A * fNorm.bSigmaFull_nb * 1e-6 / fNorm.sigmaInel_mb;
  fNorm.chiJpsi = fNorm.chiMuMu / kBrMuMu;
  fNorm.chiMuMuFullCosDiagnostic = fNorm.chiMuMu * fNorm.fCos;  // f_cos -> 1

  if (fCfg.probMuMuPerPotOverride > 0) {
    fNorm.probMuMuPerPot = fCfg.probMuMuPerPotOverride;
  } else if (fNorm.probMuMuPerPot > 0) {
    fNorm.probMuMuPerPot /= acceptance;  // window -> full phase space
  }

  RecomputeRate();
}

void Sampler::RecomputeRate() {
  // Rate the weight is built from:
  //   per POT when the target was modelled (slab stack or geometry scan),
  //   otherwise per interacting proton.
  //   Output::Jpsi is an inclusive sample, so it divides by the branching ratio.
  const bool inclusive = (fCfg.output == Output::Jpsi);
  const double rateMuMu =
      fNorm.probMuMuPerPot > 0 ? fNorm.probMuMuPerPot : fNorm.chiMuMu;
  fNorm.rate = inclusive ? rateMuMu / kBrMuMu : rateMuMu;

  if (fCfg.injection) {
    // Expected real J/psi per host event: rate * potPerEvent. Generating mu of
    // them per event keeps the expectation with weight rate*potPerEvent/mu.
    const double physical = fNorm.rate * fCfg.potPerEvent;
    fNorm.meanPerEvent =
        fCfg.meanPerEvent > 0 ? fCfg.meanPerEvent : fCfg.enhancement * physical;
    fNorm.weight = physical / fNorm.meanPerEvent;
    fNorm.enhancement = 1.0 / fNorm.weight;
    fNEvents = -1;  // set by the host run
    return;
  }

  fNEvents = fCfg.nEvents;
  if (fCfg.enhancement > 0) {
    fNEvents = std::max<long>(
        1, std::lround(fCfg.enhancement * fCfg.nPot * fNorm.rate));
  }
  fNorm.weight = fCfg.nPot * fNorm.rate / static_cast<double>(fNEvents);
  fNorm.enhancement = fNorm.weight > 0 ? 1.0 / fNorm.weight : 0.;
}

void Sampler::SetProbMuMuPerPot(double p) {
  if (p <= 0) throw std::runtime_error("JpsiSampler: rate per POT must be > 0");
  fNorm.probMuMuPerPot = p;
  RecomputeRate();
}

double Sampler::BSigmaFullForA(double A) const {
  // B*sigma(J/psi) for one nucleus, full phase space, cm^2.
  const TargetSpec w = TungstenNA50();
  const double c_nb = w.bSigmaWindow_nb / std::pow(w.A, w.alphaA - 1.0);
  const double window_cm2 = c_nb * std::pow(A, w.alphaA) * 1e-33;
  return window_cm2 / (fNorm.fY * fNorm.fCos);
}

int Sampler::NumberToInject() {
  const double mu = fNorm.meanPerEvent;
  const int base = static_cast<int>(std::floor(mu));
  return base + (fFlat(fRng) < mu - base ? 1 : 0);
}

double Sampler::YDensity(double y) const {
  return Interpolate(fYGrid, fYPdf, y);
}

double Sampler::SamplePt() { return InvertCdf(fPtGrid, fPtCdf, fFlat(fRng)); }
double Sampler::SampleY() { return InvertCdf(fYGrid, fYCdf, fFlat(fRng)); }

void Sampler::DrawKinematics(double& y, double& pt) {
  // y is drawn from the density that already includes P(pT < ptMax(y)); pT is
  // then drawn from the pT spectrum truncated at that same limit. No rejection,
  // so the generated joint density matches the one used for the normalisation.
  y = SampleY();
  const double ptMax = PtMaxAt(y);
  const double uMax = PtCdfAt(ptMax);
  pt = InvertCdf(fPtGrid, fPtCdf, fFlat(fRng) * uMax);
}

double Sampler::SampleCosTheta() {
  const double lambda = fCfg.lambdaPol;
  if (std::abs(lambda) < 1e-12) return 2 * fFlat(fRng) - 1;
  const double maxVal = 1.0 + std::max(0.0, lambda);
  for (int i = 0; i < 1000; ++i) {
    const double c = 2 * fFlat(fRng) - 1;
    if (fFlat(fRng) * maxVal <= 1.0 + lambda * c * c) return c;
  }
  return 2 * fFlat(fRng) - 1;
}

namespace {

Vec4 Boost(const Vec4& v, double bx, double by, double bz) {
  const double b2 = bx * bx + by * by + bz * bz;
  if (b2 <= 0) return v;
  const double gamma = 1.0 / std::sqrt(1 - b2);
  const double bp = bx * v.px + by * v.py + bz * v.pz;
  const double g2 = (gamma - 1.0) / b2;
  Vec4 out;
  out.px = v.px + g2 * bp * bx + gamma * bx * v.E;
  out.py = v.py + g2 * bp * by + gamma * by * v.E;
  out.pz = v.pz + g2 * bp * bz + gamma * bz * v.E;
  out.E = gamma * (v.E + bp);
  return out;
}

void Normalise3(double v[3]) {
  const double n = std::sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2]);
  for (int i = 0; i < 3; ++i) v[i] /= n;
}

}  // namespace

void Sampler::Decay(const Vec4& jpsi, double cosTheta, Vec4& mup, Vec4& mum) {
  // Collins-Soper axes: in the J/psi rest frame, z bisects the beam direction
  // and the reverse of the target direction.
  const double bx = -jpsi.px / jpsi.E, by = -jpsi.py / jpsi.E,
               bz = -jpsi.pz / jpsi.E;
  const double eBeam = std::hypot(fCfg.pBeam, kMProton);
  Vec4 beam = Boost(Vec4{0., 0., fCfg.pBeam, eBeam}, bx, by, bz);
  Vec4 targ = Boost(Vec4{0., 0., 0., kMProton}, bx, by, bz);

  double p1[3] = {beam.px, beam.py, beam.pz};
  double p2[3] = {targ.px, targ.py, targ.pz};
  Normalise3(p1);
  Normalise3(p2);
  double zAxis[3] = {p1[0] - p2[0], p1[1] - p2[1], p1[2] - p2[2]};
  Normalise3(zAxis);
  double yAxis[3] = {p1[1] * p2[2] - p1[2] * p2[1], p1[2] * p2[0] - p1[0] * p2[2],
                     p1[0] * p2[1] - p1[1] * p2[0]};
  const double yNorm =
      std::sqrt(yAxis[0] * yAxis[0] + yAxis[1] * yAxis[1] + yAxis[2] * yAxis[2]);
  if (yNorm < 1e-9) {
    yAxis[0] = 0;
    yAxis[1] = 1;
    yAxis[2] = 0;
  } else {
    for (auto& v : yAxis) v /= yNorm;
  }
  double xAxis[3] = {yAxis[1] * zAxis[2] - yAxis[2] * zAxis[1],
                     yAxis[2] * zAxis[0] - yAxis[0] * zAxis[2],
                     yAxis[0] * zAxis[1] - yAxis[1] * zAxis[0]};
  Normalise3(xAxis);

  const double pStar = std::sqrt(0.25 * kMJpsi * kMJpsi - kMMu * kMMu);
  const double sinTheta = std::sqrt(std::max(0.0, 1 - cosTheta * cosTheta));
  const double phi = 2 * M_PI * fFlat(fRng);
  double dir[3];
  for (int i = 0; i < 3; ++i) {
    dir[i] = pStar * (sinTheta * std::cos(phi) * xAxis[i] +
                      sinTheta * std::sin(phi) * yAxis[i] + cosTheta * zAxis[i]);
  }
  const double eMu = 0.5 * kMJpsi;
  const double bxl = jpsi.px / jpsi.E, byl = jpsi.py / jpsi.E,
               bzl = jpsi.pz / jpsi.E;
  mup = Boost(Vec4{dir[0], dir[1], dir[2], eMu}, bxl, byl, bzl);
  mum = Boost(Vec4{-dir[0], -dir[1], -dir[2], eMu}, bxl, byl, bzl);
}

double Sampler::SampleVertex() {
  if (fZCdf.empty()) return fCfg.zStart_cm;
  return InvertCdf(fZGrid, fZCdf, fFlat(fRng));
}

Event Sampler::Next() {
  Event ev;
  double y = 0., pt = 0.;
  DrawKinematics(y, pt);

  const double phi = 2 * M_PI * fFlat(fRng);
  const double mt = std::hypot(kMJpsi, pt);
  const double yLab = y + fYShift;
  ev.jpsi.px = pt * std::cos(phi);
  ev.jpsi.py = pt * std::sin(phi);
  ev.jpsi.pz = mt * std::sinh(yLab);
  ev.jpsi.E = mt * std::cosh(yLab);
  ev.yCM = y;
  ev.xF = 2 * mt * std::sinh(y) / fSqrtS;
  ev.z_cm = SampleVertex();
  ev.weight = fNorm.weight;

  if (fCfg.output != Output::Jpsi) {
    ev.cosThetaCS = SampleCosTheta();
    Decay(ev.jpsi, ev.cosThetaCS, ev.mup, ev.mum);
    ev.hasDimuon = true;
  }
  return ev;
}

std::string Sampler::Summary() const {
  std::ostringstream os;
  os.setf(std::ios::fixed);
  os.precision(4);
  os << "JpsiSampler v" << kVersion << " [" << fCfg.target.name
     << "] p_beam = " << fCfg.pBeam << " GeV/c, sqrt(s) = " << fSqrtS
     << " GeV, y_lab = y_cm + " << fYShift << "\n  pT: T = " << fCfg.T
     << " GeV, fHard = " << fNorm.fHard << ", <pT> = " << fNorm.meanPt
     << ", <pT^2> = " << fNorm.meanPtSq << " GeV^2\n  y : shape = "
     << (fCfg.yShape == YShape::Gauss
             ? "Gauss"
             : (fCfg.yShape == YShape::Hybrid ? "Hybrid" : "Data"))
     << ", tail n = " << fCfg.tailN << "\n  lambda = " << fCfg.lambdaPol
     << ", f_cos = " << fNorm.fCos << ", f_y = " << fNorm.fY
     << "\n  B*sigma/A = " << fNorm.bSigmaFull_nb
     << " nb/nucleon (full phase space), sigma_inel = " << fNorm.sigmaInel_mb
     << " mb";
  os.unsetf(std::ios::fixed);
  os.precision(6);
  os << "\n  chi_mumu = " << fNorm.chiMuMu << " / interacting proton, chi_Jpsi = "
     << fNorm.chiJpsi;
  if (fNorm.probMuMuPerPot > 0) {
    os << "\n  P(J/psi->mumu) per POT = " << fNorm.probMuMuPerPot
       << " (integrated over the target model)";
  }
  if (fCfg.injection) {
    os << "\n  injection: " << fNorm.meanPerEvent << " J/psi per host event ("
       << fCfg.potPerEvent << " POT each)";
  }
  os << "\n  output = "
     << (fCfg.output == Output::Jpsi
             ? "Jpsi (inclusive normalisation)"
             : (fCfg.output == Output::Both ? "Both" : "MuMu"))
     << ", rate used = " << fNorm.rate << "\n  nPot = " << fCfg.nPot
     << ", nEvents = " << fNEvents << ", weight = " << fNorm.weight
     << " (enhancement " << fNorm.enhancement << "x)";
  return os.str();
}

std::vector<std::pair<std::string, double>> Sampler::Metadata() const {
  return {
      {"version", std::atof(kVersion)},
      {"p_beam", fCfg.pBeam},
      {"target_A", fCfg.target.A},
      {"y_shape", static_cast<double>(static_cast<int>(fCfg.yShape))},
      {"tail_n", fCfg.tailN},
      {"data_lo", fCfg.dataLo},
      {"data_hi", fCfg.dataHi},
      {"y_gauss_mean", fCfg.yGauss0},
      {"y_gauss_sigma", fCfg.yGaussSigma},
      {"T", fCfg.T},
      {"p0", fCfg.p0},
      {"pt_pow_n", fCfg.nPow},
      {"f_hard", fNorm.fHard},
      {"mean_pt_sq", fNorm.meanPtSq},
      {"thermal_jacobian", fCfg.thermalJacobian ? 1.0 : 0.0},
      {"lambda_pol", fCfg.lambdaPol},
      {"f_y", fNorm.fY},
      {"f_cos", fNorm.fCos},
      {"chi_mumu", fNorm.chiMuMu},
      {"chi_jpsi", fNorm.chiJpsi},
      {"prob_mumu_per_pot", fNorm.probMuMuPerPot},
      {"chi_mumu_fullcos_diagnostic", fNorm.chiMuMuFullCosDiagnostic},
      {"rate_used", fNorm.rate},
      {"n_pot", fCfg.nPot},
      {"n_events", static_cast<double>(fNEvents)},
      {"weight", fNorm.weight},
      {"enhancement", fNorm.enhancement},
      {"output_mode", static_cast<double>(static_cast<int>(fCfg.output))},
      {"injection", fCfg.injection ? 1.0 : 0.0},
      {"mean_per_event", fNorm.meanPerEvent},
      {"pot_per_event", fCfg.potPerEvent},
      {"seed", static_cast<double>(fCfg.seed)},
  };
}

}  // namespace jpsi
