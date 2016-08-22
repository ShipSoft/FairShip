#include "strawtubesHit.h"

#include <iostream>
#include <math.h>
using std::cout;
using std::endl;


// -----   Default constructor   -------------------------------------------
strawtubesHit::strawtubesHit()
  : ShipHit()
{
}
// -----   Standard constructor   ------------------------------------------
strawtubesHit::strawtubesHit(Int_t detID, Float_t tdc)
  : ShipHit(detID,tdc)
{
}
// -------------------------------------------------------------------------

// -----   Destructor   ----------------------------------------------------
strawtubesHit::~strawtubesHit() { }
// -------------------------------------------------------------------------

// -----   Public method Print   -------------------------------------------
void strawtubesHit::Print(Int_t detID) const
{
  cout << "-I- strawtubesHit: strawtubes hit " << " in detector " << fDetectorID << endl;
  cout << "  TDC " << ftdc << " ns" << endl;
}
// -------------------------------------------------------------------------

ClassImp(strawtubesHit)

