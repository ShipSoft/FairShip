#include "ShipRpcPoint.h"

#include <iostream>
using std::cout;
using std::endl;


// -----   Default constructor   -------------------------------------------
ShipRpcPoint::ShipRpcPoint()
  : FairMCPoint()
{
}
// -------------------------------------------------------------------------

// -----   Standard constructor   ------------------------------------------
/*ShipRpcPoint::ShipRpcPoint(Int_t trackID, Int_t detID,
                                   TVector3 pos, TVector3 mom,
                                   Double_t tof, Double_t length,
			   Double_t eLoss, Int_t pdgcode, Int_t nArm, Int_t nRpc, Int_t nHpt)
  : FairMCPoint(trackID, detID, pos, mom, tof, length, eLoss), fPdgCode(pdgcode), 
    fNArm(nArm), fNRpc(nRpc), fNHpt(nHpt)
{
}
*/
ShipRpcPoint::ShipRpcPoint(Int_t trackID, Int_t detID,
                                   TVector3 pos, TVector3 mom,
                                   Double_t tof, Double_t length,
			   Double_t eLoss, Int_t pdgcode)
  : FairMCPoint(trackID, detID, pos, mom, tof, length, eLoss), fPdgCode(pdgcode)
{
}

// -------------------------------------------------------------------------

// -----   Destructor   ----------------------------------------------------
ShipRpcPoint::~ShipRpcPoint() { }
// -------------------------------------------------------------------------

// -----   Public method Print   -------------------------------------------
void ShipRpcPoint::Print(const Option_t* opt) const
{
  cout << "-I- ShipRpcPoint: ShipRpc point for track " << fTrackID
       << " in detector " << fDetectorID << endl;
  cout << "    Position (" << fX << ", " << fY << ", " << fZ
       << ") cm" << endl;
  cout << "    Momentum (" << fPx << ", " << fPy << ", " << fPz
       << ") GeV" << endl;
  cout << "    Time " << fTime << " ns,  Length " << fLength
       << " cm,  Energy loss " << fELoss*1.0e06 << " keV" << endl;
}
// -------------------------------------------------------------------------

ClassImp(ShipRpcPoint)

