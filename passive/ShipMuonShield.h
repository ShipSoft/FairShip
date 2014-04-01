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
    ClassDef(ShipMuonShield,1)
 protected:
  
  Int_t  fDesign;       // design of muon shield, 1=passive, active = ...

};

#endif //MuonShield_H

