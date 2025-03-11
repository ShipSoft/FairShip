#include "vetoPoint.h"

#include "FairLogger.h"   // for FairLogger, etc

#include <iostream>

// -----   Default constructor   -------------------------------------------
vetoPoint::vetoPoint()
    : FairMCPoint()
{}
// -------------------------------------------------------------------------

// -----   Standard constructor   ------------------------------------------
vetoPoint::vetoPoint(Int_t trackID,
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
    , fLpos(Lpos)
    , fLmom(Lmom)
{}
// -------------------------------------------------------------------------

// -----   Destructor   ----------------------------------------------------
vetoPoint::~vetoPoint() {}
// -------------------------------------------------------------------------

// -----   Public method Print   -------------------------------------------

void vetoPoint::Print() const
{
    LOG(INFO) << "    vetoPoint: veto point for track " << fTrackID << " in detector " << fDetectorID;
    LOG(INFO) << "    Position (" << fX << ", " << fY << ", " << fZ << ") cm";
    LOG(INFO) << "    Momentum (" << fPx << ", " << fPy << ", " << fPz << ") GeV";
    LOG(INFO) << "    Time " << fTime << " ns,  Length " << fLength << " cm,  Energy loss " << fELoss * 1.0e06
              << " keV";
}
// -------------------------------------------------------------------------
