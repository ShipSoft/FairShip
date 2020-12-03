#include "Floor.h"

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
#include "TGeoArb8.h"
#include <stddef.h>                     // for NULL
#include <iostream>                     // for operator<<, basic_ostream, etc


Floor::~Floor()
{
}
Floor::Floor()
  : FairModule("Floor", "")
{
}

Floor::Floor(const char* name, const char* Title)
  : FairModule(name ,Title)
{
}

Int_t Floor::InitMedium(const char* name) 
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

void Floor::ConstructGeometry()
{

	TGeoVolume *top=gGeoManager->GetTopVolume();
	InitMedium("Concrete");
	TGeoMedium *concrete =gGeoManager->GetMedium("Concrete");

	TGeoArb8 *fl_arb = new TGeoArb8(130);
	fl_arb->SetVertex(0,-20,-60);
	fl_arb->SetVertex(1,-20,8.);
	fl_arb->SetVertex(2,80,8.);
	fl_arb->SetVertex(3,80,-60);
	fl_arb->SetVertex(4,-20,-60);
	fl_arb->SetVertex(5,-20,0.);
	fl_arb->SetVertex(6,80,0.);
	fl_arb->SetVertex(7,80,-60);
	TGeoVolume *volfloor = new TGeoVolume("floor",fl_arb,concrete);
	volfloor->SetLineColor(20);
	top->AddNode(volfloor,1, new TGeoTranslation(0,0,80));
}

ClassImp(Floor)
