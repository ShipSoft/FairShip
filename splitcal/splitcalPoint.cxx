// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#include "splitcalPoint.h"

#include <iostream>

#include "FairLogger.h"

// -----   Default constructor   -------------------------------------------
splitcalPoint::splitcalPoint() : DetectorPoint() {}
// -------------------------------------------------------------------------

// -----   Destructor   ----------------------------------------------------
splitcalPoint::~splitcalPoint() {}
// -------------------------------------------------------------------------

void splitcalPoint::extraPrintInfo() const {
  LOG(info) << "This is the splitcal";
}
