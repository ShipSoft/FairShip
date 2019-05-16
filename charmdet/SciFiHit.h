#ifndef SCIFIHIT_H
#define SCIFIHIT_H

#include "ShipHit.h"

class SciFiHit : public ShipHit {
public:
   SciFiHit() : ShipHit() {}
   ~SciFiHit() = default;
   //SciFiHit(Int_t detID, Float_t digi);
   SciFiHit(Int_t detID, Float_t digi, uint32_t hitTime, uint32_t fineTime, uint16_t ch, uint16_t boardId, uint16_t module, bool flag);
   //SciFiHit(Int_t detID, Float_t digi, uint32_t hitTime, uint32_t fineTime, uint16_t amp, uint16_t ch, uint16_t sticId, uint16_t boardId, bool flag);
   void EndPoints(TVector3 &top, TVector3 &bot);

private:
    SciFiHit(const SciFiHit& other);
    SciFiHit operator=(const SciFiHit& other);
    uint32_t hitTime;
    uint32_t fineTime;
    //uint16_t amp;
    uint16_t ch;
    //uint16_t sticId;
    uint16_t boardId;
    uint16_t module;
    bool flag;
    //int16_t trigFlag;
    //bool trigFlag;

   ClassDef(SciFiHit, 1)
};

#endif
