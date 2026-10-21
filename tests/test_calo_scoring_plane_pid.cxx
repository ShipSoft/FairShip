// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

// Unit tests for CaloScoringPlanePID (energy-dependent e/h/mu confusion
// matrices). The YAML file format is tested in
// tests/test_caloScoringPlanePID.py.

#include <cmath>
#include <functional>
#include <iostream>
#include <limits>
#include <map>
#include <stdexcept>
#include <string>
#include <vector>

#include "CaloScoringPlanePID.h"
#include "CaloScoringPlanePoint.h"
#include "TRandom3.h"
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

using S = CaloScoringPlanePID;
using Values = std::vector<double>;

const Values kIdentity = {1, 0, 0, 0, 1, 0, 0, 0, 1};
// Electrons identified as hadrons, the other rows diagonal.
const Values kElectronAsHadron = {0, 1, 0, 0, 1, 0, 0, 0, 1};

Values Concat(const Values& a, const Values& b) {
  Values out = a;
  out.insert(out.end(), b.begin(), b.end());
  return out;
}

// Set() must throw std::invalid_argument and keep the previous model.
void expectInvalid(const std::function<void(S&)>& set,
                   const std::string& what) {
  S pid;
  pid.Set({1.}, {0.5, 0.5, 0, 0, 1, 0, 0, 0, 1});
  try {
    set(pid);
  } catch (const std::invalid_argument&) {
    check(close(pid.Probability(S::kElectron, S::kElectron, 1.), 0.5),
          what + ": previous model kept");
    return;
  }
  check(false, "expected std::invalid_argument: " + what);
}

}  // namespace

int main() {
  const double nan = std::numeric_limits<double>::quiet_NaN();
  const double inf = std::numeric_limits<double>::infinity();

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
    pid.Set({10., 20.}, Concat(kIdentity, kElectronAsHadron));
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
    pid.Set({10., 20.}, Concat(kIdentity, kElectronAsHadron), {}, kTRUE);
    check(pid.IsLogInterpolation(), "log interpolation set");
    const double e = std::sqrt(10. * 20.);  // geometric mean -> weight 0.5
    check(close(pid.Probability(S::kElectron, S::kElectron, e), 0.5),
          "log midpoint");
  }

  // --- frequencies ---
  {
    S pid;
    pid.Set({1.}, {0.8, 0.2, 0.0, 0.3, 0.6, 0.1, 0.0, 0.0, 1.0});
    TRandom3 rng(4357);
    const int n = 200000;
    int nE = 0, nMu = 0;
    for (int k = 0; k < n; ++k) {
      const auto s = pid.Identify(211, 3., rng);
      nE += s == S::kElectron;
      nMu += s == S::kMuon;
    }
    check(std::fabs(nE / static_cast<double>(n) - 0.3) < 0.005,
          "pi->e frequency");
    check(std::fabs(nMu / static_cast<double>(n) - 0.1) < 0.005,
          "pi->mu frequency");
  }

  // --- a fixed outcome draws no random number ---
  {
    S perfect;
    TRandom3 used(1), reference(1);
    for (int pdg : {11, -13, 211, 22, 12}) perfect.Identify(pdg, 5., used);
    check(used.Rndm() == reference.Rndm(),
          "perfect PID and unknown species leave the generator untouched");

    S pid;  // electron row (0.5, 0.5, 0) at 15 GeV, (0, 1, 0) from 20 GeV
    pid.Set({10., 20.}, Concat(kIdentity, kElectronAsHadron));
    TRandom3 a(2), b(2);
    check(pid.Identify(11, 50., a) == S::kHadron, "single non-zero entry");
    check(a.Rndm() == b.Rndm(), "single non-zero entry draws nothing");
    pid.Identify(11, 15., a);  // two possible outcomes: one draw
    b.Rndm();
    check(a.Rndm() == b.Rndm(), "a varying outcome draws exactly once");
  }

  // --- overrides ---
  {
    S pid;
    pid.Set({1.}, kIdentity, {{22, S::kElectron}, {-211, S::kUnknown}});
    check(pid.TrueSpecies(22) == S::kElectron, "override photon");
    check(pid.TrueSpecies(211) == S::kUnknown, "override pi to unknown");
    check(pid.TrueSpecies(-211) == S::kUnknown, "override applies to |pdg|");
  }

  // --- energy from a point ---
  {
    CaloScoringPlanePoint p(0, 1, 1, TVector3(0, 0, 0), TVector3(0, 3, 4), 0.,
                            0., 0., 13);
    const double m = 0.1056583755;
    check(std::fabs(S::Energy(p) - std::sqrt(25. + m * m)) < 1e-6,
          "muon energy");
  }

  // --- non-finite energies and out-of-range species ---
  {
    S pid;
    pid.Set({10., 20.}, Concat(kIdentity, kElectronAsHadron));
    TRandom3 used(3), reference(3);
    for (double e : {nan, inf, -inf}) {
      check(pid.Identify(11, e, 0.5) == S::kUnknown, "non-finite energy: u");
      check(pid.Identify(11, e, used) == S::kUnknown,
            "non-finite energy: generator");
    }
    check(used.Rndm() == reference.Rndm(), "non-finite energy draws nothing");
    bool threw = false;
    try {
      pid.Matrix(nan);
    } catch (const std::invalid_argument&) {
      threw = true;
    }
    check(threw, "Matrix(NaN) throws");
    threw = false;
    try {
      pid.Probability(S::kElectron, S::kElectron, nan);
    } catch (const std::invalid_argument&) {
      threw = true;
    }
    check(threw, "Probability(NaN) throws");
    for (int bad : {3, -2}) {
      threw = false;
      try {
        pid.Probability(static_cast<S::Species>(bad), S::kMuon, 1.);
      } catch (const std::out_of_range&) {
        threw = true;
      }
      check(threw, "true species " + std::to_string(bad) + " throws");
      threw = false;
      try {
        pid.Probability(S::kMuon, static_cast<S::Species>(bad), 1.);
      } catch (const std::out_of_range&) {
        threw = true;
      }
      check(threw, "identified species " + std::to_string(bad) + " throws");
    }
    check(pid.Probability(S::kUnknown, S::kUnknown, 1.) == 1.,
          "unknown -> unknown still allowed");
  }

  // --- validation in Set() ---
  expectInvalid([](S& p) { p.Set({}, {}); }, "no energy points");
  expectInvalid([](S& p) { p.Set({1.}, {1, 0, 0}); }, "too few values");
  expectInvalid([](S& p) { p.Set({2., 1.}, Concat(kIdentity, kIdentity)); },
                "decreasing energies");
  expectInvalid([](S& p) { p.Set({1., 1.}, Concat(kIdentity, kIdentity)); },
                "repeated energy");
  expectInvalid([](S& p) { p.Set({1.}, {0.5, 0.4, 0, 0, 1, 0, 0, 0, 1}); },
                "row sum");
  expectInvalid([](S& p) { p.Set({1.}, {1.2, -0.2, 0, 0, 1, 0, 0, 0, 1}); },
                "negative entry");
  expectInvalid([&](S& p) { p.Set({1.}, {nan, 1, 0, 0, 1, 0, 0, 0, 1}); },
                "NaN entry");
  expectInvalid([&](S& p) { p.Set({nan}, kIdentity); }, "NaN energy");
  expectInvalid([&](S& p) { p.Set({1., inf}, Concat(kIdentity, kIdentity)); },
                "infinite energy");
  expectInvalid([](S& p) { p.Set({0.}, kIdentity, {}, kTRUE); },
                "log with zero energy");
  expectInvalid([](S& p) { p.Set({1.}, kIdentity, {{22, 3}}); },
                "override species out of range");
  expectInvalid(
      [](S& p) {
        p.Set({1.}, kIdentity, {{211, S::kHadron}, {-211, S::kMuon}});
      },
      "conflicting overrides");

  if (failures) {
    std::cerr << failures << " check(s) failed" << std::endl;
    return 1;
  }
  std::cout << "CaloScoringPlanePID: all checks passed" << std::endl;
  return 0;
}
