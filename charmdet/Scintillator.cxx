// Scintillator.cxx
// Scintillator, four tracking stations in a magnetic field.

#include "Scintillator.h"
#include "ScintillatorPoint.h"
#include "TGeoManager.h"
#include "FairRun.h"                    // for FairRun
#include "FairRuntimeDb.h"              // for FairRuntimeDb
#include <iosfwd>                    // for ostream
#include "TList.h"                      // for TListIter, TList (ptr only)
#include "TObjArray.h"                  // for TObjArray
#include "TString.h"                    // for TString
#include "TClonesArray.h"
#include "TVirtualMC.h"

#include "TGeoNavigator.h"
#include "TGeoNode.h"
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

#include <stddef.h>                     // for NULL
#include <iostream>                     // for operator<<, basic_ostream, etc

using std::cout;
using std::endl;
using namespace ShipUnit;

Scintillator::Scintillator()
  : FairDetector("HighPrecisionTrackers",kTRUE, kScintillator),
    fTrackID(-1),
    fPdgCode(),
    fVolumeID(-1),
    fPos(),
    fMom(),
    fTime(-1.),
    fLength(-1.),
    fELoss(-1),
    fScintillatorPointCollection(new TClonesArray("ScintillatorPoint"))
{
}

Scintillator::Scintillator(const char* name, Bool_t Active,const char* Title)
  : FairDetector(name, Active, kScintillator),
    fTrackID(-1),
    fPdgCode(),
    fVolumeID(-1),
    fPos(),
    fMom(),
    fTime(-1.),
    fLength(-1.),
    fELoss(-1),
    fScintillatorPointCollection(new TClonesArray("ScintillatorPoint"))
{ 

}

Scintillator::~Scintillator()
{
    if (fScintillatorPointCollection) {
        fScintillatorPointCollection->Delete();
        delete fScintillatorPointCollection;
    }
}

void Scintillator::Initialize()
{
    FairDetector::Initialize();
}


// -----   Private method InitMedium 
Int_t Scintillator::InitMedium(const char* name)
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


void Scintillator::SetScoring1XY(Float_t Scoring1X, Float_t Scoring1Y)
{
     fScoring1X = Scoring1X;    //! width of 1st scintillator
     fScoring1Y = Scoring1Y;    //! height of 1st scintillator
}

void Scintillator::SetDistT1(Float_t DistT1)
{
     fDistT1 = DistT1;    //! distance from scintillator to center of first tube
}

void Scintillator::SetDistT2(Float_t DistT2)
{
     fDistT2 = DistT2;    //! distance from scintillator 2 to center of last tube
}

void Scintillator::SetS_T1coords(Float_t S_T1_x, Float_t S_T1_y)
{
     fS_T1_x = S_T1_x;    //! x origin of S_T1
     fS_T1_y = S_T1_y;    //! y origin of S_T1
}

void Scintillator::SetS_T2coords(Float_t S_T2_x, Float_t S_T2_y)
{
     fS_T2_x = S_T2_x;    //! x origin of S_T2
     fS_T2_y = S_T2_y;    //! y origin of S_T2     
}



//
void Scintillator::ConstructGeometry()
{ 
    InitMedium("vacuum");
    TGeoMedium *vacuum = gGeoManager->GetMedium("vacuum");
  
    InitMedium("ShipSens");    
    TGeoMedium *Sens =gGeoManager->GetMedium("ShipSens");  
    
    TGeoVolume *top = gGeoManager->GetTopVolume();
    
    gGeoManager->SetVisLevel(7);
    gGeoManager->SetTopVisible();

    //epsilon to avoid overlapping volumes
    Double_t eps=0.0001;
    Double_t epsS=0.00001;

    TGeoBBox *scoring1box = new TGeoBBox("T1Box",fScoring1X/2.,fScoring1Y/2.,1.25);    
    TGeoBBox *scoring2box = new TGeoBBox("T2Box",fScoring1X/2.,fScoring1Y/2.,1.25);
    TGeoVolume *scintillator1 = new TGeoVolume("SA",scoring1box,Sens);
    scintillator1->SetLineColor(kRed);
    scintillator1->SetVisibility(kTRUE);
 
    TGeoVolume *scintillator2 = new TGeoVolume("SB",scoring2box,Sens);
    scintillator2->SetLineColor(kRed);
    scintillator2->SetVisibility(kTRUE);
    
	
    //Add a sensitive plane after the absorber 
    AddSensitiveVolume(scintillator1);
    AddSensitiveVolume(scintillator2);
    top->AddNode(scintillator1,6,new TGeoTranslation(0,0,fDistT1)); 
    top->AddNode(scintillator2,7,new TGeoTranslation(0,0,fDistT2));     	

}

Bool_t  Scintillator::ProcessHits(FairVolume* vol)
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
  
  // Create na61Point at exit of active volume
  if ( gMC->IsTrackExiting()    ||
       gMC->IsTrackStop()       ||
       gMC->IsTrackDisappeared()   ) {
    if (fELoss == 0. ) { return kFALSE; }
    TParticle* p=gMC->GetStack()->GetCurrentTrack();
    Int_t pdgCode = p->GetPdgCode();       
    fTrackID  = gMC->GetStack()->GetCurrentTrackNumber();
    fVolumeID = gGeoManager->FindVolumeFast(vol->GetName())->GetNumber();
    TLorentzVector Pos; 
    gMC->TrackPosition(Pos); 
    TLorentzVector Mom; 
    gMC->TrackMomentum(Mom);
    Double_t xmean = (fPos.X()+Pos.X())/2. ;      
    Double_t ymean = (fPos.Y()+Pos.Y())/2. ;      
    Double_t zmean = (fPos.Z()+Pos.Z())/2. ;     
    AddHit(fTrackID, fVolumeID, TVector3(xmean, ymean,  zmean),
           TVector3(fMom.Px(), fMom.Py(), fMom.Pz()), fTime, fLength,
           fELoss,pdgCode );

    // Increment number of na61 det points in TParticle
    ShipStack* stack = (ShipStack*) gMC->GetStack();
    stack->AddPoint(kScintillator);
  }

  return kTRUE;
}

void Scintillator::EndOfEvent()
{
    fScintillatorPointCollection->Clear();
}


void Scintillator::Register()
{
    
    /** This will create a branch in the output tree called
     ScintillatorPoint, setting the last parameter to kFALSE means:
     this collection will not be written to the file, it will exist
     only during the simulation.
     */
    
    FairRootManager::Instance()->Register("ScintillatorPoint", "Scintillator",
                                          fScintillatorPointCollection, kTRUE);
}

// -----   Public method to Decode volume info  -------------------------------------------
// -----   returns hpt, arm, rpc numbers -----------------------------------
void Scintillator::DecodeVolumeID(Int_t detID,int &nHPT)
{
  nHPT = detID;
}

TClonesArray* Scintillator::GetCollection(Int_t iColl) const
{
    if (iColl == 0) { return fScintillatorPointCollection; }
    else { return NULL; }
}

void Scintillator::Reset()
{
    fScintillatorPointCollection->Clear();
}


ScintillatorPoint* Scintillator::AddHit(Int_t trackID, Int_t detID,
                                      TVector3 pos, TVector3 mom,
                                      Double_t time, Double_t length,
                                      Double_t eLoss, Int_t pdgCode)
{
  TClonesArray& clref = *fScintillatorPointCollection;
  Int_t size = clref.GetEntriesFast();
  // cout << "scintillatorpoint addhit called "<< pos.z()<<endl;
  return new(clref[size]) ScintillatorPoint(trackID, detID, pos, mom,
         time, length, eLoss, pdgCode);
}

ClassImp(Scintillator)
