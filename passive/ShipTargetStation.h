#ifndef TargetStation_H
#define TargetStation_H

#include "FairModule.h"                 // for FairModule
#include "Rtypes.h"                     // for ShipTargetStation::Class, Bool_t, etc
#include <string>                       // for string
#include <stdlib.h>

class ShipTargetStation : public FairModule
{
  public:
    ShipTargetStation(const char* name,const Double_t tl,const Double_t al,const Double_t tz,const Double_t az, 
                      const int nS, const Double_t sl, const char* Title="ShipTargetStation");
    ShipTargetStation(const char* name,const Double_t tl,const Double_t tz,
                      const int nS, const Double_t sl, const char* Title="ShipTargetStation");
    ShipTargetStation();
    virtual ~ShipTargetStation();
    void ConstructGeometry();
    void SetLayerPosMat(Float_t d, std::vector<float> L, std::vector<std::string> M){
     fDiameter = d;  
     fL = L;
     fM = M;
     }
    ClassDef(ShipTargetStation,4)
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
#endif //TargetStation_H
