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
: FairDetector("TargetTrackers", "",kTRUE),
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

Scifi::Scifi(const char* name,const Double_t Xdim, const Double_t Ydim, const Double_t Zdim, Bool_t Active,const char* Title)
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
	XDimension = Xdim;
	YDimension = Ydim;
	ZDimension = Zdim;
}

Scifi::~Scifi()
{
    if (fScifiPointCollection) {
        fScifiPointCollection->Delete();
        delete fScifiPointCollection;
    }
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


void Scifi::SetDetectorDimension(Double_t xdim, Double_t ydim, Double_t zdim)
{
    XDimension = xdim;
    YDimension = ydim;
    ZDimension = zdim;
}


void Scifi::ConstructGeometry()
{
	TGeoVolume *volTarget = gGeoManager->GetVolume("volTarget");

	InitMedium("TTmedium");
	TGeoMedium *medium =gGeoManager->GetMedium("TTmedium");

	TGeoBBox *ScifiBox = new TGeoBBox("ScifiBox",XDimension/2, YDimension/2, ZDimension/2);
	TGeoVolume *volScifi = new TGeoVolume("Scifi",ScifiBox,medium);
	volScifi->SetLineColor(kYellow - 10);
	AddSensitiveVolume(volScifi); 
	Double_t d_tt = -FullDetZdim/2 + ZDimension/2;
	Double_t zpos = 0;
	Int_t n = 0;
	for(int i=0;i<fNplanes;i++)
	{		
	  volTarget->AddNode(volScifi,n,new TGeoTranslation(0,0, DeltaZ + d_tt+i*(ZDimension+DeltaZ))); //target starts with first wall
	  n++;
	}   
}


Bool_t  Scifi::ProcessHits(FairVolume* vol)
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
        TParticle* p=gMC->GetStack()->GetCurrentTrack();
        Int_t pdgCode = p->GetPdgCode();
	gMC->CurrentVolID(fVolumeID);

	TLorentzVector Pos; 
        gMC->TrackPosition(Pos); 
        Double_t xmean = (fPos.X()+Pos.X())/2. ;      
        Double_t ymean = (fPos.Y()+Pos.Y())/2. ;      
        Double_t zmean = (fPos.Z()+Pos.Z())/2. ;     
        
        
        AddHit(fTrackID, fVolumeID, TVector3(xmean,ymean,zmean),
               TVector3(fMom.Px(), fMom.Py(), fMom.Pz()), fTime, fLength,
               fELoss, pdgCode);
        
        // Increment number of muon det points in TParticle
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
    //cout << "brick hit called"<< pos.z()<<endl;
    return new(clref[size]) ScifiPoint(trackID, detID, pos, mom,
                                       time, length, eLoss, pdgCode);
}


ClassImp(Scifi)








