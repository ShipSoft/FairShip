// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

// Vertex finding with ActsVertexFinder, on straight tracks from known vertices
// in the decay volume, in the ACTS frame of the reconstruction (beam along x)

#include <cmath>
#include <cstddef>
#include <iostream>
#include <random>
#include <string>
#include <vector>

#include "Acts/Definitions/Units.hpp"
#include "Acts/EventData/BoundTrackParameters.hpp"
#include "Acts/EventData/ParticleHypothesis.hpp"
#include "Acts/Geometry/GeometryContext.hpp"
#include "Acts/MagneticField/MagneticFieldContext.hpp"
#include "ActsVertexGeometry.hpp"
#include "ActsVertexing.hpp"

namespace {

namespace u = Acts::UnitConstants;

int failures = 0;

void check(bool condition, const std::string& what) {
  if (!condition) {
    std::cout << "FAIL: " << what << std::endl;
    ++failures;
  }
}

/// Plane on which the tracks are given, downstream of all vertices
constexpr double kReferenceX = 82 * u::m;
constexpr double kSigmaPosition = 0.5 * u::mm;
constexpr double kSigmaAngle = 1e-4;
constexpr double kRelativeSigmaP = 0.01;
/// Track weight above which a track counts as assigned to a vertex
constexpr double kAssigned = 0.5;
/// Largest chi2 (3 degrees of freedom) of a found vertex against the true
/// one, p = 2e-4
constexpr double kMaxPositionChi2 = 20.;
/// Largest distance of a found vertex from the true one
constexpr double kMaxDistance = 30 * u::cm;

const Acts::GeometryContext gctx =
    Acts::GeometryContext::dangerouslyDefaultConstruct();
const Acts::MagneticFieldContext mctx;

/// A muon from `vertex` with slopes `ty`, `tz` against the beam, measured on
/// the reference plane with the uncertainties above
Acts::BoundTrackParameters makeTrack(const Acts::Vector3& vertex, double ty,
                                     double tz, double p, double charge,
                                     std::mt19937& rng) {
  const Acts::Vector3 direction = Acts::Vector3(1., ty, tz).normalized();
  const Acts::Vector3 atPlane =
      vertex + (kReferenceX - vertex.x()) / direction.x() * direction;
  const auto plane = SHiP::ActsVertexGeometry::constantZPlane(
      Acts::Vector3(kReferenceX, 0., 0.));
  const double qOverP = charge / (p * u::GeV);

  Acts::BoundMatrix covariance = Acts::BoundMatrix::Zero();
  covariance(Acts::eBoundLoc0, Acts::eBoundLoc0) = std::pow(kSigmaPosition, 2);
  covariance(Acts::eBoundLoc1, Acts::eBoundLoc1) = std::pow(kSigmaPosition, 2);
  covariance(Acts::eBoundPhi, Acts::eBoundPhi) = std::pow(kSigmaAngle, 2);
  covariance(Acts::eBoundTheta, Acts::eBoundTheta) = std::pow(kSigmaAngle, 2);
  covariance(Acts::eBoundQOverP, Acts::eBoundQOverP) =
      std::pow(kRelativeSigmaP * qOverP, 2);
  covariance(Acts::eBoundTime, Acts::eBoundTime) = 1e18;

  const auto exact =
      Acts::BoundTrackParameters::create(
          gctx, plane, Acts::Vector4(atPlane.x(), atPlane.y(), atPlane.z(), 0.),
          direction, qOverP, covariance, Acts::ParticleHypothesis::muon())
          .value();
  std::normal_distribution<double> gauss;
  Acts::BoundVector smeared = exact.parameters();
  smeared[Acts::eBoundLoc0] += kSigmaPosition * gauss(rng);
  smeared[Acts::eBoundLoc1] += kSigmaPosition * gauss(rng);
  smeared[Acts::eBoundPhi] += kSigmaAngle * gauss(rng);
  smeared[Acts::eBoundTheta] += kSigmaAngle * gauss(rng);
  smeared[Acts::eBoundQOverP] *= 1. + kRelativeSigmaP * gauss(rng);
  return Acts::BoundTrackParameters(plane, smeared, covariance,
                                    Acts::ParticleHypothesis::muon());
}

/// `n` tracks of alternating charge from `vertex`
void addTracks(std::vector<Acts::BoundTrackParameters>& tracks,
               std::vector<int>& truth, int vertexId,
               const Acts::Vector3& vertex, int n, std::mt19937& rng) {
  std::uniform_real_distribution<double> slope(-0.05, 0.05);
  std::uniform_real_distribution<double> momentum(2., 20.);
  for (int i = 0; i < n; ++i) {
    tracks.push_back(makeTrack(vertex, slope(rng), slope(rng), momentum(rng),
                               i % 2 == 0 ? 1. : -1., rng));
    truth.push_back(vertexId);
  }
}

/// Vertex position in the ACTS frame from SHiP coordinates in cm
Acts::Vector3 shipVertex(double x, double y, double z) {
  return Acts::Vector3(z * u::cm, y * u::cm, -x * u::cm);
}

/// Index of the found vertex in which each track has its largest weight,
/// if that weight exceeds kAssigned, else -1
std::vector<int> assignment(const std::vector<SHiP::FoundVertex>& vertices,
                            std::size_t nTracks) {
  std::vector<int> assigned(nTracks, -1);
  std::vector<double> weight(nTracks, kAssigned);
  for (std::size_t v = 0; v < vertices.size(); ++v) {
    for (const auto& track : vertices[v].tracks) {
      if (track.weight > weight[track.index]) {
        weight[track.index] = track.weight;
        assigned[track.index] = static_cast<int>(v);
      }
    }
  }
  return assigned;
}

/// Whether a found vertex agrees with the true position within its
/// uncertainty
bool compatible(const SHiP::FoundVertex& found, const Acts::Vector3& truth) {
  const Acts::Vector3 delta = found.position - truth;
  const double chi2 = delta.dot(found.covariance.inverse() * delta);
  return chi2 < kMaxPositionChi2 && delta.norm() < kMaxDistance;
}

/// Found vertex closest to `position`
const SHiP::FoundVertex* closest(const std::vector<SHiP::FoundVertex>& found,
                                 const Acts::Vector3& position) {
  const SHiP::FoundVertex* best = nullptr;
  for (const auto& vertex : found) {
    if (!best || (vertex.position - position).norm() <
                     (best->position - position).norm()) {
      best = &vertex;
    }
  }
  return best;
}

/// Outcomes of one kind of event, counted over many events: the vertex
/// finding, like any fit, misses the tails of the distributions
struct Tally {
  std::string name;
  int events = 0;
  int rightVertexCount = 0;
  int vertices = 0;
  int compatibleVertices = 0;
  int tracks = 0;
  int rightlyAssigned = 0;

  void report() const {
    std::cout << name << ": " << rightVertexCount << "/" << events
              << " right number of vertices, " << compatibleVertices << "/"
              << vertices << " vertices compatible with the truth, "
              << rightlyAssigned << "/" << tracks << " tracks assigned rightly"
              << std::endl;
    check(rightVertexCount >= 0.98 * events,
          name + ": right number of vertices in 98% of the events");
    check(compatibleVertices >= 0.99 * vertices,
          name + ": 99% of the vertices compatible with the truth");
    check(rightlyAssigned >= 0.99 * tracks,
          name + ": 99% of the tracks assigned rightly");
  }
};

/// Find the vertices of `tracks` from the true `vertices` (track `i` from
/// vertex truth[i], or from none if negative) and count the outcome
void evaluate(const SHiP::ActsVertexFinder& finder,
              const std::vector<Acts::BoundTrackParameters>& tracks,
              const std::vector<int>& truth,
              const std::vector<Acts::Vector3>& vertices, Tally& tally) {
  const auto found = finder.find(tracks, gctx, mctx);
  ++tally.events;
  if (found.size() == vertices.size()) {
    ++tally.rightVertexCount;
  }
  for (const auto& vertex : found) {
    check(vertex.nDoF > 0., tally.name + ": vertex fit has degrees of freedom");
  }
  std::vector<int> foundOf(vertices.size(), -1);
  for (std::size_t v = 0; v < vertices.size(); ++v) {
    ++tally.vertices;
    const auto* best = closest(found, vertices[v]);
    if (best) {
      tally.compatibleVertices += compatible(*best, vertices[v]) ? 1 : 0;
      foundOf[v] = static_cast<int>(best - found.data());
    }
  }
  const auto assigned = assignment(found, tracks.size());
  for (std::size_t i = 0; i < tracks.size(); ++i) {
    ++tally.tracks;
    const int expected = truth[i] < 0 ? -1 : foundOf[truth[i]];
    tally.rightlyAssigned += assigned[i] == expected ? 1 : 0;
  }
}

void oneVertex(const SHiP::ActsVertexFinder& finder, std::mt19937& rng,
               Tally& tally) {
  std::vector<Acts::BoundTrackParameters> tracks;
  std::vector<int> truth;
  const std::vector<Acts::Vector3> vertices = {shipVertex(50., -30., 6000.)};
  addTracks(tracks, truth, 0, vertices[0], 4, rng);
  evaluate(finder, tracks, truth, vertices, tally);
}

void twoVertices(const SHiP::ActsVertexFinder& finder, std::mt19937& rng,
                 bool withStray, Tally& tally) {
  std::vector<Acts::BoundTrackParameters> tracks;
  std::vector<int> truth;
  // One on the axis, one 2 m off it (ACTS z = -2 m), 1 m apart along the beam
  const std::vector<Acts::Vector3> vertices = {shipVertex(0., 20., 5500.),
                                               shipVertex(200., -40., 5600.)};
  addTracks(tracks, truth, 0, vertices[0], 3, rng);
  addTracks(tracks, truth, 1, vertices[1], 3, rng);
  if (withStray) {
    // From far upstream, passing metres from both vertices
    tracks.push_back(
        makeTrack(shipVertex(-150., 150., 3500.), 0.02, -0.03, 8., 1., rng));
    truth.push_back(-1);
  }
  evaluate(finder, tracks, truth, vertices, tally);
}

void testTooFewTracks(const SHiP::ActsVertexFinder& finder, std::mt19937& rng) {
  std::vector<Acts::BoundTrackParameters> tracks;
  std::vector<int> truth;
  addTracks(tracks, truth, 0, shipVertex(0., 0., 6000.), 1, rng);
  check(finder.find(tracks, gctx, mctx).empty(), "no vertex from one track");
}

}  // namespace

// With --debug, the ACTS vertexing logs at debug level
int main(int argc, char** argv) {
  const bool debug = argc > 1 && std::string(argv[1]) == "--debug";
  const SHiP::ActsVertexFinder finder(debug ? Acts::Logging::DEBUG
                                            : Acts::Logging::WARNING);
  std::mt19937 rng(20261104);
  Tally one{"one vertex of four tracks"};
  Tally two{"two vertices of three tracks"};
  Tally stray{"two vertices and a stray track"};
  for (int event = 0; event < 200; ++event) {
    oneVertex(finder, rng, one);
    twoVertices(finder, rng, false, two);
    twoVertices(finder, rng, true, stray);
  }
  one.report();
  two.report();
  stray.report();
  testTooFewTracks(finder, rng);
  if (failures > 0) {
    std::cout << failures << " checks failed" << std::endl;
    return 1;
  }
  std::cout << "All ACTS vertexing checks passed" << std::endl;
  return 0;
}
