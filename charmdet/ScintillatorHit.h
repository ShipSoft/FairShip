#ifndef SCINTILLATORHIT_H
#define SCINTILLATORHIT_H

#include "ShipHit.h"
#include "ShipOnlineDataFormat.h"

class ScintillatorHit : public ShipHit {
public:
   ScintillatorHit() = default;
   ~ScintillatorHit() = default;
   ScintillatorHit(Int_t detID, Float_t digi, Float_t signal_width, uint16_t flag, uint16_t ch);
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
   bool hasTimeOverThreshold() const { return !((flags & DriftTubes::NoWidth) == DriftTubes::NoWidth); }
   Float_t GetTimeOverThreshold() const { return time_over_threshold; }

private:
   ScintillatorHit(const ScintillatorHit &other);
   ScintillatorHit operator=(const ScintillatorHit &other);
   uint16_t flags; ///< flag
   uint16_t channel;
   Float_t time_over_threshold;

   ClassDef(ScintillatorHit, 5)
};

#endif
