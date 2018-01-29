// Timing Detector
// 26/01/2017
// Alexander.Korzenev@cern.ch

#include "TimeDet.h"
#include "TimeDetPoint.h"

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

#include <iostream>
#include <sstream>
using std::cout;
using std::endl;


TimeDet::TimeDet()
  : FairDetector("TimeDet", kTRUE, kTimeDet),
    fTrackID(-1),
    fVolumeID(-1),
    fPos(),
    fMom(),
    fTime(-1.),
    fLength(-1.),
    fELoss(-1),
    //
    fzPos(0),
    fxSize(500),
    fySize(1000),
    fxBar(168),
    fyBar(6),
    fzBar(1),
    fdzBarCol(2.4),
    fdzBarRow(1.2),
    fNCol(3),
    fNRow(182),
    fxCenter(0),
    fyCenter(0),
    //
    fDetector(0),
    //
    fTimeDetPointCollection(new TClonesArray("TimeDetPoint"))
{
  FairDetector::Initialize();
}



TimeDet::TimeDet(const char* name, Bool_t active)
  : FairDetector(name, active, kTimeDet),
    fTrackID(-1),
    fVolumeID(-1),
    fPos(),
    fMom(),
    fTime(-1.),
    fLength(-1.),
    fELoss(-1),
    //
    fzPos(0),
    fxSize(500),
    fySize(1000),
    fxBar(168),
    fyBar(6),
    fzBar(1),
    fdzBarCol(2.4),
    fdzBarRow(1.2),
    fNCol(3),
    fNRow(182),
    fxCenter(0),
    fyCenter(0),
    //
    fDetector(0),
    //
    fTimeDetPointCollection(new TClonesArray("TimeDetPoint"))
{
  FairDetector::Initialize();
}



TimeDet::~TimeDet()
{
  if (fTimeDetPointCollection) {
    fTimeDetPointCollection->Delete();
    delete fTimeDetPointCollection;
  }
}


/*
void TimeDet::Initialize()
{
  FairDetector::Initialize();
  //  FairRuntimeDb* rtdb= FairRun::Instance()->GetRuntimeDb();
  //  vetoGeoPar* par=(vetoGeoPar*)(rtdb->getContainer("vetoGeoPar"));
}
*/


// -----   Private method InitMedium
Int_t TimeDet::InitMedium(const char* name)
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
  
  return 0;
}



Bool_t  TimeDet::ProcessHits(FairVolume* vol)
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

    fTrackID  = gMC->GetStack()->GetCurrentTrackNumber();

    Int_t uniqueId;
    gMC->CurrentVolID(uniqueId);
    if (uniqueId>1000000) //Solid scintillator case
    {
      Int_t vcpy;
      gMC->CurrentVolOffID(1, vcpy);
      if (vcpy==5) uniqueId+=4; //Copy of half
    }

    TParticle* p = gMC->GetStack()->GetCurrentTrack();
    Int_t pdgCode = p->GetPdgCode();
    TLorentzVector Pos;
    gMC->TrackPosition(Pos);
    TLorentzVector Mom;
    gMC->TrackMomentum(Mom);
    Double_t xmean = (fPos.X()+Pos.X())/2. ;
    Double_t ymean = (fPos.Y()+Pos.Y())/2. ;
    Double_t zmean = (fPos.Z()+Pos.Z())/2. ;

    cout << uniqueId << " :(" << xmean << ", " << ymean << ", " << zmean << "): " << gMC->CurrentVolName() << endl;

    AddHit(fTrackID, uniqueId, TVector3(xmean, ymean,  zmean),
           TVector3(fMom.Px(), fMom.Py(), fMom.Pz()), fTime, fLength,
           fELoss,pdgCode,TVector3(Pos.X(), Pos.Y(), Pos.Z()),
	   TVector3(Mom.Px(), Mom.Py(), Mom.Pz()) );

    // Increment number of veto det points in TParticle
    ShipStack* stack = (ShipStack*) gMC->GetStack();
    stack->AddPoint(kTimeDet);
  }
  
  return kTRUE;
}



void TimeDet::EndOfEvent()
{
  fTimeDetPointCollection->Clear();
}



void TimeDet::Register()
{

  /** This will create a branch in the output tree called
      TimeDetPoint, setting the last parameter to kFALSE means:
      this collection will not be written to the file, it will exist
      only during the simulation.
  */

  FairRootManager::Instance()->Register("TimeDetPoint", "TimeDet",
                                        fTimeDetPointCollection, kTRUE);
}



TClonesArray* TimeDet::GetCollection(Int_t iColl) const
{
  if (iColl == 0) { return fTimeDetPointCollection; }
  else { return NULL; }
}



void TimeDet::Reset()
{
  fTimeDetPointCollection->Clear();
}



//void TimeDet::SetZpositions(Double_t z0)
//{
//  fzPos = z0;
//}



void TimeDet::ConstructGeometry()
{
  TGeoVolume *top = gGeoManager->GetTopVolume();
  
  TGeoMedium *Sens =gGeoManager->GetMedium("ShipSens");
  InitMedium("Scintillator");
  
  double dz  =    1.5;
  
  fDetector = gGeoManager->MakeBox("TimeDet",Sens,fxSize,fySize,dz);
  fDetector->SetLineColor(kMagenta-10);
  
  top->AddNode(fDetector, 1, new TGeoTranslation(0,0,fzPos));
  AddSensitiveVolume(fDetector);

  return;
}



TimeDetPoint* TimeDet::AddHit(Int_t trackID, Int_t detID,
			TVector3 pos, TVector3 mom,
			Double_t time, Double_t length,
			Double_t eLoss, Int_t pdgCode,TVector3 Lpos, TVector3 Lmom)
{
  TClonesArray& clref = *fTimeDetPointCollection;
  Int_t size = clref.GetEntriesFast();
  // cout << "veto hit called "<< pos.z()<<endl;
  return new(clref[size]) TimeDetPoint(trackID, detID, pos, mom,
		         time, length, eLoss, pdgCode,Lpos,Lmom);
}


ClassImp(TimeDet)
