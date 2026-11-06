// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

// Tests of the ACTS straw geometry: the straw material comes from the wall,
// gas and wire volumes of the TGeo geometry.

#include <cmath>
#include <iostream>

#include "Acts/Material/ISurfaceMaterial.hpp"
#include "Acts/Material/MaterialSlab.hpp"
#include "ActsStrawGeometry.hpp"
#include "TGeoManager.h"
#include "TGeoMaterial.h"
#include "TGeoMatrix.h"
#include "TGeoMedium.h"
#include "TGeoTube.h"
#include "TGeoVolume.h"

namespace {

// Straw dimensions of geometry/strawtubes_config.yaml (cm)
constexpr double kOuterRadius = 1.;
constexpr double kWall = 0.0036;
constexpr double kWireRadius = 0.0015;
constexpr double kEps = 0.0001;

int failures = 0;

void check(bool condition, const char* what) {
  if (!condition) {
    std::cout << "FAIL: " << what << std::endl;
    ++failures;
  }
}

/// Mean path through a tube from rmin to rmax, over where a track crosses a
/// straw of radius kOuterRadius, in radiation lengths
double meanX0(double rmin, double rmax, const TGeoMaterial& material) {
  return M_PI * (rmax * rmax - rmin * rmin) / (2. * kOuterRadius) /
         material.GetRadLen();
}

void testStrawMaterial() {
  auto* manager = new TGeoManager("strawGeometry", "straws");
  // Mylar, Ar/CO2 80/20 and tungsten as in geometry/media.geo
  auto* mylar = new TGeoMixture("mylar", 3, 1.39);
  mylar->AddElement(1.008, 1., 0.042);
  mylar->AddElement(12.01, 6., 0.625);
  mylar->AddElement(16., 8., 0.333);
  auto* gasMix = new TGeoMixture("STTmix8020_1bar", 3, 0.001698);
  gasMix->AddElement(39.948, 18., 0.78);
  gasMix->AddElement(12.01, 6., 0.06);
  gasMix->AddElement(15.9994, 8., 0.16);
  auto* tungsten = new TGeoMaterial("tungsten", 183.84, 74., 19.3);
  auto* vacuum = new TGeoMaterial("vacuum", 0., 0., 0.);

  auto* top = manager->MakeBox("cave", new TGeoMedium("vacuum", 1, vacuum),
                               500., 500., 500.);
  manager->SetTopVolume(top);
  auto* layer = manager->MakeBox("layer", new TGeoMedium("air", 2, vacuum),
                                 300., 10., kOuterRadius + kEps);
  auto* straw = new TGeoVolume(
      "straw", new TGeoTube(kOuterRadius - kWall, kOuterRadius, 250.),
      new TGeoMedium("mylar", 3, mylar));
  auto* gas = new TGeoVolume(
      "gas",
      new TGeoTube(kWireRadius + kEps, kOuterRadius - kWall - kEps, 250.),
      new TGeoMedium("STTmix8020_1bar", 4, gasMix));
  auto* wire = new TGeoVolume("wire", new TGeoTube(0., kWireRadius, 250.),
                              new TGeoMedium("tungsten", 5, tungsten));
  // Two horizontal straws of station 1, view 0, layer 0
  for (int number = 1; number <= 2; ++number) {
    auto* placement =
        new TGeoCombiTrans(0., 2. * kOuterRadius * (number - 1.5), 0.,
                           new TGeoRotation("r", 90., 90., 0.));
    layer->AddNode(straw, 1001000 + number, placement);
    layer->AddNode(gas, 1002000 + number, placement);
    layer->AddNode(wire, 1003000 + number, placement);
  }
  top->AddNode(layer, 1, new TGeoTranslation(0., 0., 8400.));
  manager->CloseGeometry();

  const SHiP::ActsStrawGeometry geometry(*manager);
  check(geometry.size() == 2, "two straws");
  const Acts::Surface* surface = geometry.surface(1002001);
  check(surface != nullptr, "straw surface found by detector ID");
  if (surface == nullptr || surface->surfaceMaterial() == nullptr) {
    check(false, "straw surface has material");
    delete manager;
    return;
  }
  const double x0 = surface->surfaceMaterial()
                        ->materialSlab(Acts::Vector2::Zero())
                        .thicknessInX0();
  const double expected =
      meanX0(kOuterRadius - kWall, kOuterRadius, *mylar) +
      meanX0(kWireRadius + kEps, kOuterRadius - kWall - kEps, *gasMix) +
      meanX0(0., kWireRadius, *tungsten);
  if (std::abs(x0 - expected) > 1e-3 * expected) {
    std::cout << "straw material " << x0 << " X0, expected " << expected
              << std::endl;
  }
  check(std::abs(x0 - expected) < 1e-3 * expected,
        "straw material is the mean path through wall, gas and wire");
  // About 0.039% X0 of wall, 0.012% of gas and 0.001% of wire
  check(x0 > 5.0e-4 && x0 < 5.5e-4, "straw material is about 5.3e-4 X0");
  delete manager;
}

}  // namespace

int main() {
  testStrawMaterial();
  if (failures == 0) {
    std::cout << "All ACTS straw geometry tests passed" << std::endl;
  }
  return failures == 0 ? 0 : 1;
}
