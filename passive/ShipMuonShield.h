#ifndef MuonShield_H
#define MuonShield_H

#include "FairModule.h"                 // for FairModule
#include "FairLogger.h"

#include "Rtypes.h"                     // for ShipMuonShield::Class, Bool_t, etc

#include "TGeoUniformMagField.h"
#include "TGeoMedium.h"
#include "TGeoShapeAssembly.h"
#include "TString.h"
#include <vector>
#include <array>

enum class FieldDirection { up, down };

class ShipMuonShield : public FairModule
{
  public:

   ShipMuonShield(const char* name, const Int_t Design=1,  const char* Title="ShipMuonShield",
                               Double_t Z=0, Double_t L0=0, Double_t L1=0, Double_t L2=0, Double_t L3=0, Double_t L4=0, Double_t L5=0, Double_t L6=0, 
                               Double_t L7=0, Double_t L8=0,Double_t gap=0,Double_t LE=0,Double_t y=400, Double_t floor=500, Double_t field=1.8);

   ShipMuonShield();
   virtual ~ShipMuonShield();
   void ConstructGeometry();
   ClassDef(ShipMuonShield,4)

  void SetSupports(Bool_t supports) { 
    fSupport = supports;
    FairLogger::GetLogger()->Warning(MESSAGE_ORIGIN, "Setting supports to %s. This will not have any effect if called after the geometry has been constructed.", fSupport ? "true" : "false");
  }
    
 protected:
  
  Int_t  fDesign;       // design of muon shield, 1=passive, active = ...
  Double_t  fMuonShieldLength,fY,fField;
  Double_t fFloor;
  Bool_t fSupport;
  Double_t  dZ0,dZ1,dZ2,dZ3,dZ4,dZ5,dZ6,dZ7,dZ8,dXgap,zEndOfAbsorb,mag4Gap,midGapOut7,midGapOut8;
  Int_t InitMedium(TString name);
  
  void CreateArb8(const char* arbName, TGeoMedium* medium,Double_t dZ,std::array<Double_t,16> corners,Int_t color,
				     TGeoUniformMagField *magField,TGeoVolume *top,Int_t numberOfItems,Double_t x_translation,Double_t y_translation,
					Double_t z_translation);

  void CreateTube(const char* tubeName, TGeoMedium* medium, Double_t dX,Double_t dY,Double_t dZ,Int_t color,TGeoVolume *top,Int_t numberOfItems, Double_t x_translation,Double_t y_translation,
					Double_t z_translation);


  void Initialize(const char *(&magnetName)[9],
		  FieldDirection (&fieldDirection)[9], Double_t (&dXIn)[9],
		  Double_t (&dYIn)[9], Double_t (&dXOut)[9],
		  Double_t (&dYOut)[9], Double_t (&dZ)[9],
		  Double_t (&midGapIn)[9], Double_t (&midGapOut)[9],
		  Double_t (&HmainSideMagIn)[9], Double_t (&HmainSideMagOut)[9],
		  Double_t (&gapIn)[9], Double_t (&gapOut)[9],
		  Double_t (&Z)[9]);

  void CreateMagnet(const char* magnetName, TGeoMedium *medium, TGeoVolume *tShield,
		    TGeoUniformMagField *fields[4],
		    FieldDirection fieldDirection, Double_t dX, Double_t dY,
		    Double_t dX2, Double_t dY2, Double_t dZ, Double_t middleGap,
		    Double_t middleGap2, Double_t HmainSideMag,
		    Double_t HmainSideMag2, Double_t gap, Double_t gap2,
		    Double_t Z, Bool_t NotMagnet);
};

#endif //MuonSield_H
