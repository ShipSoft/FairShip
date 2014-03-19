#ifndef MAGNET_H
#define MAGNET_H

#include "FairModule.h"                 // for FairModule

#include "Rtypes.h"                     // for ShipMagnet::Class, Bool_t, etc

#include <string>                       // for string

class ShipMagnet : public FairModule
{
  public:
    ShipMagnet(const char* name, const char* Title="PND Magnet");
    ShipMagnet();
    virtual ~ShipMagnet();
    void ConstructGeometry();
    ClassDef(ShipMagnet,1)

};

#endif //MAGNET_H

