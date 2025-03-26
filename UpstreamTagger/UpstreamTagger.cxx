// RPC Timing Detector
// 17/12/2019
// celso.franco@cern.ch

#include "UpstreamTagger.h"
#include "UpstreamTaggerPoint.h"
#include "UpstreamTaggerHit.h"

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

#include <ROOT/TSeq.hxx>
#include <iostream>
#include <sstream>
using std::cout;
using std::endl;
using ROOT::TSeq;
using ShipUnit::m;
using ShipUnit::cm;


UpstreamTagger::UpstreamTagger()
  : FairDetector("UpstreamTagger", kTRUE, kUpstreamTagger),
    fTrackID(-1),
    fVolumeID(-1),
    fPos(),
    fMom(),
    fTime(-1.),
    fLength(-1.),
    fELoss(-1),
    //
    det_zPos(0),

    //
    UpstreamTagger_fulldet(0),
    scoringPlaneUBText(0),
  //
    fUpstreamTaggerPointCollection(new TClonesArray("UpstreamTaggerPoint"))
{
}

UpstreamTagger::UpstreamTagger(const char* name, Bool_t active)
  : FairDetector(name, active, kUpstreamTagger),
    fTrackID(-1),
    fVolumeID(-1),
    fPos(),
    fMom(),
    fTime(-1.),
    fLength(-1.),
    fELoss(-1),
    //
    det_zPos(0),

    //
    UpstreamTagger_fulldet(0),
    scoringPlaneUBText(0), // Initialize new scoring plane to nullptr
        //
    fUpstreamTaggerPointCollection(new TClonesArray("UpstreamTaggerPoint"))
{
}


void UpstreamTagger::Initialize()
{
  FairDetector::Initialize();
}


UpstreamTagger::~UpstreamTagger()
{
  if (fUpstreamTaggerPointCollection) {
    fUpstreamTaggerPointCollection->Delete();
    delete fUpstreamTaggerPointCollection;
  }
}



Int_t UpstreamTagger::InitMedium(const char* name)
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



Bool_t  UpstreamTagger::ProcessHits(FairVolume* vol)
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

    AddHit(fTrackID, uniqueId, TVector3(xmean, ymean,  zmean),
           TVector3(fMom.Px(), fMom.Py(), fMom.Pz()), fTime, fLength,
           fELoss,pdgCode,TVector3(Pos.X(), Pos.Y(), Pos.Z()),
	   TVector3(Mom.Px(), Mom.Py(), Mom.Pz()) );

    // Increment number of veto det points in TParticle
    ShipStack* stack = (ShipStack*) gMC->GetStack();
    stack->AddPoint(kUpstreamTagger);
  }

  return kTRUE;
}



void UpstreamTagger::EndOfEvent()
{
  fUpstreamTaggerPointCollection->Clear();
}



void UpstreamTagger::Register()
{

  /** This will create a branch in the output tree called
      UpstreamTaggerPoint, setting the last parameter to kFALSE means:
      this collection will not be written to the file, it will exist
      only during the simulation.
  */

  FairRootManager::Instance()->Register("UpstreamTaggerPoint", "UpstreamTagger",
                                        fUpstreamTaggerPointCollection, kTRUE);
}



TClonesArray* UpstreamTagger::GetCollection(Int_t iColl) const
{
  if (iColl == 0) { return fUpstreamTaggerPointCollection; }
  else { return NULL; }
}



void UpstreamTagger::Reset()
{
  fUpstreamTaggerPointCollection->Clear();
}



void UpstreamTagger::ConstructGeometry()
{
  TGeoVolume *top = gGeoManager->GetTopVolume();

  //////////////////////////////////////////////////////

  ///////////////////////////////////////////////////////

  ///////////////////////////////////////////////////////

  InitMedium("vacuum");
  TGeoMedium *Vacuum_box =gGeoManager->GetMedium("vacuum");
  ///////////////////////////////////////////////////////////////////

  // Adding UBT Extension
  if (!Vacuum_box) {
      Fatal("ConstructGeometry", "Medium 'vacuum' not found.");
  }

  UpstreamTagger_fulldet = gGeoManager->MakeBox("Upstream_Tagger", Vacuum_box, xbox_fulldet/2.0, ybox_fulldet/2.0, zbox_fulldet/2.0);
  UpstreamTagger_fulldet->SetLineColor(kGreen);

  top->AddNode(UpstreamTagger_fulldet, 1, new TGeoTranslation(0.0, 0.0, det_zPos));
  AddSensitiveVolume(UpstreamTagger_fulldet);
  cout << " Z Position (Upstream Tagger1) " << det_zPos << endl;
  //////////////////////////////////////////////////////////////////

  return;
}



UpstreamTaggerPoint* UpstreamTagger::AddHit(Int_t trackID, Int_t detID,
			TVector3 pos, TVector3 mom,
			Double_t time, Double_t length,
			Double_t eLoss, Int_t pdgCode,TVector3 Lpos, TVector3 Lmom)
{
  TClonesArray& clref = *fUpstreamTaggerPointCollection;
  Int_t size = clref.GetEntriesFast();

  return new(clref[size]) UpstreamTaggerPoint(trackID, detID, pos, mom,
		         time, length, eLoss, pdgCode,Lpos,Lmom);
}
