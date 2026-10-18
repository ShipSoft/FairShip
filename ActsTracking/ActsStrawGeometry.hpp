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
  std::size_t size() const { return m_surfaces.size(); }

 private:
  std::unordered_map<int, std::shared_ptr<Acts::Surface>> m_surfaces;
};

}  // namespace SHiP

#endif  // ACTSTRACKING_ACTSSTRAWGEOMETRY_HPP_
