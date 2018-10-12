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
   MufluxSpectrometerHit(Int_t detID, Float_t ftdc, uint16_t flag, uint16_t ch);
   MufluxSpectrometerHit(MufluxSpectrometerPoint *p, Double_t t0);
   void MufluxSpectrometerEndPoints(TVector3 &vbot, TVector3 &vtop);
   /** Destructor **/
   virtual ~MufluxSpectrometerHit();

   /** Output to screen **/
   virtual void Print() const;
   Float_t tdc() const { return fdigi; }
   void setInvalid() { flags &= ~DriftTubes::Valid; }
   bool isValid() const { return flags & DriftTubes::Valid; }
   bool isTrailing() const { return (channel & 0x1000) == 0x1000; }
   bool isLeading() const { return !isLeading(); }
   int GetTDC() const { return int((channel & 0xF00) >> 8); }

private:
   /** Copy constructor **/
   MufluxSpectrometerHit(const MufluxSpectrometerHit &point);
   MufluxSpectrometerHit operator=(const MufluxSpectrometerHit &point);

   uint16_t flags; ///< flag
   uint16_t channel;

   ClassDef(MufluxSpectrometerHit, 5);
};

#endif
