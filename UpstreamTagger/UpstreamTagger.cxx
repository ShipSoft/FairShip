// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

// RPC Timing Detector
// 17/12/2019
// celso.franco@cern.ch

#include "UpstreamTagger.h"

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
#include "UpstreamTaggerPoint.h"
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

UpstreamTagger::UpstreamTagger(std::string medium)
    : Detector("UpstreamTagger", kTRUE, kUpstreamTagger),
      fMedium(medium),
      det_zPos(0),
      UpstreamTagger_fulldet(0) {}

UpstreamTagger::UpstreamTagger()
    : Detector("UpstreamTagger", kTRUE, kUpstreamTagger),
      det_zPos(0),
      UpstreamTagger_fulldet(0) {}

UpstreamTagger::UpstreamTagger(const char* name, Bool_t active)
    : Detector(name, active, kUpstreamTagger),
      det_zPos(0),
      UpstreamTagger_fulldet(0) {}

Bool_t UpstreamTagger::ProcessHits(FairVolume* vol) {
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

  //  fELoss += 0.0001;

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
    stack->AddPoint(kUpstreamTagger);
  }

  return kTRUE;
}

void UpstreamTagger::SetzPositions(Double_t z1) {
  f_T1_z = z1;  //!  z-position of tracking station 1
}

void UpstreamTagger::SetApertureArea(Double_t width, Double_t height,
                                     Double_t length) {
  f_aperture_width = width;    //!  Aperture width (x)
  f_aperture_height = height;  //!  Aperture height (y)
  f_station_length = length;
}

void UpstreamTagger::SetStrawDiameter(Double_t outer_straw_diameter,
                                      Double_t wall_thickness) {
  f_outer_straw_diameter = outer_straw_diameter;  //!  Outer straw diameter
  f_inner_straw_diameter =
      outer_straw_diameter - 2 * wall_thickness;  //!  Inner straw diameter
}

void UpstreamTagger::SetStrawPitch(Double_t straw_pitch,
                                   Double_t layer_offset) {
  f_straw_pitch = straw_pitch;    //!  Distance (y) between straws in a layer
  f_offset_layer = layer_offset;  //!  Offset (y) of straws between layers
}

void UpstreamTagger::SetDeltazLayer(Double_t delta_z_layer) {
  f_delta_z_layer = delta_z_layer;  //!  Distance (z) between layers
}

void UpstreamTagger::SetStereoAngle(Double_t stereo_angle) {
  f_view_angle = stereo_angle;  //!  Stereo view angle
}

void UpstreamTagger::SetWireThickness(Double_t wire_thickness) {
  f_wire_thickness = wire_thickness;  //!  Sense wire thickness
}

void UpstreamTagger::SetDeltazView(Double_t delta_z_view) {
  f_delta_z_view = delta_z_view;  //!  Distance (z) between stereo views
}

void UpstreamTagger::SetFrameMaterial(TString frame_material) {
  f_frame_material = frame_material;  //!  Structure frame material
}

void UpstreamTagger::ConstructGeometry() {
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
      f_aperture_width;         // + 2. * eps; // Straw (half) length
  Double_t frame_width = 20.;   // Width of frame metal
  Double_t floor_offset = 14.;  // Offset due to floor space limitation
  Double_t rmin, rmax, T_station_z;
  Double_t max_stereo_growth =
      TMath::Tan(TMath::Abs(f_view_angle) * TMath::Pi() / 180.0) * straw_length;

  // Arguments of boxes are half-lengths
  TGeoBBox* detbox1 = new TGeoBBox(
      "ubt_detbox1", (straw_length + frame_width),
      (f_aperture_height + 4 * max_stereo_growth /* + frame_width */ -
       floor_offset / 2.),  // No top and bottom frame
      f_station_length);
  TGeoBBox* detbox2 = new TGeoBBox(
      "ubt_detbox2", (straw_length + eps),
      (f_aperture_height + 4 * max_stereo_growth - floor_offset / 2. + eps),
      f_station_length + eps);

  TGeoTranslation* move_up =
      new TGeoTranslation("ubt_move_up", 0, floor_offset / 2., 0);
  move_up->RegisterYourself();

  // Composite shape to create frame
  TGeoCompositeShape* detcomp1 = new TGeoCompositeShape(
      "ubt_detcomp1", "ubt_detbox1:ubt_move_up - ubt_detbox2:ubt_move_up");

  // Volume: straw - Third argument is half-length of tube
  TGeoTube* straw_tube =
      new TGeoTube("ubt_straw", f_inner_straw_diameter / 2.,
                   f_outer_straw_diameter / 2., straw_length);
  TGeoVolume* straw = new TGeoVolume("ubt_straw", straw_tube, mylar);
  straw->SetLineColor(4);
  // Volume: gas - Only the gas is sensitive
  //    TGeoTube *gas_tube = new TGeoTube("ubt_gas", f_wire_thickness / 2. +
  //    eps, f_inner_straw_diameter / 2. - eps, straw_length - 2. * eps);
  //    TGeoVolume *gas = new TGeoVolume("ubt_gas", gas_tube, sttmix8020_1bar);
  //    gas->SetLineColor(5);
  //    AddSensitiveVolume(gas);
  // Volume: wire
  TGeoTube* wire_tube = new TGeoTube("ubt_wire", 0., f_wire_thickness / 2.,
                                     straw_length - 4. * eps);
  TGeoVolume* wire = new TGeoVolume("ubt_wire", wire_tube, WReWire);
  wire->SetLineColor(6);

  // Station box to contain all components
  TGeoBBox* statbox =
      new TGeoBBox("ubt_statbox", straw_length + frame_width,
                   f_aperture_height + frame_width + 4 * max_stereo_growth -
                       floor_offset / 2.,
                   f_station_length);
  f_frame_material.ToLower();

  for (Int_t statnb = 1; statnb < 2; statnb++) {
    // Tracking station loop
    TString nmstation = "UBT";
    std::stringstream ss;
    ss << statnb;
    nmstation = nmstation + ss.str();
    switch (statnb) {
      case 1:
        T_station_z = f_T1_z;
        break;
      default:
        T_station_z = f_T1_z;
    }

    TGeoVolume* vol = new TGeoVolume(nmstation, statbox, med);
    // z-translate the station to its (absolute) position
    top->AddNode(vol, statnb,
                 new TGeoTranslation(0, floor_offset / 2., T_station_z));

    TGeoVolume* statframe =
        new TGeoVolume(nmstation + "_frame", detcomp1, FrameMatPtr);
    vol->AddNode(statframe, statnb * 1e6,
                 new TGeoTranslation(0, -floor_offset / 2., 0));
    statframe->SetLineColor(kOrange);
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
          std::floor(2 * (f_aperture_height + stereo_growth) / stereo_pitch);

      // Two sets of straws per layer
      for (Int_t lnb = 0; lnb < 2; lnb++) {
        // Layer loop
        TString nmlayer = nmview + "_layer";
        TString gasname = "ubt_gas_" + nmlayer;

        // Volume: gas - Only the gas is sensitive
        TGeoTube* gas_tube = new TGeoTube(gasname, f_wire_thickness / 2. + eps,
                                          f_inner_straw_diameter / 2. - eps,
                                          straw_length - 2. * eps);
        TGeoVolume* gas = new TGeoVolume(gasname, gas_tube, sttmix8020_1bar);
        gas->SetLineColor(5);
        AddSensitiveVolume(gas);
        nmlayer += lnb;

        TGeoBBox* layer = new TGeoBBox(
            "layer box", straw_length + eps / 4,
            f_aperture_height + stereo_growth * 2 + offset_layer + eps / 4,
            f_outer_straw_diameter / 2. + eps / 4);
        TGeoVolume* layerbox = new TGeoVolume(nmlayer, layer, med);

        // The layer box sits in the viewframe.
        // Hence, z-translate the layer w.r.t. the view
        vol->AddNode(
            layerbox, statnb * 1e6 + vnb * 1e5 + lnb * 1e4,
            new TGeoTranslation(0, -floor_offset / 2.,
                                (vnb - 3. / 2.) * f_delta_z_view +
                                    (lnb - 1. / 2.) * f_delta_z_layer));

        TGeoRotation r6s;
        TGeoTranslation t6s;
        // Loop over the straws
        for (Int_t snb = 1; snb <= straws_per_layer; snb++) {
          // y-translate the straw to its position
          t6s.SetTranslation(0,
                             f_aperture_height + stereo_growth -
                                 (snb - 1. / 2.) * stereo_pitch +
                                 lnb * offset_layer,
                             0);
          // Rotate the straw with stereo angle
          r6s.SetAngles(90 + angle, 90, 0);
          TGeoCombiTrans c6s(t6s, r6s);
          TGeoHMatrix* h6s = new TGeoHMatrix(c6s);
          layerbox->AddNode(
              straw, statnb * 1e6 + vnb * 1e5 + lnb * 1e4 + 1e3 + snb, h6s);
          layerbox->AddNode(
              gas, statnb * 1e6 + vnb * 1e5 + lnb * 1e4 + 2e3 + snb, h6s);
          layerbox->AddNode(
              wire, statnb * 1e6 + vnb * 1e5 + lnb * 1e4 + 3e3 + snb, h6s);
        }

        if (lnb == 1) {
          // Add one more straw at the bottom of the second layer to cover
          // aperture entirely
          t6s.SetTranslation(0,
                             f_aperture_height + stereo_growth -
                                 (straws_per_layer - 1. / 2.) * stereo_pitch -
                                 lnb * offset_layer,
                             0);
          r6s.SetAngles(90 + angle, 90, 0);
          TGeoCombiTrans c6s(t6s, r6s);
          TGeoHMatrix* h6s = new TGeoHMatrix(c6s);
          layerbox->AddNode(
              straw,
              statnb * 1e6 + vnb * 1e5 + lnb * 1e4 + 1e3 + straws_per_layer + 1,
              h6s);
          layerbox->AddNode(
              gas,
              statnb * 1e6 + vnb * 1e5 + lnb * 1e4 + 2e3 + straws_per_layer + 1,
              h6s);
          layerbox->AddNode(
              wire,
              statnb * 1e6 + vnb * 1e5 + lnb * 1e4 + 3e3 + straws_per_layer + 1,
              h6s);
        }
        // End of layer loop
      }
      // End of view loop
    }
    // A layer of plastic scintillator detector
    ShipGeo::InitMedium("polyvinyltoluene");
    TGeoMedium* Vacuum_box = gGeoManager->GetMedium("polyvinyltoluene");
    UpstreamTagger_plastic =
        gGeoManager->MakeBox("Upstream_Tagger_Plastic", Vacuum_box,
                             straw_length, f_aperture_height, 1);
    UpstreamTagger_plastic->SetLineColor(kGreen);
    vol->AddNode(UpstreamTagger_plastic, 1, new TGeoTranslation(0.0, 0.0, -30));
    AddSensitiveVolume(UpstreamTagger_plastic);
    std::cout << "geometry constructed" << std::endl;
    // End of tracking station loop
  }
}
