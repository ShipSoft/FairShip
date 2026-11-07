// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

// Tests of the passive material of the ACTS straw geometry, on a small TGeo
// geometry: an iron block and an aluminium wall upstream, a helium decay
// volume, then air and two straw stations.

#include <algorithm>
#include <cmath>
#include <iostream>
#include <map>

#include "Acts/Definitions/Units.hpp"
#include "Acts/EventData/BoundTrackParameters.hpp"
#include "Acts/EventData/ParticleHypothesis.hpp"
#include "Acts/Geometry/GeometryContext.hpp"
#include "Acts/MagneticField/ConstantBField.hpp"
#include "Acts/MagneticField/MagneticFieldContext.hpp"
#include "Acts/Material/ISurfaceMaterial.hpp"
#include "Acts/Material/Interactions.hpp"
#include "Acts/Propagator/ActorList.hpp"
#include "Acts/Propagator/DirectNavigator.hpp"
#include "Acts/Propagator/EigenStepper.hpp"
#include "Acts/Propagator/MaterialInteractor.hpp"
#include "Acts/Propagator/Propagator.hpp"
#include "Acts/Surfaces/PlaneSurface.hpp"
#include "ActsFrame.hpp"
#include "ActsStrawGeometry.hpp"
#include "TGeoManager.h"
#include "TGeoMaterial.h"
#include "TGeoMatrix.h"
#include "TGeoMedium.h"
#include "TGeoNavigator.h"
#include "TGeoTube.h"
#include "TGeoVolume.h"

namespace {

int failures = 0;

void check(bool condition, const char* what) {
  if (!condition) {
    std::cout << "FAIL: " << what << std::endl;
    ++failures;
  }
}

// cm
constexpr double kWallEnd = 3000.;
constexpr double kHeliumEnd = 8300.;
constexpr double kStationZ[2] = {8400., 8600.};
constexpr double kLayerPitch = 2.;
constexpr double kStrawRadius = 1.;
constexpr double kStrawHalfLength = 250.;

TGeoManager* buildGeometry() {
  auto* manager = new TGeoManager("test", "passive material test");
  auto* air =
      new TGeoMedium("air", 1, new TGeoMaterial("air", 14.61, 7.3, 0.001205));
  auto* helium =
      new TGeoMedium("helium", 2, new TGeoMaterial("helium", 4.0, 2., 1.66e-4));
  auto* iron =
      new TGeoMedium("iron", 3, new TGeoMaterial("iron", 55.85, 26., 7.87));
  auto* aluminium = new TGeoMedium(
      "aluminium", 4, new TGeoMaterial("aluminium", 26.98, 13., 2.7));
  auto* mylar =
      new TGeoMedium("mylar", 5, new TGeoMaterial("mylar", 8.7, 4.5, 1.39));

  TGeoVolume* top = manager->MakeBox("cave", air, 500., 500., 10000.);
  manager->SetTopVolume(top);
  top->AddNode(manager->MakeBox("shield", iron, 300., 300., 85.), 1,
               new TGeoTranslation(0., 0., 2085.));
  top->AddNode(manager->MakeBox("wall", aluminium, 300., 300., 2.5), 1,
               new TGeoTranslation(0., 0., kWallEnd - 2.5));
  const double heliumHalf = 0.5 * (kHeliumEnd - kWallEnd);
  top->AddNode(manager->MakeBox("decay", helium, 300., 300., heliumHalf), 1,
               new TGeoTranslation(0., 0., kWallEnd + heliumHalf));

  // Straws along x, two layers per station; the copy number plus 1000 is the
  // detector ID station * 10^6 + view * 10^5 + layer * 10^4 + straw
  auto* tube = new TGeoTube("straw", kStrawRadius - 0.01, kStrawRadius,
                            kStrawHalfLength);
  auto* straw = new TGeoVolume("straw", tube, mylar);
  auto* alongX = new TGeoRotation("alongX", 90., 90., 0.);
  for (int station = 1; station <= 2; ++station) {
    for (int layer = 0; layer < 2; ++layer) {
      const double z = kStationZ[station - 1] + layer * kLayerPitch;
      for (int k = 0; k < 50; ++k) {
        const double y = -99. + 4. * k + 2. * layer;
        const int id = station * 1000000 + layer * 10000 + k;
        top->AddNode(straw, id - 1000, new TGeoCombiTrans(0., y, z, alongX));
      }
    }
  }
  manager->CloseGeometry();
  return manager;
}

/// A plane of constant z (SHiP, cm)
std::shared_ptr<Acts::PlaneSurface> constantZPlane(double z) {
  Acts::Transform3 transform = Acts::Transform3::Identity();
  transform.linear().col(0) = Acts::Vector3::UnitY();
  transform.linear().col(1) = Acts::Vector3::UnitZ();
  transform.linear().col(2) = Acts::Vector3::UnitX();
  transform.translation() = SHiP::ActsFrame::positionToActs(0., 0., z);
  return Acts::Surface::makeShared<Acts::PlaneSurface>(transform);
}

/// Thickness in radiation lengths of a plane's surface material, whose
/// radiation length is scaled for the regional scattering
double surfaceX0(const SHiP::PassivePlane& plane) {
  return plane.surface->surfaceMaterial()
      ->materialSlab(Acts::Vector2::Zero())
      .thicknessInX0();
}

/// Propagate a muon going downstream from the plane at `fromZ` to the one
/// at `toZ` through the passive planes in between, without field, and
/// check that it crossed their material and scattered
void checkExtrapolation(const SHiP::ActsStrawGeometry& geometry, double fromZ,
                        double toZ) {
  using Propagator =
      Acts::Propagator<Acts::EigenStepper<>, Acts::DirectNavigator>;
  const Propagator propagator(
      Acts::EigenStepper<>(
          std::make_shared<Acts::ConstantBField>(Acts::Vector3::Zero())),
      Acts::DirectNavigator());
  const auto gctx = Acts::GeometryContext::dangerouslyDefaultConstruct();
  const Acts::MagneticFieldContext mctx;

  const auto start = constantZPlane(fromZ);
  const auto target = constantZPlane(toZ);
  Acts::BoundVector parameters = Acts::BoundVector::Zero();
  // Along ACTS x, i.e. the beam, at 10 GeV
  parameters[Acts::eBoundTheta] = 0.5 * M_PI;
  parameters[Acts::eBoundQOverP] = 1. / (10. * Acts::UnitConstants::GeV);
  Acts::BoundMatrix covariance = Acts::BoundMatrix::Identity() * 1e-12;
  covariance(Acts::eBoundLoc0, Acts::eBoundLoc0) = 1.;
  covariance(Acts::eBoundLoc1, Acts::eBoundLoc1) = 1.;
  const Acts::BoundTrackParameters params(start, parameters, covariance,
                                          Acts::ParticleHypothesis::muon());

  Propagator::Options<Acts::ActorList<Acts::MaterialInteractor>> options(gctx,
                                                                         mctx);
  options.direction =
      toZ > fromZ ? Acts::Direction::Forward() : Acts::Direction::Backward();
  options.navigation.surfaceSequence =
      geometry.materialSequence(fromZ, toZ, 1., *target);
  auto result = propagator.propagate(params, *target, options);
  check(result.ok() && result.value().endParameters.has_value(),
        "extrapolation through the passive planes");
  if (!result.ok() || !result.value().endParameters.has_value()) {
    return;
  }

  double expected = 0.;
  for (const auto& plane : geometry.passivePlanes()) {
    if (plane.z > std::min(fromZ, toZ) && plane.z < std::max(fromZ, toZ)) {
      expected += surfaceX0(plane);
    }
  }
  const double crossed =
      result.value().get<Acts::MaterialInteractor::result_type>().materialInX0;
  check(expected > 0. && std::abs(crossed - expected) < 1e-3 * expected,
        toZ > fromZ ? "forward extrapolation crosses all passive planes"
                    : "backward extrapolation crosses all passive planes");
  check(result.value().endParameters->covariance().value()(
            Acts::eBoundPhi, Acts::eBoundPhi) > 10. * 1e-12,
        "extrapolation adds multiple scattering");
}

}  // namespace

int main() {
  TGeoManager* manager = buildGeometry();
  TGeoNavigator* navigator = manager->GetCurrentNavigator();
  navigator->InitTrack(1., 2., 4000., 0., 0., 1.);
  const std::string pathBefore = navigator->GetPath();

  const SHiP::ActsStrawGeometry geometry(*manager);
  const auto& planes = geometry.passivePlanes();
  check(!planes.empty(), "passive planes are built");

  // The shared navigator is left where it was
  check(manager->GetCurrentNavigator() == navigator,
        "current navigator unchanged");
  check(std::abs(navigator->GetCurrentPoint()[2] - 4000.) < 1e-9,
        "navigator point restored");
  check(pathBefore == navigator->GetPath(), "navigator path restored");

  check(std::is_sorted(planes.begin(), planes.end(),
                       [](const auto& a, const auto& b) { return a.z < b.z; }),
        "planes are ordered in z");
  check(planes.front().z > kWallEnd,
        "no material upstream of the decay volume");
  check(planes.back().z <= kStationZ[1] + kLayerPitch + 3. + 1e-6,
        "no material behind the last station");

  // No plane between the layers of a station
  for (const auto& plane : planes) {
    for (const double z : kStationZ) {
      check(plane.z < z - 2.9 || plane.z > z + kLayerPitch + 2.9,
            "planes stay outside the stations");
    }
  }
  // Slices of at most one metre in the decay volume
  for (std::size_t i = 1; i < planes.size(); ++i) {
    check(planes[i].z - planes[i - 1].z <= 100. + 1e-6,
          "planes at most a metre apart");
  }

  // Helium from the wall to its end, air from there to behind the last
  // station; the probe lines pass between the straws or through a few, whose
  // material the straw surfaces carry, so allow for the air they displace
  const double heliumX0 = manager->GetMaterial("helium")->GetRadLen();
  const double airX0 = manager->GetMaterial("air")->GetRadLen();
  const double airLength = kStationZ[1] + kLayerPitch + 3. - kHeliumEnd;
  const double expected =
      (kHeliumEnd - kWallEnd) / heliumX0 + airLength / airX0;
  double total = 0.;
  for (const auto& plane : planes) {
    total += plane.thicknessInX0;
  }
  check(std::abs(total - expected) < 8. * kStrawRadius / airX0 + 1e-6,
        "total material is helium plus air");

  // Scattering regions split at the station centres; the planes of a region
  // scatter together like Highland on the region's total thickness, while
  // Highland applied to each plane alone is much narrower
  const double centres[2] = {kStationZ[0] + 0.5 * kLayerPitch,
                             kStationZ[1] + 0.5 * kLayerPitch};
  std::map<int, double> regionX0, regionVariance, planeVariance;
  for (const auto& plane : planes) {
    check(plane.region == (plane.z > centres[0]) + (plane.z > centres[1]),
          "plane in the region between the station centres");
    const double scaled = Acts::approximateHighlandScattering(surfaceX0(plane));
    const double plain =
        Acts::approximateHighlandScattering(plane.thicknessInX0);
    regionX0[plane.region] += plane.thicknessInX0;
    regionVariance[plane.region] += scaled * scaled;
    planeVariance[plane.region] += plain * plain;
  }
  check(regionX0.size() == 3, "three scattering regions");
  for (const auto& [region, x0] : regionX0) {
    const double highland = Acts::approximateHighlandScattering(x0);
    check(std::abs(std::sqrt(regionVariance[region]) / highland - 1.) < 1e-4,
          "planes of a region add up to Highland on the region");
  }
  check(std::sqrt(planeVariance[0]) <
            0.9 * Acts::approximateHighlandScattering(regionX0[0]),
        "Highland per plane is narrower in the decay volume");

  // Towards the decay volume, as to a vertex, and back
  checkExtrapolation(geometry, kHeliumEnd + 50., kWallEnd + 1000.);
  checkExtrapolation(geometry, kWallEnd + 1000., kHeliumEnd + 50.);

  if (failures == 0) {
    std::cout << "passive material: " << planes.size() << " planes, " << total
              << " X0 (expected " << expected << ")" << std::endl;
  }
  return failures == 0 ? 0 : 1;
}
