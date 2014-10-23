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
#include "TGeoTube.h"
#include "TGeoMaterial.h"
#include "TGeoElement.h"
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

ShipMagnet::ShipMagnet(const char* name, const char* Title)
  : FairModule(name ,Title)
{
}

void ShipMagnet::ConstructGeometry()
{
/*
    FairGeoMedia* Media       = FairGeoLoader::Instance()->getGeoInterface()->getMedia();
    FairGeoBuilder* geobuild  = FairGeoLoader::Instance()->getGeoBuilder();
    

 
    
    FairGeoMedium* FairMedium=Media->getMedium("vacuum");
    Int_t nmed=geobuild->createMedium(FairMedium);
    
    FairGeoMedium* FairMedium1=Media->getMedium("Aluminum");
    Int_t nmed1=geobuild->createMedium(FairMedium);
    
    FairGeoMedium* FairMedium2=Media->getMedium("iron");
    Int_t nmed2=geobuild->createMedium(FairMedium);
    
  
    TGeoMedium *Vacuum = gGeoManager->GetMedium(nmed);
    TGeoMedium *Al     = gGeoManager->GetMedium(nmed1);
    TGeoMedium *Fe     = gGeoManager->GetMedium(nmed2);
  */
   
    TGeoVolume *top=gGeoManager->GetTopVolume();
    TGeoMedium *Fe  = gGeoManager->GetMedium("iron");
    

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
    top->AddNode(magnet1, 1, new TGeoTranslation(0, 0, 1940));
    
    TGeoRotation m3;
    m3.SetAngles(180, 0, 0);
    TGeoTranslation m4(0, 0, 1940);
    TGeoCombiTrans m5(m4, m3);
    TGeoHMatrix *m6 = new TGeoHMatrix(m5);
    top->AddNode(magnet1, 2, m6);
    
    
}



ClassImp(ShipMagnet)














