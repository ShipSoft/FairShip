// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

// RPC Timing Detector
// 17/12/2019
// celso.franco@cern.ch

#include "UpstreamTaggerStraw.h"

#include <ROOT/TSeq.hxx>
#include <iostream>
#include <sstream>

#include "FairGeoBuilder.h"
#include "FairGeoInterface.h"
#include "FairGeoLoader.h"
#include "FairGeoMedia.h"
#include "FairGeoNode.h"
#include "FairGeoVolume.h"
#include "FairRootManager.h"
#include "FairRun.h"
#include "FairRuntimeDb.h"
#include "FairVolume.h"
#include "ShipDetectorList.h"
#include "ShipGeoUtil.h"
#include "ShipStack.h"
#include "TClonesArray.h"
#include "TGeoBBox.h"
#include "TGeoCompositeShape.h"
#include "TGeoManager.h"
#include "TGeoMaterial.h"
#include "TGeoMedium.h"
#include "TGeoTube.h"
#include "TMath.h"
#include "TParticle.h"
#include "TVector3.h"
#include "TVirtualMC.h"
#include "UpstreamTaggerStrawPoint.h"
using ROOT::TSeq;
using ShipUnit::cm;
using ShipUnit::m;
using std::cout;
using std::endl;

constexpr uint64_t hash(std::string_view str) {
  uint64_t hash = 0;
  for (char c : str) {
    hash = (hash * 131) + c;
  }
  return hash;
}

constexpr uint64_t operator"" _hash(const char* str, size_t len) {
  return hash(std::string_view(str, len));
}

constexpr const int detPieces(std::string_view pieceName) noexcept {
  switch (hash(pieceName)) {
    case "Upstream_Tagger_Plastic"_hash:
      return 0;
    case "ubt_gas_UBT1_y2_layer"_hash:
      return 1;
    case "ubt_gas_UBT1_v_layer"_hash:
      return 2;
    case "ubt_gas_UBT1_u_layer"_hash:
      return 3;
    case "ubt_gas_UBT1_y1_layer"_hash:
      return 4;
    default:
      return 10;
  }
}

UpstreamTaggerStraw::UpstreamTaggerStraw(std::string medium)
    : Detector("UpstreamTaggerStraw", kTRUE, kUpstreamTaggerStraw),
      fMedium(medium),
      det_zPos(0),
      UpstreamTaggerStraw_fulldet(0) {}

UpstreamTaggerStraw::UpstreamTaggerStraw()
    : Detector("UpstreamTaggerStraw", kTRUE, kUpstreamTaggerStraw),
      det_zPos(0),
      UpstreamTaggerStraw_fulldet(nullptr) {}

UpstreamTaggerStraw::UpstreamTaggerStraw(const char* name, Bool_t active)
    : Detector(name, active, kUpstreamTaggerStraw),
      det_zPos(0),
      UpstreamTaggerStraw_fulldet(nullptr) {}

Bool_t UpstreamTaggerStraw::ProcessHits(FairVolume* vol) {
  /** This method is called from the MC stepping */
  // Set parameters at entrance of volume. Reset ELoss.
  if (gMC->IsTrackEntering()) {
    fELoss = 0.;
    fTime = gMC->TrackTime() * 1.0e09;
    fLength = gMC->TrackLength();
    gMC->TrackPosition(fPos);
    gMC->TrackMomentum(fMom);
  }
  // Sum energy loss for all steps in the active volume
  fELoss += gMC->Edep();

  fELoss += 0.0001;

  // Create vetoPoint at exit of active volume
  if (gMC->IsTrackExiting() || gMC->IsTrackStop() ||
      gMC->IsTrackDisappeared()) {
    if (fELoss == 0.) {
      return kFALSE;
    }

    fTrackID = gMC->GetStack()->GetCurrentTrackNumber();
    fEventID = gMC->CurrentEvent();
    Int_t uniqueId;
    gMC->CurrentVolID(uniqueId);
    const char* volName = gMC->CurrentVolName();
    //    std::cout<<"volume id: "<<uniqueId<<" - name: "<<volName<<std::endl;
    int subDetID = detPieces(volName);
    if (uniqueId > 1000000)  // Solid scintillator case
    {
      Int_t vcpy;
      gMC->CurrentVolOffID(1, vcpy);
      if (vcpy == 5) uniqueId += 4;  // Copy of half
    }

    TParticle* p = gMC->GetStack()->GetCurrentTrack();
    Int_t pdgCode = p->GetPdgCode();
    TLorentzVector Pos;
    gMC->TrackPosition(Pos);
    TLorentzVector Mom;
    gMC->TrackMomentum(Mom);
    Double_t xmean = (fPos.X() + Pos.X()) / 2.;
    Double_t ymean = (fPos.Y() + Pos.Y()) / 2.;
    Double_t zmean = (fPos.Z() + Pos.Z()) / 2.;

    AddHit(fEventID, fTrackID, uniqueId, TVector3(xmean, ymean, zmean),
           TVector3(fMom.Px(), fMom.Py(), fMom.Pz()), fTime, fLength, fELoss,
           pdgCode, TVector3(Pos.X(), Pos.Y(), Pos.Z()),
           TVector3(Mom.Px(), Mom.Py(), Mom.Pz()));

    // Increment number of veto det points in TParticle
    ShipStack* stack = dynamic_cast<ShipStack*>(gMC->GetStack());
    stack->AddPoint(kUpstreamTaggerStraw);
  }

  return kTRUE;
}

void UpstreamTaggerStraw::SetzPositions(Double_t z1) {
  f_T1_z = z1;  //!  z-position of tracking station 1
}

void UpstreamTaggerStraw::SetApertureArea(Double_t width, Double_t height,
                                     Double_t length) {
  f_aperture_width = width;    //!  Aperture width (x)
  f_aperture_height = height;  //!  Aperture height (y)
  f_station_length = length;
}

void UpstreamTaggerStraw::SetStrawDiameter(Double_t outer_straw_diameter,
                                      Double_t wall_thickness) {
  f_outer_straw_diameter = outer_straw_diameter;  //!  Outer straw diameter
  f_inner_straw_diameter =
      outer_straw_diameter - 2 * wall_thickness;  //!  Inner straw diameter
}

void UpstreamTaggerStraw::SetStrawPitch(Double_t straw_pitch,
                                   Double_t layer_offset) {
  f_straw_pitch = straw_pitch;    //!  Distance (y) between straws in a layer
  f_offset_layer = layer_offset;  //!  Offset (y) of straws between layers
}

void UpstreamTaggerStraw::SetDeltazLayer(Double_t delta_z_layer) {
  f_delta_z_layer = delta_z_layer;  //!  Distance (z) between layers
}

void UpstreamTaggerStraw::SetStereoAngle(Double_t stereo_angle) {
  f_view_angle = stereo_angle;  //!  Stereo view angle
}

void UpstreamTaggerStraw::SetWireThickness(Double_t wire_thickness) {
  f_wire_thickness = wire_thickness;  //!  Sense wire thickness
}

void UpstreamTaggerStraw::SetDeltazView(Double_t delta_z_view) {
  f_delta_z_view = delta_z_view;  //!  Distance (z) between stereo views
}

void UpstreamTaggerStraw::SetFrameMaterial(TString frame_material) {
  f_frame_material = frame_material;  //!  Structure frame material
}

void UpstreamTaggerStraw::ConstructGeometry() {
  /** If you are using the standard ASCII input for the geometry
       just copy this and use it for your detector, otherwise you can
       implement here you own way of constructing the geometry. */

  std::cout << "Making a geometry" << std::endl;

  TGeoVolume* top = gGeoManager->GetTopVolume();
  ShipGeo::InitMedium("air");
  TGeoMedium* air = gGeoManager->GetMedium("air");
  ShipGeo::InitMedium("mylar");
  TGeoMedium* mylar = gGeoManager->GetMedium("mylar");

  ShipGeo::InitMedium("UBTMixture");
  TGeoMedium* sttmix8020_1bar = gGeoManager->GetMedium("UBTMixture");
  ShipGeo::InitMedium("WReWire");
  TGeoMedium* WReWire = gGeoManager->GetMedium("WReWire");
  ShipGeo::InitMedium(f_frame_material);

  TGeoMedium* FrameMatPtr = gGeoManager->GetMedium(f_frame_material);
  ShipGeo::InitMedium(fMedium.c_str());
  TGeoMedium* med = gGeoManager->GetMedium(fMedium.c_str());

  gGeoManager->SetVisLevel(4);
  gGeoManager->SetTopVisible();

  Double_t eps = 0.0001;  // Epsilon to avoid overlapping volumes
  Double_t straw_length =
      f_aperture_height;         // + 2. * eps; // Straw (half) length
  Double_t frame_width = 3.;   // Width of frame metal
  Double_t floor_offset = 14.;  // Offset due to floor space limitation
  Double_t max_stereo_growth =
      TMath::Tan(TMath::Abs(f_view_angle) * TMath::Pi() / 180.0) * straw_length;
  // Three tiers of straws (upper, mid and lower) cover the aperture height
  Double_t straw_half_length = straw_length / 2. - 5.;
  // Half-length of the straws of one tier
  Double_t tier_straw_half_length = straw_half_length * (2. / 3.) + 10.;
  // y-distance between the centres of two neighbouring tiers
  Double_t tier_pitch = 2. * straw_length / 3.;
  // y-position (absolute) of the middle tier
  Double_t tier_y0_abs = 0.15 * max_stereo_growth;
  // The tiers overlap in y, so the middle tier is displaced in z
  Double_t mid_tier_dz = -30.;
  // Half-heights of the frame opening and of the frame. The opening is
  // slightly larger than the box containing the straws of the tier.
  Double_t frame_inner_y = tier_straw_half_length + 2. * eps;
  Double_t frame_outer_y = frame_inner_y + frame_width + floor_offset / 2.;
  Double_t frame_half_length = f_station_length * 0.5;
  // The station box is tight around the three tiers, so it is not centred
  // on f_T1_z
  Double_t station_dz = mid_tier_dz / 2.;
  // Half-sizes of the vertical supports, which sit against the outer z-faces
  // of the frames
  Double_t support_half_x = 5.;
  Double_t support_half_z = 2.;
  Double_t station_half_z = frame_half_length + TMath::Abs(mid_tier_dz) / 2. +
                            2. * support_half_z + 2. * eps;
  // y-position (absolute) of the ECN3 cavern floor, see ShipCave. The
  // supports stand on it.
  Double_t floor_y = -3.36 * m;
  Double_t support_bottom = floor_y + 2. * eps;
  Double_t support1_top = tier_y0_abs + f_aperture_height + floor_offset;
  // Level with the top of the middle frame
  Double_t support2_top = tier_y0_abs + frame_outer_y;
  // The station box reaches from the floor to the top of the upper frame, so
  // it is not centred on the tiers in y either
  Double_t station_top = tier_y0_abs + tier_pitch + frame_outer_y + eps;
  Double_t station_bottom = floor_y + eps;
  Double_t station_y = (station_top + station_bottom) / 2.;
  Double_t station_half_y = (station_top - station_bottom) / 2.;
  // y-position of the middle tier w.r.t. the station
  Double_t tier_y0 = tier_y0_abs - station_y;

  // Arguments of boxes are half-lengths
  TGeoBBox* detbox1 = new TGeoBBox("ubt_detbox1", f_aperture_width,
                                   frame_outer_y,  // Top and bottom frame only
                                   frame_half_length);
  TGeoBBox* detbox2 = new TGeoBBox("ubt_detbox2", f_aperture_width + eps,
                                   frame_inner_y, frame_half_length + eps);

  TGeoBBox* support1 =
      new TGeoBBox("ubt_support1", support_half_x,
                   (support1_top - support_bottom) / 2., support_half_z);
  TGeoBBox* support2 =
      new TGeoBBox("ubt_support2", support_half_x,
                   (support2_top - support_bottom) / 2., support_half_z);

  // Composite shape to create frame: one bar above and one below the straws
  // of a tier
  TGeoCompositeShape* detcomp1 =
      new TGeoCompositeShape("ubt_detcomp1", "ubt_detbox1 - ubt_detbox2");

  // Volume: straw - Third argument is half-length of tube
  TGeoTube* straw_tube =
      new TGeoTube("ubt_straw", f_inner_straw_diameter / 2.,
                   f_outer_straw_diameter / 2., tier_straw_half_length);
  TGeoVolume* straw = new TGeoVolume("ubt_straw", straw_tube, mylar);
  straw->SetLineColor(4);
  // Volume: wire
  TGeoTube* wire_tube = new TGeoTube("ubt_wire", 0., f_wire_thickness / 2.,
                                     tier_straw_half_length - 4. * eps);
  TGeoVolume* wire = new TGeoVolume("ubt_wire", wire_tube, WReWire);
  wire->SetLineColor(6);

  // Station box to contain all components
  TGeoBBox* statbox =
      new TGeoBBox("ubt_statbox", f_aperture_width + 4. * eps, station_half_y,
                   station_half_z);
  f_frame_material.ToLower();

  // statnb = station number; vnb = view number; hnb = tier number (1 = upper,
  // 2 = mid, 3 = lower set of straws); lnb = layer number; snb = straw number
  Int_t statnb = 1;
  TString nmstation = "UBTStraw";
  nmstation += statnb;

  TGeoVolume* vol = new TGeoVolume(nmstation, statbox, med);
  // Translate the station to its (absolute) position
  top->AddNode(vol, statnb,
               new TGeoTranslation(0, station_y, f_T1_z + station_dz));

  // One frame per tier, centred on the straws of the tier
  TGeoVolume* statframe =
      new TGeoVolume(nmstation + "_bottomframe", detcomp1, FrameMatPtr);
  statframe->SetLineColor(kOrange);
  vol->AddNode(statframe, statnb * 1e6,
               new TGeoTranslation(0, tier_y0 - tier_pitch, -station_dz));

  TGeoVolume* midframe =
      new TGeoVolume(nmstation + "_midframe", detcomp1, FrameMatPtr);
  midframe->SetLineColor(kOrange);
  vol->AddNode(midframe, statnb * 1e6 + 1,
               new TGeoTranslation(0, tier_y0, mid_tier_dz - station_dz));

  TGeoVolume* topframe =
      new TGeoVolume(nmstation + "_topframe", detcomp1, FrameMatPtr);
  topframe->SetLineColor(kOrange);
  vol->AddNode(topframe, statnb * 1e6 + 2,
               new TGeoTranslation(0, tier_y0 + tier_pitch, -station_dz));

  // Vertical supports standing on the floor: one flush against the downstream
  // face of the upper and lower frames, the other flush against the upstream
  // face of the middle frame
  TGeoVolume* leftsupportframe =
      new TGeoVolume(nmstation + "_leftsupportframe", support1, FrameMatPtr);
  leftsupportframe->SetLineColor(kOrange);
  vol->AddNode(leftsupportframe, statnb * 1e6 + 3,
               new TGeoTranslation(
                   0, (support1_top + support_bottom) / 2. - station_y,
                   -station_dz + frame_half_length + support_half_z + eps));
  TGeoVolume* rightsupportframe =
      new TGeoVolume(nmstation + "_rightsupportframe", support2, FrameMatPtr);
  rightsupportframe->SetLineColor(kOrange);
  vol->AddNode(rightsupportframe, statnb * 1e6 + 4,
               new TGeoTranslation(
                   0, (support2_top + support_bottom) / 2. - station_y,
                   mid_tier_dz - station_dz - frame_half_length -
                       support_half_z - eps));

  // Loop over the 4 stereo layers
  for (Int_t vnb = 0; vnb < 4; vnb++) {
    // View loop
    TString nmview;
    Double_t angle;
    Double_t stereo_growth;
    Double_t stereo_pitch;
    Double_t offset_layer;
    Int_t straws_per_layer;

    switch (vnb) {
      case 0:
        angle = 0.;
        nmview = nmstation + "_y1";
        break;
      case 1:
        angle = f_view_angle;
        nmview = nmstation + "_u";
        break;
      case 2:
        angle = -f_view_angle;
        nmview = nmstation + "_v";
        break;
      case 3:
        angle = 0.;
        nmview = nmstation + "_y2";
        break;
      default:
        angle = 0.;
        nmview = nmstation + "_y1";
    }
    angle = 0;
    // Adjustments in the stereo views
    // stereo_growth: extension of stereo views beyond aperture
    // stereo_pitch: straw pitch in stereo views
    // offset_layer: layer offset in stereo views
    // straws_per_layer: number of straws in one layer with stereo extension
    // If angle == 0., all numbers return the case of non-stereo views.
    stereo_growth =
        TMath::Tan(TMath::Abs(angle) * TMath::Pi() / 180.0) * straw_length;
    stereo_pitch =
        f_straw_pitch / TMath::Cos(TMath::Abs(angle) * TMath::Pi() / 180.0);
    offset_layer =
        f_offset_layer / TMath::Cos(TMath::Abs(angle) * TMath::Pi() / 180.0);
    straws_per_layer =
        std::floor((f_aperture_width + stereo_growth) / stereo_pitch);
    std::cout << "straws_per_layer: " << straws_per_layer
              << " - width: " << f_aperture_width
              << " - stereo pitch: " << stereo_pitch << std::endl;

    // Volume: gas - Only the gas is sensitive
    TString gasname = "ubt_gas_" + nmview + "_layer";
    TGeoTube* gas_tube = new TGeoTube(gasname, f_wire_thickness / 2. + eps,
                                      f_inner_straw_diameter / 2. - eps,
                                      tier_straw_half_length - 2. * eps);
    TGeoVolume* gas = new TGeoVolume(gasname, gas_tube, sttmix8020_1bar);
    gas->SetLineColor(5);
    AddSensitiveVolume(gas);

    // Box containing the two staggered layers of one tier of straws
    TGeoBBox* viewshape = new TGeoBBox(
        "ubt_viewbox", f_aperture_width + eps, tier_straw_half_length + eps,
        (f_delta_z_layer + f_outer_straw_diameter) / 2. + eps);

    // Upper, middle and lower tiers of straws
    for (Int_t hnb = 1; hnb < 4; hnb++) {
      TString nmhalf = nmview;
      if (hnb == 1)
        nmhalf += "_upper";
      else if (hnb == 2)
        nmhalf += "_mid";
      else
        nmhalf += "_lower";
      Double_t y_offset = (2 - hnb) * tier_pitch;
      Double_t z_offset = (hnb == 2) ? mid_tier_dz : 0.;
      TGeoVolume* viewbox = new TGeoVolume(nmhalf, viewshape, med);
      // Translate the view w.r.t. the station
      vol->AddNode(viewbox, hnb * 1e6 + vnb * 1e5,
                   new TGeoTranslation(0, tier_y0 + y_offset,
                                       (vnb - 3. / 2.) * f_delta_z_view +
                                           z_offset - station_dz));

      // Two layers of straws per view
      for (Int_t lnb = 0; lnb < 2; lnb++) {
        // Layer loop
        TGeoRotation r6s;
        TGeoTranslation t6s;
        // Loop over the straws
        for (Int_t snb = 1; snb <= 2 * straws_per_layer; snb++) {
          // x-translate the straw to its position, z-translate to its layer
          t6s.SetTranslation(f_aperture_width + stereo_growth +
                                 lnb * offset_layer - snb * stereo_pitch,
                             0, (lnb - 1. / 2.) * f_delta_z_layer);
          // Rotate the straw with stereo angle
          r6s.SetAngles(0 + angle, 90, 0);
          TGeoCombiTrans c6s(t6s, r6s);
          TGeoHMatrix* h6s = new TGeoHMatrix(c6s);
          viewbox->AddNode(straw,
                           hnb * 1e6 + vnb * 1e5 + lnb * 1e4 + 1e3 + snb, h6s);
          viewbox->AddNode(gas, hnb * 1e6 + vnb * 1e5 + lnb * 1e4 + 2e3 + snb,
                           h6s);
          viewbox->AddNode(wire, hnb * 1e6 + vnb * 1e5 + lnb * 1e4 + 3e3 + snb,
                           h6s);
        }
        // End of layer loop
      }
      // End of half loop
    }
    // End of view loop
  }
/*
  // Scoring planes downstream and upstream of the station
  ShipGeo::InitMedium("vacuum");
  TGeoMedium* Vacuum_box = gGeoManager->GetMedium("vacuum");
  UpstreamTaggerStraw_plastic = gGeoManager->MakeBox(
      "Upstream_Tagger_Straw_Plastic_Downstream", Vacuum_box, 4.0 * m, 2.0 * m, 1);
  UpstreamTaggerStraw_plastic->SetLineColor(kGreen);
  top->AddNode(UpstreamTaggerStraw_plastic, 1,
               new TGeoTranslation(0.0, 0.0, f_T1_z + 40));
  AddSensitiveVolume(UpstreamTaggerStraw_plastic);

  UpstreamTaggerStraw_plastic_forward = gGeoManager->MakeBox(
      "Upstream_Tagger_Straw_Plastic_Upstream", Vacuum_box, 4.0 * m, 2.0 * m, 1);
  UpstreamTaggerStraw_plastic_forward->SetLineColor(kGreen);
  // Just upstream of the station box, which extends further upstream than
  // downstream because of the displaced middle tier
  top->AddNode(UpstreamTaggerStraw_plastic_forward, 1,
               new TGeoTranslation(0.0, 0.0,
                                   f_T1_z + station_dz - station_half_z - 10));
  AddSensitiveVolume(UpstreamTaggerStraw_plastic_forward);
*/
}
