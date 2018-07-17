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
    //Double_t zPos =  -2.09; //for front end endcap 
    Double_t zPos =  0.; //for front end endcap 
    Int_t slots = fnS;
    slots = slots-1;  
      
    fTargetLength = 154.328;

    TGeoVolume *frontcap;
    TGeoVolume *endcap;   
    TGeoVolume *targettube;   
    frontcap   = gGeoManager->MakeTube("FrontCap", steel, 0, 15./2., 0.5/2.);
    frontcap->SetLineColor(20); 
    endcap   = gGeoManager->MakeTube("EndCap", steel, 0, 15./2., 0.5/2.);
    endcap->SetLineColor(20); 
    targettube = gGeoManager->MakeTube("TargetTube", steel, fDiameter/2.+0.5, fDiameter/2.+1.1, fTargetLength/2.-0.5); //subtract 1 (front&endcaps)
    targettube->SetLineColor(20);  
    std::cout << " *************************************************** " << std::endl;
    Float_t tubelength = fTargetLength/2.-1.0;
    std::cout << " fTargetLength " << fTargetLength << " tubelength "<<tubelength << std::endl;       
    std::cout << " *************************************************** " << std::endl;   
    
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
           tTarget->AddNode(frontcap, 11, new TGeoTranslation(0, 0, zPos-0.2501) );	  
	}	
        tTarget->AddNode(slit, 1, new TGeoTranslation(0, 0, zPos+fL.at(i)+fsl/2.) );
        zPos+=fL.at(i)+fsl;
       } else {
         zPos+=fL.at(i);
	 if (fnS==18) {
               //tTarget->AddNode(endcap, 12, new TGeoTranslation(0, 0, zPos+1.29) );	
               //tTarget->AddNode(targettube, 13, new TGeoTranslation(0, 0, fTargetLength/2.-2.725));  
	       tTarget->AddNode(targettube, 13, new TGeoTranslation(0, 0, fTargetLength/2-0.5));    
	       tTarget->AddNode(endcap, 12, new TGeoTranslation(0, 0, fTargetLength-0.7499) );	     
	  }	 
	  zPos+=1.27;   
	 }
    } 
    std::cout << " *************************************************** " << std::endl;
    std::cout << " *************************************************** " << std::endl;
    std::cout << " fTargetLength " << fTargetLength << " zPos "<<zPos << std::endl;
    std::cout << " *************************************************** " << std::endl;
    std::cout << " *************************************************** " << std::endl;
    
    TGeoVolume *absorber;
    TGeoVolume *absorbercutout;
    TGeoVolume *aboveabsorbershield;
    TGeoVolume *ironshield;
    TGeoVolume *concreteshield;
    TGeoVolume *abovetargetshield;
    TGeoVolume *aboveabovetargetshield; 
    TGeoVolume *floor; 
    TGeoVolume *floorT34; 
    TGeoVolume *floorRPC;     
    
    zPos =  fTargetZ - fTargetLength/2.;
    // Absorber made of iron 
    absorber = gGeoManager->MakeBox("Absorber", iron, 120., 97.5, fAbsorberLength/2.); 
    absorbercutout = gGeoManager->MakeBox("AbsorberCO", iron, 102., 27.5, fAbsorberLength/2.); 

    ironshield = gGeoManager->MakeBox("IronShield", iron, 20., 82.5, 160.);  
    concreteshield = gGeoManager->MakeBox("ConcreteShield", concrete, 40., 82.5, 160.); 
    abovetargetshield = gGeoManager->MakeBox("AboveTargetShield", concrete, 120., 42.5, 160.); 
    aboveabsorbershield = gGeoManager->MakeBox("AboveBsorberShield", concrete, 120., 40.0, 80.); 
    aboveabovetargetshield = gGeoManager->MakeBox("AboveAboveTargetShield", concrete, fAbsorberLength, 40., fAbsorberLength); 
    floor = gGeoManager->MakeBox("Floor", concrete, 500., 80., 800.);
    //floorT34 = gGeoManager->MakeBox("FloorT34", concrete, 500., 16., 95.0);
    floorT34 = gGeoManager->MakeBox("FloorT34", concrete, 500., 16., 118.875);
    floorRPC = gGeoManager->MakeBox("FloorRPC", concrete, 500., 32.5, 110.);
    
    ironshield->SetLineColor(42); // brown / light red	
    concreteshield->SetLineColor(kGray); // gray
    floor->SetLineColor(kGray); // gray
    floorT34->SetLineColor(kGray); // gray
    floorRPC->SetLineColor(kGray); // gray
    aboveabsorbershield->SetLineColor(kGray); // gray
    abovetargetshield->SetLineColor(kGray); // gray
    aboveabovetargetshield->SetLineColor(kGray); // gray
    frontcap->SetLineColor(29); // blue-ish
    endcap->SetLineColor(29); // blue-ish
    absorber->SetLineColor(42); // brown / light red
    tTarget->AddNode(absorbercutout, 11, new TGeoTranslation(18., 97.5, fAbsorberZ-zPos)); 	
    tTarget->AddNode(absorber, 1, new TGeoTranslation(0., -27.5, fAbsorberZ-zPos)); 	
    tTarget->AddNode(floor, 7, new TGeoTranslation(0., -210., 500.)); 
    //tTarget->AddNode(floorT34, 8, new TGeoTranslation(0., -112.5, fAbsorberZ-zPos+768.5)); 
    tTarget->AddNode(floorT34, 8, new TGeoTranslation(0., -112.5, fAbsorberZ-zPos+771.125)); 
    tTarget->AddNode(floorRPC, 9, new TGeoTranslation(0., -97, fAbsorberZ-zPos+1000.));
    TGeoShapeAssembly* asmb = dynamic_cast<TGeoShapeAssembly*>(tTarget->GetShape());
    Double_t totLength = asmb->GetDZ();
    //top->AddNode(tTarget, 1, new TGeoTranslation(0, 0,fTargetZ - fTargetLength/2. + totLength+2.5));    
    top->AddNode(tTarget, 1, new TGeoTranslation(0, 0,fTargetZ - fTargetLength/2. + totLength));  
    top->AddNode(ironshield, 2, new TGeoTranslation(-50., -47.5,fTargetZ - 83.49));    //3.6
    top->AddNode(concreteshield, 3, new TGeoTranslation(85.,-47.5,fTargetZ - 83.49));   
    top->AddNode(abovetargetshield, 4, new TGeoTranslation(50.,77.5,fTargetZ - 83.49)); 
    top->AddNode(aboveabovetargetshield, 5, new TGeoTranslation(-50.,165.0,fAbsorberZ-zPos-624.5)); 
    top->AddNode(aboveabsorbershield, 6, new TGeoTranslation(0.,165.0,-26.48));        

    cout << "target and absorber positioned at " << fTargetZ <<" "<< fAbsorberZ << " m"<< endl;

}

ClassImp(MufluxTargetStation)
