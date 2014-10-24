#ifndef GOLIATH_H
#define GOLIATH_H

#include "FairModule.h"                 // for FairModule

#include "Rtypes.h"                     // for ShipMagnet::Class, Bool_t, etc

#include <string>                       // for string

class ShipGoliath : public FairModule
{
  public:
    ShipGoliath(const char* name, const Double_t zC, const Double_t LS, const Double_t TS, const Double_t GapTS, const char* Title="Goliath");
    ShipGoliath();
    virtual ~ShipGoliath();
    void ConstructGeometry();
    ClassDef(ShipGoliath,1)

protected:
    Double_t zCenter;
    Double_t LongitudinalSize;
    Double_t TransversalSize;
    Double_t GapFromTSpectro;
};

#endif //GOLIATH_H

