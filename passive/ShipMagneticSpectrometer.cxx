#include "ShipMagneticSpectrometer.h"

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
#include "TGeoUniformMagField.h"
#include <stddef.h>                     // for NULL
#include <iostream>                     // for operator<<, basic_ostream, etc

using namespace std;

ShipMagneticSpectrometer::~ShipMagneticSpectrometer()
{
}

ShipMagneticSpectrometer::ShipMagneticSpectrometer()
  : FairModule("ShipMagneticSpectrometer", "")
{
}

ShipMagneticSpectrometer::ShipMagneticSpectrometer(const char* name, const char* Title)
  : FairModule(name ,Title)
{
}

void ShipMagneticSpectrometer::ConstructGeometry()
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
    
    Int_t d = 0;
    
    Double_t Field = 1.57;
    TGeoUniformMagField *magField = new TGeoUniformMagField(0.,-Field,0.);
    TGeoUniformMagField *RetField     = new TGeoUniformMagField(0.,Field,0.);
    
    TGeoBBox *Layer = new TGeoBBox(225,225,2.5);
    TGeoVolume *volLayer = new TGeoVolume("volLayer",Layer,Fe);
    for(Int_t i = 0; i< 12; i++)
    {
        d = -2624.5 - i*7;
        top->AddNode(volLayer,i,new TGeoTranslation(0, 0, d));
    }
    volLayer->SetField(magField);
    
    cout <<"************************************" << endl;
    cout << d << endl;
    Int_t d1 = d-125; //z coord of the center of the last layer of the first spectrometer
    cout << d1 << endl;
    
    TGeoVolume *volLayer2 = new TGeoVolume("volLayer2",Layer,Fe);
    for(Int_t i = 0; i< 12; i++)
    {
        Int_t d2 = d1-i*7;
        top->AddNode(volLayer2,i,new TGeoTranslation(0, 0, d2));
    }
    volLayer2->SetField(RetField);
    
    cout <<"************************************" << endl;
    
    
}



ClassImp(ShipMagneticSpectrometer)














