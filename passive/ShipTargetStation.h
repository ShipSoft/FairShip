#ifndef TargetStation_H
#define TargetStation_H

#include "FairModule.h"                 // for FairModule

#include "Rtypes.h"                     // for ShipTargetStation::Class, Bool_t, etc

#include <string>                       // for string

class ShipTargetStation : public FairModule
{
  public:
    ShipTargetStation(const char* name, const Double_t MuonShield=700, const char* Title="ShipTargetStation");
    ShipTargetStation();
    virtual ~ShipTargetStation();
    void ConstructGeometry();
    ClassDef(ShipTargetStation,1)
 protected:
  
  Double_t fMuonShieldLength;       // Length of muon shield, need to know for positioning the target 


};

#endif //TargetStation_H

