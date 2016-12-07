#include "SpectrometerPoint.h"

#include <iostream>
using std::cout;
using std::endl;

ClassImp(SpectrometerPoint)

// -----   Default constructor   -------------------------------------------
SpectrometerPoint::SpectrometerPoint()
  : FairMCPoint()
{
}
// -------------------------------------------------------------------------

SpectrometerPoint::SpectrometerPoint(Int_t trackID, Int_t detID,
                                   TVector3 pos, TVector3 mom,
                                   Double_t tof, Double_t length,
			   Double_t eLoss, Int_t pdgcode)
  : FairMCPoint(trackID, detID, pos, mom, tof, length, eLoss), fPdgCode(pdgcode)
{
}

// -------------------------------------------------------------------------

// -----   Destructor   ----------------------------------------------------
SpectrometerPoint::~SpectrometerPoint() { }
// -------------------------------------------------------------------------

// -----   Public method Print   -------------------------------------------
void SpectrometerPoint::Print(const Option_t* opt) const
{
  cout << "-I- SpectrometerPoint: Spectrometer point for track " << fTrackID
       << " in detector " << fDetectorID << endl;
  cout << "    Position (" << fX << ", " << fY << ", " << fZ
       << ") cm" << endl;
  cout << "    Momentum (" << fPx << ", " << fPy << ", " << fPz
       << ") GeV" << endl;
  cout << "    Time " << fTime << " ns,  Length " << fLength
       << " cm,  Energy loss " << fELoss*1.0e06 << " keV" << endl;
}
// -------------------------------------------------------------------------

ClassImp(SpectrometerPoint)
