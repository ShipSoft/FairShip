#include "muon.h"

#include "muonPoint.h"


#include "FairVolume.h"
#include "FairGeoVolume.h"
#include "FairGeoNode.h"
#include "FairRootManager.h"
#include "FairGeoLoader.h"
#include "FairGeoInterface.h"
#include "FairRun.h"
#include "FairRuntimeDb.h"
#include "ShipDetectorList.h"
#include "ShipStack.h"

#include "TClonesArray.h"
#include "TVirtualMC.h"
#include "TGeoManager.h"
#include "TGeoBBox.h"
#include "TGeoCompositeShape.h"
#include "TGeoTube.h"
#include "TGeoMaterial.h"
#include "TGeoMedium.h"



#include <iostream>
using std::cout;
using std::endl;

muon::muon()
  : FairDetector("muon", kTRUE, kMuon),
    fTrackID(-1),
    fVolumeID(-1),
    fPos(),
    fMom(),
    fTime(-1.),
    fLength(-1.),
    fELoss(-1),
    fmuonPointCollection(new TClonesArray("muonPoint"))
{
}

muon::muon(const char* name, Bool_t active)
  : FairDetector(name, active, kMuon),
    fTrackID(-1),
    fVolumeID(-1),
    fPos(),
    fMom(),
    fTime(-1.),
    fLength(-1.),
    fELoss(-1),
    fmuonPointCollection(new TClonesArray("muonPoint"))
{
}

muon::~muon()
{
  if (fmuonPointCollection) {
    fmuonPointCollection->Delete();
    delete fmuonPointCollection;
  }
}

void muon::Initialize()
{
  FairDetector::Initialize();
//  FairRuntimeDb* rtdb= FairRun::Instance()->GetRuntimeDb();
//  muonGeoPar* par=(muonGeoPar*)(rtdb->getContainer("muonGeoPar"));
}

Bool_t  muon::ProcessHits(FairVolume* vol)
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
    AddHit(fTrackID, fVolumeID, TVector3(fPos.X(),  fPos.Y(),  fPos.Z()),
           TVector3(fMom.Px(), fMom.Py(), fMom.Pz()), fTime, fLength,
           fELoss);

    // Increment number of muon det points in TParticle
    ShipStack* stack = (ShipStack*) gMC->GetStack();
    stack->AddPoint(kVETO);
  }

  return kTRUE;
}

void muon::EndOfEvent()
{

  fmuonPointCollection->Clear();

}



void muon::Register()
{

  /** This will create a branch in the output tree called
      muonPoint, setting the last parameter to kFALSE means:
      this collection will not be written to the file, it will exist
      only during the simulation.
  */

  FairRootManager::Instance()->Register("muonPoint", "muon",
                                        fmuonPointCollection, kTRUE);

}


TClonesArray* muon::GetCollection(Int_t iColl) const
{
  if (iColl == 0) { return fmuonPointCollection; }
  else { return NULL; }
}

void muon::Reset()
{
  fmuonPointCollection->Clear();
}

void muon::ConstructGeometry()
{
  /** If you are using the standard ASCII input for the geometry
      just copy this and use it for your detector, otherwise you can
      implement here you own way of constructing the geometry. */
    
    TGeoVolume *top=gGeoManager->GetTopVolume();
    TGeoMedium *Al =gGeoManager->GetMedium("Al");
    
    
    if(Al==0){
        TGeoMaterial *matAl     = new TGeoMaterial("Al", 26.98, 13, 2.7);
        Al     = new TGeoMedium("Al", 2, matAl);
    }
    
    TGeoBBox *detbox1 = new TGeoBBox("detbox1", 250, 250, 10);
    TGeoBBox *detbox2 = new TGeoBBox("detbox2", 245, 245, 10);
    
    TGeoCompositeShape *detcomp1 = new TGeoCompositeShape("detcomp1", "detbox1-detbox2");    

    TGeoVolume *detmu1 = new TGeoVolume("MuX", detcomp1, Al);
    TGeoVolume *muonfilter = gGeoManager->MakeBox("muonfilter", Al, 250, 250, 20);
    AddSensitiveVolume(muonfilter);
    muonfilter->SetLineColor(kGreen);
    top->AddNode(muonfilter, 1, new TGeoTranslation(0, 0, 2500));
    
    top->AddNode(detmu1, 10, new TGeoTranslation(0, 0, 2570));
    detmu1->SetLineColor(kViolet+10);    
    TGeoRotation r5;
    r5.SetAngles(15,0,0);
    TGeoTranslation t5(0, 0, 2590);
    TGeoCombiTrans c5(t5, r5);
    TGeoHMatrix *h5 = new TGeoHMatrix(c5);
    TGeoVolume *detmu2 = new TGeoVolume("MuS", detcomp1, Al);
    detmu2->SetLineColor(kViolet+4);
    top->AddNode(detmu2, 10, h5);
    
    
}

muonPoint* muon::AddHit(Int_t trackID, Int_t detID,
                                      TVector3 pos, TVector3 mom,
                                      Double_t time, Double_t length,
                                      Double_t eLoss)
{
  TClonesArray& clref = *fmuonPointCollection;
  Int_t size = clref.GetEntriesFast();
  // cout << "muon hit called"<< pos.z()<<endl;
  return new(clref[size]) muonPoint(trackID, detID, pos, mom,
         time, length, eLoss);
}

ClassImp(muon)
