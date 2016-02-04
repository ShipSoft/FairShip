#include "ShipMuonShield.h"

#include "TGeoManager.h"
#include "FairRun.h"                    // for FairRun
#include "FairRuntimeDb.h"              // for FairRuntimeDb
#include "Riosfwd.h"                    // for ostream
#include "TList.h"                      // for TListIter, TList (ptr only)
#include "TObjArray.h"                  // for TObjArray
#include "TString.h"                    // for TString
#include "TGeoBBox.h"
#include "TGeoTrd1.h"
#include "TGeoCompositeShape.h"
#include "TGeoTube.h"
#include "TGeoMaterial.h"
#include "FairGeoInterface.h"
#include "FairGeoMedia.h"
#include "FairGeoBuilder.h"
#include <stddef.h>                     // for NULL
#include <iostream>                     // for operator<<, basic_ostream, etc
#include <string>

using std::cout;
using std::endl;

Double_t cm  = 1;       // cm
Double_t m   = 100*cm;  //  m
Double_t mm  = 0.1*cm;  //  mm
Double_t kilogauss = 1.;
Double_t tesla     = 10*kilogauss;

ShipMuonShield::~ShipMuonShield()
{
}
ShipMuonShield::ShipMuonShield()
  : FairModule("ShipMuonShield", "")
{
}

ShipMuonShield::ShipMuonShield(const char* name, const Int_t Design, const char* Title, 
                               Double_t Z, Double_t L0, Double_t L1, Double_t L2, Double_t L3, Double_t L4, Double_t L5, Double_t L6,
                               Double_t L7, Double_t L8, Double_t gap, Double_t LE, Double_t y, Double_t fl)
  : FairModule(name ,Title)
{
 fDesign = Design;
 fField  = fl;
 if (fDesign==1){
    // passive design with tungsten and lead
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
 zEndOfAbsorb = Z + dZ0 - fMuonShieldLength/2.;
 if (fDesign==6){zEndOfAbsorb = Z - fMuonShieldLength/2.;}
 fY = y;
}


// -----   Private method InitMedium 
Int_t ShipMuonShield::InitMedium(const char* name) 
{
   static FairGeoLoader *geoLoad=FairGeoLoader::Instance();
   static FairGeoInterface *geoFace=geoLoad->getGeoInterface();
   static FairGeoMedia *media=geoFace->getMedia();
   static FairGeoBuilder *geoBuild=geoLoad->getGeoBuilder();

   FairGeoMedium *ShipMedium=media->getMedium(name);

   if (!ShipMedium)
   {
     Fatal("InitMedium","Material %s not defined in media file.", name);
     return -1111;
   }
   TGeoMedium* medium=gGeoManager->GetMedium(name);
   if (medium!=NULL)
     return ShipMedium->getMediumIndex();
   return geoBuild->createMedium(ShipMedium);
}

void ShipMuonShield::CreateTube(const char* tubeName, TGeoMedium* medium, Double_t dX,Double_t dY,Double_t dZ,Int_t color,TGeoVolume *tShield,Int_t numberOfItems, Double_t x_translation,Double_t y_translation,
					Double_t z_translation)
{
  TGeoVolume* absorber = gGeoManager->MakeTube(tubeName, medium, dX, dY,dZ);
  absorber->SetLineColor(color);  
  tShield->AddNode(absorber, numberOfItems, new TGeoTranslation(x_translation, y_translation, z_translation ));
}

void ShipMuonShield::CreateBox(const char* boxName, TGeoMedium* medium, Double_t dX,Double_t dY,Double_t dZ,
					Int_t color,TGeoUniformMagField *magField,TGeoVolume *top,Int_t numberOfItems, Double_t x_translation,Double_t y_translation,
					Double_t z_translation)
{
  TGeoVolume* magF = gGeoManager->MakeBox(boxName, medium, dX, dY,dZ);
  magF->SetLineColor(color);  
  magF->SetField(magField);
  top->AddNode(magF, numberOfItems, new TGeoTranslation(x_translation, y_translation, z_translation ));
}

void ShipMuonShield::CreateArb8(const char* arbName, TGeoMedium* medium,Double_t dZ,Double_t corners[16],Int_t color,
				     TGeoUniformMagField *magField,TGeoVolume *tShield,Int_t numberOfItems,Double_t x_translation,Double_t y_translation,
					Double_t z_translation)
{
  TGeoVolume* magF = gGeoManager->MakeArb8(arbName, medium, dZ, corners);
  magF->SetLineColor(color);
  magF->SetField(magField);
  tShield->AddNode(magF, 1, new TGeoTranslation(x_translation, y_translation, z_translation ));
}

void ShipMuonShield::CreateArb8(const char* arbName, TGeoMedium* medium,Double_t dZ,std::vector<Double_t> corners,Int_t color,
				     TGeoUniformMagField *magField,TGeoVolume *tShield,Int_t numberOfItems,Double_t x_translation,Double_t y_translation,
					Double_t z_translation)
{
  Double_t* corner=&corners[0];
  TGeoVolume* magF = gGeoManager->MakeArb8(arbName, medium, dZ, corner);
  magF->SetLineColor(color);
  magF->SetField(magField);
  tShield->AddNode(magF, 1, new TGeoTranslation(x_translation, y_translation, z_translation ));
}

void ShipMuonShield::Initialize (Double_t& dX1,std::vector<std::vector<Double_t> >& corners,Double_t& Z1, Double_t& X2,Double_t& dXH1,Double_t& Z2,
		 Double_t& Z3,Double_t& Z4,Double_t& Z6,Double_t& Z7,Double_t& Z8,Double_t& ZGmid,Double_t& dY)
{	
     std::vector<Double_t> cornersA1,cornersAR,cornersAT,cornersAB,corners1,corners2,corners3,corners4,corners5,corners6,corners7,cornersC,cornersCR,cornersCL,cornersCLT,
			  cornersCLB,cornersCRT,cornersCRB,corners8,corners9,corners10,corners11,cornersC4,cornersC4L,cornersC4LB,cornersC4LT,cornersC4R,cornersC4RB,cornersC4RT,
			  corners12,corners13,corners14,corners15,cornersC6RL,cornersC6RR,cornersC6L,cornersC6R,corners20,corners21,corners22,corners23,cornersC7RL,cornersC7RR,
			  cornersC7L,cornersC7R,corners24,corners25,corners26,corners27,cornersC8RL,cornersC8RR,cornersC8L,cornersC8R,corners28,corners29,corners30,corners31;
   
    Double_t eps = 1.*mm;
    dX1 = 0.7*m; 
    //is calculated according to z.
    Double_t dYStart = 1.*m; //Y at  zEndOfAbsorb
    Double_t dYMiddle = 0.5*m; //middle is where we swap field/return-field in x
    Double_t dYEnd = fY; // 4.*m;
    X2  = 1.25*m;   
    Z1  = zEndOfAbsorb + dZ1; //юзается
    //calculate the ZMiddle and End
    Double_t ZMiddle=zEndOfAbsorb + 2*dZ1 + 2*dZ2;
    Double_t ZEnd=zEndOfAbsorb + 2*dZ1 + 2*dZ2 + 2*dZ3 + 2*dZ4+2*dZ5+2*dZ6+2*dZ7+2*dZ8;
    Double_t dY1 = dYStart;
    Double_t dY2 = (Z1+dZ1-zEndOfAbsorb)*(dYMiddle-dYStart)/(ZMiddle-zEndOfAbsorb)+dY1;
    Double_t cornersA1A[16] = {-dX1,-dY1, -dX1,dY1, dX1,dY1, dX1,-dY1,
                              -dX1,-dY2, -dX1,dY2, dX1,dY2, dX1,-dY2};
    Double_t cornersARA[16] = {-dX1/2.,-dY1, -dX1/2.,dY1, dX1/2.,dY1, dX1/2.,-dY1,
                              -dX1/2.,-dY2, -dX1/2.,dY2, dX1/2.,dY2, dX1/2.,-dY2};
    Double_t dYH1 = dX1/2.; 
    dXH1 = 0.5*(X2+dX1/2.);
    Double_t cornersATA[16] = {-dXH1,dY1, -dXH1,dY1+dYH1, dXH1,dY1+dYH1, dXH1,dY1,
                              -dXH1,dY2, -dXH1,dY2+dYH1, dXH1,dY2+dYH1, dXH1,dY2};
    Double_t cornersABA[16] = {-dXH1,-dY1-dYH1, -dXH1,-dY1, dXH1,-dY1, dXH1,-dY1-dYH1,
                              -dXH1,-dY2-dYH1, -dXH1,-dY2, dXH1,-dY2, dXH1,-dY2-dYH1};
    // 7<z<19 m: (Kept the same names at fDesign==3, i.e. 7t17 :-)
    Double_t dX2 = 0.36*m;
    Double_t dX3 = 0.19*m;
    Z2 = zEndOfAbsorb + 2*dZ1 + dZ2;
    dY1 = dY2-eps;
    dY2 = dYMiddle-eps;
    Double_t corners1A[16] = {-dX2,-dY1, -dX2,dY1, dX2,dY1, dX2,-dY1,
                             -dX3,-dY2, -dX3,dY2, dX3,dY2, dX3,-dY2};
    Double_t corners2A[16] = {1.6*m-dX2,-dY1, 1.6*m-dX2,dY1, 1.6*m,dY1, 1.6*m,-dY1, 
                             1.6*m-dX3,-dY2, 1.6*m-dX3,dY2, 1.6*m,dY2, 1.6*m,-dY2};
    Double_t corners3A[16] = {-1.6*m,-dY1, -1.6*m,dY1, -1.6*m+dX2,dY1, -1.6*m+dX2,-dY1, 
                             -1.6*m,-dY2, -1.6*m,dY2, -1.6*m+dX3,dY2, -1.6*m+dX3,-dY2};
    dY1 = dY1+eps;
    dY2 = dY2+eps;
//Top/Bot return magnets for 7-17 m
//corners "first clockwise lower z, them clockwise upper z
    Double_t corners4A[16] = {0.,dY1, 0.,dY1+dX2, 1.6*m,dY1+dX2, 1.6*m,dY1, 
                             0.,dY2, 0.,dY2+dX3, 1.6*m,dY2+dX3, 1.6*m,dY2};
    Double_t corners5A[16] = {-1.6*m,dY1, -1.6*m,dY1+dX2, 0.,dY1+dX2, 0.,dY1, 
                             -1.6*m,dY2, -1.6*m,dY2+dX3, 0.,dY2+dX3, 0.,dY2};
     //Bot return magnets for 7-17 m
    Double_t corners6A[16] = {0.,-dY1-dX2, 0.,-dY1, 1.6*m,-dY1, 1.6*m,-dY1-dX2, 
                             0.,-dY2-dX3, 0.,-dY2, 1.6*m,-dY2, 1.6*m,-dY2-dX3};
    Double_t corners7A[16] = {-1.6*m,-dY1-dX2, -1.6*m,-dY1, 0.,-dY1, 0.,-dY1-dX2, 
                             -1.6*m,-dY2-dX3, -1.6*m,-dY2, 0.,-dY2, 0.,-dY2-dX3};
    // 19<z<24 m: (again kept the "old" name)
    Double_t dX17 =  0.075*m;
    Double_t dX24 =  0.25*m;
    Double_t Clgap=0.2*m;
    Double_t dX17O = dX17+Clgap;
    Double_t dX24O = dX24+Clgap;
    Z3  = zEndOfAbsorb + 2*dZ1 + 2*dZ2 + dZ3;
    dY1=dY2-eps;
    dY2 = 2*dZ3*(dYEnd-dY1)/(ZEnd-Z3+dZ3)+dY1-eps;
    Double_t cornersCA[16] = {-dX17,-dY1, -dX17,dY1, dX17,dY1, dX17,-dY1,
                             -dX24,-dY2, -dX24,dY2, dX24,dY2, dX24,-dY2};
     //right magnet 
    Double_t cornersCRA[16] = {-2*dX17,-dX17, -2*dX17,dX17, -dX17,dX17, -dX17,-dX17,
                              -2*dX24,-dX24, -2*dX24,dX24, -dX24,dX24, -dX24,-dX24};
    //left magnet 
    Double_t cornersCLA[16] = {dX17,-dX17, dX17,dX17, 2*dX17,dX17, 2*dX17,-dX17,
                              dX24,-dX24, dX24,dX24, 2*dX24,dX24, 2*dX24,-dX24};
   //add 4 pieces for the fields.
    //left top field magnet 
    Double_t cornersCLTA[16] = {dX17,dX17, dX17O,dY1, dX17O+dX17,dY1, 2*dX17,dX17,
                               dX24,dX24, dX24O,dY2, dX24O+dX24,dY2, 2*dX24,dX24};
    //left bot field magnet 
    Double_t cornersCLBA[16] = {dX17O,-dY1, dX17,-dX17, 2*dX17,-dX17, dX17+dX17O,-dY1,
                               dX24O,-dY2, dX24,-dX24, 2*dX24,-dX24, dX24+dX24O,-dY2};
    //right top field magnet 
    Double_t cornersCRTA[16] = {-dX17,dX17, -2*dX17,dX17, -dX17O-dX17,dY1, -dX17O,dY1,
                               -dX24,dX24, -2*dX24,dX24, -dX24O-dX24,dY2, -dX24O,dY2};
    //right bot field magnet 
    Double_t cornersCRBA[16] = {-dX17O,-dY1, -dX17O-dX17,-dY1, -2*dX17,-dX17, -dX17,-dX17,
                               -dX24O,-dY2, -dX24O-dX24,-dY2, -2*dX24,-dX24, -dX24,-dX24};
    //Top/Bot return magnets for 17-24 m
    dY1 = dY1+eps;
    dY2 = dY2+eps;
    Double_t corners8A[16] = {eps,dY1, eps,dY1+dX17, dX17O+dX17,dY1+dX17, dX17O+dX17,dY1, 
                             eps,dY2, eps,dY2+dX24, dX24O+dX24,dY2+dX24, dX24O+dX24,dY2}; 
    Double_t corners9A[16] = {-dX17-dX17O,dY1, -dX17-dX17O,dY1+dX17, -eps, dY1+dX17, -eps,dY1,
                             -dX24-dX24O,dY2, -dX24-dX24O,dY2+dX24, -eps, dY2+dX24, -eps,dY2};
  //Bot return magnets 
    Double_t corners10A[16] = {eps,-dY1-dX17, eps,-dY1-eps, dX17O+dX17,-dY1-eps, dX17O+dX17,-dY1-dX17, 
                              eps,-dY2-dX24, eps,-dY2-eps, dX24O+dX24,-dY2-eps, dX24O+dX24,-dY2-dX24};
    Double_t corners11A[16] = {-dX17-dX17O,-dY1-dX17, -dX17-dX17O,-dY1, -eps,-dY1, -eps,-dY1-dX17, 
                              -dX24-dX24O,-dY2-dX24, -dX24-dX24O,-dY2, -eps,-dY2, -eps,-dY2-dX24};
    // 24<z<30. m, gap between field and return field      
    Double_t dX30I = 0.55*m;
    Double_t W30 = 0.3*m;
    Z4 = zEndOfAbsorb + 2*dZ1 + 2*dZ2 + 2*dZ3 + dZ4;
    dY1=dY2;
    dY2 = 2*dZ4*(dYEnd-dY1)/(ZEnd-Z4+dZ4)+dY1;
    Double_t cornersC4A[16] = {-dX24,-dY1, -dX24,dY1, dX24,dY1, dX24,-dY1,
                               -W30,-dY2, -W30,dY2, W30,dY2, W30,-dY2};
       //left magnet, split in three, like for previous magnet
    Double_t cornersC4LA[16] = {dX24,-dX24, dX24,dX24, 2*dX24,dX24, 2*dX24,-dX24,
                               dX30I,-W30, dX30I,W30, dX30I+W30,W30, dX30I+W30,-W30};
    Double_t cornersC4LBA[16] = {dX24,-dX24, 2*dX24,-dX24, 2*dX24+Clgap,-dY1, dX24+Clgap,-dY1,
                                dX30I,-W30, dX30I+W30,-W30, dX30I+W30,-dY2, dX30I,-dY2};
    Double_t cornersC4LTA[16] = {2*dX24,dX24, dX24,dX24, dX24+Clgap,dY1, 2*dX24+Clgap,dY1,
                                dX30I+W30,W30, dX30I,W30, dX30I,dY2, dX30I+W30,dY2};
    //right magnet, also split in 3..
    Double_t cornersC4RA[16] = {-2*dX24,-dX24, -2*dX24,dX24, -dX24,dX24, -dX24,-dX24,
                               -dX30I-W30,-W30, -dX30I-W30,W30, -dX30I,W30, -dX30I,-W30};
    Double_t cornersC4RBA[16] = {-2*dX24-Clgap,-dY1, -2*dX24,-dX24, -dX24,-dX24, -Clgap-dX24,-dY1,
                               -dX30I-W30,-dY2, -dX30I-W30,-W30, -dX30I,-W30, -dX30I,-dY2};
    Double_t cornersC4RTA[16] = {-2*dX24,dX24, -2*dX24-Clgap,dY1, -dX24-Clgap,dY1, -dX24,dX24,
                               -dX30I-W30,W30, -dX30I-W30,dY2, -dX30I,dY2, -dX30I,W30};
    //Top/Bot return magnets for 24-28 m
    Double_t corners12A[16] = {0.,dY1, 0.,dY1+dX24, 2*dX24+Clgap,dY1+dX24, 2*dX24+Clgap,dY1, 
                              0.,dY2, 0.,dY2+W30, W30+dX30I,dY2+W30, W30+dX30I,dY2}; 
    Double_t corners13A[16] = {-2*dX24-Clgap,dY1, -2*dX24-Clgap,dY1+dX24, 0., dY1+dX24, 0.,dY1,
                              -W30-dX30I,dY2,-W30-dX30I,dY2+W30, 0.,dY2+W30, 0.,dY2}; 
 //Bot return magnets 
    Double_t corners14A[16] = {eps,-dY1-dX24, eps,-dY1-eps, 2*dX24+Clgap,-dY1-eps, 2*dX24+Clgap,-dY1-dX24, 
                              eps,-dY2-W30, eps,-dY2-eps, W30+dX30I,-dY2-eps, W30+dX30I,-dY2-W30};
    Double_t corners15A[16] = {-2*dX24-Clgap,-dY1-dX24, -2*dX24-Clgap,-dY1, 0.,-dY1, 0.,-dY1-dX24, 
                              -W30-dX30I,-dY2-W30,  -W30-dX30I,-dY2, 0.,-dY2, 0.,-dY2-W30};
// 30<z<36 m: Note: here also return field splits!
    Double_t dX30O = dX30I+W30;
    Double_t dXr30O = dX30I-dXgap;
    Double_t dXr30I = dXr30O-W30;
    Double_t W36 = 0.4*m;
    Double_t dX36I = 0.85*m;
    Double_t dX36O = dX36I+W36;
    Double_t dXr36O = dX36I-dXgap;
    Double_t dXr36I = dXr36O-W36;

    Z6 = zEndOfAbsorb + 2*dZ1 + 2*dZ2 + 2*dZ3 + 2*dZ4+2*dZ5+dZ6;
    dY1=dY2;
    dY2 = 2*dZ6*(dYEnd-dY1)/(ZEnd-Z6+dZ6)+dY1;
    //return fields
    Double_t cornersC6RLA[16] = {dXr30I,-dY1, dXr30I,dY1, dXr30O,dY1, dXr30O,-dY1,
                                dXr36I,-dY2, dXr36I,dY2, dXr36O,dY2, dXr36O,-dY2};
    Double_t cornersC6RRA[16] = {-dXr30O,-dY1, -dXr30O,dY1, -dXr30I,dY1, -dXr30I,-dY1,
                                -dXr36O,-dY2, -dXr36O,dY2, -dXr36I,dY2, -dXr36I,-dY2};
    //bending fields
    Double_t cornersC6LA[16] = {dX30I,-dY1, dX30I,dY1, dX30O,dY1, dX30O,-dY1,
                               dX36I,-dY2, dX36I,dY2, dX36O,dY2, dX36O,-dY2};
    Double_t cornersC6RA[16] = {-dX30O,-dY1, -dX30O,dY1, -dX30I,dY1, -dX30I,-dY1,
                               -dX36O,-dY2, -dX36O,dY2, -dX36I,dY2, -dX36I,-dY2};
 //Top/Bot return magnets for 30-36 m, note inner return magnet splits too :-)
    Double_t corners20A[16] = {dXr30I,dY1, dXr30I,dY1+W30, dX30O,dY1+W30, dX30O,dY1, 
                              dXr36I,dY2, dXr36I,dY2+W36, dX36O,dY2+W36, dX36O,dY2}; 
    Double_t corners21A[16] = {-dX30O,dY1, -dX30O,dY1+W30, -dXr30I, dY1+W30, -dXr30I,dY1,
                              -dX36O,dY2, -dX36O,dY2+W36, -dXr36I, dY2+W36, -dXr36I,dY2};
      //Bot return magnets 
    Double_t corners22A[16] = {dXr30I+eps,-dY1-W30, dXr30I+eps,-dY1-eps, dX30O,-dY1-eps, dX30O,-dY1-W30, 
                              dXr36I+eps,-dY2-W36, dXr36I+eps,-dY2-eps, dX36O,-dY2-eps, dX36O,-dY2-W36};
    Double_t corners23A[16] = {-dX30O,-dY1-W30, -dX30O,-dY1, -dXr30I,-dY1, -dXr30I,-dY1-W30, 
                              -dX36O,-dY2-W36, -dX36O,-dY2, -dXr36I,-dY2, -dXr36I,-dY2-W36};  
// 36<z<42 m: Note: here also return field splits!
    Double_t W42 = 0.4*m;
    Double_t dX42I = 1.25*m;
    Double_t dX42O = dX42I+W42;
    Double_t dXr42O = dX42I-dXgap;
    Double_t dXr42I = dXr42O-W42;    
    Z7 = zEndOfAbsorb + 2*dZ1 + 2*dZ2 + 2*dZ3 + 2*dZ4+2*dZ5+2*dZ6+dZ7;
    dY1=dY2;
    dY2 = 2*dZ7*(dYEnd-dY1)/(ZEnd-Z7+dZ7)+dY1;

    //return fields
    Double_t cornersC7RLA[16] = {dXr36I,-dY1, dXr36I,dY1, dXr36O,dY1, dXr36O,-dY1,
                                dXr42I,-dY2, dXr42I,dY2, dXr42O,dY2, dXr42O,-dY2};
    Double_t cornersC7RRA[16] = {-dXr36O,-dY1, -dXr36O,dY1, -dXr36I,dY1, -dXr36I,-dY1,
                                -dXr42O,-dY2, -dXr42O,dY2, -dXr42I,dY2, -dXr42I,-dY2}; 
    //bending fields
    Double_t cornersC7LA[16] = {dX36I,-dY1, dX36I,dY1, dX36O,dY1, dX36O,-dY1,
                               dX42I,-dY2, dX42I,dY2, dX42O,dY2, dX42O,-dY2};
    Double_t cornersC7RA[16] = {-dX36O,-dY1, -dX36O,dY1, -dX36I,dY1, -dX36I,-dY1,
                               -dX42O,-dY2, -dX42O,dY2, -dX42I,dY2, -dX42I,-dY2};
//Top/Bot return magnets for 36-42 m, note inner return magnet splits too :-)
    Double_t corners24A[16] = {dXr36I,dY1, dXr36I,dY1+W36, dX36O,dY1+W36, dX36O,dY1, 
                             dXr42I,dY2, dXr42I,dY2+W42, dX42O,dY2+W42, dX42O,dY2}; 
    Double_t corners25A[16] = {-dX36O,dY1, -dX36O,dY1+W36, -dXr36I, dY1+W36, -dXr36I,dY1, 
                              -dX42O,dY2, -dX42O,dY2+W42, -dXr42I, dY2+W42, -dXr42I,dY2};  
 //Bot return magnets 
    Double_t corners26A[16] = {dXr36I,-dY1-W36, dXr36I,-dY1, dX36O,-dY1, dX36O,-dY1-W36, 
                              dXr42I,-dY2-W42, dXr42I,-dY2, dX42O,-dY2, dX42O,-dY2-W42};
    Double_t corners27A[16] = {-dX36O,-dY1-W36, -dX36O,-dY1, -dXr36I,-dY1, -dXr36I,-dY1-W36, 
                              -dX42O,-dY2-W42, -dX42O,-dY2, -dXr42I,-dY2, -dXr42I,-dY2-W42};
// 42<z<48 m: Note: here also return field splits!
    Double_t W48 = 0.75*m;
    Double_t dX48I = 1.7*m;
    Double_t dX48O = dX48I+W48;
    Double_t dXr48O = dX48I-dXgap;
    Double_t dXr48I = dXr48O-W48;
    Z8 = zEndOfAbsorb + 2*dZ1 + 2*dZ2 + 2*dZ3 + 2*dZ4+2*dZ5+2*dZ6+2*dZ7+dZ8;
    
    dY1=dY2;
    dY2 = 2*dZ8*(dYEnd-dY1)/(ZEnd-Z8+dZ8)+dY1;

    //return fields
    Double_t cornersC8RLA[16] = {dXr42I,-dY1, dXr42I,dY1, dXr42O,dY1, dXr42O,-dY1,
                                dXr48I,-dY2, dXr48I,dY2, dXr48O,dY2, dXr48O,-dY2}; 
    Double_t cornersC8RRA[16] = {-dXr42O,-dY1, -dXr42O,dY1, -dXr42I,dY1, -dXr42I,-dY1,
                                -dXr48O,-dY2, -dXr48O,dY2, -dXr48I,dY2, -dXr48I,-dY2};
    //bending fields
    Double_t cornersC8LA[16] = {dX42I,-dY1, dX42I,dY1, dX42O,dY1, dX42O,-dY1,
                               dX48I,-dY2, dX48I,dY2, dX48O,dY2, dX48O,-dY2};
    Double_t cornersC8RA[16] = {-dX42O,-dY1, -dX42O,dY1, -dX42I,dY1, -dX42I,-dY1,
                               -dX48O,-dY2, -dX48O,dY2, -dX48I,dY2, -dX48I,-dY2}; 
    //Top/Bot return magnets for 42-48 m, note inner return magnet splits too :-)
    Double_t corners28A[16] = {dXr42I,dY1, dXr42I,dY1+W42, dX42O,dY1+W42, dX42O,dY1, 
                              dXr48I,dY2, dXr48I,dY2+W48, dX48O,dY2+W48, dX48O,dY2}; 
    Double_t corners29A[16] = {-dX42O,dY1, -dX42O,dY1+W42, -dXr42I, dY1+W42, -dXr42I,dY1,
                              -dX48O,dY2, -dX48O,dY2+W48, -dXr48I, dY2+W48, -dXr48I,dY2};
//Bot return magnets 
    Double_t corners30A[16] = {dXr42I,-dY1-W42, dXr42I,-dY1, dX42O,-dY1, dX42O,-dY1-W42, 
                              dXr48I,-dY2-W48, dXr48I,-dY2, dX48O,-dY2, dX48O,-dY2-W48};
    Double_t corners31A[16] = {-dX42O,-dY1-W42, -dX42O,-dY1, -dXr42I,-dY1, -dXr42I,-dY1-W42, 
                              -dX48O,-dY2-W48, -dX48O,-dY2, -dXr48I,-dY2, -dXr48I,-dY2-W48};
    ZGmid=Z8+dZ8+2.25*m+0.2*m;
    dY=dYStart;
    for(int i=0;i<16;i++){
      cornersA1.push_back(cornersA1A[i]);
      cornersAR.push_back(cornersARA[i]);
      cornersAT.push_back(cornersATA[i]);
      cornersAB.push_back(cornersABA[i]);
      corners1.push_back(corners1A[i]);
      corners2.push_back(corners2A[i]);
      corners3.push_back(corners3A[i]);   
      corners4.push_back(corners4A[i]);    
      corners5.push_back(corners5A[i]);
      corners6.push_back(corners6A[i]);
      corners7.push_back(corners7A[i]);
      cornersC.push_back(cornersCA[i]);
      cornersCR.push_back(cornersCRA[i]);
      cornersCL.push_back(cornersCLA[i]);
      cornersCLT.push_back(cornersCLTA[i]);
      cornersCLB.push_back(cornersCLBA[i]);
      cornersCRT.push_back(cornersCRTA[i]);
      cornersCRB.push_back(cornersCRBA[i]);
      corners8.push_back(corners8A[i]);
      corners9.push_back(corners9A[i]);
      corners10.push_back(corners10A[i]);
      corners11.push_back(corners11A[i]);
      cornersC4.push_back(cornersC4A[i]);
      cornersC4L.push_back(cornersC4LA[i]);
      cornersC4LB.push_back(cornersC4LBA[i]);
      cornersC4LT.push_back(cornersC4LTA[i]);
      cornersC4R.push_back(cornersC4RA[i]);
      cornersC4RB.push_back(cornersC4RBA[i]);
      cornersC4RT.push_back(cornersC4RTA[i]);
      corners12.push_back(corners12A[i]);
      corners13.push_back(corners13A[i]);
      corners14.push_back(corners14A[i]);
      corners15.push_back(corners15A[i]);
      cornersC6RL.push_back(cornersC6RLA[i]);
      cornersC6RR.push_back(cornersC6RRA[i]);
      cornersC6L.push_back(cornersC6LA[i]);
      cornersC6R.push_back(cornersC6RA[i]);
      corners20.push_back(corners20A[i]);
      corners21.push_back(corners21A[i]);
      corners22.push_back(corners22A[i]);
      corners23.push_back(corners23A[i]);
      cornersC7RL.push_back(cornersC7RLA[i]);
      cornersC7RR.push_back(cornersC7RRA[i]);
      cornersC7L.push_back(cornersC7LA[i]);
      cornersC7R.push_back(cornersC7RA[i]);
      corners24.push_back(corners24A[i]);
      corners25.push_back(corners25A[i]);
      corners26.push_back(corners26A[i]);
      corners27.push_back(corners27A[i]);
      cornersC8RL.push_back(cornersC8RLA[i]);
      cornersC8RR.push_back(cornersC8RRA[i]);
      cornersC8L.push_back(cornersC8LA[i]);
      cornersC8R.push_back(cornersC8RA[i]);
      corners28.push_back(corners28A[i]);
      corners29.push_back(corners29A[i]);
      corners30.push_back(corners30A[i]);
      corners31.push_back(corners31A[i]);
    }
    corners.push_back(cornersA1);
    corners.push_back(cornersAR);
    corners.push_back(cornersAT);
    corners.push_back(cornersAB);
    corners.push_back(corners1);
    corners.push_back(corners2);
    corners.push_back(corners3);
    corners.push_back(corners4);
    corners.push_back(corners5);
    corners.push_back(corners6);
    corners.push_back(corners7);
    corners.push_back(cornersC);
    corners.push_back(cornersCR);
    corners.push_back(cornersCL);
    corners.push_back(cornersCLT);
    corners.push_back(cornersCLB);
    corners.push_back(cornersCRT);
    corners.push_back(cornersCRB);
    corners.push_back(corners8);
    corners.push_back(corners9);
    corners.push_back(corners10);
    corners.push_back(corners11);
    corners.push_back(cornersC4);
    corners.push_back(cornersC4L);      
    corners.push_back(cornersC4LB);
    corners.push_back(cornersC4LT);
    corners.push_back(cornersC4R);
    corners.push_back(cornersC4RB);
    corners.push_back(cornersC4RT);
    corners.push_back(corners12);
    corners.push_back(corners13);
    corners.push_back(corners14);
    corners.push_back(corners15);
    corners.push_back(cornersC6RL);
    corners.push_back(cornersC6RR);
    corners.push_back(cornersC6L);
    corners.push_back(cornersC6R);
    corners.push_back(corners20);
    corners.push_back(corners21);
    corners.push_back(corners22);
    corners.push_back(corners23);
    corners.push_back(cornersC7RL);
    corners.push_back(cornersC7RR);
    corners.push_back(cornersC7L);
    corners.push_back(cornersC7R);
    corners.push_back(corners24);
    corners.push_back(corners25);
    corners.push_back(corners26);
    corners.push_back(corners27);
    corners.push_back(cornersC8RL);
    corners.push_back(cornersC8RR);
    corners.push_back(cornersC8L);
    corners.push_back(cornersC8R);
    corners.push_back(corners28);
    corners.push_back(corners29);
    corners.push_back(corners30);
    corners.push_back(corners31);

}

void ShipMuonShield::ConstructGeometry()
{
    TGeoVolume *top=gGeoManager->GetTopVolume();
    TGeoVolume *tShield = new TGeoVolumeAssembly("MuonShieldArea");
    InitMedium("tungsten");
    TGeoMedium *tungsten =gGeoManager->GetMedium("tungsten");
    InitMedium("iron");
    TGeoMedium *iron  =gGeoManager->GetMedium("iron");
    InitMedium("lead");
    TGeoMedium *lead  =gGeoManager->GetMedium("lead");
    InitMedium("Concrete");
    TGeoMedium *concrete  =gGeoManager->GetMedium("Concrete");
    
    if (fDesign==1){
    // passive design with tungsten and lead
     Double_t r1 = 0.12*m; 
     Double_t r2 = 0.50*m; 
     Double_t Lz = 40*m; 
     Double_t Pbr1 = 0.22*m; 
     Double_t Pbr2 = 1*m   * Lz / (40*m); 
     Double_t Pbr3 = 1.5*m * fMuonShieldLength / (60*m); 
     Double_t rW   = 0.*m; 
     TGeoVolume *core = gGeoManager->MakeCone("Core", tungsten, Lz/2., 0.,r1, 0.,r2);
     core->SetLineColor(31);  // silver/green
     Double_t zpos = zEndOfAbsorb + Lz/2.;
     top->AddNode(core, 1, new TGeoTranslation(0, 0, zpos ));
     TGeoVolume *Pbshield1 = gGeoManager->MakeCone("Pbshield1", lead, Lz/2., r1+0.01,Pbr1,r2+0.01,Pbr2);
     Pbshield1->SetLineColor(23);  // silver/grey
     top->AddNode(Pbshield1, 1, new TGeoTranslation(0, 0, zpos ));
     TGeoVolume *Pbshield2 = gGeoManager->MakeCone("Pbshield2", lead, (fMuonShieldLength-Lz)/2., rW,Pbr2,rW,Pbr3);
     Pbshield2->SetLineColor(23);  // silver/grey
     zpos = zEndOfAbsorb  + Lz + (fMuonShieldLength-Lz)/2. ;
     top->AddNode(Pbshield2, 1, new TGeoTranslation(0, 0, zpos));
// Concrete around shielding
     Double_t dZ = fMuonShieldLength;
     TGeoBBox *box1    = new TGeoBBox("box1",  6*m,6*m,dZ/2.);    
     TGeoBBox *box2    = new TGeoBBox("box2", 10*m,10*m,dZ/2.);    
     TGeoCompositeShape *compRockS = new TGeoCompositeShape("compRockS", "box2-box1");
     TGeoVolume *rockS   = new TGeoVolume("rockS", compRockS, concrete);
     rockS->SetLineColor(11);  // grey
     rockS->SetTransparency(50);
     zpos = zEndOfAbsorb  + fMuonShieldLength/2. ;
     top->AddNode(rockS, 1, new TGeoTranslation(0, 0,zpos));
// around decay tunnel
     Double_t dZD =  100*m + 30*m;
     TGeoBBox *box3    = new TGeoBBox("box3", 15*m,12.25*m,dZD/2.);    
     TGeoBBox *box4    = new TGeoBBox("box4", 10*m, 7.25*m,dZD/2.);    
     TGeoCompositeShape *compRockD = new TGeoCompositeShape("compRockD", "box3-box4");
     TGeoVolume *rockD   = new TGeoVolume("rockD", compRockD, concrete);
     rockD->SetLineColor(11);  // grey
     rockD->SetTransparency(50);
     top->AddNode(rockD, 1, new TGeoTranslation(0, 0, zEndOfAbsorb + dZ + dZD/2.));
    
     cout << "passive muon shield postioned at " << (-fMuonShieldLength/2.-2500)/100. << "m"<< endl;
    }
    else if (fDesign==4||fDesign==5||fDesign==6){
// Slightly improved from fDesign==3, longer/thicker MagB first magnets to 
// make sure more muons end up on the right polarity side.
// add here the additional 2m hadron shield, decided 17 october 2014
     Double_t ironField = fField*tesla;
     cout<<"fField  "<<fField<<endl;
     TGeoUniformMagField *magFieldIron = new TGeoUniformMagField(0.,ironField,0.);
     TGeoUniformMagField *RetField     = new TGeoUniformMagField(0.,-ironField,0.);
     TGeoUniformMagField *ConRField    = new TGeoUniformMagField(-ironField,0.,0.);
     TGeoUniformMagField *ConLField    = new TGeoUniformMagField(ironField,0.,0.);
     Double_t eps = 1.*mm;  //create small gaps between some elements to avoid Geant to get stuck.

// fDesign==6 with magnetized hadron absorber
     if (fDesign==6){
      // central block is 1 m high/wide B-up,
      // all return fields top/bot/left/right are 0.5 m wide 
      Double_t dA = 1*m;
      TGeoVolume *AbsorberC = gGeoManager->MakeBox("AbsorberCentre", iron, dA/2., dA/2., dZ0);
      AbsorberC->SetLineColor(43);
      TGeoVolume *AbsorberL = gGeoManager->MakeBox("AbsorberLeft",   iron, dA/4., dA/2., dZ0);
      AbsorberL->SetLineColor(43);
      TGeoVolume *AbsorberR = gGeoManager->MakeBox("AbsorberRight",  iron, dA/4., dA/2., dZ0);
      AbsorberR->SetLineColor(43);
      TGeoVolume *AbsorberTL = gGeoManager->MakeBox("AbsorberTopLeft", iron,     dA/2., dA/4., dZ0);
      AbsorberTL->SetLineColor(43);
      TGeoVolume *AbsorberTR = gGeoManager->MakeBox("AbsorberTopRight", iron,    dA/2., dA/4., dZ0);
      AbsorberTR->SetLineColor(43);
      TGeoVolume *AbsorberBL = gGeoManager->MakeBox("AbsorberBottomLeft", iron,  dA/2., dA/4., dZ0);
      AbsorberBL->SetLineColor(43);
      TGeoVolume *AbsorberBR = gGeoManager->MakeBox("AbsorberBottomRight", iron, dA/2., dA/4., dZ0);
      AbsorberBR->SetLineColor(43);
 
      AbsorberC->SetField(magFieldIron);
      tShield->AddNode(AbsorberC, 1, new TGeoTranslation(0., 0.,zEndOfAbsorb - dZ0));
      AbsorberL->SetField(RetField);
      tShield->AddNode(AbsorberL, 1, new TGeoTranslation(-3*dA/4.,0.,zEndOfAbsorb - dZ0));
      AbsorberR->SetField(RetField);
      tShield->AddNode(AbsorberR, 1, new TGeoTranslation(3*dA/4.,0.,zEndOfAbsorb - dZ0));
      AbsorberTL->SetField(ConRField);
      tShield->AddNode(AbsorberTL, 1, new TGeoTranslation(-dA/2.,3*dA/4.,zEndOfAbsorb - dZ0));
      AbsorberTR->SetField(ConLField);
      tShield->AddNode(AbsorberTR, 1, new TGeoTranslation(dA/2.,3*dA/4.,zEndOfAbsorb - dZ0));
      AbsorberBL->SetField(ConLField);
      tShield->AddNode(AbsorberBL, 1, new TGeoTranslation(-dA/2.,-3*dA/4.,zEndOfAbsorb - dZ0));
      AbsorberBR->SetField(ConRField);
      tShield->AddNode(AbsorberBR, 1, new TGeoTranslation(dA/2.,-3*dA/4.,zEndOfAbsorb - dZ0));

    }else{
     // 2m more Absorber made of iron
     CreateTube("AbsorberAdd", iron, 15, 400, dZ0,43,tShield,1,0, 0, zEndOfAbsorb - dZ0);
     //TGeoVolume *absorberCore = gGeoManager->MakeTube("AbsorberAddCore", tungsten, 0, 15, dZ0);   
     CreateTube("AbsorberAddCore", iron, 0, 15, dZ0,38,tShield,1,0, 0, zEndOfAbsorb - dZ0);
    }
    /*
    #define nCorners 5 */
    std::vector<std::vector<Double_t> > corners;
   /* std::vector<Double_t> cornersA1,cornersAR,cornersAT,cornersAB,corners1,corners2,corners3,corners4,corners5,corners6,corners7,cornersC,cornersCR,cornersCL,cornersCLT,
			  cornersCLB,cornersCRT,cornersCRB,corners8,corners9,corners10,corners11,cornersC4,cornersC4L,cornersC4LB,cornersC4LT,cornersC4R,cornersC4RB,cornersC4RT,
			  corners12,corners13,corners14,corners15,cornersC6RL,cornersC6RR,cornersC6L,cornersC6R,corners20,corners21,corners22,corners23,cornersC7RL,cornersC7RR,
			  cornersC7L,cornersC7R,corners24,corners25,corners26,corners27,cornersC8RL,cornersC8RR,cornersC8L,cornersC8R,corners28,corners29,corners30,corners31;
   */ Double_t dX1,Z1,X2,dXH1,Z2,Z3,Z4,Z6,Z7,Z8,ZGmid,dY;
    
    Initialize (dX1,corners,Z1,X2,dXH1,Z2,Z3,Z4,Z6,Z7,Z8,ZGmid,dY);
    
//       std::string nameOfpart[57] = {"MagA","MagRetA","MagConALLT","MagConARRT","MagConARLB","MagConALRB","MagB","MagBRL",
//       "MagBRR","MagTopLeft7t17","MagTopRight7t17","MagBotLeft7t17","MagBotRight7t17","MagRetC1","MagCR","MagCL",
//       "MagCLT","MagCLB","MagCRT","MagCRB","MagTopLeft17t24","MagTopRight17t24","MagBotLeft17t24","MagBotRight17t24",
//       "MagRetC4","MagC4L","MagC4LB","MagC4LT","MagC4R","MagC4RB","MagC4RT","MagTopLeft24t28","MagTopRight24t28",
//       "MagBotLeft24t28","MagBotRight24t28","MagRetC6L","MagRetC6R","MagC6L","MagC6R","MagTopLeft30t36","MagTopRight30t36",
//       "MagBotLeft30t36","MagBotRight30t36","MagRetC7L","MagRetC7R","MagC7L","MagC7R","MagTopLeft36t42","MagTopRight36t42",
//       "MagBotLeft36t42","MagBotRight36t42","MagRetC8L","MagRetC8R","MagC8L","MagC8R","MagTopLeft42t48","MagTopRight42t48",
//       "MagBotLeft42t48","MagBotRight42t48"};
//     Double_t ddZ[57] = {dZ1,dZ1,dZ1,dZ1,dZ1,dZ1,dZ1,dZ2,dZ2,dZ2,dZ2,dZ2,dZ2,dZ2,dZ3,dZ3,dZ3,dZ3,dZ3,dZ3,dZ3,dZ3-eps,dZ3-eps,dZ3-eps,dZ3-eps,
// 		      dZ4,dZ4,dZ4,dZ4,dZ4,dZ4,dZ4,dZ4,dZ4,dZ4,dZ4,dZ6,dZ6,dZ6,dZ6,dZ6,dZ6,dZ6,dZ6,dZ7,dZ7,dZ7,dZ7,dZ7,dZ7,dZ7,dZ7,
// 		      dZ7,dZ7,dZ7,dZ7,dZ7,dZ7,dZ7,dZ7};
//    
    CreateArb8("MagA", iron, dZ1,corners[0],45,magFieldIron,tShield,1,0, 0, Z1 );
    CreateArb8("MagRetA", iron, dZ1, corners[1],31,RetField,tShield,1,-X2, 0, Z1);
    CreateArb8("MagRetA", iron, dZ1, corners[1],31,RetField,tShield,1, X2, 0, Z1);
    CreateArb8("MagConALLT", iron,dZ1,corners[2],38,ConLField,tShield,1,dXH1,0.,Z1);
    CreateArb8("MagConARRT", iron,dZ1,corners[2],30,ConRField,tShield,1,-dXH1,0.,Z1);
    CreateArb8("MagConARLB", iron,dZ1,corners[3],30,ConRField,tShield,1,dXH1,0.,Z1);
    CreateArb8("MagConALRB", iron,dZ1,corners[3],38,ConLField,tShield,1,-dXH1,0.,Z1);
    CreateArb8("MagB", iron, dZ2, corners[4],45,magFieldIron,tShield,1,0, 0, Z2);
    CreateArb8("MagBRL", iron, dZ2, corners[5],31,RetField,tShield,1,0, 0, Z2);
    CreateArb8("MagBRR", iron, dZ2, corners[6],31,RetField,tShield,1,0, 0, Z2);
    CreateArb8("MagTopLeft7t17", iron, dZ2, corners[7],38,ConLField,tShield,1,0, 0, Z2);
    CreateArb8("MagTopRight7t17", iron, dZ2, corners[8],30,ConRField,tShield,1,0, 0, Z2);
    CreateArb8("MagBotLeft7t17", iron, dZ2, corners[9],30,ConRField,tShield,1,0, 0, Z2);
    CreateArb8("MagBotRight7t17", iron, dZ2, corners[10],38,ConLField,tShield,1,0, 0, Z2);
    CreateArb8("MagRetC1", iron, dZ3, corners[11],31,RetField,tShield,1,0, 0, Z3);
    CreateArb8("MagCR", iron, dZ3, corners[12],45,magFieldIron,tShield,1,0, 0, Z3);
    CreateArb8("MagCL", iron, dZ3, corners[13],45,magFieldIron,tShield,1,0, 0, Z3);
   //add 4 pieces for the fields.
    //left tShield field magnet 
    CreateArb8("MagCLT", iron, dZ3, corners[14],45,magFieldIron,tShield,1,0, 0, Z3);
    CreateArb8("MagCLB", iron, dZ3, corners[15],45,magFieldIron,tShield,1,0, 0, Z3);
    CreateArb8("MagCRT", iron, dZ3, corners[16],45,magFieldIron,tShield,1,0, 0, Z3);
    CreateArb8("MagCRB", iron, dZ3, corners[17],45,magFieldIron,tShield,1,0, 0, Z3);                           
//Top/Bot return magnets for 17-24 m
    CreateArb8("MagTopLeft17t24", iron, dZ3-eps, corners[18],30,ConRField,tShield,1,0, 0, Z3);
    CreateArb8("MagTopRight17t24", iron, dZ3-eps, corners[19],38,ConLField,tShield,1,0, 0, Z3);
//Bot return magnets 
    CreateArb8("MagBotLeft17t24", iron, dZ3-eps, corners[20],38,ConLField,tShield,1,0, 0, Z3);
    CreateArb8("MagBotRight17t24", iron, dZ3-eps, corners[21],30,ConRField,tShield,1,0, 0, Z3);
// 24<z<30. m, gap between field and return field      
    CreateArb8("MagRetC4", iron, dZ4, corners[22],31,RetField,tShield,1,0, 0, Z4);
   //left magnet, split in three, like for previous magnet
    CreateArb8("MagC4L", iron, dZ4, corners[23],45,magFieldIron,tShield,1,0, 0, Z4);
    CreateArb8("MagC4LB", iron, dZ4, corners[24],45,magFieldIron,tShield,1,0, 0, Z4);
    CreateArb8("MagC4LT", iron, dZ4, corners[25],45,magFieldIron,tShield,1,0, 0, Z4);
    CreateArb8("MagC4R", iron, dZ4, corners[26],45,magFieldIron,tShield,1,0, 0, Z4);
    CreateArb8("MagC4RB", iron, dZ4, corners[27],45,magFieldIron,tShield,1,0, 0, Z4);
    CreateArb8("MagC4RT", iron, dZ4, corners[28],45,magFieldIron,tShield,1,0, 0, Z4);
// //Top/Bot return magnets for 24-28 m
    CreateArb8("MagTopLeft24t28", iron, dZ4, corners[29],30,ConRField,tShield,1,0, 0, Z4);
    CreateArb8("MagTopRight24t28", iron, dZ4, corners[30],38,ConLField,tShield,1,0, 0, Z4);
// //Bot return magnets 
    CreateArb8("MagBotLeft24t28", iron, dZ4, corners[31],38,ConLField,tShield,1,0, 0, Z4);
    CreateArb8("MagBotRight24t28", iron, dZ4, corners[32],30,ConRField,tShield,1,0, 0, Z4);
// // 30<z<36 m: Note: here also return field splits!
//     //return fields
    CreateArb8("MagRetC6L", iron, dZ6, corners[33],31,RetField,tShield,1,0, 0, Z6);
    CreateArb8("MagRetC6R", iron, dZ6, corners[34],31,RetField,tShield,1,0, 0, Z6);
 //bending fields
    CreateArb8("MagC6L", iron, dZ6, corners[35],45,magFieldIron,tShield,1,0, 0, Z6);
    CreateArb8("MagC6R", iron, dZ6, corners[36],45,magFieldIron,tShield,1,0, 0, Z6);
//Top/Bot return magnets for 30-36 m, note inner return magnet splits too :-)
    CreateArb8("MagTopLeft30t36", iron, dZ6, corners[37],30,ConRField,tShield,1,0, 0, Z6);
    CreateArb8("MagTopRight30t36", iron, dZ6, corners[38],38,ConLField,tShield,1,0, 0, Z6);
// //Bot return magnets 
    CreateArb8("MagBotLeft30t36", iron, dZ6, corners[39],38,ConLField,tShield,1,0, 0, Z6);
    CreateArb8("MagBotRight30t36", iron, dZ6, corners[40],30,ConRField,tShield,1,0, 0, Z6);
// // 36<z<42 m: Note: here also return field splits!
//     //return fields
    CreateArb8("MagRetC7L", iron, dZ7, corners[41],31,RetField,tShield,1,0, 0, Z7);
    CreateArb8("MagRetC7R", iron, dZ7, corners[42],31,RetField,tShield,1,0, 0, Z7);
   //bending fields
    CreateArb8("MagC7L", iron, dZ7, corners[43],45,magFieldIron,tShield,1,0, 0, Z7);
    CreateArb8("MagC7R", iron, dZ7, corners[44],45,magFieldIron,tShield,1,0, 0, Z7);
//Top/Bot return magnets for 36-42 m, note inner return magnet splits too :-)
    CreateArb8("MagTopLeft36t42", iron, dZ7, corners[45],30,ConRField,tShield,1,0, 0, Z7);
    CreateArb8("MagTopRight36t42", iron, dZ7, corners[46],38,ConLField,tShield,1,0, 0, Z7);
//Bot return magnets 
    CreateArb8("MagBotLeft36t42", iron, dZ7, corners[47],38,ConLField,tShield,1,0, 0, Z7);
    CreateArb8("MagBotRight36t42", iron, dZ7, corners[48],30,ConRField,tShield,1,0, 0, Z7);
// 42<z<48 m: Note: here also return field splits!
     //return fields
    CreateArb8("MagRetC8L", iron, dZ8, corners[49],31,RetField,tShield,1,0, 0, Z8);
    CreateArb8("MagRetC8R", iron, dZ8, corners[50],31,RetField,tShield,1,0, 0, Z8);
    //bending fields
    CreateArb8("MagC8L", iron, dZ8, corners[51],45,magFieldIron,tShield,1,0, 0, Z8);
    CreateArb8("MagC8R", iron, dZ8, corners[52],45,magFieldIron,tShield,1,0, 0, Z8);
//Top/Bot return magnets for 42-48 m, note inner return magnet splits too :-)
    CreateArb8("MagTopLeft42t48", iron, dZ8, corners[53],30,ConRField,tShield,1,0, 0, Z8);
    CreateArb8("MagTopRight42t48", iron, dZ8, corners[54],38,ConLField,tShield,1,0, 0, Z8);
//Bot return magnets 
    CreateArb8("MagBotLeft42t48", iron, dZ8, corners[55],38,ConLField,tShield,1,0, 0, Z8);
    CreateArb8("MagBotRight42t48", iron, dZ8, corners[56],30,ConRField,tShield,1,0, 0, Z8);
    
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
    TGeoCompositeShape *compRockD = new TGeoCompositeShape("compRockD", "box3-box4");
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
