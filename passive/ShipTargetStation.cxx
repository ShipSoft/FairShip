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

ShipTargetStation::ShipTargetStation(const char* name, const Double_t tl,const Double_t al,const Double_t tz,const Double_t az,const char* Title )
  : FairModule(name ,Title)
{
  fTargetLength    = tl;        
  fAbsorberLength  = al;       
  fAbsorberZ       = az; 
  fTargetZ         = tz;
}

void ShipTargetStation::ConstructGeometry()
{

    TGeoVolume *top=gGeoManager->GetTopVolume();
    TGeoMedium *tungsten  =gGeoManager->GetMedium("tungsten");
    if (tungsten==0){
        TGeoMaterial *matTungsten     = new TGeoMaterial("tungsten", 183.84, 74, 19.3);
        tungsten = new TGeoMedium("tungsten", 974, matTungsten); 
    }
    TGeoMedium *iron  = gGeoManager->GetMedium("iron");
    if (iron==0){
        TGeoMaterial *matFe     = new TGeoMaterial("iron", 55.847, 26, 7.87);
        iron = new TGeoMedium("iron", 926, matFe);
    }
    
    
    // target made of tungsten
    TGeoVolume *target = gGeoManager->MakeTube("Target", tungsten, 0, 25, fTargetLength/2.);
    target->SetLineColor(38);  // silver/blue
    top->AddNode(target, 1, new TGeoTranslation(0, 0, fTargetZ));
    
    
    // Absorber made of iron
    TGeoVolume *absorber = gGeoManager->MakeTube("Absorber", iron, 0, 100, fAbsorberLength/2.);  // 1890
    absorber->SetLineColor(42); // brown / light red
    top->AddNode(absorber, 1, new TGeoTranslation(0, 0, fAbsorberZ));

    cout << "target and absorber postioned at " << fTargetZ <<" "<< fAbsorberZ << " m"<< endl;
    
}

ClassImp(ShipTargetStation)














