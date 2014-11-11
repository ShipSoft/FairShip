#include "muon.h"

#include "muonPoint.h"


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
// -----   Private method InitMedium 
Int_t muon::InitMedium(const char* name) 
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
    //fVolumeID = vol->getMCid();
    //cout << "muon proc "<< fVolumeID<<" "<<vol->GetName()<<" "<<vol->getVolumeId() <<endl;
    //cout << " "<< gGeoManager->FindVolumeFast(vol->GetName())->GetNumber()<<endl;
    fVolumeID = gGeoManager->FindVolumeFast(vol->GetName())->GetNumber();
    if (fELoss == 0. ) { return kFALSE; }
    AddHit(fTrackID, fVolumeID, TVector3(fPos.X(),  fPos.Y(),  fPos.Z()),
           TVector3(fMom.Px(), fMom.Py(), fMom.Pz()), fTime, fLength,
           fELoss);

    // Increment number of muon det points in TParticle
    ShipStack* stack = (ShipStack*) gMC->GetStack();
    stack->AddPoint(kMuon);
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

void muon::SetZStationPositions(Double32_t z0, Double32_t z1,Double32_t z2,Double32_t z3)
{
  fM0z=z0;
 fM1z=z1;
 fM2z=z2;
 fM3z=z3;
}
void muon::SetZFilterPositions(Double32_t z0, Double32_t z1,Double32_t z2)
{
  fF0z=z0;
 fF1z=z1;
 fF2z=z2;
}
void muon::SetActiveThickness(Double32_t activeThickness)
{
  fActiveThickness=activeThickness;
}
void muon::SetFilterThickness(Double32_t filterThickness)
{
  fFilterThickness=filterThickness;
}
void muon::SetXMax(Double32_t xMax)
{
  fXMax=xMax;
}
void muon::SetYMax(Double32_t yMax)
{
  fYMax=yMax;
}
void muon::ConstructGeometry()
{
  /** If you are using the standard ASCII input for the geometry
      just copy this and use it for your detector, otherwise you can
      implement here you own way of constructing the geometry. */
    
    TGeoVolume *top=gGeoManager->GetTopVolume();
    InitMedium("iron");
    InitMedium("Scintillator");
    
    TGeoMedium *Al =gGeoManager->GetMedium("Scintillator");
    TGeoMedium *A2 =gGeoManager->GetMedium("iron");
    
//    TGeoBBox *detbox1 = new TGeoBBox("detbox1", 250, 250, 10);
//    TGeoBBox *detbox2 = new TGeoBBox("detbox2", 245, 245, 10);
    
//    TGeoCompositeShape *detcomp1 = new TGeoCompositeShape("detcomp1", "detbox1-detbox2");    

//    TGeoVolume *detmu1 = new TGeoVolume("MuX", detcomp1, Al);
    TGeoVolume *muondet0 = gGeoManager->MakeBox("muondet0", Al, fXMax, fYMax, fActiveThickness);
    TGeoVolume *muondet1 = gGeoManager->MakeBox("muondet1", Al, fXMax, fYMax, fActiveThickness);
    TGeoVolume *muondet2 = gGeoManager->MakeBox("muondet2", Al, fXMax, fYMax, fActiveThickness); 
    TGeoVolume *muondet3 = gGeoManager->MakeBox("muondet3", Al, fXMax, fYMax, fActiveThickness); 
    
    TGeoVolume *muonfilter0 = gGeoManager->MakeBox("muonfilter0", A2, fXMax, fYMax, fFilterThickness);
    TGeoVolume *muonfilter1 = gGeoManager->MakeBox("muonfilter1", A2, fXMax, fYMax, fFilterThickness);
    TGeoVolume *muonfilter2 = gGeoManager->MakeBox("muonfilter2", A2, fXMax, fYMax, fFilterThickness);

    AddSensitiveVolume(muondet0);
    AddSensitiveVolume(muondet1);
    AddSensitiveVolume(muondet2);
    AddSensitiveVolume(muondet3);
    muondet0->SetLineColor(kGreen);
    muondet1->SetLineColor(kGreen);
    muondet2->SetLineColor(kGreen);
    muondet3->SetLineColor(kGreen);
    muonfilter0->SetLineColor(kBlue);
    muonfilter1->SetLineColor(kBlue);
    muonfilter2->SetLineColor(kBlue);

    top->AddNode(muondet0, 1, new TGeoTranslation(0, 0, fM0z));
    top->AddNode(muonfilter0, 1, new TGeoTranslation(0, 0, fF0z));
    top->AddNode(muondet1, 1, new TGeoTranslation(0, 0, fM1z));
    top->AddNode(muonfilter1, 1, new TGeoTranslation(0, 0, fF1z));
    top->AddNode(muondet2, 1, new TGeoTranslation(0, 0, fM2z));
    top->AddNode(muonfilter2, 1, new TGeoTranslation(0, 0, fF2z));
    top->AddNode(muondet3, 1, new TGeoTranslation(0, 0, fM3z));
    

//    top->AddNode(detmu1, 10, new TGeoTranslation(0, 0, 2570));
//    detmu1->SetLineColor(kViolet+10);    
//    TGeoRotation r5;
//    r5.SetAngles(15,0,0);
//    TGeoTranslation t5(0, 0, 2590);
//    TGeoCombiTrans c5(t5, r5);
//    TGeoHMatrix *h5 = new TGeoHMatrix(c5);
//    TGeoVolume *detmu2 = new TGeoVolume("MuS", detcomp1, Al);
//    detmu2->SetLineColor(kViolet+4);
//    top->AddNode(detmu2, 10, h5);
    
    
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
