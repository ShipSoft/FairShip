#include "HptPoint.h"

#include <iostream>
using std::cout;
using std::endl;


// -----   Default constructor   -------------------------------------------
HptPoint::HptPoint()
  : FairMCPoint()
{
}
// -------------------------------------------------------------------------

HptPoint::HptPoint(Int_t trackID, Int_t detID,
                                   TVector3 pos, TVector3 mom,
                                   Double_t tof, Double_t length,
			   Double_t eLoss, Int_t pdgcode)
  : FairMCPoint(trackID, detID, pos, mom, tof, length, eLoss), fPdgCode(pdgcode)
{
}

// -------------------------------------------------------------------------

// -----   Destructor   ----------------------------------------------------
HptPoint::~HptPoint() { }
// -------------------------------------------------------------------------

// -----   Public method Print   -------------------------------------------
void HptPoint::Print(const Option_t* opt) const
{
  cout << "-I- HptPoint: Hpt point for track " << fTrackID
       << " in detector " << fDetectorID << endl;
  cout << "    Position (" << fX << ", " << fY << ", " << fZ
       << ") cm" << endl;
  cout << "    Momentum (" << fPx << ", " << fPy << ", " << fPz
       << ") GeV" << endl;
  cout << "    Time " << fTime << " ns,  Length " << fLength
       << " cm,  Energy loss " << fELoss*1.0e06 << " keV" << endl;
}
// -------------------------------------------------------------------------

ClassImp(HptPoint)

