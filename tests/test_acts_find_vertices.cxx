// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

// Vertex finding through ActsStrawTracker, from straw hits: tracks from known
// vertices in the decay volume cross four straw stations, with a magnet
// between stations 2 and 3, and are fitted and passed to FindVertices. This
// checks what the tests of ActsVertexFinder alone do not: the rotation of
// the vertices back to the SHiP frame and the units of their positions,
// uncertainties, DOCA and momenta.
//
// All materials are almost massless, so that the tracks go straight outside
// the field and the hits can be computed exactly; the pulls then only
// reflect the hit resolution.

#include <algorithm>
#include <array>
#include <cmath>
#include <iostream>
#include <random>
#include <string>
#include <vector>

#include "ActsStrawTracker.h"
#include "RecoVertex.h"
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
  auto* manager = new TGeoManager("test", "ACTS vertex finding test");
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

struct Truth {
  TVector3 vertex;
  std::vector<TVector3> momenta;
};

/// Residuals and pulls collected over events of one kind
struct Tally {
  std::string name;
  int events = 0;
  int oneVertex = 0;
  int allTracksAssigned = 0;
  std::vector<double> pull[3];
  std::vector<double> residual[3];
  std::vector<double> error[3];
  std::vector<double> momentumPull[3];
  /// Momenta at the vertex with a variance that is not positive, per axis
  int nonPositive[3] = {0, 0, 0};
  std::vector<double> momentumResidual;
  std::vector<double> doca;

  void report() const {
    std::cout << name << ": " << oneVertex << "/" << events
              << " events with one vertex, " << allTracksAssigned
              << " with all tracks assigned to it" << std::endl;
    check(oneVertex >= 0.95 * events, name + ": one vertex in 95% of events");
    check(allTracksAssigned >= 0.95 * events,
          name + ": all tracks assigned in 95% of events");
    const char* axes[3] = {"x", "y", "z"};
    for (int i = 0; i < 3; ++i) {
      const double w = width68(pull[i]);
      const double e = width68Error(w, pull[i].size());
      const double r = width68(residual[i]);
      std::vector<double> sorted = error[i];
      std::sort(sorted.begin(), sorted.end());
      const double median = sorted[sorted.size() / 2];
      std::cout << "  vertex " << axes[i] << ": residual width " << r
                << " cm, median error " << median << " cm, pull width " << w
                << " +- " << e << " (N = " << pull[i].size() << ")"
                << std::endl;
      check(w > 0.7 && w < 1.4,
            name + ": vertex " + axes[i] + " pull width within 0.7-1.4");
    }
    for (int i = 0; i < 3; ++i) {
      const double w = width68(momentumPull[i]);
      std::cout << "  momentum p" << axes[i] << " at the vertex: pull width "
                << w << " +- " << width68Error(w, momentumPull[i].size())
                << " (N = " << momentumPull[i].size() << ", " << nonPositive[i]
                << " left out with a variance <= 0)" << std::endl;
      check(w > 0.7 && w < 1.4,
            name + ": p" + axes[i] + " pull width within 0.7-1.4");
    }
    const double dp = width68(momentumResidual);
    std::cout << "  dp/p at the vertex: width " << dp << std::endl;
    check(dp < 0.05, name + ": momentum at the vertex within 5%");
    std::vector<double> sorted = doca;
    std::sort(sorted.begin(), sorted.end());
    const double median = sorted[sorted.size() / 2];
    std::cout << "  DOCA: median " << median << " cm, largest " << sorted.back()
              << " cm" << std::endl;
    check(median > 1e-3 && median < 0.5, name + ": DOCA in cm, small");
  }
};

/// Simulate, fit and find the vertex of `nTracks` tracks from `vertex`
void runEvent(SHiP::ActsStrawTracker& tracker, const TVector3& vertex,
              int nTracks, std::mt19937& rng, Tally& tally) {
  std::uniform_real_distribution<double> slope(-0.03, 0.03);
  std::uniform_real_distribution<double> momentum(3., 30.);
  tracker.ClearEvent();
  Truth truth{vertex, {}};
  std::vector<int> fitted;
  std::vector<int> truthOf;
  for (int i = 0; i < nTracks; ++i) {
    const double charge = i % 2 == 0 ? 1. : -1.;
    const TVector3 direction = TVector3(slope(rng), slope(rng), 1.).Unit();
    const TVector3 p = direction * momentum(rng);
    truth.momenta.push_back(p);
    std::vector<int> indices;
    for (const auto& [id, drift] : hits({vertex, p}, charge, rng)) {
      const int index = tracker.AddMeasurement(id, drift, kResolution);
      check(index >= 0, "hit on a known straw");
      indices.push_back(index);
    }
    const int track = tracker.FitCandidate(indices);
    if (track >= 0) {
      fitted.push_back(track);
      truthOf.push_back(i);
    }
  }
  ++tally.events;
  check(static_cast<int>(fitted.size()) == nTracks,
        tally.name + ": every track fitted");

  std::vector<SHiP::RecoVertex> vertices;
  tracker.FindVertices(fitted, vertices);
  if (vertices.size() != 1) {
    return;
  }
  ++tally.oneVertex;
  const auto& found = vertices.front();
  const double position[3] = {found.x(), found.y(), found.z()};
  const double errors[3] = {found.err_x(), found.err_y(), found.err_z()};
  for (int i = 0; i < 3; ++i) {
    check(errors[i] > 0., tally.name + ": vertex uncertainty positive");
    const double residual = position[i] - vertex[i];
    tally.residual[i].push_back(residual);
    tally.error[i].push_back(errors[i]);
    tally.pull[i].push_back(residual / errors[i]);
  }
  if (found.doca() >= 0.) {
    tally.doca.push_back(found.doca());
  }

  const auto& ids = found.trackIds();
  const auto& weights = found.trackWeights();
  int assigned = 0;
  for (std::size_t k = 0; k < ids.size(); ++k) {
    if (weights[k] < SHiP::RecoVertex::kMinTrackWeight) {
      continue;
    }
    ++assigned;
    const auto it = std::find(fitted.begin(), fitted.end(), ids[k]);
    if (it == fitted.end()) {
      check(false, tally.name + ": vertex track among those passed");
      continue;
    }
    const TVector3& p = truth.momenta[truthOf[it - fitted.begin()]];
    const double measured[3] = {found.trackPx()[k], found.trackPy()[k],
                                found.trackPz()[k]};
    const auto cov = found.GetTrackMomentumCovariance(k);
    const double variances[3] = {cov[0], cov[3], cov[5]};
    for (int i = 0; i < 3; ++i) {
      // Some low-momentum tracks come out of the fits with a slightly
      // negative pz variance; they are counted, not checked
      if (!(variances[i] > 0.)) {
        ++tally.nonPositive[i];
        continue;
      }
      tally.momentumPull[i].push_back((measured[i] - p[i]) /
                                      std::sqrt(variances[i]));
    }
    tally.momentumResidual.push_back(
        TVector3(measured[0], measured[1], measured[2]).Mag() / p.Mag() - 1.);
  }
  if (assigned == nTracks) {
    ++tally.allTracksAssigned;
  }
}

}  // namespace

int main() {
  TGeoManager* manager = buildGeometry();
  BoxField field;
  SHiP::ActsStrawTracker tracker(manager, &field);
  check(tracker.GetNStraws() == 4 * 4 * 2 * kStrawsPerLayer,
        "all straws found");

  std::mt19937 rng(20261118);
  Tally pairs{"two tracks near the axis"};
  Tally offAxis{"four tracks off the axis"};
  for (int event = 0; event < 300; ++event) {
    runEvent(tracker, TVector3(5., -3., 6000.), 2, rng, pairs);
    runEvent(tracker, TVector3(50., -30., 6500.), 4, rng, offAxis);
  }
  pairs.report();
  offAxis.report();

  if (failures > 0) {
    std::cout << failures << " checks failed" << std::endl;
    return 1;
  }
  std::cout << "All ACTS vertex finding checks passed" << std::endl;
  return 0;
}
