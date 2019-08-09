#ifndef PIXELHIT_H
#define PIXELHIT_H

#include "ShipHit.h"

class ShipPixelHit : public ShipHit {
public:
   ShipPixelHit() : ShipHit() {}
   ~ShipPixelHit() = default;
   ShipPixelHit(Int_t detID, Float_t digi);

private:
    ShipPixelHit(const ShipPixelHit& other); 
    ShipPixelHit operator=(const ShipPixelHit& other); 

   ClassDef(ShipPixelHit, 1)
};

#endif
