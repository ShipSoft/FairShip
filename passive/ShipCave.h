#ifndef Cave_H
#define Cave_H

#include "FairModule.h"                 // for FairModule

#include "Rtypes.h"                     // for ShipCave::Class, ClassDef, etc

class ShipCave : public FairModule
{
  public:
    ShipCave(Double_t z);
    ShipCave(const char* name, const char* Title="Exp Cave");
    ShipCave();
    virtual ~ShipCave();
    virtual void ConstructGeometry();


  private:
    Double_t z_end_of_proximity_shielding;
    Double_t world[3];
    Int_t InitMedium(TString name);

  public:
    ClassDef(ShipCave, 1)
};

#endif //Cave_H
