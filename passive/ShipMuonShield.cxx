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
#include "TGeoMedium.h"
#include "FairGeoInterface.h"
#include "FairGeoMedia.h"
#include "FairGeoBuilder.h"
#include "TGeoUniformMagField.h"
#include <stddef.h>                     // for NULL
#include <iostream>                     // for operator<<, basic_ostream, etc

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
                               Double_t L7, Double_t L8, Double_t gap, Double_t LE)
  : FairModule(name ,Title)
{
 fDesign = Design;
 if (fDesign==1){
    // passive design with tungsten and lead
     fMuonShieldLength = L1;   
    }
 if (fDesign==2){
     dZ0 = L0;
     dZ1 = L1;
     dZ2 = L2;
     dZ3 = L3;
     dZ4 = L4;
     dZ5 = L5;
     dZ6 = L6;
     fMuonShieldLength = 2*(dZ1+dZ2+dZ3+dZ4+dZ5+dZ6) + LE ; //leave some space for nu-tau detector   
    }
 if (fDesign==3||fDesign==4||fDesign==5){
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

void ShipMuonShield::ConstructGeometry()
{

    TGeoVolume *top=gGeoManager->GetTopVolume();
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
     TGeoBBox *box1    = new TGeoBBox("box1",  2*m,2*m,dZ/2.);    
     TGeoBBox *box2    = new TGeoBBox("box2", 10*m,7*m,dZ/2.);    
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
    else if (fDesign==2){
/*   active shield with magnets
    
  the lite design
  z<5 m: field <0.7 m, return 0.9-1.6.
  5<z<12 m: field=0.3-(z-5.)*0.02, return 1.6-(1.6-field) 
  Now the inside out magnet between 12<z<34 m:
  first the return field (called t350) around axis:
          if(z.lt.18.) then
           t350=(z-11.)*0.09/6.
          elseif(z.lt.24.) then
           t350=0.105+(z-18.)*0.18/6.
          elseif(z.lt.29.) then
           t350=0.285+(z-24.)*(0.5-0.285)/5.
          else
           t350=0.5
          endif
  now the field:
        12<z<29 m: field between t350 and 2*t350
        29<z<34 m:
               xb=(z-29.)*(1.7)/5.+0.5
               field between xb and xb+0.5, with maximum at 2.1 m
               (In fact this max makes that there is more return "flux"
               than flux, but a la for the last 1.5 m...)
z<12 m: inside tunnel, and I fill the gap between tunnel and magnet (max-x at 1.6 m), with concrete too.
z>12 m: in the experimental hall. I put its walls at 10 m from the beam-line.
*/
    Double_t ironField = 1.85*tesla;
    TGeoUniformMagField *magFieldIron = new TGeoUniformMagField(0.,ironField,0.);
    TGeoUniformMagField *RetField     = new TGeoUniformMagField(0.,-ironField,0.);
    TGeoUniformMagField *ConRField    = new TGeoUniformMagField(-ironField,0.,0.);
    TGeoUniformMagField *ConLField    = new TGeoUniformMagField(ironField,0.,0.);
 
// z<5m: just boxes, arguments are full length for python, half lengths for C++ 
    Double_t dX1 = 0.7*m; 
    Double_t dY  = 1.0*m;
    Double_t X2  = 1.25*m;   
    Double_t Z1  = zEndOfAbsorb + dZ1;
    TGeoVolume *magA = gGeoManager->MakeBox("MagA", iron, dX1, dY,dZ1);
    magA->SetLineColor(45);  // red-brown
    magA->SetField(magFieldIron);
    top->AddNode(magA, 1, new TGeoTranslation(0, 0, Z1 ));
 
    TGeoVolume *magRetA = gGeoManager->MakeBox("MagRetA", iron, dX1/2., dY, dZ1);
    magRetA->SetLineColor(31);  // green-brown
    magRetA->SetField(RetField);
    top->AddNode(magRetA, 1, new TGeoTranslation(-X2, 0, Z1 ));
    top->AddNode(magRetA, 1, new TGeoTranslation( X2, 0, Z1 ));

//  connection between field and return field, make it 1m thick :
    Double_t dYH1 = 0.5*m; 
    Double_t dXH1 = 0.5*(X2+dX1/2.);
    TGeoVolume  *magConALLT = gGeoManager->MakeBox("MagConALLT", iron,dXH1, dYH1, dZ1);
    magConALLT->SetLineColor(38);  
    magConALLT->SetField(ConLField);
    top->AddNode(magConALLT, 1, new TGeoTranslation(dXH1,dY+dYH1,Z1));
    TGeoVolume  *magConARRT = gGeoManager->MakeBox("MagConARRT", iron,dXH1, dYH1, dZ1);
    magConARRT->SetLineColor(30);  
    magConARRT->SetField(ConRField);
    top->AddNode(magConARRT, 1, new TGeoTranslation(-dXH1,dY+dYH1,Z1));
    TGeoVolume  *magConARLB = gGeoManager->MakeBox("MagConARLB", iron,dXH1, dYH1, dZ1);
    magConARLB->SetLineColor(30);  
    magConARLB->SetField(ConRField);
    top->AddNode(magConARLB, 1, new TGeoTranslation(dXH1,-(dY+dYH1),Z1));
    TGeoVolume  *magConALRB = gGeoManager->MakeBox("MagConALRB", iron,dXH1, dYH1, dZ1);
    magConALRB->SetLineColor(38);  
    magConALRB->SetField(ConLField);
    top->AddNode(magConALRB, 1, new TGeoTranslation(-dXH1,-(dY+dYH1),Z1));
// 5<z<12 m: trapezoid   
    Double_t dX2 = 0.3*m;
    Double_t dX3 = 0.16*m;
    Double_t Z2 = zEndOfAbsorb + 2*dZ1 + dZ2;
    TGeoVolume *magB = gGeoManager->MakeTrd1("MagB", iron, dX2, dX3, dY, dZ2);
    magB->SetLineColor(45);  // red-brown
    magB->SetField(magFieldIron);
    top->AddNode(magB, 1, new TGeoTranslation(0, 0, Z2 ));

    Double_t pDz   = 0.5*(2*dY);
    Double_t theta = 0; 
    Double_t phi   = 0; 
    Double_t h1    = 0.5*(2*dZ2);
    Double_t bl1   = 0.5*(dX2);
    Double_t tl1   = 0.5*(dX3);
    Double_t alpha1 = std::atan(0.5*(dX3 - dX2)/(2*dZ2));
    Double_t h2  = h1;
    Double_t bl2 = bl1;
    Double_t tl2 = tl1;
    Double_t alpha2 = alpha1;
    TGeoVolume *magRetB = gGeoManager->MakeTrap("MagRetB", iron, pDz, theta, phi, h1, bl1, tl1, alpha1, h2, bl2, tl2, alpha2);
    magRetB->SetLineColor(31);  // green-brown
    magRetB->SetField(RetField);
    TGeoRotation rot;
    rot.RotateX(90);
    Double_t X22 = 1.6*m-0.5*(dX2+dX3)/2.;
    TGeoTranslation transR(-X22, 0,Z2);
    TGeoCombiTrans fR(transR, rot);
    TGeoHMatrix *hR = new TGeoHMatrix(fR);
    top->AddNode(magRetB, 101, hR);   // right part
    TGeoTranslation transL(X22, 0,Z2);
    rot.RotateZ(180);
    TGeoCombiTrans fL(transL, rot);
    TGeoHMatrix *hL = new TGeoHMatrix(fL);
    top->AddNode(magRetB, 102, hL);   // left part
// 12<z<18 m:
    Double_t dX4 =  0.015*m;
    Double_t dX5 =  0.105*m;
    Double_t Z3  = zEndOfAbsorb + 2*dZ1 + 2*dZ2 + dZ3;
    TGeoVolume *magRetC1 = gGeoManager->MakeTrd1("MagRetC1", iron, dX4, dX5, dY, dZ3);
    magRetC1->SetLineColor(31);  // green-brown
    magRetC1->SetField(RetField);
    top->AddNode(magRetC1, 1, new TGeoTranslation(0, 0, Z3 ));
     
    TGeoTrd1 *magC1T    = new TGeoTrd1("MagC1T",2*dX4, 2*dX5, dY-0.1*mm, dZ3-0.1*mm);    
    TGeoTrd1 *magRetC1T = new TGeoTrd1("MagRetC1T",dX4, dX5, dY, dZ3);        
    TGeoCompositeShape *compmagC1 = new TGeoCompositeShape("compMagC1", "MagC1T-MagRetC1T");
    TGeoVolume *magC1   = new TGeoVolume("MagC1", compmagC1, iron);
    magC1->SetLineColor(45);  // red-brown
    magC1->SetField(magFieldIron);
    top->AddNode(magC1, 1, new TGeoTranslation(0, 0, Z3));
// 18<z<24 m:
    Double_t dX6 =  dX5;
    Double_t dX7 =  0.285*m;
    Double_t Z4  = zEndOfAbsorb + 2*dZ1 + 2*dZ2 + 2*dZ3 + dZ4;
    TGeoVolume *magRetC2 = gGeoManager->MakeTrd1("MagRetC2", iron, dX6, dX7, dY, dZ4);
    magRetC2->SetLineColor(31);  // green-brown
    magRetC2->SetField(RetField);
    top->AddNode(magRetC2, 1, new TGeoTranslation(0, 0, Z4 ));

    TGeoTrd1 *magC2T    = new TGeoTrd1("MagC2T",2*dX6, 2*dX7, dY-0.1*mm, dZ4-0.1*mm);    
    TGeoTrd1 *magRetC2T = new TGeoTrd1("MagRetC2T",dX6, dX7, dY, dZ4);    
    TGeoCompositeShape *compmagC2 = new TGeoCompositeShape("compMagC2", "MagC2T-MagRetC2T");
    TGeoVolume *magC2   = new TGeoVolume("MagC2", compmagC2, iron);
    magC2->SetField(magFieldIron);
    magC2->SetLineColor(45);  // red-brown
    top->AddNode(magC2, 1, new TGeoTranslation(0, 0, Z4));
// 24<z<29 m:
    Double_t dX8 =  dX7;
    Double_t dX9 =  0.5*m;
    Double_t Z5 = zEndOfAbsorb + 2*dZ1 + 2*dZ2 + 2*dZ3 + 2*dZ4 + dZ5;
    TGeoVolume *magRetC3 = gGeoManager->MakeTrd1("MagRetC3", iron, dX8, dX9, dY, dZ5);
    magRetC3->SetLineColor(31);  // green-brown
    magRetC3->SetField(RetField);
    top->AddNode(magRetC3, 1, new TGeoTranslation(0, 0, Z5 ));

    TGeoTrd1 *magC3T    = new TGeoTrd1("MagC3T",2*dX8, 2*dX9, dY-0.1*mm, dZ5-0.1*mm);    
    TGeoTrd1 *magRetC3T = new TGeoTrd1("MagRetC3T",dX8, dX9, dY, dZ5);
    TGeoCompositeShape *compmagC3 = new TGeoCompositeShape("compMagC3", "MagC3T-MagRetC3T");
    TGeoVolume *magC3   = new TGeoVolume("MagC3", compmagC3, iron);
    magC3->SetField(magFieldIron);
    magC3->SetLineColor(45);  // red-brown
    top->AddNode(magC3, 1, new TGeoTranslation(0, 0, Z5));
// 29<z<34 m:
    Double_t dX10 =  dX9;
    Double_t dX11 =  0.5*m;
    Double_t dX12 =  2.2*m;
    Double_t Z6 = zEndOfAbsorb + 2*dZ1 + 2*dZ2 + 2*dZ3 + 2*dZ4 + 2*dZ5 + dZ6;
    TGeoVolume *magRetC4 = gGeoManager->MakeBox("MagRetC4", iron, dX10, dY, dZ6 );
    magRetC4->SetLineColor(31);  // green-brown
    magRetC4->SetField(RetField);
    top->AddNode(magRetC4, 1, new TGeoTranslation(0, 0, Z6 ));

    TGeoTrd1 *magC4T    = new TGeoTrd1("MagC4T", 2*dX10,dX12+dX11, dY, dZ6);       
    TGeoTrd1 *magC5T    = new TGeoTrd1("MagC5T",dX10, dX12,     dY+1*mm, dZ6+1*mm); 
    TGeoCompositeShape *compmagC4 = new TGeoCompositeShape("compMagC4", "MagC4T-MagC5T");
    TGeoVolume *magC4   = new TGeoVolume("MagC4", compmagC4, iron);
    magC4->SetField(magFieldIron);
    magC4->SetLineColor(45);  // red-brown
    top->AddNode(magC4, 1, new TGeoTranslation(0, 0, Z6));
// Concrete around first magnets

    Double_t dZ = dZ1 + dZ2;
    TGeoBBox *box1    = new TGeoBBox("box1",  2*m,2*m,dZ/2.);    
    TGeoBBox *box2    = new TGeoBBox("box2", 10*m,7*m,dZ/2.);    
    TGeoCompositeShape *compRockS = new TGeoCompositeShape("compRockS", "box2-box1");
    TGeoVolume *rockS   = new TGeoVolume("rockS", compRockS, concrete);
    rockS->SetLineColor(11);  // grey
    rockS->SetTransparency(50);
    top->AddNode(rockS, 1, new TGeoTranslation(0, 0, Z1 ));
// around decay tunnel
    Double_t dZD =  100*m + 30*m;
    TGeoBBox *box3    = new TGeoBBox("box3", 15*m,12.25*m,dZD/2.);    
    TGeoBBox *box4    = new TGeoBBox("box4", 10*m, 7.25*m,dZD/2.);    
    TGeoCompositeShape *compRockD = new TGeoCompositeShape("compRockD", "box3-box4");
    TGeoVolume *rockD   = new TGeoVolume("rockD", compRockD, concrete);
    rockD->SetLineColor(11);  // grey
    rockD->SetTransparency(50);
    top->AddNode(rockD, 1, new TGeoTranslation(0, 0, zEndOfAbsorb + dZ + dZD/2.));
// lead shield
    Double_t sz = Z6+dZ6+0.1*m;
    TGeoVolume *eShield = gGeoManager->MakeTube("eShield", lead, 0., 1.1*m, 1*m);
    eShield->SetLineColor(5);
    top->AddNode(eShield, 1, new TGeoTranslation(0, 0, sz+3*m));
    }
    else if (fDesign==3){
// latest shielding of Hans with large aperture to fit tau neutrino detector
// add here the additional 2m hadron shield, decided 17 october 2014
    // 2m more Absorber made of iron
    TGeoVolume *absorber = gGeoManager->MakeTube("AbsorberAdd", iron, 15, 400, dZ0);   
    absorber->SetLineColor(43);  
    top->AddNode(absorber, 1, new TGeoTranslation(0, 0, zEndOfAbsorb - dZ0));
    TGeoVolume *absorberCore = gGeoManager->MakeTube("AbsorberAddCore", tungsten, 0, 15, dZ0);   
    absorberCore->SetLineColor(38);  
    top->AddNode(absorberCore, 1, new TGeoTranslation(0, 0, zEndOfAbsorb - dZ0));

    Double_t ironField = 1.8*tesla;
    TGeoUniformMagField *magFieldIron = new TGeoUniformMagField(0.,ironField,0.);
    TGeoUniformMagField *RetField     = new TGeoUniformMagField(0.,-ironField,0.);
    TGeoUniformMagField *ConRField    = new TGeoUniformMagField(-ironField,0.,0.);
    TGeoUniformMagField *ConLField    = new TGeoUniformMagField(ironField,0.,0.);
 
// z<7m: just boxes, arguments are full length for python, half lengths for C++ 
    Double_t dX1 = 0.7*m; 
    Double_t dY  = 1.0*m;
    Double_t X2  = 1.25*m;   
    Double_t Z1  = zEndOfAbsorb + dZ1;
    TGeoVolume *magA = gGeoManager->MakeBox("MagA", iron, dX1, dY,dZ1);
    magA->SetLineColor(45);  // red-brown
    magA->SetField(magFieldIron);
    top->AddNode(magA, 1, new TGeoTranslation(0, 0, Z1 ));
 
    TGeoVolume *magRetA = gGeoManager->MakeBox("MagRetA", iron, dX1/2., dY, dZ1);
    magRetA->SetLineColor(31);  // green-brown
    magRetA->SetField(RetField);
    top->AddNode(magRetA, 1, new TGeoTranslation(-X2, 0, Z1 ));
    top->AddNode(magRetA, 1, new TGeoTranslation( X2, 0, Z1 ));

//  connection between field and return field, same thickness as width/2, i.e. dX1
//  15/10/2014: reduce thickness from 1.m to 0.7 m to maintain same flux everywhere.
    Double_t dYH1 = dX1/2.; 
    Double_t dXH1 = 0.5*(X2+dX1/2.);
    TGeoVolume  *magConALLT = gGeoManager->MakeBox("MagConALLT", iron,dXH1, dYH1, dZ1);
    magConALLT->SetLineColor(38);  
    magConALLT->SetField(ConLField);
    top->AddNode(magConALLT, 1, new TGeoTranslation(dXH1,dY+dYH1,Z1));
    TGeoVolume  *magConARRT = gGeoManager->MakeBox("MagConARRT", iron,dXH1, dYH1, dZ1);
    magConARRT->SetLineColor(30);  
    magConARRT->SetField(ConRField);
    top->AddNode(magConARRT, 1, new TGeoTranslation(-dXH1,dY+dYH1,Z1));
    TGeoVolume  *magConARLB = gGeoManager->MakeBox("MagConARLB", iron,dXH1, dYH1, dZ1);
    magConARLB->SetLineColor(30);  
    magConARLB->SetField(ConRField);
    top->AddNode(magConARLB, 1, new TGeoTranslation(dXH1,-(dY+dYH1),Z1));
    TGeoVolume  *magConALRB = gGeoManager->MakeBox("MagConALRB", iron,dXH1, dYH1, dZ1);
    magConALRB->SetLineColor(38);  
    magConALRB->SetField(ConLField);
    top->AddNode(magConALRB, 1, new TGeoTranslation(-dXH1,-(dY+dYH1),Z1));

// 7<z<17 m: 
    Double_t dX2 = 0.36*m;
    Double_t dX3 = 0.16*m;
    Double_t Z2 = zEndOfAbsorb + 2*dZ1 + dZ2;
    Double_t corners1[16] = {-dX2,-dY, -dX2,dY, dX2,dY, dX2,-dY,
                            -dX3,-dY, -dX3,dY, dX3,dY, dX3,-dY};
    TGeoVolume *magB = gGeoManager->MakeArb8("MagB", iron, dZ2, corners1) ;
    magB->SetLineColor(45);  
    magB->SetField(magFieldIron);
    top->AddNode(magB, 1, new TGeoTranslation(0, 0, Z2 ));

    Double_t corners2[16] = {1.6*m-dX2,-dY, 1.6*m-dX2,dY, 1.6*m,dY, 1.6*m,-dY, 
                            1.6*m-dX3,-dY, 1.6*m-dX3,dY, 1.6*m,dY, 1.6*m,-dY};
    TGeoVolume *magBRL = gGeoManager->MakeArb8("MagBRL", iron, dZ2, corners2) ;
    magBRL->SetLineColor(31);  
    magBRL->SetField(RetField);
    top->AddNode(magBRL, 1, new TGeoTranslation(0, 0, Z2 ));

    Double_t corners3[16] = {-1.6*m,-dY, -1.6*m,dY, -1.6*m+dX2,dY, -1.6*m+dX2,-dY, 
                            -1.6*m,-dY, -1.6*m,dY, -1.6*m+dX3,dY, -1.6*m+dX3,-dY};
    TGeoVolume *magBRR = gGeoManager->MakeArb8("MagBRR", iron, dZ2, corners3) ;
    magBRR->SetLineColor(31);  
    magBRR->SetField(RetField);
    top->AddNode(magBRR, 1, new TGeoTranslation(0, 0, Z2 ));

//Top/Bot return magnets for 7-17 m
//corners "first clockwise lower z, them clockwise upper z
    Double_t corners4[16] = {0.,dY, 0.,dY+dX2, 1.6*m,dY+dX2, 1.6*m,dY, 
                            0.,dY, 0.,dY+dX3, 1.6*m,dY+dX3, 1.6*m,dY};
    TGeoVolume *magTopLeft7t17 = gGeoManager->MakeArb8("MagTopLeft7t17", iron, dZ2, corners4) ;
    magTopLeft7t17->SetLineColor(38);  
    magTopLeft7t17->SetField(ConLField);
    top->AddNode(magTopLeft7t17, 1, new TGeoTranslation(0, 0, Z2 ));

    Double_t corners5[16] = {-1.6*m,dY, -1.6*m,dY+dX2, 0.,dY+dX2, 0.,dY, 
                            -1.6*m,dY, -1.6*m,dY+dX3, 0.,dY+dX3, 0.,dY};
    TGeoVolume *magTopRight7t17 = gGeoManager->MakeArb8("MagTopRight7t17", iron, dZ2, corners5) ;
    magTopRight7t17->SetLineColor(30); 
    magTopRight7t17->SetField(ConRField);
    top->AddNode(magTopRight7t17, 1, new TGeoTranslation(0, 0, Z2 ));
//Bot return magnets for 7-17 m
    Double_t corners6[16] = {0.,-dY-dX2, 0.,-dY, 1.6*m,-dY, 1.6*m,-dY-dX2, 
                            0.,-dY-dX3, 0.,-dY, 1.6*m,-dY, 1.6*m,-dY-dX3};
    TGeoVolume *magBotLeft7t17 = gGeoManager->MakeArb8("MagBotLeft7t17", iron, dZ2, corners6) ;
    magBotLeft7t17->SetLineColor(30);  
    magBotLeft7t17->SetField(ConRField);
    top->AddNode(magBotLeft7t17, 1, new TGeoTranslation(0, 0, Z2 ));

    Double_t corners7[16] = {-1.6*m,-dY-dX2, -1.6*m,-dY, 0.,-dY, 0.,-dY-dX2, 
                            -1.6*m,-dY-dX3, -1.6*m,-dY, 0.,-dY, 0.,-dY-dX3};
    TGeoVolume *magBotRight7t17 = gGeoManager->MakeArb8("MagBotRight7t17", iron, dZ2, corners7) ;
    magBotRight7t17->SetLineColor(38); 
    magBotRight7t17->SetField(ConLField);
    top->AddNode(magBotRight7t17, 1, new TGeoTranslation(0, 0, Z2 ));
   

// 17<z<24 m:
    Double_t dX17 =  0.075*m;
    Double_t dX24 =  0.3*m;
    Double_t Z3  = zEndOfAbsorb + 2*dZ1 + 2*dZ2 + dZ3;
    TGeoVolume *magRetC1 = gGeoManager->MakeTrd1("MagRetC1", iron, dX17, dX24, dY, dZ3);
    magRetC1->SetLineColor(31);  // green-brown
    magRetC1->SetField(RetField);
    top->AddNode(magRetC1, 1, new TGeoTranslation(0, 0, Z3 ));
     
    TGeoTrd1 *magC1T    = new TGeoTrd1("MagC1T",2*dX17, 2*dX24, dY-0.1*mm, dZ3-0.1*mm);    
    TGeoTrd1 *magRetC1T = new TGeoTrd1("MagRetC1T",dX17, dX24, dY, dZ3);        
    TGeoCompositeShape *compmagC1 = new TGeoCompositeShape("compMagC1", "MagC1T-MagRetC1T");
    TGeoVolume *magC1   = new TGeoVolume("MagC1", compmagC1, iron);
    magC1->SetLineColor(45);  // red-brown
    magC1->SetField(magFieldIron);
    top->AddNode(magC1, 1, new TGeoTranslation(0, 0, Z3));
//Top/Bot return magnets for 17-24 m
    Double_t corners8[16] = {0.,dY, 0.,dY+dX17, 2*dX17,dY+dX17, 2*dX17,dY, 
                            0.,dY, 0.,dY+dX24, 2*dX24,dY+dX24, 2*dX24,dY}; 
    TGeoVolume *magTopLeft17t24 = gGeoManager->MakeArb8("MagTopLeft17t24", iron, dZ3, corners8) ;
    magTopLeft17t24->SetLineColor(38);  
    magTopLeft17t24->SetField(ConLField);
    top->AddNode(magTopLeft17t24, 1, new TGeoTranslation(0, 0, Z3 ));

    Double_t corners9[16] = {-2*dX17,dY, -2*dX17,dY+dX17, 0., dY+dX17, 0.,dY,
                            -2*dX24,dY, -2*dX24,dY+dX24, 0., dY+dX24, 0.,dY};
    TGeoVolume *magTopRight17t24 = gGeoManager->MakeArb8("MagTopRight17t24", iron, dZ3, corners9) ;
    magTopRight17t24->SetLineColor(30); 
    magTopRight17t24->SetField(ConRField);
    top->AddNode(magTopRight17t24, 1, new TGeoTranslation(0, 0, Z3 ));
//Bot return magnets 
    Double_t corners10[16] = {0.,-dY-dX17, 0.,-dY, 2*dX17,-dY, 2*dX17,-dY-dX17, 
                            0.,-dY-dX24, 0.,-dY, 2*dX24,-dY, 2*dX24,-dY-dX24};
    TGeoVolume *magBotLeft17t24 = gGeoManager->MakeArb8("MagBotLeft17t24", iron, dZ3, corners10) ;
    magBotLeft17t24->SetLineColor(30);  
    magBotLeft17t24->SetField(ConRField);
    top->AddNode(magBotLeft17t24, 1, new TGeoTranslation(0, 0, Z3 ));

    Double_t corners11[16] = {-2*dX17,-dY-dX17, -2*dX17,-dY, 0.,-dY, 0.,-dY-dX17, 
                            -2*dX24,-dY-dX24, -2*dX24,-dY, 0.,-dY, 0.,-dY-dX24};
    TGeoVolume *magBotRight17t24 = gGeoManager->MakeArb8("MagBotRight17t24", iron, dZ3, corners11) ;
    magBotRight17t24->SetLineColor(38); 
    magBotRight17t24->SetField(ConLField);
    top->AddNode(magBotRight17t24, 1, new TGeoTranslation(0, 0, Z3 ));

// 24<z<28 m:      
    Double_t dX28 = 0.5*m;
    Double_t Z4 = zEndOfAbsorb + 2*dZ1 + 2*dZ2 + 2*dZ3 + dZ4;
    TGeoVolume *magRetC4 = gGeoManager->MakeBox("MagRetC4", iron, dX24, dY, dZ4 );
    magRetC4->SetLineColor(31);  // green-brown
    magRetC4->SetField(RetField);
    top->AddNode(magRetC4, 1, new TGeoTranslation(0, 0, Z4 ));

    TGeoTrd1 *magC4Out    = new TGeoTrd1("MagC4Out", 2*dX24,dX24+dX28,  dY,      dZ4);       
    TGeoTrd1 *magC4In     = new TGeoTrd1("MagC4In",    dX24,     dX28,dY+1*mm, dZ4+1*mm); 
    TGeoCompositeShape *compmagC4 = new TGeoCompositeShape("compMagC4", "MagC4Out-MagC4In");
    TGeoVolume *magC4   = new TGeoVolume("MagC4", compmagC4, iron);
    magC4->SetField(magFieldIron);
    magC4->SetLineColor(45);  // red-brown
    top->AddNode(magC4, 1, new TGeoTranslation(0, 0, Z4));
//Top/Bot return magnets for 24-28 m
    Double_t corners12[16] = {0.,dY, 0.,dY+dX24, 2*dX24,dY+dX24, 2*dX24,dY, 
                            0.,dY, 0.,dY+dX28, 2*dX28,dY+dX28, 2*dX28,dY}; 
    TGeoVolume *magTopLeft24t28 = gGeoManager->MakeArb8("MagTopLeft24t28", iron, dZ4, corners12) ;
    magTopLeft24t28->SetLineColor(38);  
    magTopLeft24t28->SetField(ConLField);
    top->AddNode(magTopLeft24t28, 1, new TGeoTranslation(0, 0, Z4 ));

    Double_t corners13[16] = {-2*dX24,dY, -2*dX24,dY+dX24, 0., dY+dX24, 0.,dY,
                            -2*dX28,dY, -2*dX28,dY+dX28, 0., dY+dX28, 0.,dY};
    TGeoVolume *magTopRight24t28 = gGeoManager->MakeArb8("MagTopRight24t28", iron, dZ4, corners13) ;
    magTopRight24t28->SetLineColor(30); 
    magTopRight24t28->SetField(ConRField);
    top->AddNode(magTopRight24t28, 1, new TGeoTranslation(0, 0, Z4 ));
//Bot return magnets 
    Double_t corners14[16] = {0.,-dY-dX24, 0.,-dY, 2*dX24,-dY, 2*dX24,-dY-dX24, 
                            0.,-dY-dX28, 0.,-dY, 2*dX28,-dY, 2*dX28,-dY-dX28};
    TGeoVolume *magBotLeft24t28 = gGeoManager->MakeArb8("MagBotLeft24t28", iron, dZ4, corners14) ;
    magBotLeft24t28->SetLineColor(30);  
    magBotLeft24t28->SetField(ConRField);
    top->AddNode(magBotLeft24t28, 1, new TGeoTranslation(0, 0, Z4 ));

    Double_t corners15[16] = {-2*dX24,-dY-dX24, -2*dX24,-dY, 0.,-dY, 0.,-dY-dX24, 
                            -2*dX28,-dY-dX28, -2*dX28,-dY, 0.,-dY, 0.,-dY-dX28};
    TGeoVolume *magBotRight24t28 = gGeoManager->MakeArb8("MagBotRight24t28", iron, dZ4, corners15) ;
    magBotRight24t28->SetLineColor(38); 
    magBotRight24t28->SetField(ConLField);
    top->AddNode(magBotRight24t28, 1, new TGeoTranslation(0, 0, Z4 ));

// 28<z<30 m: Note: here also return field splits!
    Double_t W28 = dX24;
    Double_t dXr28I = 0.;
    Double_t dXr28O = dXr28I+W28;
    Double_t dX28I = dXr28O+dXgap;
    Double_t dX28O = dX28I+W28;
    Double_t W30 = W28;
    Double_t dX30I = 0.6*m;
    Double_t dX30O = dX30I+W30;
    Double_t dXr30O = dX30I-dXgap;
    Double_t dXr30I = dXr30O-W30;

    
    Double_t Z5 = zEndOfAbsorb + 2*dZ1 + 2*dZ2 + 2*dZ3 + 2*dZ4+dZ5;
    TGeoTrd1 *magC5rOut    = new TGeoTrd1("MagC5rOut", dXr28O,dXr30O, dY,      dZ5);       
    TGeoTrd1 *magC5rIn     = new TGeoTrd1("MagC5rIn",  dXr28I,dXr30I, dY+1*mm, dZ5+1*mm); 
    TGeoCompositeShape *compmagC5r = new TGeoCompositeShape("compMagC5r", "MagC5rOut-MagC5rIn");
    TGeoVolume *magRetC5   = new TGeoVolume("MagRetC5", compmagC5r, iron);
    magRetC5->SetLineColor(31);  // green-brown
    magRetC5->SetField(RetField);
    top->AddNode(magRetC5, 1, new TGeoTranslation(0, 0, Z5 ));

    TGeoTrd1 *magC5Out    = new TGeoTrd1("MagC5Out", dX28O,dX30O, dY,      dZ5);       
    TGeoTrd1 *magC5In     = new TGeoTrd1("MagC5In",  dX28I,dX30I, dY+1*mm, dZ5+1*mm); 
    TGeoCompositeShape *compmagC5 = new TGeoCompositeShape("compMagC5", "MagC5Out-MagC5In");
    TGeoVolume *magC5   = new TGeoVolume("MagC5", compmagC5, iron);
    magC5->SetField(magFieldIron);
    magC5->SetLineColor(45);  // red-brown
    top->AddNode(magC5, 1, new TGeoTranslation(0, 0, Z5));
//Top/Bot return magnets for 28-30 m, note inner return magnet splits too :-)
    Double_t corners16[16] = {dXr28I,dY, dXr28I,dY+W28, dX28O,dY+W28, dX28O,dY, 
                            dXr30I,dY, dXr30I,dY+W30, dX30O,dY+W30, dX30O,dY}; 
    TGeoVolume *magTopLeft28t30 = gGeoManager->MakeArb8("MagTopLeft28t30", iron, dZ5, corners16) ;
    magTopLeft28t30->SetLineColor(38);  
    magTopLeft28t30->SetField(ConLField);
    top->AddNode(magTopLeft28t30, 1, new TGeoTranslation(0, 0, Z5 ));

    Double_t corners17[16] = {-dX28O,dY, -dX28O,dY+W28, -dXr28I, dY+W28, -dXr28I,dY,
                            -dX30O,dY, -dX30O,dY+W30, -dXr30I, dY+W30, -dXr30I,dY};
    TGeoVolume *magTopRight28t30 = gGeoManager->MakeArb8("MagTopRight28t30", iron, dZ5, corners17) ;
    magTopRight28t30->SetLineColor(30); 
    magTopRight28t30->SetField(ConRField);
    top->AddNode(magTopRight28t30, 1, new TGeoTranslation(0, 0, Z5 ));
//Bot return magnets 
    Double_t corners18[16] = {dXr28I,-dY-W28, dXr28I,-dY, dX28O,-dY, dX28O,-dY-W28, 
                            dXr30I,-dY-W30, dXr30I,-dY, dX30O,-dY, dX30O,-dY-W30};
    TGeoVolume *magBotLeft28t30 = gGeoManager->MakeArb8("MagBotLeft28t30", iron, dZ5, corners18) ;
    magBotLeft28t30->SetLineColor(30);  
    magBotLeft28t30->SetField(ConRField);
    top->AddNode(magBotLeft28t30, 1, new TGeoTranslation(0, 0, Z5 ));

    Double_t corners19[16] = {-dX28O,-dY-W28, -dX28O,-dY, -dXr28I,-dY, -dXr28I,-dY-W28, 
                            -dX30O,-dY-W30, -dX30O,-dY, -dXr30I,-dY, -dXr30I,-dY-W30};
    TGeoVolume *magBotRight28t30 = gGeoManager->MakeArb8("MagBotRight28t30", iron, dZ5, corners19) ;
    magBotRight28t30->SetLineColor(38); 
    magBotRight28t30->SetField(ConLField);
    top->AddNode(magBotRight28t30, 1, new TGeoTranslation(0, 0, Z5 ));

// 30<z<36 m: Note: here also return field splits!
    Double_t W36 = 0.4*m;
    Double_t dX36I = 0.9*m;
    Double_t dX36O = dX36I+W36;
    Double_t dXr36O = dX36I-dXgap;
    Double_t dXr36I = dXr36O-W36;

    Double_t Z6 = zEndOfAbsorb + 2*dZ1 + 2*dZ2 + 2*dZ3 + 2*dZ4+2*dZ5+dZ6;
    TGeoTrd1 *magC6rOut    = new TGeoTrd1("MagC6rOut", dXr30O,dXr36O, dY,      dZ6);       
    TGeoTrd1 *magC6rIn     = new TGeoTrd1("MagC6rIn",  dXr30I,dXr36I, dY+1*mm, dZ6+1*mm); 
    TGeoCompositeShape *compmagC6r = new TGeoCompositeShape("compMagC6r", "MagC6rOut-MagC6rIn");
    TGeoVolume *magRetC6   = new TGeoVolume("MagRetC6", compmagC6r, iron);
    magRetC6->SetLineColor(31);  // green-brown
    magRetC6->SetField(RetField);
    top->AddNode(magRetC6, 1, new TGeoTranslation(0, 0, Z6 ));

    TGeoTrd1 *magC6Out    = new TGeoTrd1("MagC6Out", dX30O,dX36O, dY,      dZ6);       
    TGeoTrd1 *magC6In     = new TGeoTrd1("MagC6In",  dX30I,dX36I, dY+1*mm, dZ6+1*mm); 
    TGeoCompositeShape *compmagC6 = new TGeoCompositeShape("compMagC6", "MagC6Out-MagC6In");
    TGeoVolume *magC6   = new TGeoVolume("MagC6", compmagC6, iron);
    magC6->SetField(magFieldIron);
    magC6->SetLineColor(45);  // red-brown
    top->AddNode(magC6, 1, new TGeoTranslation(0, 0, Z6));
//Top/Bot return magnets for 30-36 m, note inner return magnet splits too :-)
    Double_t corners20[16] = {dXr30I,dY, dXr30I,dY+W30, dX30O,dY+W30, dX30O,dY, 
                            dXr36I,dY, dXr36I,dY+W36, dX36O,dY+W36, dX36O,dY}; 
    TGeoVolume *magTopLeft30t36 = gGeoManager->MakeArb8("MagTopLeft30t36", iron, dZ6, corners20) ;
    magTopLeft30t36->SetLineColor(38);  
    magTopLeft30t36->SetField(ConLField);
    top->AddNode(magTopLeft30t36, 1, new TGeoTranslation(0, 0, Z6 ));

    Double_t corners21[16] = {-dX30O,dY, -dX30O,dY+W30, -dXr30I, dY+W30, -dXr30I,dY,
                            -dX36O,dY, -dX36O,dY+W36, -dXr36I, dY+W36, -dXr36I,dY};
    TGeoVolume *magTopRight30t36 = gGeoManager->MakeArb8("MagTopRight30t36", iron, dZ6, corners21) ;
    magTopRight30t36->SetLineColor(30); 
    magTopRight30t36->SetField(ConRField);
    top->AddNode(magTopRight30t36, 1, new TGeoTranslation(0, 0, Z6 ));
//Bot return magnets 
    Double_t corners22[16] = {dXr30I,-dY-W30, dXr30I,-dY, dX30O,-dY, dX30O,-dY-W30, 
                            dXr36I,-dY-W36, dXr36I,-dY, dX36O,-dY, dX36O,-dY-W36};
    TGeoVolume *magBotLeft30t36 = gGeoManager->MakeArb8("MagBotLeft30t36", iron, dZ6, corners22) ;
    magBotLeft30t36->SetLineColor(30);  
    magBotLeft30t36->SetField(ConRField);
    top->AddNode(magBotLeft30t36, 1, new TGeoTranslation(0, 0, Z6 ));

    Double_t corners23[16] = {-dX30O,-dY-W30, -dX30O,-dY, -dXr30I,-dY, -dXr30I,-dY-W30, 
                            -dX36O,-dY-W36, -dX36O,-dY, -dXr36I,-dY, -dXr36I,-dY-W36};
    TGeoVolume *magBotRight30t36 = gGeoManager->MakeArb8("MagBotRight30t36", iron, dZ6, corners23) ;
    magBotRight30t36->SetLineColor(38); 
    magBotRight30t36->SetField(ConLField);
    top->AddNode(magBotRight30t36, 1, new TGeoTranslation(0, 0, Z6 ));

// 36<z<42 m: Note: here also return field splits!
    Double_t W42 = 0.4*m;
    Double_t dX42I = 1.3*m;
    Double_t dX42O = dX42I+W42;
    Double_t dXr42O = dX42I-dXgap;
    Double_t dXr42I = dXr42O-W42;

    
    Double_t Z7 = zEndOfAbsorb + 2*dZ1 + 2*dZ2 + 2*dZ3 + 2*dZ4+2*dZ5+2*dZ6+dZ7;
    TGeoTrd1 *magC7rOut    = new TGeoTrd1("MagC7rOut", dXr36O,dXr42O, dY,      dZ7);       
    TGeoTrd1 *magC7rIn     = new TGeoTrd1("MagC7rIn",  dXr36I,dXr42I, dY+1*mm, dZ7+1*mm); 
    TGeoCompositeShape *compmagC7r = new TGeoCompositeShape("compMagC7r", "MagC7rOut-MagC7rIn");
    TGeoVolume *magRetC7   = new TGeoVolume("MagRetC7", compmagC7r, iron);
    magRetC7->SetLineColor(31);  // green-brown
    magRetC7->SetField(RetField);
    top->AddNode(magRetC7, 1, new TGeoTranslation(0, 0, Z7 ));

    TGeoTrd1 *magC7Out    = new TGeoTrd1("MagC7Out", dX36O,dX42O, dY,      dZ7);       
    TGeoTrd1 *magC7In     = new TGeoTrd1("MagC7In",  dX36I,dX42I, dY+1*mm, dZ7+1*mm); 
    TGeoCompositeShape *compmagC7 = new TGeoCompositeShape("compMagC7", "MagC7Out-MagC7In");
    TGeoVolume *magC7   = new TGeoVolume("MagC7", compmagC7, iron);
    magC7->SetField(magFieldIron);
    magC7->SetLineColor(45);  // red-brown
    top->AddNode(magC7, 1, new TGeoTranslation(0, 0, Z7));
//Top/Bot return magnets for 36-42 m, note inner return magnet splits too :-)
    Double_t corners24[16] = {dXr36I,dY, dXr36I,dY+W36, dX36O,dY+W36, dX36O,dY, 
                            dXr42I,dY, dXr42I,dY+W42, dX42O,dY+W42, dX42O,dY}; 
    TGeoVolume *magTopLeft36t42 = gGeoManager->MakeArb8("MagTopLeft36t42", iron, dZ7, corners24) ;
    magTopLeft36t42->SetLineColor(38);  
    magTopLeft36t42->SetField(ConLField);
    top->AddNode(magTopLeft36t42, 1, new TGeoTranslation(0, 0, Z7 ));

    Double_t corners25[16] = {-dX36O,dY, -dX36O,dY+W36, -dXr36I, dY+W36, -dXr36I,dY,
                            -dX42O,dY, -dX42O,dY+W42, -dXr42I, dY+W42, -dXr42I,dY};
    TGeoVolume *magTopRight36t42 = gGeoManager->MakeArb8("MagTopRight36t42", iron, dZ7, corners25) ;
    magTopRight36t42->SetLineColor(30); 
    magTopRight36t42->SetField(ConRField);
    top->AddNode(magTopRight36t42, 1, new TGeoTranslation(0, 0, Z7 ));
//Bot return magnets 
    Double_t corners26[16] = {dXr36I,-dY-W36, dXr36I,-dY, dX36O,-dY, dX36O,-dY-W36, 
                            dXr42I,-dY-W42, dXr42I,-dY, dX42O,-dY, dX42O,-dY-W42};
    TGeoVolume *magBotLeft36t42 = gGeoManager->MakeArb8("MagBotLeft36t42", iron, dZ7, corners26) ;
    magBotLeft36t42->SetLineColor(30);  
    magBotLeft36t42->SetField(ConRField);
    top->AddNode(magBotLeft36t42, 1, new TGeoTranslation(0, 0, Z7 ));

    Double_t corners27[16] = {-dX36O,-dY-W36, -dX36O,-dY, -dXr36I,-dY, -dXr36I,-dY-W36, 
                            -dX42O,-dY-W42, -dX42O,-dY, -dXr42I,-dY, -dXr42I,-dY-W42};
    TGeoVolume *magBotRight36t42 = gGeoManager->MakeArb8("MagBotRight36t42", iron, dZ7, corners27) ;
    magBotRight36t42->SetLineColor(38); 
    magBotRight36t42->SetField(ConLField);
    top->AddNode(magBotRight36t42, 1, new TGeoTranslation(0, 0, Z7 ));

// 42<z<48 m: Note: here also return field splits!
    Double_t W48 = 0.75*m;
    Double_t dX48I = 1.75*m;
    Double_t dX48O = dX48I+W48;
    Double_t dXr48O = dX48I-dXgap;
    Double_t dXr48I = dXr48O-W48;
    
    Double_t Z8 = zEndOfAbsorb + 2*dZ1 + 2*dZ2 + 2*dZ3 + 2*dZ4+2*dZ5+2*dZ6+2*dZ7+dZ8;
    TGeoTrd1 *magC8rOut    = new TGeoTrd1("MagC8rOut", dXr42O,dXr48O, dY,      dZ8);       
    TGeoTrd1 *magC8rIn     = new TGeoTrd1("MagC8rIn",  dXr42I,dXr48I, dY+1*mm, dZ8+1*mm); 
    TGeoCompositeShape *compmagC8r = new TGeoCompositeShape("compMagC8r", "MagC8rOut-MagC8rIn");
    TGeoVolume *magRetC8   = new TGeoVolume("MagRetC8", compmagC8r, iron);
    magRetC8->SetLineColor(31);  // green-brown
    magRetC8->SetField(RetField);
    top->AddNode(magRetC8, 1, new TGeoTranslation(0, 0, Z8 ));

    TGeoTrd1 *magC8Out    = new TGeoTrd1("MagC8Out", dX42O,dX48O, dY,      dZ8);       
    TGeoTrd1 *magC8In     = new TGeoTrd1("MagC8In",  dX42I,dX48I, dY+1*mm, dZ8+1*mm); 
    TGeoCompositeShape *compmagC8 = new TGeoCompositeShape("compMagC8", "MagC8Out-MagC8In");
    TGeoVolume *magC8   = new TGeoVolume("MagC8", compmagC8, iron);
    magC8->SetField(magFieldIron);
    magC8->SetLineColor(45);  // red-brown
    top->AddNode(magC8, 1, new TGeoTranslation(0, 0, Z8));
//Top/Bot return magnets for 42-48 m, note inner return magnet splits too :-)
    Double_t corners28[16] = {dXr42I,dY, dXr42I,dY+W42, dX42O,dY+W42, dX42O,dY, 
                            dXr48I,dY, dXr48I,dY+W48, dX48O,dY+W48, dX48O,dY}; 
    TGeoVolume *magTopLeft42t48 = gGeoManager->MakeArb8("MagTopLeft42t48", iron, dZ8, corners28) ;
    magTopLeft42t48->SetLineColor(38);  
    magTopLeft42t48->SetField(ConLField);
    top->AddNode(magTopLeft42t48, 1, new TGeoTranslation(0, 0, Z8 ));

    Double_t corners29[16] = {-dX42O,dY, -dX42O,dY+W42, -dXr42I, dY+W42, -dXr42I,dY,
                            -dX48O,dY, -dX48O,dY+W48, -dXr48I, dY+W48, -dXr48I,dY};
    TGeoVolume *magTopRight42t48 = gGeoManager->MakeArb8("MagTopRight42t48", iron, dZ8, corners29) ;
    magTopRight42t48->SetLineColor(30); 
    magTopRight42t48->SetField(ConRField);
    top->AddNode(magTopRight42t48, 1, new TGeoTranslation(0, 0, Z8 ));
//Bot return magnets 
    Double_t corners30[16] = {dXr42I,-dY-W42, dXr42I,-dY, dX42O,-dY, dX42O,-dY-W42, 
                            dXr48I,-dY-W48, dXr48I,-dY, dX48O,-dY, dX48O,-dY-W48};
    TGeoVolume *magBotLeft42t48 = gGeoManager->MakeArb8("MagBotLeft42t48", iron, dZ8, corners30) ;
    magBotLeft42t48->SetLineColor(30);  
    magBotLeft42t48->SetField(ConRField);
    top->AddNode(magBotLeft42t48, 1, new TGeoTranslation(0, 0, Z8 ));

    Double_t corners31[16] = {-dX42O,-dY-W42, -dX42O,-dY, -dXr42I,-dY, -dXr42I,-dY-W42, 
                            -dX48O,-dY-W48, -dX48O,-dY, -dXr48I,-dY, -dXr48I,-dY-W48};
    TGeoVolume *magBotRight42t48 = gGeoManager->MakeArb8("MagBotRight42t48", iron, dZ8, corners31) ;
    magBotRight42t48->SetLineColor(38); 
    magBotRight42t48->SetField(ConLField);
    top->AddNode(magBotRight42t48, 1, new TGeoTranslation(0, 0, Z8 ));


// Concrete around first magnets
// Concrete around first magnets. i.e. Tunnel
    Double_t dZ = dZ1 + dZ2;
    Double_t dYT = dY+dX1;
    Double_t ZT  = zEndOfAbsorb + dZ;
    TGeoBBox *box1    = new TGeoBBox("box1",  1.6*m,dYT,dZ/2.);
    TGeoBBox *box2    = new TGeoBBox("box2", 10*m,10*m,dZ/2.);
    TGeoCompositeShape *compRockS = new TGeoCompositeShape("compRockS", "box2-box1");
    TGeoVolume *rockS   = new TGeoVolume("rockS", compRockS, concrete);
    rockS->SetLineColor(11);  // grey
    rockS->SetTransparency(50);
    top->AddNode(rockS, 1, new TGeoTranslation(0, 0, ZT ));

// around decay tunnel
    Double_t dZD =  100*m + fMuonShieldLength;
    TGeoBBox *box3    = new TGeoBBox("box3", 15*m,12.25*m,dZD/2.);
    TGeoBBox *box4    = new TGeoBBox("box4", 10*m, 10*m,dZD/2.);
    TGeoCompositeShape *compRockD = new TGeoCompositeShape("compRockD", "box3-box4");
    TGeoVolume *rockD   = new TGeoVolume("rockD", compRockD, concrete);
    rockD->SetLineColor(11);  // grey
    rockD->SetTransparency(50);
    top->AddNode(rockD, 1, new TGeoTranslation(0, 0, zEndOfAbsorb + 2*dZ + dZD/2.));

    }
    else if (fDesign==4||fDesign==5){


// Slightly improved from fDesign==3, longer/thicker MagB first magnets to 
// make sure more muons end up on the right polarity side.
// add here the additional 2m hadron shield, decided 17 october 2014
    // 2m more Absorber made of iron
    TGeoVolume *absorber = gGeoManager->MakeTube("AbsorberAdd", iron, 15, 400, dZ0);   
    absorber->SetLineColor(43);  
    top->AddNode(absorber, 1, new TGeoTranslation(0, 0, zEndOfAbsorb - dZ0));
    TGeoVolume *absorberCore = gGeoManager->MakeTube("AbsorberAddCore", tungsten, 0, 15, dZ0);   
    absorberCore->SetLineColor(38);  
    top->AddNode(absorberCore, 1, new TGeoTranslation(0, 0, zEndOfAbsorb - dZ0));

    Double_t ironField = 1.8*tesla;
    TGeoUniformMagField *magFieldIron = new TGeoUniformMagField(0.,ironField,0.);
    TGeoUniformMagField *RetField     = new TGeoUniformMagField(0.,-ironField,0.);
    TGeoUniformMagField *ConRField    = new TGeoUniformMagField(-ironField,0.,0.);
    TGeoUniformMagField *ConLField    = new TGeoUniformMagField(ironField,0.,0.);
 
// z<7m: just boxes, arguments are full length for python, half lengths for C++ 
    Double_t dX1 = 0.7*m; 
    Double_t dY  = 1.0*m;
    Double_t X2  = 1.25*m;   
    Double_t Z1  = zEndOfAbsorb + dZ1;
    TGeoVolume *magA = gGeoManager->MakeBox("MagA", iron, dX1, dY,dZ1);
    magA->SetLineColor(45);  // red-brown
    magA->SetField(magFieldIron);
    top->AddNode(magA, 1, new TGeoTranslation(0, 0, Z1 ));
 
    TGeoVolume *magRetA = gGeoManager->MakeBox("MagRetA", iron, dX1/2., dY, dZ1);
    magRetA->SetLineColor(31);  // green-brown
    magRetA->SetField(RetField);
    top->AddNode(magRetA, 1, new TGeoTranslation(-X2, 0, Z1 ));
    top->AddNode(magRetA, 1, new TGeoTranslation( X2, 0, Z1 ));

//  connection between field and return field, same thickness as width/2, i.e. dX1
//  15/10/2014: reduce thickness from 1.m to 0.7 m to maintain same flux everywhere.
    Double_t dYH1 = dX1/2.; 
    Double_t dXH1 = 0.5*(X2+dX1/2.);
    TGeoVolume  *magConALLT = gGeoManager->MakeBox("MagConALLT", iron,dXH1, dYH1, dZ1);
    magConALLT->SetLineColor(38);  
    magConALLT->SetField(ConLField);
    top->AddNode(magConALLT, 1, new TGeoTranslation(dXH1,dY+dYH1,Z1));
    TGeoVolume  *magConARRT = gGeoManager->MakeBox("MagConARRT", iron,dXH1, dYH1, dZ1);
    magConARRT->SetLineColor(30);  
    magConARRT->SetField(ConRField);
    top->AddNode(magConARRT, 1, new TGeoTranslation(-dXH1,dY+dYH1,Z1));
    TGeoVolume  *magConARLB = gGeoManager->MakeBox("MagConARLB", iron,dXH1, dYH1, dZ1);
    magConARLB->SetLineColor(30);  
    magConARLB->SetField(ConRField);
    top->AddNode(magConARLB, 1, new TGeoTranslation(dXH1,-(dY+dYH1),Z1));
    TGeoVolume  *magConALRB = gGeoManager->MakeBox("MagConALRB", iron,dXH1, dYH1, dZ1);
    magConALRB->SetLineColor(38);  
    magConALRB->SetField(ConLField);
    top->AddNode(magConALRB, 1, new TGeoTranslation(-dXH1,-(dY+dYH1),Z1));

// 7<z<19 m: (Kept the same names at fDesign==3, i.e. 7t17 :-)
    Double_t dX2 = 0.36*m;
    Double_t dX3 = 0.19*m;
    Double_t Z2 = zEndOfAbsorb + 2*dZ1 + dZ2;
    Double_t corners1[16] = {-dX2,-dY, -dX2,dY, dX2,dY, dX2,-dY,
                             -dX3,-dY, -dX3,dY, dX3,dY, dX3,-dY};
    TGeoVolume *magB = gGeoManager->MakeArb8("MagB", iron, dZ2, corners1) ;
    magB->SetLineColor(45);  
    magB->SetField(magFieldIron);
    top->AddNode(magB, 1, new TGeoTranslation(0, 0, Z2 ));

    Double_t corners2[16] = {1.6*m-dX2,-dY, 1.6*m-dX2,dY, 1.6*m,dY, 1.6*m,-dY, 
                             1.6*m-dX3,-dY, 1.6*m-dX3,dY, 1.6*m,dY, 1.6*m,-dY};
    TGeoVolume *magBRL = gGeoManager->MakeArb8("MagBRL", iron, dZ2, corners2) ;
    magBRL->SetLineColor(31);  
    magBRL->SetField(RetField);
    top->AddNode(magBRL, 1, new TGeoTranslation(0, 0, Z2 ));

    Double_t corners3[16] = {-1.6*m,-dY, -1.6*m,dY, -1.6*m+dX2,dY, -1.6*m+dX2,-dY, 
                             -1.6*m,-dY, -1.6*m,dY, -1.6*m+dX3,dY, -1.6*m+dX3,-dY};
    TGeoVolume *magBRR = gGeoManager->MakeArb8("MagBRR", iron, dZ2, corners3) ;
    magBRR->SetLineColor(31);  
    magBRR->SetField(RetField);
    top->AddNode(magBRR, 1, new TGeoTranslation(0, 0, Z2 ));

//Top/Bot return magnets for 7-17 m
//corners "first clockwise lower z, them clockwise upper z
    Double_t corners4[16] = {0.,dY, 0.,dY+dX2, 1.6*m,dY+dX2, 1.6*m,dY, 
                             0.,dY, 0.,dY+dX3, 1.6*m,dY+dX3, 1.6*m,dY};
    TGeoVolume *magTopLeft7t17 = gGeoManager->MakeArb8("MagTopLeft7t17", iron, dZ2, corners4) ;
    magTopLeft7t17->SetLineColor(38);  
    magTopLeft7t17->SetField(ConLField);
    top->AddNode(magTopLeft7t17, 1, new TGeoTranslation(0, 0, Z2 ));

    Double_t corners5[16] = {-1.6*m,dY, -1.6*m,dY+dX2, 0.,dY+dX2, 0.,dY, 
                             -1.6*m,dY, -1.6*m,dY+dX3, 0.,dY+dX3, 0.,dY};
    TGeoVolume *magTopRight7t17 = gGeoManager->MakeArb8("MagTopRight7t17", iron, dZ2, corners5) ;
    magTopRight7t17->SetLineColor(30); 
    magTopRight7t17->SetField(ConRField);
    top->AddNode(magTopRight7t17, 1, new TGeoTranslation(0, 0, Z2 ));
//Bot return magnets for 7-17 m
    Double_t corners6[16] = {0.,-dY-dX2, 0.,-dY, 1.6*m,-dY, 1.6*m,-dY-dX2, 
                             0.,-dY-dX3, 0.,-dY, 1.6*m,-dY, 1.6*m,-dY-dX3};
    TGeoVolume *magBotLeft7t17 = gGeoManager->MakeArb8("MagBotLeft7t17", iron, dZ2, corners6) ;
    magBotLeft7t17->SetLineColor(30);  
    magBotLeft7t17->SetField(ConRField);
    top->AddNode(magBotLeft7t17, 1, new TGeoTranslation(0, 0, Z2 ));

    Double_t corners7[16] = {-1.6*m,-dY-dX2, -1.6*m,-dY, 0.,-dY, 0.,-dY-dX2, -1.6*m,-dY-dX3, -1.6*m,-dY, 0.,-dY, 0.,-dY-dX3};
    TGeoVolume *magBotRight7t17 = gGeoManager->MakeArb8("MagBotRight7t17", iron, dZ2, corners7) ;
    magBotRight7t17->SetLineColor(38); 
    magBotRight7t17->SetField(ConLField);
    top->AddNode(magBotRight7t17, 1, new TGeoTranslation(0, 0, Z2 ));
   

// 19<z<24 m: (again kept the "old" name)
    Double_t dX17 =  0.075*m;
    Double_t dX24 =  0.25*m;
    Double_t Z3  = zEndOfAbsorb + 2*dZ1 + 2*dZ2 + dZ3;
    TGeoVolume *magRetC1 = gGeoManager->MakeTrd1("MagRetC1", iron, dX17, dX24, dY, dZ3);
    magRetC1->SetLineColor(31);  // green-brown
    magRetC1->SetField(RetField);
    top->AddNode(magRetC1, 1, new TGeoTranslation(0, 0, Z3 ));
     
    TGeoTrd1 *magC1T    = new TGeoTrd1("MagC1T",2*dX17, 2*dX24, dY-0.1*mm, dZ3-0.1*mm);    
    TGeoTrd1 *magRetC1T = new TGeoTrd1("MagRetC1T",dX17, dX24, dY, dZ3);        
    TGeoCompositeShape *compmagC1 = new TGeoCompositeShape("compMagC1", "MagC1T-MagRetC1T");
    TGeoVolume *magC1   = new TGeoVolume("MagC1", compmagC1, iron);
    magC1->SetLineColor(45);  // red-brown
    top->AddNode(magC1, 1, new TGeoTranslation(0, 0, Z3));
//Top/Bot return magnets for 17-24 m
    Double_t corners8[16] = {0.,dY, 0.,dY+dX17, 2*dX17,dY+dX17, 2*dX17,dY, 
                             0.,dY, 0.,dY+dX24, 2*dX24,dY+dX24, 2*dX24,dY}; 
    TGeoVolume *magTopLeft17t24 = gGeoManager->MakeArb8("MagTopLeft17t24", iron, dZ3, corners8) ;
    magTopLeft17t24->SetLineColor(38);  
    magTopLeft17t24->SetField(ConLField);
    top->AddNode(magTopLeft17t24, 1, new TGeoTranslation(0, 0, Z3 ));

    Double_t corners9[16] = {-2*dX17,dY, -2*dX17,dY+dX17, 0., dY+dX17, 0.,dY,
                             -2*dX24,dY, -2*dX24,dY+dX24, 0., dY+dX24, 0.,dY};
    TGeoVolume *magTopRight17t24 = gGeoManager->MakeArb8("MagTopRight17t24", iron, dZ3, corners9) ;
    magTopRight17t24->SetLineColor(30); 
    magTopRight17t24->SetField(ConRField);
    top->AddNode(magTopRight17t24, 1, new TGeoTranslation(0, 0, Z3 ));
//Bot return magnets 
    Double_t corners10[16] = {0.,-dY-dX17, 0.,-dY, 2*dX17,-dY, 2*dX17,-dY-dX17, 
                              0.,-dY-dX24, 0.,-dY, 2*dX24,-dY, 2*dX24,-dY-dX24};
    TGeoVolume *magBotLeft17t24 = gGeoManager->MakeArb8("MagBotLeft17t24", iron, dZ3, corners10) ;
    magBotLeft17t24->SetLineColor(30);  
    magBotLeft17t24->SetField(ConRField);
    top->AddNode(magBotLeft17t24, 1, new TGeoTranslation(0, 0, Z3 ));

    Double_t corners11[16] = {-2*dX17,-dY-dX17, -2*dX17,-dY, 0.,-dY, 0.,-dY-dX17, 
                              -2*dX24,-dY-dX24, -2*dX24,-dY, 0.,-dY, 0.,-dY-dX24};
    TGeoVolume *magBotRight17t24 = gGeoManager->MakeArb8("MagBotRight17t24", iron, dZ3, corners11) ;
    magBotRight17t24->SetLineColor(38); 
    magBotRight17t24->SetField(ConLField);
    top->AddNode(magBotRight17t24, 1, new TGeoTranslation(0, 0, Z3 ));

// 24<z<30. m, gap between field and return field      
    Double_t dX30I = 0.55*m;
    Double_t W30 = 0.3*m;
    Double_t Z4 = zEndOfAbsorb + 2*dZ1 + 2*dZ2 + 2*dZ3 + dZ4;
    TGeoVolume *magRetC4 = gGeoManager->MakeTrd1("MagRetC4", iron, dX24, W30, dY, dZ4);
    magRetC4->SetLineColor(31);  // green-brown
    magRetC4->SetField(RetField);
    top->AddNode(magRetC4, 1, new TGeoTranslation(0, 0, Z4 ));

    TGeoTrd1 *magC4Out    = new TGeoTrd1("MagC4Out", 2*dX24,W30+dX30I,  dY,      dZ4);       
    TGeoTrd1 *magC4In     = new TGeoTrd1("MagC4In",    dX24,     dX30I,dY+1*mm, dZ4+1*mm); 
    TGeoCompositeShape *compmagC4 = new TGeoCompositeShape("compMagC4", "MagC4Out-MagC4In");
    TGeoVolume *magC4   = new TGeoVolume("MagC4", compmagC4, iron);
    magC4->SetField(magFieldIron);
    magC4->SetLineColor(45);  // red-brown
    top->AddNode(magC4, 1, new TGeoTranslation(0, 0, Z4));
//Top/Bot return magnets for 24-28 m
    Double_t corners12[16] = {0.,dY, 0.,dY+dX24, 2*dX24,dY+dX24, 2*dX24,dY, 
                              0.,dY, 0.,dY+W30, W30+dX30I,dY+W30, W30+dX30I,dY}; 
    TGeoVolume *magTopLeft24t28 = gGeoManager->MakeArb8("MagTopLeft24t28", iron, dZ4, corners12) ;
    magTopLeft24t28->SetLineColor(38);  
    magTopLeft24t28->SetField(ConLField);
    top->AddNode(magTopLeft24t28, 1, new TGeoTranslation(0, 0, Z4 ));

    Double_t corners13[16] = {-2*dX24,dY, -2*dX24,dY+dX24, 0., dY+dX24, 0.,dY,
                              -W30-dX30I,dY,-W30-dX30I,dY+W30, 0.,dY+W30, 0.,dY}; 
    TGeoVolume *magTopRight24t28 = gGeoManager->MakeArb8("MagTopRight24t28", iron, dZ4, corners13) ;
    magTopRight24t28->SetLineColor(30); 
    magTopRight24t28->SetField(ConRField);
    top->AddNode(magTopRight24t28, 1, new TGeoTranslation(0, 0, Z4 ));
//Bot return magnets 
    Double_t corners14[16] = {0.,-dY-dX24, 0.,-dY, 2*dX24,-dY, 2*dX24,-dY-dX24, 
                              0.,-dY-W30, 0.,-dY, W30+dX30I,-dY, W30+dX30I,-dY-W30};
    TGeoVolume *magBotLeft24t28 = gGeoManager->MakeArb8("MagBotLeft24t28", iron, dZ4, corners14) ;
    magBotLeft24t28->SetLineColor(30);  
    magBotLeft24t28->SetField(ConRField);
    top->AddNode(magBotLeft24t28, 1, new TGeoTranslation(0, 0, Z4 ));

    Double_t corners15[16] = {-2*dX24,-dY-dX24, -2*dX24,-dY, 0.,-dY, 0.,-dY-dX24, 
                              -W30-dX30I,-dY-W30,  -W30-dX30I,-dY, 0.,-dY, 0.,-dY-W30};
    TGeoVolume *magBotRight24t28 = gGeoManager->MakeArb8("MagBotRight24t28", iron, dZ4, corners15) ;
    magBotRight24t28->SetLineColor(38); 
    magBotRight24t28->SetField(ConLField);
    top->AddNode(magBotRight24t28, 1, new TGeoTranslation(0, 0, Z4 ));

// 30<z<36 m: Note: here also return field splits!
    Double_t dX30O = dX30I+W30;
    Double_t dXr30O = dX30I-dXgap;
    Double_t dXr30I = dXr30O-W30;
    Double_t W36 = 0.4*m;
    Double_t dX36I = 0.85*m;
    Double_t dX36O = dX36I+W36;
    Double_t dXr36O = dX36I-dXgap;
    Double_t dXr36I = dXr36O-W36;

    Double_t Z6 = zEndOfAbsorb + 2*dZ1 + 2*dZ2 + 2*dZ3 + 2*dZ4+2*dZ5+dZ6;
    TGeoTrd1 *magC6rOut    = new TGeoTrd1("MagC6rOut", dXr30O,dXr36O, dY,      dZ6);       
    TGeoTrd1 *magC6rIn     = new TGeoTrd1("MagC6rIn",  dXr30I,dXr36I, dY+1*mm, dZ6+1*mm); 
    TGeoCompositeShape *compmagC6r = new TGeoCompositeShape("compMagC6r", "MagC6rOut-MagC6rIn");
    TGeoVolume *magRetC6   = new TGeoVolume("MagRetC6", compmagC6r, iron);
    magRetC6->SetLineColor(31);  // green-brown
    magRetC6->SetField(RetField);
    top->AddNode(magRetC6, 1, new TGeoTranslation(0, 0, Z6 ));

    TGeoTrd1 *magC6Out    = new TGeoTrd1("MagC6Out", dX30O,dX36O, dY,      dZ6);       
    TGeoTrd1 *magC6In     = new TGeoTrd1("MagC6In",  dX30I,dX36I, dY+1*mm, dZ6+1*mm); 
    TGeoCompositeShape *compmagC6 = new TGeoCompositeShape("compMagC6", "MagC6Out-MagC6In");
    TGeoVolume *magC6   = new TGeoVolume("MagC6", compmagC6, iron);
    magC6->SetField(magFieldIron);
    magC6->SetLineColor(45);  // red-brown
    top->AddNode(magC6, 1, new TGeoTranslation(0, 0, Z6));
//Top/Bot return magnets for 30-36 m, note inner return magnet splits too :-)
    Double_t corners20[16] = {dXr30I,dY, dXr30I,dY+W30, dX30O,dY+W30, dX30O,dY, 
                            dXr36I,dY, dXr36I,dY+W36, dX36O,dY+W36, dX36O,dY}; 
    TGeoVolume *magTopLeft30t36 = gGeoManager->MakeArb8("MagTopLeft30t36", iron, dZ6, corners20) ;
    magTopLeft30t36->SetLineColor(38);  
    magTopLeft30t36->SetField(ConLField);
    top->AddNode(magTopLeft30t36, 1, new TGeoTranslation(0, 0, Z6 ));

    Double_t corners21[16] = {-dX30O,dY, -dX30O,dY+W30, -dXr30I, dY+W30, -dXr30I,dY,
                            -dX36O,dY, -dX36O,dY+W36, -dXr36I, dY+W36, -dXr36I,dY};
    TGeoVolume *magTopRight30t36 = gGeoManager->MakeArb8("MagTopRight30t36", iron, dZ6, corners21) ;
    magTopRight30t36->SetLineColor(30); 
    magTopRight30t36->SetField(ConRField);
    top->AddNode(magTopRight30t36, 1, new TGeoTranslation(0, 0, Z6 ));
//Bot return magnets 
    Double_t corners22[16] = {dXr30I,-dY-W30, dXr30I,-dY, dX30O,-dY, dX30O,-dY-W30, 
                            dXr36I,-dY-W36, dXr36I,-dY, dX36O,-dY, dX36O,-dY-W36};
    TGeoVolume *magBotLeft30t36 = gGeoManager->MakeArb8("MagBotLeft30t36", iron, dZ6, corners22) ;
    magBotLeft30t36->SetLineColor(30);  
    magBotLeft30t36->SetField(ConRField);
    top->AddNode(magBotLeft30t36, 1, new TGeoTranslation(0, 0, Z6 ));

    Double_t corners23[16] = {-dX30O,-dY-W30, -dX30O,-dY, -dXr30I,-dY, -dXr30I,-dY-W30, 
                            -dX36O,-dY-W36, -dX36O,-dY, -dXr36I,-dY, -dXr36I,-dY-W36};
    TGeoVolume *magBotRight30t36 = gGeoManager->MakeArb8("MagBotRight30t36", iron, dZ6, corners23) ;
    magBotRight30t36->SetLineColor(38); 
    magBotRight30t36->SetField(ConLField);
    top->AddNode(magBotRight30t36, 1, new TGeoTranslation(0, 0, Z6 ));

// 36<z<42 m: Note: here also return field splits!
    Double_t W42 = 0.4*m;
    Double_t dX42I = 1.25*m;
    Double_t dX42O = dX42I+W42;
    Double_t dXr42O = dX42I-dXgap;
    Double_t dXr42I = dXr42O-W42;

    
    Double_t Z7 = zEndOfAbsorb + 2*dZ1 + 2*dZ2 + 2*dZ3 + 2*dZ4+2*dZ5+2*dZ6+dZ7;
    TGeoTrd1 *magC7rOut    = new TGeoTrd1("MagC7rOut", dXr36O,dXr42O, dY,      dZ7);       
    TGeoTrd1 *magC7rIn     = new TGeoTrd1("MagC7rIn",  dXr36I,dXr42I, dY+1*mm, dZ7+1*mm); 
    TGeoCompositeShape *compmagC7r = new TGeoCompositeShape("compMagC7r", "MagC7rOut-MagC7rIn");
    TGeoVolume *magRetC7   = new TGeoVolume("MagRetC7", compmagC7r, iron);
    magRetC7->SetLineColor(31);  // green-brown
    magRetC7->SetField(RetField);
    top->AddNode(magRetC7, 1, new TGeoTranslation(0, 0, Z7 ));

    TGeoTrd1 *magC7Out    = new TGeoTrd1("MagC7Out", dX36O,dX42O, dY,      dZ7);       
    TGeoTrd1 *magC7In     = new TGeoTrd1("MagC7In",  dX36I,dX42I, dY+1*mm, dZ7+1*mm); 
    TGeoCompositeShape *compmagC7 = new TGeoCompositeShape("compMagC7", "MagC7Out-MagC7In");
    TGeoVolume *magC7   = new TGeoVolume("MagC7", compmagC7, iron);
    magC7->SetField(magFieldIron);
    magC7->SetLineColor(45);  // red-brown
    top->AddNode(magC7, 1, new TGeoTranslation(0, 0, Z7));
//Top/Bot return magnets for 36-42 m, note inner return magnet splits too :-)
    Double_t corners24[16] = {dXr36I,dY, dXr36I,dY+W36, dX36O,dY+W36, dX36O,dY, 
                            dXr42I,dY, dXr42I,dY+W42, dX42O,dY+W42, dX42O,dY}; 
    TGeoVolume *magTopLeft36t42 = gGeoManager->MakeArb8("MagTopLeft36t42", iron, dZ7, corners24) ;
    magTopLeft36t42->SetLineColor(38);  
    magTopLeft36t42->SetField(ConLField);
    top->AddNode(magTopLeft36t42, 1, new TGeoTranslation(0, 0, Z7 ));

    Double_t corners25[16] = {-dX36O,dY, -dX36O,dY+W36, -dXr36I, dY+W36, -dXr36I,dY, -dX42O,dY, -dX42O,dY+W42, -dXr42I, dY+W42, -dXr42I,dY};
    TGeoVolume *magTopRight36t42 = gGeoManager->MakeArb8("MagTopRight36t42", iron, dZ7, corners25) ;
    magTopRight36t42->SetLineColor(30); 
    magTopRight36t42->SetField(ConRField);
    top->AddNode(magTopRight36t42, 1, new TGeoTranslation(0, 0, Z7 ));
//Bot return magnets 
    Double_t corners26[16] = {dXr36I,-dY-W36, dXr36I,-dY, dX36O,-dY, dX36O,-dY-W36, 
                            dXr42I,-dY-W42, dXr42I,-dY, dX42O,-dY, dX42O,-dY-W42};
    TGeoVolume *magBotLeft36t42 = gGeoManager->MakeArb8("MagBotLeft36t42", iron, dZ7, corners26) ;
    magBotLeft36t42->SetLineColor(30);  
    magBotLeft36t42->SetField(ConRField);
    top->AddNode(magBotLeft36t42, 1, new TGeoTranslation(0, 0, Z7 ));

    Double_t corners27[16] = {-dX36O,-dY-W36, -dX36O,-dY, -dXr36I,-dY, -dXr36I,-dY-W36, 
                            -dX42O,-dY-W42, -dX42O,-dY, -dXr42I,-dY, -dXr42I,-dY-W42};
    TGeoVolume *magBotRight36t42 = gGeoManager->MakeArb8("MagBotRight36t42", iron, dZ7, corners27) ;
    magBotRight36t42->SetLineColor(38); 
    magBotRight36t42->SetField(ConLField);
    top->AddNode(magBotRight36t42, 1, new TGeoTranslation(0, 0, Z7 ));

// 42<z<48 m: Note: here also return field splits!
    Double_t W48 = 0.75*m;
    Double_t dX48I = 1.7*m;
    Double_t dX48O = dX48I+W48;
    Double_t dXr48O = dX48I-dXgap;
    Double_t dXr48I = dXr48O-W48;
    
    Double_t Z8 = zEndOfAbsorb + 2*dZ1 + 2*dZ2 + 2*dZ3 + 2*dZ4+2*dZ5+2*dZ6+2*dZ7+dZ8;
    TGeoTrd1 *magC8rOut    = new TGeoTrd1("MagC8rOut", dXr42O,dXr48O, dY,      dZ8);       
    TGeoTrd1 *magC8rIn     = new TGeoTrd1("MagC8rIn",  dXr42I,dXr48I, dY+1*mm, dZ8+1*mm); 
    TGeoCompositeShape *compmagC8r = new TGeoCompositeShape("compMagC8r", "MagC8rOut-MagC8rIn");
    TGeoVolume *magRetC8   = new TGeoVolume("MagRetC8", compmagC8r, iron);
    magRetC8->SetLineColor(31);  // green-brown
    magRetC8->SetField(RetField);
    top->AddNode(magRetC8, 1, new TGeoTranslation(0, 0, Z8 ));

    TGeoTrd1 *magC8Out    = new TGeoTrd1("MagC8Out", dX42O,dX48O, dY,      dZ8);       
    TGeoTrd1 *magC8In     = new TGeoTrd1("MagC8In",  dX42I,dX48I, dY+1*mm, dZ8+1*mm); 
    TGeoCompositeShape *compmagC8 = new TGeoCompositeShape("compMagC8", "MagC8Out-MagC8In");
    TGeoVolume *magC8   = new TGeoVolume("MagC8", compmagC8, iron);
    magC8->SetField(magFieldIron);
    magC8->SetLineColor(45);  // red-brown
    top->AddNode(magC8, 1, new TGeoTranslation(0, 0, Z8));
//Top/Bot return magnets for 42-48 m, note inner return magnet splits too :-)
    Double_t corners28[16] = {dXr42I,dY, dXr42I,dY+W42, dX42O,dY+W42, dX42O,dY, 
                            dXr48I,dY, dXr48I,dY+W48, dX48O,dY+W48, dX48O,dY}; 
    TGeoVolume *magTopLeft42t48 = gGeoManager->MakeArb8("MagTopLeft42t48", iron, dZ8, corners28) ;
    magTopLeft42t48->SetLineColor(38);  
    magTopLeft42t48->SetField(ConLField);
    top->AddNode(magTopLeft42t48, 1, new TGeoTranslation(0, 0, Z8 ));

    Double_t corners29[16] = {-dX42O,dY, -dX42O,dY+W42, -dXr42I, dY+W42, -dXr42I,dY,
                            -dX48O,dY, -dX48O,dY+W48, -dXr48I, dY+W48, -dXr48I,dY};
    TGeoVolume *magTopRight42t48 = gGeoManager->MakeArb8("MagTopRight42t48", iron, dZ8, corners29) ;
    magTopRight42t48->SetLineColor(30); 
    magTopRight42t48->SetField(ConRField);
    top->AddNode(magTopRight42t48, 1, new TGeoTranslation(0, 0, Z8 ));
//Bot return magnets 
    Double_t corners30[16] = {dXr42I,-dY-W42, dXr42I,-dY, dX42O,-dY, dX42O,-dY-W42, 
                            dXr48I,-dY-W48, dXr48I,-dY, dX48O,-dY, dX48O,-dY-W48};
    TGeoVolume *magBotLeft42t48 = gGeoManager->MakeArb8("MagBotLeft42t48", iron, dZ8, corners30) ;
    magBotLeft42t48->SetLineColor(30);  
    magBotLeft42t48->SetField(ConRField);
    top->AddNode(magBotLeft42t48, 1, new TGeoTranslation(0, 0, Z8 ));

    Double_t corners31[16] = {-dX42O,-dY-W42, -dX42O,-dY, -dXr42I,-dY, -dXr42I,-dY-W42, 
                            -dX48O,-dY-W48, -dX48O,-dY, -dXr48I,-dY, -dXr48I,-dY-W48};
    TGeoVolume *magBotRight42t48 = gGeoManager->MakeArb8("MagBotRight42t48", iron, dZ8, corners31) ;
    magBotRight42t48->SetLineColor(38); 
    magBotRight42t48->SetField(ConLField);
    top->AddNode(magBotRight42t48, 1, new TGeoTranslation(0, 0, Z8 ));

    Double_t ZGmid=Z8+dZ8+2.25*m+0.2*m;
    if (fDesign==4){
//Add the Goliath magnet.
//4 Pillars
     TGeoVolume *pillarG = gGeoManager->MakeBox("PillarG", iron, 0.45*m,0.75*m,0.675*m);
     magA->SetLineColor(45);  // red-brown
    /// put the 4 pillars in place:
     Double_t ZGpillar1=Z8+dZ8+0.675*m+0.2*m;
     Double_t ZGpillar2=ZGpillar1+3.15*m;
     top->AddNode(pillarG, 1, new TGeoTranslation(-1.35*m, 0, ZGpillar1));
     top->AddNode(pillarG, 1, new TGeoTranslation(1.35*m, 0, ZGpillar1));
     top->AddNode(pillarG, 1, new TGeoTranslation(-1.35*m, 0, ZGpillar2));
     top->AddNode(pillarG, 1, new TGeoTranslation(1.35*m, 0, ZGpillar2));
//Top/bottom plates
     TGeoVolume *plateG = gGeoManager->MakeBox("PlateG", iron, 1.8*m,0.5*m,2.25*m);
     magA->SetLineColor(45);  // red-brown
    /// put the 4 pillars in place:
     top->AddNode(plateG, 1, new TGeoTranslation(0., 1.25*m, ZGmid));
     top->AddNode(plateG, 1, new TGeoTranslation(0., -1.25*m, ZGmid));
//Add  rough nu-tau Mu-Spec...  for the moment keep it until Annarita has a replacement
     Double_t sz = ZGmid+2.25*m+0.2*m+2.45*m;
     Double_t dIronOpera= 0.3*m;
     TGeoVolume *muNuTau = gGeoManager->MakeBox("MuNuTau", iron, 2.3*m, 4.*m, dIronOpera);
     muNuTau->SetLineColor(5);
     top->AddNode(muNuTau, 1, new TGeoTranslation(0, 0, sz-0.91*m));
     top->AddNode(muNuTau, 1, new TGeoTranslation(0, 0, sz+0.91*m));
    }


// Concrete around first magnets
// Concrete around first magnets. i.e. Tunnel
    Double_t dZ = dZ1 + dZ2;
    Double_t dYT = dY+dX1;
    Double_t ZT  = zEndOfAbsorb + dZ;
    TGeoBBox *box1    = new TGeoBBox("box1",  1.6*m,dYT,dZ);
    TGeoBBox *box2    = new TGeoBBox("box2", 10*m,10*m,dZ);
    TGeoCompositeShape *compRockS = new TGeoCompositeShape("compRockS", "box2-box1");
    TGeoVolume *rockS   = new TGeoVolume("rockS", compRockS, concrete);
    rockS->SetLineColor(11);  // grey
    rockS->SetTransparency(50);
    top->AddNode(rockS, 1, new TGeoTranslation(0, 0, ZT ));

// around decay tunnel
    Double_t dZD =  100*m + fMuonShieldLength;
    TGeoBBox *box3    = new TGeoBBox("box3", 15*m,12.25*m,dZD/2.);
    TGeoBBox *box4    = new TGeoBBox("box4", 10*m, 10*m,dZD/2.);
    TGeoCompositeShape *compRockD = new TGeoCompositeShape("compRockD", "box3-box4");
    TGeoVolume *rockD   = new TGeoVolume("rockD", compRockD, concrete);
    rockD->SetLineColor(11);  // grey
    rockD->SetTransparency(50);
    top->AddNode(rockD, 1, new TGeoTranslation(0, 0, zEndOfAbsorb + 2*dZ + dZD/2.));


//
    } else {
     cout << "design does not match implemented designs" << endl;
    }
}

ClassImp(ShipMuonShield)








