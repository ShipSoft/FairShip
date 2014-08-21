#include "ShipTargetStation.h"

#include "TGeoManager.h"
#include "FairRun.h"                    // for FairRun
#include "FairRuntimeDb.h"              // for FairRuntimeDb
#include "Riosfwd.h"                    // for ostream
#include "TList.h"                      // for TListIter, TList (ptr only)
#include "TObjArray.h"                  // for TObjArray
#include "TString.h"                    // for TString
#include "TGeoBBox.h"
#include "TGeoCompositeShape.h"
#include "TGeoTube.h"
#include "TGeoMaterial.h"
#include "FairGeoMedia.h"
#include "FairGeoBuilder.h"
#include "TGeoMedium.h"
#include <stddef.h>                     // for NULL
#include <iostream>                     // for operator<<, basic_ostream, etc

using std::cout;
using std::endl;


ShipTargetStation::~ShipTargetStation()
{
}
ShipTargetStation::ShipTargetStation()
  : FairModule("ShipTargetStation", "")
{
}

ShipTargetStation::ShipTargetStation(const char* name, const Double_t tl,const Double_t al,const Double_t tz,
                                     const Double_t az, const int nS, const Double_t sl, const char* Title )
  : FairModule(name ,Title)
{
  fTargetLength    = tl;        
  fAbsorberLength  = al;       
  fAbsorberZ       = az; 
  fTargetZ         = tz;
  fnS              = nS;
  fsl              = sl;        
}

// -----   Private method InitMedium 
Int_t ShipTargetStation::InitMedium(const char* name) 
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

void ShipTargetStation::ConstructGeometry()
{
    TGeoVolume *top=gGeoManager->GetTopVolume();
    InitMedium("tungsten");
    TGeoMedium *tungsten =gGeoManager->GetMedium("tungsten");
    InitMedium("iron");
    TGeoMedium *iron  =gGeoManager->GetMedium("iron");
    InitMedium("H2O");
    TGeoMedium *water  =gGeoManager->GetMedium("H2O");
    if (fnS > 0){
      Double_t dZ = (fTargetLength - (fnS-1)*fsl)/float(fnS);
      Double_t zPos =  fTargetZ - fTargetLength/2.;
    // target made of tungsten and air slits
      for (Int_t i=0; i<fnS-1; i++) {
       TString nm = "Target_"; nm += i;
       TString sm = "Slit_";   sm += i;
       TGeoVolume *target = gGeoManager->MakeTube(nm, tungsten, 0, 25, dZ/2.);
       target->SetLineColor(38);  // silver/blue
       top->AddNode(target, 1, new TGeoTranslation(0, 0, zPos+dZ/2.));
       TGeoVolume *slit   = gGeoManager->MakeTube(sm, water,    0, 25, fsl/2.);
       slit->SetLineColor(7);  // cyan
       top->AddNode(slit, 1, new TGeoTranslation(0, 0, zPos+dZ+fsl/2.));
       zPos+=dZ+fsl;
      }
      TString nm = "Target_"; nm += fnS;
      TGeoVolume *target = gGeoManager->MakeTube(nm, tungsten, 0, 25, dZ/2.);
      target->SetLineColor(38);  // silver/blue
      top->AddNode(target, 1, new TGeoTranslation(0, 0, zPos+dZ/2.));
    }else{
    // target made of solid tungsten
    TGeoVolume *target = gGeoManager->MakeTube("Target", tungsten, 0, 25, fTargetLength/2.);
    target->SetLineColor(38);  // silver/blue
    top->AddNode(target, 1, new TGeoTranslation(0, 0, fTargetZ));
    }
    
    // Absorber made of iron
    TGeoVolume *absorber = gGeoManager->MakeTube("Absorber", iron, 0, 100, fAbsorberLength/2.);  // 1890
    absorber->SetLineColor(42); // brown / light red
    top->AddNode(absorber, 1, new TGeoTranslation(0, 0, fAbsorberZ));

    // put iron shielding around target
    TGeoVolume *moreShielding = gGeoManager->MakeTube("MoreShielding", iron, 30, 100, fTargetLength/2.);  
    absorber->SetLineColor(42); // brown / light red
    top->AddNode(moreShielding, 1, new TGeoTranslation(0, 0, fTargetZ));

    cout << "target and absorber postioned at " << fTargetZ <<" "<< fAbsorberZ << " m"<< endl;
    
}

ClassImp(ShipTargetStation)
