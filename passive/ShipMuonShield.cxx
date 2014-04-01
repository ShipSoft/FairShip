#include "ShipMuonShield.h"

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


ShipMuonShield::~ShipMuonShield()
{
}
ShipMuonShield::ShipMuonShield()
  : FairModule("ShipMuonShield", "")
{
}

ShipMuonShield::ShipMuonShield(const char* name, const Int_t Design, const char* Title )
  : FairModule(name ,Title)
{
 fDesign = Design;
}

void ShipMuonShield::ConstructGeometry()
{

    TGeoVolume *top=gGeoManager->GetTopVolume();
    TGeoMedium *tungsten  =gGeoManager->GetMedium("tungsten");
    if (tungsten==0){
        TGeoMaterial *matTungsten     = new TGeoMaterial("tungsten", 183.84, 74, 19.3);
        tungsten = new TGeoMedium("tungsten", 74, matTungsten); 
    }
    TGeoMedium *iron  =gGeoManager->GetMedium("iron");
    if (iron==0){
        TGeoMaterial *matFe     = new TGeoMaterial("iron", 55.847, 26, 7.87);
        iron = new TGeoMedium("iron", 26, matFe);
    }
    TGeoMedium *lead  =gGeoManager->GetMedium("Pb");
    if (lead==0){
        TGeoMaterial *matPb     = new TGeoMaterial("Pb", 207.2, 82, 11.342);
        lead = new TGeoMedium("Pb", 26, matPb);
    }
    
    if (fDesign==1){
    // passive design with tungsten and lead
     Double_t m = 100;  // cm
     Double_t decayVolumeLength = 50*m;  
     Double_t fMuonShieldLength = 70*m;   
     Double_t r1 = 0.12*m; 
     Double_t r2 = 0.50*m; 
     Double_t Lz = 40*m; 
     Double_t Pbr1 = 0.22*m; 
     Double_t Pbr2 = 1*m   * Lz / (40*m); 
     Double_t Pbr3 = 1.5*m * fMuonShieldLength / (60*m); 
     Double_t rW   = 0.*m; 
     TGeoVolume *core = gGeoManager->MakeCone("Core", tungsten, Lz/2., 0.,r1, 0.,r2);
     core->SetLineColor(31);  // silver/green
     Double_t zpos =  -fMuonShieldLength - decayVolumeLength/2. + Lz/2.;
     top->AddNode(core, 1, new TGeoTranslation(0, 0, zpos ));
     TGeoVolume *Pbshield1 = gGeoManager->MakeCone("Pbshield1", lead, Lz/2., r1+0.01,Pbr1,r2+0.01,Pbr2);
     Pbshield1->SetLineColor(23);  // silver/grey
     top->AddNode(Pbshield1, 1, new TGeoTranslation(0, 0, zpos ));
     TGeoVolume *Pbshield2 = gGeoManager->MakeCone("Pbshield2", lead, (fMuonShieldLength-Lz)/2., rW,Pbr2,rW,Pbr3);
     Pbshield2->SetLineColor(23);  // silver/grey
     zpos = -fMuonShieldLength - decayVolumeLength/2. + Lz + (fMuonShieldLength-Lz)/2. ;
     top->AddNode(Pbshield2, 1, new TGeoTranslation(0, 0, zpos));
    
     cout << "passive muon shield postioned at " << (-fMuonShieldLength/2.-2500)/100. << "m"<< endl;
    }
    else {
     cout << "design does not match implemented designs" << endl;
    }
}

ClassImp(ShipMuonShield)








