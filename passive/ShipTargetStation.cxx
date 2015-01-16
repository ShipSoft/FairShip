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
   TGeoMedium* medium=gGeoManager->GetMedium(name);
   if (medium!=NULL)
     return ShipMedium->getMediumIndex();
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
    InitMedium("molybdenum");
    TGeoMedium *mo  =gGeoManager->GetMedium("molybdenum");
    if (fnS > 10){
      TGeoVolume *target;
      TGeoVolume *slit; 
      Double_t zPos =  fTargetZ - fTargetLength/2.;
      for (Int_t i=0; i<fnS; i++) {
       TString nm = "Target_"; nm += i+1;
       TString sm = "Slit_";   sm += i+1;
       TGeoMedium *material;
       if (fM.at(i)=="molybdenum") {material = mo;};
       if (fM.at(i)=="tungsten")   {material = tungsten;};
       target = gGeoManager->MakeBox(nm, material, fDiameter/2., fDiameter/2., fL.at(i)/2.);
       if (fM.at(i)=="molybdenum") {
         target->SetLineColor(28);
       } else {target->SetLineColor(38);};  // silver/blue
       top->AddNode(target, 1, new TGeoTranslation(0, 0, zPos + fL.at(i)/2.) );
       if (i < 16){
        slit   = gGeoManager->MakeBox(sm, water, fDiameter/2., fDiameter/2., fsl/2.);
        slit->SetLineColor(7);  // cyan
        top->AddNode(slit, 1, new TGeoTranslation(0, 0, zPos+fL.at(i)+fsl/2.) );
        zPos+=fL.at(i)+fsl;
       } else {
         zPos+=fL.at(i);}
      } 
    }else if(fnS > 0){
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
    TGeoVolume *absorber = gGeoManager->MakeTube("Absorber", iron, 0, 400, fAbsorberLength/2.);  // 1890
    absorber->SetLineColor(42); // brown / light red
    top->AddNode(absorber, 1, new TGeoTranslation(0, 0, fAbsorberZ));

    // put iron shielding around target
    if (fnS > 10){
      Float_t xTot = 400./2.; // all in cm
      Float_t yTot = 400./2.;
      Float_t spaceTopBot = 10.;
      Float_t spaceSide   = 5.;
      TGeoVolume *moreShieldingTopBot   = gGeoManager->MakeBox("moreShieldingTopBot", iron, xTot, yTot/2., fTargetLength/2.);
      moreShieldingTopBot->SetLineColor(33); 
      top->AddNode(moreShieldingTopBot, 1, new TGeoTranslation(0., fDiameter/2. +spaceTopBot+yTot/2.,fTargetZ));
      top->AddNode(moreShieldingTopBot, 2, new TGeoTranslation(0.,-fDiameter/2. -spaceTopBot-yTot/2.,fTargetZ));
      TGeoVolume *moreShieldingSide   = gGeoManager->MakeBox("moreShieldingSide", iron, xTot/2., (fDiameter+1.9*spaceTopBot)/2., fTargetLength/2.);
      moreShieldingSide->SetLineColor(33); 
      top->AddNode(moreShieldingSide, 1, new TGeoTranslation(fDiameter/2.+spaceSide+xTot/2.,0.,fTargetZ));
      top->AddNode(moreShieldingSide, 2, new TGeoTranslation(-fDiameter/2.-spaceSide-xTot/2.,0.,fTargetZ));
    }else{
    TGeoVolume *moreShielding = gGeoManager->MakeTube("MoreShielding", iron, 30, 400, fTargetLength/2.);  
    absorber->SetLineColor(43); //  
    top->AddNode(moreShielding, 1, new TGeoTranslation(0, 0, fTargetZ));
    }
    cout << "target and absorber postioned at " << fTargetZ <<" "<< fAbsorberZ << " m"<< endl;
    
}

ClassImp(ShipTargetStation)
