// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN on behalf of the SHiP Collaboration

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
