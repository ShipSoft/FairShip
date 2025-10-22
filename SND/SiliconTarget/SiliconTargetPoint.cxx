// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN on behalf of the SHiP Collaboration

#include "SiliconTargetPoint.h"

#include <iostream>
using std::cout;
using std::endl;

// -----   Default constructor   -------------------------------------------
SiliconTargetPoint::SiliconTargetPoint()
    : FairMCPoint()
{}
// -------------------------------------------------------------------------

SiliconTargetPoint::SiliconTargetPoint(Int_t trackID,
                                       Int_t detID,
                                       TVector3 pos,
                                       TVector3 mom,
                                       Double_t tof,
                                       Double_t length,
                                       Double_t eLoss,
                                       Int_t pdgcode)
    : FairMCPoint(trackID, detID, pos, mom, tof, length, eLoss)
    , fPdgCode(pdgcode)
{}

// -------------------------------------------------------------------------

// -----   Destructor   ----------------------------------------------------
SiliconTargetPoint::~SiliconTargetPoint() {}
// -------------------------------------------------------------------------

// -----   Public method Print   -------------------------------------------
void SiliconTargetPoint::Print() const
{
    cout << "-I- SiliconTargetPoint: point for track " << fTrackID << " in detector " << fDetectorID << endl;
    cout << "    Position (" << fX << ", " << fY << ", " << fZ << ") cm" << endl;
    cout << "    Momentum (" << fPx << ", " << fPy << ", " << fPz << ") GeV" << endl;
    cout << "    Time " << fTime << " ns,  Length " << fLength << " cm,  Energy loss " << fELoss * 1.0e06 << " keV"
         << endl;
}
// -------------------------------------------------------------------------
