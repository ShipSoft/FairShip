#ifndef SCIFIHIT_H
#define SCIFIHIT_H

#include "ShipHit.h"

class SciFiHit : public ShipHit {
public:
   SciFiHit() : ShipHit() {}
   ~SciFiHit() = default;
   SciFiHit(Int_t detID, Float_t digi, uint32_t hitTime, uint16_t fineTime, bool flags, bool triggerFlag);
   //void SciFiHit::GetSciFiXYZ(TVector3 &v, int detID) {
   void EndPoints(TVector3 &top, TVector3 &bot);
   //int16_t trigFlag;


   //SciFiHit(Int_t detID, Float_t digi);
   //SciFiHit(Int_t detID, Float_t digi, uint32_t hitTime, uint32_t fineTime, uint16_t amp, uint16_t ch, uint16_t sticId, uint16_t boardId, bool flag);

private:
    SciFiHit(const SciFiHit& other);
    SciFiHit operator=(const SciFiHit& other);
    uint32_t hitTime;
    uint16_t fineTime;
    bool flags;
    bool triggerFlag;

   ClassDef(SciFiHit, 1)
};

#endif
