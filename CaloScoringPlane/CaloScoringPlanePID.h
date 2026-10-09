// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#ifndef CALOSCORINGPLANE_CALOSCORINGPLANEPID_H_
#define CALOSCORINGPLANE_CALOSCORINGPLANEPID_H_

#include <map>
#include <string>
#include <vector>

#include "Rtypes.h"

class CaloScoringPlanePoint;

/**
 * @brief Energy-dependent electron / hadron / muon identification from
 * confusion matrices.
 *
 * The model is a list of 3x3 confusion matrices given at increasing
 * energies. M(E)[i][j] is the probability that a particle of true species i
 * is identified as species j; each row sums to 1. For a particle of total
 * energy E the matrix is interpolated element by element between the two
 * neighbouring energy points (linearly in E, or in log E); below the first
 * or above the last point, that point's matrix is used. Interpolating
 * row-stochastic matrices this way keeps every row normalised and
 * non-negative.
 *
 * True species from the PDG code: |pdg| = 11 electron, 13 muon; any meson or
 * baryon (|pdg| < 1e9 with a non-zero quark digit n_q2) is a hadron;
 * anything else (photons, neutrinos, nuclei, BSM codes) is kUnknown and is
 * never identified. The optional "pdg_overrides" map changes this per |pdg|.
 *
 * The configuration is a YAML file, read with yaml-cpp; its format is
 * documented in CaloScoringPlane/README.md, with an example in
 * geometry/caloScoringPlane_pid_provided.yaml. Errors in the file throw
 * std::runtime_error (a Python exception in PyROOT) naming the offending
 * entry and line.
 *
 * Usage from C++ (link against the CaloScoringPlane library):
 * @code
 *   CaloScoringPlanePID
 * pid("$FAIRSHIP/geometry/caloScoringPlane_pid_provided.yaml");
 *   CaloScoringPlanePID::Species s = pid.Identify(point);  // uses gRandom
 * @endcode
 * and from Python:
 * @code
 *   pid = ROOT.CaloScoringPlanePID("caloScoringPlane_pid.yaml")
 *   if pid.Identify(point) == ROOT.CaloScoringPlanePID.kMuon: ...
 * @endcode
 */
class CaloScoringPlanePID {
 public:
  enum Species : Int_t { kUnknown = -1, kElectron = 0, kHadron = 1, kMuon = 2 };
  static constexpr Int_t kNSpecies = 3;

  /** Perfect identification (identity matrix at all energies). */
  CaloScoringPlanePID();
  /** Load from a YAML file; environment variables in the path are expanded. */
  explicit CaloScoringPlanePID(const std::string& yamlFile);

  /** Replace the current model with the one in the file. */
  void Load(const std::string& yamlFile);
  /** Same, from a YAML string (mainly for tests). */
  void LoadFromString(const std::string& yaml);

  /** True species for a PDG code (overrides applied). */
  Species TrueSpecies(Int_t pdg) const;

  /** Interpolated probability P(identified as reco | true species, E). */
  Double_t Probability(Species trueSpecies, Species recoSpecies,
                       Double_t energy) const;
  /** Interpolated 3x3 matrix, row-major (9 values). */
  std::vector<Double_t> Matrix(Double_t energy) const;

  /** Draw the PID outcome with a given uniform number u in [0, 1]. */
  Species Identify(Int_t pdg, Double_t energy, Double_t u) const;
  /** Draw the PID outcome using gRandom. */
  Species Identify(Int_t pdg, Double_t energy) const;
  /** PDG code and total energy taken from the point; uses gRandom. */
  Species Identify(const CaloScoringPlanePoint& point) const;

  /** Total energy (GeV) at the point, using the PDG mass (0 if unknown). */
  static Double_t Energy(const CaloScoringPlanePoint& point);
  static const char* SpeciesName(Int_t species);

  const std::vector<Double_t>& GetEnergies() const { return fEnergies; }
  Bool_t IsLogInterpolation() const { return fLogInterpolation; }
  void Print() const;

 private:
  void SetIdentity();
  void Set(std::vector<Double_t> energies, std::vector<Double_t> matrices,
           std::map<Int_t, Int_t> overrides, Bool_t logInterpolation);
  Double_t At(size_t iEnergy, Int_t i, Int_t j) const {
    return fMatrices[9 * iEnergy + static_cast<size_t>(3 * i + j)];
  }

  std::vector<Double_t> fEnergies;  ///< GeV, strictly increasing
  std::vector<Double_t> fMatrices;  ///< 9 per energy, row-major, internal order
  std::map<Int_t, Int_t> fOverrides;  ///< |pdg| -> Species
  Bool_t fLogInterpolation = kFALSE;
};

#endif  // CALOSCORINGPLANE_CALOSCORINGPLANEPID_H_
