#ifndef TargetStation_H
#define TargetStation_H

#include "FairModule.h"                 // for FairModule
#include "Rtypes.h"                     // for ShipTargetStation::Class, Bool_t, etc
#include <string>                       // for string
#include <stdlib.h>

//C-AMM inside or outside class ? Maybe outside but in another header with other similar enum for other subdetectors ?
enum TargetVersion{
  oneBlock = 0,
  //1 to 10 for fixed absorber+air gap structure 
  old = 10,
  //Above 10 for variable sections
  CDR = 18, //tube geo
  Jun25 = 20 // tube geo
};

class ShipTargetStation : public FairModule
{
public:
  ShipTargetStation(const char* name,
		    const Double_t tl,
		    const Double_t al,
		    const Double_t tz,
		    const Double_t az,
		    const TargetVersion tV,
		    const int nS,
		    const Double_t sl,
		    const char* Title="ShipTargetStation");
  ShipTargetStation(const char* name,
		    const Double_t tl,
		    const Double_t tz,
		    const TargetVersion tV,
		    const int nS,
		    const Double_t sl,
		    const char* Title="ShipTargetStation");
  ShipTargetStation();
  virtual ~ShipTargetStation();
  void ConstructGeometry();
  void SetLayerPosMat(Float_t d,
		      std::vector<float> L,
		      std::vector<float> G,
		      std::vector<std::string> M){
    fDiameter = d;
    fL = L;
    //variable gap sizes
    if (G.size()>0) fG = G;
    //fixed gap sizes
    else fG.resize(fL.size()-1,fsl);
    //last element should be 0...
    fG.push_back(0);
    fM = M;
  }
  ClassDef(ShipTargetStation,5);
protected:
  
  Double_t fTargetLength;       //
  Double_t fAbsorberLength;       //
  Double_t fAbsorberZ;       //
  Double_t fTargetZ;       //
  Double_t fDiameter;      //
  std::vector<float> fL; //absorber width per layer
  std::vector<float> fG; //gap after layer
  std::vector<std::string> fM; //absorber material
  Int_t InitMedium(const char* name);
  Int_t fnS;
  Double_t fsl;
  TargetVersion fTV;
};
#endif //TargetStation_H
