// Spectrometer.cxx
// Magnetic Spectrometer, four tracking stations in a magnetic field.

#include "Spectrometer.h"
//#include "MagneticSpectrometer.h" 
#include "SpectrometerPoint.h"
#include "TGeoManager.h"
#include "FairRun.h"                    // for FairRun
#include "FairRuntimeDb.h"              // for FairRuntimeDb
#include "Riosfwd.h"                    // for ostream
#include "TList.h"                      // for TListIter, TList (ptr only)
#include "TObjArray.h"                  // for TObjArray
#include "TString.h"                    // for TString
#include "TClonesArray.h"
#include "TVirtualMC.h"

#include "TGeoBBox.h"
#include "TGeoTrd1.h"
#include "TGeoCompositeShape.h"
#include "TGeoTube.h"
#include "TGeoArb8.h"
#include "TGeoMaterial.h"
#include "TGeoMedium.h"
#include "TParticle.h"
#include "TVector3.h"

#include "FairVolume.h"
#include "FairGeoVolume.h"
#include "FairGeoNode.h"
#include "FairRootManager.h"
#include "FairGeoLoader.h"
#include "FairGeoInterface.h"
#include "FairGeoMedia.h"
#include "FairGeoBuilder.h"
#include "FairRun.h"
#include "FairRuntimeDb.h"

#include "ShipDetectorList.h"
#include "ShipUnit.h"
#include "ShipStack.h"

#include "TGeoUniformMagField.h"
#include <stddef.h>                     // for NULL
#include <iostream>                     // for operator<<, basic_ostream, etc

using std::cout;
using std::endl;
using namespace ShipUnit;

Spectrometer::Spectrometer()
  : FairDetector("HighPrecisionTrackers",kTRUE, kSpectrometer),
    fTrackID(-1),
    fPdgCode(),
    fVolumeID(-1),
    fPos(),
    fMom(),
    fTime(-1.),
    fLength(-1.),
    fELoss(-1),
    fSpectrometerPointCollection(new TClonesArray("SpectrometerPoint"))
{
}

Spectrometer::Spectrometer(const char* name, const Double_t DX, const Double_t DY, const Double_t DZ, Bool_t Active,const char* Title)
  : FairDetector(name, Active, kSpectrometer),
    fTrackID(-1),
    fPdgCode(),
    fVolumeID(-1),
    fPos(),
    fMom(),
    fTime(-1.),
    fLength(-1.),
    fELoss(-1),
    fSpectrometerPointCollection(new TClonesArray("SpectrometerPoint"))
{ 
  DimX = DX;
  DimY = DY;
  DimZ = DZ;
}

Spectrometer::~Spectrometer()
{
    if (fSpectrometerPointCollection) {
        fSpectrometerPointCollection->Delete();
        delete fSpectrometerPointCollection;
    }
}

void Spectrometer::Initialize()
{
    FairDetector::Initialize();
}

//Sets the dimension of the Magnetic Spectrometer volume in which the HPT are placed
/*void Spectrometer::SetZsize(const Double_t MSsize)
{
  zSizeMS = MSsize;
}
*/

// -----   Private method InitMedium 
Int_t Spectrometer::InitMedium(const char* name)
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

void Spectrometer::SetBoxParam(Double_t SX, Double_t SY, Double_t SZ, Double_t zBox)
{
  SBoxX = SX;
  SBoxY = SY;
  SBoxZ = SZ;
  zBoxPosition = zBox;
}
//Methods for Goliath by Annarita
void Spectrometer::SetGoliathSizes(Double_t H, Double_t TS, Double_t LS, Double_t BasisH)
{
    LongitudinalSize = LS;
    TransversalSize = TS;
    Height = H;
    BasisHeight = BasisH;
}

void Spectrometer::SetCoilParameters(Double_t CoilR, Double_t UpCoilH, Double_t LowCoilH, Double_t CoilD)
{
    CoilRadius = CoilR;
    UpCoilHeight = UpCoilH;
    LowCoilHeight = LowCoilH;
    CoilDistance = CoilD;
}
//
void Spectrometer::ConstructGeometry()
{ 
    InitMedium("vacuum");
  TGeoMedium *vacuum = gGeoManager->GetMedium("vacuum");

    InitMedium("iron");
    TGeoMedium *Fe =gGeoManager->GetMedium("iron");

    InitMedium("CoilCopper");
    TGeoMedium *Cu  = gGeoManager->GetMedium("CoilCopper");

    InitMedium("CoilAluminium");
    TGeoMedium *Al  = gGeoManager->GetMedium("CoilAluminium");
  
  TGeoVolume *top = gGeoManager->GetTopVolume();

  const Double_t MagneticField = 1 * tesla; //magnetic field
  TGeoUniformMagField *magfield = new TGeoUniformMagField(0., MagneticField, 0.); //The magnetic field must be only in the vacuum space between the stations

  TGeoBBox *SpectrometerBox = new TGeoBBox("SpectrometerBox", SBoxX/2, SBoxY/2, SBoxZ/2);
  TGeoVolume *volSciFi = new TGeoVolume("volSciFi", SpectrometerBox, vacuum);
  volSciFi->SetTransparency(1);
  
  //  top->AddNode(volSciFi,1,new TGeoTranslation(0,0,zBoxPosition));
  // Double_t Goloffset = 4.5*m; //additional space required for the Goliath magnet
  TGeoBBox *ProvaBox = new TGeoBBox("ProvaBox", DimX/2  + 1 * m/2, DimY/2  + 1 * m/2, SBoxZ/2);
  TGeoVolume *volProva = new TGeoVolume("volProva", ProvaBox, vacuum);
  volProva->SetTransparency(1);

  top->AddNode(volProva,1,new TGeoTranslation(0,0,zBoxPosition));
  
    InitMedium("Scintillator");
    TGeoMedium *Scintillator = gGeoManager->GetMedium("Scintillator");

    TGeoBBox *SciFi1 = new TGeoBBox("SciFi1", (DimX-87*cm)/2, (DimY-39*cm)/2, DimZ/2); //planes now have different dimensions (DimX è 1m,DimY è 0.5m)
      TGeoVolume *subvolSciFi1 = new TGeoVolume("volSciFi1",SciFi1,Scintillator);
    // TGeoVolume *subvolSciFi1 = new TGeoVolume("volSciFi1",SciFi1,vacuum);
    subvolSciFi1->SetLineColor(kBlue-5);
    AddSensitiveVolume(subvolSciFi1);

    TGeoBBox *SciFi2 = new TGeoBBox("SciFi2", (DimX-80*cm)/2, (DimY-30*cm)/2, DimZ/2);
    TGeoVolume *subvolSciFi2 = new TGeoVolume("volSciFi2",SciFi2,Scintillator);
   // TGeoVolume *subvolSciFi2 = new TGeoVolume("volSciFi2",SciFi2,vacuum);
    subvolSciFi2->SetLineColor(kBlue-5);
    AddSensitiveVolume(subvolSciFi2);
    
    TGeoBBox *SciFi3 = new TGeoBBox("SciFi3", DimX/2 + 1*m/2 , DimY/2 + 1*m/2, DimZ/2); 
    TGeoVolume *subvolSciFi3 = new TGeoVolume("volSciFi3",SciFi3,Scintillator);
    //TGeoVolume *subvolSciFi3 = new TGeoVolume("volSciFi3",SciFi3,vacuum);
    subvolSciFi3->SetLineColor(kBlue-5);
    AddSensitiveVolume(subvolSciFi3);

    TGeoBBox *SciFi4 = new TGeoBBox("SciFi4", DimX/2 + 1*m/2, DimY/2 + 1*m/2 , DimZ/2); 
    TGeoVolume *subvolSciFi4 = new TGeoVolume("volSciFi4",SciFi4,Scintillator);
    //TGeoVolume *subvolSciFi4 = new TGeoVolume("volSciFi4",SciFi4,vacuum);
    subvolSciFi4->SetLineColor(kBlue-5);
    AddSensitiveVolume(subvolSciFi4);

    
    //Double_t z[4] = {0,20*cm,1*m+20*cm,1*m + 40*cm}; //distanze relative (20 cm fra le stazioni) (situazione precedente)
    

    Double_t z[4] = {DimZ/2., DimZ/2. +20*cm + DimZ, DimZ/2. + 4.5*m +20*cm + 2 * DimZ, DimZ/2. + 4.5*m + 40*cm + 3 * DimZ}; //relative distances (20 cm between tracking stations) (after implementation of Goliath)
    //const int nreplica = 4;

    volProva->AddNode(subvolSciFi1,1,new TGeoTranslation(0,0,-SBoxZ/2 + z[0]));
    volProva->AddNode(subvolSciFi2,1,new TGeoTranslation(0,0,-SBoxZ/2 + z[1]));
    volProva->AddNode(subvolSciFi3,1,new TGeoTranslation(0,0,-SBoxZ/2 + z[2]));
    volProva->AddNode(subvolSciFi4,1,new TGeoTranslation(0,0,-SBoxZ/2 + z[3]));

 
    /*    for(int n = 0; n<nreplica; n++){
    volProva->AddNode(subvolSciFi,n,new TGeoTranslation(0,0,-SBoxZ/2 + z[n]));
     }*/
  
   TGeoBBox *VacuumBox = new TGeoBBox("VacuumBox", TransversalSize/2, 90*cm/2., (175 * cm)/2.);
    TGeoVolume *volVacuum = new TGeoVolume("VolVacuum", VacuumBox, vacuum);
    volVacuum->SetVisibility(0);
    volVacuum->SetField(magfield);
    volVacuum->SetLineColor(kYellow);
    // volProva->AddNode(volVacuum, 1, new TGeoTranslation(0,0,-SBoxZ/2 + z[1] + DimZ/2+50*cm)); //commented to insert the new Goliath
    volProva->AddNode(volVacuum, 1, new TGeoTranslation(0,-5 * cm,-SBoxZ/2 + z[1] + LongitudinalSize/2.)); //commented to insert the new Goliath 
    
    TGeoUniformMagField *magField2 = new TGeoUniformMagField(0.,MagneticField,0.); //magnetic field in target (how to insert in my case???)

 
    
      //***********************************************************************************************
    //*****************************************   GOLIATH BY ANNARITA *****************************************
    //***********************************************************************************************
    //    Double_t MagneticField = 1*tesla;
    
    TGeoUniformMagField *magField1 = new TGeoUniformMagField(0.,-MagneticField,0.); //magnetic field in Goliath pillars
    
    TGeoBBox *BoxGoliath = new TGeoBBox(TransversalSize/2,Height/2,LongitudinalSize/2);
    TGeoVolume *volGoliath = new TGeoVolume("volGoliath",BoxGoliath,vacuum);
    //volProva->AddNode(volGoliath,1,new TGeoTranslation(0,0,-SBoxZ/2 + z[1] + LongitudinalSize/2));  
    //Goliath raised by 17cm
    top->AddNode(volGoliath,1,new TGeoTranslation(0,17*cm,zBoxPosition-SBoxZ/2 + z[1] + LongitudinalSize/2)); 
    //
    //******* UPPER AND LOWER BASE *******
    //
    
    TGeoBBox *Base = new TGeoBBox(TransversalSize/2,BasisHeight/2,LongitudinalSize/2);
    TGeoVolume *volBase = new TGeoVolume("volBase",Base,Fe);
    volBase->SetLineColor(kRed);
    //volBase->SetTransparency(7);
    volGoliath->AddNode(volBase,1,new TGeoTranslation(0, Height/2 - BasisHeight/2, 0)); //upper part
    volGoliath->AddNode(volBase,2,new TGeoTranslation(0, -Height/2 + BasisHeight/2, 0)); //lower part
    
    //
    //**************************** MAGNETS ******************************
    //
    
    TGeoRotation *r1 = new TGeoRotation();
    r1->SetAngles(0,90,0);
    TGeoCombiTrans t1(0, Height/2 - BasisHeight - UpCoilHeight/2, 0,r1);
    //t1.Print();
    TGeoHMatrix *m1 = new TGeoHMatrix(t1);
    
    TGeoTube *magnetUp = new TGeoTube(0,CoilRadius,UpCoilHeight/2);
    TGeoVolume *volmagnetUp = new TGeoVolume("volmagnetUp",magnetUp,Cu);
    volmagnetUp->SetLineColor(kGreen);
    volGoliath->AddNode(volmagnetUp,1,m1); //upper part
    
    
    TGeoCombiTrans t2(0, -Height/2 + BasisHeight + LowCoilHeight/2, 0,r1);
    TGeoHMatrix *m_2 = new TGeoHMatrix(t2);
    
    
    TGeoTube *magnetDown = new TGeoTube(0,CoilRadius,LowCoilHeight/2);
    TGeoVolume *volmagnetDown = new TGeoVolume("volmagnetDown",magnetDown,Al);
    volmagnetDown->SetLineColor(kGreen);
    volGoliath->AddNode(volmagnetDown,1,m_2); //lower part
    
    //
    //********************* LATERAL SURFACES ****************************
    //
    
    Double_t base1 = 135, base2 = 78; //basis of the trapezoid
    Double_t side1 = 33, side2 = 125, side3 = 57, side4 = 90; //Sides of the columns
    
    //***** SIDE Left Front ****
    
    //LONGER RECTANGLE
    TGeoBBox *LateralS1 = new TGeoBBox("LateralS1",side1/2,UpCoilHeight/2,base1/2);
    TGeoTranslation *tr1 = new TGeoTranslation(-TransversalSize/2 + side1/2, Height/2 - BasisHeight - UpCoilHeight/2, -LongitudinalSize/2 + base1/2);
    TGeoVolume *volLateralS1 = new TGeoVolume("volLateralS1",LateralS1,Fe);
    volLateralS1->SetLineColor(kRed);
    volLateralS1->SetField(magField1);
    volGoliath->AddNode(volLateralS1, 1, tr1);
    
    //TRAPEZOID
    
    TGeoArb8 *LateralS2 = new TGeoArb8("LateralS2", UpCoilHeight/2);
    LateralS2->SetVertex(0, side4, 0);
    LateralS2->SetVertex(1, side1, 0);
    LateralS2->SetVertex(2, side1, base1);
    LateralS2->SetVertex(3, side4, base2);
    LateralS2->SetVertex(4, side4, 0);
    LateralS2->SetVertex(5, side1, 0);
    LateralS2->SetVertex(6, side1, base1);
    LateralS2->SetVertex(7, side4, base2);
    
    TGeoVolume *volLateralS2 = new TGeoVolume("volLateralS2",LateralS2,Fe);
    volLateralS2->SetLineColor(kRed);
    volLateralS2->SetField(magField1);
    
    TGeoRotation *r2 = new TGeoRotation();
    r2->SetAngles(0,90,0);
    TGeoCombiTrans tr3(-TransversalSize/2, Height/2 - BasisHeight - UpCoilHeight/2, -LongitudinalSize/2,r2);
    TGeoHMatrix *m3_a = new TGeoHMatrix(tr3);
    volGoliath->AddNode(volLateralS2, 1, m3_a);
    
    
    //LOWER LATERAL SURFACE
    
    //LONGER RECTANGLE
    TGeoBBox *LateralSurface1low = new TGeoBBox("LateralSurface1low",side1/2,(CoilDistance + LowCoilHeight)/2,side2/2);
    TGeoVolume *volLateralSurface1low = new TGeoVolume("volLateralSurface1low",LateralSurface1low,Fe);
    volLateralSurface1low->SetLineColor(kRed);
    volLateralSurface1low->SetField(magField1);
    TGeoTranslation *tr1low = new TGeoTranslation(-TransversalSize/2 +side1/2, Height/2 - BasisHeight - UpCoilHeight - (CoilDistance + LowCoilHeight)/2, -LongitudinalSize/2 + side2/2);
    volGoliath->AddNode(volLateralSurface1low, 1, tr1low);;
    
    
    //SHORTER RECTANGLE
    TGeoBBox *LateralSurface2low = new TGeoBBox("LateralSurface2low",side3/2,(CoilDistance + LowCoilHeight)/2,base2/2);
    TGeoVolume *volLateralSurface2low = new TGeoVolume("volLateralSurface2low",LateralSurface2low,Fe);
    volLateralSurface2low->SetLineColor(kRed);
    TGeoTranslation *tr2low = new TGeoTranslation(-TransversalSize/2 +side1 + side3/2, Height/2 - BasisHeight - UpCoilHeight - (CoilDistance + LowCoilHeight)/2, -LongitudinalSize/2 + base2/2);
    volGoliath->AddNode(volLateralSurface2low, 1, tr2low);
    volLateralSurface2low->SetField(magField1);
    
    //***** SIDE Right Front ****
    
    //LONGER RECTANGLE
    TGeoTranslation *tr1_b = new TGeoTranslation(-TransversalSize/2 + side1/2, Height/2 - BasisHeight - UpCoilHeight/2, LongitudinalSize/2 - base1/2);
    TGeoVolume *volLateralS1_b = new TGeoVolume("volLateralS1_b",LateralS1,Fe);
    volLateralS1_b->SetLineColor(kRed);
    volLateralS1_b->SetField(magField1);
    volGoliath->AddNode(volLateralS1_b, 1, tr1_b);
    
    //TRAPEZOID
    TGeoArb8 *LateralS2_b = new TGeoArb8("LateralS2_b",UpCoilHeight/2);
    LateralS2_b ->SetVertex(0, side4, 0);
    LateralS2_b ->SetVertex(1, side1, 0);
    LateralS2_b ->SetVertex(2, side1, base1);
    LateralS2_b ->SetVertex(3, side4, base2);
    LateralS2_b ->SetVertex(4, side4, 0);
    LateralS2_b ->SetVertex(5, side1, 0);
    LateralS2_b ->SetVertex(6, side1, base1);
    LateralS2_b ->SetVertex(7, side4, base2);
    
    TGeoVolume *volLateralS2_b = new TGeoVolume("volLateralS2_b",LateralS2_b,Fe);
    volLateralS2_b->SetLineColor(kRed);
    volLateralS2_b->SetField(magField1);
    
    TGeoRotation *r2_b = new TGeoRotation();
    r2_b->SetAngles(0,270,0);
    TGeoCombiTrans tr2_b(-TransversalSize/2 , Height/2 - BasisHeight - UpCoilHeight/2, LongitudinalSize/2,r2_b);
    TGeoHMatrix *m3_b = new TGeoHMatrix(tr2_b);
    volGoliath->AddNode(volLateralS2_b, 1, m3_b);
    
    
    //LOWER LATERAL SURFACE
    
    //LONGER RECTANGLE
    TGeoVolume *volLateralSurface1blow = new TGeoVolume("volLateralSurface1blow",LateralSurface1low,Fe);
    volLateralSurface1blow->SetLineColor(kRed);
    volLateralSurface1blow->SetField(magField1);
    TGeoTranslation *tr1blow = new TGeoTranslation(-TransversalSize/2 +side1/2, Height/2 - BasisHeight - UpCoilHeight - (CoilDistance + LowCoilHeight)/2, LongitudinalSize/2 - side2/2);
    volGoliath->AddNode(volLateralSurface1blow, 1, tr1blow);;
    
    
    //SHORTER RECTANGLE
    TGeoVolume *volLateralSurface2blow = new TGeoVolume("volLateralSurface2blow",LateralSurface2low,Fe);
    volLateralSurface2blow->SetLineColor(kRed);
    volLateralSurface2blow->SetField(magField1);
    TGeoTranslation *tr2blow = new TGeoTranslation(-TransversalSize/2 +side1 + side3/2, Height/2 - BasisHeight - UpCoilHeight - (CoilDistance + LowCoilHeight)/2, LongitudinalSize/2 - base2/2);
    volGoliath->AddNode(volLateralSurface2blow, 1, tr2blow);
    
    
    //***** SIDE left Back ****
    
    
    //LONGER RECTANGLE
    TGeoBBox *LateralS1_d = new TGeoBBox("LateralS1_d",side1/2,(UpCoilHeight + LowCoilHeight + CoilDistance)/2,base1/2);
    TGeoTranslation *tr1_d = new TGeoTranslation(TransversalSize/2 - side1/2, Height/2 - BasisHeight - (UpCoilHeight + LowCoilHeight + CoilDistance)/2, -LongitudinalSize/2 + base1/2);
    TGeoVolume *volLateralS1_d = new TGeoVolume("volLateralS1_d",LateralS1_d,Fe);
    volLateralS1_d->SetLineColor(kRed);
    volLateralS1_d->SetField(magField1);
    volGoliath->AddNode(volLateralS1_d, 1, tr1_d);
    
    //TRAPEZOID
    
    TGeoArb8 *LateralS2_d = new TGeoArb8("LateralS2_d",(UpCoilHeight + LowCoilHeight + CoilDistance)/2);
    LateralS2_d->SetVertex(0, side4, 0);
    LateralS2_d->SetVertex(1, side1, 0);
    LateralS2_d->SetVertex(2, side1, base1);
    LateralS2_d->SetVertex(3, side4, base2);
    LateralS2_d->SetVertex(4, side4, 0);
    LateralS2_d->SetVertex(5, side1, 0);
    LateralS2_d->SetVertex(6, side1, base1);
    LateralS2_d->SetVertex(7, side4, base2);
    
    
    TGeoVolume *volLateralS2_d = new TGeoVolume("volLateralS2_d",LateralS2_d,Fe);
    volLateralS2_d->SetLineColor(kRed);
    volLateralS2_d->SetField(magField1);
    
    TGeoRotation *r2_d = new TGeoRotation();
    r2_d->SetAngles(0,270,180);
    TGeoCombiTrans tr2_d(TransversalSize/2 , Height/2 - BasisHeight - (UpCoilHeight + LowCoilHeight + CoilDistance)/2, -LongitudinalSize/2,r2_d);
    TGeoHMatrix *m3_d = new TGeoHMatrix(tr2_d);
    volGoliath->AddNode(volLateralS2_d, 1, m3_d);
    
    
    //***** SIDE right Back ****
    
    
    //LONGER RECTANGLE
    TGeoBBox *LateralS1_c = new TGeoBBox("LateralS1_c",side1/2,(UpCoilHeight + LowCoilHeight + CoilDistance)/2,base1/2);
    TGeoTranslation *tr1_c = new TGeoTranslation(TransversalSize/2 - side1/2, Height/2 - BasisHeight - (UpCoilHeight + LowCoilHeight + CoilDistance)/2, LongitudinalSize/2 - base1/2);
    TGeoVolume *volLateralS1_c = new TGeoVolume("volLateralS1_c",LateralS1_c,Fe);
    volLateralS1_c->SetLineColor(kRed);
        volLateralS1_c->SetField(magField1);
    volGoliath->AddNode(volLateralS1_c, 1, tr1_c);
    
    //TRAPEZOID
    
    TGeoArb8 *LateralS2_c = new TGeoArb8("LateralS2_c",(UpCoilHeight + LowCoilHeight + CoilDistance)/2);
    LateralS2_c ->SetVertex(0, side4, 0);
    LateralS2_c ->SetVertex(1, side1, 0);
    LateralS2_c ->SetVertex(2, side1, base1);
    LateralS2_c ->SetVertex(3, side4, base2);
    LateralS2_c ->SetVertex(4, side4, 0);
    LateralS2_c ->SetVertex(5, side1, 0);
    LateralS2_c ->SetVertex(6, side1, base1);
    LateralS2_c ->SetVertex(7, side4, base2);
    
    TGeoVolume *volLateralS2_c = new TGeoVolume("volLateralS2_c",LateralS2_c,Fe);
    volLateralS2_c->SetLineColor(kRed);
    volLateralS2_c->SetField(magField1);
    
    TGeoRotation *r2_c = new TGeoRotation();
    r2_c->SetAngles(0,90,180);
    TGeoCombiTrans tr2_c(TransversalSize/2 , Height/2 - BasisHeight - (UpCoilHeight + LowCoilHeight + CoilDistance)/2, LongitudinalSize/2,r2_c);
    TGeoHMatrix *m3_c = new TGeoHMatrix(tr2_c);
    volGoliath->AddNode(volLateralS2_c, 1, m3_c);

    //END GOLIATH PART BY ANNARITA
    
}

Bool_t  Spectrometer::ProcessHits(FairVolume* vol)
{
    /** This method is called from the MC stepping */
    //Set parameters at entrance of volume. Reset ELoss.
    if ( gMC->IsTrackEntering() ) {
        fELoss  = 0.;
        fTime   = gMC->TrackTime() * 1.0e09;
        fLength = gMC->TrackLength();
        gMC->TrackPosition(fPos);
        gMC->TrackMomentum(fMom);
    }
    // Sum energy loss for all steps in the active volume
    fELoss += gMC->Edep();
    
    // Create muonPoint at exit of active volume
    if ( gMC->IsTrackExiting()    ||
        gMC->IsTrackStop()       ||
        gMC->IsTrackDisappeared()   ) {
        fTrackID  = gMC->GetStack()->GetCurrentTrackNumber();
	fVolumeID = vol->getMCid();
        if (fELoss == 0. ) { return kFALSE; }
        TParticle* p=gMC->GetStack()->GetCurrentTrack();
        Int_t pdgCode = p->GetPdgCode();
	//Int_t fMotherID =p->GetFirstMother();
	Int_t detID=0;
	gMC->CurrentVolID(detID);

	if (fVolumeID == detID) {
	  return kTRUE; }
	fVolumeID = detID;

        TLorentzVector Pos; 
        gMC->TrackPosition(Pos); 
        Double_t xmean = (fPos.X()+Pos.X())/2. ;      
        Double_t ymean = (fPos.Y()+Pos.Y())/2. ;      
        Double_t zmean = (fPos.Z()+Pos.Z())/2. ;     

	AddHit(fTrackID, fVolumeID, TVector3(xmean, ymean,  zmean), TVector3(fMom.Px(), fMom.Py(), fMom.Pz()), fTime, fLength,fELoss, pdgCode);
        
        // Increment number of muon det points in TParticle
        ShipStack* stack = (ShipStack*) gMC->GetStack();
        stack->AddPoint(kSpectrometer);
    }
    
    return kTRUE;
}

void Spectrometer::EndOfEvent()
{
    fSpectrometerPointCollection->Clear();
}


void Spectrometer::Register()
{
    
    /** This will create a branch in the output tree called
     SpectrometerPoint, setting the last parameter to kFALSE means:
     this collection will not be written to the file, it will exist
     only during the simulation.
     */
    
    FairRootManager::Instance()->Register("SpectrometerPoint", "Spectrometer",
                                          fSpectrometerPointCollection, kTRUE);
}

// -----   Public method to Decode volume info  -------------------------------------------
// -----   returns hpt, arm, rpc numbers -----------------------------------
void Spectrometer::DecodeVolumeID(Int_t detID,int &nHPT)
{
  nHPT = detID;
}

TClonesArray* Spectrometer::GetCollection(Int_t iColl) const
{
    if (iColl == 0) { return fSpectrometerPointCollection; }
    else { return NULL; }
}

void Spectrometer::Reset()
{
    fSpectrometerPointCollection->Clear();
}


SpectrometerPoint* Spectrometer::AddHit(Int_t trackID, Int_t detID,
                        TVector3 pos, TVector3 mom,
                        Double_t time, Double_t length,
					    Double_t eLoss, Int_t pdgCode)

{
    TClonesArray& clref = *fSpectrometerPointCollection;
    Int_t size = clref.GetEntriesFast();

    return new(clref[size]) SpectrometerPoint(trackID, detID, pos, mom,time, length, eLoss, pdgCode);
}


ClassImp(Spectrometer)
