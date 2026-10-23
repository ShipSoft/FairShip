// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#ifndef UPSTREAMTAGGER_UPSTREAMTAGGERSCORINGPLANE_H_
#define UPSTREAMTAGGER_UPSTREAMTAGGERSCORINGPLANE_H_

#include "ScoringPlane.h"
#include "UpstreamTaggerScoringPoint.h"

/**
 * @brief Thin vacuum scoring planes around the UBT
 *
 * Every track entering a plane produces one UpstreamTaggerScoringPoint (see
 * SHiP::ScoringPlane for what a point holds), so the flux reaching the decay
 * vessel can be compared with what the UBT sees. The planes and their PDG
 * filters are set with AddPlane, from the geometry configuration.
 */
class UpstreamTaggerScoringPlane
    : public SHiP::ScoringPlane<UpstreamTaggerScoringPoint> {
 public:
  UpstreamTaggerScoringPlane(const char* Name, Bool_t Active);
  UpstreamTaggerScoringPlane();

 private:
  UpstreamTaggerScoringPlane(const UpstreamTaggerScoringPlane&) = delete;
  UpstreamTaggerScoringPlane& operator=(const UpstreamTaggerScoringPlane&) =
      delete;
};

#endif  // UPSTREAMTAGGER_UPSTREAMTAGGERSCORINGPLANE_H_
