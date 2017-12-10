#include "muonHit.h"
#include "muonPoint.h"
#include "TVector3.h"

#include <iostream>

using std::cout;
using std::endl;

Double_t speedOfLight = TMath::C() *100./1000000000.0 ; // from m/sec to cm/ns
// -----   Default constructor   -------------------------------------------
muonHit::muonHit()
  : ShipHit()
{
 flag = true;
}
// -----   Standard constructor   ------------------------------------------
muonHit::muonHit(Int_t detID, Float_t tdc)
  : ShipHit(detID,tdc)
{
 flag = true;
}
// -----   constructor from muonPoint   ------------------------------------------
muonHit::muonHit(muonPoint* p, Double_t t0)
  : ShipHit()
{
     TVector3 truePosition = TVector3( p->GetY(), p->GetX(),p->GetZ());
     fromXYZ(truePosition);
     fdigi = t0 + p->GetTime(); // + drift time,  propagation inside tile, readout chain.
     flag = true;
}
// ----
Int_t muonHit::fromXYZ(TVector3 p)
{
    // needs some code to produce a unique detector ID
    Int_t detID = 3;
    return detID;
}
// ----
void muonHit::XYZfromDetID(TVector3 &p)
{
    // needs some code to return XYZ from detID
}
// -------------------------------------------------------------------------

// -----   Destructor   ----------------------------------------------------
muonHit::~muonHit() { }
// -------------------------------------------------------------------------

// -----   Public method Print   -------------------------------------------
void muonHit::Print() const
{
  cout << "-I- muonHit: muon hit " << " in detector " << fDetectorID << endl;
  cout << "  TDC " << fdigi << " ns" << endl;
}
// -------------------------------------------------------------------------

ClassImp(muonHit)

