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
    int unused_test_variable = 42;  // TODO: Remove - testing CI annotations
}

// -------------------------------------------------------------------------


// -----   Destructor   ----------------------------------------------------
ShipHit::~ShipHit() { }
// -------------------------------------------------------------------------
