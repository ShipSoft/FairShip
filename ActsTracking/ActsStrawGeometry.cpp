// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#include "ActsStrawGeometry.hpp"

#include <stdexcept>
#include <string_view>

#include "Acts/Definitions/Units.hpp"
#include "Acts/Geometry/GeometryIdentifier.hpp"
#include "Acts/Material/HomogeneousSurfaceMaterial.hpp"
#include "Acts/Material/Material.hpp"
#include "Acts/Material/MaterialSlab.hpp"
#include "Acts/Surfaces/LineBounds.hpp"
#include "Acts/Surfaces/StrawSurface.hpp"
#include "ActsFrame.hpp"
#include "TGeoManager.h"
#include "TGeoMatrix.h"
#include "TGeoNode.h"
#include "TGeoTube.h"
#include "TGeoVolume.h"

namespace SHiP {

namespace {

namespace u = Acts::UnitConstants;

// The gas volume, which defines the detector ID, is placed with the straw
// copy number plus 1000 (see strawtubes::ConstructGeometry).
constexpr int kGasCopyOffset = 1000;

/// Material of one straw crossed at normal incidence: two walls and the gas
std::shared_ptr<const Acts::HomogeneousSurfaceMaterial> strawMaterial() {
  const auto gas = Acts::Material::fromMassDensity(
      30000.0 * u::mm, 50000.0 * u::mm, 30.0, 15.0, 0.0018 * u::g / u::cm3);
  const auto wall = Acts::Material::fromMassDensity(
      300.0 * u::mm, 400.0 * u::mm, 27.0, 13.0, 1.4 * u::g / u::cm3);
  const Acts::MaterialSlab gasSlab(gas, 10.0 * u::mm);
  const Acts::MaterialSlab wallSlab(wall, 0.036 * u::mm);
  auto slab = Acts::MaterialSlab::combineLayers(wallSlab, gasSlab);
  slab = Acts::MaterialSlab::combineLayers(slab, wallSlab);
  return std::make_shared<Acts::HomogeneousSurfaceMaterial>(slab);
}

Acts::Transform3 toTransform(const TGeoHMatrix& matrix) {
  const Double_t* r = matrix.GetRotationMatrix();
  const Double_t* t = matrix.GetTranslation();
  Acts::RotationMatrix3 rotation;
  rotation << r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8];
  Acts::Transform3 transform = Acts::Transform3::Identity();
  transform.linear() = rotation;
  transform.translation() = Acts::Vector3(t[0], t[1], t[2]);
  return transform;
}

/// Geometry identifier of a straw, from its strawtubes detector ID
Acts::GeometryIdentifier geometryId(int detectorId) {
  const int station = detectorId / 1000000;
  const int view = detectorId / 100000 % 10;
  const int layer = detectorId / 10000 % 10;
  const int straw = detectorId % 1000;
  return Acts::GeometryIdentifier()
      .withVolume(1)
      .withLayer(8 * station + 2 * view + layer)
      .withSensitive(straw);
}

struct Builder {
  std::unordered_map<int, std::shared_ptr<Acts::Surface>>& surfaces;
  std::shared_ptr<const Acts::HomogeneousSurfaceMaterial> material;

  void visit(const TGeoVolume& volume, const TGeoHMatrix& parent) {
    for (int i = 0; i < volume.GetNdaughters(); ++i) {
      const TGeoNode* node = volume.GetNode(i);
      TGeoHMatrix global = parent;
      global.Multiply(node->GetMatrix());
      const TGeoVolume* daughter = node->GetVolume();
      if (std::string_view(daughter->GetName()) == "straw") {
        addStraw(*node, global);
      } else {
        visit(*daughter, global);
      }
    }
  }

  void addStraw(const TGeoNode& node, const TGeoHMatrix& global) {
    const auto* tube =
        dynamic_cast<const TGeoTube*>(node.GetVolume()->GetShape());
    if (tube == nullptr) {
      throw std::runtime_error("ActsStrawGeometry: straw is not a TGeoTube");
    }
    const int detectorId = node.GetNumber() + kGasCopyOffset;
    auto bounds = std::make_shared<const Acts::LineBounds>(
        tube->GetRmax() * ActsFrame::kShipLength,
        tube->GetDZ() * ActsFrame::kShipLength);
    auto surface = Acts::Surface::makeShared<Acts::StrawSurface>(
        ActsFrame::transformToActs(toTransform(global)), bounds);
    surface->assignSurfaceMaterial(material);
    surface->assignGeometryId(geometryId(detectorId));
    surfaces.emplace(detectorId, std::move(surface));
  }
};

}  // namespace

ActsStrawGeometry::ActsStrawGeometry(const TGeoManager& geometry) {
  const TGeoVolume* top = geometry.GetTopVolume();
  if (top == nullptr) {
    throw std::invalid_argument("ActsStrawGeometry: no geometry loaded");
  }
  Builder builder{m_surfaces, strawMaterial()};
  builder.visit(*top, TGeoHMatrix());
  if (m_surfaces.empty()) {
    throw std::runtime_error("ActsStrawGeometry: no straws in the geometry");
  }
}

const Acts::Surface* ActsStrawGeometry::surface(int detectorId) const {
  const auto it = m_surfaces.find(detectorId);
  return it == m_surfaces.end() ? nullptr : it->second.get();
}

}  // namespace SHiP
