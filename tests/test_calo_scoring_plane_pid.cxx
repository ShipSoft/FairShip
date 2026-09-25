// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

// Unit tests for CaloScoringPlanePID (energy-dependent e/h/mu confusion
// matrices read from YAML).

#include <cmath>
#include <functional>
#include <iostream>
#include <stdexcept>
#include <string>

#include "CaloScoringPlanePID.h"
#include "CaloScoringPlanePoint.h"
#include "TRandom.h"
#include "TVector3.h"

namespace {

int failures = 0;

void check(bool ok, const std::string& what) {
  if (!ok) {
    std::cerr << "FAIL: " << what << std::endl;
    ++failures;
  }
}

bool close(double a, double b, double tol = 1e-9) {
  return std::fabs(a - b) < tol;
}

void expectThrow(const std::string& yaml, const std::string& what) {
  CaloScoringPlanePID pid;
  try {
    pid.LoadFromString(yaml);
  } catch (const std::runtime_error&) {
    return;
  }
  check(false, "expected exception: " + what);
}

using S = CaloScoringPlanePID;

// Two energy points; electron row changes with energy, others constant.
const char* kTwoPoints = R"(
species: [electron, hadron, muon]
points:
  - energy: 10
    matrix: [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
  - energy: 20
    matrix: [[0, 1, 0], [0, 1, 0], [0, 0, 1]]
)";

std::string OnePoint(const std::string& matrix, const std::string& extra = "") {
  return extra + "\npoints:\n  - energy: 1\n    matrix: " + matrix + "\n";
}

}  // namespace

int main() {
  // --- default: perfect PID ---
  {
    S pid;
    check(pid.Identify(11, 5., 0.5) == S::kElectron, "identity e");
    check(pid.Identify(-13, 5., 0.5) == S::kMuon, "identity mu");
    check(pid.Identify(211, 5., 0.99) == S::kHadron, "identity pi");
    check(pid.Identify(22, 5., 0.5) == S::kUnknown, "photon unknown");
  }

  // --- true species from PDG codes ---
  {
    S pid;
    check(pid.TrueSpecies(-11) == S::kElectron, "e+");
    check(pid.TrueSpecies(13) == S::kMuon, "mu-");
    for (int h : {211, -211, 321, 130, 310, 2212, -2212, 2112, 3122, 111}) {
      check(pid.TrueSpecies(h) == S::kHadron, "hadron " + std::to_string(h));
    }
    for (int u : {22, 12, -14, 16, 1000010020, 9900015, 0}) {
      check(pid.TrueSpecies(u) == S::kUnknown, "unknown " + std::to_string(u));
    }
  }

  // --- linear interpolation and clamping ---
  {
    S pid;
    pid.LoadFromString(kTwoPoints);
    check(close(pid.Probability(S::kElectron, S::kElectron, 15.), 0.5),
          "linear midpoint");
    check(close(pid.Probability(S::kElectron, S::kHadron, 12.5), 0.25),
          "linear quarter");
    check(close(pid.Probability(S::kElectron, S::kElectron, 1.), 1.0),
          "clamp low");
    check(close(pid.Probability(S::kElectron, S::kElectron, 1e4), 0.0),
          "clamp high");
    auto m = pid.Matrix(15.);
    for (size_t i = 0; i < 3; ++i) {
      check(close(m[3 * i] + m[3 * i + 1] + m[3 * i + 2], 1.),
            "interpolated row sums to 1");
    }
    // deterministic draws at E = 15: electron row = (0.5, 0.5, 0)
    check(pid.Identify(11, 15., 0.49) == S::kElectron, "draw below 0.5");
    check(pid.Identify(11, 15., 0.51) == S::kHadron, "draw above 0.5");
    check(pid.Identify(11, 15., 1.0) == S::kHadron, "u == 1");
    check(pid.Identify(13, 15., 1.0) == S::kMuon, "u == 1, diagonal row");
  }

  // --- log interpolation ---
  {
    S pid;
    pid.LoadFromString(std::string("interpolation: log\n") + kTwoPoints);
    const double e = std::sqrt(10. * 20.);  // geometric mean -> weight 0.5
    check(close(pid.Probability(S::kElectron, S::kElectron, e), 0.5),
          "log midpoint");
  }

  // --- rows/columns given in a different order ---
  {
    S pid;
    pid.LoadFromString(OnePoint("[[0.7, 0.0, 0.3], [0, 1, 0], [0, 0, 1]]",
                                "species: [muon, electron, hadron]"));
    check(close(pid.Probability(S::kMuon, S::kMuon, 1.), 0.7), "reorder mm");
    check(close(pid.Probability(S::kMuon, S::kHadron, 1.), 0.3), "reorder mh");
    check(close(pid.Probability(S::kElectron, S::kElectron, 1.), 1.),
          "reorder ee");
  }

  // --- frequencies ---
  {
    S pid;
    pid.LoadFromString(
        OnePoint("[[0.8, 0.2, 0.0], [0.3, 0.6, 0.1], [0.0, 0.0, 1.0]]"));
    gRandom->SetSeed(4357);
    const int n = 200000;
    int nE = 0, nMu = 0;
    for (int k = 0; k < n; ++k) {
      const auto s = pid.Identify(211, 3.);
      nE += s == S::kElectron;
      nMu += s == S::kMuon;
    }
    check(std::fabs(nE / static_cast<double>(n) - 0.3) < 0.005,
          "pi->e frequency");
    check(std::fabs(nMu / static_cast<double>(n) - 0.1) < 0.005,
          "pi->mu frequency");
  }

  // --- overrides ---
  {
    S pid;
    pid.LoadFromString(OnePoint("[[1, 0, 0], [0, 1, 0], [0, 0, 1]]",
                                "pdg_overrides: {22: electron, -211: none}"));
    check(pid.TrueSpecies(22) == S::kElectron, "override photon");
    check(pid.TrueSpecies(211) == S::kUnknown, "override pi to none");
  }

  // --- empty pdg_overrides (all entries commented out) ---
  {
    S pid;
    pid.LoadFromString(
        OnePoint("[[1, 0, 0], [0, 1, 0], [0, 0, 1]]", "pdg_overrides:"));
    check(pid.TrueSpecies(22) == S::kUnknown, "empty pdg_overrides accepted");
  }

  // --- energy from a point ---
  {
    CaloScoringPlanePoint p(0, 1, 1, TVector3(0, 0, 0), TVector3(0, 3, 4), 0.,
                            0., 0., 13);
    const double m = 0.1056583755;
    check(std::fabs(S::Energy(p) - std::sqrt(25. + m * m)) < 1e-6,
          "muon energy");
  }

  // --- validation ---
  const std::string id = "[[1, 0, 0], [0, 1, 0], [0, 0, 1]]";
  expectThrow("points: [", "malformed YAML");
  expectThrow("points: []", "no points");
  expectThrow(R"(points:
  - energy: 2
    matrix: [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
  - energy: 1
    matrix: [[1, 0, 0], [0, 1, 0], [0, 0, 1]])",
              "decreasing energies");
  expectThrow(OnePoint("[[0.5, 0.4, 0], [0, 1, 0], [0, 0, 1]]"), "row sum");
  expectThrow(OnePoint("[[1, 0], [0, 1], [0, 0]]"), "not 3x3");
  expectThrow(OnePoint("[[1.2, -0.2, 0], [0, 1, 0], [0, 0, 1]]"), "negative");
  expectThrow(OnePoint("[[a, 0, 0], [0, 1, 0], [0, 0, 1]]"), "not a number");
  expectThrow(OnePoint(id, "energies: [1]"), "unknown key");
  expectThrow(OnePoint(id, "species: [electron, electron, muon]"),
              "species not a permutation");
  expectThrow(OnePoint(id, "species: [electron, pion, muon]"),
              "unknown species");
  expectThrow(OnePoint(id, "interpolation: spline"), "bad interpolation");
  expectThrow(R"(interpolation: log
points:
  - energy: 0
    matrix: [[1, 0, 0], [0, 1, 0], [0, 0, 1]])",
              "log with zero energy");
  {
    CaloScoringPlanePID pid;
    bool threw = false;
    try {
      pid.Load("does/not/exist.yaml");
    } catch (const std::runtime_error&) {
      threw = true;
    }
    check(threw, "missing file throws");
    check(pid.Identify(13, 5., 0.5) == S::kMuon,
          "failed load leaves model unchanged");
  }

  // --- the example file shipped with FairShip ---
  {
    S pid;
    try {
      pid.Load("geometry/caloScoringPlane_pid_provided.yaml");
      check(!pid.GetEnergies().empty(), "shipped PID file loads");
    } catch (const std::exception& e) {
      check(false, std::string("example file: ") + e.what());
    }
  }

  if (failures) {
    std::cerr << failures << " check(s) failed" << std::endl;
    return 1;
  }
  std::cout << "CaloScoringPlanePID: all checks passed" << std::endl;
  return 0;
}
