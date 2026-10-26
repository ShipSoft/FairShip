// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#ifndef ACTSTRACKING_ACTSSTRAWGEOMETRY_HPP_
#define ACTSTRACKING_ACTSSTRAWGEOMETRY_HPP_

#include <memory>
#include <unordered_map>
#include <vector>

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

/// A plane of constant z that carries the material of a slice of the
/// detector outside the straws (decay volume gas, windows, air between and
/// inside the stations)
struct PassivePlane {
  /// Position along the beam, SHiP frame (cm)
  double z;
  /// Thickness in radiation lengths at normal incidence
  double thicknessInX0;
  std::shared_ptr<Acts::Surface> surface;
};

/// ACTS straw surfaces of the strawtubes spectrometer.
///
/// Built from the "straw" volumes of the loaded TGeo geometry, so the surfaces
/// follow the geometry the event was simulated with. Each straw is looked up
/// by its strawtubes detector ID.
///
/// The material outside the straws is read from the TGeo geometry along
/// lines parallel to the beam and lumped onto passive planes, from the
/// upstream end of the decay volume to the last station.
class ActsStrawGeometry {
 public:
  explicit ActsStrawGeometry(const TGeoManager& geometry);

  /// The straw surface for a strawtubes detector ID, or nullptr if unknown
  const Acts::Surface* surface(int detectorId) const;
  /// The wire for a strawtubes detector ID, or nullptr if unknown
  const StrawWire* wire(int detectorId) const;
  const std::unordered_map<int, StrawWire>& wires() const { return m_wires; }
  std::size_t size() const { return m_surfaces.size(); }
  /// Passive material planes, ordered in z
  const std::vector<PassivePlane>& passivePlanes() const { return m_passive; }

 private:
  std::unordered_map<int, std::shared_ptr<Acts::Surface>> m_surfaces;
  std::unordered_map<int, StrawWire> m_wires;
  std::vector<PassivePlane> m_passive;
};

}  // namespace SHiP

#endif  // ACTSTRACKING_ACTSSTRAWGEOMETRY_HPP_
