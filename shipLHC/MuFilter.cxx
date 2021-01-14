//
//  MuFilter.cxx
//
//  by A.Buonaura
//

#include "MuFilter.h"
#include "MuFilterPoint.h"

#include "TGeoManager.h"
#include "FairRun.h"                    // for FairRun
#include "FairRuntimeDb.h"              // for FairRuntimeDb
#include "TList.h"                      // for TListIter, TList (ptr only)
#include "TObjArray.h"                  // for TObjArray
#include "TString.h"                    // for TString

#include "TClonesArray.h"
#include "TVirtualMC.h"

#include "TGeoBBox.h"
#include "TGeoMaterial.h"
#include "TGeoMedium.h"

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

MuFilter::MuFilter()
: FairDetector("MuonFilter", "",kTRUE),
  fTrackID(-1),
fVolumeID(-1),
fPos(),
fMom(),
fTime(-1.),
fLength(-1.),
fELoss(-1),
fMuFilterPointCollection(new TClonesArray("MuFilterPoint"))
{
}

MuFilter::MuFilter(const char* name, Bool_t Active,const char* Title)
: FairDetector(name, true, kMuFilter),
  fTrackID(-1),
fVolumeID(-1),
fPos(),
fMom(),
fTime(-1.),
fLength(-1.),
fELoss(-1),
fMuFilterPointCollection(new TClonesArray("MuFilterPoint"))
{
}

MuFilter::~MuFilter()
{
    if (fMuFilterPointCollection) {
        fMuFilterPointCollection->Delete();
        delete fMuFilterPointCollection;
    }
}

void MuFilter::SetIronBlockDimensions(Double_t x, Double_t y, Double_t z)
{
	fFeBlockX = x;
	fFeBlockY = y;
	fFeBlockZ = z;
}

void MuFilter::SetMuFilterDimensions(Double_t x, Double_t y, Double_t z)
{	
	fMuFilterX = x;
	fMuFilterY = y;
	fMuFilterZ = z;
}

void MuFilter::SetUpstreamPlanesDimensions(Double_t x, Double_t y, Double_t z)
{
	fUpstreamDetX = x;
	fUpstreamDetY = y;
	fUpstreamDetZ = z;
}

void MuFilter::SetNUpstreamPlanes(Int_t n)
{
	fNUpstreamPlanes = n;
}

void MuFilter::SetUpstreamBarsDimensions(Double_t x, Double_t y, Double_t z)
{
        fUpstreamBarX = x;
	fUpstreamBarY = y;
	fUpstreamBarZ = z;
}

void MuFilter::SetNUpstreamBars(Int_t n)
{
	fNUpstreamBars = n;
}

void MuFilter::SetDownstreamPlanesDimensions(Double_t x, Double_t y, Double_t z)
{
	fDownstreamDetX = x;
	fDownstreamDetY = y;
	fDownstreamDetZ = z;
}

void MuFilter::SetNDownstreamPlanes(Int_t n)
{
	fNDownstreamPlanes = n;
}

void MuFilter::SetDownstreamBarsDimensions(Double_t x, Double_t y, Double_t z)
{
        fDownstreamBarX = x;
	fDownstreamBarY = y;
	fDownstreamBarZ = z;
}

void MuFilter::SetDownstreamVerticalBarsDimensions(Double_t x, Double_t y, Double_t z)
{
        fDownstreamBarX_ver = x;
	fDownstreamBarY_ver = y;
	fDownstreamBarZ_ver = z;
}

void MuFilter::SetNDownstreamBars(Int_t n)
{
	fNDownstreamBars = n;
}

void MuFilter::SetCenterZ(Double_t z)
{
	fCenterZ = z;
}

void MuFilter::SetXYDisplacement(Double_t x, Double_t y)
{
	fShiftX = x;
	fShiftY = y;
}

void MuFilter::SetYPlanesDisplacement(Double_t y)
{
        fShiftYEnd = y;
}

void MuFilter::SetSlope(Double_t Slope)
{
        fSlope = Slope;
}

void MuFilter::Initialize()
{
	FairDetector::Initialize();
}

// -----  Private method InitMedium
Int_t MuFilter::InitMedium(const char* name)
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

void MuFilter::ConstructGeometry()
{
	TGeoVolume *top=gGeoManager->GetTopVolume();
	if(top) cout<<" top volume found! "<<endl;
	gGeoManager->SetVisLevel(10);

	//Materials 
	InitMedium("air");
	TGeoMedium *air =gGeoManager->GetMedium("air");

	InitMedium("iron");
	TGeoMedium *Fe =gGeoManager->GetMedium("iron");

	InitMedium("polyvinyltoluene");
	TGeoMedium *Scint =gGeoManager->GetMedium("polyvinyltoluene");

	//Definition of the box containing Fe Blocks + Timing Detector planes 
	TGeoVolumeAssembly *volMuFilter = new TGeoVolumeAssembly("volMuFilter");

	//Iron blocks volume definition
	TGeoBBox *FeBlockBox = new TGeoBBox("FeBlockBox",fFeBlockX/2, fFeBlockY/2, fFeBlockZ/2);
	TGeoVolume *volFeBlock = new TGeoVolume("volFeBlock",FeBlockBox,Fe);
	volFeBlock->SetLineColor(19);

	top->AddNode(volMuFilter,1,new TGeoTranslation(fShiftX,fShiftY,fCenterZ));

	Double_t dy = 0;
	Double_t dz = 0;
	
	//*****************************************UPSTREAM SECTION*********************************//
	//Upstream Detector planes definition
	TGeoBBox *UpstreamDetBox = new TGeoBBox("UpstreamDetBox",fUpstreamDetX/2,fUpstreamDetY/2,fUpstreamDetZ/2);
	TGeoVolume *volUpstreamDet = new TGeoVolume("volUpstreamDet",UpstreamDetBox,air);
	volUpstreamDet->SetLineColor(kRed+2);

	//first loop, adding detector main boxes
	
	for(Int_t l=0; l<fNUpstreamPlanes; l++)
	{
	  dz = (fFeBlockZ + fUpstreamDetZ)*l;
	  dy = dz * TMath::Tan(TMath::DegToRad() * fSlope);
	  //last upstream station does not follow slope, start of support. Same dy is used for downstream planes
	  if (l == fNUpstreamPlanes - 1) dy = fShiftYEnd - fShiftY;

	  volMuFilter->AddNode(volFeBlock,l,new TGeoTranslation(0,fMuFilterY/2-fFeBlockY/2+dy,-fMuFilterZ/2+fFeBlockZ/2+dz));
	  volMuFilter->AddNode(volUpstreamDet,l,new TGeoTranslation(0,fMuFilterY/2-fFeBlockY/2+dy,-fMuFilterZ/2+fFeBlockZ+fUpstreamDetZ/2+dz));
	  dz+=fFeBlockZ+fUpstreamDetZ;
	}

	//adding staggered bars, first part, only 11 bars, (single stations, readout on both ends)
	
	TGeoBBox *MuUpstreamBar = new TGeoBBox("MuUpstreamBar",fUpstreamBarX/2, fUpstreamBarY/2, fUpstreamBarZ/2);
	TGeoVolume *volMuUpstreamBar = new TGeoVolume("volMuUpstreamBar",MuUpstreamBar,Scint);
	volMuUpstreamBar->SetLineColor(kBlue+2);
	AddSensitiveVolume(volMuUpstreamBar);
            
       //second loop, adding bars within each detector box
	
	for (Int_t ibar = 0; ibar < fNUpstreamBars; ibar++){
	  
	  Double_t dy_bar = -fUpstreamDetY/2 + fUpstreamBarY/2. + fUpstreamBarY*ibar; 
	  
	  TGeoTranslation *yztrans = new TGeoTranslation(0,dy_bar,0);
	  
	  volUpstreamDet->AddNode(volMuUpstreamBar,ibar+1E+3,yztrans);
			   }
	//*************************************DOWNSTREAM (high granularity) SECTION*****************//
	//Downstream Detector planes definition
	TGeoBBox *DownstreamDetBox = new TGeoBBox("DownstreamDetBox",fDownstreamDetX/2,fDownstreamDetY/2,fDownstreamDetZ/2);
	TGeoVolume *volDownstreamDet = new TGeoVolume("volDownstreamDet",DownstreamDetBox,air);
	volDownstreamDet->SetLineColor(kRed+2);

        //first loop, adding detector main boxes

	for(Int_t l=0; l<fNDownstreamPlanes; l++)
	{	  
	  volMuFilter->AddNode(volFeBlock,l+fNUpstreamPlanes,new TGeoTranslation(0,fMuFilterY/2-fFeBlockY/2+dy,-fMuFilterZ/2+fFeBlockZ/2+dz));
	  volMuFilter->AddNode(volDownstreamDet,l+fNUpstreamPlanes,new TGeoTranslation(0,fMuFilterY/2-fFeBlockY/2+dy,-fMuFilterZ/2+fFeBlockZ+fDownstreamDetZ/2+dz));
	  dz+=fFeBlockZ+fDownstreamDetZ;
	}

	//adding staggered bars, second part, 77 bars, each for x and y coordinates
	
	TGeoBBox *MuDownstreamBar_hor = new TGeoBBox("MuDownstreamBar_hor",fDownstreamBarX/2, fDownstreamBarY/2, fDownstreamBarZ/2);
	TGeoVolume *volMuDownstreamBar_hor = new TGeoVolume("volMuDownstreamBar_hor",MuDownstreamBar_hor,Scint);
	volMuDownstreamBar_hor->SetLineColor(kBlue+2);
	AddSensitiveVolume(volMuDownstreamBar_hor);

	//vertical bars, for x measurement
	TGeoBBox *MuDownstreamBar_ver = new TGeoBBox("MuDownstreamBar_ver",fDownstreamBarX_ver/2, fDownstreamBarY_ver/2, fDownstreamBarZ/2);
	TGeoVolume *volMuDownstreamBar_ver = new TGeoVolume("volMuDownstreamBar_ver",MuDownstreamBar_ver,Scint);
	volMuDownstreamBar_ver->SetLineColor(kGreen+2);
	AddSensitiveVolume(volMuDownstreamBar_ver);

	//second loop, adding bars within each detector box
	
	for (Int_t ibar = 0; ibar < fNDownstreamBars; ibar++){
	  //adding verizontal bars for y

	  Double_t dy_bar = -fDownstreamDetY/2 + fDownstreamBarY/2. + fDownstreamBarY*ibar; 
          Double_t dz_bar_hor = -fDownstreamDetZ/2. + fDownstreamBarZ/2.;

	  TGeoTranslation *yztrans = new TGeoTranslation(0,dy_bar,dz_bar_hor);
	  
	  volDownstreamDet->AddNode(volMuDownstreamBar_hor,ibar+1E+3,yztrans);
	  //adding vertical bars for x

	  Double_t dx_bar = -fDownstreamDetY/2 + fDownstreamBarX_ver/2. + fDownstreamBarX_ver*ibar; //they do not cover all the x region, but only 60 x 60.
          Double_t dz_bar_ver = -fDownstreamDetZ/2. + 2*fDownstreamBarZ + fDownstreamBarZ/2.;

	  TGeoTranslation *xztrans = new TGeoTranslation(dx_bar,0,dz_bar_ver);
	  
	  volDownstreamDet->AddNode(volMuDownstreamBar_ver,ibar+1E+5,xztrans);  
       
			   }    
}

Bool_t  MuFilter::ProcessHits(FairVolume* vol)
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

	// Create MuFilterPoint at exit of active volume
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

		// Increment number of muon det points in TParticle
		ShipStack* stack = (ShipStack*) gMC->GetStack();
		stack->AddPoint(kMuFilter);
	}   

	return kTRUE;
}

void MuFilter::EndOfEvent()
{
    fMuFilterPointCollection->Clear();
}


void MuFilter::Register()
{

    /** This will create a branch in the output tree called
 *      TargetPoint, setting the last parameter to kFALSE means:
 *           this collection will not be written to the file, it will exist
 *                only during the simulation.
 *                     */

    FairRootManager::Instance()->Register("MuFilterPoint", "MuFilter",
                                          fMuFilterPointCollection, kTRUE);
}

TClonesArray* MuFilter::GetCollection(Int_t iColl) const
{
    if (iColl == 0) { return fMuFilterPointCollection; }
    else { return NULL; }
}

void MuFilter::Reset()
{
    fMuFilterPointCollection->Clear();
}


MuFilterPoint* MuFilter::AddHit(Int_t trackID,Int_t detID,
                           TVector3 pos, TVector3 mom,
                           Double_t time, Double_t length,
                            Double_t eLoss, Int_t pdgCode)
{
    TClonesArray& clref = *fMuFilterPointCollection;
    Int_t size = clref.GetEntriesFast();
    return new(clref[size]) MuFilterPoint(trackID,detID, pos, mom,
                                        time, length, eLoss, pdgCode);
}
ClassImp(MuFilter)
