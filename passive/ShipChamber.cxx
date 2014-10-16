#include "ShipChamber.h"

#include "TGeoManager.h"
#include "FairRun.h"                    // for FairRun
#include "FairRuntimeDb.h"              // for FairRuntimeDb
#include "Riosfwd.h"                    // for ostream
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

void ShipChamber::SetZpositions(Double32_t z1, Double32_t z2, Double32_t z3, Double32_t z4, Double32_t z5, Double32_t z6)
{
     fTub1z = z1;                                                 //!  z-position of tub1
     fTub2z = z2;                                                 //!  z-position of tub2
     fTub3z = z3;                                                 //!  z-position of tub3
     fTub4z = z4;                                                 //!  z-position of tub4
     fTub5z = z5;                                                 //!  z-position of tub5
     fTub6z = z6;                                                 //!  z-position of tub6
}

void ShipChamber::SetTublengths(Double32_t l1, Double32_t l2, Double32_t l3, Double32_t l4, Double32_t l5, Double32_t l6)
{
     fTub1length = l1;                                                 //!  half length of tub1
     fTub2length = l2;                                                 //!  half length of tub2
     fTub3length = l3;                                                 //!  half length of tub3
     fTub4length = l4;                                                 //!  half length of tub4
     fTub5length = l5;                                                 //!  half length of tub5
     fTub6length = l6;                                                 //!  half length of tub6
}

void ShipChamber::SetRmin(Double32_t rmin)
{
     fRmin = rmin;                                                //!  minimum diameter of vacuum chamber
}

void ShipChamber::SetRmax(Double32_t rmax)
{
     fRmax = rmax;                                                //!  maximum diameter of vacuum chamber
}

void ShipChamber::ConstructGeometry()
{

    TGeoVolume *top=gGeoManager->GetTopVolume();
    InitMedium("Aluminum");
    TGeoMedium *Al =gGeoManager->GetMedium("Aluminum");
    // first part of vacuum chamber up to veto station
    //TGeoVolume *tub1 = gGeoManager->MakeTube("tub1", Al, 245, 250, 50);
    TGeoVolume *tub1 = gGeoManager->MakeTube("tub1", Al, fRmin, fRmax, fTub1length);
    tub1->SetLineColor(18);  // silver/gray
    //top->AddNode(tub1, 1, new TGeoTranslation(0, 0, -2450));
    top->AddNode(tub1, 1, new TGeoTranslation(0, 0, fTub1z));


    // second part of vacuum chamber up to first tracking station
    //TGeoVolume *tub2 = gGeoManager->MakeTube("tub2", Al, 245, 250, 3880/2);  // 1940
    TGeoVolume *tub2 = gGeoManager->MakeTube("tub2", Al, fRmin, fRmax, fTub2length);  // 1940
    tub2->SetLineColor(18);
    //top->AddNode(tub2, 1, new TGeoTranslation(0, 0, -440));
    top->AddNode(tub2, 1, new TGeoTranslation(0, 0, fTub2z));


    // third part of vacuum chamber up to second tracking station
    //TGeoVolume *tub3 = gGeoManager->MakeTube("tub3", Al, 245, 250, 80);
    TGeoVolume *tub3 = gGeoManager->MakeTube("tub3", Al, fRmin, fRmax, fTub3length);
    tub3->SetLineColor(18);
    //top->AddNode(tub3, 1, new TGeoTranslation(0, 0, 1620));
    top->AddNode(tub3, 1, new TGeoTranslation(0, 0, fTub3z));

    // fourth part of vacuum chamber up to third tracking station and being covered by magnet
    //TGeoVolume *tub4 = gGeoManager->MakeTube("tub4", Al, 245, 250, 200);
    TGeoVolume *tub4 = gGeoManager->MakeTube("tub4", Al, fRmin, fRmax, fTub4length);
    tub4->SetLineColor(18);
    //top->AddNode(tub4, 1, new TGeoTranslation(0, 0, 1940));
    top->AddNode(tub4, 1, new TGeoTranslation(0, 0, fTub4z));

    // fifth part of vacuum chamber up to fourth tracking station
    //TGeoVolume *tub5 = gGeoManager->MakeTube("tub5", Al, 245, 250, 90);
    TGeoVolume *tub5 = gGeoManager->MakeTube("tub5", Al, fRmin, fRmax, fTub5length);
    tub5->SetLineColor(18);
    //top->AddNode(tub5, 1, new TGeoTranslation(0, 0, 2270));
    top->AddNode(tub5, 1, new TGeoTranslation(0, 0, fTub5z));

    // sixth part of vacuum chamber up to muon detector
    //TGeoVolume *tub6 = gGeoManager->MakeTube("tub6", Al, 245, 250, 20);
    TGeoVolume *tub6 = gGeoManager->MakeTube("tub6", Al, fRmin, fRmax, fTub6length);
    tub6->SetLineColor(18);
    //top->AddNode(tub6, 1, new TGeoTranslation(0, 0, 2540));
    top->AddNode(tub6, 1, new TGeoTranslation(0, 0, fTub6z));

}


ClassImp(ShipChamber)














