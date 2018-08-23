#ifndef PIXELHIT_H
#define PIXELHIT_H

#include "ShipHit.h"

class PixelHit : public ShipHit {
public:
   PixelHit() : ShipHit() {}
   ~PixelHit() = default;
   PixelHit(Int_t detID, Float_t digi);
   void Position(TVector3 &position);

private:
    PixelHit(const PixelHit& other); 
    PixelHit operator=(const PixelHit& other); 

   ClassDef(PixelHit, 1)
};

#endif
