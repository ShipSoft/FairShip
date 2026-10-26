// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#include "ActsStrawGeometry.hpp"

#include <algorithm>
#include <array>
#include <cmath>
#include <map>
#include <stdexcept>
#include <string_view>
#include <utility>
#include <vector>

#include "Acts/Definitions/Units.hpp"
#include "Acts/Geometry/GeometryIdentifier.hpp"
#include "Acts/Material/HomogeneousSurfaceMaterial.hpp"
#include "Acts/Material/Material.hpp"
#include "Acts/Material/MaterialSlab.hpp"
#include "Acts/Surfaces/LineBounds.hpp"
#include "Acts/Surfaces/PlaneSurface.hpp"
#include "Acts/Surfaces/StrawSurface.hpp"
#include "ActsFrame.hpp"
#include "TGeoManager.h"
#include "TGeoMaterial.h"
#include "TGeoMatrix.h"
#include "TGeoNavigator.h"
#include "TGeoNode.h"
#include "TGeoTube.h"
#include "TGeoVolume.h"

namespace SHiP {

namespace {

namespace u = Acts::UnitConstants;

// The gas volume, which defines the detector ID, is placed with the straw
// copy number plus 1000 (see strawtubes::ConstructGeometry).
constexpr int kGasCopyOffset = 1000;

/// Passive material (SHiP frame, cm): planes are kept this far outside the
/// stations, so that none falls between a wire and the point where a track
/// crosses its straw; between the stations and in the decay volume the
/// material is lumped onto planes at most this far apart
constexpr double kStationMargin = 3.;
constexpr double kMaxSlice = 100.;
/// Where the material walk starts along the beam (cm), upstream of the decay
/// volume
constexpr double kWalkStart = 2000.;
/// A solid at least this thick (cm) bounds the decay volume upstream
constexpr double kBoundaryThickness = 0.5;
constexpr double kGasDensity = 0.01;  // g/cm3

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
  std::unordered_map<int, StrawWire>& wires;
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

/// One step of a walk through the TGeo geometry along the beam
struct Step {
  double z0, z1;
  const TGeoMaterial* material;
  /// Inside a straw (wall, gas or wire), whose material the straw surfaces
  /// carry already
  bool straw;
};

/// The volumes crossed by the line through (x, y) parallel to the beam
std::vector<Step> walk(TGeoNavigator& navigator, double x, double y, double z0,
                       double z1) {
  navigator.InitTrack(x, y, z0, 0., 0., 1.);
  std::vector<Step> steps;
  double z = z0;
  while (z < z1) {
    const TGeoNode* node = navigator.GetCurrentNode();
    navigator.FindNextBoundaryAndStep(z1 - z);
    double next = std::min(navigator.GetCurrentPoint()[2], z1);
    if (next <= z) {
      // Stuck on a boundary: nudge past it
      next = z + 1e-4;
      navigator.InitTrack(x, y, next, 0., 0., 1.);
    }
    if (node != nullptr) {
      const TGeoVolume* volume = node->GetVolume();
      const std::string_view name = volume->GetName();
      steps.push_back({z, next, volume->GetMaterial(),
                       name == "straw" || name == "gas" || name == "wire"});
    }
    z = next;
  }
  return steps;
}

/// Upstream end of the decay volume seen along a walk: the downstream face
/// of the last thick solid before the first station
double decayVolumeStart(const std::vector<Step>& steps, double zFirst) {
  for (auto it = steps.rbegin(); it != steps.rend(); ++it) {
    if (it->z1 > zFirst || it->straw || it->material == nullptr) {
      continue;
    }
    if (it->material->GetDensity() > kGasDensity &&
        it->z1 - it->z0 > kBoundaryThickness) {
      return it->z1;
    }
  }
  return steps.empty() ? zFirst : steps.front().z0;
}

Acts::MaterialSlab slab(const TGeoMaterial& material, double thickness) {
  return Acts::MaterialSlab(
      Acts::Material::fromMassDensity(
          material.GetRadLen() * ActsFrame::kShipLength,
          material.GetIntLen() * ActsFrame::kShipLength, material.GetA(),
          material.GetZ(), material.GetDensity() * u::g / u::cm3),
      thickness * ActsFrame::kShipLength);
}

/// Passive planes carrying the material outside the straws, from the
/// upstream end of the decay volume to the last station.
///
/// Station interiors go half to a plane just upstream and half to one just
/// downstream of the station; the stretches between are cut into slices of
/// at most kMaxSlice, each lumped onto a plane at its centre. The material
/// is read along a few lines across the acceptance, and the one with the
/// median material is used.
std::vector<PassivePlane> buildPassivePlanes(
    TGeoManager& manager, const std::unordered_map<int, StrawWire>& wires) {
  std::map<int, std::pair<double, double>> stations;
  double yExtent = 0.;
  double halfLength = 0.;
  for (const auto& [id, wire] : wires) {
    auto [it, inserted] = stations.try_emplace(wire.station, wire.z, wire.z);
    it->second.first = std::min(it->second.first, wire.z);
    it->second.second = std::max(it->second.second, wire.z);
    yExtent = std::max(yExtent, std::abs(wire.y));
    halfLength = std::max(halfLength, wire.halfLength);
  }
  // Station zones and the stretches of gas between them, in z order
  std::vector<std::pair<double, double>> zones;
  for (const auto& [station, extent] : stations) {
    zones.emplace_back(extent.first - kStationMargin,
                       extent.second + kStationMargin);
  }
  const double zFirst = zones.front().first;
  const double zLast = zones.back().second;

  std::vector<std::pair<double, double>> probes = {{0., 0.},
                                                   {0.4 * halfLength, 0.},
                                                   {-0.4 * halfLength, 0.},
                                                   {0., 0.4 * yExtent},
                                                   {0., -0.4 * yExtent}};
  // The current navigator, with its state saved and restored: a second
  // navigator on the same thread shares the voxel search state with the
  // first and does not find the daughter volumes
  TGeoNavigator* navigator = manager.GetCurrentNavigator();
  if (navigator == nullptr) {
    navigator = manager.AddNavigator();
  }
  const std::array<double, 3> savedPoint = {navigator->GetCurrentPoint()[0],
                                            navigator->GetCurrentPoint()[1],
                                            navigator->GetCurrentPoint()[2]};
  const std::array<double, 3> savedDirection = {
      navigator->GetCurrentDirection()[0], navigator->GetCurrentDirection()[1],
      navigator->GetCurrentDirection()[2]};
  navigator->PushPoint();
  std::vector<std::pair<double, std::vector<Step>>> walks;
  for (const auto& [x, y] : probes) {
    auto steps = walk(*navigator, x, y, kWalkStart, zLast);
    const double start = decayVolumeStart(steps, zFirst);
    std::vector<Step> kept;
    double x0 = 0.;
    for (auto step : steps) {
      if (step.straw || step.material == nullptr || step.z1 <= start) {
        continue;
      }
      step.z0 = std::max(step.z0, start);
      kept.push_back(step);
      x0 += (step.z1 - step.z0) / step.material->GetRadLen();
    }
    walks.emplace_back(x0, std::move(kept));
  }
  navigator->PopPoint();
  navigator->SetCurrentPoint(savedPoint.data());
  navigator->SetCurrentDirection(savedDirection.data());
  std::sort(walks.begin(), walks.end(),
            [](const auto& a, const auto& b) { return a.first < b.first; });
  const std::vector<Step>& steps = walks[walks.size() / 2].second;
  if (steps.empty()) {
    return {};
  }

  // Stretches between the stations (and upstream of the first), cut into
  // slices
  std::vector<std::pair<double, double>> gaps;
  double previous = steps.front().z0;
  for (const auto& zone : zones) {
    if (zone.first > previous) {
      gaps.emplace_back(previous, zone.first);
    }
    previous = zone.second;
  }
  std::map<double, std::vector<Acts::MaterialSlab>> lumped;
  for (const Step& step : steps) {
    for (const auto& [a, b] : zones) {
      const double lo = std::max(step.z0, a);
      const double hi = std::min(step.z1, b);
      if (hi > lo) {
        lumped[a].push_back(slab(*step.material, 0.5 * (hi - lo)));
        lumped[b].push_back(slab(*step.material, 0.5 * (hi - lo)));
      }
    }
    for (const auto& [a, b] : gaps) {
      const int n = static_cast<int>(std::ceil((b - a) / kMaxSlice));
      const double width = (b - a) / n;
      for (int k = 0; k < n; ++k) {
        const double lo = std::max(step.z0, a + k * width);
        const double hi = std::min(step.z1, a + (k + 1) * width);
        if (hi > lo) {
          lumped[a + (k + 0.5) * width].push_back(
              slab(*step.material, hi - lo));
        }
      }
    }
  }

  std::vector<PassivePlane> planes;
  for (const auto& [z, slabs] : lumped) {
    const Acts::MaterialSlab combined =
        Acts::MaterialSlab::combineLayers(slabs);
    if (!(combined.thicknessInX0() > 0.)) {
      continue;
    }
    // A plane of constant z (SHiP), i.e. of constant x (ACTS)
    Acts::Transform3 transform = Acts::Transform3::Identity();
    transform.linear().col(0) = Acts::Vector3::UnitY();
    transform.linear().col(1) = Acts::Vector3::UnitZ();
    transform.linear().col(2) = Acts::Vector3::UnitX();
    transform.translation() = ActsFrame::positionToActs(0., 0., z);
    auto surface = Acts::Surface::makeShared<Acts::PlaneSurface>(transform);
    surface->assignSurfaceMaterial(
        std::make_shared<Acts::HomogeneousSurfaceMaterial>(combined));
    surface->assignGeometryId(
        Acts::GeometryIdentifier().withVolume(2).withPassive(
            static_cast<Acts::GeometryIdentifier::Value>(planes.size() + 1)));
    planes.push_back({z, combined.thicknessInX0(), std::move(surface)});
  }
  return planes;
}

}  // namespace

ActsStrawGeometry::ActsStrawGeometry(const TGeoManager& geometry) {
  const TGeoVolume* top = geometry.GetTopVolume();
  if (top == nullptr) {
    throw std::invalid_argument("ActsStrawGeometry: no geometry loaded");
  }
  Builder builder{m_surfaces, m_wires, strawMaterial()};
  builder.visit(*top, TGeoHMatrix());
  if (m_surfaces.empty()) {
    throw std::runtime_error("ActsStrawGeometry: no straws in the geometry");
  }
  // Navigating needs a mutable manager; the walks use their own navigator
  m_passive = buildPassivePlanes(const_cast<TGeoManager&>(geometry), m_wires);
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
