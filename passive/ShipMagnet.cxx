#include "ShipMagnet.h"

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
#include "TGeoCompositeShape.h"
#include "FairGeoInterface.h"
#include "FairGeoMedia.h"
#include "FairGeoBuilder.h"
#include "TGeoTube.h"
#include "TGeoMaterial.h"
#include "TGeoElement.h"
#include "TGeoEltu.h"
#include "TGeoMedium.h"
#include <stddef.h>                     // for NULL
#include <iostream>                     // for operator<<, basic_ostream, etc



ShipMagnet::~ShipMagnet()
{
}
ShipMagnet::ShipMagnet()
  : FairModule("ShipMagnet", "")
{
}

ShipMagnet::ShipMagnet(const char* name, const char* Title, Double_t z, Int_t c, Double_t dy)
  : FairModule(name ,Title)
{
 fDesign = c;
 fSpecMagz = z; 
 fDy = dy;
}

// -----   Private method InitMedium 
Int_t ShipMagnet::InitMedium(const char* name) 
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

void ShipMagnet::ConstructGeometry()
{

    TGeoVolume *top=gGeoManager->GetTopVolume();
    InitMedium("iron");
    TGeoMedium *Fe =gGeoManager->GetMedium("iron");
    InitMedium("Aluminum");
    TGeoMedium *Al =gGeoManager->GetMedium("Aluminum");

    if (fDesign==1){
    // magnet yoke
     TGeoBBox *magyoke1 = new TGeoBBox("magyoke1", 350, 350, 125);
     TGeoBBox *magyoke2 = new TGeoBBox("magyoke2", 250, 250, 126);
    
     TGeoCompositeShape *magyokec = new TGeoCompositeShape("magyokec", "magyoke1-magyoke2");
     TGeoVolume *magyoke = new TGeoVolume("magyoke", magyokec, Fe);
     magyoke->SetLineColor(kBlue);
    //magyoke->SetTransparency(50);
     top->AddNode(magyoke, 1, new TGeoTranslation(0, 0, 1940));
    
    // magnet
     TGeoTubeSeg *magnet1a = new TGeoTubeSeg("magnet1a", 250, 300, 35, 45, 135);
     TGeoTubeSeg *magnet1b = new TGeoTubeSeg("magnet1b", 250, 300, 35, 45, 135);
     TGeoTubeSeg *magnet1c = new TGeoTubeSeg("magnet1c", 250, 270, 125, 45, 60);
     TGeoTubeSeg *magnet1d = new TGeoTubeSeg("magnet1d", 250, 270, 125, 120, 135);
    
    // magnet composite shape matrices
     TGeoTranslation *m1 = new TGeoTranslation(0, 0, 160);
     m1->SetName("m1");
     m1->RegisterYourself();
     TGeoTranslation *m2 = new TGeoTranslation(0, 0, -160);
     m2->SetName("m2");
     m2->RegisterYourself();
    
     TGeoCompositeShape *magcomp1 = new TGeoCompositeShape("magcomp1", "magnet1a:m1+magnet1b:m2+magnet1c+magnet1d");
     TGeoVolume *magnet1 = new TGeoVolume("magnet1", magcomp1, Fe);
     magnet1->SetLineColor(kYellow);
     top->AddNode(magnet1, 1, new TGeoTranslation(0, 0, fSpecMagz));  // was 1940
    
     TGeoRotation m3;
     m3.SetAngles(180, 0, 0);
     TGeoTranslation m4(0, 0, fSpecMagz);   // was 1940
     TGeoCombiTrans m5(m4, m3);
     TGeoHMatrix *m6 = new TGeoHMatrix(m5);
     top->AddNode(magnet1, 2, m6);
    }
   else {  // fDesign==2 
    Double_t cm  = 1;       
    Double_t m   = 100*cm;  
    Double_t Yokel = 1.25*m; 
    Double_t magnetIncrease = 100.*cm;
    // magnet yoke
    Double_t bradius = fDy/2.;
    TGeoBBox *magyoke1 = new TGeoBBox("magyoke1", 3.7*m, bradius+1.2*m, Yokel);
    TGeoBBox *magyoke2 = new TGeoBBox("magyoke2", 2.70*m,bradius+0.2*m, Yokel+0.1*cm);
    
    TGeoCompositeShape *magyokec = new TGeoCompositeShape("magyokec", "magyoke1-magyoke2");
    TGeoVolume *magyoke = new TGeoVolume("magyoke", magyokec, Fe);
    magyoke->SetLineColor(kBlue);
    top->AddNode(magyoke, 1, new TGeoTranslation(0, 0, fSpecMagz));

    //Attempt to make Al coils...
    TGeoEltu *C2  = new TGeoEltu("C2",3.*m,bradius+0.5*m,Yokel+0.6*m+magnetIncrease/2.);
    TGeoEltu *C1  = new TGeoEltu("C1",2.7*m,bradius+0.2*m,Yokel+0.601*m+magnetIncrease/2.);
    TGeoBBox *Box1 = new TGeoBBox("Box1", 1.*m, bradius+0.51*m, Yokel+0.61*m+magnetIncrease/2.);
    TGeoBBox *Box2 = new TGeoBBox("Box2", 3.01*m, bradius-0.5*m, Yokel+0.01*m+magnetIncrease/2.);
    TGeoCompositeShape *MCoilc = new TGeoCompositeShape("MCoilc", "C2-C1-magyokec-Box1-Box2");
    TGeoVolume *MCoil = new TGeoVolume("MCoil", MCoilc, Al);
    MCoil->SetLineColor(kYellow);

    top->AddNode(MCoil, 1, new TGeoTranslation(0, 0, fSpecMagz));
    }
}



ClassImp(ShipMagnet)














