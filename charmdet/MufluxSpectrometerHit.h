#ifndef MUFLUXSPECTROMETERHIT_H
#define MUFLUXSPECTROMETERHIT_H 1

#include "ShipHit.h"
#include "MufluxSpectrometerPoint.h"
#include "ShipOnlineDataFormat.h"
#include "TVector3.h"

class MufluxSpectrometerHit : public ShipHit {
public:
   /** Default constructor **/
   MufluxSpectrometerHit() = default;

   /** Constructor with arguments
    *@param detID    Detector ID
    *@param digi     digitized/measured TDC
    *@param flags    collection of flags
    **/
   MufluxSpectrometerHit(Int_t detID, Float_t ftdc);
   MufluxSpectrometerHit(Int_t detID, Float_t ftdc, Float_t signal_width, uint16_t flag, uint16_t ch);
   MufluxSpectrometerHit(MufluxSpectrometerPoint *p, Double_t t0);
   void MufluxSpectrometerEndPoints(TVector3 &vbot, TVector3 &vtop, bool charm); // false for muonflux configuration, true for charm one
   /** Destructor **/
   virtual ~MufluxSpectrometerHit();

   /** Output to screen **/
   virtual void Print() const;
   Float_t tdc() const { return fdigi; }
   void setInvalid() { flags |= DriftTubes::InValid; }
   void setValid() { flags &= ~DriftTubes::InValid; }
   bool isValid() const { return !((flags & DriftTubes::InValid) == DriftTubes::InValid); }
   int GetTDC() const { return int((channel & 0xF00) >> 8); }
   bool TDCGood() const
   {
      auto TDC = GetTDC();
      auto AllOK = (flags & DriftTubes::All_OK) == DriftTubes::All_OK;
      uint16_t TDCNotOK = 1 << (TDC + 1);
      return AllOK || !((flags & TDCNotOK) == TDCNotOK);
   }
   bool hasDelay() const { return !((flags & DriftTubes::NoDelay) == DriftTubes::NoDelay); }
   bool hasTrigger() const { return !((flags & DriftTubes::NoTrigger) == DriftTubes::NoTrigger); }
   bool hasTimeOverThreshold() const { return !((flags & DriftTubes::NoWidth) == DriftTubes::NoWidth); }
   Float_t GetTimeOverThreshold() const { return time_over_threshold; }
   std::vector<int> StationInfo();
private:
   /** Copy constructor **/
   MufluxSpectrometerHit(const MufluxSpectrometerHit &point);
   MufluxSpectrometerHit operator=(const MufluxSpectrometerHit &point);

   Float_t time_over_threshold;
   uint16_t flags;
   uint16_t channel;

   ClassDef(MufluxSpectrometerHit, 8);
};

#endif
