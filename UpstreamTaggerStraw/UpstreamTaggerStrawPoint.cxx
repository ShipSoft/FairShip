// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#include "UpstreamTaggerStrawPoint.h"

#include <iostream>

#include "FairLogger.h"

// -----   Default constructor   -------------------------------------------
UpstreamTaggerStrawPoint::UpstreamTaggerStrawPoint() : SHiP::DetectorPoint() {}
// -------------------------------------------------------------------------

// -----   Destructor   ----------------------------------------------------
UpstreamTaggerStrawPoint::~UpstreamTaggerStrawPoint() = default;
// -------------------------------------------------------------------------

void UpstreamTaggerStrawPoint::extraPrintInfo() const {
  LOG(info) << "This is the upstream tagger";
}
