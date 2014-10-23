#include "ShipGoliath.h"

#include "TGeoManager.h"
#include "FairRun.h"                    // for FairRun
#include "FairRuntimeDb.h"              // for FairRuntimeDb
//#include "FairGeoMedia.h"
//#include "FairGeoBuilder.h"

#include "Riosfwd.h"                    // for ostream
#include "TList.h"                      // for TListIter, TList (ptr only)
#include "TObjArray.h"                  // for TObjArray
#include "TString.h"                    // for TString
#include "TGeoBBox.h"
#include "TGeoTrd1.h"
#include "TGeoArb8.h"
#include "TGeoCompositeShape.h"
#include "TGeoTube.h"
#include "TGeoMaterial.h"
#include "TGeoElement.h"
#include "TGeoMedium.h"
#include <stddef.h>                     // for NULL
#include <iostream>                     // for operator<<, basic_ostream, etc

using namespace std;

ShipGoliath::~ShipGoliath()
{
}

ShipGoliath::ShipGoliath()
  : FairModule("ShipGoliath", "")
{
}

ShipGoliath::ShipGoliath(const char* name, const char* Title)
  : FairModule(name ,Title)
{
}

void ShipGoliath::ConstructGeometry()
{

    TGeoVolume *top=gGeoManager->GetTopVolume();
    TGeoMedium *Fe  = gGeoManager->GetMedium("iron");
    
    //
    //******* UPPER AND LOWER BASE *******
    //
    
    TGeoBBox *TopS = new TGeoBBox(180,57/2,225);
    TGeoVolume *volTopS = new TGeoVolume("volTopS",TopS,Fe);
    volTopS->SetLineColor(kRed);
    volTopS->SetTransparency(7);
    Int_t d = -3247;
    top->AddNode(volTopS,1,new TGeoTranslation(0, 126, d)); //upper part
    top->AddNode(volTopS,2,new TGeoTranslation(0, -111, d)); //lower part
    
    
    //*******************************************************************
    //**************************** MAGNETS ******************************
    //*******************************************************************

    
    
    TGeoRotation *r1 = new TGeoRotation();
    r1->SetAngles(0,90,0);
    TGeoCombiTrans t(0, 75, d,r1);
    t.Print();
    TGeoHMatrix *m = new TGeoHMatrix(t);
    //m->Print();
    
    
    TGeoTube *magnetUp = new TGeoTube(90,160,22.5);
    TGeoVolume *volmagnetUp = new TGeoVolume("volmagnetUp",magnetUp,Fe);
    volmagnetUp->SetLineColor(kGreen);
    top->AddNode(volmagnetUp,1,m); //upper part
    
    
    TGeoCombiTrans t1(0, -67.5, d,r1);
    TGeoHMatrix *m1 = new TGeoHMatrix(t1);
    
    
    TGeoTube *magnetDown = new TGeoTube(90,160,15);
    TGeoVolume *volmagnetDown = new TGeoVolume("volmagnetDown",magnetDown,Fe);
    volmagnetDown->SetLineColor(kGreen);
    top->AddNode(volmagnetDown,1,m1); //lower part

    
    //*******************************************************************
    //********************* LATERAL SURFACES ****************************
    //*******************************************************************
    
    Double_t side1 = 360, side2 = 450;  //side1 = short side, side2 = long side
    Double_t base1 = 135/2, base2 = 78/2; //basis of the trapezoid
    
    
 /*
    TGeoBBox *LateralSurface1 = new TGeoBBox("LateralSurface1",16.5,180/2,67.5);
    TGeoTranslation *tr1 = new TGeoTranslation(180-16.5, 14.5/2, -3246.5);
    tr1->SetName("tr1");
    tr1->RegisterYourself();

    TGeoTrd1 *LateralSurface2 = new TGeoTrd1("LateralSurface2",base1, base2, 45/2, 57/2);
    TGeoTranslation *tr2 = new TGeoTranslation(180-33-28.5, 14.5/2, -3275);
    tr2->SetName("tr2");
    tr2->RegisterYourself();
    
    */
    
    //***** SIDE Left Front ****
    
    //LONGER RECTANGLE
    TGeoBBox *LateralS1 = new TGeoBBox("LateralS1",16.5,45/2,67.5);
    TGeoTranslation *tr1 = new TGeoTranslation(-side1/2 +33/2, 75, d - side2/2 +135/2);
    TGeoVolume *volLateralS1 = new TGeoVolume("volLateralS1",LateralS1,Fe);
    volLateralS1->SetLineColor(kRed);
    top->AddNode(volLateralS1, 1, tr1);
    
    //TRAPEZOID
    
    TGeoArb8 *LateralS2 = new TGeoArb8("LateralS2",45/2);
    LateralS2->SetVertex(0, 33, 0);
    LateralS2->SetVertex(1, 90, 0);
    LateralS2->SetVertex(2, 90, 78);
    LateralS2->SetVertex(3, 33, 135);
    LateralS2->SetVertex(4, 33, 0);
    LateralS2->SetVertex(5, 90, 0);
    LateralS2->SetVertex(6, 90, 78);
    LateralS2->SetVertex(7, 33, 135);

    TGeoVolume *volLateralS2 = new TGeoVolume("volLateralS2",LateralS2,Fe);
    volLateralS2->SetLineColor(kRed);
    
    TGeoRotation *r2 = new TGeoRotation();
    r2->SetAngles(0,90,0);
    TGeoCombiTrans tr2(-side1/2, 75, d-side2/2,r2);
    TGeoHMatrix *m2 = new TGeoHMatrix(tr2);
    top->AddNode(volLateralS2, 1, m2);

    //LOWER LATERAL SURFACE
    
    //LONGER RECTANGLE
    TGeoBBox *LateralSurface1low = new TGeoBBox("LateralSurface1low",33/2,135/2,125/2);
    TGeoTranslation *tr1low = new TGeoTranslation(-side1/2 +33/2, -15, d - side2/2 +125/2);
    tr1low->SetName("tr1low");
    tr1low->RegisterYourself();
    
    //SHORTER RECTANGLE
    TGeoBBox *LateralSurface2low = new TGeoBBox("LateralSurface2low",28.5,135/2,78/2);
    TGeoTranslation *tr2low = new TGeoTranslation(-side1/2 + (90-33)/2 + 33, -15, d -side2/2 +78/2);
    tr2low->SetName("tr2low");
    tr2low->RegisterYourself();
    
    TGeoCompositeShape *LateralSurfacelow = new TGeoCompositeShape("LateralSurfacelow", "LateralSurface1low:tr1low+LateralSurface2low:tr2low");
    TGeoVolume *volLateralSurfacelow = new TGeoVolume("volLateralSurfacelow",LateralSurfacelow,Fe);
    
    volLateralSurfacelow->SetLineColor(kRed);
    top->AddNode(volLateralSurfacelow, 1, new TGeoTranslation(0,0,0));
    
    
    
    //***** SIDE Right Front ****
    
    //LONGER RECTANGLE
    TGeoBBox *LateralS1_b = new TGeoBBox("LateralS1_b",16.5,45/2,67.5);
    TGeoTranslation *tr1_b = new TGeoTranslation(-side1/2 +33/2, 75, d + side2/2 - 135/2);
    TGeoVolume *volLateralS1_b = new TGeoVolume("volLateralS1_b",LateralS1_b,Fe);
    volLateralS1_b->SetLineColor(kRed);
    top->AddNode(volLateralS1_b, 1, tr1_b);
    
    //TRAPEZOID
    TGeoArb8 *LateralS2_b = new TGeoArb8("LateralS2_b",45/2);
    LateralS2_b ->SetVertex(0, 33, 0);
    LateralS2_b ->SetVertex(1, 90, 0);
    LateralS2_b ->SetVertex(2, 90, 78);
    LateralS2_b ->SetVertex(3, 33, 135);
    LateralS2_b ->SetVertex(4, 33, 0);
    LateralS2_b ->SetVertex(5, 90, 0);
    LateralS2_b ->SetVertex(6, 90, 78);
    LateralS2_b ->SetVertex(7, 33, 135);
    
    TGeoVolume *volLateralS2_b = new TGeoVolume("volLateralS2_b",LateralS2_b,Fe);
    volLateralS2_b->SetLineColor(kRed);
    
    TGeoRotation *r2_b = new TGeoRotation();
    r2_b->SetAngles(0,270,0);
    TGeoCombiTrans tr2_b(-side1/2, 75, d+side2/2,r2_b);
    TGeoHMatrix *m2_b = new TGeoHMatrix(tr2_b);
    top->AddNode(volLateralS2_b, 1, m2_b);

    //LOWER LATERAL SURFACE
    
    //LONGER RECTANGLE
    TGeoBBox *LateralSurface1dlow = new TGeoBBox("LateralSurface1dlow",33/2,135/2,125/2);
    TGeoTranslation *tr1dlow = new TGeoTranslation(-side1/2 +33/2, -15, d + side2/2 -125/2);
    tr1dlow->SetName("tr1dlow");
    tr1dlow->RegisterYourself();
    
    //SHORTER RECTANGLE
    TGeoBBox *LateralSurface2dlow = new TGeoBBox("LateralSurface2dlow",28.5,135/2,78/2);
    TGeoTranslation *tr2dlow = new TGeoTranslation(-side1/2 + (90-33)/2 + 33, -15, d +side2/2 -78/2);
    tr2dlow->SetName("tr2dlow");
    tr2dlow->RegisterYourself();
    
    TGeoCompositeShape *LateralSurfacedlow = new TGeoCompositeShape("LateralSurfacedlow", "LateralSurface1dlow:tr1dlow+LateralSurface2dlow:tr2dlow");
    TGeoVolume *volLateralSurfacedlow = new TGeoVolume("volLateralSurfacedlow",LateralSurfacedlow,Fe);
    
    volLateralSurfacedlow->SetLineColor(kRed);
    top->AddNode(volLateralSurfacedlow, 1, new TGeoTranslation(0,0,0));
    
    
    //***** SIDE left Back ****
    
    //UPPER LATERAL SURFACE = LOWER ONE
    
    //LONGER RECTANGLE
    
    TGeoBBox *LateralS1_d = new TGeoBBox("LateralS1_d",16.5,225/2,67.5);
    TGeoTranslation *tr1_d = new TGeoTranslation(side1/2 - 33/2, 7.5, d - side2/2 +135/2);
    TGeoVolume *volLateralS1_d = new TGeoVolume("volLateralS1_d",LateralS1_d,Fe);
    volLateralS1_d->SetLineColor(kRed);
    top->AddNode(volLateralS1_d, 1, tr1_d);
    
    //TRAPEZOID
    
    TGeoArb8 *LateralS2_d = new TGeoArb8("LateralS2_d",225/2);
    LateralS2_d ->SetVertex(0, 33, 0);
    LateralS2_d ->SetVertex(1, 90, 0);
    LateralS2_d ->SetVertex(2, 90, 78);
    LateralS2_d ->SetVertex(3, 33, 135);
    LateralS2_d ->SetVertex(4, 33, 0);
    LateralS2_d ->SetVertex(5, 90, 0);
    LateralS2_d ->SetVertex(6, 90, 78);
    LateralS2_d ->SetVertex(7, 33, 135);
    
    TGeoVolume *volLateralS2_d = new TGeoVolume("volLateralS2_d",LateralS2_d,Fe);
    volLateralS2_d->SetLineColor(kRed);
    
    TGeoRotation *r2_d = new TGeoRotation();
    r2_d->SetAngles(0,270,180);
    TGeoCombiTrans tr2_d(side1/2, 7.5, d-side2/2,r2_d);
    TGeoHMatrix *m2_d = new TGeoHMatrix(tr2_d);
    top->AddNode(volLateralS2_d, 1, m2_d);
    
    
    
    //***** SIDE right Back ****
    
    
    //UPPER LATERAL SURFACE = LOWER ONE
    
    //LONGER RECTANGLE
    
    TGeoBBox *LateralS1_c = new TGeoBBox("LateralS1_c",16.5,225/2,67.5);
    TGeoTranslation *tr1_c = new TGeoTranslation(side1/2 - 33/2, 7.5, d + side2/2 -135/2);
    TGeoVolume *volLateralS1_c = new TGeoVolume("volLateralS1_c",LateralS1_c,Fe);
    volLateralS1_c->SetLineColor(kRed);
    top->AddNode(volLateralS1_c, 1, tr1_c);
    
    
    //TRAPEZOID
    
    TGeoArb8 *LateralS2_c = new TGeoArb8("LateralS2_d",225/2);
    LateralS2_c ->SetVertex(0, 33, 0);
    LateralS2_c ->SetVertex(1, 90, 0);
    LateralS2_c ->SetVertex(2, 90, 78);
    LateralS2_c ->SetVertex(3, 33, 135);
    LateralS2_c ->SetVertex(4, 33, 0);
    LateralS2_c ->SetVertex(5, 90, 0);
    LateralS2_c ->SetVertex(6, 90, 78);
    LateralS2_c ->SetVertex(7, 33, 135);
    
    TGeoVolume *volLateralS2_c = new TGeoVolume("volLateralS2_c",LateralS2_c,Fe);
    volLateralS2_c->SetLineColor(kRed);
    
    TGeoRotation *r2_c = new TGeoRotation();
    r2_c->SetAngles(0,90,180);
    TGeoCombiTrans tr2_c(side1/2, 7.5, d+side2/2,r2_c);
    TGeoHMatrix *m2_c = new TGeoHMatrix(tr2_c);
    top->AddNode(volLateralS2_c, 1, m2_c);
}

ClassImp(ShipGoliath)














