// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#include "ShipTargetStation.h"

#include "FairGeoBuilder.h"
#include "FairGeoMedia.h"
#include "FairLogger.h"
#include "FairRun.h"        // for FairRun
#include "FairRuntimeDb.h"  // for FairRuntimeDb
#include "ShipGeoUtil.h"
#include "ShipUnit.h"
#include "TGeoBBox.h"
#include "TGeoCompositeShape.h"
#include "TGeoManager.h"
#include "TGeoMaterial.h"
#include "TGeoMedium.h"
#include "TGeoShapeAssembly.h"
#include "TGeoTube.h"
#include "TList.h"      // for TListIter, TList (ptr only)
#include "TObjArray.h"  // for TObjArray
#include "TString.h"    // for TString

using ShipUnit::cm;
using ShipUnit::mm;

ShipTargetStation::~ShipTargetStation() = default;
ShipTargetStation::ShipTargetStation() : FairModule("ShipTargetStation", "") {}

ShipTargetStation::ShipTargetStation(const char* name, const Double_t tl,
                                     const Double_t tz, const int nS,
                                     const int HeT, const char* Title)
    : FairModule(name, Title) {
  fTargetLength = tl;
  fTargetZ = tz;
  fnS = nS;
  fHeT = HeT;
}

void ShipTargetStation::ConstructGeometry() {
  TGeoVolume* top = gGeoManager->GetTopVolume();

  ShipGeo::InitMedium("tungsten");
  TGeoMedium* tungsten = gGeoManager->GetMedium("tungsten");
  ShipGeo::InitMedium("tantalum");
  TGeoMedium* tantalum = gGeoManager->GetMedium("tantalum");
  ShipGeo::InitMedium("molybdenum");
  TGeoMedium* mo = gGeoManager->GetMedium("molybdenum");
  ShipGeo::InitMedium("iron");
  TGeoMedium* iron = gGeoManager->GetMedium("iron");
  ShipGeo::InitMedium("steel316L");
  TGeoMedium* steel316L = gGeoManager->GetMedium("steel316L");
  ShipGeo::InitMedium("copper");
  TGeoMedium* copper = gGeoManager->GetMedium("copper");

  ShipGeo::InitMedium("Inconel718");
  TGeoMedium* inc718 = gGeoManager->GetMedium("Inconel718");

  ShipGeo::InitMedium("vacuums");
  TGeoMedium* vacuum = gGeoManager->GetMedium("vacuums");

  double He_T = 273.15 + fHeT;       // in K, use average 90 degrees C.
  double He_P = 1.6e6 * 6.241509e3;  // 16 bar in MeV/mm3

  std::ostringstream lHename;
  lHename << "PressurisedHe" << fHeT;
  ShipGeo::InitMedium(lHename.str().c_str());
  TGeoMedium* pressurised_He = gGeoManager->GetMedium(lHename.str().c_str());

  // CAMM- dirty fix to have pressure and temperature correct for Geant4.
  // Should fix this properly in future...
  TGeoMaterial* fixedCooler = pressurised_He->GetMaterial();
  fixedCooler->SetTemperature(He_T);
  fixedCooler->SetPressure(He_P);
  TGeoMedium* cooler = pressurised_He;

  LOG(info) << "-- Target cooler: " << cooler->GetName()
            << " T=" << cooler->GetMaterial()->GetTemperature()
            << " K, P=" << cooler->GetMaterial()->GetPressure()
            << " MeV/mm3, Density=" << cooler->GetMaterial()->GetDensity();

  TGeoVolume* tTarget = new TGeoVolumeAssembly("TargetArea");

  if (fDesign == 1) {
    // Target vessel - inner dimensions for diameter, shifts and length
    double vessel_thickness = 8 * mm;
    double vessel_diameter = fDiameter + 150 * mm;  // Inner diameter of vessel
    double vessel_shift =
        62 *
        mm;  // Shift in z at y=0 (round shape not implemented for vessel lids)
    double vessel_length = fTargetLength + 2 * vessel_shift;

    TGeoVolume* vessel;
    vessel = gGeoManager->MakeTube("TargetVessel", inc718, vessel_diameter / 2.,
                                   vessel_diameter / 2. + vessel_thickness,
                                   vessel_length / 2.);
    vessel->SetLineColor(28);
    tTarget->AddNode(
        vessel, 1,
        new TGeoTranslation(0, 0, -1. * vessel_shift + vessel_length / 2.));
    // Front face
    vessel = gGeoManager->MakeTube("TargetVesselFront", inc718, 0,
                                   vessel_diameter / 2. + vessel_thickness,
                                   vessel_thickness / 2.);
    vessel->SetLineColor(28);
    tTarget->AddNode(
        vessel, 1,
        new TGeoTranslation(0, 0, -1. * vessel_shift - vessel_thickness / 2.));
    // Back face
    vessel = gGeoManager->MakeTube("TargetVesselBack", inc718, 0,
                                   vessel_diameter / 2. + vessel_thickness,
                                   vessel_thickness / 2.);
    vessel->SetLineColor(28);
    tTarget->AddNode(
        vessel, 1,
        new TGeoTranslation(
            0, 0, -1. * vessel_shift + vessel_length + vessel_thickness / 2.));
    // He inside
    vessel = gGeoManager->MakeTube("HeVolume", cooler, 0, vessel_diameter / 2.,
                                   vessel_length / 2.);
    vessel->SetLineColor(7);

    // Steel enclosure around target inside He volume
    // Inner radius must be larger than target radius (fDiameter/2) to avoid
    // overlaps
    double enclosure_clearance =
        0.1 * mm;  // Clearance between target and enclosure
    double enclosure_inner_radius = fDiameter / 2. + enclosure_clearance;
    double enclosure_thickness = 66.9 * mm;  // Updated to match BDF model
    double enclosure_outer_radius =
        enclosure_inner_radius + enclosure_thickness;
    double enclosure_cutout_width_x = 160 * mm;  // Width in x direction
    double enclosure_cutout_width_y = 280 * mm;  // Width in y direction
    double enclosure_length = fTargetLength;

    [[maybe_unused]] auto enclosure_outer_tube =
        new TGeoTube("enclosure_outer_tube", enclosure_inner_radius,
                     enclosure_outer_radius, enclosure_length / 2.);
    [[maybe_unused]] auto enclosure_cutout_box =
        new TGeoBBox("enclosure_cutout_box", enclosure_cutout_width_x / 2.,
                     enclosure_cutout_width_y / 2., enclosure_length / 2.);
    auto enclosure_shape = new TGeoCompositeShape(
        "enclosure_shape", "enclosure_outer_tube - enclosure_cutout_box");
    auto enclosure =
        new TGeoVolume("target_enclosure", enclosure_shape, steel316L);
    enclosure->SetLineColor(46);  // Reddish color for steel
    vessel->AddNode(
        enclosure, 1,
        new TGeoTranslation(
            0, 0, -vessel_length / 2. + vessel_shift + enclosure_length / 2.));

    // now place target inside He volume (and inside steel enclosure)
    //  Using nested volumes: tantalum cladding contains target core
    double cladding_width = 1.5 * mm;

    Double_t zPos = 0.;
    unsigned slots = fnS;
    if (slots > 0) slots = slots - 1;

    TGeoVolume* claddedTarget;
    TGeoVolume* targetCore;
    // Double_t zPos =  fTargetZ - fTargetLength/2.;
    for (unsigned i = 0; i < fnS; i++) {  // loop on layers
      TString nmi_cladded = "CladdedTarget_";
      nmi_cladded += i + 1;
      TString nmi_core = "TargetCore_";
      nmi_core += i + 1;

      TGeoMedium* material = nullptr;
      if (fM.at(i) == "molybdenum") {
        material = mo;
      } else if (fM.at(i) == "tungsten") {
        material = tungsten;
      }

      // Create outer cladded volume (tantalum, full dimensions)
      claddedTarget = gGeoManager->MakeTube(nmi_cladded, tantalum, 0.,
                                            fDiameter / 2., fL.at(i) / 2.);
      claddedTarget->SetLineColor(8);  // Green for tantalum

      // Create inner target core (W or Mo, reduced dimensions)
      // Positioned at centre (z=0) of cladded volume - tantalum fills the gaps
      // automatically
      targetCore = gGeoManager->MakeTube(nmi_core, material, 0.,
                                         fDiameter / 2. - cladding_width,
                                         (fL.at(i) - 2 * cladding_width) / 2.);
      if (fM.at(i) == "molybdenum") {
        targetCore->SetLineColor(28);
      } else {
        targetCore->SetLineColor(38);
      };  // silver/blue

      // Nest core inside cladding (at centre, z=0 in cladded volume's
      // coordinate system)
      claddedTarget->AddNode(targetCore, 1, new TGeoTranslation(0, 0, 0));

      // Place complete cladded target in He volume
      vessel->AddNode(
          claddedTarget, 1,
          new TGeoTranslation(
              0, 0, -vessel_length / 2. + vessel_shift + zPos + fL.at(i) / 2.));

      if (i < slots) {
        // slits will already be filled with He, no need to define volume
        zPos += fL.at(i) + fG.at(i);
      } else {
        zPos += fL.at(i);
      }
    }  // loop on layers

    // now add the He+target to the target area.
    tTarget->AddNode(
        vessel, 1,
        new TGeoTranslation(0, 0, -1. * vessel_shift + vessel_length / 2.));
  } else if (fDesign == 2) {
    // Design 2: 2026 BDF target, from CATIA model ST1A07710_01_AB.02.
    // Simplified to axisymmetric shapes. All z coordinates below are measured
    // from the front face of the first disk, which coincides with the local
    // z = 0 of the TargetArea assembly (global z = 0).
    if (fDiameter2 <= 0) {
      LOG(fatal) << "Target design 2 requires the last disk diameter, "
                    "use SetLastDiskDiameter()";
    }

    // He container: encloses steel core, jacket, flanges, beam window,
    // cover-plate bore rings and rear endcap
    const double he_zmin = -37.8 * mm;   // upstream face of the cover plate
    const double he_zmax = 1509.7 * mm;  // downstream end of rear endcap
    const double he_rmax = 237 * mm;     // rear flange outer radius
    const double he_zc = (he_zmin + he_zmax) / 2.;
    TGeoVolume* heVolume = gGeoManager->MakeTube("HeVolume", cooler, 0, he_rmax,
                                                 (he_zmax - he_zmin) / 2.);
    heVolume->SetLineColor(7);

    // Place a daughter so that it spans [z0, z1] on the axis
    auto placeAt = [he_zc](double z0, double z1) {
      return new TGeoTranslation(0, 0, (z0 + z1) / 2. - he_zc);
    };

    // W disks, no cladding; the last disk (rear block) is larger.
    // Added first so that the first daughter of HeVolume starts at the
    // target front face (FixedTargetGenerator fallback z extraction).
    Double_t zPos = 0.;
    for (unsigned i = 0; i < fnS; i++) {
      TString nmi_core = "TargetCore_";
      nmi_core += i + 1;
      TGeoMedium* material = nullptr;
      if (fM.at(i) == "molybdenum") {
        material = mo;
      } else if (fM.at(i) == "tungsten") {
        material = tungsten;
      }
      double radius = (i == fnS - 1) ? fDiameter2 / 2. : fDiameter / 2.;
      TGeoVolume* targetCore =
          gGeoManager->MakeTube(nmi_core, material, 0., radius, fL.at(i) / 2.);
      targetCore->SetLineColor(fM.at(i) == "molybdenum" ? 28 : 38);
      heVolume->AddNode(targetCore, 1, placeAt(zPos, zPos + fL.at(i)));
      zPos += fL.at(i) + fG.at(i);  // last gap is 0
    }

    // Steel core: the two clamp halves around the disks, modelled as one
    // axisymmetric piece with the He cooling grooves subtracted. The
    // composite shape is built in a frame where z = 0 is the target front
    // face; boolean members are placed with absolute-z translations.
    const double core_zmin = 7.2 * mm;
    const double core_zmax = 1443.7 * mm;
    const double core_rout = 207 * mm;
    const double bore_r1 = fDiameter / 2.;      // matches disks 1..nS-1
    const double bore_r2 = fDiameter2 / 2.;     // matches the last disk
    const double bore_step_z = 1005 * mm;       // bore radius change
    const double core_front_rout = 195 * mm;    // front, inside the flange
    const double core_front_zmax = 55.2 * mm;   // end of front step
    const double core_rear_rout = 190 * mm;     // rear, inside rear flange
    const double core_rear_zmin = 1233.7 * mm;  // start of rear step
    const double groove_rmax = 153 * mm;
    const double groove_phi = 61.;  // arc width in degrees, centred vertically
    const double margin = 5 * mm;   // avoid coincident boolean surfaces

    std::ostringstream core_expr;
    auto addTube = [&core_expr](const TString& name, double rmin, double rmax,
                                double z0, double z1, bool subtract) {
      new TGeoTube(name, rmin, rmax, (z1 - z0) / 2.);
      auto trans = new TGeoTranslation(name + "_tr", 0, 0, (z0 + z1) / 2.);
      trans->RegisterYourself();
      if (subtract) {
        core_expr << " - ";
      }
      core_expr << name << ":" << name << "_tr";
    };
    auto addGroove = [&core_expr](const TString& name, double rmin, double rmax,
                                  double z0, double z1, double phi1,
                                  double phi2) {
      new TGeoTubeSeg(name, rmin, rmax, (z1 - z0) / 2., phi1, phi2);
      auto trans = new TGeoTranslation(name + "_tr", 0, 0, (z0 + z1) / 2.);
      trans->RegisterYourself();
      core_expr << " - " << name << ":" << name << "_tr";
    };

    addTube("tgt_core_base", bore_r1, core_rout, core_zmin, core_zmax, false);
    addTube("tgt_core_front_step", core_front_rout, core_rout + margin,
            core_zmin - margin, core_front_zmax, true);
    addTube("tgt_core_rear_step", core_rear_rout, core_rout + margin,
            core_rear_zmin, core_zmax + margin, true);
    addTube("tgt_core_rear_bore", bore_r1 - margin, bore_r2, bore_step_z,
            core_zmax + margin, true);

    // Serpentine He cooling grooves: 61 degree arcs in the bore, staggered
    // between the upper and lower half; He flows between them through the
    // inter-disk slits.
    const std::vector<std::pair<double, double>> grooves_top = {{12.2, 57.0},
                                                                {95.0, 153.0},
                                                                {191.0, 257.0},
                                                                {300.0, 464.0},
                                                                {559.0, 933.2}};
    const std::vector<std::pair<double, double>> grooves_bottom = {
        {45.0, 104.7}, {142.7, 200.7}, {238.7, 334.7}, {385.7, 1005.0}};
    int grooveId = 0;
    for (const auto& [z0, z1] : grooves_top) {
      addGroove(TString::Format("tgt_groove_%d", grooveId++), bore_r1 - margin,
                groove_rmax, z0 * mm, z1 * mm, 90. - groove_phi / 2.,
                90. + groove_phi / 2.);
    }
    for (const auto& [z0, z1] : grooves_bottom) {
      addGroove(TString::Format("tgt_groove_%d", grooveId++), bore_r1 - margin,
                groove_rmax, z0 * mm, z1 * mm, 270. - groove_phi / 2.,
                270. + groove_phi / 2.);
    }
    // Groove around the rear block (upper half only), ends 2 mm before the
    // core rear face
    addGroove("tgt_groove_rear", bore_r2 - margin, 182 * mm, bore_step_z,
              1441.7 * mm, 90. - 49. / 2., 90. + 49. / 2.);

    auto core_shape =
        new TGeoCompositeShape("target_core_shape", core_expr.str().c_str());
    auto core = new TGeoVolume("target_core_steel", core_shape, steel316L);
    core->SetLineColor(46);  // Reddish color for steel
    heVolume->AddNode(core, 1, new TGeoTranslation(0, 0, -he_zc));

    // Outer jacket tube with front and rear flanges; the gap between the
    // core (r 207) and the jacket (r 217) is a He annulus. The flange bore
    // (r 195) matches the core front step, so the flange/jacket boundary is
    // placed at the end of the step (CAD: 64.2 mm, with a stepped flange
    // bore).
    const double jacket_zmin = core_front_zmax;
    const double jacket_zmax = 1198.7 * mm;
    auto jacket =
        gGeoManager->MakeTube("target_jacket", steel316L, 217 * mm, 225 * mm,
                              (jacket_zmax - jacket_zmin) / 2.);
    jacket->SetLineColor(46);
    heVolume->AddNode(jacket, 1, placeAt(jacket_zmin, jacket_zmax));
    // The flange proper starts at the cover-plate step; upstream of it the
    // outer radius is the r 195 nose that slides into the cover-plate bore
    const double flange_front_zmin = -23.8 * mm;
    const double nose_zmin = -35.8 * mm;  // upstream face of the vessel
    auto flangeFront =
        gGeoManager->MakeTube("target_flange_front", steel316L, core_front_rout,
                              225 * mm, (jacket_zmin - flange_front_zmin) / 2.);
    flangeFront->SetLineColor(46);
    heVolume->AddNode(flangeFront, 1, placeAt(flange_front_zmin, jacket_zmin));
    // Beam window: dished membrane closing the bore, 8 mm of steel on the
    // beam axis (z -33.5..-25.5); the dishing is simplified to a flat disc,
    // preserving the on-axis material budget. The r 141-195 nose ring
    // connects the window rim to the flange.
    const double window_rmax = 141 * mm;
    auto window = gGeoManager->MakeTube("target_front_window", steel316L, 0,
                                        window_rmax, (33.5 - 25.5) * mm / 2.);
    window->SetLineColor(46);
    heVolume->AddNode(window, 1, placeAt(-33.5 * mm, -25.5 * mm));
    auto nose = gGeoManager->MakeTube("target_front_nose", steel316L,
                                      window_rmax, core_front_rout,
                                      (flange_front_zmin - nose_zmin) / 2.);
    nose->SetLineColor(46);
    heVolume->AddNode(nose, 1, placeAt(nose_zmin, flange_front_zmin));
    // Cover plate (600 x 650 x 20 mm, stepped bore r 196/226): the part
    // within the He container radius is modelled as two rings here; the
    // rectangular remainder is added to the TargetArea below
    auto coverRing1 =
        gGeoManager->MakeTube("target_cover_ring1", steel316L, 196 * mm,
                              he_rmax, (flange_front_zmin - he_zmin) / 2.);
    coverRing1->SetLineColor(46);
    heVolume->AddNode(coverRing1, 1, placeAt(he_zmin, flange_front_zmin));
    auto coverRing2 =
        gGeoManager->MakeTube("target_cover_ring2", steel316L, 226 * mm,
                              he_rmax, (-17.8 * mm - flange_front_zmin) / 2.);
    coverRing2->SetLineColor(46);
    heVolume->AddNode(coverRing2, 1, placeAt(flange_front_zmin, -17.8 * mm));
    const double flange_rear_zmax = 1263.7 * mm;
    auto flangeRear =
        gGeoManager->MakeTube("target_flange_back", steel316L, 225 * mm,
                              he_rmax, (flange_rear_zmax - jacket_zmax) / 2.);
    flangeRear->SetLineColor(46);
    heVolume->AddNode(flangeRear, 1, placeAt(jacket_zmax, flange_rear_zmax));

    // Rear endcap: 8 mm shell, cylindrical section closed by a domed head,
    // approximated by three cone segments and an apex disc
    const double endcap_zmin = flange_rear_zmax;
    auto endcapTube =
        gGeoManager->MakeTube("target_endcap_tube", steel316L, 229 * mm,
                              237 * mm, (1413.7 * mm - endcap_zmin) / 2.);
    heVolume->AddNode(endcapTube, 1, placeAt(endcap_zmin, 1413.7 * mm));
    auto endcapDome1 = gGeoManager->MakeCone(
        "target_endcap_dome1", steel316L, (1450. - 1413.7) * mm / 2., 229 * mm,
        237 * mm, 212 * mm, 223 * mm);
    heVolume->AddNode(endcapDome1, 1, placeAt(1413.7 * mm, 1450. * mm));
    auto endcapDome2 = gGeoManager->MakeCone(
        "target_endcap_dome2", steel316L, (1480. - 1450.) * mm / 2., 212 * mm,
        223 * mm, 142 * mm, 166.5 * mm);
    heVolume->AddNode(endcapDome2, 1, placeAt(1450. * mm, 1480. * mm));
    auto endcapDome3 = gGeoManager->MakeCone("target_endcap_dome3", steel316L,
                                             (1505. - 1480.) * mm / 2.,
                                             142 * mm, 166.5 * mm, 0, 67 * mm);
    heVolume->AddNode(endcapDome3, 1, placeAt(1480. * mm, 1505. * mm));
    auto endcapCap =
        gGeoManager->MakeTube("target_endcap_cap", steel316L, 0, 67 * mm,
                              (he_zmax - 1505. * mm) / 2.);
    heVolume->AddNode(endcapCap, 1, placeAt(1505. * mm, he_zmax));
    for (auto* v :
         {endcapTube, endcapDome1, endcapDome2, endcapDome3, endcapCap}) {
      v->SetLineColor(46);
    }

    // Cover plate remainder outside the He container: rectangular plate,
    // asymmetric about the beam axis (x +-300, y -400..+250), with the
    // central hole covering the He container; the stepped bore is modelled
    // by the rings inside HeVolume above
    const double cover_y_offset = -75 * mm;  // plate centre below the axis
    [[maybe_unused]] auto cover_box =
        new TGeoBBox("target_cover_box", 300 * mm, 325 * mm, 10 * mm);
    [[maybe_unused]] auto cover_hole =
        new TGeoTube("target_cover_hole", 0, he_rmax, 11 * mm);
    auto cover_hole_shift =
        new TGeoTranslation("target_cover_hole_shift", 0, -cover_y_offset, 0);
    cover_hole_shift->RegisterYourself();
    auto cover_shape = new TGeoCompositeShape(
        "target_cover_shape",
        "target_cover_box - target_cover_hole:target_cover_hole_shift");
    auto coverPlate =
        new TGeoVolume("target_cover_plate", cover_shape, steel316L);
    coverPlate->SetLineColor(46);
    tTarget->AddNode(coverPlate, 1,
                     new TGeoTranslation(0, cover_y_offset, -27.8 * mm));

    // add the He + target to the target area
    tTarget->AddNode(heVolume, 1, new TGeoTranslation(0, 0, he_zc));
  } else {
    LOG(fatal) << "Unknown target design " << fDesign << ", expected 1 or 2";
  }

  // Proximity shielding

  double start_of_target = fTargetZ - fTargetLength / 2.;
  if (fShieldingReferenceLength <= 0) {
    LOG(fatal) << "Shielding reference length not set, "
                  "use SetShieldingReferenceLength()";
  }
  // Make shielding independent of actual target length
  fTargetLength = fShieldingReferenceLength;
  double shielding_width = 1600 * mm;
  double shielding_length = 3000 * mm;
  double proximity_shielding_height = 1126 * mm;
  double proximity_shielding_thickness = 250 * mm;
  double proximity_shielding_thickness_front = 550 * mm;
  double proximity_shielding_hole_diameter = 200 * mm;
  double proximity_shielding_hole_height = 735 * mm;
  double proximity_shielding_distance_after_target = 96.1 * mm;
  double top_shielding_height = 600 * mm;
  double bottom_shielding_height = 545 * mm;
  double shielding_position = start_of_target + fTargetLength +
                              proximity_shielding_distance_after_target +
                              proximity_shielding_thickness -
                              shielding_length / 2;
  double target_box_shift = 14.45 * cm;
  [[maybe_unused]] auto proximity_shielding_envelope =
      new TGeoBBox("proximity_shielding_envelope", shielding_width / 2,
                   proximity_shielding_height / 2, shielding_length / 2);
  [[maybe_unused]] auto proximity_shielding_inner = new TGeoBBox(
      "proximity_shielding_inner",
      shielding_width / 2 - proximity_shielding_thickness,
      proximity_shielding_height / 2,
      (shielding_length -
       (proximity_shielding_thickness_front + proximity_shielding_thickness)) /
          2);
  [[maybe_unused]] auto proximity_shielding_hole = new TGeoTube(
      "proximity_shielding_hole", 0, proximity_shielding_hole_diameter / 2,
      proximity_shielding_thickness_front / 2);
  auto proximity_shielding_inner_shift = new TGeoTranslation(
      "proximity_shielding_inner_shift", 0, 0,
      (proximity_shielding_thickness_front - proximity_shielding_thickness) /
          2);
  proximity_shielding_inner_shift->RegisterYourself();
  auto proximity_shielding_hole_shift = new TGeoTranslation(
      "proximity_shielding_hole_shift", 0,
      proximity_shielding_hole_height - proximity_shielding_height / 2,
      -shielding_length / 2 + proximity_shielding_thickness_front / 2);
  proximity_shielding_hole_shift->RegisterYourself();
  auto proximity_shielding_shape = new TGeoCompositeShape(
      "proximity_shielding_shape",
      "proximity_shielding_envelope"
      "- proximity_shielding_inner:proximity_shielding_inner_shift"
      "- proximity_shielding_hole:proximity_shielding_hole_shift");
  auto proximity_shielding =
      new TGeoVolume("proximity_shielding", proximity_shielding_shape, copper);
  auto proximity_shielding_centre = new TGeoTranslation(
      0.,
      -(proximity_shielding_hole_height - proximity_shielding_height / 2) +
          target_box_shift,
      0);

  auto target_vacuum_box =
      gGeoManager->MakeBox("target_vacuum_box", vacuum, shielding_width / 2,
                           (proximity_shielding_height + top_shielding_height +
                            bottom_shielding_height) /
                               2,
                           shielding_length / 2);
  auto vacuum_vessel_centre = new TGeoTranslation(
      0.,
      // -(proximity_shielding_hole_height - proximity_shielding_height / 2)
      //     + (bottom_shielding_height - top_shielding_height) / 2,
      -target_box_shift, shielding_position);
  top->AddNode(target_vacuum_box, 1, vacuum_vessel_centre);

  target_vacuum_box->AddNode(proximity_shielding, 1,
                             proximity_shielding_centre);

  // Top/bottom copper shielding
  auto top_shielding =
      gGeoManager->MakeBox("top_shielding", copper, shielding_width / 2,
                           top_shielding_height / 2, shielding_length / 2);
  target_vacuum_box->AddNode(
      top_shielding, 1,
      new TGeoTranslation(
          0.,
          top_shielding_height / 2 + proximity_shielding_height -
              proximity_shielding_hole_height + target_box_shift,
          0));
  auto bottom_shielding =
      gGeoManager->MakeBox("bottom_shielding", copper, shielding_width / 2,
                           bottom_shielding_height / 2, shielding_length / 2);
  target_vacuum_box->AddNode(
      bottom_shielding, 1,
      new TGeoTranslation(0.,
                          -bottom_shielding_height / 2 -
                              proximity_shielding_hole_height +
                              target_box_shift,
                          0));
  double pedestal_length = 2170 * mm;
  double pedestal_width = 1070 * mm;
  double pedestal_height = 150 * mm;
  auto shielding_pedestal =
      gGeoManager->MakeBox("shielding_pedestal", iron, pedestal_width / 2,
                           pedestal_height / 2, pedestal_length / 2);
  target_vacuum_box->AddNode(
      shielding_pedestal, 1,
      new TGeoTranslation(
          0.,
          pedestal_height / 2 - proximity_shielding_hole_height +
              target_box_shift,
          -shielding_length / 2 + 565 * mm + pedestal_length / 2));

  target_vacuum_box->AddNode(
      tTarget, 1,
      new TGeoTranslation(0, target_box_shift,
                          start_of_target - shielding_position));
}
