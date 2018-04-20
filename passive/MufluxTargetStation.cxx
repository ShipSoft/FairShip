#include "MufluxTargetStation.h"

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


MufluxTargetStation::~MufluxTargetStation()
{
}
MufluxTargetStation::MufluxTargetStation()
  : FairModule("MufluxTargetStation", "")
{
}

MufluxTargetStation::MufluxTargetStation(const char* name, const Double_t tl,const Double_t al,const Double_t tz,
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

MufluxTargetStation::MufluxTargetStation(const char* name, const Double_t tl,const Double_t tz,
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
Int_t MufluxTargetStation::InitMedium(const char* name) 
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

void MufluxTargetStation::ConstructGeometry()
{
    TGeoVolume *top=gGeoManager->GetTopVolume();
    InitMedium("tungstenmisis");
    TGeoMedium *tungstenmisis =gGeoManager->GetMedium("tungstenmisis");
    InitMedium("Concrete");
    TGeoMedium *concrete  =gGeoManager->GetMedium("Concrete");
    InitMedium("iron");
    TGeoMedium *iron  =gGeoManager->GetMedium("iron");
    InitMedium("H2O");
    TGeoMedium *water  =gGeoManager->GetMedium("H2O");
    InitMedium("molybdenummisis");
    TGeoMedium *momisis  =gGeoManager->GetMedium("molybdenummisis");
    InitMedium("air");
    TGeoMedium *air = gGeoManager->GetMedium("air");   
    InitMedium("PlasticBase");
    TGeoMedium *plasticbase = gGeoManager->GetMedium("PlasticBase");
    InitMedium("steel");
    TGeoMedium *steel = gGeoManager->GetMedium("steel");

    TGeoVolume *tTarget = new TGeoVolumeAssembly("TargetArea");
    Double_t zPos =  -4.59; //for front end endcap //-3.02
    Int_t slots = fnS;
    slots = slots-1;    


    TGeoVolume *frontcap;
    TGeoVolume *endcap;   
    TGeoVolume *targettube;   
    frontcap   = gGeoManager->MakeTube("FrontCap", steel, 0, 15./2., 2.5/2.);
    frontcap->SetLineColor(20); 
    endcap   = gGeoManager->MakeTube("EndCap", steel, 0, 15./2., 2.5/2.);
    endcap->SetLineColor(20); 
    targettube = gGeoManager->MakeTube("TargetTube", steel, fDiameter/2.+0.5, fDiameter/2.+1.1, fTargetLength/2.-0.225);
    targettube->SetLineColor(20);  
    
    TGeoVolume *target;
    TGeoVolume *slit; 

    for (Int_t i=0; i<fnS; i++) {
       TString nmi = "Target_"; nmi += i+1;
       TString sm = "Slit_";   sm += i+1;
       TGeoMedium *material;
       if (fM.at(i)=="molybdenummisis") {material = momisis;};

       if (fM.at(i)=="tungstenmisis")   {material = tungstenmisis;};

       
       if (fnS == 18) { // new target layout
          target = gGeoManager->MakeTube(nmi, material, 0., fDiameter/2., fL.at(i)/2.);                     
       }
       else {
          target = gGeoManager->MakeBox(nmi, material, fDiameter/2., fDiameter/2., fL.at(i)/2.);
       }
       if (fM.at(i)=="molybdenummisis") {
         target->SetLineColor(28);
       } else {target->SetLineColor(38);};  // silver/blue
       tTarget->AddNode(target, 1, new TGeoTranslation(0, 0, zPos + fL.at(i)/2.) );
       if (i < slots){
        if(fnS == 18) {
	  slit = gGeoManager->MakeTube(sm, plasticbase, 0., fDiameter/2., fsl/2.);  
	}
	else {  
	  slit   = gGeoManager->MakeBox(sm, water, fDiameter/2., fDiameter/2., fsl/2.);
	}  
        slit->SetLineColor(7);  // cyan
	if (i==0) {
           tTarget->AddNode(frontcap, 11, new TGeoTranslation(0, 0, zPos-1.251) );	  
	}	
        tTarget->AddNode(slit, 1, new TGeoTranslation(0, 0, zPos+fL.at(i)+fsl/2.) );
        zPos+=fL.at(i)+fsl;
       } else {
         zPos+=fL.at(i);
	 if (fnS==18) {
               tTarget->AddNode(endcap, 12, new TGeoTranslation(0, 0, zPos+1.29) );	
               tTarget->AddNode(targettube, 13, new TGeoTranslation(0, 0, fTargetLength/2.-4.815));   //-3.245   
	  }	 
	  zPos+=1.27;   
	 }
    } 

    TGeoVolume *absorber;
    TGeoVolume *absorbercutout;
    TGeoVolume *aboveabsorbershield;
    TGeoVolume *ironshield;
    TGeoVolume *concreteshield;
    TGeoVolume *abovetargetshield;
    TGeoVolume *aboveabovetargetshield;  
    
    zPos =  fTargetZ - fTargetLength/2.;
    // Absorber made of iron 
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
 
    TGeoShapeAssembly* asmb = dynamic_cast<TGeoShapeAssembly*>(tTarget->GetShape());
    Double_t totLength = asmb->GetDZ();
    top->AddNode(tTarget, 1, new TGeoTranslation(0, 0,fTargetZ - fTargetLength/2. + totLength+2.5));    
    top->AddNode(ironshield, 2, new TGeoTranslation(-50., -45.,fTargetZ - 83.49));    //3.6
    top->AddNode(concreteshield, 3, new TGeoTranslation(85.,-45.,fTargetZ - 83.49));   
    top->AddNode(abovetargetshield, 4, new TGeoTranslation(50.,77.5,fTargetZ - 83.49)); 
    top->AddNode(aboveabovetargetshield, 5, new TGeoTranslation(-50.,165.0,fAbsorberZ-zPos-624.5)); 
    top->AddNode(aboveabsorbershield, 6, new TGeoTranslation(0.,165.0,-31.48));        

    cout << "target and absorber positioned at " << fTargetZ <<" "<< fAbsorberZ << " m"<< endl;

}

ClassImp(MufluxTargetStation)
