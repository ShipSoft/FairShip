// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#ifndef ACTSTRACKING_ACTSVERTEXING_HPP_
#define ACTSTRACKING_ACTSVERTEXING_HPP_

#include <cstddef>
#include <memory>
#include <vector>

#include "Acts/Definitions/Algebra.hpp"
#include "Acts/EventData/BoundTrackParameters.hpp"
#include "Acts/Geometry/GeometryContext.hpp"
#include "Acts/MagneticField/MagneticFieldContext.hpp"
#include "Acts/Utilities/Logger.hpp"

namespace SHiP {

/// A track of a found vertex
struct VertexTrack {
  /// Index of the track in the input of ActsVertexFinder::find
  std::size_t index;
  /// Weight of the track in the adaptive fit, between 0 and 1
  double weight;
  /// Track parameters refitted with the vertex constraint
  Acts::BoundTrackParameters atVertex;
};

/// A vertex found by ActsVertexFinder, in the ACTS frame
struct FoundVertex {
  Acts::Vector3 position;
  Acts::SquareMatrix3 covariance;
  double chi2;
  double nDoF;
  std::vector<VertexTrack> tracks;
};

/// Finds any number of vertices among tracks with the ACTS adaptive
/// multi-vertex finder.
///
/// The tracks are taken as straight lines: the finder works in the decay
/// volume, which has no field, and the caller has to bring the tracks there
/// through the field and the material. The ACTS seed finders and part of the
/// finder assume a beam along ACTS z, but the beam is along ACTS x in the SHiP
/// reconstruction frame (ActsFrame.hpp). The seeds therefore come from the
/// closest pair of tracks, and the finder is configured not to cut on z.
class ActsVertexFinder {
 public:
  explicit ActsVertexFinder(
      Acts::Logging::Level level = Acts::Logging::WARNING);
  ~ActsVertexFinder();
  ActsVertexFinder(const ActsVertexFinder&) = delete;
  ActsVertexFinder& operator=(const ActsVertexFinder&) = delete;

  /// Vertices with at least two tracks; empty if none is found or the
  /// finder fails
  std::vector<FoundVertex> find(
      const std::vector<Acts::BoundTrackParameters>& tracks,
      const Acts::GeometryContext& gctx,
      const Acts::MagneticFieldContext& mctx) const;

 private:
  struct Impl;
  std::unique_ptr<Impl> fImpl;
};

}  // namespace SHiP

#endif  // ACTSTRACKING_ACTSVERTEXING_HPP_
