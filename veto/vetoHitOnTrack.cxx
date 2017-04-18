#include "vetoHitOnTrack.h"


// -----   Default constructor   -------------------------------------------
vetoHitOnTrack::vetoHitOnTrack()
  : TObject(),
    fDist(-1),
    fHitID(-1)
{
}
// -------------------------------------------------------------------------



// -----   Standard constructor   ------------------------------------------
vetoHitOnTrack::vetoHitOnTrack(Int_t hitID, Float_t dist)
  :TObject(),
   fDist        (dist),
   fHitID  (hitID)
{
}

// -------------------------------------------------------------------------


// -----   Destructor   ----------------------------------------------------
vetoHitOnTrack::~vetoHitOnTrack() { }
// -------------------------------------------------------------------------


ClassImp(vetoHitOnTrack)
