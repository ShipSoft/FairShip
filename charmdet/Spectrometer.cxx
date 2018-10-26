// Spectrometer.cxx
// Magnetic Spectrometer, four tracking stations in a magnetic field.

#include "Spectrometer.h"
//#include "MagneticSpectrometer.h" 
#include "SpectrometerPoint.h"
#include "TGeoManager.h"
#include "FairRun.h"                    // for FairRun
#include "FairRuntimeDb.h"              // for FairRuntimeDb
#include <iosfwd>                    // for ostream
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
    fbeamx = 0.; //default beam center position in xy plane is origin
    fbeamy = 0.;
}

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

void Spectrometer::SetBoxParam(Double_t SX, Double_t SY, Double_t SZ, Double_t zBox, Double_t SZPixel)
{
  SBoxX = SX;
  SBoxY = SY;
  SBoxZ = SZ;
  zBoxPosition = zBox;
  DimZPixelBox = SZPixel;
}

void Spectrometer::SetSiliconDZ(Double_t SiliconDZ)
{
  DimZSi = SiliconDZ;
}

void Spectrometer::SetSiliconDetPositions(Double_t zSi0, Double_t zSi1, Double_t zSi2, Double_t zSi3, Double_t zSi4, Double_t zSi5, Double_t PairSiDistance)
{ 
 zs0 = zSi0;
 zs1 = zSi1;
 zs2 = zSi2;
 zs3 = zSi3;
 zs4 = zSi4;
 zs5 = zSi5;
 pairwisedistance = PairSiDistance;
}

void Spectrometer::SetSciFiDetPositions(Double_t zSciFi1, Double_t zSciFi2)
{ 
 zposSciFi1 = zSciFi1;
 zposSciFi2 = zSciFi2;
}

void Spectrometer::SetSiliconDetNumber(Int_t nSilicon)
{
 nSi = nSilicon;
}


void Spectrometer::SetTransverseSizes(Double_t D1short, Double_t D1long, Double_t Sioverlap, Double_t DSciFi1X, Double_t DSciFi1Y, Double_t DSciFi2X, Double_t DSciFi2Y){
  Dim1Short = D1short;
  Dim1Long = D1long;
  overlap = Sioverlap;
  DimSciFi1X = DSciFi1X;
  DimSciFi1Y = DSciFi1Y;
  DimSciFi2X = DSciFi2X;
  DimSciFi2Y = DSciFi2Y;
}   

void Spectrometer::GetBeamPosition(Double_t beamx, Double_t beamy)
{
 fbeamx = beamx;
 fbeamy = beamy;
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
    InitMedium("air");
  TGeoMedium *air = gGeoManager->GetMedium("air");

    InitMedium("iron");
    TGeoMedium *Fe =gGeoManager->GetMedium("iron");
    
    InitMedium("silicon");
    TGeoMedium *Silicon = gGeoManager->GetMedium("silicon");

    InitMedium("CoilCopper");
    TGeoMedium *Cu  = gGeoManager->GetMedium("CoilCopper");

    InitMedium("CoilAluminium");
    TGeoMedium *Al  = gGeoManager->GetMedium("CoilAluminium");

    InitMedium("TTmedium");
    TGeoMedium *TT  = gGeoManager->GetMedium("TTmedium");
    
    InitMedium("STTmix8020_2bar");
    TGeoMedium *sttmix8020_2bar   = gGeoManager->GetMedium("STTmix8020_2bar");
  
    TGeoVolume *top = gGeoManager->GetTopVolume();


    //Double_t DimZPixelBox = zs5 -zs0 +pairwisedistance + DimZSi;
    TGeoBBox *PixelBox = new TGeoBBox("PixelBox", Dim1Long/2 + overlap, Dim1Long/2 + overlap, DimZPixelBox/2.);
    TGeoVolume *volPixelBox = new TGeoVolume("volPixelBox",PixelBox,air);

    top->AddNode(volPixelBox, 1, new TGeoTranslation(fbeamx,fbeamy,zBoxPosition));

    TGeoBBox *Pixely = new TGeoBBox("Pixely", Dim1Short/2, Dim1Long/2, DimZSi/2); //long along y
    TGeoVolume *volPixely = new TGeoVolume("volPixely",Pixely,Silicon); 
    volPixely->SetLineColor(kBlue-5);
    AddSensitiveVolume(volPixely);

    TGeoBBox *Pixelx = new TGeoBBox("Pixelx", (Dim1Long)/2, (Dim1Short)/2, DimZSi/2); //long along x
    TGeoVolume *volPixelx = new TGeoVolume("volPixelx",Pixelx,Silicon); 
    volPixelx->SetLineColor(kBlue-5);
    AddSensitiveVolume(volPixelx);

    volPixelBox->AddNode(volPixely, 111, new TGeoTranslation(overlap - Dim1Short/2.,0,-DimZPixelBox/2.+ zs0 - pairwisedistance/2));
    volPixelBox->AddNode(volPixely, 112, new TGeoTranslation(-overlap + Dim1Short/2.,0,-DimZPixelBox/2. + zs0 + pairwisedistance/2));
    volPixelBox->AddNode(volPixelx, 121, new TGeoTranslation(0,overlap - Dim1Short/2.,-DimZPixelBox/2.  + zs1 - pairwisedistance/2)); 
    volPixelBox->AddNode(volPixelx, 122, new TGeoTranslation(0,-overlap + Dim1Short/2.,-DimZPixelBox/2.  +  zs1 + pairwisedistance/2)); 
    volPixelBox->AddNode(volPixely, 131, new TGeoTranslation(overlap - Dim1Short/2.,0,-DimZPixelBox/2. + zs2 - pairwisedistance/2));
    volPixelBox->AddNode(volPixely, 132, new TGeoTranslation(-overlap + Dim1Short/2.,0,-DimZPixelBox/2. +  zs2 + pairwisedistance/2));
    volPixelBox->AddNode(volPixelx, 141, new TGeoTranslation(0,overlap - Dim1Short/2. ,-DimZPixelBox/2. +  zs3 - pairwisedistance/2)); 
    volPixelBox->AddNode(volPixelx, 142, new TGeoTranslation(0,-overlap + Dim1Short/2.,-DimZPixelBox/2. + zs3 + pairwisedistance/2)); 
    volPixelBox->AddNode(volPixely, 151, new TGeoTranslation(overlap - Dim1Short/2.,0,-DimZPixelBox/2. + zs4 - pairwisedistance/2));
    volPixelBox->AddNode(volPixely, 152, new TGeoTranslation(-overlap + Dim1Short/2.,0,-DimZPixelBox/2. + zs4 + pairwisedistance/2));
    volPixelBox->AddNode(volPixelx, 161, new TGeoTranslation(0,overlap - Dim1Short/2.,-DimZPixelBox/2. + zs5 - pairwisedistance/2)); 
    volPixelBox->AddNode(volPixelx, 162, new TGeoTranslation(0,-overlap + Dim1Short/2.,-DimZPixelBox/2. + zs5 + pairwisedistance/2)); 
    
    TGeoBBox *SciFi1 = new TGeoBBox("SciFi1", DimSciFi1X/2, DimSciFi1Y/2, DimZ/2); 
    TGeoVolume *subvolSciFi1 = new TGeoVolume("volSciFi1",SciFi1,sttmix8020_2bar);
    subvolSciFi1->SetLineColor(kBlue-5);
    AddSensitiveVolume(subvolSciFi1);
  		
    TGeoBBox *SciFi2 = new TGeoBBox("SciFi2", DimSciFi2X/2, DimSciFi2Y/2, DimZ/2);
    TGeoVolume *subvolSciFi2 = new TGeoVolume("volSciFi2",SciFi2,sttmix8020_2bar);
    subvolSciFi2->SetLineColor(kBlue-5);
    AddSensitiveVolume(subvolSciFi2);    

    top->AddNode(subvolSciFi1,1,new TGeoTranslation(0,0,zposSciFi1)); //DetectorIDs are 1 and 2
    top->AddNode(subvolSciFi2,2,new TGeoTranslation(0,0,zposSciFi2));
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

        if (fELoss == 0. ) { return kFALSE; }
        TParticle* p=gMC->GetStack()->GetCurrentTrack();
        Int_t pdgCode = p->GetPdgCode();
	//Int_t fMotherID =p->GetFirstMother();
        gMC->CurrentVolID(fVolumeID);	

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
