#ifndef SCINTILLATORHIT_H
#define SCINTILLATORHIT_H

#include "ShipHit.h"

class ScintillatorHit : public ShipHit {
public:
   ScintillatorHit() : ShipHit() {}
   ~ScintillatorHit() = default;
   ScintillatorHit(Int_t detID, Float_t digi);

private:
    ScintillatorHit(const ScintillatorHit& other); 
    ScintillatorHit operator=(const ScintillatorHit& other); 

   ClassDef(ScintillatorHit, 1)
};

#endif
