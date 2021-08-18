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
#include <cstring>

using std::cout;
using std::endl;
using std::to_string;
using std::string;
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

void MuFilter::SetVetoShift(Double_t x, Double_t y)
{
  fVetoShiftX = x;
  fVetoShiftY = y;
}

void MuFilter::SetVetoPlanesDimensions(Double_t x, Double_t y, Double_t z)
{
  fVetoPlaneX = x;
  fVetoPlaneY = y;
  fVetoPlaneZ = z;
}

void MuFilter::SetVetoBarsDimensions(Double_t x, Double_t y, Double_t z)
{
  fVetoBarX = x;
  fVetoBarY = y;
  fVetoBarZ = z;
}

void MuFilter::SetVetoCenterPosition(Double_t z)
{
  fVetoCenterZ = z;
}

void MuFilter::SetNVetoPlanes(Int_t n)
{
  fNVetoPlanes = n;
}

void MuFilter::SetNVetoBars(Int_t n)
{
  fNVetoBars = n;
}

void MuFilter::SetVetoPlaneShiftY(Double_t y)
{
  fVetoPlaneShiftY = y;
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

void MuFilter::SetDS4ZGap(Double_t z)
{
	fDS4ZGap = z;
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

	//Definition of the box containing veto planes
	TGeoVolumeAssembly *volVeto = new TGeoVolumeAssembly("volVeto");
	
	//Veto Planes
	TGeoBBox *VetoPlane = new TGeoBBox("VetoPlane",fVetoPlaneX/2., fVetoPlaneY/2., fVetoPlaneZ/2.);
	// TGeoVolume *volVetoPlane = new TGeoVolume("volVetoPlane",VetoPlane,air);

	//Veto bars
	TGeoBBox *VetoBar = new TGeoBBox("VetoBar",fVetoBarX/2., fVetoBarY/2., fVetoBarZ/2.);
	TGeoVolume *volVetoBar = new TGeoVolume("volVetoBar",VetoBar,Scint);

	volVetoBar->SetLineColor(kBlue+2);
	AddSensitiveVolume(volVetoBar);

	//adding mother volume
	top->AddNode(volVeto, 1, new TGeoTranslation(fVetoShiftX, fVetoShiftY,fVetoCenterZ));

	//adding veto planes
	TGeoVolume* volVetoPlane;
	Double_t startZ = -(fNVetoPlanes * fVetoPlaneZ)/2.;
	for (int iplane; iplane < fNVetoPlanes; iplane++){
	  
      string name = "volVetoPlane_"+to_string(iplane);
	  volVetoPlane = new TGeoVolume(name.c_str(), VetoPlane, air);
	  volVetoPlane->SetLineColor(kGray);
	  volVeto->AddNode(volVetoPlane,iplane, new TGeoTranslation(0,-fVetoPlaneShiftY/2. + iplane * fVetoPlaneShiftY, startZ + fVetoPlaneZ/2. + iplane * fVetoPlaneZ));

	  	//adding veto bars
	  for (int ibar=0; ibar < fNVetoBars; ibar++){

	  	Double_t dy_vetobar = -fVetoPlaneY/2. + fVetoBarY/2 + ibar * fVetoBarY;
	  	TGeoTranslation* vetobar_trans = new TGeoTranslation(0, dy_vetobar, 0);
	    volVetoPlane->AddNode(volVetoBar, 1e+4+iplane*1e+3+ibar, vetobar_trans);							 
		}
	}
	
	//*****************************************UPSTREAM SECTION*********************************//

		//Definition of the box containing Fe Blocks + Timing Detector planes 
	TGeoVolumeAssembly *volMuFilter = new TGeoVolumeAssembly("volMuFilter");

	//Iron blocks volume definition
	TGeoBBox *FeBlockBox = new TGeoBBox("FeBlockBox",fFeBlockX/2, fFeBlockY/2, fFeBlockZ/2);
	TGeoVolume *volFeBlock = new TGeoVolume("volFeBlock",FeBlockBox,Fe);
	volFeBlock->SetLineColor(19);

	top->AddNode(volMuFilter,1,new TGeoTranslation(fShiftX,fShiftY,fCenterZ));

	Double_t dy = 0;
	Double_t dz = 0;
	//Upstream Detector planes definition
	TGeoBBox *UpstreamDetBox = new TGeoBBox("UpstreamDetBox",fUpstreamDetX/2,fUpstreamDetY/2,fUpstreamDetZ/2);
//	TGeoVolume *volUpstreamDet = new TGeoVolume("volUpstreamDet",UpstreamDetBox,air);

	// create pointer for upstream plane to be re-used
	TGeoVolume* volUpstreamDet;

	//adding staggered bars, first part, only 11 bars, (single stations, readout on both ends)
	TGeoBBox *MuUpstreamBar = new TGeoBBox("MuUpstreamBar",fUpstreamBarX/2, fUpstreamBarY/2, fUpstreamBarZ/2);
	TGeoVolume *volMuUpstreamBar = new TGeoVolume("volMuUpstreamBar",MuUpstreamBar,Scint);
	volMuUpstreamBar->SetLineColor(kBlue+2);
	AddSensitiveVolume(volMuUpstreamBar);

	for(Int_t l=0; l<fNUpstreamPlanes; l++)
	{
	  string name = "volMuUpstreamDet_"+std::to_string(l);
	  volUpstreamDet = new TGeoVolume(name.c_str(), UpstreamDetBox, air);
	  volUpstreamDet->SetLineColor(kRed+2);
	  dz = (fFeBlockZ + fUpstreamDetZ)*l;
	  dy = dz * TMath::Tan(TMath::DegToRad() * fSlope);
	  //last upstream station does not follow slope, start of support. Same dy is used for downstream planes
	  if (l == fNUpstreamPlanes - 1) dy = fShiftYEnd - fShiftY;

	  // Double check all these distances
	  volMuFilter->AddNode(volFeBlock,l,new TGeoTranslation(0,fMuFilterY/2-fFeBlockY/2+dy,-fMuFilterZ/2+fFeBlockZ/2+dz));
	  volMuFilter->AddNode(volUpstreamDet,fNVetoPlanes+l,new TGeoTranslation(0,fMuFilterY/2-fFeBlockY/2+dy,-fMuFilterZ/2+fFeBlockZ+fUpstreamDetZ/2+dz));
	  dz+=fFeBlockZ+fUpstreamDetZ;

	  for (Int_t ibar = 0; ibar < fNUpstreamBars; ibar++){
	  
	    Double_t dy_bar = -fUpstreamDetY/2 + fUpstreamBarY/2. + fUpstreamBarY*ibar; 
	    TGeoTranslation *yztrans = new TGeoTranslation(0,dy_bar,0);
	    volUpstreamDet->AddNode(volMuUpstreamBar,2e+4+l*1e+3+ibar,yztrans);
			   }

	}
	           

	//*************************************DOWNSTREAM (high granularity) SECTION*****************//

    // first loop, adding detector main boxes
	TGeoVolume* volDownstreamDet;

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

	for(Int_t l=0; l<fNDownstreamPlanes; l++)
	{
	  string name = "volMuDownstreamDet_"+std::to_string(l);
	  volDownstreamDet = new TGeoVolumeAssembly(name.c_str());
	  volDownstreamDet->SetLineColor(kRed+2);
	  volMuFilter->AddNode(volDownstreamDet,l+fNUpstreamPlanes+fNVetoPlanes, new TGeoTranslation(0,fMuFilterY/2-fFeBlockY/2+dy,-fMuFilterZ/2+fFeBlockZ+fDownstreamDetZ/2+dz));
	  if (l<fNDownstreamPlanes-1){
		volMuFilter->AddNode(volFeBlock,l+fNUpstreamPlanes+fNVetoPlanes, new TGeoTranslation(0,fMuFilterY/2-fFeBlockY/2+dy,-fMuFilterZ/2+fFeBlockZ/2+dz));}
	  if (l<fNDownstreamPlanes-2){dz+=fFeBlockZ+fDownstreamDetZ;}
	  else{dz+= fDS4ZGap+fDownstreamDetZ/2;}

	//second loop, adding bars within each detector box
	  if (l!=fNDownstreamPlanes-1) {
		for (Int_t ibar = 0; ibar < fNDownstreamBars; ibar++){
	                 //adding horizontal bars for y
			Double_t dy_bar = -fDownstreamDetY/2 + fDownstreamBarY/2. + fDownstreamBarY*ibar; // so just fDownstreamBarY*ibar?
		    	Double_t dz_bar_hor = -fDownstreamDetZ/2. + fDownstreamBarZ/2.;
		    	TGeoTranslation *yztrans = new TGeoTranslation(0,dy_bar,dz_bar_hor);
		    	volDownstreamDet->AddNode(volMuDownstreamBar_hor,3e+4+l*1e+3+ibar,yztrans);
		}
	  }
	    //adding vertical bars for x
	  for (Int_t i_vbar = 0; i_vbar<fNDownstreamBars; i_vbar++) {
		Double_t dx_bar =  fDownstreamDetX/2 - fDownstreamBarX_ver/2. - fDownstreamBarX_ver*i_vbar; //they do not cover all the x region, but only 60 x 60.
		Double_t dz_bar_ver = -fDownstreamDetZ/2. + 2*fDownstreamBarZ + fDownstreamBarZ/2.;
		TGeoTranslation *xztrans = new TGeoTranslation(dx_bar,0,dz_bar_ver);
		Int_t i_vbar_rev = fNDownstreamBars-1-i_vbar;
		volDownstreamDet->AddNode(volMuDownstreamBar_ver,3e+4+l*1e+3+i_vbar_rev+60,xztrans);   // I added a 60 here to make each horizontal + vertical
			// sub-plane contain bars given detIDs as one plane. So the first bar in the vert. sub plane is the 60th etc. 		  
		}
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
		gMC->CurrentVolID(fVolumeID);

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

void MuFilter::GetPosition(Int_t fDetectorID, TVector3& vLeft, TVector3& vRight) 
{

  int subsystem     = floor(fDetectorID/10000);
  int plane                = floor(fDetectorID/1000) - 10*subsystem;
  int bar_number = fDetectorID%1000;

  TString path = "/cave_1/";
  TString barName;

  switch(subsystem) {
  
  case 1: 
      path+="volVeto_1/volVetoPlane_"+std::to_string(plane)+"_"+std::to_string(plane);
      barName = "/volVetoBar_";
      break;
  case 2: 
      path+="volMuFilter_1/volMuUpstreamDet_"+std::to_string(plane)+"_"+std::to_string(plane+2);
      barName = "/volMuUpstreamBar_";
      break;
  case 3: 
      path+="volMuFilter_1/volMuDownstreamDet_"+std::to_string(plane)+"_"+std::to_string(plane+5);
      barName = "/volMuDownstreamBar_";
      if (bar_number<60){barName+="hor_";}
      else{barName+="ver_";}
      break;
  }

  path += barName+std::to_string(fDetectorID);

  TGeoNavigator* nav = gGeoManager->GetCurrentNavigator();
  nav->cd(path);
  LOG(DEBUG) <<path<<" "<<fDetectorID<<" "<<subsystem<<" "<<bar_number;
  TGeoNode* W = nav->GetCurrentNode();
  TGeoBBox* S = dynamic_cast<TGeoBBox*>(W->GetVolume()->GetShape());

  if (subsystem == 3 and bar_number >59){  // vertical bars
      Double_t top[3] = {0,S->GetDY(), 0};
      Double_t bot[3] = {0,-S->GetDY(),0};
      Double_t Gtop[3],Gbot[3];
      nav->LocalToMaster(top, Gtop);   nav->LocalToMaster(bot, Gbot);
      vLeft.SetXYZ(Gtop[0],Gtop[1],Gtop[2]);
      vRight.SetXYZ(Gbot[0],Gbot[1],Gbot[2]);
    }
    else {     // horizontal bars
      Double_t posXend[3] = {S->GetDX(),0,0};
      Double_t negXend[3] = {-S->GetDX(),0,0};
      Double_t GposXend[3],GnegXend[3];
      nav->LocalToMaster(posXend, GposXend);   nav->LocalToMaster(negXend, GnegXend);
      vLeft.SetXYZ(GposXend[0],GposXend[1],GposXend[2]);
      vRight.SetXYZ(GnegXend[0],GnegXend[1],GnegXend[2]);
    }
}

   Int_t MuFilter::GetnSiPMs(Int_t detID){
       int subsystem     = floor(detID/10000);
       return nSiPMs[subsystem-1];
   }
   Int_t MuFilter::GetnSides(Int_t detID){
       int subsystem     = floor(detID/10000);
       return nSides[subsystem-1];
  }


ClassImp(MuFilter)
