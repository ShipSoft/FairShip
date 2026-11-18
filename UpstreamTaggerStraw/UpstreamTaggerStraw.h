// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#ifndef UPSTREAMTAGGERSTRAW_UPSTREAMTAGGERSTRAW_H_
#define UPSTREAMTAGGERSTRAW_UPSTREAMTAGGERSTRAW_H_

#include <array>
#include <string>

#include "Detector.h"
#include "TString.h"

class UpstreamTaggerStrawPoint;
class FairVolume;
class TGeoMedium;
class TGeoShape;
class TGeoVolume;

/**
 * @brief Straw-tube Upstream Background Tagger (UBT)
 *
 * One station of straw tubes upstream of the decay volume, made of three
 * layers (views y1, u, v) in z. Each layer has three squares (upper, mid,
 * lower) stacked in y, the middle one slightly upstream; each square holds
 * two staggered rows of straws in a frame and is rotated about z by the
 * layer's stereo angle. Only the gas is sensitive.
 * Configured from python/shipDet_conf.py via the setters below.
 */
class UpstreamTaggerStraw : public SHiP::Detector<UpstreamTaggerStrawPoint> {
 public:
  UpstreamTaggerStraw();
  explicit UpstreamTaggerStraw(std::string medium);

  /** Called for each step in a sensitive volume */
  Bool_t ProcessHits(FairVolume* v = nullptr) override;

  void ConstructGeometry() override;

  void SetzPositions(Double_t z1);
  /** Half-height (y) of the aperture; the tiers are 2/3 of it apart */
  void SetApertureHeight(Double_t height);
  void SetStrawDiameter(Double_t outer_straw_diameter, Double_t wall_thickness);
  void SetStrawPitch(Double_t straw_pitch, Double_t row_offset);
  void SetDeltazRow(Double_t delta_z_row);
  void SetStereoAngle(Double_t stereo_angle);
  void SetWireThickness(Double_t wire_thickness);
  void SetFrameMaterial(TString frame_material);
  void SetDeltazView(Double_t delta_z_view);
  /** Outer size of the frame of one square (full lengths) */
  void SetFrameSize(Double_t width, Double_t height);
  /** Thickness of the frame, the same on all 4 sides */
  void SetFrameThickness(Double_t thickness);
  /** z-distance by which the middle square of each layer sits upstream of
   *  the upper and lower squares */
  void SetDeltazMid(Double_t delta_z_mid);
  /** Profile of the support bars: width (in x for the uprights, in y for
   *  the horizontal bars) and depth in z */
  void SetSupportSize(Double_t width, Double_t depth);

 private:
  /** Builds one layer (view vnb = 0 y1, 1 u, 2 v) covering the aperture,
   *  made of 3 squares, one per tier */
  void BuildLayer(TGeoVolume* station, Int_t vnb);

  /** Builds one square of straws of view vnb in tier hnb (1 upper, 2 mid,
   *  3 lower), centred at (0, y, z) in the station: 2 staggered rows of
   *  straws plus its frame */
  void BuildSquare(TGeoVolume* station, Int_t vnb, Int_t hnb, Double_t y,
                   Double_t z);

  /** Builds the support structure in the plane z of the station: two
   *  uprights just outside +-inner_half_x, running the full station height
   *  (+-upright_half_y), and horizontal bars between them at the top of the
   *  upper square, the bottom of the lower square and centred in the two
   *  overlap regions between neighbouring squares (square half-height
   *  square_half_y) */
  void BuildSupport(TGeoVolume* station, TGeoMedium* medium, Double_t z,
                    Double_t inner_half_x, Double_t square_half_y,
                    Double_t upright_half_y);

  /** Stereo angle (degrees) of view vnb = 0 (y1), 1 (u), 2 (v) */
  Double_t ViewAngle(Int_t vnb) const;

  std::string fMedium;  // medium of the station and view boxes

  Double_t f_T1_z = 0.;            // z-position of the station
  Double_t f_aperture_height = 0.;  // half-height (y)
  Double_t f_straw_pitch = 0.;   // x-distance between straws in a row
  Double_t f_row_offset = 0.;    // x-offset between the two rows
  Double_t f_view_angle = 0.;    // stereo angle (degrees)
  Double_t f_inner_straw_diameter = 0.;
  Double_t f_outer_straw_diameter = 0.;
  Double_t f_wire_thickness = 0.;
  Double_t f_delta_z_view = 0.;   // z-distance between views
  Double_t f_delta_z_row = 0.;    // z-distance between the two rows
  TString f_frame_material;
  Double_t f_frame_width = 0.;      // outer x size of one frame (full)
  Double_t f_frame_height = 0.;     // outer y size of one frame (full)
  Double_t f_frame_thickness = 0.;  // same on all 4 sides
  Double_t f_delta_z_mid = 0.;      // mid square shift upstream
  Double_t f_support_width = 0.;    // support bar profile
  Double_t f_support_depth = 0.;    // support bar depth in z

  // Geometry pieces created in ConstructGeometry and placed by BuildLayer
  std::array<Double_t, 3> fTierY = {};          //!  tier centre, index hnb-1
  std::array<Double_t, 3> fTierZ = {};          //!  w.r.t. layer centre
  Double_t fStrawHalfWidth = 0.;                //!  straws fill +-this in x
  TString fStationName;                         //!
  Int_t fStationNb = 1;                         //!
  TGeoMedium* fBoxMedium = nullptr;             //!
  TGeoShape* fViewShape = nullptr;              //!
  TGeoVolume* fFrame = nullptr;                 //!  frame of one square
  TGeoVolume* fStraw = nullptr;                 //!
  TGeoVolume* fWire = nullptr;                  //!
  std::array<TGeoVolume*, 3> fGas = {};         //!  one per view

  UpstreamTaggerStraw(const UpstreamTaggerStraw&) = delete;
  UpstreamTaggerStraw& operator=(const UpstreamTaggerStraw&) = delete;
};

#endif  // UPSTREAMTAGGERSTRAW_UPSTREAMTAGGERSTRAW_H_
