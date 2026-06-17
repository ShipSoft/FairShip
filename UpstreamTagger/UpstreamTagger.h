// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#ifndef UPSTREAMTAGGER_UPSTREAMTAGGER_H_
#define UPSTREAMTAGGER_UPSTREAMTAGGER_H_

#include <map>
#include <vector>

#include "Detector.h"
#include "ShipUnit.h"
#include "TLorentzVector.h"
#include "TVector3.h"

class UpstreamTaggerPoint;
class FairVolume;
class TClonesArray;

using ShipUnit::cm;
using ShipUnit::m;

/**
 * @brief Upstream Background Tagger (UBT) detector
 *
 * The UBT is a simplified scoring plane detector implemented as a vacuum box.
 * It serves as a background tagging device upstream of the decay volume.
 *
 * Historical Note:
 * The UBT was previously implemented as a detailed RPC (Resistive Plate
 * Chamber) with multiple material layers (Glass, PMMA, Freon SF6, FR4,
 * Aluminium, strips). It was simplified to a single vacuum box scoring plane to
 * avoid geometry overlaps and reduce simulation complexity while maintaining
 * its physics purpose. See commits 178787588 and related for the simplification
 * history.
 *
 * Current Implementation:
 * - Simple vacuum box with configurable dimensions
 * - Default dimensions: 4.4m (X) × 6.4m (Y) × 16cm (Z)
 * - Z position and box dimensions are set from geometry_config.py
 * - Configured via SetZposition() and SetBoxDimensions()
 */

class UpstreamTagger : public SHiP::Detector<UpstreamTaggerPoint> {
 public:
  /**      Name :  Detector Name
   *       Active: kTRUE for active detectors (ProcessHits() will be called)
   *               kFALSE for inactive detectors
   */
  UpstreamTagger(const char* Name, Bool_t Active);
  UpstreamTagger(std::string medium);
  /** default constructor */
  UpstreamTagger();

  /**   this method is called for each step during simulation
   *    (see FairMCApplication::Stepping())
   */
  Bool_t ProcessHits(FairVolume* v = nullptr) override;

  /** Sets detector position and sizes */
  void SetZposition(Double_t z) { det_zPos = z; }

  void SetzPositions(Double_t z1);
  void SetApertureArea(Double_t width, Double_t height, Double_t length);
  void SetStrawDiameter(Double_t outer_straw_diameter, Double_t wall_thickness);
  void SetStrawPitch(Double_t straw_pitch, Double_t layer_offset);
  void SetDeltazLayer(Double_t delta_z_layer);
  void SetStereoAngle(Double_t stereo_angle);
  void SetWireThickness(Double_t wire_thickness);
  void SetFrameMaterial(TString frame_material);
  void SetDeltazView(Double_t delta_z_view);
  static std::tuple<Int_t, Int_t, Int_t, Int_t> StrawDecode(Int_t detID);
  static void StrawEndPoints(Int_t detID, TVector3& top, TVector3& bot);
  /**  Create the detector geometry */

  void ConstructGeometry() override;

  Double_t module[11][3];  // x,y,z centre positions for each module
                           // TODO Avoid 1-indexed array!

  /** Detector parameters.*/

  Double_t f_aperture_width;
  Double_t f_aperture_height;
  Double_t f_station_length;
  Double_t f_straw_pitch;
  Double_t f_view_angle;
  Double_t f_offset_layer;
  Double_t f_inner_straw_diameter;
  Double_t f_outer_straw_diameter;
  Double_t f_wire_thickness;
  Double_t f_T1_z;
  Double_t f_delta_z_view;
  Double_t f_delta_z_layer;
  TString f_frame_material;
  std::string fMedium;
  /** Detector parameters.*/

  Double_t det_zPos;  //!  z-position of detector (set via SetZposition)

 private:
  /** container for data points */

  TGeoVolume* UpstreamTagger_plastic;
  TGeoVolume* UpstreamTagger_fulldet;

  UpstreamTagger(const UpstreamTagger&) = delete;
  UpstreamTagger& operator=(const UpstreamTagger&) = delete;

  ClassDefOverride(UpstreamTagger, 3)
};

#endif  // UPSTREAMTAGGER_UPSTREAMTAGGER_H_
