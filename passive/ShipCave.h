#ifndef Cave_H
#define Cave_H

#include "FairModule.h"                 // for FairModule

#include "Rtypes.h"                     // for ShipCave::Class, ClassDef, etc

class ShipCave : public FairModule
{
  public:
    ShipCave(const char* name, const char* Title="Exp Cave");
    ShipCave();
    virtual ~ShipCave();
    virtual void ConstructGeometry();


  private:
    Double_t world[3];
    ClassDef(ShipCave,1) //PNDCaveSD
};

#endif //Cave_H

