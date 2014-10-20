#ifndef Chamber_H
#define Chamber_H

#include "FairModule.h"                 // for FairModule

#include "Rtypes.h"                     // for ShipChamber::Class, Bool_t, etc

#include <string>                       // for string

class ShipChamber : public FairModule
{
  public:
    ShipChamber(const char* name, const char* Title="ShipChamber");
    ShipChamber();
    virtual ~ShipChamber();
    void ConstructGeometry();
    ClassDef(ShipChamber,1)
    Int_t InitMedium(const char* name);

};

#endif //Chamber_H

