// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#include "ActsVertexing.hpp"

#include <cmath>
#include <limits>
#include <utility>

#include "Acts/MagneticField/NullBField.hpp"
#include "Acts/Propagator/Propagator.hpp"
#include "Acts/Propagator/StraightLineStepper.hpp"
#include "Acts/Propagator/VoidNavigator.hpp"
#include "Acts/Utilities/AnnealingUtility.hpp"
#include "Acts/Vertexing/AdaptiveMultiVertexFinder.hpp"
#include "Acts/Vertexing/AdaptiveMultiVertexFitter.hpp"
#include "Acts/Vertexing/HelicalTrackLinearizer.hpp"
#include "Acts/Vertexing/IVertexFinder.hpp"
#include "Acts/Vertexing/ImpactPointEstimator.hpp"
#include "Acts/Vertexing/TrackAtVertex.hpp"
#include "Acts/Vertexing/Vertex.hpp"
#include "Acts/Vertexing/VertexingOptions.hpp"
#include "ActsVertexGeometry.hpp"

namespace SHiP {

namespace {

using StraightPropagator =
    Acts::Propagator<Acts::StraightLineStepper, Acts::VoidNavigator>;

/// Largest impact parameter significance at the seed of a track added to a
/// vertex. The finder takes the seed position as exact, but a seed from two
/// tracks lies close to the better measured one, and the other track of a
/// true pair can be more than 5 standard deviations from it. The fit itself
/// then decides with the annealed track weights.
constexpr double kTracksMaxSignificance = 10.;
/// Smallest significance of the distance between two vertices that are kept
/// apart
constexpr double kMaxMergeVertexSignificance = 3.;
/// Chi2 of a track against a vertex at which its weight in the annealed fit
/// falls to 0.5, and the largest chi2 of a track compatible with a vertex.
/// The ACTS defaults (9 and 18.42) leave out 7% of the tracks of 8-track
/// vertices and lose 2% of HNL decays; with the cut-off at 25, 1.5% and 0.8%.
/// The straw track errors are about 10% too small, which inflates chi2.
constexpr double kAnnealingCutOff = 25.;
constexpr double kMaxVertexChi2 = 40.;
/// Distance to the perigee surface at which the linearisation stops
/// propagating. The ACTS default of 1e-12 mm cannot be reached in double
/// precision tens of metres from the origin.
constexpr double kLinearizerTolerance = 1e-6 * Acts::UnitConstants::mm;

Acts::HelicalTrackLinearizer::Config linearizerConfig(
    std::shared_ptr<const Acts::BasePropagator> propagator) {
  // Without field, the linearisation is that of a straight line
  Acts::HelicalTrackLinearizer::Config config;
  config.propagator = std::move(propagator);
  config.targetTolerance = kLinearizerTolerance;
  return config;
}

/// Tracks within this many standard deviations of a seed refine it
constexpr double kSeedTrackSignificance = 5.;
/// Most refinements of a seed with the tracks near it
constexpr int kSeedRefinements = 5;

/// A track as a straight line, with the variances of its position across
/// the line at the reference surface and of its direction
struct SeedLine {
  Acts::Vector3 position;
  Acts::Vector3 direction;
  double positionVariance;
  double angleVariance;

  explicit SeedLine(const Acts::BoundTrackParameters& params,
                    const Acts::GeometryContext& gctx)
      : position(params.position(gctx)), direction(params.direction()) {
    const auto& cov = params.covariance().value();
    positionVariance = 0.5 * (cov(Acts::eBoundLoc0, Acts::eBoundLoc0) +
                              cov(Acts::eBoundLoc1, Acts::eBoundLoc1));
    angleVariance = 0.5 * (cov(Acts::eBoundPhi, Acts::eBoundPhi) +
                           cov(Acts::eBoundTheta, Acts::eBoundTheta));
  }

  /// Vector from the line to a point, across the line
  Acts::Vector3 residual(const Acts::Vector3& point) const {
    const Acts::Vector3 delta = point - position;
    return delta - delta.dot(direction) * direction;
  }

  /// Variance of the position across the line, near `point`
  double variance(const Acts::Vector3& point) const {
    return positionVariance + (point - position).squaredNorm() * angleVariance;
  }
};

/// Point closest to the lines, each weighted by the inverse variance of its
/// position near `near`, and its covariance
std::pair<Acts::Vector3, Acts::SquareMatrix3> weightedClosestPoint(
    const std::vector<const SeedLine*>& lines, const Acts::Vector3& near) {
  Acts::SquareMatrix3 a = Acts::SquareMatrix3::Zero();
  Acts::Vector3 b = Acts::Vector3::Zero();
  for (const SeedLine* line : lines) {
    const Acts::SquareMatrix3 projection =
        (Acts::SquareMatrix3::Identity() -
         line->direction * line->direction.transpose()) /
        line->variance(near);
    a += projection;
    b += projection * line->position;
  }
  return {a.colPivHouseholderQr().solve(b), a.inverse()};
}

bool inSeedRange(const Acts::Vector3& point) {
  return point.allFinite() &&
         point.x() >= ActsVertexGeometry::kVertexSeedMinX &&
         point.x() <= ActsVertexGeometry::kVertexSeedMaxX;
}

/// Seeds a vertex from the pair of remaining tracks that pass closest to
/// each other, relative to their uncertainties, taken as straight lines. The
/// seed is then refined with the tracks that pass near it: a seed from two
/// tracks at a small opening angle is poorly known along the beam, and
/// tracks of the same vertex might otherwise not be added to it. Unlike the
/// ACTS seed finders, it does not assume a beam axis.
class ClosestPairSeedFinder final : public Acts::IVertexFinder {
 public:
  struct State {};

  Acts::Result<std::vector<Acts::Vertex>> find(
      const std::vector<Acts::InputTrack>& tracks,
      const Acts::VertexingOptions& options,
      IVertexFinder::State& /*state*/) const override {
    std::vector<SeedLine> lines;
    lines.reserve(tracks.size());
    for (const auto& track : tracks) {
      lines.emplace_back(Acts::InputTrack::extractParameters(track),
                         options.geoContext);
    }

    double bestChi2 = std::numeric_limits<double>::infinity();
    Acts::Vector3 seed = Acts::Vector3::Zero();
    std::pair<std::size_t, std::size_t> bestPair{0, 0};
    for (std::size_t i = 0; i < lines.size(); ++i) {
      for (std::size_t j = i + 1; j < lines.size(); ++j) {
        const Acts::Vector3 point = ActsVertexGeometry::closestPoint(
            {{lines[i].position, lines[i].direction},
             {lines[j].position, lines[j].direction}});
        if (!inSeedRange(point)) {
          continue;
        }
        const double distance = ActsVertexGeometry::lineDistance(
            lines[i].position, lines[i].direction, lines[j].position,
            lines[j].direction);
        const double chi2 =
            distance * distance /
            (lines[i].variance(point) + lines[j].variance(point));
        if (chi2 < bestChi2) {
          bestChi2 = chi2;
          seed = point;
          bestPair = {i, j};
        }
      }
    }
    if (!std::isfinite(bestChi2)) {
      return std::vector<Acts::Vertex>{};
    }

    // Add the tracks compatible with the seed, given the uncertainty of both,
    // and refit the seed with them, until no more tracks are added
    std::vector<const SeedLine*> near{&lines[bestPair.first],
                                      &lines[bestPair.second]};
    auto [point, covariance] = weightedClosestPoint(near, seed);
    for (int refinement = 0; refinement < kSeedRefinements; ++refinement) {
      std::vector<const SeedLine*> compatible;
      for (const auto& line : lines) {
        const Acts::Vector3 residual = line.residual(point);
        const double distance2 = residual.squaredNorm();
        const double seedVariance =
            distance2 > 0. ? residual.dot(covariance * residual) / distance2
                           : 0.;
        if (distance2 < kSeedTrackSignificance * kSeedTrackSignificance *
                            (line.variance(point) + seedVariance)) {
          compatible.push_back(&line);
        }
      }
      if (compatible.size() < 2 || compatible == near) {
        break;
      }
      const auto [refined, refinedCovariance] =
          weightedClosestPoint(compatible, point);
      if (!inSeedRange(refined)) {
        break;
      }
      near = std::move(compatible);
      point = refined;
      covariance = refinedCovariance;
    }
    if (inSeedRange(point)) {
      seed = point;
    }
    return std::vector<Acts::Vertex>{Acts::Vertex(seed)};
  }

  IVertexFinder::State makeState(
      const Acts::MagneticFieldContext& /*mctx*/) const override {
    return IVertexFinder::State{State{}};
  }

  void setTracksToRemove(
      IVertexFinder::State& /*state*/,
      const std::vector<Acts::InputTrack>& /*removedTracks*/) const override {}
};

}  // namespace

struct ActsVertexFinder::Impl {
  explicit Impl(Acts::Logging::Level level)
      : propagator(std::make_shared<StraightPropagator>(
            Acts::StraightLineStepper(), Acts::VoidNavigator(),
            Acts::getDefaultLogger("VertexPropagator", level))),
        ipEstimator(Acts::ImpactPointEstimator::Config(propagator),
                    Acts::getDefaultLogger("ImpactPointEstimator", level)),
        linearizer(linearizerConfig(propagator),
                   Acts::getDefaultLogger("TrackLinearizer", level)),
        finder(makeFinder(level)) {}

  Acts::AdaptiveMultiVertexFinder makeFinder(Acts::Logging::Level level) {
    Acts::AdaptiveMultiVertexFitter::Config fitterConfig(ipEstimator);
    Acts::AnnealingUtility::Config annealing;
    annealing.cutOff = kAnnealingCutOff;
    fitterConfig.annealingTool = Acts::AnnealingUtility(annealing);
    // Refit the tracks at the vertex, for their momenta there
    fitterConfig.doSmoothing = true;
    fitterConfig.extractParameters
        .connect<&Acts::InputTrack::extractParameters>();
    fitterConfig.trackLinearizer
        .connect<&Acts::HelicalTrackLinearizer::linearizeTrack>(&linearizer);
    Acts::AdaptiveMultiVertexFitter fitter(
        std::move(fitterConfig),
        Acts::getDefaultLogger("AdaptiveMultiVertexFitter", level));

    Acts::AdaptiveMultiVertexFinder::Config config(
        std::move(fitter), std::make_shared<ClosestPairSeedFinder>(),
        ipEstimator, std::make_shared<Acts::NullBField>());
    // The finder skips tracks further than this from a vertex along ACTS z,
    // which is across the beam here
    config.tracksMaxZinterval = std::numeric_limits<double>::max();
    config.tracksMaxSignificance = kTracksMaxSignificance;
    config.maxMergeVertexSignificance = kMaxMergeVertexSignificance;
    // Compare vertices in 3D, not along ACTS z only
    config.doFullSplitting = true;
    config.useTime = false;
    config.addSingleTrackVertices = false;
    config.maxVertexChi2 = kMaxVertexChi2;
    config.extractParameters.connect<&Acts::InputTrack::extractParameters>();
    return Acts::AdaptiveMultiVertexFinder(
        std::move(config),
        Acts::getDefaultLogger("AdaptiveMultiVertexFinder", level));
  }

  std::shared_ptr<const StraightPropagator> propagator;
  Acts::ImpactPointEstimator ipEstimator;
  Acts::HelicalTrackLinearizer linearizer;
  Acts::AdaptiveMultiVertexFinder finder;
};

ActsVertexFinder::ActsVertexFinder(Acts::Logging::Level level)
    : fImpl(std::make_unique<Impl>(level)) {}

ActsVertexFinder::~ActsVertexFinder() = default;

std::vector<FoundVertex> ActsVertexFinder::find(
    const std::vector<Acts::BoundTrackParameters>& tracks,
    const Acts::GeometryContext& gctx,
    const Acts::MagneticFieldContext& mctx) const {
  std::vector<FoundVertex> found;
  if (tracks.size() < 2) {
    return found;
  }
  std::vector<Acts::InputTrack> inputs;
  inputs.reserve(tracks.size());
  for (const auto& track : tracks) {
    inputs.emplace_back(&track);
  }
  const Acts::VertexingOptions options(gctx, mctx);
  auto state = fImpl->finder.makeState(mctx);
  auto result = fImpl->finder.find(inputs, options, state);
  if (!result.ok()) {
    return found;
  }
  for (const auto& vertex : *result) {
    FoundVertex out{vertex.position(),
                    vertex.covariance(),
                    vertex.fitQuality().first,
                    vertex.fitQuality().second,
                    {}};
    for (const auto& track : vertex.tracks()) {
      const auto* original =
          track.originalParams.as<Acts::BoundTrackParameters>();
      out.tracks.push_back({static_cast<std::size_t>(original - tracks.data()),
                            track.trackWeight, track.fittedParams});
    }
    if (out.tracks.size() >= 2) {
      found.push_back(std::move(out));
    }
  }
  return found;
}

}  // namespace SHiP
