#include "prestrawdetectorPoint.h"

#include <iostream>
#include <math.h>
using std::cout;
using std::endl;


// -----   Default constructor   -------------------------------------------
prestrawdetectorPoint::prestrawdetectorPoint()
  : FairMCPoint()
{
}
// -------------------------------------------------------------------------

// -----   Standard constructor   ------------------------------------------
prestrawdetectorPoint::prestrawdetectorPoint(Int_t trackID, Int_t detID,
                                   TVector3 pos, TVector3 mom,
                                   Double_t tof, Double_t length,
                                   Double_t eLoss,Int_t pdgcode)
  : FairMCPoint(trackID, detID, pos, mom, tof, length, eLoss), fPdgCode(pdgcode)
{
}
// -------------------------------------------------------------------------

// -----   Destructor   ----------------------------------------------------
prestrawdetectorPoint::~prestrawdetectorPoint() { }
// -------------------------------------------------------------------------

// -----   Public method Print   -------------------------------------------
void prestrawdetectorPoint::Print() const
{
  cout << "-I- prestrawdetectorPoint: prestrawdetector point for track " << fTrackID
       << " in detector " << fDetectorID << endl;
  cout << "    Position (" << fX << ", " << fY << ", " << fZ 
       << ") cm" << endl;
  cout << "    Momentum (" << fPx << ", " << fPy << ", " << fPz
       << ") GeV" << endl;
  cout << "    Time " << fTime << " ns,  Length " << fLength << "pdgid" << fPdgCode
       << " cm,  Energy loss " << fELoss*1.0e06 << " keV" << endl;
}
// -------------------------------------------------------------------------
