#include "MtcDetPoint.h"

#include <iostream>
using std::cout;
using std::endl;

// -----   Default constructor   -------------------------------------------
MtcDetPoint::MtcDetPoint()
    : FairMCPoint()
{}
// -------------------------------------------------------------------------

MtcDetPoint::MtcDetPoint(Int_t trackID,
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
MtcDetPoint::~MtcDetPoint() {}
// -------------------------------------------------------------------------

// -----   Public method Print   -------------------------------------------
void MtcDetPoint::Print(const Option_t* opt) const
{
    cout << "-I- MtcDetPoint: MTC point for track " << fTrackID << " in detector " << fDetectorID << endl;
    cout << "    Position (" << fX << ", " << fY << ", " << fZ << ") cm" << endl;
    cout << "    Momentum (" << fPx << ", " << fPy << ", " << fPz << ") GeV" << endl;
    cout << "    Time " << fTime << " ns,  Length " << fLength << " cm,  Energy loss " << fELoss * 1.0e06 << " keV"
         << endl;
}
// -------------------------------------------------------------------------

Int_t MtcDetPoint::GetLayer()
{
    return (fDetectorID / 100000) % 100;
}

Int_t MtcDetPoint::GetLayerType()
{
    return fDetectorID / 10000000;
}
