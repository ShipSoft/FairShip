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
                               Double_t Z, Double_t L1, Double_t L2, Double_t L3, Double_t L4, Double_t L5, Double_t L6, Double_t LE)
  : FairModule(name ,Title)
{
 fDesign = Design;
 if (fDesign==1){
    // passive design with tungsten and lead
     fMuonShieldLength = L1;   
    }
 if (fDesign==2){
     dZ1 = L1;
     dZ2 = L2;
     dZ3 = L3;
     dZ4 = L4;
     dZ5 = L5;
     dZ6 = L6;
     fMuonShieldLength = 2*(dZ1+dZ2+dZ3+dZ4+dZ5+dZ6) + LE ; //leave some space for nu-tau detector   
    }
 zEndOfAbsorb = Z - fMuonShieldLength/2.;

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
    }
    else {
     cout << "design does not match implemented designs" << endl;
    }



}

ClassImp(ShipMuonShield)








