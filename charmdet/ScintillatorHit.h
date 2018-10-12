#ifndef SCINTILLATORHIT_H
#define SCINTILLATORHIT_H

#include "ShipHit.h"
#include "ShipOnlineDataFormat.h"

class ScintillatorHit : public ShipHit {
public:
   ScintillatorHit() = default;
   ~ScintillatorHit() = default;
   ScintillatorHit(Int_t detID, Float_t ftdc, uint16_t flag, uint16_t ch);
   bool isTrailing() const { return (channel & 0x1000) == 0x1000; }
   bool isLeading() const { return !isLeading(); }
   int GetTDC() const { return int((channel & 0xF00) >> 8); }

private:
   ScintillatorHit(const ScintillatorHit &other);
   ScintillatorHit operator=(const ScintillatorHit &other);
   uint16_t flags; ///< flag
   uint16_t channel;

   ClassDef(ScintillatorHit, 2)
};

#endif
