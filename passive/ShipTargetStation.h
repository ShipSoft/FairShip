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
    ShipTargetStation();
    virtual ~ShipTargetStation();
    void ConstructGeometry();
    void SetLayerPosMat(Float_t d,Float_t l1,const char* m1,Float_t l2,const char* m2,Float_t l3,const char* m3,Float_t l4,const char* m4,Float_t l5,const char* m5,
                        Float_t l6,const char* m6,Float_t l7,const char* m7,Float_t l8,const char* m8,Float_t l9,const char* m9,Float_t l10,const char* m10,
                        Float_t l11,const char* m11,Float_t l12,const char* m12,Float_t l13,const char* m13,Float_t l14,const char* m14,
                        Float_t l15,const char* m15,Float_t l16,const char* m16,Float_t l17,const char* m17){ 
     fL.push_back(l1);
     fL.push_back(l2);
     fL.push_back(l3);
     fL.push_back(l4);
     fL.push_back(l5);
     fL.push_back(l6);
     fL.push_back(l7);
     fL.push_back(l8);
     fL.push_back(l9);
     fL.push_back(l10);
     fL.push_back(l11);
     fL.push_back(l12);
     fL.push_back(l13);
     fL.push_back(l14);
     fL.push_back(l15);
     fL.push_back(l16);
     fL.push_back(l17);
     fM.push_back(m1);
     fM.push_back(m2);
     fM.push_back(m3);
     fM.push_back(m4);
     fM.push_back(m5);
     fM.push_back(m6);
     fM.push_back(m7);
     fM.push_back(m8);
     fM.push_back(m9);
     fM.push_back(m10);
     fM.push_back(m11);
     fM.push_back(m12);
     fM.push_back(m13);
     fM.push_back(m14);
     fM.push_back(m15);
     fM.push_back(m16);
     fM.push_back(m17);  
     fDiameter = d;                                         
     }

    ClassDef(ShipTargetStation,2)
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
