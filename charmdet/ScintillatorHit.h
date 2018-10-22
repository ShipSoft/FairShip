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
   bool isLeading() const { return !isTrailing(); }
   int GetTDC() const { return int((channel & 0xF00) >> 8); }
   bool TDCGood() const
   {
      auto TDC = GetTDC();
      auto AllOK = (flags & DriftTubes::All_OK) == DriftTubes::All_OK;
      uint16_t TDCNotOK = 1 << (TDC + 1);
      return AllOK || !((flags & TDCNotOK) == TDCNotOK);
   }
   // return hardware channel (ignore edge)
   uint16_t GetChannel() const { return channel % 0x1000; }
   /* Float_t GetWidth() const { return width; } */

private:
   ScintillatorHit(const ScintillatorHit &other);
   ScintillatorHit operator=(const ScintillatorHit &other);
   uint16_t flags; ///< flag
   uint16_t channel;

   ClassDef(ScintillatorHit, 4)
};

#endif
