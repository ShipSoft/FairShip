// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#include "CaloScoringPlanePoint.h"

#include "FairLogger.h"

CaloScoringPlanePoint::CaloScoringPlanePoint() : SHiP::DetectorPoint() {}

CaloScoringPlanePoint::~CaloScoringPlanePoint() = default;

void CaloScoringPlanePoint::extraPrintInfo() const {
  LOG(info) << "This is the scoring plane";
}
