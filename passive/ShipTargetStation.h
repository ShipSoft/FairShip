#ifndef TargetStation_H
#define TargetStation_H

#include "FairModule.h"                 // for FairModule

#include "Rtypes.h"                     // for ShipTargetStation::Class, Bool_t, etc

#include <string>                       // for string

class ShipTargetStation : public FairModule
{
  public:
    ShipTargetStation(const char* name,const Double_t tl,const Double_t al,const Double_t tz,const Double_t az, const char* Title="ShipTargetStation");
    ShipTargetStation();
    virtual ~ShipTargetStation();
    void ConstructGeometry();
    ClassDef(ShipTargetStation,1)
 protected:
  
  Double_t fTargetLength;       //
  Double_t fAbsorberLength;       //
  Double_t fAbsorberZ;       //
  Double_t fTargetZ;       //


};

#endif //TargetStation_H

