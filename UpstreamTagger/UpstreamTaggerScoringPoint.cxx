// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#include "UpstreamTaggerScoringPoint.h"

#include "FairLogger.h"

// -----   Default constructor   -------------------------------------------
UpstreamTaggerScoringPoint::UpstreamTaggerScoringPoint()
    : SHiP::DetectorPoint() {}
// -------------------------------------------------------------------------

// -----   Destructor   ----------------------------------------------------
UpstreamTaggerScoringPoint::~UpstreamTaggerScoringPoint() = default;
// -------------------------------------------------------------------------

void UpstreamTaggerScoringPoint::extraPrintInfo() const {
  // Plane numbers as set in shipDet_conf.configure
  switch (GetDetectorID()) {
    case 1:
      LOG(info) << "UBT scoring plane 1, at the decay vessel entrance";
      break;
    case 2:
      LOG(info) << "UBT scoring plane 2, behind the muon shield (muons only)";
      break;
    default:
      LOG(info) << "UBT scoring plane " << GetDetectorID();
  }
}
