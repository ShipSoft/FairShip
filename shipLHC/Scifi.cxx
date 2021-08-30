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

void Scifi::SetMatParam(Double_t scifimat_width, Double_t scifimat_length, Double_t scifimat_z, Double_t epoxymat_z, Double_t scifimat_gap)
{   
    fWidthScifiMat = scifimat_width;  
    fLengthScifiMat = scifimat_length;
    fZScifiMat = scifimat_z;
    fZEpoxyMat = epoxymat_z;
    fGapScifiMat = scifimat_gap; //dead zone between mats
}

void Scifi::SetFiberParam(Double_t fiber_length, Double_t scintcore_rmax, Double_t clad1_rmax, Double_t clad2_rmax)
{

    fFiberLength = fiber_length;
    fScintCore_rmax = scintcore_rmax;   
    fClad1_rmin = fScintCore_rmax;
    fClad1_rmax = clad1_rmax;
    fClad2_rmin = clad1_rmax;
    fClad2_rmax = clad2_rmax;
}

void Scifi::SetFiberPosParam(Double_t horizontal_pitch, Double_t vertical_pitch, Double_t rowlong_offset, Double_t rowshort_offset)
{
    fHorPitch = horizontal_pitch;       
    fVertPitch= vertical_pitch;         
    fOffsetRowS = rowlong_offset;             
    fOffsetRowL= rowshort_offset;       
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

void Scifi::SetNFibers(Int_t nfibers_shortrow, Int_t nfibers_longrow, Int_t nfibers_z)
{
    fNFibers_Srow = nfibers_shortrow;  
    fNFibers_Lrow = nfibers_longrow;    
    fNFibers_z = nfibers_z;                 
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

void Scifi::SiPMParams(Double_t half_width, Double_t channel_width, Double_t charr_width, Double_t sipm_edge, Double_t charr_gap, Double_t simparr_width, Double_t sipm_diegap, Double_t nsipm_channels)
{  
    fHalfWidth =  half_width;                
    fWidthChannel = channel_width;           
    fCharr = charr_width;                    
    fEdge = sipm_edge;                      
    fCharrGap = charr_gap;                  			
    fSipmArray = simparr_width;            
    fBigGap = sipm_diegap;                 				
    fNSiPMChan = nsipm_channels;          
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
  InitMedium("CarbonComposite");
  TGeoMedium *CarbonComposite = gGeoManager->GetMedium("CarbonComposite");

  InitMedium("rohacell");
  TGeoMedium *rohacell = gGeoManager->GetMedium("rohacell");

  InitMedium("air");
  TGeoMedium *air = gGeoManager->GetMedium("air");

  InitMedium("Polycarbonate");
  TGeoMedium *PlasticBase = gGeoManager->GetMedium("Polycarbonate");
  
  InitMedium("Polystyrene");
  TGeoMedium *Polystyrene = gGeoManager->GetMedium("Polystyrene");

  InitMedium("PMMA");
  TGeoMedium *PMMA = gGeoManager->GetMedium("PMMA");

  InitMedium("PMMA2");
  TGeoMedium *PMMA2 = gGeoManager->GetMedium("PMMA2");
  
  InitMedium("Epoxy");
  TGeoMedium *Epoxy = gGeoManager->GetMedium("Epoxy");

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

  //Fiber volume that contains the scintillating core and double cladding
  TGeoVolumeAssembly *FiberVolume = new TGeoVolumeAssembly("FiberVolume");

  TGeoVolume *ScintCoreVol = gGeoManager->MakeTube("ScintCoreVol", Polystyrene, 0, fScintCore_rmax, fFiberLength/2); 
  TGeoVolume *Clad1Vol = gGeoManager->MakeTube("Clad1Vol", PMMA, fClad1_rmin, fClad1_rmax, fFiberLength/2); 
  TGeoVolume *Clad2Vol = gGeoManager->MakeTube("Clad2Vol", PMMA2, fClad2_rmin, fClad2_rmax, fFiberLength/2); 
  
  FiberVolume->AddNode(ScintCoreVol, 0);
  FiberVolume->AddNode(Clad1Vol, 0);
  FiberVolume->AddNode(Clad2Vol, 0);
  FiberVolume->SetVisDaughters(kFALSE);

  //Add SciFi fiber as sensitive unit
  AddSensitiveVolume(ScintCoreVol);

  //Fiber and plane rotations
  TGeoRotation *rothorfiber = new TGeoRotation("rothorfiber", 90, 90, 0);
  TGeoRotation *rotvertfiber = new TGeoRotation("rotvertfiber", 0, 90, 0);
  TGeoRotation *rot = new TGeoRotation("rot", 90, 180, 0);

  // DetID is of the form: 
  // first digit - station number
  // second digit - type of the plane: 0-horizontal fiber, 1-vertical fiber
  // third digit - mat number
  // fourth digit - row number (in Z direction)
  // last three digits - fiber number
  // e.g. DetID = 1021074 -> station 1, horizontal fiber plane, mat 2, row 1, fiber 74
  for (int istation = 0; istation < fNScifi; istation++){
    
    TGeoVolumeAssembly *ScifiVolume = new TGeoVolumeAssembly("ScifiVolume");
    volTarget->AddNode(ScifiVolume, 1e6*(istation+1), new TGeoTranslation(0, 0, fZOffset + istation*fSeparationBrick));
    
    TGeoVolumeAssembly *ScifiHorPlaneVol = new TGeoVolumeAssembly("ScifiHorPlaneVol");
    TGeoVolumeAssembly *ScifiVertPlaneVol = new TGeoVolumeAssembly("ScifiVertPlaneVol");

    //Adding the first half of the SciFi module that contains horizontal fibres
    ScifiVolume->AddNode(CarbonFiberVolume, 0, new TGeoTranslation(0, 0, fZCarbonFiber/2));
    ScifiVolume->AddNode(HoneycombVolume, 0, new TGeoTranslation(0, 0, fZCarbonFiber + fZHoneycomb/2));
    ScifiVolume->AddNode(CarbonFiberVolume, 1, new TGeoTranslation(0, 0, fZCarbonFiber + fZHoneycomb + fZCarbonFiber/2));
    ScifiVolume->AddNode(ScifiHorPlaneVol, 0, new TGeoTranslation(0, 0, 2*fZCarbonFiber + fZHoneycomb + fZEpoxyMat/2));
    ScifiVolume->AddNode(PlasticAirVolume, 0, new TGeoTranslation(0, 0, 2*fZCarbonFiber + fZHoneycomb + fZEpoxyMat+ fZPlastBar/2));
  
    //Adding the second half of the SciFi module that contains vertical fibres
    ScifiVolume->AddNode(PlasticAirVolume, 1, new TGeoCombiTrans("rottrans0", 0, 0, 2*fZCarbonFiber + fZHoneycomb + fZEpoxyMat + 3*fZPlastBar/2, rot));
    ScifiVolume->AddNode(ScifiVertPlaneVol, 0, new TGeoTranslation(0, 0, 2*fZCarbonFiber + fZHoneycomb + fZEpoxyMat + 2*fZPlastBar + fZEpoxyMat/2)); 
    ScifiVolume->AddNode(CarbonFiberVolume, 2, new TGeoTranslation(0, 0, 2*fZCarbonFiber + fZHoneycomb + fZEpoxyMat + 2*fZPlastBar + fZEpoxyMat +fZCarbonFiber/2));
    ScifiVolume->AddNode(HoneycombVolume, 1, new TGeoTranslation(0, 0, 3*fZCarbonFiber + fZHoneycomb + fZEpoxyMat + 2*fZPlastBar + fZEpoxyMat + fZHoneycomb/2));
    ScifiVolume->AddNode(CarbonFiberVolume, 3, new TGeoTranslation(0, 0, 3*fZCarbonFiber + 2*fZHoneycomb + fZEpoxyMat + 2*fZPlastBar + fZEpoxyMat + fZCarbonFiber/2));

    //Creating Scifi planes by appending fiber mats
    for (int imat = 0; imat < fNMats; imat++){
        
        //SciFi mats for X and Y fiber planes
        TGeoVolume *HorMatVolume = gGeoManager->MakeBox("HorMatVolume", Epoxy, fLengthScifiMat/2, fWidthScifiMat/2, fZEpoxyMat/2); 
        TGeoVolume *VertMatVolume = gGeoManager->MakeBox("VertMatVolume", Epoxy, fWidthScifiMat/2, fLengthScifiMat/2, fZEpoxyMat/2); 

        //Placing mats along Y 
        ScifiHorPlaneVol->AddNode(HorMatVolume, 1e6*(istation+1) + 1e4*(imat + 1), new TGeoTranslation(0, (imat-1)*(fWidthScifiMat+fGapScifiMat), 0));
        
        //Adding horizontal fibers
        for (int irow = 0; irow < fNFibers_z; irow++){
    
            if (irow%2 == 0){
                for (int ifiber = 0; ifiber < fNFibers_Srow; ifiber++){
                    TGeoCombiTrans *rottranshor0 = new TGeoCombiTrans("rottranshor0", 0, -fWidthScifiMat/2 + fOffsetRowS + ifiber*fHorPitch, -fZScifiMat/2 + fClad2_rmax/2 + irow*fVertPitch, rothorfiber);
                    HorMatVolume->AddNode(FiberVolume, 1e6*(istation+1) + 1e4*(imat + 1) + 1e3*(irow + 1) + ifiber + 1, rottranshor0);
                }
            }
            else{
                for (int ifiber = 0; ifiber < fNFibers_Lrow; ifiber++){
                    TGeoCombiTrans *rottranshor1 = new TGeoCombiTrans("rottranshor1", 0, -fWidthScifiMat/2 + fOffsetRowL + ifiber*fHorPitch, -fZScifiMat/2 + fClad2_rmax/2 + irow*fVertPitch, rothorfiber);
                    HorMatVolume->AddNode(FiberVolume, 1e6*(istation+1) + 1e4*(imat + 1) + 1e3*(irow + 1) + ifiber + 1, rottranshor1);
                }
            }
        }
        //Placing mats along X
        ScifiVertPlaneVol->AddNode(VertMatVolume, 1e6*(istation+1) + 1e5 + 1e4*(imat + 1), new TGeoTranslation((imat-1)*(fWidthScifiMat+fGapScifiMat), 0, 0));
        
        //Adding vertical fibers
        for (int irow = 0; irow < fNFibers_z; irow++){
            if (irow%2 == 0){
                for (int ifiber = 0; ifiber < fNFibers_Srow; ifiber++){
                    TGeoCombiTrans *rottransvert0 = new TGeoCombiTrans("rottransvert0", -fWidthScifiMat/2 + fOffsetRowS + ifiber*fHorPitch, 0, -fZScifiMat/2 + fClad2_rmax/2 + irow*fVertPitch, rotvertfiber);
                    VertMatVolume->AddNode(FiberVolume, 1e6*(istation+1) + 1e5 + 1e4*(imat + 1) + 1e3*(irow + 1) + ifiber + 1, rottransvert0);
                }
            }
            else{
                for (int ifiber = 0; ifiber < fNFibers_Lrow; ifiber++){
                    TGeoCombiTrans *rottransvert1 = new TGeoCombiTrans("rottransvert1", -fWidthScifiMat/2 + fOffsetRowL + ifiber*fHorPitch, 0, -fZScifiMat/2 + fClad2_rmax/2 + irow*fVertPitch, rotvertfiber);
                    VertMatVolume->AddNode(FiberVolume, 1e6*(istation+1) + 1e5 + 1e4*(imat + 1) + 1e3*(irow + 1) + ifiber + 1, rottransvert1);
                }
            }
        }
}}}

TGeoVolume* Scifi::SiPMOverlap()
{   
    //Contains all plane SiPMs, defined for horizontal fiber plane
    //To obtain SiPM map for vertical fiber plane rotate by 90 degrees around Z
    TGeoVolumeAssembly *SiPMmapVol = new TGeoVolumeAssembly("SiPMmapVol");

    TGeoVolume*ChannelVol = gGeoManager->MakeBox("ChannelVol", 0, fLengthScifiMat/2, fWidthChannel/2, fZEpoxyMat/2);

    //DetID for each channel:
    //first digit: SiPM number
    //last three digits: channel number (1-128)
    for (int isipms = 0; isipms < fNSiPMs; isipms++){

        TGeoVolumeAssembly *SiPMArrayVol = new TGeoVolumeAssembly("SiPMArrayVol");
        
        //Positioning SiPMs
        SiPMmapVol->AddNode(SiPMArrayVol, (isipms + 1)*1000, new TGeoTranslation(0, -fHalfWidth + fEdge + fSipmArray/2 + isipms*(fBigGap  + fSipmArray), 0));

        //Adding channels 1-64
        TGeoVolumeAssembly *SiPMCharrVol0 = new TGeoVolumeAssembly("SiPMCharrVol0");
        for (int ichannel = 0; ichannel < fNSiPMChan/2; ichannel++){
            SiPMCharrVol0->AddNode(ChannelVol, (isipms + 1)*1000 + ichannel + 1, new TGeoTranslation(0, - fCharr/2 + fWidthChannel/2 + ichannel*fWidthChannel, 0));
        }
        SiPMArrayVol->AddNode(SiPMCharrVol0, 0, new TGeoTranslation(0, -fSipmArray/2 + fCharr/2, 0));
        
        //Adding channels 65-128 (channels after die gap)
        TGeoVolumeAssembly *SiPMCharrVol1 = new TGeoVolumeAssembly("SiPMCharrVol1");
        for (int ichannel = 0; ichannel < fNSiPMChan/2; ichannel++){
            SiPMCharrVol1->AddNode(ChannelVol, (isipms + 1)*1000 + fNSiPMChan/2 + ichannel + 1, new TGeoTranslation(0, - fCharr/2 + fWidthChannel/2 + ichannel*fWidthChannel, 0));
        }
        SiPMArrayVol->AddNode(SiPMCharrVol1, 1, new TGeoTranslation(0, -fSipmArray/2 + fCharr + fCharrGap + fCharr/2, 0));
    }
    return SiPMmapVol;
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
		if (fELoss == 0. ) { return kFALSE; }
		fTrackID  = gMC->GetStack()->GetCurrentTrackNumber();
		TGeoNavigator* nav = gGeoManager->GetCurrentNavigator();
		TString  S    = TString(nav->GetPath());
		int k = 12 + S.Index("FiberVolume_");
		fVolumeID =  TString(S(k,7)).Atoi();
/* STMRFFF
First digit S: station # within the sub-detector
Second digit T: type of the plane: 0-horizontal fiber plane, 1-vertical fiber plane
Third digit M: determines the mat number
Fourth digit R: row number (in Z direction)
Last three digits F: fiber number
*/
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
