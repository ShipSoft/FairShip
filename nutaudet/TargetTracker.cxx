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

TargetTracker::TargetTracker(const char* name, Bool_t Active,const char* Title)
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

void TargetTracker::SetTargetTrackerParam(Double_t TTX, Double_t TTY, Double_t TTZ,
                                          Double_t composite_z_, Double_t sci_fi_z_,
                                          Double_t support_z_) ////
{
    TTrackerX = TTX;
    TTrackerY = TTY;
    TTrackerZ = TTZ;
    composite_z = composite_z_;	////
    sci_fi_z = sci_fi_z_;	//// (!) Change to 5.33 * dSciFi
    support_z = support_z_;	////
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

//// (!) The function to define a BOX volume
TGeoVolume* TargetTracker::DefineVolume(const std::string& name, Double_t x_half_size,
                                        Double_t y_half_size, Double_t z_half_size,
                                        const std::string& medium_name,
                                        int colour, size_t transparency_level)
{
    InitMedium(medium_name.c_str());
    TGeoMedium *medium = gGeoManager->GetMedium(medium_name.c_str());
    TGeoBBox* geo_box = new TGeoBBox((name + "_box").c_str(), x_half_size, y_half_size, z_half_size);
    TGeoVolume* geo_volume = new TGeoVolume(name.c_str(), geo_box, medium);
    geo_volume->SetLineColor(colour);
    geo_volume->SetTransparency(transparency_level);
    geo_volume->SetVisibility(kTRUE);
    return geo_volume;
}

void TargetTracker::ConstructGeometry() ////
{
  //(!) Move to the definition part----------------------------------------------------------
  Int_t nSciFi = 80; 			//Number of fibers on 1st layer
  Int_t nStep = 3;			//For triangle definition of fiber volumes
  Double_t dFiber = 0.24 * mm; 		//Inner diameter sensitive core ??? 
  Double_t dSciFi = 0.25 * mm;		//Full diameter with 
  Double_t LySciFi = 2424 * mm; 	//Long ~2424 mm ???
  Double_t LxSciFi = dSciFi * nSciFi; 	//Width ~132 mm
  Double_t LzSciFi = 5.33 * dSciFi; 	//Height - six fiber layers
  Double_t distFiber = dSciFi * 0.91; 	//Distance between ...???
  
  
  //???
  InitMedium("TTmedium");
  TGeoMedium *TTmedium = gGeoManager->GetMedium("TTmedium");
  
  InitMedium("vacuum");
  TGeoMedium *vacuum = gGeoManager->GetMedium("vacuum");

  InitMedium("Composite");
  TGeoMedium *Composite = gGeoManager->GetMedium("Composite");

  InitMedium("SciFi");
  TGeoMedium *SciFi = gGeoManager->GetMedium("SciFi");

  InitMedium("Airex");
  TGeoMedium *Airex = gGeoManager->GetMedium("Airex");

  
  //Target Tracker 
  TGeoVolume *volTarget = gGeoManager->GetVolume("volTarget");

  //A plane of TTracker x-y with composite and support
  //TTrackerZ = 2 * c.NuTauTT.composite_z + c.NuTauTT.sci_fi_z + 2 * c.NuTauTT.support_z 
  TGeoBBox* TT_box = new TGeoBBox("TT_box", TTrackerX / 2, TTrackerY / 2, TTrackerZ / 2);
  TGeoVolume* TT_volume = new TGeoVolume("TT", TT_box, vacuum);
  TT_volume->SetLineColor(kBlue - 1);
  //TT_volume->SetTransparency(1);
  TT_volume->SetVisibility(1);
  TT_volume->SetVisDaughters(1);


  //Carbon Composite
  TGeoBBox* TT_composite_box = new TGeoBBox("TT_composite_box", TTrackerX / 2, TTrackerY / 2, composite_z / 2);
  TGeoVolume* TT_composite_volume = new TGeoVolume("TT_composite", TT_composite_box, Composite);
  TT_composite_volume->SetLineColor(kGray - 1);
  TT_composite_volume->SetVisibility(1);
  
  //Support Airex (or Nomex)
  TGeoBBox* TT_support_box = new TGeoBBox("TT_support_box", TTrackerX / 2, TTrackerY / 2, support_z / 2);
  TGeoVolume* TT_support_volume = new TGeoVolume("TT_support", TT_support_box, Airex);
  TT_support_volume->SetLineColor(kYellow - 1);
  TT_support_volume->SetVisibility(1);

  //SciFi tracker (with x and y), size = 2 * sci_fi_size
  TGeoBBox* TT_scifi_plane_box = new TGeoBBox("TT_scifi_plane_box", TTrackerX / 2, TTrackerY / 2, sci_fi_z / 2);
  TGeoVolume* TT_scifi_plane_volume = new TGeoVolume("TT_scifi_plane", TT_scifi_plane_box, SciFi);
  TT_scifi_plane_volume->SetLineColor(kGreen - 1);

  //SciFi mat (total 4 vertical and 8 horisontal)
  //(!) Change material to Epoxy Glue with TiO2
  TGeoBBox* TT_scifi_mat_box = new TGeoBBox("TT_scifi_mat_box", TTrackerX / 2, TTrackerY / 2, sci_fi_z / 2);
  TGeoVolume* TT_scifi_mat_volume = new TGeoVolume("TT_scifi_mat", TT_scifi_mat_box, vacuum);
  TT_scifi_mat_volume->SetLineColor(kGreen - 2);

  //Scintillating Fiber
  TGeoTube *TT_scifiber_tube = new TGeoTube("TT_scifiber_tube", 0, dFiber / 2, LySciFi / 2);
  TGeoVolume *TT_scifiber_volume = new TGeoVolume("TT_scifiber", TT_scifiber_tube, SciFi);
  TT_scifiber_volume->SetLineColor(kGreen - 3);


  AddSensitiveVolume(TT_scifi_plane_volume);
  //AddSensitiveVolume(TT_scifiber_volume);
  
  //Create physical volumes and multiply
  //vol_scifi->AddNode(vol_scifi_mat, 0, new TGeoTranslation(0, 0, 0));

  TT_volume->AddNode(TT_composite_volume, 0, new TGeoTranslation(0, 0, - TTrackerZ / 2 + composite_z / 2));
  TT_volume->AddNode(TT_scifi_plane_volume, 0, new TGeoTranslation(0, 0, - TTrackerZ / 2 + composite_z + sci_fi_z / 2));
  TT_volume->AddNode(TT_scifi_plane_volume, 1, new TGeoTranslation(0, 0, - TTrackerZ / 2 + composite_z + sci_fi_z + sci_fi_z / 2));
  TT_volume->AddNode(TT_support_volume, 0, new TGeoTranslation(0, 0, - TTrackerZ / 2 + composite_z + 2 * sci_fi_z + support_z / 2));
  TT_volume->AddNode(TT_composite_volume, 1, new TGeoTranslation(0, 0, - TTrackerZ / 2 + composite_z + 2 * sci_fi_z + support_z + composite_z / 2));
  ////Double_t first_tt_position = -ZDimension / 2 + TTrackerZ / 2;
  Double_t first_tt_position = -ZDimension / 2 + TTrackerZ / 2 + TTrackerZ / 10 ; //Manually + TTrackerZ / 20 to shift TT. Remove that (!)

  // l < fNTT
  for (int l = 0; l < fNTT; ++l) 
  {
    volTarget->AddNode(TT_volume, l, new TGeoTranslation(0, 0, first_tt_position + l * (TTrackerZ + CellWidth)));
  }
//------------------------------------------------------------------------------------
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
    if ( gMC->IsTrackExiting()    ||
        gMC->IsTrackStop()       ||
        gMC->IsTrackDisappeared()   ) {
        fTrackID  = gMC->GetStack()->GetCurrentTrackNumber();
        //Int_t fTrackID  = gMC->GetStack()->GetCurrentTrackNumber();
        gMC->CurrentVolID(fVolumeID);
	//gGeoManager->PrintOverlaps();
	
	//cout<< "detID = " << detID << endl;
	Int_t MaxLevel = gGeoManager->GetLevel();
	const Int_t MaxL = MaxLevel;
       	//cout << gMC->CurrentVolPath()<< endl;
	

	const char *name;
	
	Double_t zEnd = 0, zStart =0;

	
	if (fELoss == 0. ) { return kFALSE; }
        TParticle* p=gMC->GetStack()->GetCurrentTrack();
	Int_t fMotherID =p->GetFirstMother();
	Int_t pdgCode = p->GetPdgCode();

        TLorentzVector Pos; 
        gMC->TrackPosition(Pos); 
        Double_t xmean = (fPos.X()+Pos.X())/2. ;      
        Double_t ymean = (fPos.Y()+Pos.Y())/2. ;      
        Double_t zmean = (fPos.Z()+Pos.Z())/2. ;     
        

	AddHit(fTrackID,fVolumeID, TVector3(xmean, ymean,  zmean),
               TVector3(fMom.Px(), fMom.Py(), fMom.Pz()), fTime, fLength,
               fELoss, pdgCode);
	
        // Increment number of muon det points in TParticle
        ShipStack* stack = (ShipStack*) gMC->GetStack();
        stack->AddPoint(ktauTT);
    }
    
    return kTRUE;
}


void TargetTracker::DecodeTTID(Int_t detID, Int_t &NTT)
{
  NTT = detID;
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

