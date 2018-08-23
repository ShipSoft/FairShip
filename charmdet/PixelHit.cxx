#include "PixelHit.h"
#include <iostream>

PixelHit::PixelHit(Int_t detID, Float_t digi) : ShipHit(detID, digi) {}

void PixelHit::Position(TVector3 &position)
{
}

ClassImp(PixelHit)
