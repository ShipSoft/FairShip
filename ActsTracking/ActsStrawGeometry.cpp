// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#include "ActsStrawGeometry.hpp"

#include <cmath>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>

#include "Acts/Definitions/Units.hpp"
#include "Acts/Geometry/GeometryIdentifier.hpp"
#include "Acts/Material/HomogeneousSurfaceMaterial.hpp"
#include "Acts/Material/Material.hpp"
#include "Acts/Material/MaterialSlab.hpp"
#include "Acts/Surfaces/LineBounds.hpp"
#include "Acts/Surfaces/StrawSurface.hpp"
#include "ActsFrame.hpp"
#include "TGeoManager.h"
#include "TGeoMaterial.h"
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

/// A straw component ("straw" for the wall, "gas", "wire") among the daughters
/// of the volume holding the straws, or nullptr
const TGeoNode* strawComponent(const TGeoVolume& volume,
                               std::string_view name) {
  for (int i = 0; i < volume.GetNdaughters(); ++i) {
    const TGeoNode* node = volume.GetNode(i);
    if (std::string_view(node->GetVolume()->GetName()) == name) {
      return node;
    }
  }
  return nullptr;
}

/// Material of a straw for a track at normal incidence, from the straw
/// volumes of the geometry: the wall, the gas and, if there is one, the wire.
/// Each contributes its mean path over where the track crosses the straw,
/// i.e. its cross-section divided by the straw diameter. The straws of a layer
/// touch, so this is also the mean material per layer.
std::shared_ptr<const Acts::HomogeneousSurfaceMaterial> strawMaterial(
    const TGeoVolume& volume) {
  double diameter = 0.;
  std::vector<Acts::MaterialSlab> slabs;
  for (const char* name : {"straw", "gas", "wire"}) {
    const TGeoNode* node = strawComponent(volume, name);
    if (node == nullptr) {
      if (std::string_view(name) == "wire") {
        continue;
      }
      throw std::runtime_error(std::string("ActsStrawGeometry: no straw ") +
                               name + " volume");
    }
    const auto* tube =
        dynamic_cast<const TGeoTube*>(node->GetVolume()->GetShape());
    if (tube == nullptr) {
      throw std::runtime_error(std::string("ActsStrawGeometry: straw ") + name +
                               " is not a TGeoTube");
    }
    if (diameter == 0.) {
      diameter = 2. * tube->GetRmax();
    }
    const TGeoMaterial* material = node->GetVolume()->GetMaterial();
    const double area = M_PI * (tube->GetRmax() * tube->GetRmax() -
                                tube->GetRmin() * tube->GetRmin());
    slabs.emplace_back(
        Acts::Material::fromMassDensity(
            material->GetRadLen() * ActsFrame::kShipLength,
            material->GetIntLen() * ActsFrame::kShipLength, material->GetA(),
            material->GetZ(), material->GetDensity() * u::g / u::cm3),
        area / diameter * ActsFrame::kShipLength);
  }
  return std::make_shared<Acts::HomogeneousSurfaceMaterial>(
      Acts::MaterialSlab::combineLayers(slabs));
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
  std::unordered_map<int, StrawWire>& wires;
  std::shared_ptr<const Acts::HomogeneousSurfaceMaterial> material;

  void visit(const TGeoVolume& volume, const TGeoHMatrix& parent) {
    for (int i = 0; i < volume.GetNdaughters(); ++i) {
      const TGeoNode* node = volume.GetNode(i);
      TGeoHMatrix global = parent;
      global.Multiply(node->GetMatrix());
      const TGeoVolume* daughter = node->GetVolume();
      if (std::string_view(daughter->GetName()) == "straw") {
        if (material == nullptr) {
          // All straws are alike
          material = strawMaterial(volume);
        }
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

    const Double_t* t = global.GetTranslation();
    const Double_t* r = global.GetRotationMatrix();
    // The tube axis is the local z axis, i.e. the third column
    wires.emplace(
        detectorId,
        StrawWire{detectorId, detectorId / 1000000, detectorId / 100000 % 10,
                  detectorId / 10000 % 10, t[0], t[1], t[2], r[2], r[5], r[8],
                  tube->GetRmin(), tube->GetDZ()});
  }
};

}  // namespace

ActsStrawGeometry::ActsStrawGeometry(const TGeoManager& geometry) {
  const TGeoVolume* top = geometry.GetTopVolume();
  if (top == nullptr) {
    throw std::invalid_argument("ActsStrawGeometry: no geometry loaded");
  }
  Builder builder{m_surfaces, m_wires, nullptr};
  builder.visit(*top, TGeoHMatrix());
  if (m_surfaces.empty()) {
    throw std::runtime_error("ActsStrawGeometry: no straws in the geometry");
  }
}

const Acts::Surface* ActsStrawGeometry::surface(int detectorId) const {
  const auto it = m_surfaces.find(detectorId);
  return it == m_surfaces.end() ? nullptr : it->second.get();
}

const StrawWire* ActsStrawGeometry::wire(int detectorId) const {
  const auto it = m_wires.find(detectorId);
  return it == m_wires.end() ? nullptr : &it->second;
}

}  // namespace SHiP
