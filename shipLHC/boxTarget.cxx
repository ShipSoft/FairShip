#include "boxTarget.h"
#include <math.h>
#include "vetoPoint.h"

#include "FairLogger.h"                 // for FairLogger, MESSAGE_ORIGIN
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
#include "ShipStack.h"

#include "TClonesArray.h"
#include "TVirtualMC.h"
#include "TGeoManager.h"
#include "TGeoBBox.h"
#include "TGeoBBox.h"
#include "TGeoCompositeShape.h"
#include "TGeoBoolNode.h"
#include "TGeoMaterial.h"
#include "TParticle.h"
#include "TROOT.h"
#include "TH1D.h"
#include "TH2D.h"
#include "TDatabasePDG.h"

#include <iostream>
using std::cout;
using std::endl;

boxTarget::boxTarget()
  : FairDetector("boxTarget", kTRUE, kVETO),
    fTrackID(-1),
    fVolumeID(-1),
    fPos(),
    fMom(),
    fTime(-1.),
    fLength(-1.),
    fTargetMaterial("tungsten"),
    fTargetL(1.),
    fboxTargetPointCollection(new TClonesArray("vetoPoint"))
{}

boxTarget::~boxTarget()
{
  if (fboxTargetPointCollection) {
    fboxTargetPointCollection->Delete();
    delete fboxTargetPointCollection;
  }
}

Bool_t  boxTarget::ProcessHits(FairVolume* vol)
{
  /** This method is called from the MC stepping */
  if ( gMC->IsTrackEntering() ) {
    fTime   = gMC->TrackTime() * 1.0e09;
    fLength = gMC->TrackLength();
    gMC->TrackPosition(fPos);
    gMC->TrackMomentum(fMom);
    LOG(DEBUG) <<"track enters"<<gMC->GetStack()->GetCurrentTrack()->GetPdgCode();
  }
  if (!gMC->IsTrackEntering() ) { 
        LOG(DEBUG) <<"track is not entering"<<gMC->GetStack()->GetCurrentTrack()->GetPdgCode();
  }
  if ( gMC->IsTrackExiting()    ||
       gMC->IsTrackStop()       ||
       gMC->IsTrackDisappeared()   ) {
       LOG(DEBUG) <<"track stopped"<<gMC->GetStack()->GetCurrentTrack()->GetPdgCode();

    fTrackID  = gMC->GetStack()->GetCurrentTrackNumber();
    Int_t veto_uniqueId;
    gMC->CurrentVolID(veto_uniqueId);

    TParticle* p=gMC->GetStack()->GetCurrentTrack();
    Int_t pdgCode = p->GetPdgCode();
    TLorentzVector Pos;
    gMC->TrackPosition(Pos);
    TLorentzVector Mom;
    gMC->TrackMomentum(Mom);
    Double_t xmean = (fPos.X()+Pos.X())/2. ;
    Double_t ymean = (fPos.Y()+Pos.Y())/2. ;
    Double_t zmean = (fPos.Z()+Pos.Z())/2. ;
    AddHit(fTrackID, veto_uniqueId, TVector3(xmean, ymean,  zmean),
           TVector3(fMom.Px(), fMom.Py(), fMom.Pz()), fTime, fLength,
           0.,pdgCode,TVector3(Pos.X(), Pos.Y(), Pos.Z()),TVector3(Mom.Px(), Mom.Py(), Mom.Pz()) );
    // Increment number of veto det points in TParticle
    ShipStack* stack = (ShipStack*) gMC->GetStack();
    stack->AddPoint(kVETO);
  }
  return kTRUE;
}
// -----   Private method InitMedium 
Int_t boxTarget::InitMedium(TString name) 
{
   static FairGeoLoader *geoLoad=FairGeoLoader::Instance();
   static FairGeoInterface *geoFace=geoLoad->getGeoInterface();
   static FairGeoMedia *media=geoFace->getMedia();
   static FairGeoBuilder *geoBuild=geoLoad->getGeoBuilder();

   FairGeoMedium *ShipMedium=media->getMedium(name);

   if (!ShipMedium)
     Fatal("InitMedium","Material %s not defined in media file.", name.Data());
   TGeoMedium* medium=gGeoManager->GetMedium(name);
   if (medium)
     return ShipMedium->getMediumIndex();
   return geoBuild->createMedium(ShipMedium);
}


void boxTarget::Initialize()
{
  FairDetector::Initialize();
}

void boxTarget::EndOfEvent()
{

  fboxTargetPointCollection->Clear();

}

void boxTarget::FinishRun(){
}

void boxTarget::ConstructGeometry()
{
   Double_t cm  = 1;       // cm
   Double_t m   = 100*cm;  //  m
   Double_t mm  = 0.1*cm;  //  mm

   TGeoVolume *top = gGeoManager->GetTopVolume();
   InitMedium(fTargetMaterial);
   TGeoMedium *TargetMaterial = gGeoManager->GetMedium(fTargetMaterial);
   InitMedium("vacuums");
   TGeoMedium *vac  = gGeoManager->GetMedium("vacuums");

   TGeoVolume* target  = gGeoManager->MakeBox("Target",TargetMaterial,199.*cm,199.*cm,(fTargetL/2)*cm);
   top->AddNode(target, 1, new TGeoTranslation(0, 0, (fTargetL/2)*cm));

   TGeoVolume *sensPlane = gGeoManager->MakeBox("sensPlane",vac,199.*cm,199.*cm,1.*mm);
   sensPlane->SetLineColor(kGreen);
   top->AddNode(sensPlane, 13, new TGeoTranslation(0, 0, (fTargetL+ 0.11)*cm));
   AddSensitiveVolume(sensPlane);
   AddSensitiveVolume(target);
}

vetoPoint* boxTarget::AddHit(Int_t trackID, Int_t detID,
                                      TVector3 pos, TVector3 mom,
                                      Double_t time, Double_t length,
                                      Double_t eLoss, Int_t pdgCode,TVector3 Lpos, TVector3 Lmom)
{
  TClonesArray& clref = *fboxTargetPointCollection;
  Int_t size = clref.GetEntriesFast();
  return new(clref[size]) vetoPoint(trackID, detID, pos, mom,
         time, length, eLoss, pdgCode,Lpos,Lmom);
}

void boxTarget::Register()
{

  FairRootManager::Instance()->Register("vetoPoint", "veto",
                                        fboxTargetPointCollection, kTRUE);
}

TClonesArray* boxTarget::GetCollection(Int_t iColl) const
{
  if (iColl == 0) { return fboxTargetPointCollection; }
  else { return NULL; }
}
void boxTarget::Reset()
{
  fboxTargetPointCollection->Clear();
}

ClassImp(boxTarget)
