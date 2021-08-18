#include "Scifi.h"
#include "ScifiPoint.h"

#include "TGeoManager.h"
#include "FairRun.h"                    // for FairRun
#include "FairRuntimeDb.h"              // for FairRuntimeDb
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
#include "TParticle.h"

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
#include "ShipUnit.h"
#include "ShipStack.h"

#include "TGeoUniformMagField.h"
#include <stddef.h>                     // for NULL
#include <iostream>                     // for operator<<, basic_ostream, etc

using std::cout;
using std::endl;

using namespace ShipUnit;

Scifi::Scifi()
: FairDetector("Scifi", "", kTRUE),
fTrackID(-1),
fVolumeID(-1),
fPos(),
fMom(),
fTime(-1.),
fLength(-1.),
fELoss(-1),
fScifiPointCollection(new TClonesArray("ScifiPoint"))
{
}

Scifi::Scifi(const char* name, const Double_t xdim, const Double_t ydim, const Double_t zdim, Bool_t Active, const char* Title)
: FairDetector(name, true, kLHCScifi),
fTrackID(-1),
fVolumeID(-1),
fPos(),
fMom(),
fTime(-1.),
fLength(-1.),
fELoss(-1),
fScifiPointCollection(new TClonesArray("ScifiPoint"))
{
	fXDimension = xdim;
	fYDimension = ydim;
	fZDimension = zdim;
}

Scifi::~Scifi()
{
    if (fScifiPointCollection) {
        fScifiPointCollection->Delete();
        delete fScifiPointCollection;
    }
}

void Scifi::SetScifiParam(Double_t xdim, Double_t ydim, Double_t zdim)
{
	fXDimension = xdim;
	fYDimension = ydim;
	fZDimension = zdim;
}

void Scifi::SetMatParam(Double_t scifimat_width, Double_t scifimat_length, Double_t scifimat_z, Double_t scifimat_gap)
{
    fWidthScifiMat = scifimat_width;  
    fLengthScifiMat = scifimat_length;
    fZScifiMat = scifimat_z;
    fGapScifiMat = scifimat_gap; //dead zone between mats
}
void Scifi::SetPlaneParam(Double_t carbonfiber_z, Double_t honeycomb_z)
{
    fZCarbonFiber = carbonfiber_z; 
    fZHoneycomb = honeycomb_z; 
}

void Scifi::SetPlastBarParam(Double_t plastbar_x, Double_t plastbar_y, Double_t plastbar_z)
{
    fXPlastBar = plastbar_x;
    fYPlastBar = plastbar_y; 
    fZPlastBar = plastbar_z; 
}

void Scifi::SetScifiSep(Double_t scifi_separation)
{
    fSeparationBrick = scifi_separation;
}

void Scifi::SetZOffset(Double_t offset_z)
{
    fZOffset = offset_z;
}

void Scifi::SetNMats(Int_t nmats)
{
    fNMats = nmats;
}

void Scifi::SetNScifi(Int_t nscifi)
{
    fNScifi = nscifi;
}

void Scifi::SetNSiPMs(Int_t nsipms)
{
    fNSiPMs = nsipms;
}

void Scifi::Initialize()
{
    FairDetector::Initialize();
}

// -----   Private method InitMedium
Int_t Scifi::InitMedium(const char* name)
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

void Scifi::ConstructGeometry()
{
  InitMedium("vacuum");
  TGeoMedium *vacuum = gGeoManager->GetMedium("vacuum");

  InitMedium("CarbonComposite");
  TGeoMedium *CarbonComposite = gGeoManager->GetMedium("CarbonComposite");

  InitMedium("SciFiMat");
  TGeoMedium *SciFiMat = gGeoManager->GetMedium("SciFiMat");

  InitMedium("rohacell");
  TGeoMedium *rohacell = gGeoManager->GetMedium("rohacell");

  InitMedium("air");
  TGeoMedium *air = gGeoManager->GetMedium("air");

  InitMedium("Polycarbonate");
  TGeoMedium *PlasticBase = gGeoManager->GetMedium("Polycarbonate");
  
  TGeoVolume *volTarget = gGeoManager->GetVolume("volTarget");

  //Carbon Fiber Film
  TGeoVolume *CarbonFiberVolume = gGeoManager->MakeBox("CarbonFiber", CarbonComposite, fXDimension/2, fYDimension/2, fZCarbonFiber/2);
  CarbonFiberVolume->SetLineColor(kGray - 2);
  CarbonFiberVolume->SetVisibility(1);

  //Honeycomb Rohacell
  TGeoVolume *HoneycombVolume = gGeoManager->MakeBox("Honeycomb", rohacell, fXDimension/2, fYDimension/2, fZHoneycomb/2);
  HoneycombVolume->SetLineColor(kYellow);
  HoneycombVolume->SetVisibility(1);

  //Plastic/Air
  //Definition of the box containing polycarbonate pieces and an air gap
  TGeoVolume *PlasticAirVolume = gGeoManager->MakeBox("PlasticAir", air, fXDimension/2, fYDimension/2, fZPlastBar/2); 
  PlasticAirVolume->SetLineColor(kGray-1);
  PlasticAirVolume->SetVisibility(1);
  PlasticAirVolume->SetVisDaughters(1);
  
  //Plastic bars
  TGeoVolume *PlasticBarVolume = gGeoManager->MakeBox("PlasticBar", PlasticBase, fXPlastBar/2, fYPlastBar/2, fZPlastBar/2); 
  PlasticBarVolume->SetLineColor(kGray-4);
  PlasticBarVolume->SetVisibility(1);

  PlasticAirVolume->AddNode(PlasticBarVolume, 0, new TGeoTranslation(- fXDimension/2 + fXPlastBar/2, 0, 0));  //bars are placed || to y
  PlasticAirVolume->AddNode(PlasticBarVolume, 1, new TGeoTranslation(+ fXDimension/2 - fXPlastBar/2, 0, 0));
  
  //SciFi mats for X and Y fiber planes
  TGeoVolume *HorMatVolume = gGeoManager->MakeBox("HorMatVolume", SciFiMat, fLengthScifiMat/2, fWidthScifiMat/2, fZScifiMat/2);      
  HorMatVolume->SetLineColor(kBlue - 2);
  HorMatVolume->SetVisibility(1);

  TGeoVolume *VertMatVolume = gGeoManager->MakeBox("VertMatVolume", SciFiMat, fWidthScifiMat/2, fLengthScifiMat/2, fZScifiMat/2);      
  VertMatVolume->SetLineColor(kBlue - 2);
  VertMatVolume->SetVisibility(1);

  //Add SciFi mat as sensitive unit
  AddSensitiveVolume(HorMatVolume);
  AddSensitiveVolume(VertMatVolume);
  
  //Rotation 
  TGeoRotation *rot = new TGeoRotation("rot", 90, 180, 0);

  // DetID is of the form: 
  // first digit - station number
  // second digit - type of the plane: 0-horizontal fiber, 1-vertical fiber
  // third digit - mat number
  // e.g. DetID = 102 -> station 1, horizontal fiber plane, mat 2
  for (int istation = 0; istation < fNScifi; istation++){
    
    TGeoVolumeAssembly *ScifiVolume = new TGeoVolumeAssembly("ScifiVolume");
    volTarget->AddNode(ScifiVolume, 100*(istation+1), new TGeoTranslation(0, 0, fZOffset + istation*fSeparationBrick));
    
    TGeoVolumeAssembly *ScifiHorPlaneVol = new TGeoVolumeAssembly("ScifiHorPlaneVol");
    TGeoVolumeAssembly *ScifiVertPlaneVol = new TGeoVolumeAssembly("ScifiVertPlaneVol");

    //Adding the first half of the SciFi module that contains horizontal fibres
    ScifiVolume->AddNode(CarbonFiberVolume, 0, new TGeoTranslation(0, 0, fZCarbonFiber/2));
    ScifiVolume->AddNode(HoneycombVolume, 0, new TGeoTranslation(0, 0, fZCarbonFiber + fZHoneycomb/2));
    ScifiVolume->AddNode(CarbonFiberVolume, 1, new TGeoTranslation(0, 0, fZCarbonFiber + fZHoneycomb + fZCarbonFiber/2));
    ScifiVolume->AddNode(ScifiHorPlaneVol, 0, new TGeoTranslation(0, 0, 2*fZCarbonFiber + fZHoneycomb + fZScifiMat/2));
    ScifiVolume->AddNode(PlasticAirVolume, 0, new TGeoTranslation(0, 0, 2*fZCarbonFiber + fZHoneycomb + fZScifiMat + fZPlastBar/2));
  
    //Adding the second half of the SciFi module that contains vertical fibres
    ScifiVolume->AddNode(PlasticAirVolume, 1, new TGeoCombiTrans("rottrans0", 0, 0, 2*fZCarbonFiber + fZHoneycomb + fZScifiMat + 3*fZPlastBar/2, rot));
    ScifiVolume->AddNode(ScifiVertPlaneVol, 0, new TGeoTranslation(0, 0, 2*fZCarbonFiber + fZHoneycomb + fZScifiMat +2*fZPlastBar + fZScifiMat/2)); 
    ScifiVolume->AddNode(CarbonFiberVolume, 2, new TGeoTranslation(0, 0, 2*fZCarbonFiber + fZHoneycomb + fZScifiMat +2*fZPlastBar + fZScifiMat +fZCarbonFiber/2));
    ScifiVolume->AddNode(HoneycombVolume, 1, new TGeoTranslation(0, 0, 3*fZCarbonFiber + fZHoneycomb + fZScifiMat +2*fZPlastBar + fZScifiMat + fZHoneycomb/2));
    ScifiVolume->AddNode(CarbonFiberVolume, 3, new TGeoTranslation(0, 0, 3*fZCarbonFiber + 2*fZHoneycomb + fZScifiMat +2*fZPlastBar + fZScifiMat + fZCarbonFiber/2));

    //Creating Scifi planes by appending fiber mats
    for (int imat = 0; imat < fNMats; imat++){
        ScifiHorPlaneVol->AddNode(HorMatVolume, 100*(istation+1) + imat + 1, new TGeoTranslation(0, (imat-1)*(fWidthScifiMat+fGapScifiMat), 0));
        ScifiVertPlaneVol->AddNode(VertMatVolume, 100*(istation+1)+ imat + 11, new TGeoTranslation((imat-1)*(fWidthScifiMat+fGapScifiMat), 0, 0));
    }
  }
}

Bool_t  Scifi::ProcessHits(FairVolume* vol)
{
	/** This method is called from the MC stepping */
	//Set parameters at entrance of volume. Reset ELoss.
	if ( gMC->IsTrackEntering() ) 
	{
		fELoss  = 0.;
		fTime   = gMC->TrackTime() * 1.0e09;
		fLength = gMC->TrackLength();
		gMC->TrackPosition(fPos);
		gMC->TrackMomentum(fMom);
	}
	// Sum energy loss for all steps in the active volume
	fELoss += gMC->Edep();

	// Create ScifiPoint at exit of active volume
	if ( gMC->IsTrackExiting()    ||
			gMC->IsTrackStop()       || 
			gMC->IsTrackDisappeared()   ) {
		fTrackID  = gMC->GetStack()->GetCurrentTrackNumber();
		fVolumeID = vol->getMCid();
		gMC->CurrentVolID(fVolumeID);

		gGeoManager->PrintOverlaps();

		if (fELoss == 0. ) { return kFALSE; }
		TParticle* p=gMC->GetStack()->GetCurrentTrack();
		Int_t pdgCode = p->GetPdgCode();

		TLorentzVector Pos; 
		gMC->TrackPosition(Pos); 
		Double_t xmean = (fPos.X()+Pos.X())/2. ;
		Double_t ymean = (fPos.Y()+Pos.Y())/2. ;
		Double_t zmean = (fPos.Z()+Pos.Z())/2. ;


		AddHit(fTrackID,fVolumeID, TVector3(xmean, ymean,  zmean),
				TVector3(fMom.Px(), fMom.Py(), fMom.Pz()), fTime, fLength,
				fELoss, pdgCode);

		// Increment number of det points in TParticle
		ShipStack* stack = (ShipStack*) gMC->GetStack();
		stack->AddPoint(kLHCScifi);
	}   

	return kTRUE;
}

void Scifi::EndOfEvent()
{
    fScifiPointCollection->Clear();
}


void Scifi::Register()
{
    
    /** This will create a branch in the output tree called
     ScifiPoint, setting the last parameter to kFALSE means:
     this collection will not be written to the file, it will exist
     only during the simulation.
     */
    
    FairRootManager::Instance()->Register("ScifiPoint", "Scifi",
                                          fScifiPointCollection, kTRUE);
}

TClonesArray* Scifi::GetCollection(Int_t iColl) const
{
    if (iColl == 0) { return fScifiPointCollection; }
    else { return NULL; }
}

void Scifi::Reset()
{
    fScifiPointCollection->Clear();
}


ScifiPoint* Scifi::AddHit(Int_t trackID, Int_t detID,
                           TVector3 pos, TVector3 mom,
                           Double_t time, Double_t length,
                           Double_t eLoss, Int_t pdgCode)
{
    TClonesArray& clref = *fScifiPointCollection;
    Int_t size = clref.GetEntriesFast();
    return new(clref[size]) ScifiPoint(trackID, detID, pos, mom,
                                       time, length, eLoss, pdgCode);
}


ClassImp(Scifi)
