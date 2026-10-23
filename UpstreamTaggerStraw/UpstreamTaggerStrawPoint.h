// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#ifndef UPSTREAMTAGGER_UPSTREAMTAGGERPOINT_H_
#define UPSTREAMTAGGER_UPSTREAMTAGGERPOINT_H_

#include <array>

#include "DetectorPoint.h"
#include "TObject.h"
#include "TVector3.h"
#include "UpstreamTaggerStraw.h"
#include "UpstreamTaggerStrawHit.h"

class UpstreamTaggerStrawPoint : public SHiP::DetectorPoint {
 public:
  /** Default constructor **/
  UpstreamTaggerStrawPoint();

  using SHiP::DetectorPoint::DetectorPoint;
  /** Destructor **/
  ~UpstreamTaggerStrawPoint() override;

  void extraPrintInfo() const override;

 private:
  ClassDefOverride(UpstreamTaggerStrawPoint, 4)
};

#endif  // UPSTREAMTAGGER_UPSTREAMTAGGERPOINT_H_
