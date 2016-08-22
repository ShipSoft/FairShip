#include "ShipHit.h"


// -----   Default constructor   -------------------------------------------
ShipHit::ShipHit()
  : TObject(),
    fdigi(0),
    fDetectorID(-1)
{
}
// -------------------------------------------------------------------------



// -----   Standard constructor   ------------------------------------------
ShipHit::ShipHit(Int_t detID, Float_t digi)
  :TObject(),
   fdigi        (digi),
   fDetectorID  (detID)
{
}

// -------------------------------------------------------------------------


// -----   Destructor   ----------------------------------------------------
ShipHit::~ShipHit() { }
// -------------------------------------------------------------------------


ClassImp(ShipHit)
