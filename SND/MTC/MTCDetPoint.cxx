// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

#include "MTCDetPoint.h"

#include <iostream>
using std::cout;
using std::endl;

// -----   Default constructor   -------------------------------------------
MTCDetPoint::MTCDetPoint()
    : FairMCPoint()
{}
// -------------------------------------------------------------------------

MTCDetPoint::MTCDetPoint(Int_t trackID,
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
MTCDetPoint::~MTCDetPoint() {}
// -------------------------------------------------------------------------

// -----   Public method Print   -------------------------------------------
void MTCDetPoint::Print() const
{
    cout << "-I- MTCDetPoint: MTC point for track " << fTrackID << " in detector " << fDetectorID << endl;
    cout << "    Position (" << fX << ", " << fY << ", " << fZ << ") cm" << endl;
    cout << "    Momentum (" << fPx << ", " << fPy << ", " << fPz << ") GeV" << endl;
    cout << "    Time " << fTime << " ns,  Length " << fLength << " cm,  Energy loss " << fELoss * 1.0e06 << " keV"
         << endl;
}
// -------------------------------------------------------------------------
