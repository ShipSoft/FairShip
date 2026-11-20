// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

// Straw-tube Upstream Background Tagger (UBT)

#include "UpstreamTaggerStraw.h"

#include <algorithm>
#include <array>
#include <cmath>
#include <iostream>
#include <utility>

#include "FairLogger.h"
#include "ShipDetectorList.h"
#include "ShipGeoUtil.h"
#include "ShipStack.h"
#include "ShipUnit.h"
#include "TGeoBBox.h"
#include "TGeoCompositeShape.h"
#include "TGeoManager.h"
#include "TGeoMatrix.h"
#include "TGeoMedium.h"
#include "TGeoTube.h"
#include "TLorentzVector.h"
#include "TMath.h"
#include "TParticle.h"
#include "TVirtualMC.h"
#include "UpstreamTaggerStrawPoint.h"

using ShipUnit::m;

UpstreamTaggerStraw::UpstreamTaggerStraw()
    : Detector("UpstreamTaggerStraw", kTRUE, kUpstreamTaggerStraw) {}

UpstreamTaggerStraw::UpstreamTaggerStraw(std::string medium)
    : Detector("UpstreamTaggerStraw", kTRUE, kUpstreamTaggerStraw),
      fMedium(std::move(medium)) {}

Bool_t UpstreamTaggerStraw::ProcessHits(FairVolume*) {
  // Store entry point and reset the energy loss when entering the gas
  if (gMC->IsTrackEntering()) {
    fELoss = 0.;
    fTime = gMC->TrackTime() * 1.0e09;
    fLength = gMC->TrackLength();
    gMC->TrackPosition(fPos);
    gMC->TrackMomentum(fMom);
  }
  fELoss += gMC->Edep();

  // Create a point when the track leaves the gas
  if (!(gMC->IsTrackExiting() || gMC->IsTrackStop() ||
        gMC->IsTrackDisappeared())) {
    return kTRUE;
  }
  if (fELoss == 0.) {
    return kFALSE;
  }

  fTrackID = gMC->GetStack()->GetCurrentTrackNumber();
  fEventID = gMC->CurrentEvent();
  Int_t uniqueId;
  gMC->CurrentVolID(uniqueId);  // copy number of the gas volume
  Int_t pdgCode = gMC->GetStack()->GetCurrentTrack()->GetPdgCode();

  TLorentzVector pos, mom;
  gMC->TrackPosition(pos);
  gMC->TrackMomentum(mom);
  TVector3 meanPos = 0.5 * (fPos.Vect() + pos.Vect());

  AddHit(fEventID, fTrackID, uniqueId, meanPos, fMom.Vect(), fTime, fLength,
         fELoss, pdgCode, pos.Vect(), mom.Vect());

  dynamic_cast<ShipStack*>(gMC->GetStack())->AddPoint(kUpstreamTaggerStraw);
  return kTRUE;
}

void UpstreamTaggerStraw::SetzPositions(Double_t z1) { f_T1_z = z1; }

void UpstreamTaggerStraw::SetApertureHeight(Double_t height) {
  f_aperture_height = height;
}

void UpstreamTaggerStraw::SetStrawDiameter(Double_t outer_straw_diameter,
                                           Double_t wall_thickness) {
  f_outer_straw_diameter = outer_straw_diameter;
  f_inner_straw_diameter = outer_straw_diameter - 2 * wall_thickness;
}

void UpstreamTaggerStraw::SetStrawPitch(Double_t straw_pitch,
                                        Double_t row_offset) {
  f_straw_pitch = straw_pitch;    // x-distance between straws in a row
  f_row_offset = row_offset;  // x-offset between the two rows
}

void UpstreamTaggerStraw::SetDeltazRow(Double_t delta_z_row) {
  f_delta_z_row = delta_z_row;
}

void UpstreamTaggerStraw::SetStereoAngle(Double_t stereo_angle) {
  f_view_angle = stereo_angle;
}

void UpstreamTaggerStraw::SetWireThickness(Double_t wire_thickness) {
  f_wire_thickness = wire_thickness;
}

void UpstreamTaggerStraw::SetDeltazView(Double_t delta_z_view) {
  f_delta_z_view = delta_z_view;
}

void UpstreamTaggerStraw::SetFrameMaterial(TString frame_material) {
  f_frame_material = frame_material;
}

void UpstreamTaggerStraw::SetSupportMaterial(TString support_material) {
  f_support_material = support_material;
}

void UpstreamTaggerStraw::SetSupportWallThickness(Double_t thickness) {
  f_support_wall_thickness = thickness;
}

void UpstreamTaggerStraw::SetFrameSize(Double_t width, Double_t height) {
  f_frame_width = width;
  f_frame_height = height;
}

void UpstreamTaggerStraw::SetFrameThickness(Double_t thickness) {
  f_frame_thickness = thickness;
}

void UpstreamTaggerStraw::SetFrameWallThickness(Double_t thickness) {
  f_frame_wall_thickness = thickness;
}

void UpstreamTaggerStraw::SetDeltazMid(Double_t delta_z_mid) {
  f_delta_z_mid = delta_z_mid;
}

void UpstreamTaggerStraw::SetSupportSize(Double_t width, Double_t depth) {
  f_support_width = width;
  f_support_depth = depth;
}

namespace {
TGeoMedium* GetMedium(const char* name) {
  ShipGeo::InitMedium(name);
  return gGeoManager->GetMedium(name);
}

const char* kViewSuffix[] = {"_y1", "_u", "_v"};
// Indexed by tier number hnb = 1 upper, 2 mid, 3 lower
const char* kTierSuffix[] = {"", "_upper", "_mid", "_lower"};
}  // namespace

Double_t UpstreamTaggerStraw::ViewAngle(Int_t vnb) const {
  const Double_t angles[] = {0., f_view_angle, -f_view_angle};
  return angles[vnb];
}

void UpstreamTaggerStraw::BuildLayer(TGeoVolume* station, Int_t vnb) {
  const Double_t dz = (vnb - 1) * f_delta_z_view;  // layers centred on 0
  for (Int_t hnb = 1; hnb <= 3; hnb++) {
    BuildSquare(station, vnb, hnb, fTierY[hnb - 1], fTierZ[hnb - 1] + dz);
  }
}

void UpstreamTaggerStraw::BuildSquare(TGeoVolume* station, Int_t vnb,
                                      Int_t hnb, Double_t y, Double_t z) {
  // Straws are vertical in the square's own frame; for the stereo layers the
  // whole square (box and frame) is rotated about z around its centre.
  const Double_t pitch = f_straw_pitch;
  const Double_t offset = f_row_offset;

  // As many straws per row as fit in +-half_width, counting the straw walls
  // and the offset between the two rows; then centre the pattern on x = 0.
  // Straw snb = 1 is at +x. Row 1 is shifted by +offset w.r.t. row 0.
  const Double_t half_width = fStrawHalfWidth;
  const Double_t radius = f_outer_straw_diameter / 2.;
  const Int_t straws_per_row =
      std::floor((2. * half_width - offset - 2. * radius) / pitch + 1e-9) + 1;
  const Double_t span = (straws_per_row - 1) * pitch + offset;  // centres
  const Double_t x_first = span / 2. - offset;  // row 0, snb = 1

  const Int_t squareId = hnb * 1e6 + vnb * 1e5;
  auto* box = new TGeoVolume(
      fStationName + kViewSuffix[vnb] + kTierSuffix[hnb], fViewShape,
      fBoxMedium);
  TGeoRotation square_rot;
  square_rot.RotateZ(ViewAngle(vnb));
  auto* placement =
      new TGeoCombiTrans(TGeoTranslation(0, y, z), square_rot);
  station->AddNode(box, squareId, placement);
  // Frame all around the square, as deep in z as the square
  station->AddNode(fFrame, squareId, placement);

  TGeoRotation rot;  // tube axis along y
  rot.SetAngles(0, 90, 0);
  // Two staggered rows of straws (rnb)
  for (Int_t rnb = 0; rnb < 2; rnb++) {
    for (Int_t snb = 1; snb <= straws_per_row; snb++) {
      TGeoTranslation trans(x_first + rnb * offset - (snb - 1) * pitch, 0,
                            (rnb - 0.5) * f_delta_z_row);
      auto* matrix = new TGeoHMatrix(TGeoCombiTrans(trans, rot));
      const Int_t id = squareId + rnb * 1e4 + snb;
      box->AddNode(fStraw, id + 1000, matrix);
      box->AddNode(fGas[vnb], id + 2000, matrix);
      box->AddNode(fWire, id + 3000, matrix);
    }
  }
}

TGeoShape* UpstreamTaggerStraw::MakeHollowBox(const TString& name,
					      Double_t half_x, Double_t half_y,
					      Double_t half_z,
					      Double_t thickness) {

  auto* outer = new TGeoBBox(name + "_outer", half_x, half_y, half_z);

  if (thickness < 1e-12)
    return outer;
  
  new TGeoBBox(name + "_inner", half_x-thickness,
	       half_y-thickness, half_z-thickness);  
  
  return new TGeoCompositeShape(name, Form("%s_outer - %s_inner", name.Data(), name.Data()));
}

void UpstreamTaggerStraw::BuildSupport(TGeoVolume* station,
                                       TGeoMedium* medium, Double_t z,
                                       Double_t inner_half_x,
                                       Double_t square_half_y,
                                       Double_t upright_half_y,
				       Double_t wall_thickness) {
  const Double_t eps = 0.0001;
  const Double_t half_w = f_support_width / 2.;
  const Double_t half_d = f_support_depth / 2.;

  
  // Uprights, left and right, just outside the squares
  auto* upright = new TGeoVolume(fStationName + "_upright",
				 MakeHollowBox("ubt_upright", half_w, upright_half_y, half_d, wall_thickness),
				 medium);

  upright->SetLineColor(kGray + 1);
  const Double_t x_upright = inner_half_x + half_w + eps;
  station->AddNode(upright, 1, new TGeoTranslation(-x_upright, 0, z));
  station->AddNode(upright, 2, new TGeoTranslation(+x_upright, 0, z));

  // Horizontal bars between the uprights. fTierY = {upper, mid, lower}.
  auto* bar = new TGeoVolume(
      fStationName + "_bar",
      MakeHollowBox("ubt_bar", inner_half_x, half_w, half_d, wall_thickness),
      medium);
  bar->SetLineColor(kGray + 1);
  const Double_t bar_y[] = {
      fTierY[0] + square_half_y - half_w,     // top of the upper square
      (fTierY[0] + fTierY[1]) / 2.,           // upper / mid overlap
      (fTierY[1] + fTierY[2]) / 2.,           // mid / lower overlap
      fTierY[2] - square_half_y + half_w};    // bottom of the lower square
  for (Int_t i = 0; i < 4; i++) {
    station->AddNode(bar, i + 1, new TGeoTranslation(0, bar_y[i], z));
  }
}

void UpstreamTaggerStraw::ConstructGeometry() {
  // Layout: one station made of 3 layers (views y1, u, v), delta_z_view
  // apart in z and centred on f_T1_z. Each layer is made of 3 squares
  // (upper, mid, lower) stacked in y to cover the aperture; the squares
  // overlap in y, so within each layer the middle square sits delta_z_mid
  // upstream of the other two. Each square holds 2 staggered rows of straws
  // and has its own frame; in the u and v layers it is rotated about z.
  //
  // Copy numbers (decoded downstream, do not change):
  //   square box, frame : hnb*1e6 + vnb*1e5
  //   straw/gas/wire : hnb*1e6 + vnb*1e5 + rnb*1e4 + {1,2,3}*1e3 + snb
  // with hnb = 1 upper, 2 mid, 3 lower.

  TGeoVolume* top = gGeoManager->GetTopVolume();
  TGeoMedium* mylar = GetMedium("mylar");
  TGeoMedium* gasMedium = GetMedium("UBTMixture");
  TGeoMedium* wireMedium = GetMedium("WReWire");
  TGeoMedium* frameMedium = GetMedium(f_frame_material.Data());
  TGeoMedium* supportMedium = GetMedium(f_support_material.Data());  
  fBoxMedium = GetMedium(fMedium.c_str());

  gGeoManager->SetVisLevel(4);
  gGeoManager->SetTopVisible();

  const Double_t eps = 0.0001;  // avoids overlapping volumes
  const Double_t floor_y = -3.36 * m;  // ECN3 cavern floor, see ShipCave

  // --- Tier positions in y ---
  // NOTE: the middle tier is raised by 15% of the y-extension of a straw of
  // full aperture height at the stereo angle (kept from the original layout)
  const Double_t tier_pitch = 2. * f_aperture_height / 3.;  // y between tiers
  const Double_t max_stereo_growth =
      std::tan(std::abs(f_view_angle) * TMath::DegToRad()) * f_aperture_height;
  const Double_t tier_y0_abs = 0.15 * max_stereo_growth;  // mid tier y

  // --- Square (two rows of straws) and its frame. The frame size is
  // configured; the straws fill the inside of the frame. The frame is as
  // deep in z as the square. ---
  const Double_t square_half_z =
      (f_delta_z_row + f_outer_straw_diameter) / 2. + eps;
  const Double_t frame_outer_x = f_frame_width / 2.;
  const Double_t frame_outer_y = f_frame_height / 2.;
  const Double_t frame_inner_x = frame_outer_x - f_frame_thickness;
  const Double_t frame_inner_y = frame_outer_y - f_frame_thickness;
  const Double_t tier_straw_half_length = frame_inner_y - 2. * eps;
  fStrawHalfWidth = frame_inner_x - 2. * eps;

  // Half-extent in x and y of a frame rotated by the stereo angle
  const Double_t stereo = std::abs(f_view_angle) * TMath::DegToRad();
  const Double_t rotated_half_x = frame_outer_x * std::cos(stereo) +
                                  frame_outer_y * std::sin(stereo);
  const Double_t rotated_half_y = frame_outer_x * std::sin(stereo) +
                                  frame_outer_y * std::cos(stereo);
  const Double_t frame_half_x = std::max(frame_outer_x, rotated_half_x);
  const Double_t frame_half_y = std::max(frame_outer_y, rotated_half_y);

  // --- Sanity checks ---
  if (frame_inner_x <= f_outer_straw_diameter ||
      frame_inner_y <= f_outer_straw_diameter) {
    LOG(fatal) << "UpstreamTaggerStraw: frame " << f_frame_width << " x "
               << f_frame_height << " cm is too small for thickness "
               << f_frame_thickness << " cm";
  }
  // Closest squares of neighbouring layers: the middle square of one layer
  // and the outer squares of the layer upstream of it
  if (f_delta_z_view - f_delta_z_mid <= 2. * square_half_z) {
    LOG(error) << "UpstreamTaggerStraw: layers overlap in z, need "
               << "delta_z_view - delta_z_mid > square depth "
               << 2. * square_half_z;
  }
  if (frame_half_y >= tier_pitch) {
    LOG(error) << "UpstreamTaggerStraw: upper and lower frames overlap in y";
  }
  if (tier_y0_abs - tier_pitch - frame_half_y <= floor_y) {
    LOG(error) << "UpstreamTaggerStraw: lower frames go below the floor";
  }
  if (2. * frame_half_y > tier_pitch && f_delta_z_mid <= 2. * square_half_z) {
    LOG(error) << "UpstreamTaggerStraw: middle square overlaps its "
               << "neighbours, increase delta_z_mid above "
               << 2. * square_half_z;
  }

  // --- Support plane, just downstream of the last layer ---
  const Double_t support_z =
      f_delta_z_view + square_half_z + f_support_depth / 2. + 2. * eps;

  // --- Station box: from the floor to the top of the upper frames, so not
  // centred on the squares in y. In z it is centred on the middle layer and
  // reaches the middle square of the first layer upstream and the supports
  // downstream. In x it includes the uprights. ---
  const Double_t station_half_z =
      std::max(f_delta_z_view + f_delta_z_mid + square_half_z,
               support_z + f_support_depth / 2.) +
      eps;
  const Double_t station_half_x = frame_half_x + f_support_width + 2. * eps;
  const Double_t station_top = tier_y0_abs + tier_pitch + frame_half_y + eps;
  const Double_t station_bottom = floor_y + eps;
  const Double_t station_y = (station_top + station_bottom) / 2.;
  const Double_t station_half_y = (station_top - station_bottom) / 2.;

  // Square centres w.r.t. the station and the layer centre, index hnb-1
  const Double_t tier_y0 = tier_y0_abs - station_y;
  fTierY = {tier_y0 + tier_pitch, tier_y0, tier_y0 - tier_pitch};
  fTierZ = {0., -f_delta_z_mid, 0.};

  // --- Station ---
  fStationNb = 1;
  fStationName = TString::Format("UpstreamTaggerStraw%d", fStationNb);
  auto* statbox = new TGeoBBox("ubt_statbox", station_half_x,
                               station_half_y, station_half_z);
  auto* station = new TGeoVolume(fStationName, statbox, fBoxMedium);
  top->AddNode(station, fStationNb,
               new TGeoTranslation(0, station_y, f_T1_z));

  // --- Pieces shared by all squares ---
  fViewShape = new TGeoBBox("ubt_viewbox", frame_inner_x - eps,
                            frame_inner_y - eps, square_half_z);

//   // Frame made from one solid ring
//   new TGeoBBox("ubt_detbox1", frame_outer_x, frame_outer_y, square_half_z);
//   new TGeoBBox("ubt_detbox2", frame_inner_x, frame_inner_y,
//                square_half_z + eps);
//   fFrame = new TGeoVolume(
//       fStationName + "_frame",
//       new TGeoCompositeShape("ubt_detcomp1", "ubt_detbox1 - ubt_detbox2"),
//       frameMedium);
//   fFrame->SetLineColor(kOrange);

  // Frame made from 4 hollow side bars, not one solid ring.
  fFrame = new TGeoVolumeAssembly(fStationName + "_frame");
  fFrame->SetLineColor(kOrange);

  const Double_t bar_z = square_half_z;

  auto* hbar = new TGeoVolume(
      fStationName + "_frame_hbar",
      MakeHollowBox("ubt_frame_hbar", frame_outer_x - f_frame_thickness,
                    f_frame_thickness / 2., bar_z, f_support_wall_thickness),
      frameMedium);
  hbar->SetLineColor(kOrange);

  auto* vbar = new TGeoVolume(
      fStationName + "_frame_vbar",
      MakeHollowBox("ubt_frame_vbar", f_frame_thickness / 2., frame_outer_y,
                    bar_z, f_support_wall_thickness),
      frameMedium);
  vbar->SetLineColor(kOrange);

  const Double_t x_bar = frame_outer_x - f_frame_thickness / 2.;
  const Double_t y_bar = frame_outer_y - f_frame_thickness / 2.;

  fFrame->AddNode(hbar, 1, new TGeoTranslation(0, +y_bar, 0));
  fFrame->AddNode(hbar, 2, new TGeoTranslation(0, -y_bar, 0));
  fFrame->AddNode(vbar, 3, new TGeoTranslation(+x_bar, 0, 0));
  fFrame->AddNode(vbar, 4, new TGeoTranslation(-x_bar, 0, 0));
  
  fStraw = new TGeoVolume(
      "ubt_straw",
      new TGeoTube("ubt_straw", f_inner_straw_diameter / 2.,
                   f_outer_straw_diameter / 2., tier_straw_half_length),
      mylar);
  fStraw->SetLineColor(5);
  fWire = new TGeoVolume(
      "ubt_wire",
      new TGeoTube("ubt_wire", 0., f_wire_thickness / 2.,
                   tier_straw_half_length - 4. * eps),
      wireMedium);
  fWire->SetLineColor(6);

  // Only the gas is sensitive. One volume per view, identical but for the
  // name.
  for (Int_t vnb = 0; vnb < 3; vnb++) {
    TString gasname = "ubt_gas_" + fStationName + kViewSuffix[vnb] + "_layer";
    fGas[vnb] = new TGeoVolume(
        gasname,
        new TGeoTube(gasname, f_wire_thickness / 2. + eps,
                     f_inner_straw_diameter / 2. - eps,
                     tier_straw_half_length - 2. * eps),
        gasMedium);
    fGas[vnb]->SetLineColor(5);
    AddSensitiveVolume(fGas[vnb]);
  }

  // --- The three layers ---
  for (Int_t vnb = 0; vnb < 3; vnb++) {
    BuildLayer(station, vnb);
  }

  // --- Support structure ---
  BuildSupport(station, supportMedium, support_z, frame_outer_x, frame_outer_y,
               station_half_y - eps, f_support_wall_thickness);
}
