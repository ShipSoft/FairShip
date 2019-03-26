#ifndef SCIFIHIT_H
#define SCIFIHIT_H

#include "ShipHit.h"

class SciFiHit : public ShipHit {
public:
   SciFiHit() : ShipHit() {}
   ~SciFiHit() = default;
   SciFiHit(Int_t detID, Float_t digi);
   void EndPoints(TVector3 &top, TVector3 &bot);

private:
    SciFiHit(const SciFiHit& other);
    SciFiHit operator=(const SciFiHit& other);

   ClassDef(SciFiHit, 1)
};

#endif
