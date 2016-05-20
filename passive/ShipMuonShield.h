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
   ClassDef(ShipMuonShield,3)
    
 protected:
  
  Int_t  fDesign;       // design of muon shield, 1=passive, active = ...
  Double_t  fMuonShieldLength,fY,fField ;
  Double_t  dZ0,dZ1,dZ2,dZ3,dZ4,dZ5,dZ6,dZ7,dZ8,dXgap,zEndOfAbsorb,mag4Gap,midGapOut7,midGapOut8;
  Int_t InitMedium(const char* name);
  
 /* void CreateBox(const char* boxName, TGeoMedium* medium, Double_t dX,Double_t dY,Double_t dZ,
					Int_t color,TGeoUniformMagField *magField,TGeoVolume *top,Int_t numberOfItems, Double_t x_translation,Double_t y_translation,
					Double_t z_translation);
  */
  void CreateArb8(const char* arbName, TGeoMedium* medium,Double_t dZ,Double_t corners[16],Int_t color,
				     TGeoUniformMagField *magField,TGeoVolume *top,Int_t numberOfItems,Double_t x_translation,Double_t y_translation,
					Double_t z_translation);

  void CreateArb8(const char* arbName, TGeoMedium* medium,Double_t dZ,std::vector<Double_t> corners,Int_t color,
				     TGeoUniformMagField *magField,TGeoVolume *top,Int_t numberOfItems,Double_t x_translation,Double_t y_translation,
					Double_t z_translation);
 
 
  void CreateTube(const char* tubeName, TGeoMedium* medium, Double_t dX,Double_t dY,Double_t dZ,Int_t color,TGeoVolume *top,Int_t numberOfItems, Double_t x_translation,Double_t y_translation,
					Double_t z_translation);
  void Initialize(const char* (&magnetName)[8],const char* (&fieldDirection)[8],
				    Double_t (&dXIn)[8], Double_t (&dYIn)[8], Double_t (&dXOut)[8], Double_t (&dYOut)[8], Double_t (&dZ)[8],
				  Double_t (&midGapIn)[8],Double_t (&midGapOut)[8],
				  Double_t (&HmainSideMagIn)[8], Double_t (&HmainSideMagOut)[8],
				  Double_t (&gapIn)[8],Double_t (&gapOut)[8], Double_t (&Z)[8]);

  void CreateMagnet(const char* magnetName,TGeoMedium* medium,TGeoVolume *tShield,TGeoUniformMagField *fields[4],const char* fieldDirection,
				  Double_t dX, Double_t dY, Double_t dX2, Double_t dY2, Double_t dZ,
				  Double_t middleGap,Double_t middleGap2,
				  Double_t HmainSideMag, Double_t HmainSideMag2,
				  Double_t gap,Double_t gap2, Double_t Z,Bool_t NotMagnet);
};

#endif //MuonSield_H
