//
//  TargetTracker.cxx
//  
//
//  Created by Annarita Buonaura on 21/10/15.
//
//

#include "TargetTracker.h"

#include "TTPoint.h"

#include "TGeoManager.h"
#include "FairRun.h"                    // for FairRun
#include "FairRuntimeDb.h"              // for FairRuntimeDb
#include <iosfwd>                    // for ostream
#include "TList.h"                      // for TListIter, TList (ptr only)
#include "TObjArray.h"                  // for TObjArray
#include "TString.h"                    // for TString

#include "TClonesArray.h"
#include "TVirtualMC.h"

#include "TGeoBBox.h"
#include "TGeoTrd1.h"
#include "TGeoCompositeShape.h"
#include "TGeoTube.h"
#include "TGeoMaterial.h"
#include "TGeoMedium.h"
#include "TGeoTrd1.h"
#include "TGeoArb8.h"

#include "TParticle.h"
#include "TParticlePDG.h"
#include "TParticleClassPDG.h"
#include "TVirtualMCStack.h"

#include "FairVolume.h"
#include "FairGeoVolume.h"
#include "FairGeoNode.h"
#include "FairRootManager.h"
#include "FairGeoLoader.h"
#include "FairGeoInterface.h"
#include "FairGeoTransform.h"
#include "FairGeoMedia.h"
#include "FairGeoMedium.h"
#include "FairGeoBuilder.h"
#include "FairRun.h"
#include "FairRuntimeDb.h"

#include "ShipDetectorList.h"
#include "ShipUnit.h"
#include "ShipStack.h"

#include "TGeoUniformMagField.h"
#include <stddef.h>                     // for NULL
#include <iostream>                     // for operator<<, basic_ostream,etc
#include <string.h>

using std::cout;
using std::endl;

using namespace ShipUnit;

TargetTracker::TargetTracker()
: FairDetector("TargetTracker", "",kTRUE),
  fTrackID(-1),
fVolumeID(-1),
fPos(),
fMom(),
fTime(-1.),
fLength(-1.),
fELoss(-1),
fTTPointCollection(new TClonesArray("TTPoint"))
{
}

TargetTracker::TargetTracker(const char* name, Double_t TTX, Double_t TTY, Double_t TTZ, Bool_t Active,const char* Title)
: FairDetector(name, true, ktauTT),
  fTrackID(-1),
fVolumeID(-1),
fPos(),
fMom(),
fTime(-1.),
fLength(-1.),
fELoss(-1),
fTTPointCollection(new TClonesArray("TTPoint"))
{
  TTrackerX = TTX;
  TTrackerY = TTY;
  TTrackerZ = TTZ;
}

TargetTracker::~TargetTracker()
{
    if (fTTPointCollection) {
        fTTPointCollection->Delete();
        delete fTTPointCollection;
    }
}

void TargetTracker::Initialize()
{
    FairDetector::Initialize();
}

// -----   Private method InitMedium
Int_t TargetTracker::InitMedium(const char* name)
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

void TargetTracker::SetSciFiParam(Double_t scifimat_width_, Double_t scifimat_hor_, Double_t scifimat_vert_, 
                                    Double_t scifimat_z_, Double_t support_z_, Double_t honeycomb_z_)
{
  scifimat_width = scifimat_width_;
  scifimat_hor = scifimat_hor_;
  scifimat_vert = scifimat_vert_;
  scifimat_z = scifimat_z_;
  support_z = support_z_; 
  honeycomb_z = honeycomb_z_;  
}

void TargetTracker::SetNumberSciFi(Int_t n_hor_planes_, Int_t n_vert_planes_)
{
  n_hor_planes = n_hor_planes_;
  n_vert_planes = n_vert_planes_;
}

void TargetTracker::SetTargetTrackerParam(Double_t TTX, Double_t TTY, Double_t TTZ)
{
    TTrackerX = TTX;
    TTrackerY = TTY;
    TTrackerZ = TTZ;
}

void TargetTracker::SetBrickParam(Double_t CellW)
{
  CellWidth = CellW;
}

void TargetTracker::SetTotZDimension(Double_t Zdim)
{
  ZDimension = Zdim;
}

void TargetTracker::SetNumberTT(Int_t n)
{
  fNTT =n;
}

void TargetTracker::SetDesign(Int_t Design)
{
  fDesign = Design;
}

void TargetTracker::ConstructGeometry()
{
  InitMedium("TTmedium");
  TGeoMedium *TTmedium = gGeoManager->GetMedium("TTmedium");

  InitMedium("vacuum");
  TGeoMedium *vacuum = gGeoManager->GetMedium("vacuum");

  InitMedium("CarbonComposite");
  TGeoMedium *CarbonComposite = gGeoManager->GetMedium("CarbonComposite");

  InitMedium("SciFiMat");
  TGeoMedium *SciFiMat = gGeoManager->GetMedium("SciFiMat");

  InitMedium("Airex");
  TGeoMedium *Airex = gGeoManager->GetMedium("Airex");
  
  //Target Tracker 
  TGeoVolume *volTarget = gGeoManager->GetVolume("volTarget");

  TGeoBBox* TT_box = new TGeoBBox("TT_box", TTrackerX / 2, TTrackerY / 2, TTrackerZ / 2);
  TGeoVolume* TT_volume = new TGeoVolume("TT", TT_box, vacuum);
  TT_volume->SetLineColor(kBlue - 1);
  //TT_volume->SetTransparency(1);
  TT_volume->SetVisibility(1);
  TT_volume->SetVisDaughters(1);

  //Support Carbon Composite
  TGeoBBox* TT_support_box = new TGeoBBox("TT_support_box", TTrackerX / 2, TTrackerY / 2, support_z / 2);
  TGeoVolume* TT_support_volume = new TGeoVolume("TT_support", TT_support_box, CarbonComposite);
  TT_support_volume->SetLineColor(kGray - 2);
  TT_support_volume->SetVisibility(1);

  //Honeycomb Airex (or Nomex)
  TGeoBBox* TT_honeycomb_box = new TGeoBBox("TT_honeycomb_box", TTrackerX / 2, TTrackerY / 2, honeycomb_z / 2);
  TGeoVolume* TT_honeycomb_volume = new TGeoVolume("TT_honeycomb", TT_honeycomb_box, Airex);
  TT_honeycomb_volume->SetLineColor(kYellow);
  TT_honeycomb_volume->SetVisibility(1);

    //SciFi planes
  TGeoBBox* TT_scifi_plane_hor_box = new TGeoBBox("TT_scifi_plane_hor_box", TTrackerX / 2, TTrackerY / 2, scifimat_z / 2);
  TGeoVolume* TT_scifi_plane_hor_volume = new TGeoVolume("TT_scifi_plane_hor", TT_scifi_plane_hor_box, SciFiMat);
  TT_scifi_plane_hor_volume->SetVisibility(1);

  TGeoBBox* TT_scifi_plane_vert_box = new TGeoBBox("TT_scifi_plane_vert_box", TTrackerX / 2, TTrackerY / 2, scifimat_z / 2);
  TGeoVolume* TT_scifi_plane_vert_volume = new TGeoVolume("TT_scifi_plane_vert", TT_scifi_plane_vert_box, SciFiMat);
  TT_scifi_plane_vert_volume->SetVisibility(1);
  
  //SciFi mats for X and Y 
  TGeoBBox* TT_scifimat_hor_box = new TGeoBBox("TT_scifimat_hor_box", scifimat_hor / 2, scifimat_width / 2, scifimat_z / 2);
  TGeoVolume* TT_scifimat_hor_volume = new TGeoVolume("TT_scifimat_hor", TT_scifimat_hor_box, SciFiMat);
  TT_scifimat_hor_volume->SetLineColor(kCyan-9);

  TGeoBBox* TT_scifimat_vert_box = new TGeoBBox("TT_scifimat_vert_box", scifimat_width / 2, scifimat_vert / 2, scifimat_z / 2);
  TGeoVolume* TT_scifimat_vert_volume = new TGeoVolume("TT_scifimat_vert", TT_scifimat_vert_box, SciFiMat);
  TT_scifimat_vert_volume->SetLineColor(kGreen-7);

  //Add SciFi mat as sensitive unit
  AddSensitiveVolume(TT_scifimat_hor_volume);
  AddSensitiveVolume(TT_scifimat_vert_volume);

  //Creating physical volumes and multiply
  for (int i = 0; i < n_hor_planes; i++){
    TT_scifi_plane_hor_volume->AddNode(TT_scifimat_hor_volume, i+1, new TGeoTranslation(0, (-(n_hor_planes-1)/2.0 + i)*scifimat_width, 0));
  }
  for (int i = 0; i < n_vert_planes; i++){
    TT_scifi_plane_vert_volume->AddNode(TT_scifimat_vert_volume, 100+i+1, new TGeoTranslation((-(n_vert_planes-1)/2.0 + i)*scifimat_width, 0, 0));
  }

  TT_volume->AddNode(TT_support_volume,          0, new TGeoTranslation(0, 0, -TTrackerZ/2 + support_z/2));
  TT_volume->AddNode(TT_scifi_plane_hor_volume,  0, new TGeoTranslation(0, 0, -TTrackerZ/2 + support_z + scifimat_z/2));
  TT_volume->AddNode(TT_scifi_plane_vert_volume, 0, new TGeoTranslation(0, 0, -TTrackerZ/2 + support_z + scifimat_z + scifimat_z/2));
  TT_volume->AddNode(TT_honeycomb_volume,        0, new TGeoTranslation(0, 0, -TTrackerZ/2 + support_z + 2*scifimat_z + honeycomb_z/2));
  TT_volume->AddNode(TT_support_volume,          1, new TGeoTranslation(0, 0, -TTrackerZ/2 + support_z + 2*scifimat_z + honeycomb_z + support_z/2));

  Double_t first_tt_position = -ZDimension / 2 + TTrackerZ / 2;

  //fNTT - number of TT walls 
  for (int l = 0; l < fNTT; ++l){
    volTarget->AddNode(TT_volume, 1000*(l+1), new TGeoTranslation(0, 0, first_tt_position + l * (TTrackerZ + CellWidth)));
  } 

}


Bool_t TargetTracker::ProcessHits(FairVolume* vol)
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
  if (gMC->IsTrackExiting()     ||
      gMC->IsTrackStop()        ||
      gMC->IsTrackDisappeared() ){
    if (fELoss == 0. ) { return kFALSE; }
    TParticle* p=gMC->GetStack()->GetCurrentTrack();
    Int_t pdgCode = p->GetPdgCode();
    fTrackID  = gMC->GetStack()->GetCurrentTrackNumber();

    gMC->CurrentVolID(fVolumeID); 
    Int_t detID = fVolumeID;
    Int_t TTstationID; 
    gMC->CurrentVolOffID(2, TTstationID); 
    fVolumeID = TTstationID + detID;

    TLorentzVector Pos; 
    gMC->TrackPosition(Pos); 
    Double_t xmean = (fPos.X()+Pos.X())/2. ;      
    Double_t ymean = (fPos.Y()+Pos.Y())/2. ;      
    Double_t zmean = (fPos.Z()+Pos.Z())/2. ; 

    AddHit(fTrackID, fVolumeID, TVector3(xmean, ymean,  zmean),
           TVector3(fMom.Px(), fMom.Py(), fMom.Pz()), 
           fTime, fLength, fELoss, pdgCode);

    // Increment number of muon det points in TParticle
    ShipStack* stack = (ShipStack*) gMC->GetStack();
    stack->AddPoint(ktauTT);
  }

  return kTRUE;
}


void TargetTracker::DecodeTTID(Int_t detID, Int_t &NTT, int &nplane, Bool_t &ishor)
{
  NTT = detID/1000;
  int idir = (detID - NTT*1000)/100;

  if (idir == 1) ishor = kFALSE;
  else if (idir == 0) ishor = kTRUE;

  nplane = (detID - NTT*1000 - idir*100);
}


void TargetTracker::EndOfEvent()
{
    fTTPointCollection->Clear();
}


void TargetTracker::Register()
{
    
    /** This will create a branch in the output tree called
     TargetPoint, setting the last parameter to kFALSE means:
     this collection will not be written to the file, it will exist
     only during the simulation.
     */
    
    FairRootManager::Instance()->Register("TTPoint", "TargetTracker",
                                          fTTPointCollection, kTRUE);
}

TClonesArray* TargetTracker::GetCollection(Int_t iColl) const
{
    if (iColl == 0) { return fTTPointCollection; }
    else { return NULL; }
}

void TargetTracker::Reset()
{
    fTTPointCollection->Clear();
}


TTPoint* TargetTracker::AddHit(Int_t trackID,Int_t detID,
                           TVector3 pos, TVector3 mom,
                           Double_t time, Double_t length,
			    Double_t eLoss, Int_t pdgCode)
{
    TClonesArray& clref = *fTTPointCollection;
    Int_t size = clref.GetEntriesFast();
    //cout << "brick hit called"<< pos.z()<<endl;
    return new(clref[size]) TTPoint(trackID,detID, pos, mom,
					time, length, eLoss, pdgCode);
}

ClassImp(TargetTracker)

