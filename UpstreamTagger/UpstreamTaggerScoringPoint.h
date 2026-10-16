// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#ifndef UPSTREAMTAGGER_UPSTREAMTAGGERSCORINGPOINT_H_
#define UPSTREAMTAGGER_UPSTREAMTAGGERSCORINGPOINT_H_

#include "DetectorPoint.h"

/**
 * @brief Track crossing of the vacuum scoring plane downstream of the UBT
 *
 * Position, momentum and time are taken where the track enters the plane.
 */
class UpstreamTaggerScoringPoint : public SHiP::DetectorPoint {
 public:
  /** Default constructor **/
  UpstreamTaggerScoringPoint();

  using SHiP::DetectorPoint::DetectorPoint;
  /** Destructor **/
  ~UpstreamTaggerScoringPoint() override;

  void extraPrintInfo() const override;

 private:
  ClassDefOverride(UpstreamTaggerScoringPoint, 1)
};

#endif  // UPSTREAMTAGGER_UPSTREAMTAGGERSCORINGPOINT_H_
