#ifndef MuonShield_H
#define MuonShield_H

#include "FairModule.h"                 // for FairModule

#include "Rtypes.h"                     // for ShipMuonShield::Class, Bool_t, etc

#include <string>                       // for string
#include "TGeoUniformMagField.h"
#include "TGeoMedium.h"
#include "TGeoShapeAssembly.h"
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
  void Initialize(Double_t& dX1,std::vector<std::vector<Double_t> >& corners,Double_t& Z1, Double_t& X2,Double_t& dXH1,Double_t& Z2,
		 Double_t& Z3,Double_t& Z4,Double_t& Z6,Double_t& Z7,Double_t& Z8,Double_t& ZGmid,Double_t& dY);
};

#endif //MuonSield_H
