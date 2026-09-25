// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#include "CaloScoringPlanePID.h"

#include <yaml-cpp/yaml.h>

#include <algorithm>
#include <cmath>
#include <cstdlib>
#include <sstream>
#include <stdexcept>
#include <utility>

#include "CaloScoringPlanePoint.h"
#include "FairLogger.h"
#include "TDatabasePDG.h"
#include "TParticlePDG.h"
#include "TRandom.h"
#include "TString.h"
#include "TSystem.h"

namespace {

constexpr Double_t kRowSumTolerance = 1e-6;

/// Parsed and validated configuration, committed only when complete.
struct Model {
  std::vector<Double_t> energies;
  std::vector<Double_t> matrices;  // 9 per energy, internal species order
  std::map<Int_t, Int_t> overrides;
  bool logInterpolation = false;
};

[[noreturn]] void Fail(const YAML::Node& node, const std::string& what) {
  std::ostringstream os;
  os << "CaloScoringPlanePID: " << what;
  if (!node.Mark().is_null()) os << " (line " << node.Mark().line + 1 << ")";
  throw std::runtime_error(os.str());
}

double ToDouble(const YAML::Node& node, const std::string& where) {
  try {
    return node.as<double>();
  } catch (const YAML::Exception&) {
    Fail(node, where + " must be a number");
  }
}

Int_t SpeciesFromName(const YAML::Node& node) {
  const std::string name = node.as<std::string>();
  if (name == "electron") return CaloScoringPlanePID::kElectron;
  if (name == "hadron") return CaloScoringPlanePID::kHadron;
  if (name == "muon") return CaloScoringPlanePID::kMuon;
  if (name == "none") return CaloScoringPlanePID::kUnknown;
  Fail(node,
       "unknown species '" + name + "' (use electron, hadron, muon or none)");
}

// PDG Monte Carlo numbering scheme: mesons and baryons have a non-zero quark
// digit n_q2 (hundreds). Codes >= 9900000 are generator-specific or BSM
// (e.g. HNL 9900015), codes >= 1e9 are nuclei.
bool IsHadronCode(Int_t pdg) {
  const Int_t a = std::abs(pdg);
  if (a >= 9900000) return false;
  return (a / 100) % 10 != 0;
}

Model Parse(const YAML::Node& root) {
  if (!root.IsMap()) Fail(root, "top level must be a mapping");
  for (const auto& kv : root) {
    const auto key = kv.first.as<std::string>();
    if (key != "species" && key != "interpolation" && key != "points" &&
        key != "pdg_overrides") {
      Fail(kv.first, "unknown key '" + key + "'");
    }
  }
  Model m;

  // Order of rows/columns in the file -> internal species index.
  std::vector<Int_t> order = {CaloScoringPlanePID::kElectron,
                              CaloScoringPlanePID::kHadron,
                              CaloScoringPlanePID::kMuon};
  if (const YAML::Node species = root["species"]) {
    if (!species.IsSequence() || species.size() != 3) {
      Fail(species, "'species' must list electron, hadron and muon");
    }
    for (size_t i = 0; i < 3; ++i) order[i] = SpeciesFromName(species[i]);
    std::vector<Int_t> sorted = order;
    std::sort(sorted.begin(), sorted.end());
    if (sorted != std::vector<Int_t>{CaloScoringPlanePID::kElectron,
                                     CaloScoringPlanePID::kHadron,
                                     CaloScoringPlanePID::kMuon}) {
      Fail(species,
           "'species' must be a permutation of electron, hadron, "
           "muon");
    }
  }

  if (const YAML::Node interp = root["interpolation"]) {
    const auto mode = interp.as<std::string>();
    if (mode != "linear" && mode != "log") {
      Fail(interp, "'interpolation' must be linear or log");
    }
    m.logInterpolation = mode == "log";
  }

  const YAML::Node points = root["points"];
  if (!points || !points.IsSequence() || points.size() == 0) {
    Fail(root, "'points' must be a non-empty list of {energy, matrix}");
  }
  for (size_t k = 0; k < points.size(); ++k) {
    const YAML::Node point = points[k];
    const std::string where = "points[" + std::to_string(k) + "]";
    if (!point.IsMap() || !point["energy"] || !point["matrix"]) {
      Fail(point, where + " must have 'energy' and 'matrix'");
    }
    const double e = ToDouble(point["energy"], where + ".energy");
    if (!m.energies.empty() && e <= m.energies.back()) {
      Fail(point, "energies must be strictly increasing");
    }
    if (m.logInterpolation && e <= 0.) {
      Fail(point, "log interpolation needs positive energies");
    }
    m.energies.push_back(e);

    const YAML::Node matrix = point["matrix"];
    if (!matrix.IsSequence() || matrix.size() != 3) {
      Fail(matrix, where + ".matrix must have 3 rows");
    }
    const size_t base = m.matrices.size();
    m.matrices.resize(base + 9, 0.);
    for (size_t i = 0; i < 3; ++i) {
      const YAML::Node row = matrix[i];
      const std::string rwhere = where + ".matrix[" + std::to_string(i) + "]";
      if (!row.IsSequence() || row.size() != 3) {
        Fail(row, rwhere + " must have 3 entries");
      }
      double sum = 0.;
      for (size_t j = 0; j < 3; ++j) {
        const double x = ToDouble(row[j], rwhere);
        if (x < 0.) Fail(row, rwhere + " has a negative entry");
        sum += x;
        m.matrices[base + static_cast<size_t>(3 * order[i] + order[j])] = x;
      }
      if (std::fabs(sum - 1.) > kRowSumTolerance) {
        std::ostringstream os;
        os << rwhere << " sums to " << sum << ", expected 1";
        Fail(row, os.str());
      }
    }
  }

  if (const YAML::Node overrides = root["pdg_overrides"];
      overrides && !overrides.IsNull()) {  // empty key = no overrides
    if (!overrides.IsMap()) {
      Fail(overrides, "'pdg_overrides' must map PDG codes to species");
    }
    for (const auto& kv : overrides) {
      Int_t pdg = 0;
      try {
        pdg = kv.first.as<Int_t>();
      } catch (const YAML::Exception&) {
        Fail(kv.first, "'pdg_overrides' keys must be PDG codes");
      }
      m.overrides[std::abs(pdg)] = SpeciesFromName(kv.second);
    }
  }
  return m;
}

}  // namespace

CaloScoringPlanePID::CaloScoringPlanePID() { SetIdentity(); }

CaloScoringPlanePID::CaloScoringPlanePID(const std::string& yamlFile) {
  Load(yamlFile);
}

void CaloScoringPlanePID::SetIdentity() {
  fEnergies = {1.0};
  fMatrices.assign(9, 0.);
  for (Int_t i = 0; i < kNSpecies; ++i) fMatrices[3 * i + i] = 1.;
  fOverrides.clear();
  fLogInterpolation = kFALSE;
}

void CaloScoringPlanePID::Set(std::vector<Double_t> energies,
                              std::vector<Double_t> matrices,
                              std::map<Int_t, Int_t> overrides,
                              Bool_t logInterpolation) {
  fEnergies = std::move(energies);
  fMatrices = std::move(matrices);
  fOverrides = std::move(overrides);
  fLogInterpolation = logInterpolation;
}

void CaloScoringPlanePID::Load(const std::string& yamlFile) {
  TString path(yamlFile.c_str());
  gSystem->ExpandPathName(path);
  Model m;
  try {
    m = Parse(YAML::LoadFile(path.Data()));
  } catch (const YAML::BadFile&) {
    throw std::runtime_error("CaloScoringPlanePID: cannot open '" +
                             std::string(path.Data()) + "'");
  } catch (const std::exception& e) {  // YAML::Exception or our own
    throw std::runtime_error(std::string(e.what()) + " [" + path.Data() + "]");
  }
  Set(std::move(m.energies), std::move(m.matrices), std::move(m.overrides),
      m.logInterpolation);
  LOG(info) << "CaloScoringPlanePID: " << fEnergies.size()
            << " energy point(s) from " << path.Data();
}

void CaloScoringPlanePID::LoadFromString(const std::string& yaml) {
  Model m;
  try {
    m = Parse(YAML::Load(yaml));
  } catch (const YAML::Exception& e) {
    throw std::runtime_error(std::string("CaloScoringPlanePID: ") + e.what());
  }
  Set(std::move(m.energies), std::move(m.matrices), std::move(m.overrides),
      m.logInterpolation);
}

CaloScoringPlanePID::Species CaloScoringPlanePID::TrueSpecies(Int_t pdg) const {
  const Int_t a = std::abs(pdg);
  if (auto it = fOverrides.find(a); it != fOverrides.end()) {
    return static_cast<Species>(it->second);
  }
  if (a == 11) return kElectron;
  if (a == 13) return kMuon;
  if (IsHadronCode(a)) return kHadron;
  return kUnknown;
}

std::vector<Double_t> CaloScoringPlanePID::Matrix(Double_t energy) const {
  std::vector<Double_t> m(9);
  const size_t n = fEnergies.size();
  if (n == 1 || energy <= fEnergies.front()) {
    std::copy_n(fMatrices.begin(), 9, m.begin());
    return m;
  }
  if (energy >= fEnergies.back()) {
    std::copy_n(fMatrices.begin() + 9 * (n - 1), 9, m.begin());
    return m;
  }
  const auto hi = static_cast<size_t>(
      std::upper_bound(fEnergies.begin(), fEnergies.end(), energy) -
      fEnergies.begin());
  const size_t lo = hi - 1;
  const double w =
      fLogInterpolation
          ? std::log(energy / fEnergies[lo]) /
                std::log(fEnergies[hi] / fEnergies[lo])
          : (energy - fEnergies[lo]) / (fEnergies[hi] - fEnergies[lo]);
  for (Int_t i = 0; i < kNSpecies; ++i) {
    for (Int_t j = 0; j < kNSpecies; ++j) {
      m[3 * i + j] = (1. - w) * At(lo, i, j) + w * At(hi, i, j);
    }
  }
  return m;
}

Double_t CaloScoringPlanePID::Probability(Species trueSpecies,
                                          Species recoSpecies,
                                          Double_t energy) const {
  if (trueSpecies == kUnknown) return recoSpecies == kUnknown ? 1. : 0.;
  if (recoSpecies == kUnknown) return 0.;
  return Matrix(energy)[3 * trueSpecies + recoSpecies];
}

CaloScoringPlanePID::Species CaloScoringPlanePID::Identify(Int_t pdg,
                                                           Double_t energy,
                                                           Double_t u) const {
  const Species s = TrueSpecies(pdg);
  if (s == kUnknown) return kUnknown;
  const std::vector<Double_t> m = Matrix(energy);
  double cumulative = 0.;
  Int_t last = s;
  for (Int_t j = 0; j < kNSpecies; ++j) {
    const double p = m[3 * s + j];
    if (p <= 0.) continue;
    last = j;
    cumulative += p;
    if (u < cumulative) return static_cast<Species>(j);
  }
  // u at (or, through rounding, above) the row total: last non-empty outcome.
  return static_cast<Species>(last);
}

CaloScoringPlanePID::Species CaloScoringPlanePID::Identify(
    Int_t pdg, Double_t energy) const {
  return Identify(pdg, energy, gRandom->Rndm());
}

CaloScoringPlanePID::Species CaloScoringPlanePID::Identify(
    const CaloScoringPlanePoint& point) const {
  return Identify(point.PdgCode(), Energy(point));
}

Double_t CaloScoringPlanePID::Energy(const CaloScoringPlanePoint& point) {
  const double p2 = point.GetPx() * point.GetPx() +
                    point.GetPy() * point.GetPy() +
                    point.GetPz() * point.GetPz();
  double mass = 0.;
  if (const TParticlePDG* particle =
          TDatabasePDG::Instance()->GetParticle(point.PdgCode())) {
    mass = particle->Mass();
  }
  return std::sqrt(p2 + mass * mass);
}

const char* CaloScoringPlanePID::SpeciesName(Int_t species) {
  switch (species) {
    case kElectron:
      return "electron";
    case kHadron:
      return "hadron";
    case kMuon:
      return "muon";
    default:
      return "unknown";
  }
}

void CaloScoringPlanePID::Print() const {
  LOG(info) << "CaloScoringPlanePID: " << fEnergies.size()
            << " energy point(s), " << (fLogInterpolation ? "log" : "linear")
            << " interpolation; rows = true, columns = identified "
               "(electron, hadron, muon)";
  for (size_t k = 0; k < fEnergies.size(); ++k) {
    for (Int_t i = 0; i < kNSpecies; ++i) {
      LOG(info) << "  E = " << fEnergies[k] << " GeV  " << SpeciesName(i)
                << ": " << At(k, i, 0) << " " << At(k, i, 1) << " "
                << At(k, i, 2);
    }
  }
  for (const auto& [pdg, s] : fOverrides) {
    LOG(info) << "  override |pdg| " << pdg << " -> " << SpeciesName(s);
  }
}
