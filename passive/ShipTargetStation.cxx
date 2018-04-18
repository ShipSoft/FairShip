#include "ShipTargetStation.h"

#include "TGeoManager.h"
#include "FairRun.h"                    // for FairRun
#include "FairRuntimeDb.h"              // for FairRuntimeDb
#include <iosfwd>                    // for ostream
#include "TList.h"                      // for TListIter, TList (ptr only)
#include "TObjArray.h"                  // for TObjArray
#include "TString.h"                    // for TString
#include "TGeoBBox.h"
#include "TGeoCompositeShape.h"
#include "TGeoShapeAssembly.h"
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

ShipTargetStation::ShipTargetStation(const char* name, const Double_t tl,const Double_t tz,
                                     const int nS, const Double_t sl, const char* Title )
  : FairModule(name ,Title)
{
  fTargetLength    = tl;        
  fAbsorberLength  = 0;       
  fAbsorberZ       = 0; 
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

void ShipTargetStation::SetMuFlux(Bool_t muflux)
{
  fMuFlux = muflux;
}

void ShipTargetStation::ConstructGeometry()
{
    TGeoVolume *top=gGeoManager->GetTopVolume();
    InitMedium("tungsten");
    TGeoMedium *tungsten =gGeoManager->GetMedium("tungsten");
    InitMedium("tungsten1");
    TGeoMedium *tungsten1 =gGeoManager->GetMedium("tungsten1");
    InitMedium("tungsten2");
    TGeoMedium *tungsten2 =gGeoManager->GetMedium("tungsten2");
    InitMedium("tungsten3");
    TGeoMedium *tungsten3 =gGeoManager->GetMedium("tungsten3");
    InitMedium("tungsten4");
    TGeoMedium *tungsten4 =gGeoManager->GetMedium("tungsten4");
    InitMedium("tungsten5");
    TGeoMedium *tungsten5 =gGeoManager->GetMedium("tungsten5");
    InitMedium("Concrete");
    TGeoMedium *concrete  =gGeoManager->GetMedium("Concrete");
    InitMedium("iron");
    TGeoMedium *iron  =gGeoManager->GetMedium("iron");
    InitMedium("H2O");
    TGeoMedium *water  =gGeoManager->GetMedium("H2O");
    InitMedium("molybdenum");
    TGeoMedium *mo  =gGeoManager->GetMedium("molybdenum");
    InitMedium("molybdenum1");
    TGeoMedium *mo1  =gGeoManager->GetMedium("molybdenum1");
    InitMedium("molybdenum2");
    TGeoMedium *mo2  =gGeoManager->GetMedium("molybdenum2");
    InitMedium("molybdenum3");
    TGeoMedium *mo3  =gGeoManager->GetMedium("molybdenum3");
    InitMedium("molybdenum4");
    TGeoMedium *mo4  =gGeoManager->GetMedium("molybdenum4");
    InitMedium("air");
    TGeoMedium *air = gGeoManager->GetMedium("air");   
    InitMedium("PlasticBase");
    TGeoMedium *plasticbase = gGeoManager->GetMedium("PlasticBase");
    InitMedium("aluminium");
    TGeoMedium *Al = gGeoManager->GetMedium("aluminium");

    TGeoVolume *tTarget = new TGeoVolumeAssembly("TargetArea");
    Double_t zPos =  -4.59; //for front end endcap //-3.02
    Int_t slots = fnS;
    slots = slots-1;    


    TGeoVolume *frontcap;
    TGeoVolume *endcap;   
    TGeoVolume *targettube;   
    frontcap   = gGeoManager->MakeTube("FrontCap", Al,    0, 15./2., 2.5/2.);
    frontcap->SetLineColor(20); 
    endcap   = gGeoManager->MakeTube("EndCap", Al,    0, 15./2., 2.5/2.);
    endcap->SetLineColor(20); 
    targettube = gGeoManager->MakeTube("TargetTube", Al, fDiameter/2.+0.5, fDiameter/2.+1.1, fTargetLength/2.-0.225);
    targettube->SetLineColor(20);  
    
    if (fnS > 10){
      TGeoVolume *target;
      TGeoVolume *slit; 

      for (Int_t i=0; i<fnS; i++) {
       TString nmi = "Target_"; nmi += i+1;
       TString sm = "Slit_";   sm += i+1;
       TGeoMedium *material;
       if (fM.at(i)=="molybdenum") {material = mo;};
       if (fM.at(i)=="molybdenum1") {material = mo1;};
       if (fM.at(i)=="molybdenum2") {material = mo2;};
       if (fM.at(i)=="molybdenum3") {material = mo3;};
       if (fM.at(i)=="molybdenum4") {material = mo4;};
       if (fM.at(i)=="tungsten")   {material = tungsten;};
       if (fM.at(i)=="tungsten1")   {material = tungsten1;};
       if (fM.at(i)=="tungsten2")   {material = tungsten2;};
       if (fM.at(i)=="tungsten3")   {material = tungsten3;};
       if (fM.at(i)=="tungsten4")   {material = tungsten4;};
       if (fM.at(i)=="tungsten5")   {material = tungsten5;};
       
       if (fnS == 18) { // new target layout
          target = gGeoManager->MakeTube(nmi, material, 0., fDiameter/2., fL.at(i)/2.);                     
       }
       else {
          target = gGeoManager->MakeBox(nmi, material, fDiameter/2., fDiameter/2., fL.at(i)/2.);
       }
       if (fM.at(i)=="molybdenum") {
         target->SetLineColor(28);
       } else {target->SetLineColor(38);};  // silver/blue
       tTarget->AddNode(target, 1, new TGeoTranslation(0, 0, zPos + fL.at(i)/2.) );
       if (i < slots){
        if(fnS == 18) {
	  if(fMuFlux) { slit = gGeoManager->MakeTube(sm, plasticbase, 0., fDiameter/2., fsl/2.);  }
	  else { slit   = gGeoManager->MakeTube(sm, water, 0., fDiameter/2., fsl/2.); }
	}
	else {  
	  slit   = gGeoManager->MakeBox(sm, water, fDiameter/2., fDiameter/2., fsl/2.);
	}  
        slit->SetLineColor(7);  // cyan
	if (fMuFlux) {
	  if (i==0) {
           tTarget->AddNode(frontcap, 11, new TGeoTranslation(0, 0, zPos-1.251) );	  
	  }	
	}
        tTarget->AddNode(slit, 1, new TGeoTranslation(0, 0, zPos+fL.at(i)+fsl/2.) );
        zPos+=fL.at(i)+fsl;
       } else {
         zPos+=fL.at(i);
	  if (fMuFlux) {
	     if (fnS==18) {
               tTarget->AddNode(endcap, 12, new TGeoTranslation(0, 0, zPos+1.29) );	
               tTarget->AddNode(targettube, 13, new TGeoTranslation(0, 0, fTargetLength/2.-4.815));   //-3.245   
	     }	 
	     zPos+=1.27;
	  }   
	 }
      } 
    }else if(fnS > 0){
      Double_t dZ = (fTargetLength - (fnS-1)*fsl)/float(fnS);
    // target made of tungsten and air slits
      for (Int_t i=0; i<fnS-1; i++) {
       TString nmi = "Target_"; nmi += i;
       TString sm = "Slit_";   sm += i;
       TGeoVolume *target = gGeoManager->MakeTube(nmi, tungsten, 0, 25, dZ/2.);
       target->SetLineColor(38);  // silver/blue
       tTarget->AddNode(target, 1, new TGeoTranslation(0, 0, zPos+dZ/2.));
       TGeoVolume *slit   = gGeoManager->MakeTube(sm, water,    0, 25, fsl/2.);
       slit->SetLineColor(7);  // cyan
       tTarget->AddNode(slit, 1, new TGeoTranslation(0, 0, zPos+dZ+fsl/2.));
       zPos+=dZ+fsl;
      }
      TString nmi = "Target_"; nmi += fnS;
      TGeoVolume *target = gGeoManager->MakeTube(nmi, tungsten, 0, 25, dZ/2.);
      target->SetLineColor(38);  // silver/blue
      if (fMuFlux) {	
	tTarget->AddNode(target, 112, new TGeoTranslation(0, 0, zPos+dZ/2.)); 
      }	 
      else { 	
        tTarget->AddNode(target, 1, new TGeoTranslation(0, 0, zPos+dZ/2.));      
      }  
    }
    else{
      // target made of solid tungsten
      TGeoVolume *target = gGeoManager->MakeTube("Target", tungsten, 0, 25, fTargetLength/2.);
      target->SetLineColor(38);  // silver/blue
      tTarget->AddNode(target, 1, new TGeoTranslation(0, 0, fTargetZ));
    }
    TGeoVolume *absorber;
    TGeoVolume *absorbercutout;
    TGeoVolume *aboveabsorbershield;
    TGeoVolume *ironshield;
    TGeoVolume *concreteshield;
    TGeoVolume *abovetargetshield;
    TGeoVolume *aboveabovetargetshield;  
    
    if (fAbsorberLength>0){  // otherwise, magnetized hadron absorber defined in ShipMuonShield.cxx
     zPos =  fTargetZ - fTargetLength/2.;
    // Absorber made of iron

    if(fMuFlux) {   

        absorber = gGeoManager->MakeBox("Absorber", iron, 120., 97.5, fAbsorberLength/2.); 
	absorbercutout = gGeoManager->MakeBox("AbsorberCO", iron, 102., 27.5, fAbsorberLength/2.); 

	ironshield = gGeoManager->MakeBox("IronShield", iron, 20., 80., 160.);  
	concreteshield = gGeoManager->MakeBox("ConcreteShield", concrete, 40., 80., 160.); 
	abovetargetshield = gGeoManager->MakeBox("AboveTargetShield", concrete, 120., 42.5, 160.); 
	aboveabsorbershield = gGeoManager->MakeBox("AboveBsorberShield", concrete, 120., 40.0, 80.); 
	aboveabovetargetshield = gGeoManager->MakeBox("AboveAboveTargetShield", concrete, fAbsorberLength, 40., fAbsorberLength); 
	ironshield->SetLineColor(42); // brown / light red	
	concreteshield->SetLineColor(kGray); // gray
	aboveabsorbershield->SetLineColor(kGray); // gray
	abovetargetshield->SetLineColor(kGray); // gray
	aboveabovetargetshield->SetLineColor(kGray); // gray
	frontcap->SetLineColor(29); // blue-ish
	endcap->SetLineColor(29); // blue-ish
	absorber->SetLineColor(42); // brown / light red
	tTarget->AddNode(absorbercutout, 11, new TGeoTranslation(18., 97.5, fAbsorberZ-zPos-2.5)); 	
	tTarget->AddNode(absorber, 1, new TGeoTranslation(0., -27.5, fAbsorberZ-zPos-2.5)); 	
     }
     else {
        absorber = gGeoManager->MakeTube("Absorber", iron, 0, 400, fAbsorberLength/2.);  // 1890
	absorber->SetLineColor(42); // brown / light red
        tTarget->AddNode(absorber, 1, new TGeoTranslation(0., 0, fAbsorberZ-zPos));
     }

    } 
    // put iron shielding around target
    if (fnS > 10){
      Float_t xTot = 400./2.; // all in cm
      Float_t yTot = 400./2.;
      Float_t spaceTopBot = 10.;
      Float_t spaceSide   = 5.;
      if (!fMuFlux) {
        TGeoVolume *moreShieldingTopBot   = gGeoManager->MakeBox("moreShieldingTopBot", iron, xTot, yTot/2., fTargetLength/2.);
        moreShieldingTopBot->SetLineColor(33); 
        tTarget->AddNode(moreShieldingTopBot, 1, new TGeoTranslation(0., fDiameter/2. +spaceTopBot+yTot/2.,fTargetLength/2.));
        tTarget->AddNode(moreShieldingTopBot, 2, new TGeoTranslation(0.,-fDiameter/2. -spaceTopBot-yTot/2.,fTargetLength/2.));
        TGeoVolume *moreShieldingSide   = gGeoManager->MakeBox("moreShieldingSide", iron, xTot/2., (fDiameter+1.9*spaceTopBot)/2., fTargetLength/2.);
        moreShieldingSide->SetLineColor(33); 
        tTarget->AddNode(moreShieldingSide, 1, new TGeoTranslation(fDiameter/2.+spaceSide+xTot/2.,0.,fTargetLength/2.));
        tTarget->AddNode(moreShieldingSide, 2, new TGeoTranslation(-fDiameter/2.-spaceSide-xTot/2.,0.,fTargetLength/2.));
      } 
    }else{
    TGeoVolume *moreShielding = gGeoManager->MakeTube("MoreShielding", iron, 30, 400, fTargetLength/2.);  
    moreShielding->SetLineColor(43); //  
    tTarget->AddNode(moreShielding, 1, new TGeoTranslation(0, 0, fTargetLength/2.));
    }
    TGeoShapeAssembly* asmb = dynamic_cast<TGeoShapeAssembly*>(tTarget->GetShape());
    Double_t totLength = asmb->GetDZ();
    top->AddNode(tTarget, 1, new TGeoTranslation(0, 0,fTargetZ - fTargetLength/2. + totLength+2.5));
    
    if(fMuFlux) { 

       top->AddNode(ironshield, 2, new TGeoTranslation(-50., -45.,fTargetZ - 83.49));    //3.6
       top->AddNode(concreteshield, 3, new TGeoTranslation(85.,-45.,fTargetZ - 83.49));   
       top->AddNode(abovetargetshield, 4, new TGeoTranslation(50.,77.5,fTargetZ - 83.49)); 
       top->AddNode(aboveabovetargetshield, 5, new TGeoTranslation(-50.,165.0,fAbsorberZ-zPos-624.5)); 
       top->AddNode(aboveabsorbershield, 6, new TGeoTranslation(0.,165.0,-31.48));        
    } 
    if (fAbsorberLength>0){
     cout << "target and absorber positioned at " << fTargetZ <<" "<< fAbsorberZ << " m"<< endl;
    }else{
     cout << "target at " << fTargetZ/100. <<"m "<< endl;
    }
}

ClassImp(ShipTargetStation)
