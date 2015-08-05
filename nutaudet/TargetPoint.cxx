#include "TargetPoint.h"

#include <iostream>
using std::cout;
using std::endl;


// -----   Default constructor   -------------------------------------------
TargetPoint::TargetPoint()
  : FairMCPoint()
{
}
// -------------------------------------------------------------------------

// -----   Standard constructor   ------------------------------------------
/*
TargetPoint::TargetPoint(Int_t trackID, Int_t detID,TVector3 pos, TVector3 mom,
                         Double_t tof, Double_t length,
			 Double_t eLoss, Int_t pdgcode,
			 Bool_t emTop, Bool_t emBot,Bool_t emCESTop, Bool_t emCESBot, Bool_t tt,
			 Int_t nPlate, Int_t nColumn, Int_t nRow, Int_t nWall)
  : FairMCPoint(trackID, detID, pos, mom, tof, length, eLoss),fPdgCode(pdgcode),
    fEmTop(emTop), fEmBot(emBot), fEmCESTop(emCESTop), fEmCESBot(emCESBot),fTT(tt),
    fNPlate(nPlate),fNColumn(nColumn), fNRow(nRow),fNWall(nWall)
{  }
*/

TargetPoint::TargetPoint(Int_t trackID, Int_t detID,TVector3 pos, TVector3 mom,
                         Double_t tof, Double_t length,
			 Double_t eLoss, Int_t pdgcode)
  : FairMCPoint(trackID, detID, pos, mom, tof, length, eLoss),fPdgCode(pdgcode)
{  }

// -------------------------------------------------------------------------

//,  EmTop, EmBot, EmCESTop,EmCESBot,TT,NPlate,NColumn,NRow,NWall
// -----   Destructor   ----------------------------------------------------
TargetPoint::~TargetPoint() { }
// -------------------------------------------------------------------------

// -----   Public method Print   -------------------------------------------
void TargetPoint::Print(const Option_t* opt) const
{
  cout << "-I- TargetPoint: ShipRpc point for track " << fTrackID
       << " in detector " << fDetectorID << endl;
  cout << "    Position (" << fX << ", " << fY << ", " << fZ
       << ") cm" << endl;
  cout << "    Momentum (" << fPx << ", " << fPy << ", " << fPz
       << ") GeV" << endl;
  cout << "    Time " << fTime << " ns,  Length " << fLength
       << " cm,  Energy loss " << fELoss*1.0e06 << " keV" << endl;
}
// -------------------------------------------------------------------------

ClassImp(TargetPoint)

