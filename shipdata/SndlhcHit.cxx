#include "SndlhcHit.h"


// -----   Default constructor   -------------------------------------------
SndlhcHit::SndlhcHit()
  : TObject(),
    fDetectorID(-1)
{
}
// -------------------------------------------------------------------------



// -----   Standard constructor   ------------------------------------------
SndlhcHit::SndlhcHit(Int_t detID)
  :TObject(),
   fDetectorID(detID)
{
}

Float_t SndlhcHit::GetSignal(Int_t nChannel)
{
 return signals[nChannel];
}
Float_t SndlhcHit::GetTime(Int_t nChannel)
{
 return times[nChannel];
}
// -------------------------------------------------------------------------


// -----   Destructor   ----------------------------------------------------
SndlhcHit::~SndlhcHit() { }
// -------------------------------------------------------------------------


ClassImp(SndlhcHit)
