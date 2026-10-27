// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#include "ShipMuonShield.h"

#include <algorithm>  // for std::ranges::copy
#include <iterator>   // for std::back_inserter

#include "FairLogger.h"  /// for FairLogger, MESSAGE_ORIGIN
#include "ShipCavernLayout.h"
#include "ShipGeoUtil.h"
#include "ShipUnit.h"
#include "TGeoBBox.h"
#include "TGeoCompositeShape.h"
#include "TGeoManager.h"
#include "TGeoMatrix.h"
#include "TString.h"  // for TString

using ShipUnit::m;

ShipMuonShield::~ShipMuonShield() = default;
ShipMuonShield::ShipMuonShield() : FairModule("ShipMuonShield", "") {}

ShipMuonShield::ShipMuonShield(std::vector<double> in_params, size_t n_magnets,
                               Double_t z)
    : FairModule("MuonShield", "ShipMuonShield") {
  LOG(debug) << " Function ShipMuonShield MS ";
  std::ranges::copy(in_params, std::back_inserter(shield_params));
  nMagnets = n_magnets;

  z_end_of_proximity_shielding = z;
}

void ShipMuonShield::SetSNDSpace(Bool_t hole, Double_t hole_dx,
                                 Double_t hole_dy, Int_t first_magnet,
                                 Int_t last_magnet) {
  snd_hole = hole;
  snd_first_magnet = first_magnet;
  snd_last_magnet = last_magnet;
  snd_hole_dx = hole_dx;
  snd_hole_dy = hole_dy;
}

void ShipMuonShield::CreateMagnet(const TString& magnetName, TGeoMedium* medium,
                                  TGeoVolume* tShield, Double_t dX, Double_t dY,
                                  Double_t dZ, Double_t Z, Bool_t withSNDHole) {
  LOG(debug) << " Create a magnet of the MS ";
  TGeoVolume* magVol = nullptr;

  if (withSNDHole) {
    // Solid box minus a void box along the beam axis
    TString shapeName = magnetName + "_shape";
    new TGeoBBox(shapeName, dX, dY, dZ);

    // Void 0.1 mm smaller than the hole transversally (anti-overlap with the
    // SND) and longer than the magnet, so that no faces coincide
    constexpr double eps = 0.01;
    TString voidName = magnetName + "_void";
    new TGeoBBox(voidName, snd_hole_dx - eps, snd_hole_dy - eps, dZ + eps);

    auto* compShape = new TGeoCompositeShape(magnetName + "_comp",
                                             shapeName + " - " + voidName);
    magVol = new TGeoVolume(magnetName, compShape, medium);
  } else {
    magVol = gGeoManager->MakeBox(magnetName, medium, dX, dY, dZ);
  }

  magVol->SetLineColor(45);
  tShield->AddNode(magVol, 1, new TGeoTranslation(0, 0, Z));
}

void ShipMuonShield::ConstructGeometry() {
  LOG(debug) << " Construct Geometry of the MS ";
  // A list in the old 15-value format also divides evenly by nParams, so
  // check the size against the expected number of magnets.
  if (shield_params.size() != nMagnets * nParams) {
    LOG(fatal) << "ShipMuonShield: expected " << nMagnets << " magnets x "
               << nParams << " parameters, got " << shield_params.size()
               << " values. Is the geometry from an older version?";
  }
  TGeoVolume* top = gGeoManager->GetTopVolume();
  TGeoVolume* tShield = new TGeoVolumeAssembly("MuonShieldArea");
  ShipGeo::InitMedium("iron");
  TGeoMedium* iron = gGeoManager->GetMedium("iron");

  bool absorber_magnet = false;
  Double_t Z = z_end_of_proximity_shielding;
  for (size_t nM = 0; nM < nMagnets; ++nM) {
    const Double_t Zgap = shield_params[nM * nParams + 0];
    const Double_t dZ = shield_params[nM * nParams + 1];
    const Double_t dX = shield_params[nM * nParams + 2];
    const Double_t dY = shield_params[nM * nParams + 3];
    // Subsequent magnets are placed relative to the previous one
    if (nM > 0) {
      Z += shield_params[(nM - 1) * nParams + 1];
    }
    Z += Zgap + dZ;

    TString name = nM == 0 ? TString("MagnAbsorb") : Form("Magn%zu", nM);
    LOG(debug) << "Magnet " << name << ": Zgap=" << Zgap << ", dZ=" << dZ
               << ", dX=" << dX << ", dY=" << dY << ", Z=" << Z;
    if (dZ < 1e-5 || dX == 0) {
      continue;
    }
    const auto i = static_cast<Int_t>(nM);
    CreateMagnet(name, iron, tShield, dX, dY, dZ, Z,
                 snd_hole && i >= snd_first_magnet && i <= snd_last_magnet);
    absorber_magnet |= nM == 0;
  }

  // Place in origin of SHiP coordinate system as subnodes placed correctly
  top->AddNode(tShield, 1);

  Double_t absorber_offset = shield_params[0];
  Double_t absorber_half_length = shield_params[1];

  // Absorber: iron filling the TCC8 cross-section around the hadron stopper

  using ShipCavernLayout::kTCC8CeilingY;
  using ShipCavernLayout::kTCC8FloorY;
  using ShipCavernLayout::kTCC8LeftX;
  using ShipCavernLayout::kTCC8RightX;
  TGeoShape* absorberShape = new TGeoBBox(
      "absorber", (kTCC8RightX - kTCC8LeftX) / 2. - 0.002 * m,
      (kTCC8CeilingY - kTCC8FloorY) / 2., absorber_half_length - 0.002 * m);
  Double_t shift_x = (kTCC8RightX + kTCC8LeftX) / 2.;
  Double_t shift_y = (kTCC8CeilingY + kTCC8FloorY) / 2.;

  if (absorber_magnet) {
    // Leave room for the magnet of the hadron absorber
    auto* absorber_shift =
        new TGeoTranslation("absorber_shift", shift_x, shift_y, 0);
    absorber_shift->RegisterYourself();
    absorberShape = new TGeoCompositeShape(
        "Absorber", "absorber:absorber_shift - MagnAbsorb");
    shift_x = shift_y = 0;
  }

  TGeoVolume* absorber = new TGeoVolume("AbsorberVol", absorberShape, iron);
  absorber->SetLineColor(42);  // brown / light red
  tShield->AddNode(
      absorber, 1,
      new TGeoTranslation(shift_x, shift_y,
                          z_end_of_proximity_shielding + absorber_half_length +
                              absorber_offset));  // - Passive?
}
