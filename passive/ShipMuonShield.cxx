#include "ShipMuonShield.h"

#include "TGeoManager.h"
#include "FairRun.h"                    // for FairRun
#include "FairRuntimeDb.h"              // for FairRuntimeDb
#include <iosfwd>                    // for ostream
#include "TList.h"                      // for TListIter, TList (ptr only)
#include "TObjArray.h"                  // for TObjArray
#include "TString.h"                    // for TString
#include "TGeoBBox.h"
#include "TGeoTrd1.h"
#include "TGeoCompositeShape.h"
#include "TGeoBoolNode.h"
#include "TGeoTube.h"
#include "TGeoMaterial.h"
#include "FairGeoInterface.h"
#include "FairGeoMedia.h"
#include "FairGeoBuilder.h"
#include <iostream>                     // for operator<<, basic_ostream, etc

Double_t cm = 1;
Double_t m = 100 * cm;
Double_t mm = 0.1 * cm;
Double_t kilogauss = 1.;
Double_t tesla = 10 * kilogauss;

ShipMuonShield::~ShipMuonShield() {}
ShipMuonShield::ShipMuonShield() : FairModule("ShipMuonShield", "") {}

ShipMuonShield::ShipMuonShield(const char* name, const Int_t Design, const char* Title,
                               Double_t Z, Double_t L0, Double_t L1, Double_t L2, Double_t L3, Double_t L4, Double_t L5, Double_t L6,
                               Double_t L7, Double_t L8, Double_t gap, Double_t LE, Double_t y, Double_t floor, Double_t field)
  : FairModule(name ,Title)
{
 fDesign = Design;
 fField  = field;
 if (fDesign==1){
     fMuonShieldLength = L1;   
    }
 if (fDesign==2 || fDesign==3 || fDesign==4 ){
     Fatal("ShipMuonShield","Design %i not anymore supported",fDesign);
    }
 if (fDesign==5 || fDesign==6){
     dZ0 = L0;
     dZ1 = L1;
     dZ2 = L2;
     dZ3 = L3;
     dZ4 = L4;
     dZ5 = L5;
     dZ6 = L6;
     dZ7 = L7;
     dZ8 = L8;
     dXgap= gap;
     fMuonShieldLength = 2*(dZ1+dZ2+dZ3+dZ4+dZ5+dZ6+dZ7+dZ8) + LE ; //leave some space for nu-tau detector   
    }
    
 if (fDesign==7){
     dZ1 = L1;
     dZ2 = L2;
     dZ3 = L3;
     dZ4 = L4;
     dZ5 = L5;
     dZ6 = L6;
     dZ7 = L7;
     dZ8 = L8;
     fMuonShieldLength =
	 2 * (dZ1 + dZ2 + dZ3 + dZ4 + dZ5 + dZ6 + dZ7 + dZ8) + LE;
   }
    
 fFloor = (fDesign == 7) ? floor : 0;

 zEndOfAbsorb = Z + dZ0 - fMuonShieldLength/2.;   
 if(fDesign==6||fDesign==7){zEndOfAbsorb = Z - fMuonShieldLength/2.;}
 fY = y;
 fSupport = true;
}

// -----   Private method InitMedium 
Int_t ShipMuonShield::InitMedium(TString name) 
{
   static FairGeoLoader *geoLoad=FairGeoLoader::Instance();
   static FairGeoInterface *geoFace=geoLoad->getGeoInterface();
   static FairGeoMedia *media=geoFace->getMedia();
   static FairGeoBuilder *geoBuild=geoLoad->getGeoBuilder();

   FairGeoMedium *ShipMedium=media->getMedium(name);

   if (!ShipMedium)
     Fatal("InitMedium","Material %s not defined in media file.", name.Data());
   TGeoMedium* medium=gGeoManager->GetMedium(name);
   if (medium)
     return ShipMedium->getMediumIndex();
   return geoBuild->createMedium(ShipMedium);
}

void ShipMuonShield::CreateTube(TString tubeName, TGeoMedium *medium,
				Double_t dX, Double_t dY, Double_t dZ,
				Int_t color, TGeoVolume *tShield,
				Double_t x_translation, Double_t y_translation,
				Double_t z_translation) {
  TGeoVolume* absorber = gGeoManager->MakeTube(tubeName, medium, dX, dY,dZ);
  absorber->SetLineColor(color);  
  tShield->AddNode(
      absorber, 1,
      new TGeoTranslation(x_translation, y_translation, z_translation));
}

void ShipMuonShield::CreateArb8(TString arbName, TGeoMedium *medium,
				Double_t dZ, std::array<Double_t, 16> corners,
				Int_t color, TGeoUniformMagField *magField,
				TGeoVolume *tShield, Double_t x_translation,
				Double_t y_translation,
				Double_t z_translation) {
  TGeoVolume *magF =
      gGeoManager->MakeArb8(arbName, medium, dZ, corners.data());
  magF->SetLineColor(color);
  magF->SetField(magField);
  tShield->AddNode(magF, 1, new TGeoTranslation(x_translation, y_translation,
						z_translation));
}

void ShipMuonShield::CreateMagnet(TString magnetName,TGeoMedium* medium,TGeoVolume *tShield,TGeoUniformMagField *fields[4],FieldDirection fieldDirection,
				  Double_t dX, Double_t dY, Double_t dX2, Double_t dY2, Double_t dZ,
				  Double_t middleGap,Double_t middleGap2,
				  Double_t HmainSideMag, Double_t HmainSideMag2,
				  Double_t gap,Double_t gap2, Double_t Z, Bool_t NotMagnet)
  {
    Double_t Clgap,Clgap2;
    Int_t color[4] = {30,31,38,45};

    if (NotMagnet) {
      Clgap = gap;
      Clgap2 = gap2;
    } else {
      Clgap = std::max(20., gap);
      Clgap2 = std::max(20., gap2);
      gap = std::max(2., gap);
      gap2 = std::max(2., gap2);
    }

    Double_t testGap = (fDesign == 5) ? 0.0 : 0.1; // gap between fields in the
						   // corners for mitred joints
						   // (Geant goes crazy when
						   // they touch each other)

    std::array<Double_t,16> cornersMainL = {
	middleGap,	-dY - dX + testGap,
	middleGap,	dY + dX - testGap,
	dX + middleGap,   dY - testGap,
	dX + middleGap,   -dY + testGap,
	middleGap2,       -dY2 - dX2 + testGap,
	middleGap2,       dY2 + dX2 - testGap,
	dX2 + middleGap2, dY2 - testGap,
	dX2 + middleGap2, -dY2 + testGap};
    std::array<Double_t,16> cornersMainR = {
	-dX - middleGap,    -dY + testGap,
	-dX - middleGap,    dY - testGap,
	- middleGap,     dY + dX - testGap,
	- middleGap,     -dY - dX + testGap,
	-dX2 - middleGap2, -dY2 + testGap,
	-dX2 - middleGap2, dY2 - testGap,
	- middleGap2,  dY2 + dX2 - testGap,
	- middleGap2,  -dY2 - dX2 + testGap};
    std::array<Double_t,16> cornersMainSideL = {
	dX + middleGap + gap,	-HmainSideMag,
	dX + middleGap + gap,	HmainSideMag,
	2 * dX + middleGap + gap,    HmainSideMag,
	2 * dX + middleGap + gap,    -HmainSideMag,
	dX2 + middleGap2 + gap2,     -HmainSideMag2,
	dX2 + middleGap2 + gap2,     HmainSideMag2,
	2 * dX2 + middleGap2 + gap2, HmainSideMag2,
	2 * dX2 + middleGap2 + gap2, -HmainSideMag2};
    std::array<Double_t,16> cornersMainSideR = {
	-dX - middleGap - gap,	-HmainSideMag,
	-2 * dX - middleGap - gap,    -HmainSideMag,
	-2 * dX - middleGap - gap,    HmainSideMag,
	-dX - middleGap - gap,	HmainSideMag,
	-dX2 - middleGap2 - gap2,     -HmainSideMag2,
	-2 * dX2 - middleGap2 - gap2, -HmainSideMag2,
	-2 * dX2 - middleGap2 - gap2, HmainSideMag2,
	-dX2 - middleGap2 - gap2,     HmainSideMag2};
    std::array<Double_t,16> cornersCLBA = {
	dX + middleGap + gap,	  -HmainSideMag,
	2 * dX + middleGap + gap,      -HmainSideMag,
	2 * dX + middleGap + Clgap,    -dY - dX + testGap,
	dX + middleGap + Clgap,	-dY + testGap,
	dX2 + middleGap2 + gap2,       -HmainSideMag2,
	2 * dX2 + middleGap2 + gap2,   -HmainSideMag2,
	2 * dX2 + middleGap2 + Clgap2, -dY2 - dX2 + testGap,
	dX2 + middleGap2 + Clgap2,     -dY2 + testGap};
    std::array<Double_t,16> cornersCLTA = {
	dX + middleGap + Clgap,	dY - testGap,
	2 * dX + middleGap + Clgap,    dY + dX - testGap,
	2 * dX + middleGap + gap,      HmainSideMag,
	dX + middleGap + gap,	  HmainSideMag,
	dX2 + middleGap2 + Clgap2,     dY2 - testGap,
	2 * dX2 + middleGap2 + Clgap2, dY2 + dX2 - testGap,
	2 * dX2 + middleGap2 + gap2,   HmainSideMag2,
	dX2 + middleGap2 + gap2,       HmainSideMag2};
    std::array<Double_t,16> cornersCRBA = {
	-dX - middleGap - Clgap,	-dY + testGap,
	-2 * dX - middleGap - Clgap,    -dY - dX + testGap,
	-2 * dX - middleGap - gap,      -HmainSideMag,
	-dX - middleGap - gap,		-HmainSideMag,
	-dX2 - middleGap2 - Clgap2,     -dY2 + testGap,
	-2 * dX2 - middleGap2 - Clgap2, -dY2 - dX2 + testGap,
	-2 * dX2 - middleGap2 - gap2,   -HmainSideMag2,
	-dX2 - middleGap2 - gap2,       -HmainSideMag2};
    std::array<Double_t,16> cornersCRTA = {
	-dX - middleGap - gap,		HmainSideMag,
	-2 * dX - middleGap - gap,      HmainSideMag,
	-2 * dX - middleGap - Clgap,    dY + dX - testGap,
	-dX - middleGap - Clgap,	dY - testGap,
	-dX2 - middleGap2 - gap2,       HmainSideMag2,
	-2 * dX2 - middleGap2 - gap2,   HmainSideMag2,
	-2 * dX2 - middleGap2 - Clgap2, dY2 + dX2 - testGap,
	-dX2 - middleGap2 - Clgap2,     dY2 - testGap};
    std::array<Double_t,16> cornersTL = {
	middleGap + dX, dY,
	middleGap, dY + dX,
	2 * dX + middleGap + Clgap, dY + dX,
	dX + middleGap + Clgap, dY,
	middleGap2 + dX2, dY2,
	middleGap2, dY2 + dX2,
	2 * dX2 + middleGap2 + Clgap2, dY2 + dX2,
	dX2 + middleGap2 + Clgap2, dY2};
    std::array<Double_t,16> cornersTR = {
	-dX - middleGap - Clgap, dY,
	-2 * dX - middleGap - Clgap, dY + dX,
	-middleGap, dY + dX,
	-middleGap - dX, dY,
	-dX2 - middleGap2 - Clgap2, dY2,
	-2 * dX2 - middleGap2 - Clgap2, dY2 + dX2,
	-middleGap2, dY2 + dX2,
	-middleGap2 - dX2, dY2};
    std::array<Double_t,16> cornersBL = {
	dX + middleGap + Clgap, -dY,
	2 * dX + middleGap + Clgap, -dY - dX,
	middleGap, -dY - dX,
	middleGap + dX, -dY,
	dX2 + middleGap2 + Clgap2, -dY2,
	2 * dX2 + middleGap2 + Clgap2, -dY2 - dX2,
	middleGap2, -dY2 - dX2,
	middleGap2 + dX2, -dY2};
    std::array<Double_t,16> cornersBR = {
	-middleGap - dX, -dY,
	-middleGap, -dY - dX,
	-2 * dX - middleGap - Clgap, -dY - dX,
	-dX - middleGap - Clgap, -dY,
	-middleGap2 - dX2, -dY2,
	-middleGap2, -dY2 - dX2,
	-2 * dX2 - middleGap2 - Clgap2, -dY2 - dX2,
	-dX2 - middleGap2 - Clgap2, -dY2};
				 
    TString str1L = "_MiddleMagL";
    TString str1R = "_MiddleMagR";
    TString str2 = "_MagRetL";
    TString str3 = "_MagRetR";
    TString str4 = "_MagCLB";
    TString str5 = "_MagCLT";
    TString str6 = "_MagCRT";
    TString str7 = "_MagCRB";
    TString str8 = "_MagTopLeft";
    TString str9 = "_MagTopRight";
    TString str10 = "_MagBotLeft";
    TString str11 = "_MagBotRight";

    switch (fieldDirection){

    case FieldDirection::up: 
      CreateArb8(magnetName + str1L, medium, dZ, cornersMainL, color[3], fields[0], tShield,  0, 0, Z);
      CreateArb8(magnetName + str1R, medium, dZ, cornersMainR, color[3], fields[0], tShield,  0, 0, Z);
      CreateArb8(magnetName + str2, medium, dZ, cornersMainSideL, color[1], fields[1], tShield,  0, 0, Z);
      CreateArb8(magnetName + str3, medium, dZ, cornersMainSideR, color[1], fields[1], tShield,  0, 0, Z);
      CreateArb8(magnetName + str4, medium, dZ, cornersCLBA, color[1], fields[1], tShield,  0, 0, Z);
      CreateArb8(magnetName + str5, medium, dZ, cornersCLTA, color[1], fields[1], tShield,  0, 0, Z);
      CreateArb8(magnetName + str6, medium, dZ, cornersCRTA, color[1], fields[1], tShield,  0, 0, Z);
      CreateArb8(magnetName + str7, medium, dZ, cornersCRBA, color[1], fields[1], tShield,  0, 0, Z);
      CreateArb8(magnetName + str8, medium, dZ, cornersTL, color[2], fields[3], tShield,  0, 0, Z);
      CreateArb8(magnetName + str9, medium, dZ, cornersTR, color[0], fields[2], tShield,  0, 0, Z);
      CreateArb8(magnetName + str10, medium, dZ, cornersBL, color[0], fields[2], tShield,  0, 0, Z);
      CreateArb8(magnetName + str11, medium, dZ, cornersBR, color[2], fields[3], tShield,  0, 0, Z);
      break;
    case FieldDirection::down:
      CreateArb8(magnetName + str1L, medium, dZ, cornersMainL, color[1], fields[1], tShield,  0, 0, Z);
      CreateArb8(magnetName + str1R, medium, dZ, cornersMainR, color[1], fields[1], tShield,  0, 0, Z);
      CreateArb8(magnetName + str2, medium, dZ, cornersMainSideL, color[3], fields[0], tShield,  0, 0, Z);
      CreateArb8(magnetName + str3, medium, dZ, cornersMainSideR, color[3], fields[0], tShield,  0, 0, Z);
      CreateArb8(magnetName + str4, medium, dZ, cornersCLBA, color[3], fields[0], tShield,  0, 0, Z);
      CreateArb8(magnetName + str5, medium, dZ, cornersCLTA, color[3], fields[0], tShield,  0, 0, Z);
      CreateArb8(magnetName + str6, medium, dZ, cornersCRTA, color[3], fields[0], tShield,  0, 0, Z);
      CreateArb8(magnetName + str7, medium, dZ, cornersCRBA, color[3], fields[0], tShield,  0, 0, Z);
      CreateArb8(magnetName + str8, medium, dZ, cornersTL, color[0], fields[2], tShield,  0, 0, Z);
      CreateArb8(magnetName + str9, medium, dZ, cornersTR, color[2], fields[3], tShield,  0, 0, Z);
      CreateArb8(magnetName + str10, medium, dZ, cornersBL, color[2], fields[3], tShield,  0, 0, Z);
      CreateArb8(magnetName + str11, medium, dZ, cornersBR, color[0], fields[2], tShield,  0, 0, Z);
      break;
    }
  }

void ShipMuonShield::Initialize (TString (&magnetName)[9],FieldDirection (&fieldDirection)[9],
				    Double_t (&dXIn)[9], Double_t (&dYIn)[9], Double_t (&dXOut)[9], Double_t (&dYOut)[9], Double_t (&dZ)[9],
				  Double_t (&midGapIn)[9],Double_t (&midGapOut)[9],
				  Double_t (&HmainSideMagIn)[9], Double_t (&HmainSideMagOut)[9],
				  Double_t (&gapIn)[9],Double_t (&gapOut)[9], Double_t (&Z)[9])
{
  Double_t zgap = (fDesign > 6) ? 10 : 0;  // fixed distance between magnets in Z-axis
  Double_t dYEnd = fY;
  if(fDesign==7){
      
  magnetName[0] = "MagnAbsorb1";	fieldDirection[0] = FieldDirection::up;
  dXIn[0]  = 0.4*m;			dYIn[0]	= 1.5*m;
  dXOut[0] = 0.40*m;			dYOut[0]= 1.5*m;
  midGapIn[0] = 0; 			midGapOut[0] = 0;
  HmainSideMagIn[0] = dYIn[0]/2;  	HmainSideMagOut[0] = dYOut[0]/2;
  gapIn[0] = 0.02*m;			gapOut[0] = 0.02*m;
  dZ[0] = dZ1-zgap/2;			Z[0] = zEndOfAbsorb + dZ[0]+zgap;
  
  magnetName[1] = "MagnAbsorb2";	fieldDirection[1] = FieldDirection::up;
  dXIn[1]  = 0.8*m;			dYIn[1]	= 1.5*m;
  dXOut[1] = 0.8*m;			dYOut[1]= 1.5*m;
  midGapIn[1] = 0; 			midGapOut[1] = 0;
  HmainSideMagIn[1] = dYIn[1]/2;  	HmainSideMagOut[1] = dYOut[1]/2;
  gapIn[1] = 0.02*m;				gapOut[1] = 0.02*m;
  dZ[1] = dZ2-zgap/2;			Z[1] = Z[0] + dZ[0] + dZ[1]+zgap;
    
  magnetName[2] = "Magn1";		fieldDirection[2] = FieldDirection::up;
  dXIn[2]  = 0.87*m;			dYIn[2]	= 0.35*m;
  dXOut[2] = 0.65*m;			dYOut[2]= 1.21*m;
  midGapIn[2] = 0; 			midGapOut[2] = 0;
  HmainSideMagIn[2] = dYIn[2]/2;  	HmainSideMagOut[2] = dYOut[2]/2;
  gapIn[2] = 0.11*m;				gapOut[2] = 0.02*m;
  dZ[2] = dZ3-zgap/2;			Z[2] = Z[1] + dZ[1] + dZ[2]+zgap;

  magnetName[3] = "Magn2";		fieldDirection[3] = FieldDirection::up;
  dXIn[3]  = 0.65*m;			dYIn[3]	= 1.21*m;
  dXOut[3] = 0.43*m;			dYOut[3]= 2.07*m;
  midGapIn[3] = 0; 			midGapOut[3] = 0;
  HmainSideMagIn[3] = dYIn[3]/2;  	HmainSideMagOut[3] = dYOut[3]/2;
  gapIn[3] = 0.11*m;				gapOut[3] = 0.02*m;
  dZ[3] = dZ4-zgap/2;			Z[3] = Z[2] + dZ[2] + dZ[3]+zgap;

  magnetName[4] = "Magn3";		fieldDirection[4] = FieldDirection::up;
  dXIn[4]  = 0.06*m;			dYIn[4]	= 0.32*m;
  dXOut[4] = 0.33*m;			dYOut[4]= 0.13*m;
  midGapIn[4] = 0; 			midGapOut[4] = 0;
  HmainSideMagIn[4] = dYIn[4]/2;  	HmainSideMagOut[4] = dYOut[4]/2;
  gapIn[4] = 0.7*m;			gapOut[4] = 0.11*m;
  dZ[4] = dZ5-zgap/2;			Z[4] = Z[3] + dZ[3] + dZ[4]+zgap;
  
  magnetName[5] = "Magn4";		fieldDirection[5] = FieldDirection::down;
  dXIn[5]  = 0.05*m;			dYIn[5]	= 1.12*m;
  dXOut[5] =0.16*m;			dYOut[5]= 0.05*m;
  midGapIn[5] = 0; 			midGapOut[5] = 0;
  HmainSideMagIn[5] = dYIn[5]/2;  	HmainSideMagOut[5] = dYOut[5]/2;
  gapIn[5] = 0.04*m;			gapOut[5] = 0.02*m;
  dZ[5] = dZ6-zgap/2;			Z[5] = Z[4] + dZ[4] + dZ[5]+zgap;
  
  magnetName[6] = "Magn5";		fieldDirection[6] = FieldDirection::down;
  dXIn[6]  = 0.15*m;			dYIn[6]	= 2.35*m;
  dXOut[6] = 0.34*m;			dYOut[6]= 0.32*m;
  midGapIn[6] = 0; 		        midGapOut[6] = 0;
  HmainSideMagIn[6] = dYIn[6]/2;  	HmainSideMagOut[6] = dYOut[6]/2;
  gapIn[6] = 0.05*m;			gapOut[6] = 0.08*m;
  dZ[6] = dZ7-zgap/2;			Z[6] = Z[5] + dZ[5] + dZ[6]+zgap;
  
  Double_t clip_width = 0.1*m; // clip field width by this width
  magnetName[7] = "Magn6";		fieldDirection[7] = FieldDirection::down;
  dXIn[7]  = 0.31*m;			dYIn[7]	= 1.86*m;
  dXOut[7] = 0.9*m - clip_width;	dYOut[7]= 3.1*m;
  midGapIn[7] = 0; 		        midGapOut[7] = 0;
  Double_t clip_len =
       (dZ8-zgap/2) * (1 - (dXOut[7] - dXIn[7]) / (dXOut[7] + clip_width - dXIn[7]));
  HmainSideMagIn[7] = dYIn[7]/2;  	HmainSideMagOut[7] = dYOut[7]/2;
  gapIn[7] = 0.02*m;			gapOut[7] = 0.55*m;
  dZ[7] = dZ8 - clip_len - zgap / 2;	Z[7] = Z[6] + dZ[6] + dZ[7] + zgap;

  magnetName[8] = "Magn7";		fieldDirection[8] = FieldDirection::down;
  dXIn[8]  = dXOut[7];			dYIn[8]	= dYOut[7];
  dXOut[8] = dXOut[7];			dYOut[8]= dYOut[7];
  midGapIn[8] = 0; 		        midGapOut[8] = 0;
  HmainSideMagIn[8] = dYIn[8]/2;  	HmainSideMagOut[8] = dYOut[8]/2;
  gapIn[8] = 0.55*m;			gapOut[8] = 0.55*m;
  dZ[8] = clip_len;			Z[8] = Z[7] + dZ[7] + dZ[8];
      
  } else {
  magnetName[0] = "1";			fieldDirection[0] = FieldDirection::up;
  dXIn[0]  = 0.7*m;			dYIn[0]	= 1.*m; 
  dXOut[0] = 0.7*m;			dYOut[0]= 0.8158*m;
  midGapIn[0] = 0; 			midGapOut[0] = 0;
  HmainSideMagIn[0] = dYIn[0];  	HmainSideMagOut[0] = dYOut[0];
  gapIn[0] = 20;			gapOut[0] = 20;
  dZ[0] = dZ1-zgap;			Z[0] = zEndOfAbsorb + dZ[0]+zgap;
    
  magnetName[1] = "2";			fieldDirection[1] = FieldDirection::up;
  dXIn[1]  = 0.36*m;			dYIn[1]	= 0.8158*m;
  dXOut[1] = 0.19*m;			dYOut[1]= 0.499*m;
  midGapIn[1] = 0; 			midGapOut[1] = 0;
  HmainSideMagIn[1] = dYIn[1]/2;  	HmainSideMagOut[1] = dYOut[1]/2;
  gapIn[1] = 88;			gapOut[1] = 122;
  dZ[1] = dZ2-zgap/2;			Z[1] = Z[0] + dZ[0] + dZ[1]+zgap;
  
  magnetName[2] = "3";			fieldDirection[2] = FieldDirection::down;
  dXIn[2]  = 0.075*m;			dYIn[2]	= 0.499*m;
  dXOut[2] = 0.25*m;			dYOut[2]= 1.10162*m;
  midGapIn[2] = 0; 			midGapOut[2] = 0;
  HmainSideMagIn[2] = dYIn[2]/2;  	HmainSideMagOut[2] = dYOut[2]/2;
  gapIn[2] = 0;				gapOut[2] = 0;
  dZ[2] = dZ3-zgap/2;			Z[2] = Z[1] + dZ[1] + dZ[2]+zgap;
    
  magnetName[3] = "4";			fieldDirection[3] = FieldDirection::down;
  dXIn[3]  = 0.25*m;			dYIn[3]	= 1.10262*m;
  dXOut[3] = 0.3*m;			dYOut[3]= 1.82697*m;
  midGapIn[3] = 0; 			midGapOut[3] = 0;
  HmainSideMagIn[3] = dXIn[3];  	HmainSideMagOut[3] = dXOut[3];
  gapIn[3] = 0;				gapOut[3] = 25;
  dZ[3] = dZ4-zgap/2;			Z[3] = Z[2] + dZ[2] + dZ[3]+zgap;

  magnetName[4] = "5";			fieldDirection[4] = FieldDirection::down;
  dXIn[4]  = 0.3*m;			dYIn[4]	= 1.82697*m;
  dXOut[4] = 0.4*m;			dYOut[4]= 2.55131*m;
  midGapIn[4] = 5; 			midGapOut[4] = 25;
  HmainSideMagIn[4] = dXIn[4];  	HmainSideMagOut[4] = dXOut[4];
  gapIn[4] = 20;			gapOut[4] = 20;
  dZ[4] = dZ6-zgap/2;			Z[4] = Z[3] + dZ[3] + dZ[4]+zgap;
  
  magnetName[5] = "6";			fieldDirection[5] = FieldDirection::down;
  dXIn[5]  = 0.4*m;			dYIn[5]	= 2.55131*m;
  dXOut[5] =0.4*m;			dYOut[5]= 3.27566*m;
  midGapIn[5] = 25; 			midGapOut[5] = 65;
  HmainSideMagIn[5] = dXIn[5];  	HmainSideMagOut[5] = dXOut[5];
  gapIn[5] = 20;			gapOut[5] = 20;
  dZ[5] = dZ7-zgap/2;			Z[5] = Z[4] + dZ[4] + dZ[5]+zgap;
  
  magnetName[6] = "7";			fieldDirection[6] = FieldDirection::down;
  dXIn[6]  = 0.4*m;			dYIn[6]	= 3.27566*m;
  dXOut[6] = 0.75*m;			dYOut[6]= 4*m;
  midGapIn[6] = 65; 		        midGapOut[6] = 75;
  HmainSideMagIn[6] = dXIn[6];  	HmainSideMagOut[6] = dXOut[6];
  gapIn[6] = 20;			gapOut[6] = 20;
  dZ[6] = dZ8-zgap/2;			Z[6] = Z[5] + dZ[5] + dZ[6]+zgap;
  }
}
void ShipMuonShield::ConstructGeometry()
{
    TGeoVolume *top=gGeoManager->GetTopVolume();
    TGeoVolume *tShield = new TGeoVolumeAssembly("MuonShieldArea");
    InitMedium("tungsten");
    TGeoMedium *tungsten =gGeoManager->GetMedium("tungsten");
    InitMedium("steel");
    TGeoMedium *steel =gGeoManager->GetMedium("steel");
    InitMedium("iron");
    TGeoMedium *iron  =gGeoManager->GetMedium("iron");
    InitMedium("lead");
    TGeoMedium *lead  =gGeoManager->GetMedium("lead");
    InitMedium("Concrete");
    TGeoMedium *concrete  =gGeoManager->GetMedium("Concrete");
    
    if (fDesign==4||fDesign==5||fDesign==6||fDesign==7){
      Double_t ironField = fField*tesla;
      std::cout << "fField  " << fField << std::endl;
      TGeoUniformMagField *magFieldIron = new TGeoUniformMagField(0.,ironField,0.);
      TGeoUniformMagField *RetField     = new TGeoUniformMagField(0.,-ironField,0.);
      TGeoUniformMagField *ConRField    = new TGeoUniformMagField(-ironField,0.,0.);
      TGeoUniformMagField *ConLField    = new TGeoUniformMagField(ironField,0.,0.);
      TGeoUniformMagField *fields[4] = {magFieldIron,RetField,ConRField,ConLField};
      if(fDesign==7){
            TGeoUniformMagField *fieldsTarget[4] = {new TGeoUniformMagField(0.,0.,0.),new TGeoUniformMagField(0.,0.,0.),new TGeoUniformMagField(0.,0.,0.),new TGeoUniformMagField(0.,0.,0.)};
      }
      Int_t nMagnets = (fDesign == 7) ? 9 : 8;

      // need to use literal 8 here as initialisation function's signature requires it.
      // TODO use nMagnets, std::vector and TString!
      const static int nMag = 9;
      TString magnetName[nMag];
      FieldDirection fieldDirection[nMag];
      Double_t dXIn[nMag], dYIn[nMag], dXOut[nMag], dYOut[nMag], dZf[nMag], midGapIn[nMag],
	  midGapOut[nMag], HmainSideMagIn[nMag], HmainSideMagOut[nMag], gapIn[nMag],
	  gapOut[nMag], Z[nMag];
      Initialize (magnetName,fieldDirection,dXIn,dYIn,dXOut,dYOut,dZf,midGapIn,midGapOut,HmainSideMagIn,HmainSideMagOut,gapIn,gapOut,Z);
      
      if (fDesign==6){
	Double_t dA = 3*m;
	CreateMagnet("AbsorberStop-1",iron,tShield,fields,FieldDirection::up,
		  dA/6.,dA/6.,dA/6.,dA/6.,dZ0/3.,0,0,dA/12.,dA/12.,0,0,zEndOfAbsorb - 5.*dZ0/3.,0);
	CreateMagnet("AbsorberStop-2",iron,tShield,fields,FieldDirection::up,
		  dA/2.,dA/2.,dA/2.,dA/2.,dZ0*2./3.,0,0,dA/4.,dA/4.,0,0,zEndOfAbsorb - 2.*dZ0/3.,0);
        TGeoBBox* fullAbsorber = new TGeoBBox("fullAbsorber", dA, dA, dZ0/3.);
        TGeoBBox* cutOut = new TGeoBBox("cutout", dA/3.+20*cm, dA/3.+20*cm, dZ0/3.+0.1*mm); //no idea why to add 20cm
        TGeoSubtraction *subtraction = new TGeoSubtraction("fullAbsorber","cutout");
        TGeoCompositeShape *Tc = new TGeoCompositeShape("passiveAbsorberStopSubtr", subtraction);
        TGeoVolume* passivAbsorber = new TGeoVolume("passiveAbsorberStop-1",Tc, iron);
        tShield->AddNode(passivAbsorber, 1, new TGeoTranslation(0,0,zEndOfAbsorb - 5.*dZ0/3.));
      }else if(fDesign==7){
      for(Int_t nM=0;nM<2;nM++)
      {
	 CreateMagnet(magnetName[nM],iron,tShield,fields,fieldDirection[nM],
		   dXIn[nM],dYIn[nM],dXOut[nM],dYOut[nM],dZf[nM],
		   midGapIn[nM],midGapOut[nM],HmainSideMagIn[nM],HmainSideMagOut[nM],
		   gapIn[nM],gapOut[nM],Z[nM],1);
      }

      TGeoTranslation *mag1 = new TGeoTranslation("mag1", 0, 0, -dZ2);
      TGeoTranslation *mag2 = new TGeoTranslation("mag2", 0, 0, +dZ1);

      mag1->RegisterYourself();
      mag2->RegisterYourself();

      Double_t zgap = 10;
      Double_t absorber_offset = zgap;
      Double_t absorber_half_length = (dZf[0] + dZf[1]) + zgap / 2.;
      TGeoTube *abs = new TGeoTube("absorber", 0, 400, absorber_half_length);
      const std::vector<TString> absorber_magnets = {"MagnAbsorb1",
						     "MagnAbsorb2"};
      const std::vector<TString> magnet_components = {
	  "_MiddleMagL", "_MiddleMagR",  "_MagRetL",    "_MagRetR",
	  "_MagCLB",     "_MagCLT",      "_MagCRT",     "_MagCRB",
	  "_MagTopLeft", "_MagTopRight", "_MagBotLeft", "_MagBotRight",
      };
      TString absorber_magnet_components;
      for (auto &&magnet_component : magnet_components) {
	// format: "-<magnetName>_<magnet_component>:<translation>"
	absorber_magnet_components +=
	    ("-" + absorber_magnets[0] + magnet_component + ":" +
	     mag1->GetName());
	absorber_magnet_components +=
	    ("-" + absorber_magnets[1] + magnet_component + ":" +
	     mag2->GetName());
      }
      TGeoCompositeShape *absorberShape = new TGeoCompositeShape(
	  "Absorber", "absorber" + absorber_magnet_components); // cutting out
								// magnet parts
								// from absorber
      TGeoVolume *absorber = new TGeoVolume("AbsorberVol", absorberShape, iron);
      absorber->SetLineColor(42); // brown / light red
      tShield->AddNode(absorber, 1, new TGeoTranslation(0, 0, zEndOfAbsorb + absorber_half_length + absorber_offset));

      for (Int_t nM = 2; nM <= (nMagnets - 1); nM++) {
	CreateMagnet(magnetName[nM], iron, tShield, fields, fieldDirection[nM],
		     dXIn[nM], dYIn[nM], dXOut[nM], dYOut[nM], dZf[nM],
		     midGapIn[nM], midGapOut[nM], HmainSideMagIn[nM],
		     HmainSideMagOut[nM], gapIn[nM], gapOut[nM], Z[nM], nM==8);

	if (nM==8 || !fSupport) continue;
	// TODO split out into function/method?
	Double_t dymax = std::max(dYIn[nM] + dXIn[nM], dYOut[nM] + dXOut[nM]);
	Double_t dymin = std::min(dYIn[nM] + dXIn[nM], dYOut[nM] + dXOut[nM]);
	Double_t slope =
	    (dYIn[nM] + dXIn[nM] - dYOut[nM] - dXOut[nM]) / (2 * dZf[nM]);
	Double_t w1 = 2 * dXIn[nM] + std::max(20., gapIn[nM]);
	Double_t w2 = 2 * dXOut[nM] + std::max(20., gapOut[nM]);
	Double_t anti_overlap = 0.1;
	Double_t h1 = 0.5 * (dYIn[nM] + dXIn[nM] + anti_overlap - fFloor);
	Double_t h2 = 0.5 * (dYOut[nM] + dXOut[nM] + anti_overlap - fFloor);
	std::vector<Double_t> verticesIn = {
	    -w1, -h1,
	    +w1, -h1,
	    +w1, +h1,
	    -w1, +h1,
	    -w1, -h1 + slope * m,
	    +w1, -h1 + slope * m,
	    +w1, +h1,
	    -w1, +h1,
	};
	std::vector<Double_t> verticesOut = {
	    -w2, -h2 - slope * m,
	    +w2, -h2 - slope * m,
	    +w2, +h2,
	    -w2, +h2,
	    -w2, -h2,
	    +w2, -h2,
	    +w2, +h2,
	    -w2, +h2,
	};
	TGeoVolume *pillar1 =
	    gGeoManager->MakeArb8(TString::Format("pillar_%d", 2 * nM - 1),
				  steel, 0.5 * m, verticesIn.data());
	TGeoVolume *pillar2 =
	    gGeoManager->MakeArb8(TString::Format("pillar_%d", 2 * nM), steel,
				  0.5 * m, verticesOut.data());
	pillar1->SetLineColor(kGreen-5);
	pillar2->SetLineColor(kGreen-5);
	tShield->AddNode(pillar1, 1, new TGeoTranslation(
				     0, -0.5 * (dYIn[nM] + dXIn[nM] + fFloor),
				     Z[nM] - dZf[nM] + 0.5 * m));
	tShield->AddNode(pillar2, 1, new TGeoTranslation(
				     0, -0.5 * (dYOut[nM] + dXOut[nM] + fFloor),
				     Z[nM] + dZf[nM] - 0.5 * m));
      }
          
      } else {
	CreateTube("AbsorberAdd", iron, 15, 400, dZ0, 43, tShield, 0, 0, zEndOfAbsorb - dZ0);
	CreateTube("AbsorberAddCore", iron, 0, 15, dZ0, 38, tShield, 0, 0, zEndOfAbsorb - dZ0);

	for (Int_t nM = 0; nM < (nMagnets - 1); nM++) {
	  CreateMagnet(magnetName[nM],iron,tShield,fields,fieldDirection[nM],
		   dXIn[nM],dYIn[nM],dXOut[nM],dYOut[nM],dZf[nM],
		   midGapIn[nM],midGapOut[nM],HmainSideMagIn[nM],HmainSideMagOut[nM],
		   gapIn[nM],gapOut[nM],Z[nM],0);
	}
      }
      Double_t dX1 = dXIn[0];
      Double_t dY = dYIn[0];

      TGeoShapeAssembly* asmbShield = dynamic_cast<TGeoShapeAssembly*>(tShield->GetShape());
      Double_t totLength = asmbShield->GetDZ();
      top->AddNode(tShield, 1, new TGeoTranslation(0, 0, totLength));

// Concrete around first magnets. i.e. Tunnel
      Double_t dZ = dZ1 + dZ2;
      Double_t dYT = dY+dX1;
      Double_t ZT  = zEndOfAbsorb + dZ;
      TGeoBBox *box1    = new TGeoBBox("box1", 10*m,10*m,dZ);
      TGeoBBox *box2    = new TGeoBBox("box2", 15*m,15*m,dZ);
      TGeoCompositeShape *compRockS = new TGeoCompositeShape("compRockS", "box2-box1");
      TGeoVolume *rockS   = new TGeoVolume("rockS", compRockS, concrete);
      rockS->SetLineColor(11);  // grey
      rockS->SetTransparency(50);
      top->AddNode(rockS, 1, new TGeoTranslation(0, 0, ZT ));
// Concrete around decay tunnel
      Double_t dZD =  100*m + fMuonShieldLength;
      TGeoBBox *box3    = new TGeoBBox("box3", 15*m, 15*m,dZD/2.);
      TGeoBBox *box4    = new TGeoBBox("box4", 10*m, 10*m,dZD/2.);

      if (fDesign == 7 && fFloor > 0) {
	// Only add floor for new shield
	TGeoBBox *box5 = new TGeoBBox("shield_floor", 10 * m, fFloor / 2.,
				      fMuonShieldLength / 2.);
	TGeoVolume *floor = new TGeoVolume("floorM", box5, concrete);
	floor->SetLineColor(11); // grey
	top->AddNode(floor, 1, new TGeoTranslation(0, -10 * m + fFloor / 2.,
						   zEndOfAbsorb +
						       fMuonShieldLength / 2.));
      }
      TGeoCompositeShape *compRockD =
	  new TGeoCompositeShape("compRockD", "(box3-box4)");
      TGeoVolume *rockD   = new TGeoVolume("rockD", compRockD, concrete);
      rockD->SetLineColor(11);  // grey
      rockD->SetTransparency(50);
      top->AddNode(rockD, 1, new TGeoTranslation(0, 0, zEndOfAbsorb + 2*dZ + dZD/2.));
//
    } else {
     Fatal("ShipMuonShield","Design %i does not match implemented designs",fDesign);
    }
}
ClassImp(ShipMuonShield)
