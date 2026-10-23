// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#ifndef UPSTREAMTAGGERSTRAW_UPSTREAMTAGGERSTRAWPOINT_H_
#define UPSTREAMTAGGERSTRAW_UPSTREAMTAGGERSTRAWPOINT_H_

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

#endif  // UPSTREAMTAGGERSTRAW_UPSTREAMTAGGERSTRAWPOINT_H_
