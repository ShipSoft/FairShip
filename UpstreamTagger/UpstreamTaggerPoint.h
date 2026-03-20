// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#ifndef UPSTREAMTAGGER_UPSTREAMTAGGERPOINT_H_
#define UPSTREAMTAGGER_UPSTREAMTAGGERPOINT_H_

#include <array>

#include "DetectorPoint.h"
#include "TObject.h"
#include "TVector3.h"
#include "UpstreamTagger.h"
#include "UpstreamTaggerHit.h"

class UpstreamTaggerPoint : public SHiP::DetectorPoint {
 public:
  /** Default constructor **/
  UpstreamTaggerPoint();

  using SHiP::DetectorPoint::DetectorPoint;
  /** Destructor **/
  ~UpstreamTaggerPoint() override;

  void extraPrintInfo() const override;

 private:
  ClassDefOverride(UpstreamTaggerPoint, 4)
};

#endif  // UPSTREAMTAGGER_UPSTREAMTAGGERPOINT_H_
