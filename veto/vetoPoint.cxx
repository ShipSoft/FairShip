// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#include "vetoPoint.h"

#include <iostream>

#include "FairLogger.h"  // for FairLogger, etc

// -----   Default constructor   -------------------------------------------
vetoPoint::vetoPoint() : SHiP::DetectorPoint() {}
// -------------------------------------------------------------------------

// -----   Destructor   ----------------------------------------------------
vetoPoint::~vetoPoint() {}
// -------------------------------------------------------------------------

// -----   Public method Print   -------------------------------------------

void vetoPoint::extraPrintInfo() const {
  LOG(info) << "This is the veto detector";
}

// -------------------------------------------------------------------------
