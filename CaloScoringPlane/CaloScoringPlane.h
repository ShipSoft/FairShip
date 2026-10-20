// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#ifndef CALOSCORINGPLANE_CALOSCORINGPLANE_H_
#define CALOSCORINGPLANE_CALOSCORINGPLANE_H_

#include "CaloScoringPlanePoint.h"
#include "ScoringPlane.h"
#include "ShipUnit.h"

/**
 * @brief Ideal scoring plane downstream of the timing detector.
 *
 * Replaces the former SplitCal calorimeter. The plane is a thin vacuum box
 * placed where the SplitCal front face used to be, recording a
 * CaloScoringPlanePoint for every track entering it (see SHiP::ScoringPlane
 * for what a point holds). Its node in the top volume is
 * "CaloScoringPlane_1".
 */
class CaloScoringPlane : public SHiP::ScoringPlane<CaloScoringPlanePoint> {
 public:
  CaloScoringPlane(const char* Name, Bool_t Active);
  CaloScoringPlane();

  /** Centre of the plane in global z (cm). */
  void SetZposition(Double_t z) { fZPos = z; }
  /** Full dimensions of the box (cm). */
  void SetBoxDimensions(Double_t x, Double_t y, Double_t z) {
    fXSize = x;
    fYSize = y;
    fZSize = z;
  }

  void ConstructGeometry() override;

 private:
  Double_t fZPos = 0.;                   //!
  Double_t fXSize = 4.0 * ShipUnit::m;   //!  full width
  Double_t fYSize = 6.0 * ShipUnit::m;   //!  full height
  Double_t fZSize = 1.0 * ShipUnit::mm;  //!  full thickness

  CaloScoringPlane(const CaloScoringPlane&) = delete;
  CaloScoringPlane& operator=(const CaloScoringPlane&) = delete;
};

#endif  // CALOSCORINGPLANE_CALOSCORINGPLANE_H_
