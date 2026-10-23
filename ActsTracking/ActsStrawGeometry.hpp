// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#ifndef ACTSTRACKING_ACTSSTRAWGEOMETRY_HPP_
#define ACTSTRACKING_ACTSSTRAWGEOMETRY_HPP_

#include <memory>
#include <unordered_map>

#include "Acts/Surfaces/Surface.hpp"

class TGeoManager;

namespace SHiP {

/// A straw wire in the SHiP frame (cm), for pattern recognition
struct StrawWire {
  int detectorId;
  int station;
  int view;
  int layer;
  /// Wire centre
  double x, y, z;
  /// Unit vector along the wire
  double dx, dy, dz;
  /// Inner radius of the straw
  double radius;
  /// Half-length of the straw
  double halfLength;
};

/// ACTS straw surfaces of the strawtubes spectrometer.
///
/// Built from the "straw" volumes of the loaded TGeo geometry, so the surfaces
/// follow the geometry the event was simulated with. Each straw is looked up
/// by its strawtubes detector ID.
class ActsStrawGeometry {
 public:
  explicit ActsStrawGeometry(const TGeoManager& geometry);

  /// The straw surface for a strawtubes detector ID, or nullptr if unknown
  const Acts::Surface* surface(int detectorId) const;
  /// The wire for a strawtubes detector ID, or nullptr if unknown
  const StrawWire* wire(int detectorId) const;
  const std::unordered_map<int, StrawWire>& wires() const { return m_wires; }
  std::size_t size() const { return m_surfaces.size(); }

 private:
  std::unordered_map<int, std::shared_ptr<Acts::Surface>> m_surfaces;
  std::unordered_map<int, StrawWire> m_wires;
};

}  // namespace SHiP

#endif  // ACTSTRACKING_ACTSSTRAWGEOMETRY_HPP_
