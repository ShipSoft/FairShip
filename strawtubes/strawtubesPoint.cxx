#include "strawtubesPoint.h"

#include <iostream>
#include <math.h>
using std::cout;
using std::endl;


// -----   Default constructor   -------------------------------------------
strawtubesPoint::strawtubesPoint()
  : FairMCPoint()
{
}
// -------------------------------------------------------------------------

// -----   Standard constructor   ------------------------------------------
strawtubesPoint::strawtubesPoint(Int_t trackID, Int_t detID,
                                   TVector3 pos, TVector3 mom,
                                   Double_t tof, Double_t length,
                                   Double_t eLoss,Int_t pdgcode,Double_t dist)
  : FairMCPoint(trackID, detID, pos, mom, tof, length, eLoss), fPdgCode(pdgcode), fdist2Wire(dist)
{
}
// -------------------------------------------------------------------------

// -----   Destructor   ----------------------------------------------------
strawtubesPoint::~strawtubesPoint() { }
// -------------------------------------------------------------------------

// -----   Public method Print   -------------------------------------------
void strawtubesPoint::Print() const
{
  cout << "-I- strawtubesPoint: strawtubes point for track " << fTrackID
       << " in detector " << fDetectorID << endl;
  cout << "    Position (" << fX << ", " << fY << ", " << fZ << ", " << fdist2Wire
       << ") cm" << endl;
  cout << "    Momentum (" << fPx << ", " << fPy << ", " << fPz
       << ") GeV" << endl;
  cout << "    Time " << fTime << " ns,  Length " << fLength << "pdgid" << fPdgCode
       << " cm,  Energy loss " << fELoss*1.0e06 << " keV" << endl;
}
// -------------------------------------------------------------------------

ClassImp(strawtubesPoint)

