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
  LOG(info) << "This is the scoring plane downstream of the upstream tagger";
}
