#include "ecal.h"

#include "ecalPoint.h"

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

#include "TGeoManager.h"
#include "TGeoMaterial.h"
#include "TGeoMedium.h"

#include "TClonesArray.h"
#include "TVirtualMC.h"

#include <iostream>
using std::cout;
using std::endl;

ecal::ecal()
  : FairDetector("ecal", kTRUE, kecal),
    fTrackID(-1),
    fVolumeID(-1),
    fPos(),
    fMom(),
    fTime(-1.),
    fLength(-1.),
    fELoss(-1),
    fecalPointCollection(new TClonesArray("ecalPoint"))
{
}

ecal::ecal(const char* name, Bool_t active)
  : FairDetector(name, active, kecal),
    fTrackID(-1),
    fVolumeID(-1),
    fPos(),
    fMom(),
    fTime(-1.),
    fLength(-1.),
    fELoss(-1),
    fecalPointCollection(new TClonesArray("ecalPoint"))
{
}

ecal::~ecal()
{
  if (fecalPointCollection) {
    fecalPointCollection->Delete();
    delete fecalPointCollection;
  }
}

void ecal::Initialize()
{
  FairDetector::Initialize();
//  FairRuntimeDb* rtdb= FairRun::Instance()->GetRuntimeDb();
}

Bool_t  ecal::ProcessHits(FairVolume* vol)
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

  // Create ecalPoint at exit of active volume
  if ( gMC->IsTrackExiting()    ||
       gMC->IsTrackStop()       ||
       gMC->IsTrackDisappeared()   ) {
    fTrackID  = gMC->GetStack()->GetCurrentTrackNumber();
    fVolumeID = vol->getMCid();
    if (fELoss == 0. ) { return kFALSE; }
    AddHit(fTrackID, fVolumeID, TVector3(fPos.X(),  fPos.Y(),  fPos.Z()),
           TVector3(fMom.Px(), fMom.Py(), fMom.Pz()), fTime, fLength,
           fELoss);

    // Increment number of ecal det points in TParticle
    ShipStack* stack = dynamic_cast <ShipStack*> (gMC->GetStack());
    stack->AddPoint(kecal);
  }

  return kTRUE;
}

void ecal::EndOfEvent()
{

  fecalPointCollection->Clear();

}



void ecal::Register()
{

  /** This will create a branch in the output tree called
      ecalPoint, setting the last parameter to kFALSE means:
      this collection will not be written to the file, it will exist
      only during the simulation.
  */

  FairRootManager::Instance()->Register("ecalPoint", "ecal",
                                        fecalPointCollection, kTRUE);

}


TClonesArray* ecal::GetCollection(Int_t iColl) const
{
  if (iColl == 0) { return fecalPointCollection; }
  else { return NULL; }
}

void ecal::Reset()
{
  fecalPointCollection->Clear();
}

void ecal::ConstructGeometry()
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
    
    // ecal
    TGeoVolume *ecal = gGeoManager->MakeBox("ecal", Al, 250, 250, 40);
    AddSensitiveVolume(ecal);

    ecal->SetLineColor(6); // purple
    top->AddNode(ecal, 1, new TGeoTranslation(0, 0, 2440));
    
    

}

ecalPoint* ecal::AddHit(Int_t trackID, Int_t detID,
                                      TVector3 pos, TVector3 mom,
                                      Double_t time, Double_t length,
                                      Double_t eLoss)
{
  TClonesArray& clref = *fecalPointCollection;
  Int_t size = clref.GetEntriesFast();
  return new(clref[size]) ecalPoint(trackID, detID, pos, mom,
         time, length, eLoss);
}

ClassImp(ecal)
