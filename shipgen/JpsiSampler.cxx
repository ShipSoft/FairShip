// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#include "JpsiSampler.h"

#include <algorithm>
#include <cmath>
#include <fstream>
#include <map>
#include <set>
#include <sstream>
#include <stdexcept>

#include "Math/PdfFuncMathCore.h"
#include "Math/Vector3D.h"
#include "Math/VectorUtil.h"
#include "TMath.h"

namespace jpsi {

namespace {

/// SHiP Table 5 (arXiv:2604.03661), Mo/W target: y_low, B*sigma/A per 0.1
/// in y_cm [pb/nucleon].
struct ShipBin {
  double yLow;
  double value_pb;
};
constexpr ShipBin kShipTable[] = {
    {0.2, 660.34}, {0.3, 473.61}, {0.4, 375.56}, {0.5, 329.45}, {0.6, 291.41},
    {0.7, 240.60}, {0.8, 205.21}, {0.9, 166.79}, {1.0, 135.93}, {1.1, 104.79},
    {1.2, 75.83},  {1.3, 53.78},  {1.4, 30.94},  {1.5, 22.45},  {1.6, 12.84},
    {1.7, 6.25},   {1.8, 0.94},   {1.9, 0.02}};
constexpr double kShipBinWidth = 0.1;

constexpr double kYWindowLo = -0.425;  // NA50 acceptance window
constexpr double kYWindowHi = 0.575;

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
  const double sigmaW_cm2 = w.A / (TMath::Na() * w.lambdaInt_gcm2);
  const double sigma_cm2 = sigmaW_cm2 * std::pow(A / w.A, 0.71);
  t.lambdaInt_gcm2 = A / (TMath::Na() * sigma_cm2);
  return t;
}

TargetSpec MolybdenumScaled() { return TargetFromA(95.95, 10.22, "Mo"); }

std::vector<Layer> LoadLayers(const std::string& path, double* zStart) {
  std::ifstream in(path.c_str());
  if (!in)
    throw std::runtime_error("JpsiSampler: cannot read layer file " + path);
  std::vector<Layer> out;
  std::string line;
  int n = 0;
  while (std::getline(in, line)) {
    ++n;
    const auto h = line.find('#');
    if (h != std::string::npos) line.erase(h);
    std::istringstream is(line);
    std::string key;
    if (!(is >> key)) continue;
    auto bad = [&]() {
      throw std::runtime_error("JpsiSampler: " + path + " line " +
                               std::to_string(n) + ": " + line);
    };
    if (key == "zstart") {
      double z;
      if (!(is >> z)) bad();
      if (zStart) *zStart = z;
    } else if (key == "layer") {
      std::string name;
      double A;
      double rho;
      double len;
      if (!(is >> name >> A >> rho >> len) || A <= 0 || rho <= 0 || len <= 0)
        bad();
      out.push_back(Layer{TargetFromA(A, rho, name), len});
    } else if (key == "gap") {
      double len;
      if (!(is >> len) || len < 0) bad();
      if (len > 0) out.push_back(Layer{TargetFromA(1.0, 0.0, "gap"), len});
    } else {
      bad();
    }
  }
  if (out.empty())
    throw std::runtime_error("JpsiSampler: no layers in " + path);
  return out;
}

DataMap LoadDataMap(const std::string& path) {
  std::ifstream in(path.c_str());
  if (!in)
    throw std::runtime_error("JpsiSampler: cannot read data map " + path);
  std::map<std::string, double> kv;
  std::string line;
  std::string text;
  while (std::getline(in, line)) {
    text += line + "\n";
    const auto h = line.find('#');
    if (h != std::string::npos) line.erase(h);
    std::istringstream is(line);
    std::string key;
    double v;
    // other keys (errors, covariance, fit quality) are information only
    if (is >> key >> v) kv[key] = v;
  }
  auto need = [&](const char* k) {
    auto it = kv.find(k);
    if (it == kv.end())
      throw std::runtime_error(std::string("JpsiSampler: data map ") + path +
                               " has no " + k);
    return it->second;
  };
  auto opt = [&](const char* k, double d) {
    auto it = kv.find(k);
    return it == kv.end() ? d : it->second;
  };
  DataMap m;
  m.on = true;
  m.yJoin = need("y_join");
  m.yHi = need("y_hi");
  m.q0 = need("ptsq_ref");
  m.qMax = need("ptsq_max");
  m.b1 = need("b1");
  m.b2 = need("b2");
  m.c = need("c");
  m.eb1 = opt("b1_err", 0.);
  m.eb2 = opt("b2_err", 0.);
  m.ec = opt("c_err", 0.);
  m.baseMeanPtSq = need("base_mean_pt_sq");
  m.basePtSqSlope = need("base_pt_sq_slope");
  m.baseLambda = need("base_lambda_pol");
  m.tailN = opt("tail_n", NAN);
  m.eTailN = opt("tail_n_err", NAN);
  m.source = path;
  m.text = text;
  return m;
}

void SetDataMap(Config& cfg, const DataMap& m) {
  cfg.dataMap = m;
  // a map with a fitted forward exponent brings its continuation along
  if (std::isfinite(m.tailN)) {
    cfg.forwardTail = ForwardTail::MapEnd;
    cfg.tailN = m.tailN;
  }
}

Config NominalConfig() {
  Config c;
  // <pT^2> = 1.9 GeV^2: NA50-type value for p-A at 400 GeV (systematic band
  // 1.6-2.2), independent of y (the NA50 assumption)
  c.ptSq = 1.9;
  c.ptSqSlope = 0.;
  // Collins-Soper polar coefficient measured by SHiP with the 2018 data,
  // Lambda = 0.11 +- 0.14 (stat) +- 0.02 (syst), arXiv:2604.03661 (variations
  // 0.25 and -0.03)
  c.lambdaPol = 0.11;
  c.yShape = YShape::Data;
  c.tailN = 5.5;
  c.secondaryFactor = 1.10;
  c.dataMap = DataMap();  // SHiP Table 5 as published
  c.physicsWeight = true;
  return c;
}

namespace {

/// The values of one line of a configuration file, read in order.
class ConfigLine {
 public:
  ConfigLine(const std::string& values, const std::string& where)
      : fIs(values), fWhere(where) {}
  double Num() {
    double v;
    if (!(fIs >> v))
      throw std::runtime_error("JpsiSampler: number expected in " + fWhere);
    return v;
  }
  std::string Word() {
    std::string w;
    if (!(fIs >> w))
      throw std::runtime_error("JpsiSampler: value expected in " + fWhere);
    return w;
  }
  /// an optional last number: false if there is none, an error if the token
  /// is not a number
  bool Maybe(double& v) {
    std::string w;
    if (!(fIs >> w)) return false;
    std::size_t used = 0;
    try {
      v = std::stod(w, &used);
    } catch (const std::exception&) {
      used = 0;
    }
    if (used != w.size()) Bad(w);
    return true;
  }
  [[noreturn]] void Bad(const std::string& w) const {
    throw std::runtime_error("JpsiSampler: bad value '" + w + "' in " + fWhere);
  }
  /// nothing may follow the values
  void End() {
    std::string rest;
    if (fIs >> rest)
      throw std::runtime_error("JpsiSampler: unexpected '" + rest + "' in " +
                               fWhere);
  }

 private:
  std::istringstream fIs;
  std::string fWhere;
};

}  // namespace

void ApplyConfigFile(Config& cfg, const std::string& path,
                     std::vector<std::string>* keys) {
  std::ifstream in(path.c_str());
  if (!in)
    throw std::runtime_error("JpsiSampler: cannot read configuration " + path);
  // relative file names inside the file are relative to its directory
  const auto slash = path.rfind('/');
  const std::string dir =
      slash == std::string::npos ? std::string() : path.substr(0, slash + 1);
  auto resolve = [&dir](const std::string& f) {
    return (f.empty() || f[0] == '/') ? f : dir + f;
  };
  static const std::set<std::string> kKeys = {"ptsq",
                                              "fhard",
                                              "pt_sq_slope",
                                              "thermal_slope",
                                              "thermal_jacobian",
                                              "shape",
                                              "tail",
                                              "forward_tail",
                                              "alpha_xf",
                                              "data_lo",
                                              "data_hi",
                                              "y_gauss",
                                              "data_map",
                                              "map_b1",
                                              "map_b2",
                                              "map_c",
                                              "map_base_check",
                                              "secondary",
                                              "secondary_depth",
                                              "lambda",
                                              "target",
                                              "layers",
                                              "output",
                                              "physics_weight",
                                              "n_events",
                                              "n_pot",
                                              "seed"};

  // Read the whole file first: every key at most once, so that the order of
  // the lines does not matter. Each value: (values, position in the file).
  std::map<std::string, std::pair<std::string, std::string>> found;
  std::string line;
  std::string text;
  int ln = 0;
  while (std::getline(in, line)) {
    ++ln;
    text += line + "\n";
    const auto h = line.find('#');
    if (h != std::string::npos) line.erase(h);
    std::istringstream is(line);
    std::string key;
    if (!(is >> key)) continue;
    const std::string where =
        path + ":" + std::to_string(ln) + " (" + key + ")";
    if (kKeys.count(key) == 0)
      throw std::runtime_error("JpsiSampler: unknown key in " + where);
    std::string values;
    std::getline(is, values);
    const auto [it, isNew] = found.emplace(key, std::make_pair(values, where));
    if (!isNew)
      throw std::runtime_error("JpsiSampler: " + where + " repeats " +
                               it->second.second);
    if (keys) keys->push_back(key);
  }
  auto has = [&found](const std::string& key) { return found.count(key) != 0; };
  auto get = [&found](const std::string& key) {
    const auto& v = found.at(key);
    return ConfigLine(v.first, v.second);
  };
  if (has("ptsq") && has("fhard"))
    throw std::runtime_error(
        "JpsiSampler: " + path +
        ": ptsq and fhard both fix the p_T spectrum, give one of them");

  // 1. the data map: a map file brings its own forward continuation, which
  // forward_tail and tail below override
  if (has("data_map")) {
    ConfigLine v = get("data_map");
    const std::string w = v.Word();
    if (w == "none") {
      cfg.dataMap = DataMap();
    } else if (w == "base") {
      cfg.dataMap = DataMap();
      cfg.dataMap.on = true;
      cfg.dataMap.source = "map base (b1 = b2 = c = 0)";
    } else {
      SetDataMap(cfg, LoadDataMap(resolve(w)));
    }
    v.End();
  }
  // 2. changes to the map
  for (const char* key : {"map_b1", "map_b2", "map_c"}) {
    if (!has(key)) continue;
    ConfigLine v = get(key);
    if (!cfg.dataMap.on)
      throw std::runtime_error("JpsiSampler: " + found.at(key).second +
                               " needs a data map (data_map ...)");
    double& par = key == std::string("map_b1")   ? cfg.dataMap.b1
                  : key == std::string("map_b2") ? cfg.dataMap.b2
                                                 : cfg.dataMap.c;
    par = v.Num();
    v.End();
    cfg.dataMap.source += std::string(" [") + key + " changed]";
  }
  if (has("map_base_check")) {
    ConfigLine v = get("map_base_check");
    if (v.Num() == 0.) {
      cfg.dataMap.baseMeanPtSq = -1.;
      cfg.dataMap.basePtSqSlope = NAN;
      cfg.dataMap.baseLambda = NAN;
    }
    v.End();
  }
  // 3. the other keys, each of which sets its own settings
  for (const auto& [key, values] : found) {
    if (key == "data_map" || key.rfind("map_", 0) == 0) continue;
    ConfigLine v(values.first, values.second);
    if (key == "ptsq") {
      cfg.ptSq = v.Num();
    } else if (key == "fhard") {
      cfg.fHard = v.Num();
      cfg.ptSq = -1;
    } else if (key == "pt_sq_slope") {
      cfg.ptSqSlope = v.Num();
    } else if (key == "thermal_slope") {
      cfg.T = v.Num();
    } else if (key == "thermal_jacobian") {
      cfg.thermalJacobian = v.Num() != 0.;
    } else if (key == "shape") {
      const std::string w = v.Word();
      if (w == "data")
        cfg.yShape = YShape::Data;
      else if (w == "gauss")
        cfg.yShape = YShape::Gauss;
      else
        v.Bad(w);
    } else if (key == "tail") {
      cfg.tailN = v.Num();
    } else if (key == "forward_tail") {
      const std::string w = v.Word();
      if (w == "table")
        cfg.forwardTail = ForwardTail::Table;
      else if (w == "map")
        cfg.forwardTail = ForwardTail::MapEnd;
      else
        v.Bad(w);
    } else if (key == "alpha_xf") {
      cfg.alphaXf1 = v.Num();
      cfg.alphaXf2 = v.Num();
      double a = 0.;
      if (v.Maybe(a)) cfg.shapeA = a;
    } else if (key == "data_lo") {
      cfg.dataLo = v.Num();
    } else if (key == "data_hi") {
      cfg.dataHi = v.Num();
    } else if (key == "y_gauss") {
      cfg.yGauss0 = v.Num();
      cfg.yGaussSigma = v.Num();
    } else if (key == "secondary") {
      cfg.secondaryFactor = v.Num();
    } else if (key == "secondary_depth") {
      cfg.secondaryDepth_cm = v.Num();
    } else if (key == "lambda") {
      cfg.lambdaPol = v.Num();
    } else if (key == "target") {
      const std::string w = v.Word();
      if (w == "W")
        cfg.target = TungstenNA50();
      else if (w == "Mo")
        cfg.target = MolybdenumScaled();
      else
        v.Bad(w);
    } else if (key == "layers") {
      cfg.layers = LoadLayers(resolve(v.Word()), &cfg.zStart_cm);
    } else if (key == "output") {
      const std::string w = v.Word();
      if (w == "mumu")
        cfg.output = Output::MuMu;
      else if (w == "jpsi")
        cfg.output = Output::Jpsi;
      else if (w == "both")
        cfg.output = Output::Both;
      else
        v.Bad(w);
    } else if (key == "physics_weight") {
      cfg.physicsWeight = v.Num() != 0.;
    } else if (key == "n_events") {
      cfg.nEvents = static_cast<int64_t>(v.Num());
      cfg.enhancement = -1;
    } else if (key == "n_pot") {
      cfg.nPot = v.Num();
    } else if (key == "seed") {
      cfg.seed = static_cast<std::uint64_t>(v.Num());
    }
    v.End();
  }
  cfg.provenance += "# configuration file " + path + "\n" + text;
}

// ---------------------------------------------------------------- helpers

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

  fNorm.aEff = EffectiveA();
  BuildPtGrids();
  if (fCfg.dataMap.on) {
    // the map corrects one base configuration: the p_T spectrum and the
    // polarisation it was fitted on
    const DataMap& m = fCfg.dataMap;
    std::ostringstream os;
    if (m.baseMeanPtSq > 0 &&
        std::fabs(fNorm.meanPtSq - m.baseMeanPtSq) > 1e-3 * m.baseMeanPtSq)
      os << " <pT^2>(y=0) " << fNorm.meanPtSq << " (map: " << m.baseMeanPtSq
         << ")";
    if (std::isfinite(m.basePtSqSlope) &&
        std::fabs(fCfg.ptSqSlope - m.basePtSqSlope) > 1e-6)
      os << " pT slope " << fCfg.ptSqSlope << " (map: " << m.basePtSqSlope
         << ")";
    if (std::isfinite(m.baseLambda) &&
        std::fabs(fCfg.lambdaPol - m.baseLambda) > 1e-6)
      os << " lambda " << fCfg.lambdaPol << " (map: " << m.baseLambda << ")";
    if (!os.str().empty())
      throw std::runtime_error(
          "JpsiSampler: data map " + m.source +
          " was fitted on another base configuration:" + os.str());
  }
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
  if (fCfg.yShape != YShape::Data && fCfg.yShape != YShape::Gauss)
    fail("unknown rapidity shape");
  if (fCfg.secondaryFactor <= 0) fail("secondary factor must be positive");
  if (fCfg.secondaryDepth_cm < 0) fail("secondary depth must be >= 0");
  if (!(fCfg.shapeA > 0))
    fail("alpha_xf: the shape mass number must be positive");
  if (std::fabs(fCfg.alphaXf1) > 2 || std::fabs(fCfg.alphaXf2) > 2)
    fail("alpha_xf coefficients beyond |2| are not physical");
  if (fCfg.forwardTail == ForwardTail::MapEnd && !fCfg.dataMap.on)
    fail("forward_tail map needs a data map");
  if (fCfg.secondaryDepth_cm > 0 && fCfg.layers.empty())
    fail("the secondary depth variation needs a layer model");
  if (fCfg.dataMap.on) {
    const DataMap& m = fCfg.dataMap;
    if (fCfg.yShape != YShape::Data)
      fail("the data map needs the Data rapidity shape");
    if (std::isnan(m.yHi) || std::isnan(m.yJoin) || std::isnan(m.qMax) ||
        m.yHi <= m.yJoin || m.qMax <= 0)
      fail("data map: empty y range or p_T^2 cap");
    if (m.yJoin < fCfg.dataLo || m.yHi >= fCfg.dataHi)
      fail("data map range must end below the end of the SHiP table");
    if (!std::isfinite(m.b1) || !std::isfinite(m.b2) || !std::isfinite(m.c))
      fail("data map parameters not finite");
  }
  if (fCfg.injection) {
    if (fCfg.potPerEvent <= 0) fail("potPerEvent must be positive");
    if (fCfg.enhancement <= 0 && fCfg.meanPerEvent <= 0) {
      fail("injection needs an enhancement or a mean number per event");
    }
  } else if (fCfg.physicsWeight) {
    if (fCfg.potPerEvent <= 0) fail("potPerEvent must be positive");
    if (fCfg.nEvents <= 0) fail("nEvents must be > 0");
  } else {
    if (fCfg.nPot <= 0) fail("nPot must be positive");
    if (fCfg.enhancement <= 0 && fCfg.nEvents <= 0) fail("nEvents must be > 0");
  }
  bool dense = fCfg.layers.empty();
  for (const auto& l : fCfg.layers) {
    if (l.length_cm <= 0) fail("layer length must be positive");
    if (l.material.A <= 0 || l.material.density_gcm3 < 0)
      fail("layer material is not physical");
    dense |= l.material.density_gcm3 > 0;
  }
  if (!dense) fail("the layer stack has no material");
}

double Sampler::PtSqAt(double y) const {
  // <pT^2> depends on |x_F|, so the rapidity dependence is symmetric in y_cm:
  // <pT^2>(y) = ptSq + slope * |y|. The data constrain 0.2 < y < 1.8; beyond
  // that this is an extrapolation, clipped in BuildPtGrids to what is
  // reachable.
  return fCfg.ptSq + fCfg.ptSqSlope * std::fabs(y);
}

void Sampler::BuildPtGrids() {
  constexpr int kN = 4001;
  fPtGrid.resize(kN);
  fPtThermal.resize(kN);
  fPtHard.resize(kN);
  for (int i = 0; i < kN; ++i) {
    const double pt = fCfg.ptMax * i / (kN - 1);
    fPtGrid[i] = pt;
    const double mt = std::hypot(kMJpsi, pt);
    const double jac = fCfg.thermalJacobian ? pt : 1.0;
    fPtThermal[i] = jac * mt * std::cyl_bessel_k(1., mt / fCfg.T);
    fPtHard[i] = pt * std::pow(1 + (pt / fCfg.p0) * (pt / fCfg.p0), -fCfg.nPow);
  }
  auto normalise = [this](std::vector<double>& f) {
    const double integral = Trapezoid(fPtGrid, f);
    for (auto& v : f) v /= integral;
  };
  normalise(fPtThermal);
  normalise(fPtHard);

  // rapidity nodes covering the kinematically allowed range
  const double yKin = std::asinh(fSqrtS / (2 * kMJpsi));
  constexpr int kNodes = 161;  // node spacing 0.027 in y (81 before v1.5)
  fPtNodeY.resize(kNodes);
  fPtPdfN.assign(kNodes, std::vector<double>(kN, 0.));
  fPtCdfN.assign(kNodes, std::vector<double>(kN, 0.));
  fPtNodeScale.assign(kNodes, 1.);
  const double a = PtMoment(fPtThermal, 2);
  const double b = PtMoment(fPtHard, 2);
  const double floorSq = std::min(a, b);
  const double ceilSq = std::max(a, b);
  int nClipped = 0;
  int nSoft = 0;
  // Below the mixture's floor the spectrum is the softer component alone,
  // rescaled continuously to the requested <pT^2>: the power law through its
  // scale p0 (a pure rescaling of p_T), the thermal term through T. At the
  // floor the rescaled component equals the mixture (fHard = 1 or 0), so the
  // spectrum and its tail change continuously with y.
  const bool floorIsHard = b < a;
  auto component = [this, floorIsHard](double scale) {
    std::vector<double> f(fPtGrid.size());
    for (std::size_t i = 0; i < fPtGrid.size(); ++i) {
      const double pt = fPtGrid[i];
      if (floorIsHard) {
        const double r = pt / (fCfg.p0 * scale);
        f[i] = pt * std::pow(1 + r * r, -fCfg.nPow);
      } else {
        const double mt = std::hypot(kMJpsi, pt);
        f[i] = (fCfg.thermalJacobian ? pt : 1.0) * mt *
               std::cyl_bessel_k(1., mt / (fCfg.T * scale));
      }
    }
    const double integral = Trapezoid(fPtGrid, f);
    for (auto& v : f) v /= integral;
    return f;
  };
  constexpr double kMinPtSq = 0.2;  // GeV^2, lowest <pT^2> the model accepts
  for (int n = 0; n < kNodes; ++n) {
    const double y = -yKin + 2 * yKin * n / (kNodes - 1);
    fPtNodeY[n] = y;
    double fHard = fCfg.fHard;
    bool soft = false;
    std::vector<double> softPdf;
    if (fCfg.ptSq > 0) {
      double want = PtSqAt(y);
      const bool measured =
          std::fabs(y) < 1.8;  // the region the data constrain
      if (want > ceilSq || want < kMinPtSq) {
        if (measured) {
          std::ostringstream os;
          os << "JpsiSampler: <pT^2>(y=" << y << ") = " << want
             << " not reachable, range [" << kMinPtSq << ", " << ceilSq << "]";
          throw std::runtime_error(os.str());
        }
        want = std::min(ceilSq, std::max(kMinPtSq, want));  // extrapolation
        ++nClipped;
      }
      if (want < floorSq) {
        double lo = 0.05;
        double hi = 1.;  // scale of p0 or T
        for (int it = 0; it < 50; ++it) {
          const double mid = 0.5 * (lo + hi);
          (PtMoment(component(mid), 2) < want ? lo : hi) = mid;
        }
        softPdf = component(0.5 * (lo + hi));
        soft = true;
        fHard = floorIsHard ? 1. : 0.;
        ++nSoft;
      } else {
        fHard = (want - a) / (b - a);
      }
    }
    for (int i = 0; i < kN; ++i)
      fPtPdfN[n][i] =
          soft ? softPdf[i] : (1 - fHard) * fPtThermal[i] + fHard * fPtHard[i];
    // data map: the y-p_T correlation part reshapes the spectrum; its integral
    // (kept in fPtNodeScale and in the density itself) changes the y density,
    // exactly as a weight would
    // The nuclear x_F factor (optional) acts the same way: it depends on y
    // and p_T through x_F.
    const bool mapPt = fCfg.dataMap.on && fCfg.dataMap.c != 0.;
    const bool nucl = fCfg.alphaXf1 != 0. || fCfg.alphaXf2 != 0.;
    if (mapPt || nucl) {
      for (int i = 0; i < kN; ++i) {
        if (mapPt)
          fPtPdfN[n][i] *= DataMapPtFactor(fCfg.dataMap, y, fPtGrid[i]);
        if (nucl) fPtPdfN[n][i] *= NuclearXfFactor(y, fPtGrid[i]);
      }
      fPtNodeScale[n] = Trapezoid(fPtGrid, fPtPdfN[n]);
    }
    MakeCdf(fPtGrid, fPtPdfN[n], fPtCdfN[n]);
    if (n == (kNodes - 1) / 2) {  // y = 0: the numbers quoted in the summary
                                  // (the map is 1 there)
      fNorm.fHard = fHard;
      fNorm.meanPt = PtMoment(fPtPdfN[n], 1);
      fNorm.meanPtSq = PtMoment(fPtPdfN[n], 2);
    }
  }
  fNorm.ptSqSlope = fCfg.ptSqSlope;
  // reported in Summary(): with a negative slope, the nodes at large |y| use
  // the rescaled floor component, which is part of the model, not a warning
  fNorm.ptNodes = kNodes;
  fNorm.ptNodesSoftened = nSoft;
  fNorm.ptNodesClipped = nClipped;
  fNorm.ptMixtureFloor = floorSq;
  fNorm.nuclearXfAt16 = NuclearXfFactor(1.6, 1.0);
}

double Sampler::PtMoment(const std::vector<double>& pdf, int k) const {
  std::vector<double> f(pdf.size());
  for (std::size_t i = 0; i < pdf.size(); ++i) {
    f[i] = std::pow(fPtGrid[i], k) * pdf[i];
  }
  return Trapezoid(fPtGrid, f);
}

int Sampler::PtNode(double y) const {
  if (fPtNodeY.empty()) return 0;
  const double lo = fPtNodeY.front();
  const double hi = fPtNodeY.back();
  const int n = static_cast<int>(fPtNodeY.size());
  const int k = static_cast<int>(std::llround((y - lo) / (hi - lo) * (n - 1)));
  return std::min(n - 1, std::max(0, k));
}

double Sampler::PtCdfAt(double pt, double y) const {
  return Interpolate(fPtGrid, fPtCdfN[PtNode(y)], pt);
}

double Sampler::PtMaxAt(double y) const {
  // Exact kinematic limit: baryon number leaves at least two nucleons (p N ->
  // J/psi p N), so the J/psi energy in the centre of mass is at most E*max = (s
  // + M^2 - (2 m_p)^2) / (2 sqrt(s)), i.e. mT cosh(y) <= E*max. (Before v1.6:
  // |x_F| < 1, which ignores the recoil mass and allowed the J/psi up to 405.5
  // GeV in the lab instead of 398.6 GeV at 400 GeV/c.)
  const double s = fSqrtS * fSqrtS;
  const double mx = 2 * kMProton;
  const double eMax = (s + kMJpsi * kMJpsi - mx * mx) / (2 * fSqrtS);
  const double mtMax = eMax / std::cosh(y);
  if (mtMax <= kMJpsi) return 0.;
  return std::min(fCfg.ptMax, std::sqrt(mtMax * mtMax - kMJpsi * kMJpsi));
}

double Sampler::TailFactor(double y, double pt) const {
  // dN/dxF ~ (1-|xF|)^n turned into a density in y at fixed pT
  const double mt = std::hypot(kMJpsi, pt);
  const double xf = 2 * mt * std::sinh(y) / fSqrtS;
  const double base = std::max(0.0, 1.0 - std::abs(xf));
  const double jac = 2 * mt * std::cosh(y) / fSqrtS;
  return std::pow(base, fCfg.tailN) * jac;
}

double Sampler::TailDensity(double y) const {
  // dsigma/dy of the tail: f(pT | y) (1-|xF|)^n |dxF/dy| integrated over the
  // allowed pT, rather than evaluated at a reference transverse mass. The
  // kinematic limit is applied here, once.
  constexpr int kNpt = 400;
  double sum = 0.;
  const double ptMax = PtMaxAt(y);
  if (ptMax <= 0) return 0.;
  const auto& pdf = fPtPdfN[PtNode(y)];
  for (int i = 0; i <= kNpt; ++i) {
    const double pt = ptMax * i / kNpt;
    const double w = (i == 0 || i == kNpt) ? 0.5 : 1.0;
    sum +=
        w * Interpolate(fPtGrid, pdf, pt) * TailFactor(y, pt) * (ptMax / kNpt);
  }
  return sum;
}

void Sampler::BuildYGrid() {
  // Grid limit: the largest rapidity still allowed for pT -> 0.
  const double yKin = std::asinh(fSqrtS / (2 * kMJpsi));
  constexpr int kN = 20001;
  fYGrid.resize(kN);
  fYPdf.assign(kN, 0.);
  fYJoint.assign(kN, 0.);
  fTailStart = HUGE_VAL;
  fTailJoint = 0.;
  for (int i = 0; i < kN; ++i) fYGrid[i] = -yKin + 2 * yKin * i / (kN - 1);

  auto gauss = [this](double y) {
    return ROOT::Math::normal_pdf(y, fCfg.yGaussSigma, fCfg.yGauss0);
  };
  // fraction of the p_T spectrum allowed at y, times the node's integral
  // (fPtNodeScale: the mean of the data map's p_T factor, 1 without a map)
  auto allowed = [this](double y) {
    return PtCdfAt(PtMaxAt(y), y) * fPtNodeScale[PtNode(y)];
  };

  // Outside the tail the joint density is base(y) f(pT | y) for pT <
  // ptMax(y); fYJoint holds base(y), and the y density is base(y) times the
  // allowed part of f. The same factor is used for generation and for f_y,
  // so the normalised density and the generated sample are identical by
  // construction.
  if (fCfg.yShape == YShape::Gauss) {
    for (int i = 0; i < kN; ++i) fYJoint[i] = gauss(fYGrid[i]);
  } else {  // Data
    double firstVal = -1.;
    double lastVal = -1.;
    for (const auto& b : kShipTable) {
      if (b.yLow >= fCfg.dataLo - 1e-9 && b.yLow < fCfg.dataHi - 1e-9) {
        if (firstVal < 0) firstVal = b.value_pb / kShipBinWidth;
        lastVal = b.value_pb / kShipBinWidth;
      }
    }
    if (firstVal <= 0)
      throw std::runtime_error("JpsiSampler: empty data range");
    auto tableAt = [](double y) {
      for (const auto& b : kShipTable)
        if (y >= b.yLow && y < b.yLow + kShipBinWidth)
          return b.value_pb / kShipBinWidth;
      return 0.;
    };
    double tailLevel = lastVal;  // base(y) just below the start of the tail
    double tailStart = fCfg.dataHi;
    if (fCfg.dataMap.on && fCfg.forwardTail == ForwardTail::MapEnd) {
      // The map up to its end (yHi), then directly the (1-|xF|)^n tail with
      // the exponent fitted to the same data: no SHiP table bin is used.
      const DataMap& m = fCfg.dataMap;
      tailStart = m.yHi;
      tailLevel = gauss(m.yHi) * DataMapYFactor(m, m.yHi);
      for (int i = 0; i < kN; ++i) {
        const double y = fYGrid[i];
        if (y < m.yHi) fYJoint[i] = gauss(y) * DataMapYFactor(m, y);
      }
    } else if (fCfg.dataMap.on) {
      // The map drives the shape: the NA50 Gaussian (which also fixes the
      // absolute rate in its window) times the map up to the end of the map
      // (yHi). The SHiP table is used only beyond the map, between yHi and
      // dataHi, scaled to the map level at yHi; then the tail.
      const DataMap& m = fCfg.dataMap;
      const double tableHi = tableAt(m.yHi + 1e-9);
      if (!(tableHi > 0))
        throw std::runtime_error(
            "JpsiSampler: no SHiP table bin above the data map range");
      const double kT = gauss(m.yHi) * DataMapYFactor(m, m.yHi) /
                        tableHi;  // table -> map level at yHi
      tailLevel = lastVal * kT;
      for (int i = 0; i < kN; ++i) {
        const double y = fYGrid[i];
        if (y < m.yHi)
          fYJoint[i] = gauss(y) * DataMapYFactor(m, y);
        else if (y < fCfg.dataHi)
          fYJoint[i] = tableAt(y) * kT;
      }
    } else {
      // The Gaussian is matched at dataLo itself, not at a bin centre, so the
      // density is continuous there.
      const double gScale = firstVal / gauss(fCfg.dataLo);
      for (int i = 0; i < kN; ++i) {
        const double y = fYGrid[i];
        if (y < fCfg.dataLo)
          fYJoint[i] = gScale * gauss(y);
        else if (y < fCfg.dataHi)
          fYJoint[i] = tableAt(y);
      }
    }
    // Tail: joint density fTailJoint f(pT | y) (1-|xF|)^n |dxF/dy|, so the y
    // density (TailDensity) and the p_T drawn at that y (DrawKinematics) come
    // from the same function. fTailJoint continues the density below the tail
    // at its start, where that side carries the allowed fraction.
    const double tailAtStart = TailDensity(tailStart);
    if (!(tailAtStart > 0))
      throw std::runtime_error(
          "JpsiSampler: the tail starts beyond the kinematic limit");
    fTailStart = tailStart;
    fTailJoint = tailLevel * allowed(tailStart) / tailAtStart;
  }

  for (int i = 0; i < kN; ++i) {
    const double y = fYGrid[i];
    if (InTail(y)) {
      fYJoint[i] = 0.;
      fYPdf[i] = fTailJoint * TailDensity(y);
    } else {
      fYPdf[i] = fYJoint[i] * allowed(y);
    }
  }
  MakeCdf(fYGrid, fYPdf, fYCdf);
}

double Sampler::EffectiveA() const {
  // J/psi production share of each slab: n_A sigma_J(A) times the beam
  // surviving to it, integrated over the slab; geometric mean of A
  if (fCfg.layers.empty()) return fCfg.target.A;
  const TargetSpec w = TungstenNA50();
  double tau = 0.;
  double sw = 0.;
  double swl = 0.;
  for (const auto& l : fCfg.layers) {
    const double rho = l.material.density_gcm3;
    if (!(rho > 0)) continue;
    const double li = rho / l.material.lambdaInt_gcm2;  // 1/cm
    const double part =
        (std::exp(-tau) - std::exp(-tau - li * l.length_cm)) / li;
    const double wgt =
        rho / l.material.A * std::pow(l.material.A, w.alphaA) * part;
    sw += wgt;
    swl += wgt * std::log(l.material.A);
    tau += li * l.length_cm;
  }
  return sw > 0 ? std::exp(swl / sw) : fCfg.target.A;
}

double Sampler::NuclearXfFactor(double y, double pt) const {
  if (fCfg.alphaXf1 == 0. && fCfg.alphaXf2 == 0.) return 1.;
  const double xf =
      std::fabs(2 * std::hypot(kMJpsi, pt) * std::sinh(y) / fSqrtS);
  const double da = fCfg.alphaXf1 * xf + fCfg.alphaXf2 * xf * xf;
  return std::pow(fNorm.aEff / fCfg.shapeA, da);
}

void Sampler::BuildTargetModel() {
  if (fCfg.layers.empty()) return;
  constexpr int kNz = 8001;
  double total = 0.;
  for (const auto& l : fCfg.layers) total += l.length_cm;

  fZGrid.resize(kNz);
  std::vector<double> dens(kNz, 0.);  // vertex density (arbitrary scale)
  std::vector<double> rate(kNz, 0.);  // d(P_mumu/POT)/dz, absolute
  const TargetSpec w = TungstenNA50();
  // B*sigma_Jpsi(A) = c A^alpha with c fixed by the NA50 tungsten point.
  const double cJpsi_nb =
      w.bSigmaWindow_nb /
      std::pow(w.A, w.alphaA - 1.0);  // nb, per nucleus /A^a

  double tau = 0.;  // interaction lengths traversed
  const double dz = total / (kNz - 1);
  std::map<std::string, double> byMaterial;
  std::vector<const Layer*> material(kNz, nullptr);
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
        here->material.density_gcm3 * TMath::Na() / here->material.A;
    // B*sigma(J/psi) for this nucleus, full phase space, in cm^2
    const double bSigma_cm2 =
        cJpsi_nb * std::pow(here->material.A, w.alphaA) * 1e-33;
    dens[i] = std::exp(-tau) * nA_cm3 * bSigma_cm2;
    rate[i] = dens[i];
    material[i] = here;
  }
  // Depth variation of the secondary component (modelling assumption): its
  // vertices follow the primary ones convolved with exp(-dz / depth),
  // restricted to material, with the same integral (secondaryFactor - 1) as
  // when it sits at the primary depth. The rate is unchanged.
  const double extra = fCfg.secondaryFactor - 1.;
  if (fCfg.secondaryDepth_cm > 0 && extra > 0) {
    std::vector<double> sec(kNz, 0.);
    const double decay = std::exp(-dz / fCfg.secondaryDepth_cm);
    double carried = 0.;
    for (int i = 0; i < kNz; ++i) {
      carried = carried * decay + dens[i] * dz / fCfg.secondaryDepth_cm;
      sec[i] = material[i]->material.density_gcm3 > 0 ? carried : 0.;
    }
    const double norm = Trapezoid(fZGrid, sec);
    if (norm > 0) {
      const double scale = extra * Trapezoid(fZGrid, dens) / norm;
      for (int i = 0; i < kNz; ++i) dens[i] += scale * sec[i];
    }
  }
  for (int i = 0; i < kNz; ++i)
    byMaterial[material[i]->material.name] += dens[i] * dz;
  MakeCdf(fZGrid, dens, fZCdf);
  fNorm.pInteract = 1. - std::exp(-tau);
  fNorm.targetLength_cm = total;
  double sum = 0.;
  for (const auto& kv : byMaterial) sum += kv.second;
  fNorm.materialShare.clear();
  for (const auto& kv : byMaterial)
    if (kv.second > 0)
      fNorm.materialShare.push_back({kv.first, kv.second / sum});
  // The acceptance division is applied in Normalise(), where f_y and f_cos are
  // known; here we only integrate the window-restricted rate.
  fNorm.probMuMuPerPot = Trapezoid(fZGrid, rate);
}

void Sampler::Normalise() {
  // Deterministic f_y: the rapidity density already contains the kinematic
  // validity factor, so integrating it over the NA50 window is exact.
  const double inWindow = Interpolate(fYGrid, fYCdf, kYWindowHi) -
                          Interpolate(fYGrid, fYCdf, kYWindowLo);
  fNorm.fY = inWindow;
  fNorm.fCos = CosAcceptance(fCfg.lambdaPol, 0.5);

  const double acceptance = fNorm.fY * fNorm.fCos;
  fNorm.bSigmaFull_nb = fCfg.target.bSigmaWindow_nb / acceptance;
  const double sigmaInel_cm2 =
      fCfg.target.A / (TMath::Na() * fCfg.target.lambdaInt_gcm2);
  fNorm.sigmaInel_mb = sigmaInel_cm2 * 1e27;
  fNorm.chiMuMuPrimary =
      fCfg.target.A * fNorm.bSigmaFull_nb * 1e-6 / fNorm.sigmaInel_mb;
  // thin-target (NA50) rate scaled up for secondary production in a thick
  // target
  fNorm.secondaryFactor = fCfg.secondaryFactor;
  fNorm.chiMuMu = fNorm.chiMuMuPrimary * fNorm.secondaryFactor;
  fNorm.chiJpsi = fNorm.chiMuMu / kBrMuMu;
  fNorm.chiMuMuFullCosDiagnostic = fNorm.chiMuMu * fNorm.fCos;  // f_cos -> 1

  if (fNorm.probMuMuPerPot > 0) {
    fNorm.probMuMuPerPot /= acceptance;  // window -> full phase space
  }

  RecomputeRate();
}

void Sampler::RecomputeRate() {
  // Rate the weight is built from:
  //   per POT when the target was modelled (slab stack or geometry scan),
  //   otherwise per interacting proton.
  //   Output::Jpsi is an inclusive sample, so it divides by the branching
  //   ratio.
  const bool inclusive = (fCfg.output == Output::Jpsi);
  // per POT (target modelled): the primary rate times the secondary factor, as
  // for chiMuMu
  const double rateMuMu = fNorm.probMuMuPerPot > 0
                              ? fNorm.probMuMuPerPot * fNorm.secondaryFactor
                              : fNorm.chiMuMu;
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
  if (fCfg.physicsWeight) {
    // physics weight: expected J/psi (-> mu mu) per POT that one event stands
    // for (potPerEvent POT each); the number of POT is applied in the analysis
    fNorm.weight = fNorm.rate * fCfg.potPerEvent;
    fNorm.enhancement = 0.;
    return;
  }
  if (fCfg.enhancement > 0) {
    fNEvents = std::max<int64_t>(
        1, std::llround(fCfg.enhancement * fCfg.nPot * fNorm.rate));
  }
  fNorm.weight = fCfg.nPot * fNorm.rate / static_cast<double>(fNEvents);
  fNorm.enhancement = fNorm.weight > 0 ? 1.0 / fNorm.weight : 0.;
}

int Sampler::NumberToInject() {
  const double mu = fNorm.meanPerEvent;
  const int base = static_cast<int>(std::floor(mu));
  return base + (fFlat(fRng) < mu - base ? 1 : 0);
}

double Sampler::YDensity(double y) const {
  return Interpolate(fYGrid, fYPdf, y);
}

double Sampler::JointDensity(double y, double pt) const {
  if (pt < 0 || pt > PtMaxAt(y)) return 0.;
  const double f = Interpolate(fPtGrid, fPtPdfN[PtNode(y)], pt);
  if (InTail(y)) return fTailJoint * f * TailFactor(y, pt);
  return Interpolate(fYGrid, fYJoint, y) * f;
}

double Sampler::SamplePt(double y) {
  return InvertCdf(fPtGrid, fPtCdfN[PtNode(y)], fFlat(fRng));
}
double Sampler::SampleY() { return InvertCdf(fYGrid, fYCdf, fFlat(fRng)); }

void Sampler::DrawKinematics(double& y, double& pt) {
  // y is drawn from its marginal, which already includes the kinematic limit;
  // pT is then drawn from the conditional of the same joint density
  // (JointDensity): the pT spectrum truncated at ptMax(y), times the tail
  // factor (1-|xF|)^n |dxF/dy| above dataHi.
  y = SampleY();
  pt = DrawPt(y);
}

double Sampler::DrawPt(double y) {
  const int node = PtNode(y);  // <pT^2> may depend on y
  const double ptMax = PtMaxAt(y);
  const double uMax = Interpolate(fPtGrid, fPtCdfN[node], ptMax);
  double pt = InvertCdf(fPtGrid, fPtCdfN[node], fFlat(fRng) * uMax);
  if (!InTail(y)) return pt;
  // Tail (y > 0): (1-|xF|)^n falls and |dxF/dy| rises with mT, so their
  // product is below (1-|xF(pT=0)|)^n |dxF/dy|(ptMax). Accept-reject against
  // that bound.
  const double xf0 = 2 * kMJpsi * std::sinh(y) / fSqrtS;
  const double bound =
      std::pow(std::max(0.0, 1.0 - std::abs(xf0)), fCfg.tailN) * 2 *
      std::hypot(kMJpsi, ptMax) * std::cosh(y) / fSqrtS;
  for (int it = 0; it < 100000; ++it) {
    if (fFlat(fRng) * bound <= TailFactor(y, pt)) return pt;
    pt = InvertCdf(fPtGrid, fPtCdfN[node], fFlat(fRng) * uMax);
  }
  return pt;
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

void Sampler::Decay(const ROOT::Math::PxPyPzEVector& jpsi, double cosTheta,
                    ROOT::Math::PxPyPzEVector& mup,
                    ROOT::Math::PxPyPzEVector& mum) {
  using ROOT::Math::PxPyPzEVector;
  using ROOT::Math::XYZVector;
  using ROOT::Math::VectorUtil::boost;
  // Collins-Soper axes: in the J/psi rest frame, z bisects the beam direction
  // and the reverse of the target direction.
  const XYZVector toRest = jpsi.BoostToCM();
  const double eBeam = std::hypot(fCfg.pBeam, kMProton);
  const XYZVector p1 =
      boost(PxPyPzEVector(0., 0., fCfg.pBeam, eBeam), toRest).Vect().Unit();
  const XYZVector p2 =
      boost(PxPyPzEVector(0., 0., 0., kMProton), toRest).Vect().Unit();
  const XYZVector zAxis = (p1 - p2).Unit();
  XYZVector yAxis = p1.Cross(p2);
  yAxis = yAxis.R() < 1e-9 ? XYZVector(0., 1., 0.) : yAxis.Unit();
  const XYZVector xAxis = yAxis.Cross(zAxis).Unit();

  const double pStar = std::sqrt(0.25 * kMJpsi * kMJpsi - kMMu * kMMu);
  const double sinTheta = std::sqrt(std::max(0.0, 1 - cosTheta * cosTheta));
  const double phi = TMath::TwoPi() * fFlat(fRng);
  const XYZVector dir =
      pStar * (sinTheta * std::cos(phi) * xAxis +
               sinTheta * std::sin(phi) * yAxis + cosTheta * zAxis);
  const double eMu = 0.5 * kMJpsi;
  mup = boost(PxPyPzEVector(dir.X(), dir.Y(), dir.Z(), eMu), -toRest);
  mum = boost(PxPyPzEVector(-dir.X(), -dir.Y(), -dir.Z(), eMu), -toRest);
}

double Sampler::SampleVertex() {
  if (fZCdf.empty()) return fCfg.zStart_cm;
  return InvertCdf(fZGrid, fZCdf, fFlat(fRng));
}

Event Sampler::Next() {
  Event ev;
  double y = 0.;
  double pt = 0.;
  DrawKinematics(y, pt);

  const double phi = TMath::TwoPi() * fFlat(fRng);
  const double mt = std::hypot(kMJpsi, pt);
  const double yLab = y + fYShift;
  ev.jpsi.SetPxPyPzE(pt * std::cos(phi), pt * std::sin(phi),
                     mt * std::sinh(yLab), mt * std::cosh(yLab));
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
  os << "JpsiSampler v" << kVersion << " ["
     << (fCfg.layers.empty() ? fCfg.target.name : std::string("layer stack"))
     << "] p_beam = " << fCfg.pBeam << " GeV/c, sqrt(s) = " << fSqrtS
     << " GeV, y_lab = y_cm + " << fYShift << "\n  pT: T = " << fCfg.T
     << " GeV, fHard = " << fNorm.fHard << ", <pT> = " << fNorm.meanPt
     << ", <pT^2>(y=0) = " << fNorm.meanPtSq
     << " GeV^2, d<pT^2>/dy = " << fCfg.ptSqSlope;
  if (fNorm.ptNodesSoftened > 0)
    os << "\n      softer component rescaled at " << fNorm.ptNodesSoftened
       << " of " << fNorm.ptNodes << " rapidity nodes (large |y|, where "
       << "<pT^2>(y) is below the mixture's floor of " << fNorm.ptMixtureFloor
       << " GeV^2)";
  if (fNorm.ptNodesClipped > 0)
    os << "\n      <pT^2>(y) clipped to the reachable range at "
       << fNorm.ptNodesClipped << " of " << fNorm.ptNodes
       << " rapidity nodes (|y| > 1.8, outside the measured region)";
  os << "\n  y : shape = " << (fCfg.yShape == YShape::Gauss ? "Gauss" : "Data")
     << ", tail n = " << fCfg.tailN;
  if (fCfg.dataMap.on) {
    const DataMap& m = fCfg.dataMap;
    if (fCfg.forwardTail == ForwardTail::MapEnd)
      os << "\n  y shape: NA50 Gaussian x data map up to y = " << m.yHi
         << ", then (1-|xF|)^" << fCfg.tailN << " matched to the map there"
         << (std::isfinite(m.tailN)
                 ? " (exponent fitted to the same data, +- " +
                       std::to_string(m.eTailN) + ")"
                 : "");
    else
      os << "\n  y shape: NA50 Gaussian x data map up to y = " << m.yHi
         << ", SHiP table only above (scaled to the map level), then the tail";
    os << "\n  data map " << m.source
       << ": w = exp(D (b1 + b2 D) + c D (pT^2 - " << m.q0 << ")), D = y - "
       << m.yJoin << " clamped to [0, " << m.yHi - m.yJoin
       << "], pT^2 capped at " << m.qMax << "\n      b1 = " << m.b1 << " +- "
       << m.eb1 << ", b2 = " << m.b2 << " +- " << m.eb2 << ", c = " << m.c
       << " +- " << m.ec;
  } else {
    os << "\n  no data map: SHiP Table 5 shape as published";
  }
  if (fCfg.alphaXf1 != 0. || fCfg.alphaXf2 != 0.)
    os << "\n  nuclear x_F factor: (A_eff / " << fCfg.shapeA << ")^("
       << fCfg.alphaXf1 << " xF + " << fCfg.alphaXf2
       << " xF^2), A_eff = " << fNorm.aEff
       << "; at y = 1.6, p_T = 1 GeV: " << fNorm.nuclearXfAt16;
  os << "\n  lambda = " << fCfg.lambdaPol << ", f_cos = " << fNorm.fCos
     << ", f_y = " << fNorm.fY << "\n  B*sigma/A = " << fNorm.bSigmaFull_nb
     << " nb/nucleon (full phase space), sigma_inel = " << fNorm.sigmaInel_mb
     << " mb";
  os.unsetf(std::ios::fixed);
  os.precision(6);
  os << "\n  secondary factor = " << fNorm.secondaryFactor
     << " (modelling assumption; thin-target chi_mumu = "
     << fNorm.chiMuMuPrimary << ")";
  if (fCfg.secondaryDepth_cm > 0)
    os << ", secondary vertices shifted deeper by exp(-dz / "
       << fCfg.secondaryDepth_cm << " cm)";
  os << "\n  chi_mumu = " << fNorm.chiMuMu
     << " / interacting proton, chi_Jpsi = " << fNorm.chiJpsi;
  if (fNorm.probMuMuPerPot > 0) {
    os << "\n  P(J/psi->mumu) per POT = " << fNorm.probMuMuPerPot
       << " primary, x " << fNorm.secondaryFactor << " = "
       << fNorm.probMuMuPerPot * fNorm.secondaryFactor
       << " (integrated over the target model)";
    if (!fCfg.layers.empty()) {
      os << "\n  layers: " << fCfg.layers.size() << ", "
         << fNorm.targetLength_cm << " cm from z = " << fCfg.zStart_cm
         << " cm, P(interaction) = " << fNorm.pInteract << "; J/psi made in:";
      for (const auto& m : fNorm.materialShare)
        os << " " << m.first << " " << m.second;
    }
    os << "\n  weights are per POT";
  } else {
    os << "\n  weights are per interacting proton (thin-target "
       << fCfg.target.name << ")";
  }
  if (fCfg.injection) {
    os << "\n  injection: " << fNorm.meanPerEvent << " J/psi per host event ("
       << fCfg.potPerEvent << " POT each)";
  }
  os << "\n  output = "
     << (fCfg.output == Output::Jpsi
             ? "Jpsi (inclusive normalisation)"
             : (fCfg.output == Output::Both ? "Both" : "MuMu"))
     << ", rate used = " << fNorm.rate;
  if (fCfg.physicsWeight && !fCfg.injection)
    os << "\n  physics weights: weight = " << fNorm.weight << " per event ("
       << fCfg.potPerEvent
       << " POT each; the POT normalisation is applied in the analysis), "
          "nEvents = "
       << fNEvents;
  else if (fCfg.injection)
    os << "\n  weight = " << fNorm.weight
       << " per injected J/psi (physics weight)";
  else
    os << "\n  nPot = " << fCfg.nPot << ", nEvents = " << fNEvents
       << ", weight = " << fNorm.weight << " (enhancement " << fNorm.enhancement
       << "x)";
  return os.str();
}

std::vector<std::pair<std::string, double>> Sampler::Metadata() const {
  return {
      {"version_major", static_cast<double>(kVersionMajor)},
      {"version_minor", static_cast<double>(kVersionMinor)},
      {"p_beam", fCfg.pBeam},
      {"target_A", fCfg.target.A},
      {"y_shape", static_cast<double>(static_cast<int>(fCfg.yShape))},
      {"tail_n", fCfg.tailN},
      {"data_lo", fCfg.dataLo},
      {"data_hi", fCfg.dataHi},
      {"data_map", fCfg.dataMap.on ? 1.0 : 0.0},
      {"map_y_join", fCfg.dataMap.yJoin},
      {"map_y_hi", fCfg.dataMap.yHi},
      {"map_ptsq_ref", fCfg.dataMap.q0},
      {"map_ptsq_max", fCfg.dataMap.qMax},
      {"map_b1", fCfg.dataMap.b1},
      {"map_b2", fCfg.dataMap.b2},
      {"map_c", fCfg.dataMap.c},
      {"forward_tail", static_cast<double>(static_cast<int>(fCfg.forwardTail))},
      {"map_tail_n", fCfg.dataMap.tailN},
      {"alpha_xf1", fCfg.alphaXf1},
      {"alpha_xf2", fCfg.alphaXf2},
      {"shape_A", fCfg.shapeA},
      {"a_eff", fNorm.aEff},
      {"pt_sq", fCfg.ptSq},
      {"y_gauss_mean", fCfg.yGauss0},
      {"y_gauss_sigma", fCfg.yGaussSigma},
      {"T", fCfg.T},
      {"p0", fCfg.p0},
      {"pt_pow_n", fCfg.nPow},
      {"f_hard", fNorm.fHard},
      {"mean_pt_sq", fNorm.meanPtSq},
      {"pt_nodes_softened", static_cast<double>(fNorm.ptNodesSoftened)},
      {"pt_sq_slope", fCfg.ptSqSlope},
      {"thermal_jacobian", fCfg.thermalJacobian ? 1.0 : 0.0},
      {"lambda_pol", fCfg.lambdaPol},
      {"f_y", fNorm.fY},
      {"f_cos", fNorm.fCos},
      {"chi_mumu", fNorm.chiMuMu},
      {"chi_mumu_primary", fNorm.chiMuMuPrimary},
      {"secondary_factor", fNorm.secondaryFactor},
      {"secondary_depth_cm", fCfg.secondaryDepth_cm},
      {"chi_jpsi", fNorm.chiJpsi},
      {"prob_mumu_per_pot", fNorm.probMuMuPerPot},
      {"per_pot", fNorm.probMuMuPerPot > 0 ? 1.0 : 0.0},
      {"p_interact", fNorm.pInteract},
      {"n_layers", static_cast<double>(fCfg.layers.size())},
      {"target_length_cm", fNorm.targetLength_cm},
      {"z_start_cm", fCfg.zStart_cm},
      {"chi_mumu_fullcos_diagnostic", fNorm.chiMuMuFullCosDiagnostic},
      {"rate_used", fNorm.rate},
      {"n_pot", fCfg.nPot},
      {"n_events", static_cast<double>(fNEvents)},
      {"weight", fNorm.weight},
      {"physics_weight", fCfg.physicsWeight || fCfg.injection ? 1.0 : 0.0},
      {"enhancement", fNorm.enhancement},
      {"output_mode", static_cast<double>(static_cast<int>(fCfg.output))},
      {"injection", fCfg.injection ? 1.0 : 0.0},
      {"mean_per_event", fNorm.meanPerEvent},
      {"pot_per_event", fCfg.potPerEvent},
      {"seed", static_cast<double>(fCfg.seed)},
  };
}

}  // namespace jpsi
