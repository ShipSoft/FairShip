// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#include "UpstreamTaggerPoint.h"

#include <iostream>

#include "FairLogger.h"

// -----   Default constructor   -------------------------------------------
UpstreamTaggerPoint::UpstreamTaggerPoint() : SHiP::DetectorPoint() {}
// -------------------------------------------------------------------------

// -----   Destructor   ----------------------------------------------------
UpstreamTaggerPoint::~UpstreamTaggerPoint() {}
// -------------------------------------------------------------------------

void UpstreamTaggerPoint::extraPrintInfo() const {
  LOG(info) << "This is the upstream tagger";
}
