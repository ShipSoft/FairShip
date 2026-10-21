// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#include "CaloScoringPlanePID.h"

#include <algorithm>
#include <cmath>
#include <cstdlib>
#include <map>
#include <sstream>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

#include "CaloScoringPlanePoint.h"
#include "FairLogger.h"
#include "TDatabasePDG.h"
#include "TParticlePDG.h"
#include "TRandom.h"

namespace {

constexpr Double_t kRowSumTolerance = 1e-6;

[[noreturn]] void Invalid(const std::string& what) {
  throw std::invalid_argument("CaloScoringPlanePID::Set: " + what);
}

// PDG Monte Carlo numbering scheme: mesons and baryons have a non-zero quark
// digit n_q2 (hundreds). Codes >= 9900000 are generator-specific or BSM
// (e.g. HNL 9900015), codes >= 1e9 are nuclei.
bool IsHadronCode(Int_t pdg) {
  const Int_t a = std::abs(pdg);
  if (a >= 9900000) return false;
  return (a / 100) % 10 != 0;
}

}  // namespace

CaloScoringPlanePID::CaloScoringPlanePID() { SetIdentity(); }

void CaloScoringPlanePID::SetIdentity() {
  fEnergies = {1.0};
  fMatrices.assign(9, 0.);
  for (Int_t i = 0; i < kNSpecies; ++i) fMatrices[3 * i + i] = 1.;
  fOverrides.clear();
  fLogInterpolation = kFALSE;
}

void CaloScoringPlanePID::Set(const std::vector<Double_t>& energies,
                              const std::vector<Double_t>& matrices,
                              const std::map<Int_t, Int_t>& overrides,
                              Bool_t logInterpolation) {
  // Validate everything before changing the model, so that a rejected model
  // leaves the previous one in place.
  const size_t n = energies.size();
  if (n == 0) Invalid("no energy points");
  if (matrices.size() != 9 * n) {
    Invalid("expected " + std::to_string(9 * n) +
            " matrix values (9 per energy point), got " +
            std::to_string(matrices.size()));
  }
  for (size_t k = 0; k < n; ++k) {
    std::ostringstream where;
    where << "energy point " << k << " (" << energies[k] << " GeV)";
    if (!std::isfinite(energies[k])) Invalid(where.str() + ": not finite");
    if (k > 0 && energies[k] <= energies[k - 1]) {
      Invalid(where.str() + ": energies must be strictly increasing");
    }
    if (logInterpolation && energies[k] <= 0.) {
      Invalid(where.str() + ": log interpolation needs positive energies");
    }
    for (Int_t i = 0; i < kNSpecies; ++i) {
      const std::string row = where.str() + ", true " + SpeciesName(i) + " row";
      double sum = 0.;
      for (Int_t j = 0; j < kNSpecies; ++j) {
        const double x = matrices[9 * k + static_cast<size_t>(3 * i + j)];
        if (!std::isfinite(x)) Invalid(row + ": entry not finite");
        if (x < 0.) Invalid(row + ": negative entry");
        sum += x;
      }
      if (std::fabs(sum - 1.) > kRowSumTolerance) {
        std::ostringstream os;
        os << row << " sums to " << sum << ", expected 1";
        Invalid(os.str());
      }
    }
  }
  std::map<Int_t, Int_t> byAbsPdg;
  for (const auto& [pdg, species] : overrides) {
    if (species < kUnknown || species >= kNSpecies) {
      Invalid("override for PDG code " + std::to_string(pdg) + ": species " +
              std::to_string(species) +
              " is not -1 (unknown), 0 (electron), 1 (hadron) or 2 (muon)");
    }
    const auto [it, inserted] = byAbsPdg.emplace(std::abs(pdg), species);
    if (!inserted && it->second != species) {
      Invalid("conflicting overrides for |PDG code| " +
              std::to_string(std::abs(pdg)));
    }
  }
  fEnergies = energies;
  fMatrices = matrices;
  fOverrides = std::move(byAbsPdg);
  fLogInterpolation = logInterpolation;
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
