#include "MuonTaggerPoint.h"

#include <iostream>
using std::cout;
using std::endl;


// -----   Default constructor   -------------------------------------------
MuonTaggerPoint::MuonTaggerPoint()
  : FairMCPoint()
{
}
// -------------------------------------------------------------------------

// -----   Standard constructor   ------------------------------------------

MuonTaggerPoint::MuonTaggerPoint(Int_t trackID, Int_t detID,TVector3 pos, TVector3 mom,
                         Double_t tof, Double_t length,
			 Double_t eLoss, Int_t pdgcode)
  : FairMCPoint(trackID, detID, pos, mom, tof, length, eLoss),fPdgCode(pdgcode)
{  }

// -------------------------------------------------------------------------


// -----   Destructor   ----------------------------------------------------
MuonTaggerPoint::~MuonTaggerPoint() { }
// -------------------------------------------------------------------------

// -----   Public method Print   -------------------------------------------
void MuonTaggerPoint::Print(const Option_t* opt) const
{
  cout << "-I- MuonTaggerPoint: box point for track " << fTrackID
       << " in detector " << fDetectorID << endl;
  cout << "    Position (" << fX << ", " << fY << ", " << fZ
       << ") cm" << endl;
  cout << "    Momentum (" << fPx << ", " << fPy << ", " << fPz
       << ") GeV" << endl;
  cout << "    Time " << fTime << " ns,  Length " << fLength
       << " cm,  Energy loss " << fELoss*1.0e06 << " keV" << endl;
}
// -------------------------------------------------------------------------

ClassImp(MuonTaggerPoint)

