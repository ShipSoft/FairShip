// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#include "ShipMuonShield.h"

#include <algorithm>  // for std::ranges::copy, std::ranges::find, std::max, std::min
#include <array>
#include <iterator>  // for std::back_inserter

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

void ShipMuonShield::SetFloorBlocks(Int_t first_magnet, Double_t floor_gap,
                                    Double_t magnet_gap, Double_t z_transition,
                                    Double_t stair_step_length) {
  floor_blocks_first_magnet = first_magnet;
  floor_blocks_floor_gap = floor_gap;
  floor_blocks_magnet_gap = magnet_gap;
  cave_z_transition = z_transition;
  cave_stair_step_length = stair_step_length;
}

void ShipMuonShield::SkipFloorBlockOnStair(Int_t magnet) {
  floor_blocks_no_stair.push_back(magnet);
}

void ShipMuonShield::SetFloorBlockFloorGap(Int_t magnet, Double_t floor_gap) {
  floor_blocks_floor_gap_per_magnet[magnet] = floor_gap;
}

void ShipMuonShield::CreateFloorBlocks(Int_t magnet, const TString& magnetName,
                                       TGeoMedium* medium, TGeoVolume* tShield,
                                       Double_t dX, Double_t dY, Double_t dZ,
                                       Double_t Z) {
  using ShipCavernLayout::kECN3FloorY;
  using ShipCavernLayout::kStairFloorY;
  using ShipCavernLayout::kTCC8FloorY;
  struct FloorSegment {
    Double_t z_start, z_end, y;
  };
  const Double_t z_ecn3 = cave_z_transition + cave_stair_step_length;
  const std::array<FloorSegment, 3> floor = {
      {{-1e9, cave_z_transition, kTCC8FloorY},
       {cave_z_transition, z_ecn3, kStairFloorY},
       {z_ecn3, 1e9, kECN3FloorY}}};

  const Double_t y_top = -dY - floor_blocks_magnet_gap;
  const auto gap_it = floor_blocks_floor_gap_per_magnet.find(magnet);
  const Double_t floor_gap = gap_it != floor_blocks_floor_gap_per_magnet.end()
                                 ? gap_it->second
                                 : floor_blocks_floor_gap;
  const bool no_stair = std::ranges::find(floor_blocks_no_stair, magnet) !=
                        floor_blocks_no_stair.end();
  Int_t n_blocks = 0;
  for (size_t i = 0; i < floor.size(); ++i) {
    if (i == 1 && no_stair) {
      continue;  // segment 1 is the stair step
    }
    const auto& segment = floor[i];
    // Downstream of a step, keep floor_blocks_floor_gap from its vertical
    // face as well
    const Double_t z_start =
        i == 0 ? segment.z_start : segment.z_start + floor_blocks_floor_gap;
    const Double_t z1 = std::max(Z - dZ, z_start);
    const Double_t z2 = std::min(Z + dZ, segment.z_end);
    const Double_t y_bottom = segment.y + floor_gap;
    if (z2 <= z1 || y_top <= y_bottom) {
      continue;
    }
    TString name = magnetName + Form("_FloorBlock%d", ++n_blocks);
    LOG(info) << "Floor block " << name << ": y = [" << y_bottom << ", "
              << y_top << "], z = [" << z1 << ", " << z2 << "] cm";
    TGeoVolume* block = gGeoManager->MakeBox(
        name, medium, dX, (y_top - y_bottom) / 2., (z2 - z1) / 2.);
    block->SetLineColor(30);
    tShield->AddNode(
        block, 1,
        new TGeoTranslation(0, (y_top + y_bottom) / 2., (z1 + z2) / 2.));
  }
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
  // check the size against the expected number of magnets. At least one
  // magnet is needed, since the absorber is sized from the first one.
  if (nMagnets == 0 || shield_params.size() != nMagnets * nParams) {
    LOG(fatal) << "ShipMuonShield: expected " << nMagnets << " magnets x "
               << nParams << " parameters, got " << shield_params.size()
               << " values. Is the geometry from an older version?";
  }
  TGeoVolume* top = gGeoManager->GetTopVolume();
  TGeoVolume* tShield = new TGeoVolumeAssembly("MuonShieldArea");
  ShipGeo::InitMedium("iron");
  TGeoMedium* iron = gGeoManager->GetMedium("iron");
  ShipGeo::InitMedium("Concrete");
  TGeoMedium* concrete = gGeoManager->GetMedium("Concrete");

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
    if (floor_blocks_first_magnet >= 0 && i >= floor_blocks_first_magnet) {
      CreateFloorBlocks(i, name, concrete, tShield, dX, dY, dZ, Z);
    }
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
