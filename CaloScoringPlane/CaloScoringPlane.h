// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#ifndef CALOSCORINGPLANE_CALOSCORINGPLANE_H_
#define CALOSCORINGPLANE_CALOSCORINGPLANE_H_

#include "Detector.h"
#include "ShipUnit.h"

class CaloScoringPlanePoint;
class FairVolume;

/**
 * @brief Ideal scoring plane downstream of the timing detector.
 *
 * Replaces the former SplitCal calorimeter. The plane is a thin vacuum box
 * placed where the SplitCal front face used to be. Every track *entering*
 * the box produces one CaloScoringPlanePoint holding the MC-truth position,
 * momentum, time and PDG code. ProcessHits runs after the step that
 * enters the box, so these are the values at the end of that step, i.e. at
 * the exit face for a particle crossing the plane. No energy deposit is
 * required (the medium is vacuum), so neutral particles are recorded too.
 *
 * A track crossing the plane twice (e.g. back-scattered) gives two points;
 * the sign of Pz tells the direction.
 */
class CaloScoringPlane : public SHiP::Detector<CaloScoringPlanePoint> {
 public:
  CaloScoringPlane(const char* Name, Bool_t Active);
  CaloScoringPlane();

  Bool_t ProcessHits(FairVolume* v = nullptr) override;

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
