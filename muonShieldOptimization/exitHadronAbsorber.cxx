#include "exitHadronAbsorber.h"
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

Double_t cm  = 1;       // cm
Double_t m   = 100*cm;  //  m
Double_t mm  = 0.1*cm;  //  mm

exitHadronAbsorber::exitHadronAbsorber()
  : FairDetector("exitHadronAbsorber", kTRUE, kVETO),
    fTrackID(-1),
    fVolumeID(-1),
    fPos(),
    fMom(),
    fTime(-1.),
    fLength(-1.),
    fOnlyMuons(kFALSE),
    fzPos(3E8),
    fexitHadronAbsorberPointCollection(new TClonesArray("vetoPoint"))
{}

exitHadronAbsorber::~exitHadronAbsorber()
{
  if (fexitHadronAbsorberPointCollection) {
    fexitHadronAbsorberPointCollection->Delete();
    delete fexitHadronAbsorberPointCollection;
  }
}

Bool_t  exitHadronAbsorber::ProcessHits(FairVolume* vol)
{
  /** This method is called from the MC stepping */
  if ( gMC->IsTrackEntering() ) {
    fTrackID  = gMC->GetStack()->GetCurrentTrackNumber();
    TParticle* p  = gMC->GetStack()->GetCurrentTrack();
    Int_t pdgCode = p->GetPdgCode();
    gMC->TrackMomentum(fMom);
    if (!(fOnlyMuons && TMath::Abs(pdgCode)!=13)){ 
     fTime   = gMC->TrackTime() * 1.0e09;
     fLength = gMC->TrackLength();
     gMC->TrackPosition(fPos);
     if ( (fMom.E()-fMom.M() )>EMax) {
      AddHit(fTrackID, 111, TVector3(fPos.X(),fPos.Y(),fPos.Z()),
           TVector3(fMom.Px(), fMom.Py(), fMom.Pz()), fTime, fLength,
           0,pdgCode,TVector3(p->Vx(), p->Vy(), p->Vz()),TVector3(p->Px(), p->Py(), p->Pz()) );
      ShipStack* stack = (ShipStack*) gMC->GetStack();
      stack->AddPoint(kVETO);
      }
    }
  }
  gMC->StopTrack();
  return kTRUE;
}

void exitHadronAbsorber::Initialize()
{
  FairDetector::Initialize();
  TSeqCollection* fileList=gROOT->GetListOfFiles();
  fout = ((TFile*)fileList->At(0));
}

void exitHadronAbsorber::EndOfEvent()
{

  fexitHadronAbsorberPointCollection->Clear();

}

void exitHadronAbsorber::PreTrack(){
    gMC->TrackMomentum(fMom);
    TParticle* p  = gMC->GetStack()->GetCurrentTrack();
    Int_t pdgCode = p->GetPdgCode();
// record statistics for neutrinos, electrons and photons
    Int_t idabs = TMath::Abs(pdgCode);
    if (idabs<18 || idabs==22){
         Double_t wspill = p->GetWeight();
         Int_t idhnu=idabs+1000;
         if (pdgCode<0 || idabs==22){ idhnu+=1000;}
         Double_t l10ptot = TMath::Min(TMath::Max(TMath::Log10(fMom.P()),-0.3),1.69999);
         Double_t l10pt   = TMath::Min(TMath::Max(TMath::Log10(fMom.Pt()),-2.),0.4999);
         TString key; key+=idhnu;
         TH1D* h1 = (TH1D*)fout->Get(key);
         if (h1){h1->Fill(fMom.P(),wspill);}
         key="";key+=idhnu+100;
         TH2D* h2 = (TH2D*)fout->Get(key);
         if (h2){h2->Fill(l10ptot,l10pt,wspill);}
         key="";key+=idhnu+200;
         h2 = (TH2D*)fout->Get(key);
         if (h2){h2->Fill(l10ptot,l10pt,wspill);}
       }
    if  ( (fMom.E()-fMom.M() )<EMax){
        gMC->StopTrack();
    }
}

void exitHadronAbsorber::ConstructGeometry()
{
   static FairGeoLoader *geoLoad=FairGeoLoader::Instance();
   static FairGeoInterface *geoFace=geoLoad->getGeoInterface();
   static FairGeoMedia *media=geoFace->getMedia();
   static FairGeoBuilder *geoBuild=geoLoad->getGeoBuilder();

   FairGeoMedium *ShipMedium=media->getMedium("vacuums");
   TGeoMedium* vac=gGeoManager->GetMedium("vacuums");
   if (vac==NULL)
     geoBuild->createMedium(ShipMedium);
   vac =gGeoManager->GetMedium("vacuums");
   TGeoVolume *top=gGeoManager->GetTopVolume();
   Double_t zLoc;
   if (fzPos>1E8){
   //Add thin sensitive plane after hadron absorber
    TGeoVolume *muonShield = top->GetNode("MuonShieldArea_1")->GetVolume();
    Double_t z   = muonShield->GetNode("MagnAbsorb2_MagRetL_1")->GetMatrix()->GetTranslation()[2]; // this piece is bigger than AbsorberVol!
    TGeoBBox* tmp =  (TGeoBBox*)muonShield->GetNode("MagnAbsorb2_MagRetL_1")->GetVolume()->GetShape();
    Double_t dz  = tmp->GetDZ();
    zLoc = z+dz;
   }else{zLoc = fzPos;} // use external input
   TGeoVolume *sensPlane = gGeoManager->MakeBox("sensPlane",vac,10.*m-1.*mm,10.*m-1.*mm,1.*mm);
   top->AddNode(sensPlane, 1, new TGeoTranslation(0, 0, zLoc+1*cm));
   AddSensitiveVolume(sensPlane);
}

vetoPoint* exitHadronAbsorber::AddHit(Int_t trackID, Int_t detID,
                                      TVector3 pos, TVector3 mom,
                                      Double_t time, Double_t length,
                                      Double_t eLoss, Int_t pdgCode,TVector3 Lpos, TVector3 Lmom)
{
  TClonesArray& clref = *fexitHadronAbsorberPointCollection;
  Int_t size = clref.GetEntriesFast();
  return new(clref[size]) vetoPoint(trackID, detID, pos, mom,
         time, length, eLoss, pdgCode,Lpos,Lmom);
}

void exitHadronAbsorber::Register()
{

  FairRootManager::Instance()->Register("vetoPoint", "veto",
                                        fexitHadronAbsorberPointCollection, kTRUE);
}

TClonesArray* exitHadronAbsorber::GetCollection(Int_t iColl) const
{
  if (iColl == 0) { return fexitHadronAbsorberPointCollection; }
  else { return NULL; }
}
void exitHadronAbsorber::Reset()
{
  fexitHadronAbsorberPointCollection->Clear();
}

ClassImp(exitHadronAbsorber)
