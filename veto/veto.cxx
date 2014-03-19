#include "veto.h"

#include "vetoPoint.h"


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

veto::veto()
  : FairDetector("veto", kTRUE, kVETO),
    fTrackID(-1),
    fVolumeID(-1),
    fPos(),
    fMom(),
    fTime(-1.),
    fLength(-1.),
    fELoss(-1),
    fvetoPointCollection(new TClonesArray("vetoPoint"))
{
}

veto::veto(const char* name, Bool_t active)
  : FairDetector(name, active, kVETO),
    fTrackID(-1),
    fVolumeID(-1),
    fPos(),
    fMom(),
    fTime(-1.),
    fLength(-1.),
    fELoss(-1),
    fvetoPointCollection(new TClonesArray("vetoPoint"))
{
}

veto::~veto()
{
  if (fvetoPointCollection) {
    fvetoPointCollection->Delete();
    delete fvetoPointCollection;
  }
}

void veto::Initialize()
{
  FairDetector::Initialize();
//  FairRuntimeDb* rtdb= FairRun::Instance()->GetRuntimeDb();
//  vetoGeoPar* par=(vetoGeoPar*)(rtdb->getContainer("vetoGeoPar"));
}

Bool_t  veto::ProcessHits(FairVolume* vol)
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
    fTrackID  = gMC->GetStack()->GetCurrentTrackNumber();
    fVolumeID = vol->getMCid();
    if (fELoss == 0. ) { return kFALSE; }
    AddHit(fTrackID, fVolumeID, TVector3(fPos.X(),  fPos.Y(),  fPos.Z()),
           TVector3(fMom.Px(), fMom.Py(), fMom.Pz()), fTime, fLength,
           fELoss);

    // Increment number of veto det points in TParticle
    ShipStack* stack = (ShipStack*) gMC->GetStack();
    stack->AddPoint(kVETO);
  }

  return kTRUE;
}

void veto::EndOfEvent()
{

  fvetoPointCollection->Clear();

}



void veto::Register()
{

  /** This will create a branch in the output tree called
      vetoPoint, setting the last parameter to kFALSE means:
      this collection will not be written to the file, it will exist
      only during the simulation.
  */

  FairRootManager::Instance()->Register("vetoPoint", "veto",
                                        fvetoPointCollection, kTRUE);

}


TClonesArray* veto::GetCollection(Int_t iColl) const
{
  if (iColl == 0) { return fvetoPointCollection; }
  else { return NULL; }
}

void veto::Reset()
{
  fvetoPointCollection->Clear();
}

void veto::ConstructGeometry()
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
    TGeoVolume *det1 = new TGeoVolume("det1", detcomp1, Al);
    det1->SetLineColor(kRed);
    top->AddNode(det1, 1, new TGeoTranslation(0, 0, -2390));
    TGeoRotation r0;
    r0.SetAngles(15,0,0);
    TGeoTranslation t0(0, 0, -2370);
    TGeoCombiTrans c0(t0, r0);
    TGeoHMatrix *h0 = new TGeoHMatrix(c0);
    top->AddNode(det1, 11, h0);

    // tracking station 1
    top->AddNode(det1, 2, new TGeoTranslation(0, 0, 1510));
    TGeoRotation r1;
    r1.SetAngles(15,0,0);
    TGeoTranslation t1(0, 0, 1530);
    TGeoCombiTrans c1(t1, r1);
    TGeoHMatrix *h1 = new TGeoHMatrix(c1);
    top->AddNode(det1, 3, h1);
    
    // tracking station 2
    top->AddNode(det1, 4, new TGeoTranslation(0, 0, 1710));
    TGeoRotation r2;
    r2.SetAngles(15,0,0);
    TGeoTranslation t2(0, 0, 1730);
    TGeoCombiTrans c2(t2, r2);
    TGeoHMatrix *h2 = new TGeoHMatrix(c2);
    top->AddNode(det1, 5, h2);
    
    // tracking station 3
    top->AddNode(det1, 6, new TGeoTranslation(0, 0, 2150));
    TGeoRotation r3;
    r3.SetAngles(15,0,0);
    TGeoTranslation t3(0, 0, 2170);
    TGeoCombiTrans c3(t3, r3);
    TGeoHMatrix *h3 = new TGeoHMatrix(c3);
    top->AddNode(det1, 7, h3);
    
    // tracking station 4
    top->AddNode(det1, 8, new TGeoTranslation(0, 0, 2370));
    TGeoRotation r4;
    r4.SetAngles(15,0,0);
    TGeoTranslation t4(0, 0, 2390);
    TGeoCombiTrans c4(t4, r4);
    TGeoHMatrix *h4 = new TGeoHMatrix(c4);
    top->AddNode(det1, 9, h4);
    
    
    
}

vetoPoint* veto::AddHit(Int_t trackID, Int_t detID,
                                      TVector3 pos, TVector3 mom,
                                      Double_t time, Double_t length,
                                      Double_t eLoss)
{
  TClonesArray& clref = *fvetoPointCollection;
  Int_t size = clref.GetEntriesFast();
  return new(clref[size]) vetoPoint(trackID, detID, pos, mom,
         time, length, eLoss);
}

ClassImp(veto)
