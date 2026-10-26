// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#ifndef CALOSCORINGPLANE_CALOSCORINGPLANEPOINT_H_
#define CALOSCORINGPLANE_CALOSCORINGPLANEPOINT_H_

#include "DetectorPoint.h"

/** MC-truth crossing of the scoring plane.
 *
 * Position, momentum and time are those at the end of the track's first step
 * inside the plane, i.e. the exit face for a particle crossing it.
 */
class CaloScoringPlanePoint : public SHiP::DetectorPoint {
 public:
  CaloScoringPlanePoint();

  using SHiP::DetectorPoint::DetectorPoint;

  ~CaloScoringPlanePoint() override;

  void extraPrintInfo() const override;

 private:
  ClassDefOverride(CaloScoringPlanePoint, 1)
};

#endif  // CALOSCORINGPLANE_CALOSCORINGPLANEPOINT_H_
