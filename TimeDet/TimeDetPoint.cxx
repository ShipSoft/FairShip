// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#include "TimeDetPoint.h"

#include <iostream>

#include "FairLogger.h"

// -----   Default constructor   -------------------------------------------
TimeDetPoint::TimeDetPoint() : SHiP::DetectorPoint() {}
// -------------------------------------------------------------------------

// -----   Destructor   ----------------------------------------------------
TimeDetPoint::~TimeDetPoint() {}
// -------------------------------------------------------------------------

void TimeDetPoint::setDetectorName() { fDetectorName = "TimeDetector"; }

void TimeDetPoint::extraPrintInfo() const {
  LOG(info) << "This is the time detector";
}
