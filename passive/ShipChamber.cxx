#include "ShipChamber.h"

#include "TGeoManager.h"
#include "FairRun.h"                    // for FairRun
#include "FairRuntimeDb.h"              // for FairRuntimeDb
#include <iosfwd>                    // for ostream
#include "TList.h"                      // for TListIter, TList (ptr only)
#include "TObjArray.h"                  // for TObjArray
#include "TString.h"                    // for TString
#include "TGeoBBox.h"
#include "TGeoCompositeShape.h"
#include "FairGeoMedia.h"
#include "FairGeoBuilder.h"
#include "TGeoTube.h"
#include "TGeoMaterial.h"
#include "TGeoMedium.h"
#include <stddef.h>                     // for NULL
#include <iostream>                     // for operator<<, basic_ostream, etc



ShipChamber::~ShipChamber()
{
}
ShipChamber::ShipChamber()
  : FairModule("ShipChamber", "")
{
}

ShipChamber::ShipChamber(const char* name, const char* Title)
  : FairModule(name ,Title)
{
}
// -----   Private method InitMedium 
Int_t ShipChamber::InitMedium(const char* name) 
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
void ShipChamber::ConstructGeometry()
{

    TGeoVolume *top=gGeoManager->GetTopVolume();
    InitMedium("Aluminum");
    TGeoMedium *Al =gGeoManager->GetMedium("Aluminum");
    // first part of vacuum chamber up to veto station
    TGeoVolume *tub1 = gGeoManager->MakeTube("tub1", Al, 245, 250, 50);
    tub1->SetLineColor(18);  // silver/gray
    top->AddNode(tub1, 1, new TGeoTranslation(0, 0, -2450));
    
    
    // second part of vacuum chamber up to first tracking station
    TGeoVolume *tub2 = gGeoManager->MakeTube("tub2", Al, 245, 250, 3880/2);  // 1890
    tub2->SetLineColor(18);
    top->AddNode(tub2, 1, new TGeoTranslation(0, 0, -440));
    
    
    // third part of vacuum chamber up to second tracking station
    TGeoVolume *tub3 = gGeoManager->MakeTube("tub3", Al, 245, 250, 80);
    tub3->SetLineColor(18);
    top->AddNode(tub3, 1, new TGeoTranslation(0, 0, 1620));
    
    // fourth part of vacuum chamber up to third tracking station and being covered by magnet
    TGeoVolume *tub4 = gGeoManager->MakeTube("tub4", Al, 245, 250, 200);
    tub4->SetLineColor(18);
    top->AddNode(tub4, 1, new TGeoTranslation(0, 0, 1940));
    
    // fifth part of vacuum chamber up to fourth tracking station
    TGeoVolume *tub5 = gGeoManager->MakeTube("tub5", Al, 245, 250, 90);
    tub5->SetLineColor(18);
    top->AddNode(tub5, 1, new TGeoTranslation(0, 0, 2270));
    
    // sixth part of vacuum chamber up to muon detector
    TGeoVolume *tub6 = gGeoManager->MakeTube("tub6", Al, 245, 250, 20);
    tub6->SetLineColor(18);
    top->AddNode(tub6, 1, new TGeoTranslation(0, 0, 2540));
    

    
}



ClassImp(ShipChamber)














