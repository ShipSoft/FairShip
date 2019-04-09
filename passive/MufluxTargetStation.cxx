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

void MufluxTargetStation::SetIronAbsorber(Double_t absorber_x, Double_t absorber_y)
{
    fabsorber_x=absorber_x;
    fabsorber_y=absorber_y;
    
}


void MufluxTargetStation::SetAbsorberCutout(Double_t absorbercutout_x, Double_t absorbercutout_y)
{
    fabsorbercutout_x=absorbercutout_x;
    fabsorbercutout_y=absorbercutout_y;
}

void MufluxTargetStation::SetIronShield(Double_t ironshield_x, Double_t ironshield_y, Double_t ironshield_z)
{    
   fironshield_x=ironshield_x;
   fironshield_y=ironshield_y;
   fironshield_z=ironshield_z;
}

void MufluxTargetStation::SetConcreteShield(Double_t concreteshield_x, Double_t concreteshield_y, Double_t concreteshield_z)
{
    fconcreteshield_x=concreteshield_x;
    fconcreteshield_y=concreteshield_y;
    fconcreteshield_z=concreteshield_z;
}

void MufluxTargetStation::SetAboveTargetShield(Double_t abovetargetshield_x, Double_t abovetargetshield_y,Double_t abovetargetshield_z)
{
    fabovetargetshield_x=abovetargetshield_x;
    fabovetargetshield_y=abovetargetshield_y;
    fabovetargetshield_z=abovetargetshield_z;
}

void MufluxTargetStation::SetAboveAbsorberShield(Double_t aboveabsorbershield_x, Double_t aboveabsorbershield_y, Double_t aboveabsorbershield_z)
{
    faboveabsorbershield_x=aboveabsorbershield_x;
    faboveabsorbershield_y=aboveabsorbershield_y;
    faboveabsorbershield_z=aboveabsorbershield_z;
}

void MufluxTargetStation::SetAboveAboveTargetShield(Double_t aboveabovetargetshield_y)   
{
  
    faboveabovetargetshield_y=aboveabovetargetshield_y;
    
}

void MufluxTargetStation::SetFloor(Double_t floor_x, Double_t floor_y, Double_t floor_z)
{   
    ffloor_x=floor_x;
    ffloor_y=floor_y;
    ffloor_z=floor_z;
}

void MufluxTargetStation::SetFloorT34(Double_t floorT34_x, Double_t floorT34_y, Double_t floorT34_z)
{
    ffloorT34_x=floorT34_x;
    ffloorT34_y=floorT34_y;
    ffloorT34_z=floorT34_z;
}

void MufluxTargetStation::SetFloorRPC(Double_t floorRPC_x, Double_t floorRPC_y, Double_t floorRPC_z)
{     
    ffloorRPC_x=floorRPC_x;
    ffloorRPC_y=floorRPC_y;
    ffloorRPC_z=floorRPC_z;
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
      
    TGeoVolume *frontcap;
    TGeoVolume *endcap;   
    TGeoVolume *targettube;   
    frontcap   = gGeoManager->MakeTube("FrontCap", steel, 0, 15./2., 0.5/2.);
    frontcap->SetLineColor(20); 
    endcap   = gGeoManager->MakeTube("EndCap", steel, 0, 15./2., 0.5/2.);
    endcap->SetLineColor(20); 
    targettube = gGeoManager->MakeTube("TargetTube", steel, fDiameter/2.+0.5, fDiameter/2.+1.1, fTargetLength/2.-0.5); //subtract 1 (front&endcaps)
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
           tTarget->AddNode(frontcap, 11, new TGeoTranslation(0, 0, zPos-0.2501) );	  
	}	
        tTarget->AddNode(slit, 1, new TGeoTranslation(0, 0, zPos+fL.at(i)+fsl/2.) );
        zPos+=fL.at(i)+fsl;
       } else {
         zPos+=fL.at(i);
	 if (fnS==18) {
	       tTarget->AddNode(targettube, 13, new TGeoTranslation(0, 0, fTargetLength/2-0.5));    
	       tTarget->AddNode(endcap, 12, new TGeoTranslation(0, 0, fTargetLength-0.7499) );	     
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
    TGeoVolume *floor; 
    TGeoVolume *floorT34; 
    TGeoVolume *floorRPC;     
    
    zPos =  fTargetZ - fTargetLength/2.;
    // Absorber made of iron 
    absorber = gGeoManager->MakeBox("Absorber", iron, fabsorber_x, fabsorber_y, fAbsorberLength/2.); 
    absorbercutout = gGeoManager->MakeBox("AbsorberCO", iron, fabsorbercutout_x, fabsorbercutout_y, fAbsorberLength/2.); 

    ironshield = gGeoManager->MakeBox("IronShield", iron, fironshield_x, fironshield_y, fironshield_z);  
    concreteshield = gGeoManager->MakeBox("ConcreteShield", concrete, fconcreteshield_x, fconcreteshield_y, fconcreteshield_z); 
    abovetargetshield = gGeoManager->MakeBox("AboveTargetShield", concrete, fabovetargetshield_x, fabovetargetshield_y, fabovetargetshield_z); 
    aboveabsorbershield = gGeoManager->MakeBox("AboveBsorberShield", concrete, faboveabsorbershield_x, faboveabsorbershield_y, faboveabsorbershield_z); 
    aboveabovetargetshield = gGeoManager->MakeBox("AboveAboveTargetShield", concrete, fAbsorberLength, faboveabovetargetshield_y, fAbsorberLength); 
    floor = gGeoManager->MakeBox("Floor", concrete, ffloor_x, ffloor_y, ffloor_z);
    floorT34 = gGeoManager->MakeBox("FloorT34", concrete, ffloorT34_x, ffloorT34_y, ffloorT34_z);
    floorRPC = gGeoManager->MakeBox("FloorRPC", concrete, ffloorRPC_x, ffloorRPC_y, ffloorRPC_z);
    
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
    
    //TGeoNode *node = GetNode("Absorber");    
    //tTarget->ReplaceNode(node,new TGeoTube(1.,2.,10.),new TGeoTranslation(0,-100.2,12),iron); //
        
    tTarget->AddNode(floor, 7, new TGeoTranslation(0., -217., 500.)); 
    tTarget->AddNode(floorT34, 8, new TGeoTranslation(0., -120., fAbsorberZ-zPos+771.125)); 
    tTarget->AddNode(floorRPC, 9, new TGeoTranslation(0., -94.49, fAbsorberZ-zPos+1075.));
    
    TGeoShapeAssembly* asmb = dynamic_cast<TGeoShapeAssembly*>(tTarget->GetShape());
    Double_t totLength = asmb->GetDZ();

    top->AddNode(tTarget, 1, new TGeoTranslation(0, 0,fTargetZ - fTargetLength/2. + totLength));  
    top->AddNode(ironshield, 2, new TGeoTranslation(-50., -47.5,fTargetZ - 83.49));    //3.6
    top->AddNode(concreteshield, 3, new TGeoTranslation(85.,-47.5,fTargetZ - 83.49));   
    top->AddNode(abovetargetshield, 4, new TGeoTranslation(50.,77.5,fTargetZ - 83.49)); 
    top->AddNode(aboveabovetargetshield, 5, new TGeoTranslation(-50.,165.0,fAbsorberZ-zPos-624.5)); 
    top->AddNode(aboveabsorbershield, 6, new TGeoTranslation(0.,165.0,-26.48));        

    cout << "target and absorber positioned at " << fTargetZ <<" "<< fAbsorberZ << " m"<< endl;

}

ClassImp(MufluxTargetStation)
