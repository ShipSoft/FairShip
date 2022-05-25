#include "simpleTarget.h"
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
#include "TGeoEltu.h"
#include "TGeoBoolNode.h"
#include "TGeoMaterial.h"
#include "TParticle.h"
#include "TROOT.h"
#include "TH1D.h"
#include "TH2D.h"

#include <iostream>
using std::cout;
using std::endl;

simpleTarget::simpleTarget()
  : FairDetector("simpleTarget", kTRUE, kVETO),
    fTrackID(-1),
    fVolumeID(-1),
    fPos(),
    fMom(),
    fTime(-1.),
    fLength(-1.),
    fThick(-1.),
    fOnlyMuons(kFALSE),
    fFastMuon(kFALSE),
    fzPos(3E8),
    fTotalEloss(0),
    fsimpleTargetPointCollection(new TClonesArray("vetoPoint"))
{}

simpleTarget::~simpleTarget()
{
  if (fsimpleTargetPointCollection) {
    fsimpleTargetPointCollection->Delete();
    delete fsimpleTargetPointCollection;
  }
}

Bool_t  simpleTarget::ProcessHits(FairVolume* vol)
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

  // Create vetoPoint at exit of active volume
  if ( gMC->IsTrackExiting()    ||
       gMC->IsTrackStop()       ||
       gMC->IsTrackDisappeared()   ) {
    if (fELoss == 0. ) { return kFALSE; }
   // if (fOnlyMuons and fPos.Z()<140){ used for LiquidKrypton study
    if (fOnlyMuons){
       fTotalEloss+=fELoss;
       TClonesArray& clref = *fsimpleTargetPointCollection;
       new (clref[0]) vetoPoint(0, 0, TVector3(0, 0,  0), TVector3(0, 0,  0),
         0, 0, fTotalEloss, 0,TVector3(0, 0,  0), TVector3(0, 0,  0));
       return kTRUE;}
    
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
    //cout << veto_uniqueId << " :(" << xmean << ", " << ymean << ", " << zmean << "): " << fELoss << endl;
    AddHit(fTrackID, veto_uniqueId, TVector3(xmean, ymean,  zmean),
           TVector3(fMom.Px(), fMom.Py(), fMom.Pz()), fTime, fLength,
           fELoss,pdgCode,TVector3(Pos.X(), Pos.Y(), Pos.Z()),TVector3(Mom.Px(), Mom.Py(), Mom.Pz()) );

    // Increment number of veto det points in TParticle
    ShipStack* stack = (ShipStack*) gMC->GetStack();
    stack->AddPoint(kVETO);
  }

  return kTRUE;
}


void simpleTarget::Initialize()
{
  FairDetector::Initialize();
  TSeqCollection* fileList=gROOT->GetListOfFiles();
  fout = ((TFile*)fileList->At(0));
}

void simpleTarget::EndOfEvent()
{
  fsimpleTargetPointCollection->Clear();
  fTotalEloss=0;
}


void simpleTarget::ConstructGeometry()
{
   static FairGeoLoader *geoLoad=FairGeoLoader::Instance();
   static FairGeoInterface *geoFace=geoLoad->getGeoInterface();
   static FairGeoMedia *media=geoFace->getMedia();
   static FairGeoBuilder *geoBuild=geoLoad->getGeoBuilder();

   FairGeoMedium *ShipMedium=media->getMedium(fMaterial);
   TGeoMedium* mat=gGeoManager->GetMedium(fMaterial);
   if (mat==NULL)
     geoBuild->createMedium(ShipMedium);
   mat =gGeoManager->GetMedium(fMaterial);
   TGeoVolume *top=gGeoManager->GetTopVolume();
   TGeoVolume *target = gGeoManager->MakeBox("target",mat,10.*100.,10.*100.,fThick);
   top->AddNode(target, 1, new TGeoTranslation(0, 0, fzPos));
   AddSensitiveVolume(target);
}

vetoPoint* simpleTarget::AddHit(Int_t trackID, Int_t detID,
                                      TVector3 pos, TVector3 mom,
                                      Double_t time, Double_t length,
                                      Double_t eLoss, Int_t pdgCode,TVector3 Lpos, TVector3 Lmom)
{
  TClonesArray& clref = *fsimpleTargetPointCollection;
  Int_t size = clref.GetEntriesFast();
  return new(clref[size]) vetoPoint(trackID, detID, pos, mom,
         time, length, eLoss, pdgCode,Lpos,Lmom);
}

void simpleTarget::PreTrack(){
    if (!fFastMuon){return;}
    if (TMath::Abs(gMC->TrackPid())!=13){
        gMC->StopTrack();
    }
}

void simpleTarget::Register()
{

  FairRootManager::Instance()->Register("vetoPoint", "veto",
                                        fsimpleTargetPointCollection, kTRUE);
}

TClonesArray* simpleTarget::GetCollection(Int_t iColl) const
{
  if (iColl == 0) { return fsimpleTargetPointCollection; }
  else { return NULL; }
}
void simpleTarget::Reset()
{
  fsimpleTargetPointCollection->Clear();
}

