#ifndef PIXELHIT_H
#define PIXELHIT_H 1

#include "ShipHit.h"
#include "ShipOnlineDataFormat.h"

struct HitID {
   int32_t partitionID;
   int32_t frontEndID;
   int32_t moduleID;
   int32_t row;
   int32_t column;
};


class ShipPixelHit : public ShipHit {
public:
   /** Default constructor **/
   ShipPixelHit() = default;
   ~ShipPixelHit() = default;

   /** Constructor with arguments
    *@param detID    Detector ID
    *@param tot      digitized/measured time over threshold in nanoseconds
    *@param flags    collection of flags
    **/
   ShipPixelHit(int32_t detID, uint16_t tot);
   HitID GetPixel();
   int32_t GetDetectorID() const { return detID; }
   int32_t GetModule();
   void PixelCenter(TVector3 &pixel);
   void Print() const;
   uint16_t GetTimeOverThreshold() const { return tot*25; } // tot is measured in steps of 25 ns, so multiply by 25 to get ns value

private:
   /** Copy constructor **/
   ShipPixelHit(const ShipPixelHit &other);
   ShipPixelHit operator=(const ShipPixelHit &other);

   int32_t detID;
   uint16_t tot;

   ClassDef(ShipPixelHit, 1);
};

#endif
