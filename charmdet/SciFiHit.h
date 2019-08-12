#ifndef SCIFIHIT_H
#define SCIFIHIT_H

#include "ShipHit.h"

class SciFiHit : public ShipHit {
public:
   SciFiHit() : ShipHit() {}
   ~SciFiHit() = default;
   SciFiHit(Int_t detID, Int_t layerID, uint16_t ch, uint8_t board, uint32_t hitTime, uint16_t fineTime, int flags, bool triggerFlag);
   void GetSciFiXYZ(TVector3 &v, int detID);

private:
    SciFiHit(const SciFiHit& other);
    SciFiHit operator=(const SciFiHit& other);
    uint8_t board;
    uint16_t ch;
    uint32_t hitTime;
    uint16_t fineTime;
    int  flags;
    bool triggerFlag;

   ClassDef(SciFiHit, 1)
};

#endif
