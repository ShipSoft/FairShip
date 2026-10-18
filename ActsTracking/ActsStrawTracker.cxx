// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#include "ActsStrawTracker.h"

#include <algorithm>
#include <array>
#include <cmath>
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
#include "Acts/MagneticField/NullBField.hpp"
#include "Acts/Propagator/DirectNavigator.hpp"
#include "Acts/Propagator/EigenStepper.hpp"
#include "Acts/Propagator/Propagator.hpp"
#include "Acts/Propagator/VoidNavigator.hpp"
#include "Acts/Surfaces/PerigeeSurface.hpp"
#include "Acts/Surfaces/PlaneSurface.hpp"
#include "Acts/TrackFitting/GainMatrixSmoother.hpp"
#include "Acts/TrackFitting/GainMatrixUpdater.hpp"
#include "Acts/TrackFitting/KalmanFitter.hpp"
#include "Acts/Utilities/CalibrationContext.hpp"
#include "Acts/Utilities/Logger.hpp"
#include "Acts/Vertexing/FullBilloirVertexFitter.hpp"
#include "Acts/Vertexing/HelicalTrackLinearizer.hpp"
#include "Acts/Vertexing/TrackAtVertex.hpp"
#include "Acts/Vertexing/Vertex.hpp"
#include "Acts/Vertexing/VertexingOptions.hpp"
#include "ActsFrame.hpp"
#include "ActsShipField.hpp"
#include "ActsStrawGeometry.hpp"
#include "TGeoManager.h"

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

/// Seed uncertainties of the track fit
constexpr double kSeedSigmaLoc0 = 5 * u::mm;
constexpr double kSeedSigmaLoc1 = 50 * u::mm;
constexpr double kSeedSigmaAngle = 0.05;
constexpr double kSeedRelativeSigmaP = 0.2;
// The time is not measured, so it is effectively left free
constexpr double kSeedSigmaTime = 1e9;

/// Range of the vertex seed along the beam (ACTS x)
constexpr double kVertexSeedMinX = 20 * u::m;
constexpr double kVertexSeedMaxX = 90 * u::m;
/// Field below which the vertex fit treats tracks as straight lines
constexpr double kNegligibleField = 1e-6 * u::T;

constexpr double kPathLimit = 100 * u::m;

struct StrawMeasurement {
  const Acts::Surface* surface;
  double driftRadius;
  double variance;
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

/// Closest point between two lines, or the projection for parallel lines
Acts::Vector3 vertexSeed(const std::vector<Acts::BoundTrackParameters>& tracks,
                         const Acts::GeometryContext& gctx) {
  Acts::SquareMatrix3 a = Acts::SquareMatrix3::Zero();
  Acts::Vector3 b = Acts::Vector3::Zero();
  for (const auto& track : tracks) {
    const Acts::Vector3 direction = track.direction();
    const Acts::SquareMatrix3 projection =
        Acts::SquareMatrix3::Identity() - direction * direction.transpose();
    a += projection;
    b += projection * track.position(gctx);
  }
  Acts::Vector3 seed = a.colPivHouseholderQr().solve(b);
  if (!seed.allFinite()) {
    seed = Acts::Vector3(0.5 * (kVertexSeedMinX + kVertexSeedMaxX), 0., 0.);
  }
  seed.x() = std::clamp(seed.x(), kVertexSeedMinX, kVertexSeedMaxX);
  return seed;
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
  Impl(const TGeoManager& geometry, TVirtualMagField* shipField)
      : straws(geometry),
        field(std::make_shared<ActsShipField>(shipField)),
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
    state.template calibrated<1>()(0) = measurement.driftRadius;
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
  std::shared_ptr<const ActsShipField> field;
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
}

Int_t ActsStrawTracker::AddMeasurement(Int_t detectorId, Double_t driftRadius,
                                       Double_t resolution) {
  const Acts::Surface* surface = fImpl->straws.surface(detectorId);
  if (surface == nullptr) {
    return -1;
  }
  const double sigma = resolution * ActsFrame::kShipLength;
  fImpl->measurements.push_back(
      {surface, driftRadius * ActsFrame::kShipLength, sigma * sigma});
  return static_cast<Int_t>(fImpl->measurements.size() - 1);
}

Int_t ActsStrawTracker::FitTrack(const std::vector<Int_t>& measurements,
                                 const TVector3& seedPosition,
                                 const TVector3& seedMomentum, Int_t charge) {
  auto& impl = *fImpl;
  if (measurements.empty() || charge == 0 || seedMomentum.Mag() <= 0.) {
    return -1;
  }
  std::vector<Acts::SourceLink> sourceLinks;
  std::vector<const Acts::Surface*> surfaces;
  for (const Int_t index : measurements) {
    if (index < 0 ||
        static_cast<std::size_t>(index) >= impl.measurements.size()) {
      throw std::out_of_range("ActsStrawTracker: measurement out of range");
    }
    sourceLinks.emplace_back(static_cast<std::size_t>(index));
    surfaces.push_back(impl.measurements[index].surface);
  }

  // Seed on the surface of the first measurement
  const Acts::Surface& seedSurface = *surfaces.front();
  const Acts::Vector3 position = ActsFrame::positionToActs(
      seedPosition.X(), seedPosition.Y(), seedPosition.Z());
  const Acts::Vector3 momentum = ActsFrame::momentumToActs(
      seedMomentum.X(), seedMomentum.Y(), seedMomentum.Z());
  const Acts::Vector3 direction = momentum.normalized();
  const auto hypothesis = Acts::ParticleHypothesis::muon();
  const double qOverP =
      hypothesis.qOverP(momentum.norm(), static_cast<double>(charge));

  // The seed is generally not on the straw, so take its point of closest
  // approach and the local coordinates there
  const auto intersection =
      seedSurface.intersect(impl.gctx, position, direction).closest();
  const Acts::Vector3 onSurface =
      intersection.isValid() ? intersection.position() : position;
  auto local = seedSurface.globalToLocal(impl.gctx, onSurface, direction);
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
  const Acts::BoundTrackParameters seed(seedSurface.getSharedPtr(), parameters,
                                        covariance, hypothesis);

  Acts::PropagatorPlainOptions propagatorOptions(impl.gctx, impl.mctx);
  Acts::KalmanFitterOptions<Trajectory> options(
      impl.gctx, impl.mctx, std::cref(impl.cctx), impl.extensions,
      propagatorOptions, &seedSurface);
  options.referenceSurfaceStrategy = Acts::TrackExtrapolationStrategy::first;

  const std::size_t nTracksBefore = impl.tracks.size();
  auto result = impl.fitter.fit(sourceLinks.begin(), sourceLinks.end(), seed,
                                options, surfaces, impl.tracks);
  if (!result.ok() || !result.value().hasReferenceSurface()) {
    // A failed fit may leave a partial track behind. Drop it, so that track
    // indices stay contiguous.
    while (impl.tracks.size() > nTracksBefore) {
      impl.tracks.removeTrack(impl.tracks.size() - 1);
    }
    return -1;
  }
  return static_cast<Int_t>(result.value().index());
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
  const Acts::Vector3 seed = vertexSeed(fitted, impl.gctx);

  // Where the field at the seed is negligible, the helical linearisation is
  // ill-defined, so treat the tracks as straight lines there
  std::shared_ptr<const Acts::MagneticFieldProvider> field = impl.field;
  auto cache = field->makeCache(impl.mctx);
  const auto seedField = field->getField(seed, cache);
  if (seedField.ok() && seedField.value().norm() < kNegligibleField) {
    field = std::make_shared<Acts::NullBField>();
  }
  auto propagator = std::make_shared<Extrapolator>(
      Stepper(field), Acts::VoidNavigator(),
      Acts::getDefaultLogger("VertexPropagator", Acts::Logging::WARNING));

  // Start the fit from the track parameters at the seed
  const auto seedSurface =
      Acts::Surface::makeShared<Acts::PerigeeSurface>(seed);
  std::vector<Acts::BoundTrackParameters> atSeed;
  for (const auto& params : fitted) {
    auto extrapolated = impl.extrapolate(*propagator, params, *seedSurface);
    if (!extrapolated) {
      return false;
    }
    atSeed.push_back(std::move(*extrapolated));
  }

  Acts::HelicalTrackLinearizer::Config linearizerConfig;
  linearizerConfig.bField = field;
  linearizerConfig.propagator = propagator;
  linearizerConfig.targetTolerance = 1e-4;
  const Acts::HelicalTrackLinearizer linearizer(linearizerConfig);

  Acts::FullBilloirVertexFitter::Config fitterConfig;
  fitterConfig.maxIterations = 200;
  fitterConfig.extractParameters
      .connect<&Acts::InputTrack::extractParameters>();
  fitterConfig.trackLinearizer
      .connect<&Acts::HelicalTrackLinearizer::linearizeTrack>(&linearizer);
  const Acts::FullBilloirVertexFitter fitter(
      fitterConfig,
      Acts::getDefaultLogger("VertexFitter", Acts::Logging::WARNING));

  std::vector<Acts::InputTrack> inputTracks;
  for (const auto& params : atSeed) {
    inputTracks.emplace_back(&params);
  }
  // A loose constraint at the seed only sets the starting point of the fit
  Acts::Vertex constraint(seed);
  constraint.setFullCovariance(Acts::SquareMatrix4::Identity() * 1e6);
  const Acts::VertexingOptions vertexingOptions(impl.gctx, impl.mctx,
                                                constraint);
  auto fieldCache = field->makeCache(impl.mctx);
  const auto result = fitter.fit(inputTracks, vertexingOptions, fieldCache);
  if (!result.ok()) {
    return false;
  }
  const Acts::Vertex& fittedVertex = result.value();

  const Acts::RotationMatrix3 rotation = ActsFrame::toShipRotation();
  const Acts::Vector3 position =
      ActsFrame::positionToShip(fittedVertex.position());
  const Acts::SquareMatrix3 positionCovariance =
      rotation * fittedVertex.covariance() * rotation.transpose() /
      (ActsFrame::kShipLength * ActsFrame::kShipLength);
  const auto [chi2, nDoF] = fittedVertex.fitQuality();
  vertex = RecoVertex(TVector3(position.x(), position.y(), position.z()),
                      upperTriangle<3>(positionCovariance), chi2, nDoF);

  for (const auto& trackAtVertex : fittedVertex.tracks()) {
    const auto* original =
        trackAtVertex.originalParams.as<Acts::BoundTrackParameters>();
    const auto index = static_cast<std::size_t>(original - atSeed.data());
    if (original == nullptr || index >= atSeed.size()) {
      return false;
    }
    const auto& params = trackAtVertex.fittedParams;
    const Acts::Vector3 momentum = ActsFrame::momentumToShip(params.momentum());
    vertex.AddTrack(tracks[index],
                    TVector3(momentum.x(), momentum.y(), momentum.z()),
                    upperTriangle<3>(shipMomentumCovariance(params)));
  }

  if (atSeed.size() == 2) {
    const double doca =
        lineDistance(atSeed[0].position(impl.gctx), atSeed[0].direction(),
                     atSeed[1].position(impl.gctx), atSeed[1].direction());
    vertex.SetDoca(doca / ActsFrame::kShipLength);
  }
  return true;
}

Double_t ActsStrawTracker::DistanceToHit(Int_t track,
                                         const TVector3& hit) const {
  const auto& impl = *fImpl;
  // Plane of constant z (SHiP), i.e. constant x (ACTS), centred on the hit
  Acts::Transform3 transform = Acts::Transform3::Identity();
  transform.linear().col(0) = Acts::Vector3::UnitY();
  transform.linear().col(1) = Acts::Vector3::UnitZ();
  transform.linear().col(2) = Acts::Vector3::UnitX();
  transform.translation() =
      ActsFrame::positionToActs(hit.X(), hit.Y(), hit.Z());
  const auto plane = Acts::Surface::makeShared<Acts::PlaneSurface>(transform);

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
