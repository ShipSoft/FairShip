// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN on behalf of the SHiP Collaboration

#include "UpstreamTaggerPoint.h"

#include <iostream>
using std::cout;
using std::endl;


// -----   Default constructor   -------------------------------------------
UpstreamTaggerPoint::UpstreamTaggerPoint()
  : FairMCPoint()
{
}
// -------------------------------------------------------------------------

// -----   Standard constructor   ------------------------------------------
UpstreamTaggerPoint::UpstreamTaggerPoint(Int_t trackID,
                                         Int_t detID,
                                         TVector3 pos,
                                         TVector3 mom,
                                         Double_t tof,
                                         Double_t length,
                                         Double_t eLoss,
                                         Int_t pdgcode,
                                         TVector3 Lpos,
                                         TVector3 Lmom)
    : FairMCPoint(trackID, detID, pos, mom, tof, length, eLoss)
    , fPdgCode(pdgcode)
    , fLpos{Lpos.X(), Lpos.Y(), Lpos.Z()}
    , fLmom{Lmom.X(), Lmom.Y(), Lmom.Z()}
{
}
// -------------------------------------------------------------------------

// -----   Destructor   ----------------------------------------------------
UpstreamTaggerPoint::~UpstreamTaggerPoint() { }
// -------------------------------------------------------------------------

// -----   Public method Print   -------------------------------------------
void UpstreamTaggerPoint::Print() const
{
  cout << "-I- TimeRpcPoint: veto point for track " << fTrackID
       << " in detector " << fDetectorID << endl;
  cout << "    Position (" << fX << ", " << fY << ", " << fZ
       << ") cm" << endl;
  cout << "    Momentum (" << fPx << ", " << fPy << ", " << fPz
       << ") GeV" << endl;
  cout << "    Time " << fTime << " ns,  Length " << fLength
       << " cm,  Energy loss " << fELoss*1.0e06 << " keV" << endl;
}
// -------------------------------------------------------------------------
