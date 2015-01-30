#ifndef MuonShield_H
#define MuonShield_H

#include "FairModule.h"                 // for FairModule

#include "Rtypes.h"                     // for ShipMuonShield::Class, Bool_t, etc

#include <string>                       // for string
#include "TGeoUniformMagField.h"
#include "TGeoMedium.h"
#include <vector>


class ShipMuonShield : public FairModule
{
  public:
   ShipMuonShield(const char* name, const Int_t Design=1,  const char* Title="ShipMuonShield",
                               Double_t Z=0, Double_t L0=0, Double_t L1=0, Double_t L2=0, Double_t L3=0, Double_t L4=0, Double_t L5=0, Double_t L6=0, 
                               Double_t L7=0, Double_t L8=0,Double_t gap=0,Double_t LE=0,Double_t y=400,Double_t fl=1.8);
   ShipMuonShield();
   virtual ~ShipMuonShield();
   void ConstructGeometry();
   ClassDef(ShipMuonShield,2)
    
 protected:
  
  Int_t  fDesign;       // design of muon shield, 1=passive, active = ...
  Double_t  fMuonShieldLength,fY,fField ;
  Double_t  dZ0,dZ1,dZ2,dZ3,dZ4,dZ5,dZ6,dZ7,dZ8,dXgap,zEndOfAbsorb;
  Int_t InitMedium(const char* name);
  
  void CreateBox(const char* boxName, TGeoMedium* medium, Double_t dX,Double_t dY,Double_t dZ,
					Int_t color,TGeoUniformMagField *magField,TGeoVolume *top,Int_t numberOfItems, Double_t x_translation,Double_t y_translation,
					Double_t z_translation);
  
  void CreateArb8(const char* arbName, TGeoMedium* medium,Double_t dZ,Double_t corners[16],Int_t color,
				     TGeoUniformMagField *magField,TGeoVolume *top,Int_t numberOfItems,Double_t x_translation,Double_t y_translation,
					Double_t z_translation);

  void CreateArb8(const char* arbName, TGeoMedium* medium,Double_t dZ,std::vector<Double_t> corners,Int_t color,
				     TGeoUniformMagField *magField,TGeoVolume *top,Int_t numberOfItems,Double_t x_translation,Double_t y_translation,
					Double_t z_translation);
 
 
  void CreateTube(const char* tubeName, TGeoMedium* medium, Double_t dX,Double_t dY,Double_t dZ,Int_t color,TGeoVolume *top,Int_t numberOfItems, Double_t x_translation,Double_t y_translation,
					Double_t z_translation);
  void Initialize (Double_t& dX1,std::vector<Double_t>& cornersA1,Double_t& Z1,std::vector<Double_t>& cornersAR,Double_t& X2, std::vector<Double_t>& cornersAT,Double_t& dXH1,std::vector<Double_t>& cornersAB,Double_t& Z2,
		std::vector<Double_t>& corners1,std::vector<Double_t>& corners2,std::vector<Double_t>& corners3,std::vector<Double_t>& corners4,std::vector<Double_t>& corners5,std::vector<Double_t>& corners6,std::vector<Double_t>& corners7,
		 Double_t& Z3, std::vector<Double_t>& cornersC,std::vector<Double_t>& cornersCR,std::vector<Double_t>& cornersCL,std::vector<Double_t>& cornersCLT,std::vector<Double_t>& cornersCLB,std::vector<Double_t>& cornersCRT,std::vector<Double_t>& cornersCRB,
		 std::vector<Double_t>& corners8,std::vector<Double_t>& corners9,std::vector<Double_t>& corners10,std::vector<Double_t>& corners11,Double_t& Z4,std::vector<Double_t>& cornersC4,std::vector<Double_t>& cornersC4L,std::vector<Double_t>& cornersC4LB,std::vector<Double_t>& cornersC4LT,
		 std::vector<Double_t>& cornersC4R,std::vector<Double_t>& cornersC4RB,std::vector<Double_t>& cornersC4RT,std::vector<Double_t>& corners12,std::vector<Double_t>& corners13,std::vector<Double_t>& corners14,std::vector<Double_t>& corners15,Double_t& Z6,std::vector<Double_t>& cornersC6RL,
		 std::vector<Double_t>& cornersC6RR,std::vector<Double_t>& cornersC6L,std::vector<Double_t>& cornersC6R,std::vector<Double_t>& corners20,std::vector<Double_t>& corners21,std::vector<Double_t>& corners22,std::vector<Double_t>& corners23,Double_t& Z7,std::vector<Double_t>& cornersC7RL,
		 std::vector<Double_t>& cornersC7RR,std::vector<Double_t>& cornersC7L,std::vector<Double_t>& cornersC7R,std::vector<Double_t>& corners24,std::vector<Double_t>& corners25,std::vector<Double_t>& corners26,std::vector<Double_t>& corners27,Double_t& Z8,std::vector<Double_t>& cornersC8RL,
		 std::vector<Double_t>& cornersC8RR,std::vector<Double_t>& cornersC8L,std::vector<Double_t>& cornersC8R,std::vector<Double_t>& corners28,std::vector<Double_t>& corners29,std::vector<Double_t>& corners30,std::vector<Double_t>& corners31,Double_t& ZGmid,Double_t& dY);
};

#endif //MuonSield_H
