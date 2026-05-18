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

  /** default constructor */
  UpstreamTagger();

  /**   this method is called for each step during simulation
   *    (see FairMCApplication::Stepping())
   */
  Bool_t ProcessHits(FairVolume* v = nullptr) override;

  /** Sets detector position and sizes */
  void SetZposition(Double_t z) { det_zPos = z; }
  void SetBoxDimensions(Double_t x, Double_t y, Double_t z) {
    xbox_fulldet = x;
    ybox_fulldet = y;
    zbox_fulldet = z;
  }

  /**  Create the detector geometry */
  void ConstructGeometry() override;

  Double_t module[11][3];  // x,y,z centre positions for each module
  // TODO Avoid 1-indexed array!

  /** Detector parameters.*/

  Double_t det_zPos;  //!  z-position of detector (set via SetZposition)
  // Detector box dimensions (set via SetBoxDimensions, defaults provided below)
  Double_t xbox_fulldet = 4.4 * m;  //!  X dimension (default: 4.4 m)
  Double_t ybox_fulldet = 6.4 * m;  //!  Y dimension (default: 6.4 m)
  Double_t zbox_fulldet =
      16.0 * cm;  //!  Z dimension/thickness (default: 16 cm)

 private:
  TGeoVolume* UpstreamTagger_fulldet;  // Timing_detector_1 object
  TGeoVolume* scoringPlaneUBText;      // new scoring plane
  /** container for data points */

  UpstreamTagger(const UpstreamTagger&) = delete;
  UpstreamTagger& operator=(const UpstreamTagger&) = delete;
};

#endif  // UPSTREAMTAGGER_UPSTREAMTAGGER_H_
