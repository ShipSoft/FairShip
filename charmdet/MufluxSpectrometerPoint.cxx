#include "MufluxSpectrometerPoint.h"

#include <iostream>
using std::cout;
using std::endl;

ClassImp(MufluxSpectrometerPoint)

// -----   Default constructor   -------------------------------------------
MufluxSpectrometerPoint::MufluxSpectrometerPoint()
  : FairMCPoint()
{
}
// -------------------------------------------------------------------------

MufluxSpectrometerPoint::MufluxSpectrometerPoint(Int_t trackID, Int_t detID,
                                   TVector3 pos, TVector3 mom,
                                   Double_t tof, Double_t length,
			   Double_t eLoss, Int_t pdgcode,Double_t dist)
  : FairMCPoint(trackID, detID, pos, mom, tof, length, eLoss), fPdgCode(pdgcode), fdist2Wire(dist)
{
}

// -------------------------------------------------------------------------

// -----   Destructor   ----------------------------------------------------
MufluxSpectrometerPoint::~MufluxSpectrometerPoint() { }
// -------------------------------------------------------------------------

// -----   Public method Print   -------------------------------------------
void MufluxSpectrometerPoint::Print(const Option_t* opt) const
{
  cout << "-I- MufluxSpectrometerPoint: MufluxSpectrometer point for track " << fTrackID
       << " in detector " << fDetectorID << endl;
  cout << "    Position (" << fX << ", " << fY << ", " << fZ <<", " << fdist2Wire
       << ") cm" << endl;
  cout << "    Momentum (" << fPx << ", " << fPy << ", " << fPz
       << ") GeV" << endl;
  cout << "    Time " << fTime << " ns,  Length " << fLength
       << " cm,  Energy loss " << fELoss*1.0e06 << " keV" << endl;
}
// -------------------------------------------------------------------------

ClassImp(MufluxSpectrometerPoint)
