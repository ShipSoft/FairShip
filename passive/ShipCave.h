#ifndef PASSIVE_SHIPCAVE_H_
#define PASSIVE_SHIPCAVE_H_

#include "FairModule.h"                 // for FairModule

#include "Rtypes.h"                     // for ShipCave::Class, ClassDef, etc

class ShipCave : public FairModule
{
  public:
    explicit ShipCave(Double_t z);
    explicit ShipCave(const char* name, const char* Title="Exp Cave");
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

#endif  // PASSIVE_SHIPCAVE_H_
