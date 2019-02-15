#include "ScintillatorHit.h"

ScintillatorHit::ScintillatorHit(Int_t detID, Float_t digi, Float_t signal_width, uint16_t flag, uint16_t ch)
   : ShipHit(detID, digi), time_over_threshold(signal_width), flags(flag), channel(ch)
{
}

ClassImp(ScintillatorHit)
