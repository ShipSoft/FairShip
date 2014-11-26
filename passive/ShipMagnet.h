#ifndef MAGNET_H
#define MAGNET_H

#include "FairModule.h"                 // for FairModule
#include "TGeoMedium.h"

#include "Rtypes.h"                     // for ShipMagnet::Class, Bool_t, etc

#include <string>                       // for string

class ShipMagnet : public FairModule
{
  public:
    ShipMagnet(const char* name, const char* Title="SHiP Magnet",Double_t z=2018.,Int_t c=2,Double_t dy=5);
    ShipMagnet();
    virtual ~ShipMagnet();
    void ConstructGeometry();
    ClassDef(ShipMagnet,2)
 protected:
  
  Int_t  fDesign;       // design, 1=circular 5m, 2 = ellipse 5x10
  Int_t  fSpecMagz;     // z position
  Int_t  fDy;          // y diameter of ellipse
  Int_t InitMedium(const char* name);
};

#endif //MAGNET_H

