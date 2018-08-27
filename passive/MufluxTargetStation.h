#ifndef MufluxTargetStation_H
#define MufluxTargetStation_H

#include "FairModule.h"                 // for FairModule
#include "Rtypes.h"                     // for MufluxTargetStation::Class, Bool_t, etc
#include <string>                       // for string
#include <stdlib.h>

class MufluxTargetStation : public FairModule
{
  public:
    MufluxTargetStation(const char* name,const Double_t tl,const Double_t al,const Double_t tz,const Double_t az, 
                      const int nS, const Double_t sl, const char* Title="MufluxTargetStation");
    MufluxTargetStation(const char* name,const Double_t tl,const Double_t tz,
                      const int nS, const Double_t sl, const char* Title="MufluxTargetStation");
    MufluxTargetStation();
    virtual ~MufluxTargetStation();
    
    void SetIronAbsorber(Double_t absorber_x, Double_t absorber_y);
    void SetAbsorberCutout(Double_t absorbercutout_x ,Double_t absorbercutout_y);
    void SetIronShield(Double_t ironshield_x, Double_t ironshield_y, Double_t ironshield_z);
    void SetConcreteShield(Double_t concreteshield_x, Double_t concreteshield_y, Double_t concreteshield_z);
    void SetAboveTargetShield(Double_t abovetargetshield_x, Double_t abovetargetshield_y, Double_t abovetargetshield_z);
    void SetAboveAbsorberShield(Double_t aboveabsorbershield_x, Double_t aboveabsorbershield_y, Double_t aboveabsorbershield_z);
    void SetAboveAboveTargetShield(Double_t aboveabovetargetshield_y);
    void SetFloor(Double_t floor_x, Double_t floor_y, Double_t floor_z);
    void SetFloorT34(Double_t floorT34_x, Double_t floorT34_y, Double_t floorT34_z);
    void SetFloorRPC(Double_t floorRPC_x, Double_t floorRPC_y, Double_t floorRPC_z);
    
    void ConstructGeometry();
    void SetLayerPosMat(Float_t d, std::vector<float> L, std::vector<std::string> M){
     fDiameter = d;  
     fL = L;
     fM = M;
     }
    ClassDef(MufluxTargetStation,4)
    
 private:
  Double_t fabsorber_x;
  Double_t fabsorber_y;
  Double_t fabsorbercutout_x;
  Double_t fabsorbercutout_y;
  Double_t fironshield_x;
  Double_t fironshield_y;
  Double_t fironshield_z;
  Double_t fconcreteshield_x;
  Double_t fconcreteshield_y;
  Double_t fconcreteshield_z;
  Double_t fabovetargetshield_x;
  Double_t fabovetargetshield_y;
  Double_t fabovetargetshield_z;
  Double_t faboveabsorbershield_x;
  Double_t faboveabsorbershield_y;
  Double_t faboveabsorbershield_z;
  Double_t faboveabovetargetshield_y;
  Double_t ffloor_x;
  Double_t ffloor_y;
  Double_t ffloor_z;
  Double_t ffloorT34_x;
  Double_t ffloorT34_y;
  Double_t ffloorT34_z;
  Double_t ffloorRPC_x;
  Double_t ffloorRPC_y;
  Double_t ffloorRPC_z;    
        
 protected:
  
  Double_t fTargetLength;       //
  Double_t fAbsorberLength;       //
  Double_t fAbsorberZ;       //
  Double_t fTargetZ;       //
  Double_t fDiameter;      //
  std::vector<float> fL; //
  std::vector<std::string> fM; //
  Int_t InitMedium(const char* name);
  Int_t fnS;
  Double_t fsl;
};
#endif //MufluxTargetStation_H
