#include "TimeDetPoint.h"

#include <iostream>
using std::cout;
using std::endl;


// -----   Default constructor   -------------------------------------------
TimeDetPoint::TimeDetPoint()
  : FairMCPoint()
{
}
// -------------------------------------------------------------------------

// -----   Standard constructor   ------------------------------------------
TimeDetPoint::TimeDetPoint(Int_t trackID, Int_t detID,
			   TVector3 pos, TVector3 mom,
			   Double_t tof, Double_t length,
			   Double_t eLoss, Int_t pdgcode,TVector3 Lpos, TVector3 Lmom)
  : FairMCPoint(trackID, detID, pos, mom, tof, length, eLoss), fPdgCode(pdgcode),fLpos(Lpos),fLmom(Lmom)
{
}
// -------------------------------------------------------------------------

// -----   Destructor   ----------------------------------------------------
TimeDetPoint::~TimeDetPoint() { }
// -------------------------------------------------------------------------

// -----   Public method Print   -------------------------------------------
void TimeDetPoint::Print() const
{
  cout << "-I- TimeDetPoint: veto point for track " << fTrackID
       << " in detector " << fDetectorID << endl;
  cout << "    Position (" << fX << ", " << fY << ", " << fZ
       << ") cm" << endl;
  cout << "    Momentum (" << fPx << ", " << fPy << ", " << fPz
       << ") GeV" << endl;
  cout << "    Time " << fTime << " ns,  Length " << fLength
       << " cm,  Energy loss " << fELoss*1.0e06 << " keV" << endl;
}
// -------------------------------------------------------------------------

ClassImp(TimeDetPoint)
