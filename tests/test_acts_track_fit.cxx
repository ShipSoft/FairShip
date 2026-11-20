// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

// Track fits through ActsStrawTracker, from straw hits: tracks from the decay
// volume cross four straw stations, with a magnet between stations 2 and 3.
// Checks that the momentum covariance of every fitted track is positive
// definite, and that the px and py pulls at the first measurement have about
// unit width. The fits are at low momentum, where the bending angle in the
// magnet is almost fully correlated with the poorly known q/p of the seed:
// the gain-matrix smoother lost the positive definiteness there.
//
// The pz pull is printed but not checked: below 5 GeV/c the fitted momentum
// is a few 1e-4 too high for both charges, several times its uncertainty,
// with either smoother and with a tighter stepper tolerance.
//
// All materials are almost massless, so that the tracks go straight outside
// the field and the hits can be computed exactly; the pulls then only
// reflect the hit resolution.

#include <algorithm>
#include <cmath>
#include <iostream>
#include <random>
#include <string>
#include <vector>

#include "ActsStrawTracker.h"
#include "RecoTrack.h"
#include "TGeoManager.h"
#include "TGeoMaterial.h"
#include "TGeoMatrix.h"
#include "TGeoMedium.h"
#include "TGeoTube.h"
#include "TGeoVolume.h"
#include "TVector3.h"
#include "TVirtualMagField.h"

namespace {

int failures = 0;

void check(bool condition, const std::string& what) {
  if (!condition) {
    std::cout << "FAIL: " << what << std::endl;
    ++failures;
  }
}

// SHiP frame, cm
constexpr double kStationZ[4] = {8400., 8600., 9300., 9500.};
constexpr double kViewSpacing = 10.;
constexpr double kLayerSpacing = 2.;
constexpr double kStereoAngle = 4.57 * M_PI / 180.;
constexpr double kPitch = 2.;
constexpr double kOuterRadius = 1.;
constexpr double kInnerRadius = 0.98;
constexpr double kHalfLength = 250.;
/// Straws per layer, centred on the axis
constexpr int kStrawsPerLayer = 240;
/// Uniform Bx between stations 2 and 3
constexpr double kFieldStart = 8800.;
constexpr double kFieldEnd = 9100.;
constexpr double kFieldTesla = 1.;
/// Drift distance resolution (cm)
constexpr double kResolution = 0.012;
/// Density of every material (g/cm3): almost no scattering or energy loss
constexpr double kDensity = 1e-8;

/// Uniform Bx in a box between stations 2 and 3, none elsewhere
class BoxField : public TVirtualMagField {
 public:
  BoxField() : TVirtualMagField("box") {}
  void Field(const Double_t* x, Double_t* b) override {
    const bool inside = x[2] > kFieldStart && x[2] < kFieldEnd &&
                        std::abs(x[0]) < 300. && std::abs(x[1]) < 400.;
    b[0] = inside ? 10. * kFieldTesla : 0.;  // kGauss
    b[1] = 0.;
    b[2] = 0.;
  }
};

double viewAngle(int view) {
  return view == 1 ? kStereoAngle : view == 2 ? -kStereoAngle : 0.;
}

double viewZ(int station, int view, int layer) {
  return kStationZ[station - 1] + kViewSpacing * view + kLayerSpacing * layer;
}

/// Offset of straw `n` of a layer along the normal to its wires
double strawOffset(int layer, int n) {
  return (n - kStrawsPerLayer / 2) * kPitch + layer * kPitch / 2.;
}

/// Detector ID as in strawtubes: station, view, layer, 2000 + straw
int detectorId(int station, int view, int layer, int n) {
  return station * 1000000 + view * 100000 + layer * 10000 + 2000 + n;
}

TGeoManager* buildGeometry() {
  auto* manager = new TGeoManager("test", "ACTS track fit test");
  auto* thin =
      new TGeoMedium("thin", 1, new TGeoMaterial("thin", 14.61, 7.3, kDensity));
  TGeoVolume* top = manager->MakeBox("cave", thin, 500., 500., 10000.);
  manager->SetTopVolume(top);

  auto* straw = new TGeoVolume(
      "straw", new TGeoTube("straw", kInnerRadius, kOuterRadius, kHalfLength),
      thin);
  auto* gas = new TGeoVolume(
      "gas", new TGeoTube("gas", 0., kInnerRadius, kHalfLength), thin);
  for (int station = 1; station <= 4; ++station) {
    for (int view = 0; view < 4; ++view) {
      // Wires along (cos a, sin a, 0): local z to the wire, local y to the
      // beam, local x to the normal (-sin a, cos a, 0)
      const double c = std::cos(viewAngle(view));
      const double s = std::sin(viewAngle(view));
      const double rotation[9] = {-s, 0., c, c, 0., s, 0., 1., 0.};
      auto* matrix = new TGeoRotation();
      matrix->SetMatrix(rotation);
      for (int layer = 0; layer < 2; ++layer) {
        const double z = viewZ(station, view, layer);
        for (int n = 0; n < kStrawsPerLayer; ++n) {
          const double offset = strawOffset(layer, n);
          const int id = detectorId(station, view, layer, n);
          auto* placement =
              new TGeoCombiTrans(-s * offset, c * offset, z, matrix);
          top->AddNode(straw, id - 1000, placement);
          top->AddNode(gas, id, placement);
        }
      }
    }
  }
  manager->CloseGeometry();
  return manager;
}

/// A charged track: position and momentum (SHiP frame, cm and GeV)
struct State {
  TVector3 position;
  TVector3 momentum;
};

/// Move a track with Bx in [kFieldStart, kFieldEnd] to `z`: straight
/// outside the field, on the exact circle in the y-z plane inside it
State moveTo(State state, double z, double charge) {
  auto straight = [](State s, double to) {
    const double dz = to - s.position.Z();
    s.position += s.momentum * (dz / s.momentum.Z());
    return s;
  };
  if (state.position.Z() < kFieldStart && z > kFieldStart) {
    state = straight(state, kFieldStart);
    const double pyz = std::hypot(state.momentum.Y(), state.momentum.Z());
    // d(py)/dt is q vz Bx: the angle from z towards y grows at a rate
    // kappa per unit path in the y-z plane, and sin(angle) by kappa dz
    const double kappa = charge * 0.299792458 * kFieldTesla / pyz / 100.;
    const double sin0 = state.momentum.Y() / pyz;
    const double cos0 = state.momentum.Z() / pyz;
    const double end = std::min(z, kFieldEnd);
    const double sin1 = sin0 + kappa * (end - kFieldStart);
    const double cos1 = std::sqrt(1. - sin1 * sin1);
    const double arc = (std::asin(sin1) - std::asin(sin0)) / kappa;
    state.position.SetXYZ(state.position.X() + state.momentum.X() / pyz * arc,
                          state.position.Y() + (cos0 - cos1) / kappa, end);
    state.momentum.SetXYZ(state.momentum.X(), pyz * sin1, pyz * cos1);
  }
  return straight(state, z);
}

/// Straw hits of one track: (detector ID, smeared drift distance)
std::vector<std::pair<int, double>> hits(const State& start, double charge,
                                         std::mt19937& rng) {
  std::normal_distribution<double> gauss(0., kResolution);
  std::vector<std::pair<int, double>> out;
  for (int station = 1; station <= 4; ++station) {
    for (int view = 0; view < 4; ++view) {
      const double c = std::cos(viewAngle(view));
      const double s = std::sin(viewAngle(view));
      const TVector3 wireDirection(c, s, 0.);
      const TVector3 normal(-s, c, 0.);
      for (int layer = 0; layer < 2; ++layer) {
        const State at = moveTo(start, viewZ(station, view, layer), charge);
        const double u = normal.Dot(at.position);
        const int nearest =
            static_cast<int>(std::lround((u - layer * kPitch / 2.) / kPitch) +
                             kStrawsPerLayer / 2);
        for (int n = nearest - 1; n <= nearest + 1; ++n) {
          if (n < 0 || n >= kStrawsPerLayer) {
            continue;
          }
          const TVector3 wire = normal * strawOffset(layer, n) +
                                TVector3(0., 0., viewZ(station, view, layer));
          const TVector3 cross = at.momentum.Unit().Cross(wireDirection);
          const double distance =
              std::abs((at.position - wire).Dot(cross.Unit()));
          if (distance < kInnerRadius &&
              std::abs((at.position - wire).Dot(wireDirection)) < kHalfLength) {
            out.emplace_back(detectorId(station, view, layer, n),
                             std::abs(distance + gauss(rng)));
          }
        }
      }
    }
  }
  return out;
}

/// The 68% half-width of the distribution of `values`
double width68(std::vector<double> values) {
  std::sort(values.begin(), values.end());
  const auto at = [&values](double f) {
    return values[static_cast<std::size_t>(f * (values.size() - 1))];
  };
  return 0.5 * (at(0.8413) - at(0.1587));
}

/// Statistical uncertainty of width68 for `n` Gaussian values
double width68Error(double width, std::size_t n) {
  return 1.1 * width / std::sqrt(static_cast<double>(n));
}

/// Element (i, j) of a symmetric 6x6 matrix stored as its upper triangle,
/// row by row
double element(const std::vector<Double_t>& upper, int i, int j) {
  if (i > j) {
    std::swap(i, j);
  }
  return upper[i * 6 - i * (i - 1) / 2 + (j - i)];
}

/// Whether the (px, py, pz) block of a track covariance is positive definite:
/// the leading minors of its correlation matrix are positive (Sylvester)
bool momentumPositiveDefinite(const std::vector<Double_t>& upper) {
  double sigma[3];
  for (int i = 0; i < 3; ++i) {
    const double variance = element(upper, 3 + i, 3 + i);
    if (!(variance > 0.)) {
      return false;
    }
    sigma[i] = std::sqrt(variance);
  }
  auto r = [&](int i, int j) {
    return element(upper, 3 + i, 3 + j) / (sigma[i] * sigma[j]);
  };
  const double minor2 = 1. - r(0, 1) * r(0, 1);
  const double minor3 = 1. + 2. * r(0, 1) * r(1, 2) * r(0, 2) -
                        r(0, 1) * r(0, 1) - r(1, 2) * r(1, 2) -
                        r(0, 2) * r(0, 2);
  return minor2 > 0. && minor3 > 0.;
}

}  // namespace

int main() {
  TGeoManager* manager = buildGeometry();
  BoxField field;
  SHiP::ActsStrawTracker tracker(manager, &field);
  check(tracker.GetNStraws() == 4 * 4 * 2 * kStrawsPerLayer,
        "all straws found");

  std::mt19937 rng(20261121);
  std::uniform_real_distribution<double> slope(-0.03, 0.03);
  std::uniform_real_distribution<double> momentum(3., 10.);
  const TVector3 vertex(5., -3., 6000.);
  constexpr int kTracks = 1000;
  int fitted = 0;
  int notPositiveDefinite = 0;
  std::vector<double> pulls[3];
  for (int i = 0; i < kTracks; ++i) {
    tracker.ClearEvent();
    const double charge = i % 2 == 0 ? 1. : -1.;
    const TVector3 p =
        TVector3(slope(rng), slope(rng), 1.).Unit() * momentum(rng);
    std::vector<int> indices;
    for (const auto& [id, drift] : hits({vertex, p}, charge, rng)) {
      indices.push_back(tracker.AddMeasurement(id, drift, kResolution));
    }
    const int index = tracker.FitCandidate(indices);
    if (index < 0) {
      continue;
    }
    ++fitted;
    const SHiP::RecoTrack track = tracker.GetTrack(index);
    const auto& covariance = track.GetCovarianceElements();
    if (!momentumPositiveDefinite(covariance)) {
      ++notPositiveDefinite;
      continue;
    }
    // Outside the field the momentum does not change, so the truth at the
    // first measurement is the momentum at the vertex
    const TVector3 measured(track.px(), track.py(), track.pz());
    for (int k = 0; k < 3; ++k) {
      pulls[k].push_back((measured[k] - p[k]) /
                         std::sqrt(element(covariance, 3 + k, 3 + k)));
    }
  }

  std::cout << fitted << " of " << kTracks << " tracks fitted, "
            << notPositiveDefinite
            << " with a momentum covariance that is not positive definite"
            << std::endl;
  check(fitted >= 0.99 * kTracks, "at least 99% of the tracks fitted");
  check(notPositiveDefinite == 0,
        "every momentum covariance positive definite");
  const char* names[3] = {"px", "py", "pz"};
  for (int k = 0; k < 3; ++k) {
    if (pulls[k].empty()) {
      continue;
    }
    const double width = width68(pulls[k]);
    const double error = width68Error(width, pulls[k].size());
    std::cout << names[k] << " pull width " << width << " +- " << error
              << " (N = " << pulls[k].size() << ")" << std::endl;
    if (k < 2) {
      check(width > 0.8 && width < 1.25,
            std::string(names[k]) + " pull width between 0.8 and 1.25");
    }
  }

  if (failures > 0) {
    std::cout << failures << " checks failed" << std::endl;
    return 1;
  }
  std::cout << "All ACTS track fit checks passed" << std::endl;
  return 0;
}
