#include "ShipTAUMagneticSpectrometer.h"

#include "TGeoManager.h"
#include "FairRun.h"                    // for FairRun
#include "FairRuntimeDb.h"              // for FairRuntimeDb
//#include "FairGeoMedia.h"
//#include "FairGeoBuilder.h"

#include <iosfwd>                    // for ostream
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

ShipTAUMagneticSpectrometer::~ShipTAUMagneticSpectrometer()
{
}

ShipTAUMagneticSpectrometer::ShipTAUMagneticSpectrometer()
  : FairModule("ShipTAUMagneticSpectrometer", "")
{
}

ShipTAUMagneticSpectrometer::ShipTAUMagneticSpectrometer(const char* name,const Double_t zLS,const Double_t FeL, const Double_t AirL, const Double_t SpectroL, const Double_t GapV, const Double_t DGap, const Double_t MGap, const Double_t mf, const char* Title)
  : FairModule(name ,Title)
{
    zLastSlab = zLS;
    IronLenght = FeL;
    AirLenght = AirL;
    SpectrometerLenght = SpectroL;
    GapFromVacuum = GapV;
    DriftGap = DGap;
    MiddleGap = MGap;
    MagneticField = mf;
}

void ShipTAUMagneticSpectrometer::ConstructGeometry()
{
    Int_t NIronSlabs = 12;
    
    TGeoVolume *top=gGeoManager->GetTopVolume();
    TGeoMedium *Fe  = gGeoManager->GetMedium("iron");
    
    Double_t d = 0;
    
    TGeoUniformMagField *magField = new TGeoUniformMagField(0.,-MagneticField,0.);
    TGeoUniformMagField *RetField     = new TGeoUniformMagField(0.,MagneticField,0.);
    
    TGeoBBox *Layer = new TGeoBBox(225,400,IronLenght/2);
    TGeoVolume *volLayer = new TGeoVolume("volLayer",Layer,Fe);
    for(Int_t i = 0; i< NIronSlabs; i++)
    {
        d = zLastSlab - i*(IronLenght+AirLenght);
        top->AddNode(volLayer,i,new TGeoTranslation(0, 0, d));
    }
    volLayer->SetField(magField);
    
    cout <<"************************************" << endl;
    cout << " IronLenght+AirLenght = " << IronLenght+AirLenght << endl;
    cout << " NIronSlabs = " << NIronSlabs << endl;
    cout << " zLastSlab = "<< zLastSlab << endl;
    cout << d << endl;
    Double_t d1 = d- (MiddleGap + IronLenght); //z coord of the center of the last layer of the first spectrometer
    cout << d1 << endl;
    
    TGeoVolume *volLayer2 = new TGeoVolume("volLayer2",Layer,Fe);
    for(Int_t i = 0; i< NIronSlabs; i++)
    {
        Double_t d2 = d1-i*(IronLenght+AirLenght);
        top->AddNode(volLayer2,i,new TGeoTranslation(0, 0, d2));
    }
    volLayer2->SetField(RetField);
    
    cout <<"************************************" << endl;
    
    
}



ClassImp(ShipTAUMagneticSpectrometer)














