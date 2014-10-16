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

    void SetZpositions(Double32_t z1, Double32_t z2, Double32_t z3, Double32_t z4, Double32_t z5, Double32_t z6);
    void SetTublengths(Double32_t l1, Double32_t l2, Double32_t l3, Double32_t l4, Double32_t l5, Double32_t l6);
    void SetRmin(Double32_t rmin);
    void SetRmax(Double32_t rmax);

  private:
    Double32_t fTub1z;
    Double32_t fTub2z;
    Double32_t fTub3z;
    Double32_t fTub4z;
    Double32_t fTub5z;
    Double32_t fTub6z;
    Double32_t fTub1length;
    Double32_t fTub2length;
    Double32_t fTub3length;
    Double32_t fTub4length;
    Double32_t fTub5length;
    Double32_t fTub6length;
    Double32_t fRmin;
    Double32_t fRmax;
};

#endif //Chamber_H

