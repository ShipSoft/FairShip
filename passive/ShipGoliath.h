#ifndef GOLIATH_H
#define GOLIATH_H

#include "FairModule.h"                 // for FairModule

#include "Rtypes.h"                     // for ShipMagnet::Class, Bool_t, etc

#include <string>                       // for string

class ShipGoliath : public FairModule
{
  public:
    ShipGoliath(const char* name, const char* Title="Goliath");
    ShipGoliath();
    virtual ~ShipGoliath();
    void ConstructGeometry();
    ClassDef(ShipGoliath,1)

};

#endif //GOLIATH_H

