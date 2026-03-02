// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#include "strawtubesPoint.h"

#include <math.h>

#include <iostream>

#include "FairLogger.h"

// -----   Default constructor   -------------------------------------------
strawtubesPoint::strawtubesPoint() : DetectorPoint() {}
// -------------------------------------------------------------------------

// -----   Standard constructor   ------------------------------------------
strawtubesPoint::strawtubesPoint(Int_t eventID, Int_t trackID, Int_t detID,
                                 TVector3 pos, TVector3 mom, Double_t tof,
                                 Double_t length, Double_t eLoss, Int_t pdgcode,
                                 Double_t dist)
    : DetectorPoint(eventID, trackID, detID, pos, mom, tof, length, eLoss,
                    pdgcode, pos, mom),
      fdist2Wire(dist) {}
// -------------------------------------------------------------------------

// -----   Destructor   ----------------------------------------------------
strawtubesPoint::~strawtubesPoint() {}
// -------------------------------------------------------------------------

void strawtubesPoint::setDetectorName() { fDetectorName = "UpstreamTagger"; }

void strawtubesPoint::extraPrintInfo() const {
  LOG(info) << "    Position (" << fX << ", " << fY << ", " << fZ << ", "
            << fdist2Wire << ") cm";
}
