#include "ScintillatorHit.h"

ScintillatorHit::ScintillatorHit(Int_t detID, Float_t digi, uint16_t flag, uint16_t ch)
   : ShipHit(detID, digi), flags(flag), channel(ch)
{
}

ClassImp(ScintillatorHit)
