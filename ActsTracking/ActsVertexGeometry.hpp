// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#ifndef ACTSTRACKING_ACTSVERTEXGEOMETRY_HPP_
#define ACTSTRACKING_ACTSVERTEXGEOMETRY_HPP_

#include <algorithm>
#include <cmath>
#include <memory>
#include <utility>
#include <vector>

#include "Acts/Definitions/Algebra.hpp"
#include "Acts/Definitions/TrackParametrization.hpp"
#include "Acts/Definitions/Units.hpp"
#include "Acts/EventData/BoundTrackParameters.hpp"
#include "Acts/Geometry/GeometryContext.hpp"
#include "Acts/Surfaces/PlaneSurface.hpp"
#include "Acts/Utilities/UnitVectors.hpp"

/// Straight-line geometry for the vertex fit and the vertex seeds, in the
/// ACTS frame (see ActsFrame.hpp)
namespace SHiP::ActsVertexGeometry {

/// Range of the vertex seed along the beam (ACTS x)
inline constexpr double kVertexSeedMinX = 20 * Acts::UnitConstants::m;
inline constexpr double kVertexSeedMaxX = 90 * Acts::UnitConstants::m;

/// A straight line: a point and a unit direction
using Tangent = std::pair<Acts::Vector3, Acts::Vector3>;

/// Tangent of a track with the given bound parameters on a surface
inline Tangent tangent(const Acts::Surface& surface,
                       const Acts::BoundVector& params,
                       const Acts::GeometryContext& gctx) {
  const Acts::Vector3 direction = Acts::makeDirectionFromPhiTheta(
      params[Acts::eBoundPhi], params[Acts::eBoundTheta]);
  return {surface.localToGlobal(
              gctx,
              Acts::Vector2(params[Acts::eBoundLoc0], params[Acts::eBoundLoc1]),
              direction),
          direction};
}

inline std::vector<Tangent> tangents(
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
inline Acts::Vector3 closestPoint(const std::vector<Tangent>& lines) {
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
inline Acts::Vector3 vertexSeed(
    const std::vector<Acts::BoundTrackParameters>& tracks,
    const Acts::GeometryContext& gctx) {
  Acts::Vector3 seed = closestPoint(tangents(tracks, gctx));
  if (!seed.allFinite()) {
    seed = Acts::Vector3(0.5 * (kVertexSeedMinX + kVertexSeedMaxX), 0., 0.);
  }
  seed.x() = std::clamp(seed.x(), kVertexSeedMinX, kVertexSeedMaxX);
  return seed;
}

/// Plane of constant z (SHiP), i.e. constant x (ACTS), through a point
inline std::shared_ptr<Acts::PlaneSurface> constantZPlane(
    const Acts::Vector3& point) {
  Acts::Transform3 transform = Acts::Transform3::Identity();
  transform.linear().col(0) = Acts::Vector3::UnitY();
  transform.linear().col(1) = Acts::Vector3::UnitZ();
  transform.linear().col(2) = Acts::Vector3::UnitX();
  transform.translation() = point;
  return Acts::Surface::makeShared<Acts::PlaneSurface>(transform);
}

/// Distance of closest approach between two straight lines
inline double lineDistance(const Acts::Vector3& p1, const Acts::Vector3& d1,
                           const Acts::Vector3& p2, const Acts::Vector3& d2) {
  const Acts::Vector3 delta = p1 - p2;
  const Acts::Vector3 normal = d1.cross(d2);
  if (normal.norm() > 1e-12) {
    return std::abs(delta.dot(normal)) / normal.norm();
  }
  return delta.cross(d1.normalized()).norm();
}

}  // namespace SHiP::ActsVertexGeometry

#endif  // ACTSTRACKING_ACTSVERTEXGEOMETRY_HPP_
