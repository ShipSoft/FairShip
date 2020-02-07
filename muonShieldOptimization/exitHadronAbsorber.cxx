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
#include "TDatabasePDG.h"

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
    fSkipNeutrinos(kFALSE),
    fzPos(3E8),
    withNtuple(kFALSE),
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
  // book hists for Genie neutrino momentum distribution
  // add also leptons, and photon
  // add pi0 111 eta 221 eta' 331  omega 223 for DM production
  TDatabasePDG* PDG = TDatabasePDG::Instance();
  for(Int_t idnu=11; idnu<26; idnu+=1){
  // nu or anti-nu
   for (Int_t idadd=-1; idadd<3; idadd+=2){
    Int_t idw=idnu;
    if (idnu==18){idw=22;}
    if (idnu==19){idw=111;}
    if (idnu==20){idw=221;}
    if (idnu==21){idw=223;}
    if (idnu==22){idw=331;}
    if (idnu==23){idw=211;}
    if (idnu==24){idw=321;}
    if (idnu==25){idw=2212;}
    Int_t idhnu=10000+idw;
    if (idadd==-1){
     if (idnu>17){continue;}
     idhnu+=10000;
     idw=-idnu;
    }
    TString name=PDG->GetParticle(idw)->GetName();
    TString title = name;title+=" momentum (GeV)";
    TString key = "";key+=idhnu;
    TH1D* Hidhnu = new TH1D(key,title,400,0.,400.);
    title = name;title+="  log10-p vs log10-pt";
    key = "";key+=idhnu+1000;
    TH2D* Hidhnu100 = new TH2D(key,title,100,-0.3,1.7,100,-2.,0.5);
    title = name;title+="  log10-p vs log10-pt";
    key = "";key+=idhnu+2000;
    TH2D* Hidhnu200 = new TH2D(key,title,25,-0.3,1.7,100,-2.,0.5);
     }
   }
  if(withNtuple) {
         fNtuple = new TNtuple("4DP","4DP","id:px:py:pz:x:y:z");
  }
}

void exitHadronAbsorber::EndOfEvent()
{

  fexitHadronAbsorberPointCollection->Clear();

}

void exitHadronAbsorber::PreTrack(){
    gMC->TrackMomentum(fMom);
    if  ( (fMom.E()-fMom.M() )<EMax){
      gMC->StopTrack();
      return;
    }
    TParticle* p  = gMC->GetStack()->GetCurrentTrack();
    Int_t pdgCode = p->GetPdgCode();
// record statistics for neutrinos, electrons and photons
// add pi0 111 eta 221 eta' 331  omega 223 
    Int_t idabs = TMath::Abs(pdgCode);
    if (idabs<18 || idabs==22 || idabs==111 || idabs==221 || idabs==223 || idabs==331 
                 || idabs==211  || idabs==321   || idabs==2212 ){
         Double_t wspill = p->GetWeight();
         Int_t idhnu=idabs+10000;
         if (pdgCode<0){ idhnu+=10000;}
         Double_t l10ptot = TMath::Min(TMath::Max(TMath::Log10(fMom.P()),-0.3),1.69999);
         Double_t l10pt   = TMath::Min(TMath::Max(TMath::Log10(fMom.Pt()),-2.),0.4999);
         TString key; key+=idhnu;
         TH1D* h1 = (TH1D*)fout->Get(key);
         if (h1){h1->Fill(fMom.P(),wspill);}
         key="";key+=idhnu+1000;
         TH2D* h2 = (TH2D*)fout->Get(key);
         if (h2){h2->Fill(l10ptot,l10pt,wspill);}
         key="";key+=idhnu+2000;
         h2 = (TH2D*)fout->Get(key);
         if (h2){h2->Fill(l10ptot,l10pt,wspill);}
         if(withNtuple){
          fNtuple->Fill(pdgCode,fMom.Px(),fMom.Py(), fMom.Pz(),fPos.X(),fPos.Y(),fPos.Z());
         }
    if (fSkipNeutrinos && (idabs==12 or idabs==14 or idabs == 16 )){gMC->StopTrack();}
   }
}

void exitHadronAbsorber::FinishRun(){
  for(Int_t idnu=11; idnu<23; idnu+=1){
  // nu or anti-nu
   for (Int_t idadd=-1; idadd<3; idadd+=2){
    Int_t idw=idnu;
    if (idnu==18){idw=22;}
    if (idnu==19){idw=111;}
    if (idnu==20){idw=221;}
    if (idnu==21){idw=223;}
    if (idnu==22){idw=331;}
    Int_t idhnu=10000+idw;
    if (idadd==-1){
     if (idnu>17){continue;}
     idhnu+=10000;
     idw=-idnu;
    }
    TString key = "";key+=idhnu;
    TSeqCollection* fileList=gROOT->GetListOfFiles();
    ((TFile*)fileList->At(0))->cd();
    TH1D* Hidhnu = (TH1D*)fout->Get(key);
    Hidhnu->Write();
    key="";key+=idhnu+1000;
    TH2D* Hidhnu100 = (TH2D*)fout->Get(key);
    Hidhnu100->Write();
    key = "";key+=idhnu+2000;
    TH2D* Hidhnu200 = (TH2D*)fout->Get(key);
    Hidhnu200->Write();
   }
  }
  if(withNtuple){fNtuple->Write();}
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
   TGeoNavigator* nav = gGeoManager->GetCurrentNavigator();
   Double_t zLoc;
   if (fzPos>1E8){
   //Add thin sensitive plane after hadron absorber
    Float_t distance = 1.;
    Double_t local[3]= {0,0,0};
    if (not nav->cd("/MuonShieldArea_1/CoatWall_1")) {
      nav->cd("/MuonShieldArea_1/MagnAbsorb2_MagRetL_1");
      distance = -1.;}
    TGeoBBox* tmp =  (TGeoBBox*)(nav->GetCurrentNode()->GetVolume()->GetShape());
    local[2] = distance * tmp->GetDZ();
    Double_t global[3] = {0,0,0};
    nav->LocalToMaster(local,global);
    zLoc = global[2] + distance * 1.*cm;
   }else{zLoc = fzPos;} // use external input
   TGeoVolume *sensPlane = gGeoManager->MakeBox("sensPlane",vac,10.*m-1.*mm,10.*m-1.*mm,1.*mm);
   nav->cd("/MuonShieldArea_1/");
   nav->GetCurrentNode()->GetVolume()->AddNode(sensPlane, 1, new TGeoTranslation(0, 0, zLoc));
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
