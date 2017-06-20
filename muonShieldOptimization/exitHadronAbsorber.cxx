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
    fTime   = gMC->TrackTime() * 1.0e09;
    fLength = gMC->TrackLength();
    gMC->TrackPosition(fPos);
    gMC->TrackMomentum(fMom);
    if ( (fMom.E()-fMom.M() )>EMax) {
     AddHit(fTrackID, 111, TVector3(fPos.X(),fPos.Y(),fPos.Z()),
           TVector3(fMom.Px(), fMom.Py(), fMom.Pz()), fTime, fLength,
           0,pdgCode,TVector3(p->Vx(), p->Vy(), p->Vz()),TVector3(p->Px(), p->Py(), p->Pz()) );
      }
  }
  ShipStack* stack = (ShipStack*) gMC->GetStack();
  stack->AddPoint(kVETO);
  gMC->StopTrack();
  return kTRUE;
}

void exitHadronAbsorber::Initialize()
{
  FairDetector::Initialize();
}

void exitHadronAbsorber::EndOfEvent()
{

  fexitHadronAbsorberPointCollection->Clear();

}

void exitHadronAbsorber::PreTrack(){
    gMC->TrackMomentum(fMom);
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
   if (vac=NULL)
     geoBuild->createMedium(ShipMedium);
   vac =gGeoManager->GetMedium("vacuums");
   //Add thin sensitive plane after hadron absorber
   TGeoVolume *top=gGeoManager->GetTopVolume();
   TGeoVolume *muonShield = top->GetNode("MuonShieldArea_1")->GetVolume();
   Double_t z   = muonShield->GetNode("MagnAbsorb2_MagCRB_1")->GetMatrix()->GetTranslation()[2]; // this piece is bigger than AbsorberVol!
   TGeoBBox* tmp =  (TGeoBBox*)muonShield->GetNode("MagnAbsorb2_MagCRB_1")->GetVolume()->GetShape();
   Double_t dz  = tmp->GetDZ();
   TGeoVolume *sensPlane = gGeoManager->MakeBox("sensPlane",vac,10.*m-1.*mm,10.*m-1.*mm,1.*mm);
   top->AddNode(sensPlane, 1, new TGeoTranslation(0, 0, z+dz+1*cm));
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
