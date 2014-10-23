#ifndef MuonShield_H
#define MuonShield_H

#include "FairModule.h"                 // for FairModule

#include "Rtypes.h"                     // for ShipMuonShield::Class, Bool_t, etc

#include <string>                       // for string

class ShipMuonShield : public FairModule
{
  public:
    ShipMuonShield(const char* name, const Int_t Design=1,  const char* Title="ShipMuonShield",
                               Double_t Z=0, Double_t L1=0, Double_t L2=0, Double_t L3=0, Double_t L4=0, Double_t L5=0, Double_t L6=0, Double_t LE=0);
    ShipMuonShield();
    virtual ~ShipMuonShield();
    void ConstructGeometry();
    ClassDef(ShipMuonShield,1)
 protected:
  
  Int_t  fDesign;       // design of muon shield, 1=passive, active = ...
  Double_t  fMuonShieldLength ;
  Double_t  dZ1,dZ2,dZ3,dZ4,dZ5,dZ6,zEndOfAbsorb;
  Int_t InitMedium(const char* name);

};

#endif //MuonShield_H

