// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#ifndef STRAWTUBES_STRAWTUBES_H_
#define STRAWTUBES_STRAWTUBES_H_

#include <array>
#include <map>
#include <vector>

#include "Detector.h"
#include "TLorentzVector.h"
#include "TVector3.h"

class strawtubesPoint;
class FairVolume;
class TClonesArray;
class strawtubes : public SHiP::Detector<strawtubesPoint> {
 public:
  /**      Name :  Detector Name
   *       Active: kTRUE for active detectors (ProcessHits() will be called)
   *               kFALSE for inactive detectors
   */
  strawtubes(const char* Name, Bool_t Active);

  explicit strawtubes(std::string medium);

  /**      default constructor    */
  strawtubes();

  /**       this method is called for each step during simulation
   *       (see FairMCApplication::Stepping())
   */
  Bool_t ProcessHits(FairVolume* v = nullptr) override;

  void SetzPositions(Double_t z1, Double_t z2, Double_t z3, Double_t z4);
  void SetApertureArea(Double_t width, Double_t height);
  void SetStrawDiameter(Double_t outer_straw_diameter, Double_t wall_thickness);
  void SetStrawPitch(Double_t straw_pitch, Double_t layer_offset);
  void SetDeltazLayer(Double_t delta_z_layer);
  void SetStereoAngle(Double_t stereo_angle);
  void SetWireThickness(Double_t wire_thickness);
  void SetFrameMaterial(TString frame_material);
  void SetDeltazView(Double_t delta_z_view);
  void SetStationEnvelope(Double_t x, Double_t y, Double_t z);
  static std::array<Int_t, 4> StrawDecode(Int_t detID);
  static void StrawEndPoints(Int_t detID, TVector3& top, TVector3& bot);
  // for the digitizing step
  void SetStrawResolution(Double_t a, Double_t b) {
    v_drift = a;
    sigma_spatial = b;
  }
  Double_t StrawVdrift() { return v_drift; }
  Double_t StrawSigmaSpatial() { return sigma_spatial; }

  /**      Create the detector geometry        */
  void ConstructGeometry() override;

 private:
  /** Track information to be stored until the track leaves the
  active volume.
  */
  Double_t f_T1_z;                  //!  z-position of tracking station 1
  Double_t f_T2_z;                  //!  z-position of tracking station 2
  Double_t f_T3_z;                  //!  z-position of tracking station 3
  Double_t f_T4_z;                  //!  z-position of tracking station 4
  Double_t f_aperture_width;        //!  Aperture width (x)
  Double_t f_aperture_height;       //!  Aperture height (y)
  Double_t f_inner_straw_diameter;  //!  Inner Straw diameter
  Double_t f_outer_straw_diameter;  //!  Outer Straw diameter
  Double_t f_straw_pitch;           //!  Distance (y) between straws in a layer
  Double_t f_offset_layer;          //!  Offset (y) of straws between layers
  Double_t f_delta_z_layer;         //!  Distance (z) between layers
  Double_t f_view_angle;            //!  Stereo view angle
  Double_t f_wire_thickness;        //!  Sense wire thickness
  TString f_frame_material;         //!  Structure frame material
  Double_t f_delta_z_view;          //!  Distance (z) between stereo views
  Double_t f_station_width;         //!  Station envelope width (x)
  Double_t f_station_height;        //!  Station envelope height (y)
  Double_t f_station_length;        //!  Station envelope length (z)
  Double_t v_drift;                 //! drift velocity
  Double_t sigma_spatial;           //! spatial resolution
  std::string fMedium;              //! vacuum box medium
  /** container for data points */

  strawtubes(const strawtubes&) = delete;
  strawtubes& operator=(const strawtubes&) = delete;
  ClassDefOverride(strawtubes, 8)
};

#endif  // STRAWTUBES_STRAWTUBES_H_
