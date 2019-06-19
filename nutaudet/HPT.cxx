//
//  TargetTracker.cxx
//  
//
//  Created by Annarita Buonaura.
//  Design3 added by Antonio Iuliano for HPT
//

#include "HPT.h"
#include "NuTauMudet.h"
#include "HptPoint.h"
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

Hpt::Hpt()
  : FairDetector("HighPrecisionTrackers",kTRUE, ktauHpt),
    fTrackID(-1),
    fPdgCode(),
    fVolumeID(-1),
    fPos(),
    fMom(),
    fTime(-1.),
    fLength(-1.),
    fELoss(-1),
    fHptPointCollection(new TClonesArray("HptPoint"))
{
}

Hpt::Hpt(const char* name, const Double_t DX, const Double_t DY, const Double_t DZ, Bool_t Active,const char* Title)
  : FairDetector(name, Active, ktauHpt),
    fTrackID(-1),
    fPdgCode(),
    fVolumeID(-1),
    fPos(),
    fMom(),
    fTime(-1.),
    fLength(-1.),
    fELoss(-1),
    fHptPointCollection(new TClonesArray("HptPoint"))
{
  DimX = DX;
  DimY = DY;
  DimZ = DZ;
}

Hpt::~Hpt()
{
    if (fHptPointCollection) {
        fHptPointCollection->Delete();
        delete fHptPointCollection;
    }
}

void Hpt::Initialize()
{
    FairDetector::Initialize();
}

//Sets the dimension of the Magnetic Spectrometer volume in which the HPT are placed
void Hpt::SetZsize(const Double_t Mudetsize)
{
  zSizeMudet = Mudetsize;
}

//Sets the dimension of the concrete base on which the external couples of HPTs are placed
void Hpt::SetConcreteBaseDim(Double_t X, Double_t Y, Double_t Z)
{
  fConcreteX = X;
  fConcreteY = Y;
  fConcreteZ = Z;
}

void Hpt::SetDistanceHPTs(Double_t dd) //only for geometry 3
{
  fDistance = dd;
}

void Hpt::SetHPTNumber(Int_t nHPT)
{
 fnHPT = nHPT;
}

void Hpt::SetDesign(Int_t Design)
{
  fDesign = Design;
}

void Hpt::SetSurroundingDetHeight(Double_t height)
{ 
 fSRHeight = height;
}

void Hpt::GetMagnetGeometry(Double_t EmuzC, Double_t EmuY)
{
  fmagnetcenter = EmuzC;
  fmagnety = EmuY;
}

void Hpt::GetNumberofTargets(Int_t ntarget) //in nutautargetdesign 3 more than one neutrino target are considered
{
   fntarget = ntarget;
} 

// -----   Private method InitMedium 
Int_t Hpt::InitMedium(const char* name)
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

void Hpt::ConstructGeometry()
{ 
       
    InitMedium("HPTgas");
    TGeoMedium *HPTmat =gGeoManager->GetMedium("HPTgas");

    InitMedium("Concrete");
    TGeoMedium *Conc =gGeoManager->GetMedium("Concrete");

    // cout << "zSizeMudet = " << zSizeMudet << endl;
    if (fDesign < 3){
    TGeoVolume *volMudetBox = gGeoManager->GetVolume("volNuTauMudet");
    TGeoBBox *HPT = new TGeoBBox("HPT", DimX/2, DimY/2, DimZ/2);
    TGeoVolume *volHPT = new TGeoVolume("volHPT",HPT,HPTmat);
    volHPT->SetLineColor(kBlue-5);
    AddSensitiveVolume(volHPT);
    
    TGeoBBox *Cbase = new TGeoBBox("Cbase", fConcreteX/2, fConcreteY/2, fConcreteZ/2);
    TGeoVolume *volCbase = new TGeoVolume("volCbase",Cbase,Conc);
    volCbase->SetLineColor(kOrange-7);

    //1 closer to Goliath
    volMudetBox->AddNode(volHPT,1,new TGeoTranslation(0,0,-zSizeMudet/2 + DimZ/2));
    volMudetBox->AddNode(volCbase,1,new TGeoTranslation(0,-DimY/2-fConcreteY/2,-zSizeMudet/2 + DimZ/2));

    //2 closer to Arm1
    //NB: 55 cm is the distance between the borders of the last 2 drift tubes
    volMudetBox->AddNode(volHPT,2,new TGeoTranslation(0,0,-zSizeMudet/2 + 3*DimZ/2 +55*cm));
    volMudetBox->AddNode(volCbase,2,new TGeoTranslation(0,-DimY/2-fConcreteY/2,-zSizeMudet/2 + 3*DimZ/2 +55*cm));
   
    //Central Drift tubes // 3 closer to Arm1, 4 closer to Arm2
    volMudetBox->AddNode(volHPT,3,new TGeoTranslation(0,0,-72*cm/2 - DimZ/2));

    //NB: 72cm is the distance between the borders of the central drift tubes
    volMudetBox->AddNode(volHPT,4,new TGeoTranslation(0,0,72*cm/2 + DimZ/2));
   
    
    //After spectro Drift Tubes 5 closer to Arm, 6 closer to decay vessel
    volMudetBox->AddNode(volHPT,5,new TGeoTranslation(0,0,zSizeMudet/2 - 3*DimZ/2 - 55*cm));
    volMudetBox->AddNode(volCbase,5,new TGeoTranslation(0,-DimY/2-fConcreteY/2,zSizeMudet/2 - 3*DimZ/2 - 55*cm));    

    volMudetBox->AddNode(volHPT,6,new TGeoTranslation(0,0,zSizeMudet/2 - DimZ/2));
    volMudetBox->AddNode(volCbase,6,new TGeoTranslation(0,-DimY/2-fConcreteY/2,zSizeMudet/2 - DimZ/2));

    }
    if (fDesign == 3){
    //Trackers that in design 3 follow the target --------------------------------------------------------------------------------------    
    TGeoVolume *volMagRegion=gGeoManager->GetVolume("volMagRegion"); 
    TGeoVolume *volTarget =gGeoManager->GetVolume("volTarget");
    TGeoVolume *tTauNuDet = gGeoManager->GetVolume("tTauNuDet");  

    Double_t DZMagnetizedRegion = ((TGeoBBox*) volMagRegion->GetShape())->GetDZ() *2;  
    Double_t DYMagnetizedRegion = ((TGeoBBox*) volMagRegion->GetShape())->GetDY() *2;  
    Double_t DXMagnetizedRegion = ((TGeoBBox*) volMagRegion->GetShape())->GetDX() *2;      

    Double_t DZTarget = ((TGeoBBox*) volTarget->GetShape())->GetDZ() *2;  

    TGeoBBox *DT = new TGeoBBox("DT", DimX/2, DimY/2, DimZ/2);
    TGeoVolume *volDT = new TGeoVolume("volDT",DT,HPTmat); //downstreamtrackers
    volDT->SetLineColor(kBlue-5);
    AddSensitiveVolume(volDT);

    TGeoBBox *Surroundingdet = new TGeoBBox("Surroundingdet",DXMagnetizedRegion/2., fSRHeight/2, DZMagnetizedRegion/2.);
    TGeoVolume *volSurroundingdet = new TGeoVolume("volSurroundingdet",Surroundingdet, HPTmat);
    AddSensitiveVolume(volSurroundingdet);
    volSurroundingdet->SetLineColor(kBlue);
    tTauNuDet->AddNode(volSurroundingdet,100, new TGeoTranslation(0,+fmagnety/2+fSRHeight/2, fmagnetcenter));
    volMagRegion->AddNode(volSurroundingdet, 200, new TGeoTranslation(0.,+DYMagnetizedRegion/2-fSRHeight/2,0.));
    volMagRegion->AddNode(volSurroundingdet, 300, new TGeoTranslation(0.,-DYMagnetizedRegion/2+fSRHeight/2,0.));
    tTauNuDet->AddNode(volSurroundingdet,400, new TGeoTranslation(0,-fmagnety/2-fSRHeight/2, fmagnetcenter));
    

    Int_t n = 0;
    for(int i=0;i<fnHPT;i++){
	  {
           for (int j = 0; j < fntarget; j++){
           volMagRegion->AddNode(volDT,i+j*fnHPT,new TGeoTranslation(0,0, -DZMagnetizedRegion/2 + DZTarget + DimZ/2 + i*(fDistance+DimZ) + j*(DZTarget+ fnHPT * DimZ + (fnHPT-1)*fDistance)));              
           }
	  }
     }
    }
}

Bool_t  Hpt::ProcessHits(FairVolume* vol)
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
        stack->AddPoint(ktauRpc);
    }
    
    return kTRUE;
}

void Hpt::EndOfEvent()
{
    fHptPointCollection->Clear();
}


void Hpt::Register()
{
    
    /** This will create a branch in the output tree called
     HptPoint, setting the last parameter to kFALSE means:
     this collection will not be written to the file, it will exist
     only during the simulation.
     */
    
    FairRootManager::Instance()->Register("HptPoint", "Hpt",
                                          fHptPointCollection, kTRUE);
}

// -----   Public method to Decode volume info  -------------------------------------------
// -----   returns hpt, arm, rpc numbers -----------------------------------
void Hpt::DecodeVolumeID(Int_t detID,int &nHPT)
{
  nHPT = detID;
}

TClonesArray* Hpt::GetCollection(Int_t iColl) const
{
    if (iColl == 0) { return fHptPointCollection; }
    else { return NULL; }
}

void Hpt::Reset()
{
    fHptPointCollection->Clear();
}


HptPoint* Hpt::AddHit(Int_t trackID, Int_t detID,
                        TVector3 pos, TVector3 mom,
                        Double_t time, Double_t length,
					    Double_t eLoss, Int_t pdgCode)

{
    TClonesArray& clref = *fHptPointCollection;
    Int_t size = clref.GetEntriesFast();

    return new(clref[size]) HptPoint(trackID, detID, pos, mom,time, length, eLoss, pdgCode);
}


ClassImp(Hpt)
