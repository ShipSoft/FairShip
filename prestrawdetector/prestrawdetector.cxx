#include "prestrawdetector.h"
#include "prestrawdetectorPoint.h"

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
#include "TMath.h"
#include "TParticle.h"
#include "TVector3.h"


prestrawdetector::prestrawdetector()
    : FairDetector("prestrawdetector", kTRUE)
    , fTrackID(-1)
    , fVolumeID(-1)
    , fPos()
    , fMom()
    , fTime(-1.)
    , fLength(-1.)
    , fELoss(-1)
    , fMedium("air")
    , fprestrawdetectorPointCollection(new TClonesArray("prestrawdetectorPoint"))
{}

prestrawdetector::prestrawdetector(const char* name, Bool_t active)
    : FairDetector(name, active)
    , fTrackID(-1)
    , fVolumeID(-1)
    , fPos()
    , fMom()
    , fTime(-1.)
    , fLength(-1.)
    , fELoss(-1)
    , fMedium("air")
    , fprestrawdetectorPointCollection(new TClonesArray("prestrawdetectorPoint"))
{}

prestrawdetector::~prestrawdetector() {
    if (fprestrawdetectorPointCollection) {
    fprestrawdetectorPointCollection->Delete();
    delete fprestrawdetectorPointCollection;
  }
}

void prestrawdetector::Initialize()
{
  FairDetector::Initialize();
//  FairRuntimeDb* rtdb= FairRun::Instance()->GetRuntimeDb();
//  vetoGeoPar* par=(vetoGeoPar*)(rtdb->getContainer("vetoGeoPar"));
}

// -----   Private method InitMedium
Int_t prestrawdetector::InitMedium(const char* name)
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

Bool_t prestrawdetector::ProcessHits(FairVolume* vol)
{

  std::cout << "In PH\n";
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
  //std::cout << gMC->IsTrackExiting()<<gMC->IsTrackStop()<<gMC->IsTrackDisappeared();
  // Create strawtubesPoint at exit of active volume
  if ( gMC->IsTrackEntering()   ) {
    //if (fELoss == 0. ) { return kFALSE; }
    std::cout << "Entering track was found\n";
    TParticle* p=gMC->GetStack()->GetCurrentTrack();
    Int_t pdgCode = p->GetPdgCode();
    fTrackID  = gMC->GetStack()->GetCurrentTrackNumber();
    Int_t det_uniqueId;
    gMC->CurrentVolID(det_uniqueId);
    /*if (fVolumeID == det_uniqueId) {
        //std::cout << pdgCode<< " same volume again ? "<< straw_uniqueId << " exit:" << gMC->IsTrackExiting() << " stop:" << gMC->IsTrackStop() << " disappeared:" << gMC->IsTrackDisappeared()<< std::endl;
         return kTRUE; }*/
    fVolumeID = det_uniqueId;
     // # d = |pq . u x v|/|u x v|
    TLorentzVector Pos;
    gMC->TrackPosition(Pos);
    Double_t xmean = (fPos.X()+Pos.X())/2. ;
    Double_t ymean = (fPos.Y()+Pos.Y())/2. ;
    Double_t zmean = (fPos.Z()+Pos.Z())/2. ;
    Double_t deltaTrackLength = gMC->TrackLength() - fLength;
    AddHit(fTrackID, det_uniqueId, TVector3(xmean, ymean,  zmean),
           TVector3(fMom.Px(), fMom.Py(), fMom.Pz()), fTime, deltaTrackLength,
           fELoss,pdgCode);
    // Increment number of strawtubes det points in TParticle
    /*ShipStack* stack = (ShipStack*) gMC->GetStack();
    stack->AddPoint(kStraw);*/
  }  
    return kTRUE;
}

prestrawdetectorPoint* prestrawdetector::AddHit(Int_t trackID, Int_t detID,
                                      TVector3 pos, TVector3 mom,
                                      Double_t time, Double_t length,
                                      Double_t eLoss, Int_t pdgCode)
{
  TClonesArray& clref = *fprestrawdetectorPointCollection;
  Int_t size = clref.GetEntriesFast();
  std::cout << "adding hit detid " << detID <<std::endl;
  return new(clref[size]) prestrawdetectorPoint(trackID, detID, pos, mom,
         time, length, eLoss, pdgCode);
}

void prestrawdetector::Register()
{

  /** This will create a branch in the output tree called
      strawtubesPoint, setting the last parameter to kFALSE means:
      this collection will not be written to the file, it will exist
      only during the simulation.
  */
  std::cout << "reg1";
  FairRootManager::Instance()->Register("prestrawdetectorPoint", "prestrawdetector",
                                        fprestrawdetectorPointCollection, kTRUE);
  std::cout << "reg2";

}

TClonesArray* prestrawdetector::GetCollection(Int_t iColl) const
{
  if (iColl == 0) { return fprestrawdetectorPointCollection; }
  else { return NULL; }
}

void prestrawdetector::Reset()
{
  fprestrawdetectorPointCollection->Clear();
}

void prestrawdetector::SetZ(Double_t z0)
{
    fPSDz = z0;                                                 //!  z-position of veto station
}

void prestrawdetector::ConstructGeometry()
{
    TGeoVolume *top               = gGeoManager->GetTopVolume();
    InitMedium("air");
    TGeoMedium *air               = gGeoManager->GetMedium("air");
    InitMedium("ShipSens");
    TGeoMedium *Se                = gGeoManager->GetMedium("ShipSens");
    InitMedium("aluminium");
    TGeoMedium *Al                = gGeoManager->GetMedium("aluminium");
    InitMedium("mylar");
    TGeoMedium *mylar             = gGeoManager->GetMedium("mylar");
    InitMedium("STTmix9010_2bar");
    TGeoMedium *sttmix9010_2bar   = gGeoManager->GetMedium("STTmix9010_2bar");
    InitMedium("tungsten");
    TGeoMedium *tungsten          = gGeoManager->GetMedium("tungsten");
    

    gGeoManager->SetVisLevel(4);
    gGeoManager->SetTopVisible();
    Double_t eps=0.0001;

    TGeoBBox* myBox = new TGeoBBox("myBox", 300, 300, 1);
    TGeoVolume* myVol = new TGeoVolume("myVol", myBox, air);
    myVol->SetLineColor(kYellow);
    top->AddNode(myVol, 0, new TGeoTranslation(0, 0, fPSDz));

    AddSensitiveVolume(myVol); 

    // Position it somewhere
    // top->AddNode(myVol, 1, new TGeoTranslation(0, 0, 500));
}

void prestrawdetector::EndOfEvent()
{
  fprestrawdetectorPointCollection->Clear();
}



