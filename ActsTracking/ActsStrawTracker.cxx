// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#include "ActsStrawTracker.h"

#include <algorithm>
#include <array>
#include <cmath>
#include <limits>
#include <numeric>
#include <optional>
#include <stdexcept>
#include <utility>

#include "Acts/Definitions/TrackParametrization.hpp"
#include "Acts/Definitions/Units.hpp"
#include "Acts/EventData/BoundTrackParameters.hpp"
#include "Acts/EventData/ParticleHypothesis.hpp"
#include "Acts/EventData/SourceLink.hpp"
#include "Acts/EventData/TrackContainer.hpp"
#include "Acts/EventData/TransformationHelpers.hpp"
#include "Acts/EventData/VectorMultiTrajectory.hpp"
#include "Acts/EventData/VectorTrackContainer.hpp"
#include "Acts/Geometry/GeometryContext.hpp"
#include "Acts/MagneticField/MagneticFieldContext.hpp"
#include "Acts/Propagator/DirectNavigator.hpp"
#include "Acts/Propagator/EigenStepper.hpp"
#include "Acts/Propagator/Propagator.hpp"
#include "Acts/Propagator/VoidNavigator.hpp"
#include "Acts/Surfaces/PlaneSurface.hpp"
#include "Acts/TrackFitting/GainMatrixSmoother.hpp"
#include "Acts/TrackFitting/GainMatrixUpdater.hpp"
#include "Acts/TrackFitting/KalmanFitter.hpp"
#include "Acts/Utilities/CalibrationContext.hpp"
#include "Acts/Utilities/Logger.hpp"
#include "Acts/Utilities/UnitVectors.hpp"
#include "ActsFrame.hpp"
#include "ActsShipField.hpp"
#include "ActsStrawGeometry.hpp"
#include "StrawPatRec.hpp"
#include "TGeoManager.h"
#include "TVirtualMagField.h"

namespace SHiP {

namespace {

namespace u = Acts::UnitConstants;

using Trajectory = Acts::VectorMultiTrajectory;
using TrackContainer = Acts::TrackContainer<Acts::VectorTrackContainer,
                                            Trajectory, std::shared_ptr>;
using Stepper = Acts::EigenStepper<>;
using DirectPropagator = Acts::Propagator<Stepper, Acts::DirectNavigator>;
using KalmanFitter = Acts::KalmanFitter<DirectPropagator, Trajectory>;
using Extrapolator = Acts::Propagator<Stepper, Acts::VoidNavigator>;

/// Seed uncertainties of the track fit, for a seed from the straight-line
/// segments of the pattern recognition
constexpr double kSeedSigmaLoc0 = 1 * u::mm;
constexpr double kSeedSigmaLoc1 = 20 * u::mm;
constexpr double kSeedSigmaAngle = 5e-3;
constexpr double kSeedRelativeSigmaP = 0.3;
/// Refits that re-resolve the left/right ambiguity and drop outliers
constexpr int kMaxRefits = 3;
/// Hits further than this many sigma from the fitted track are dropped
constexpr double kOutlierPull = 5.;
/// Step of the field integration along the track (cm)
constexpr double kFieldStep = 5.;
/// GeV per (T m) for a unit charge
constexpr double kKick = 0.299792458;
/// Highest seed momentum (GeV), for tracks with no measurable kink
constexpr double kMaxSeedMomentum = 1000.;
/// Fewest measurements a fitted track may keep
constexpr int kMinFitMeasurements = 10;
/// Ambiguity resolution between fitted tracks: the weight of a hit against
/// the chi2 per degree of freedom when ranking them, the worst chi2 per
/// degree of freedom accepted, and the largest fraction of the hits of the
/// shorter of two tracks they may share
constexpr double kTrackHitWeight = 0.5;
constexpr double kMaxTrackChi2PerNdf = 5.;
constexpr double kMaxSharedFraction = 0.25;
/// Fewest hits on a track found by the pattern recognition. With fewer, the
/// fit can absorb hits of different tracks into a low momentum.
constexpr std::size_t kMinTrackHits = 20;
// The time is not measured, so it is effectively left free
constexpr double kSeedSigmaTime = 1e9;

/// Range of the vertex seed along the beam (ACTS x)
constexpr double kVertexSeedMinX = 20 * u::m;
constexpr double kVertexSeedMaxX = 90 * u::m;
/// Iterations and convergence of the vertex seed
constexpr int kVertexIterations = 10;
constexpr double kVertexTolerance = 0.1 * u::mm;

constexpr double kPathLimit = 100 * u::m;

struct StrawMeasurement {
  const Acts::Surface* surface;
  const StrawWire* wire;
  /// Unsigned drift distance and its variance, in ACTS units
  double driftRadius;
  double variance;
  /// Side of the wire in the current fit
  int sign{1};
};

/// Upper triangle of a symmetric matrix, row-major
template <int N, std::size_t M = N * (N + 1) / 2>
std::array<Double_t, M> upperTriangle(const Acts::SquareMatrix<N>& matrix) {
  std::array<Double_t, M> elements{};
  std::size_t k = 0;
  for (int row = 0; row < N; ++row) {
    for (int col = row; col < N; ++col) {
      elements[k++] = matrix(row, col);
    }
  }
  return elements;
}

/// Jacobian of the momentum vector (ACTS frame) w.r.t. direction and q/p
Acts::Matrix<3, 3> momentumJacobianDirection(double qOverP) {
  return Acts::SquareMatrix3::Identity() / std::abs(qOverP);
}

Acts::Vector3 momentumJacobianQOverP(const Acts::Vector3& direction,
                                     double qOverP) {
  return -direction / (qOverP * std::abs(qOverP));
}

/// Covariance of (x, y, z, px, py, pz) in the SHiP frame for bound parameters
Acts::SquareMatrix<6> shipCovariance(const Acts::BoundTrackParameters& params,
                                     const Acts::GeometryContext& gctx) {
  const auto& surface = params.referenceSurface();
  const Acts::FreeVector free =
      Acts::transformBoundToFreeParameters(surface, gctx, params.parameters());
  const Acts::Vector3 direction = free.segment<3>(Acts::eFreeDir0);
  const Acts::BoundToFreeMatrix boundToFree = surface.boundToFreeJacobian(
      gctx, free.segment<3>(Acts::eFreePos0), direction);
  const Acts::FreeMatrix freeCovariance =
      boundToFree * params.covariance().value() * boundToFree.transpose();

  const double qOverP = free[Acts::eFreeQOverP];
  const Acts::RotationMatrix3 rotation = ActsFrame::toShipRotation();
  Acts::Matrix<6, Acts::eFreeSize> freeToShip =
      Acts::Matrix<6, Acts::eFreeSize>::Zero();
  freeToShip.block<3, 3>(0, Acts::eFreePos0) =
      rotation / ActsFrame::kShipLength;
  freeToShip.block<3, 3>(3, Acts::eFreeDir0) =
      rotation * momentumJacobianDirection(qOverP) / u::GeV;
  freeToShip.block<3, 1>(3, Acts::eFreeQOverP) =
      rotation * momentumJacobianQOverP(direction, qOverP) / u::GeV;
  return freeToShip * freeCovariance * freeToShip.transpose();
}

/// Covariance of the momentum (SHiP frame) for bound parameters
Acts::SquareMatrix3 shipMomentumCovariance(
    const Acts::BoundTrackParameters& params) {
  const double phi = params.parameters()[Acts::eBoundPhi];
  const double theta = params.parameters()[Acts::eBoundTheta];
  const double qOverP = params.parameters()[Acts::eBoundQOverP];
  const double p = 1. / std::abs(qOverP);
  const Acts::Vector3 direction = params.direction();
  Acts::Matrix<3, Acts::eBoundSize> boundToMomentum =
      Acts::Matrix<3, Acts::eBoundSize>::Zero();
  boundToMomentum.col(Acts::eBoundPhi) =
      Acts::Vector3(-std::sin(phi) * std::sin(theta),
                    std::cos(phi) * std::sin(theta), 0.) *
      p;
  boundToMomentum.col(Acts::eBoundTheta) =
      Acts::Vector3(std::cos(phi) * std::cos(theta),
                    std::sin(phi) * std::cos(theta), -std::sin(theta)) *
      p;
  boundToMomentum.col(Acts::eBoundQOverP) =
      momentumJacobianQOverP(direction, qOverP);
  const Acts::Matrix<3, Acts::eBoundSize> jacobian =
      ActsFrame::toShipRotation() * boundToMomentum / u::GeV;
  return jacobian * params.covariance().value() * jacobian.transpose();
}

/// A straight line: a point and a unit direction
using Tangent = std::pair<Acts::Vector3, Acts::Vector3>;

/// Tangent of a track with the given bound parameters on a surface
Tangent tangent(const Acts::Surface& surface, const Acts::BoundVector& params,
                const Acts::GeometryContext& gctx) {
  const Acts::Vector3 direction = Acts::makeDirectionFromPhiTheta(
      params[Acts::eBoundPhi], params[Acts::eBoundTheta]);
  return {surface.localToGlobal(
              gctx,
              Acts::Vector2(params[Acts::eBoundLoc0], params[Acts::eBoundLoc1]),
              direction),
          direction};
}

std::vector<Tangent> tangents(
    const std::vector<Acts::BoundTrackParameters>& tracks,
    const Acts::GeometryContext& gctx) {
  std::vector<Tangent> lines;
  for (const auto& track : tracks) {
    lines.push_back(
        tangent(track.referenceSurface(), track.parameters(), gctx));
  }
  return lines;
}

/// The point closest to a set of lines, in the least-squares sense
Acts::Vector3 closestPoint(const std::vector<Tangent>& lines) {
  Acts::SquareMatrix3 a = Acts::SquareMatrix3::Zero();
  Acts::Vector3 b = Acts::Vector3::Zero();
  for (const auto& [position, direction] : lines) {
    const Acts::SquareMatrix3 projection =
        Acts::SquareMatrix3::Identity() - direction * direction.transpose();
    a += projection;
    b += projection * position;
  }
  return a.colPivHouseholderQr().solve(b);
}

/// Starting point of the vertex fit: the closest point of the straight
/// tracks, kept within the range along the beam where vertices are
Acts::Vector3 vertexSeed(const std::vector<Acts::BoundTrackParameters>& tracks,
                         const Acts::GeometryContext& gctx) {
  Acts::Vector3 seed = closestPoint(tangents(tracks, gctx));
  if (!seed.allFinite()) {
    seed = Acts::Vector3(0.5 * (kVertexSeedMinX + kVertexSeedMaxX), 0., 0.);
  }
  seed.x() = std::clamp(seed.x(), kVertexSeedMinX, kVertexSeedMaxX);
  return seed;
}

/// Plane of constant z (SHiP), i.e. constant x (ACTS), through a point
std::shared_ptr<Acts::PlaneSurface> constantZPlane(const Acts::Vector3& point) {
  Acts::Transform3 transform = Acts::Transform3::Identity();
  transform.linear().col(0) = Acts::Vector3::UnitY();
  transform.linear().col(1) = Acts::Vector3::UnitZ();
  transform.linear().col(2) = Acts::Vector3::UnitX();
  transform.translation() = point;
  return Acts::Surface::makeShared<Acts::PlaneSurface>(transform);
}

/// Distance of closest approach between two straight lines
double lineDistance(const Acts::Vector3& p1, const Acts::Vector3& d1,
                    const Acts::Vector3& p2, const Acts::Vector3& d2) {
  const Acts::Vector3 delta = p1 - p2;
  const Acts::Vector3 normal = d1.cross(d2);
  if (normal.norm() > 1e-12) {
    return std::abs(delta.dot(normal)) / normal.norm();
  }
  return delta.cross(d1.normalized()).norm();
}

}  // namespace

struct ActsStrawTracker::Impl {
  Impl(const TGeoManager& geometry, TVirtualMagField* magField)
      : straws(geometry),
        shipField(magField),
        field(std::make_shared<ActsShipField>(magField)),
        fitter(DirectPropagator(Stepper(field), Acts::DirectNavigator(),
                                Acts::getDefaultLogger("Propagator",
                                                       Acts::Logging::WARNING)),
               Acts::getDefaultLogger("KalmanFitter", Acts::Logging::WARNING)),
        extrapolator(
            Stepper(field), Acts::VoidNavigator(),
            Acts::getDefaultLogger("Extrapolator", Acts::Logging::WARNING)),
        tracks(std::make_shared<Acts::VectorTrackContainer>(),
               std::make_shared<Trajectory>()) {
    extensions.surfaceAccessor.connect<&Impl::surfaceOf>(this);
    extensions.calibrator.connect<&Impl::calibrate>(this);
    extensions.updater
        .connect<&Acts::GainMatrixUpdater::operator()<Trajectory>>(&updater);
    extensions.smoother
        .connect<&Acts::GainMatrixSmoother::operator()<Trajectory>>(&smoother);

    // The magnet sits between stations 2 and 3
    for (const auto& [id, wire] : straws.wires()) {
      if (wire.station == 2) {
        magnetStart = std::max(magnetStart, wire.z);
      } else if (wire.station == 3) {
        magnetEnd = std::min(magnetEnd, wire.z);
      }
    }
    LineSegment axis;
    const auto [integral, centre] = fieldIntegral(axis);
    patRec.emplace(StrawPatRec::Config{}, centre, integral);
  }

  /// Hits for the pattern recognition, from measurement indices
  std::vector<PatRecHit> patRecHits(const std::vector<Int_t>& indices) const;
  /// Seed for the fit of a candidate, on the surface of its first hit
  Acts::BoundTrackParameters seed(const TrackCandidate& candidate,
                                  const StrawMeasurement& first) const;
  /// Fit a candidate, refining the sides of the wires and dropping
  /// outliers; returns the track index or -1
  Int_t fit(const TrackCandidate& candidate,
            const std::vector<PatRecHit>& hits);
  /// One Kalman fit of the given measurements, appended to the tracks
  std::optional<std::size_t> fitOnce(const std::vector<Int_t>& indices,
                                     const Acts::BoundTrackParameters& start);

  /// Integral of Bx along a straight line through the magnet (T m), and the
  /// z of its centre (cm)
  std::pair<double, double> fieldIntegral(const LineSegment& line) const {
    double integral = 0.;
    double moment = 0.;
    for (double z = magnetStart; z < magnetEnd; z += kFieldStep) {
      const double zMid = z + kFieldStep / 2.;
      const double x[3] = {line.x(zMid), line.y(zMid), zMid};
      double b[3] = {0., 0., 0.};
      shipField->Field(x, b);
      // kGauss to T, cm to m
      const double bx = 0.1 * b[0] * 0.01 * kFieldStep;
      integral += bx;
      moment += bx * zMid;
    }
    return {integral, integral != 0. ? moment / integral
                                     : 0.5 * (magnetStart + magnetEnd)};
  }

  const Acts::Surface* surfaceOf(const Acts::SourceLink& sourceLink) const {
    return measurements.at(sourceLink.get<std::size_t>()).surface;
  }

  void calibrate(const Acts::GeometryContext& /*gctx*/,
                 const Acts::CalibrationContext& /*cctx*/,
                 const Acts::SourceLink& sourceLink,
                 Trajectory::TrackStateProxy state) const {
    const auto& measurement = measurements.at(sourceLink.get<std::size_t>());
    state.allocateCalibrated(1);
    state.template calibrated<1>()(0) =
        measurement.sign * measurement.driftRadius;
    state.template calibratedCovariance<1>()(0, 0) = measurement.variance;
    state.setProjectorSubspaceIndices(std::array{Acts::eBoundLoc0});
    state.setUncalibratedSourceLink(Acts::SourceLink(sourceLink));
  }

  Acts::BoundTrackParameters trackParameters(Int_t track) const {
    if (track < 0 || static_cast<std::size_t>(track) >= tracks.size()) {
      throw std::out_of_range("ActsStrawTracker: track index out of range");
    }
    return tracks.getTrack(track).createParametersAtReference();
  }

  /// Propagate to `target` in whichever direction reaches it
  std::optional<Acts::BoundTrackParameters> extrapolate(
      const Extrapolator& propagator, const Acts::BoundTrackParameters& start,
      const Acts::Surface& target) const {
    for (const auto direction :
         {Acts::Direction::Forward(), Acts::Direction::Backward()}) {
      Extrapolator::Options<> options(gctx, mctx);
      options.pathLimit = kPathLimit;
      options.direction = direction;
      auto result = propagator.propagate(start, target, options);
      if (result.ok() && result.value().endParameters.has_value()) {
        return result.value().endParameters.value();
      }
    }
    return std::nullopt;
  }

  ActsStrawGeometry straws;
  TVirtualMagField* shipField;
  std::shared_ptr<const ActsShipField> field;
  double magnetStart = -std::numeric_limits<double>::infinity();
  double magnetEnd = std::numeric_limits<double>::infinity();
  std::optional<StrawPatRec> patRec;
  KalmanFitter fitter;
  Extrapolator extrapolator;
  Acts::GainMatrixUpdater updater;
  Acts::GainMatrixSmoother smoother;
  Acts::KalmanFitterExtensions<Trajectory> extensions;
  Acts::GeometryContext gctx =
      Acts::GeometryContext::dangerouslyDefaultConstruct();
  Acts::MagneticFieldContext mctx;
  Acts::CalibrationContext cctx;
  std::vector<StrawMeasurement> measurements;
  TrackContainer tracks;
  /// Measurements used in each track
  std::vector<std::vector<Int_t>> trackMeasurements;
};

ActsStrawTracker::ActsStrawTracker(const TGeoManager* geometry,
                                   TVirtualMagField* field) {
  if (geometry == nullptr) {
    throw std::invalid_argument("ActsStrawTracker: geometry is null");
  }
  fImpl = std::make_unique<Impl>(*geometry, field);
}

ActsStrawTracker::~ActsStrawTracker() = default;

void ActsStrawTracker::ClearEvent() {
  fImpl->measurements.clear();
  fImpl->tracks.clear();
  fImpl->trackMeasurements.clear();
}

Int_t ActsStrawTracker::AddMeasurement(Int_t detectorId, Double_t driftRadius,
                                       Double_t resolution) {
  const Acts::Surface* surface = fImpl->straws.surface(detectorId);
  const StrawWire* wire = fImpl->straws.wire(detectorId);
  if (surface == nullptr || wire == nullptr) {
    return -1;
  }
  const double sigma = resolution * ActsFrame::kShipLength;
  fImpl->measurements.push_back({surface, wire,
                                 std::abs(driftRadius) * ActsFrame::kShipLength,
                                 sigma * sigma});
  return static_cast<Int_t>(fImpl->measurements.size() - 1);
}

std::vector<PatRecHit> ActsStrawTracker::Impl::patRecHits(
    const std::vector<Int_t>& indices) const {
  std::vector<PatRecHit> hits;
  hits.reserve(indices.size());
  for (const Int_t index : indices) {
    if (index < 0 || static_cast<std::size_t>(index) >= measurements.size()) {
      throw std::out_of_range("ActsStrawTracker: measurement out of range");
    }
    const auto& m = measurements[index];
    hits.push_back({index, m.wire, m.driftRadius / ActsFrame::kShipLength,
                    std::sqrt(m.variance) / ActsFrame::kShipLength});
  }
  return hits;
}

Acts::BoundTrackParameters ActsStrawTracker::Impl::seed(
    const TrackCandidate& candidate, const StrawMeasurement& first) const {
  const LineSegment& line = candidate.upstream;
  const double z = first.wire->z;
  const Acts::Vector3 position =
      ActsFrame::positionToActs(line.x(z), line.y(z), z);
  const Acts::Vector3 direction =
      (ActsFrame::toActsRotation() * Acts::Vector3(line.tx, line.ty, 1.))
          .normalized();
  const auto hypothesis = Acts::ParticleHypothesis::muon();
  const double qOverP = hypothesis.qOverP(
      candidate.momentum * u::GeV, static_cast<double>(candidate.charge));

  // Local coordinates at the point of closest approach to the first straw
  const Acts::Surface& surface = *first.surface;
  const auto intersection =
      surface.intersect(gctx, position, direction).closest();
  const Acts::Vector3 onSurface =
      intersection.isValid() ? intersection.position() : position;
  auto local = surface.globalToLocal(gctx, onSurface, direction);
  const Acts::Vector2 localPosition =
      local.ok() ? local.value() : Acts::Vector2::Zero();

  Acts::BoundVector parameters = Acts::BoundVector::Zero();
  parameters[Acts::eBoundLoc0] = localPosition[0];
  parameters[Acts::eBoundLoc1] = localPosition[1];
  parameters[Acts::eBoundPhi] = Acts::VectorHelpers::phi(direction);
  parameters[Acts::eBoundTheta] = Acts::VectorHelpers::theta(direction);
  parameters[Acts::eBoundQOverP] = qOverP;
  Acts::BoundVector sigmas;
  sigmas << kSeedSigmaLoc0, kSeedSigmaLoc1, kSeedSigmaAngle, kSeedSigmaAngle,
      kSeedRelativeSigmaP * std::abs(qOverP), kSeedSigmaTime;
  const Acts::BoundMatrix covariance = sigmas.cwiseProduct(sigmas).asDiagonal();
  return Acts::BoundTrackParameters(surface.getSharedPtr(), parameters,
                                    covariance, hypothesis);
}

std::optional<std::size_t> ActsStrawTracker::Impl::fitOnce(
    const std::vector<Int_t>& indices,
    const Acts::BoundTrackParameters& start) {
  std::vector<Acts::SourceLink> sourceLinks;
  std::vector<const Acts::Surface*> surfaces;
  for (const Int_t index : indices) {
    sourceLinks.emplace_back(static_cast<std::size_t>(index));
    surfaces.push_back(measurements[index].surface);
  }
  Acts::PropagatorPlainOptions propagatorOptions(gctx, mctx);
  Acts::KalmanFitterOptions<Trajectory> options(gctx, mctx, std::cref(cctx),
                                                extensions, propagatorOptions,
                                                surfaces.front());
  options.referenceSurfaceStrategy = Acts::TrackExtrapolationStrategy::first;

  const std::size_t nTracksBefore = tracks.size();
  auto result = fitter.fit(sourceLinks.begin(), sourceLinks.end(), start,
                           options, surfaces, tracks);
  if (!result.ok() || !result.value().hasReferenceSurface()) {
    // A failed fit may leave a partial track behind. Drop it, so that track
    // indices stay contiguous.
    while (tracks.size() > nTracksBefore) {
      tracks.removeTrack(tracks.size() - 1);
    }
    return std::nullopt;
  }
  return result.value().index();
}

Int_t ActsStrawTracker::Impl::fit(const TrackCandidate& candidate,
                                  const std::vector<PatRecHit>& hits) {
  // The measurements, ordered in z, with the sides of the wires from the
  // segment fits
  std::vector<std::pair<double, Int_t>> ordered;
  for (const LineSegment* segment :
       {&candidate.upstream, &candidate.downstream}) {
    for (std::size_t k = 0; k < segment->hits.size(); ++k) {
      const PatRecHit& hit = hits[segment->hits[k]];
      measurements[hit.index].sign = segment->signs[k];
      ordered.emplace_back(hit.wire->z, hit.index);
    }
  }
  std::sort(ordered.begin(), ordered.end());
  std::vector<Int_t> indices;
  for (const auto& [z, index] : ordered) {
    indices.push_back(index);
  }

  // Momentum from the kink, with the field integral along this track
  TrackCandidate refined = candidate;
  const auto [integral, centre] = fieldIntegral(candidate.upstream);
  const double kink = candidate.downstream.ty - candidate.upstream.ty;
  if (integral != 0. && kink != 0.) {
    const LineSegment& up = candidate.upstream;
    const double pz =
        std::min(std::abs(kKick * integral / kink), kMaxSeedMomentum);
    refined.momentum = pz * std::sqrt(1. + up.tx * up.tx + up.ty * up.ty);
    refined.charge = kink / integral > 0. ? 1 : -1;
  }
  Acts::BoundTrackParameters start =
      seed(refined, measurements[indices.front()]);

  for (int refit = 0;; ++refit) {
    if (static_cast<int>(indices.size()) < kMinFitMeasurements) {
      return -1;
    }
    const auto track = fitOnce(indices, start);
    if (!track) {
      return -1;
    }
    // Check each hit against the fitted track: take the side of the wire it
    // passes on, and drop hits that are too far from it
    bool changed = false;
    std::vector<std::pair<double, Int_t>> kept;
    const auto proxy = tracks.getTrack(*track);
    for (const auto state : proxy.trackStatesReversed()) {
      if (!state.hasUncalibratedSourceLink() || !state.hasSmoothed()) {
        continue;
      }
      const auto index = static_cast<Int_t>(
          state.getUncalibratedSourceLink().template get<std::size_t>());
      auto& m = measurements[index];
      const double predicted = state.smoothed()[Acts::eBoundLoc0];
      const double sigma =
          std::sqrt(m.variance + state.smoothedCovariance()(Acts::eBoundLoc0,
                                                            Acts::eBoundLoc0));
      if (std::abs(std::abs(predicted) - m.driftRadius) >
          kOutlierPull * sigma) {
        changed = true;
        continue;
      }
      const int side = predicted >= 0. ? 1 : -1;
      if (side != m.sign && std::abs(predicted) > std::sqrt(m.variance)) {
        m.sign = side;
        changed = true;
      }
      kept.emplace_back(m.wire->z, index);
    }
    if (!changed || refit == kMaxRefits) {
      trackMeasurements.push_back(indices);
      return static_cast<Int_t>(*track);
    }
    // Refit from the fitted parameters, with the seed uncertainties so the
    // previous fit does not bias the next
    auto params = proxy.createParametersAtReference();
    start = Acts::BoundTrackParameters(
        params.referenceSurface().getSharedPtr(), params.parameters(),
        seed(refined, measurements[indices.front()]).covariance(),
        params.particleHypothesis());
    tracks.removeTrack(*track);
    std::sort(kept.begin(), kept.end());
    indices.clear();
    for (const auto& [z, index] : kept) {
      indices.push_back(index);
    }
  }
}

Int_t ActsStrawTracker::FindTracks() {
  auto& impl = *fImpl;
  std::vector<Int_t> all(impl.measurements.size());
  std::iota(all.begin(), all.end(), 0);
  const auto hits = impl.patRecHits(all);
  const auto candidates = impl.patRec->findTracks(hits);

  // Fit every candidate, then resolve the ambiguities between the fitted
  // tracks: best first, rejecting tracks that share too many hits with an
  // accepted one or fit badly
  struct Fitted {
    std::size_t candidate;
    double chi2PerNdf;
    std::vector<Int_t> measurements;
  };
  std::vector<Fitted> fitted;
  for (std::size_t i = 0; i < candidates.size(); ++i) {
    const Int_t track = impl.fit(candidates[i], hits);
    if (track < 0) {
      continue;
    }
    const auto proxy = impl.tracks.getTrack(track);
    if (proxy.nDoF() > 0) {
      fitted.push_back(
          {i, proxy.chi2() / proxy.nDoF(), impl.trackMeasurements[track]});
    }
  }
  const auto rank = [](const Fitted& f) {
    return f.chi2PerNdf -
           kTrackHitWeight * static_cast<double>(f.measurements.size());
  };
  std::sort(fitted.begin(), fitted.end(),
            [&](const auto& a, const auto& b) { return rank(a) < rank(b); });
  std::vector<const Fitted*> accepted;
  for (const auto& f : fitted) {
    if (f.chi2PerNdf > kMaxTrackChi2PerNdf ||
        f.measurements.size() < kMinTrackHits) {
      continue;
    }
    const bool conflict =
        std::any_of(accepted.begin(), accepted.end(), [&](const Fitted* a) {
          int shared = 0;
          for (const Int_t m : f.measurements) {
            shared +=
                std::count(a->measurements.begin(), a->measurements.end(), m);
          }
          const auto shorter =
              std::min(f.measurements.size(), a->measurements.size());
          return shared > kMaxSharedFraction * static_cast<double>(shorter);
        });
    if (!conflict) {
      accepted.push_back(&f);
    }
  }
  // Refit the accepted tracks into an empty container, in candidate order,
  // so the track indices are contiguous
  std::sort(accepted.begin(), accepted.end(),
            [](const Fitted* a, const Fitted* b) {
              return a->candidate < b->candidate;
            });
  impl.tracks.clear();
  impl.trackMeasurements.clear();
  for (const Fitted* f : accepted) {
    impl.fit(candidates[f->candidate], hits);
  }
  return GetNTracks();
}

Int_t ActsStrawTracker::FitCandidate(const std::vector<Int_t>& measurements) {
  auto& impl = *fImpl;
  const auto hits = impl.patRecHits(measurements);
  const auto candidate = impl.patRec->fitCandidate(hits);
  return candidate ? impl.fit(*candidate, hits) : -1;
}

std::vector<Int_t> ActsStrawTracker::GetTrackMeasurements(Int_t track) const {
  if (track < 0 ||
      static_cast<std::size_t>(track) >= fImpl->trackMeasurements.size()) {
    throw std::out_of_range("ActsStrawTracker: track index out of range");
  }
  return fImpl->trackMeasurements[track];
}

Int_t ActsStrawTracker::GetNTracks() const {
  return static_cast<Int_t>(fImpl->tracks.size());
}

RecoTrack ActsStrawTracker::GetTrack(Int_t track) const {
  const auto& impl = *fImpl;
  const auto params = impl.trackParameters(track);
  const auto proxy = impl.tracks.getTrack(track);

  std::vector<Double_t> residuals;
  std::vector<Double_t> pulls;
  for (const auto state : proxy.trackStatesReversed()) {
    if (!state.hasCalibrated() || !state.hasSmoothed()) {
      continue;
    }
    const double measured = state.template calibrated<1>()(0);
    const double variance = state.template calibratedCovariance<1>()(0, 0);
    const double smoothed = state.smoothed()[Acts::eBoundLoc0];
    const double smoothedVariance =
        state.smoothedCovariance()(Acts::eBoundLoc0, Acts::eBoundLoc0);
    const double residual = measured - smoothed;
    // Residuals of smoothed states have variance V - HCH^T
    const double residualVariance = variance - smoothedVariance;
    residuals.push_back(residual / ActsFrame::kShipLength);
    pulls.push_back(
        residualVariance > 0. ? residual / std::sqrt(residualVariance) : 0.);
  }
  std::reverse(residuals.begin(), residuals.end());
  std::reverse(pulls.begin(), pulls.end());

  const Acts::Vector3 position =
      ActsFrame::positionToShip(params.position(impl.gctx));
  const Acts::Vector3 momentum = ActsFrame::momentumToShip(params.momentum());
  return RecoTrack(TVector3(position.x(), position.y(), position.z()),
                   TVector3(momentum.x(), momentum.y(), momentum.z()),
                   static_cast<Int_t>(std::lround(params.charge())),
                   upperTriangle<6>(shipCovariance(params, impl.gctx)),
                   proxy.chi2(), proxy.nDoF(), proxy.nMeasurements(),
                   std::move(residuals), std::move(pulls));
}

Bool_t ActsStrawTracker::FitVertex(const std::vector<Int_t>& tracks,
                                   RecoVertex& vertex) const {
  const auto& impl = *fImpl;
  if (tracks.size() < 2) {
    return false;
  }
  std::vector<Acts::BoundTrackParameters> fitted;
  for (const Int_t track : tracks) {
    fitted.push_back(impl.trackParameters(track));
  }

  // As in the GenFit vertexing: start from the closest approach of the
  // straight tracks, then extrapolate them through the field to the plane of
  // constant z through the current estimate, and take the closest approach
  // of their tangents there, until it no longer moves
  Acts::Vector3 point = vertexSeed(fitted, impl.gctx);
  std::vector<Acts::BoundTrackParameters> atPlane;
  for (int iteration = 0; iteration < kVertexIterations; ++iteration) {
    const auto plane = constantZPlane(point);
    atPlane.clear();
    for (const auto& params : fitted) {
      auto extrapolated = impl.extrapolate(impl.extrapolator, params, *plane);
      if (!extrapolated) {
        return false;
      }
      atPlane.push_back(std::move(*extrapolated));
    }
    const Acts::Vector3 next = closestPoint(tangents(atPlane, impl.gctx));
    if (!next.allFinite()) {
      return false;
    }
    const double step = (next - point).norm();
    point = next;
    if (step < kVertexTolerance) {
      break;
    }
  }

  // Covariance of the vertex (and of the DOCA) from the covariances of the
  // tangents' positions and directions on the plane, by linear propagation
  // with numerical derivatives
  const auto base = tangents(atPlane, impl.gctx);
  const int nPar = 4;  // loc0, loc1, phi, theta
  const int n = static_cast<int>(atPlane.size());
  Eigen::MatrixXd jacobian = Eigen::MatrixXd::Zero(4, nPar * n);
  Eigen::MatrixXd covariance = Eigen::MatrixXd::Zero(nPar * n, nPar * n);
  const bool twoTracks = n == 2;
  const double baseDoca = twoTracks
                              ? lineDistance(base[0].first, base[0].second,
                                             base[1].first, base[1].second)
                              : 0.;
  for (int i = 0; i < n; ++i) {
    const auto& cov = atPlane[i].covariance().value();
    covariance.block(nPar * i, nPar * i, nPar, nPar) =
        cov.topLeftCorner(nPar, nPar);
    for (int k = 0; k < nPar; ++k) {
      const double epsilon = std::max(1e-3 * std::sqrt(cov(k, k)), 1e-12);
      Acts::BoundVector shifted = atPlane[i].parameters();
      shifted[k] += epsilon;
      auto lines = base;
      lines[i] = tangent(atPlane[i].referenceSurface(), shifted, impl.gctx);
      jacobian.block(0, nPar * i + k, 3, 1) =
          (closestPoint(lines) - point) / epsilon;
      if (twoTracks) {
        jacobian(3, nPar * i + k) =
            (lineDistance(lines[0].first, lines[0].second, lines[1].first,
                          lines[1].second) -
             baseDoca) /
            epsilon;
      }
    }
  }
  const Eigen::MatrixXd propagated =
      jacobian * covariance * jacobian.transpose();
  const Acts::SquareMatrix3 actsCovariance = propagated.topLeftCorner(3, 3);

  const Acts::RotationMatrix3 rotation = ActsFrame::toShipRotation();
  const Acts::Vector3 position = ActsFrame::positionToShip(point);
  const Acts::SquareMatrix3 positionCovariance =
      rotation * actsCovariance * rotation.transpose() /
      (ActsFrame::kShipLength * ActsFrame::kShipLength);
  // Fit quality: the DOCA against its uncertainty for two tracks
  const double docaVariance = propagated(3, 3);
  const double chi2 =
      twoTracks && docaVariance > 0. ? baseDoca * baseDoca / docaVariance : 0.;
  vertex = RecoVertex(TVector3(position.x(), position.y(), position.z()),
                      upperTriangle<3>(positionCovariance), chi2,
                      twoTracks ? 1. : 2. * n - 3.);

  for (int i = 0; i < n; ++i) {
    const Acts::Vector3 momentum =
        ActsFrame::momentumToShip(atPlane[i].momentum());
    vertex.AddTrack(tracks[i],
                    TVector3(momentum.x(), momentum.y(), momentum.z()),
                    upperTriangle<3>(shipMomentumCovariance(atPlane[i])));
  }
  if (twoTracks) {
    vertex.SetDoca(baseDoca / ActsFrame::kShipLength);
  }
  return true;
}

Double_t ActsStrawTracker::DistanceToHit(Int_t track,
                                         const TVector3& hit) const {
  const auto& impl = *fImpl;
  // Plane of constant z centred on the hit
  const auto plane =
      constantZPlane(ActsFrame::positionToActs(hit.X(), hit.Y(), hit.Z()));

  const auto result =
      impl.extrapolate(impl.extrapolator, impl.trackParameters(track), *plane);
  if (!result) {
    return -1.;
  }
  const auto& local = result->parameters();
  return std::hypot(local[Acts::eBoundLoc0], local[Acts::eBoundLoc1]) /
         ActsFrame::kShipLength;
}

Int_t ActsStrawTracker::GetNStraws() const {
  return static_cast<Int_t>(fImpl->straws.size());
}

}  // namespace SHiP
