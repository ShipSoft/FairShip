#ifndef MuonShield_H
#define MuonShield_H

#include "FairModule.h"                 // for FairModule

#include "Rtypes.h"                     // for ShipMuonShield::Class, Bool_t, etc

#include <string>                       // for string

class ShipMuonShield : public FairModule
{
  public:
    ShipMuonShield(const char* name, const Int_t Design=1,  const char* Title="ShipMuonShield");
    ShipMuonShield();
    virtual ~ShipMuonShield();
    void ConstructGeometry();
    Double_t GetStartZ();
    ClassDef(ShipMuonShield,1)
 protected:
  
  Int_t  fDesign;       // design of muon shield, 1=passive, active = ...
  Double_t  fstartZ;   
  Double_t  decayVolumeLength;  
  Double_t  fMuonShieldLength ;
  Double_t  dZ1,dZ2,dZ3,dZ4,dZ5,dZ6,zEndOfAbsorb;

};

#endif //MuonShield_H

