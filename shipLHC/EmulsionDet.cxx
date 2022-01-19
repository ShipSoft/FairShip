//
//  EmulsionDet.cxx
//  
//
//
//

#include "EmulsionDet.h"

#include "EmulsionDetPoint.h"

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
#include "TGeoCompositeShape.h"

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

#include "FairLogger.h"

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

EmulsionDet::EmulsionDet()
: FairDetector("EmulsionDet", "",kTRUE),
fTrackID(-1),
fVolumeID(-1),
fPos(),
fMom(),
fTime(-1.),
fLength(-1.),
fELoss(-1),
fEmulsionDetPointCollection(new TClonesArray("EmulsionDetPoint"))
{
}

EmulsionDet::EmulsionDet(const char* name, Bool_t Active,const char* Title)
: FairDetector(name, true, kEmulsionDet),
fTrackID(-1),
fVolumeID(-1),
fPos(),
fMom(),
fTime(-1.),
fLength(-1.),
fELoss(-1),
fEmulsionDetPointCollection(new TClonesArray("EmulsionDetPoint"))
{
}

EmulsionDet::~EmulsionDet()
{
    if (fEmulsionDetPointCollection) {
        fEmulsionDetPointCollection->Delete();
        delete fEmulsionDetPointCollection;
    }
}

void EmulsionDet::Initialize()
{
    FairDetector::Initialize();
}

// -----   Private method InitMedium
Int_t EmulsionDet::InitMedium(const char* name)
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

void EmulsionDet::DecodeBrickID(Int_t detID, Int_t &NWall, Int_t &NRow, Int_t &NColumn, Int_t &NPlate){

  NWall = detID/1E4;
  Int_t NTransverse = (detID - NWall*1E4)/1E3;
  switch (NTransverse){
    case (1):  
      NColumn = 1;
      NRow = 2;
      break;
      
    case (2):
      NColumn = 1;
      NRow = 1;
      break;
    
    case (3):
      NColumn = 2;
      NRow = 2;
      break;

    case (4):
      NColumn = 2;
      NRow = 1;
      break;
    }

  NPlate = detID - NWall*1E4 - NTransverse*1E3;
  

}

void EmulsionDet::ConstructGeometry()
{
	// configuration parameters
	fCenterZ        = conf_floats["EmulsionDet/zC"];
	XDimension = conf_floats["EmulsionDet/xdim"];
	YDimension = conf_floats["EmulsionDet/ydim"];
	ZDimension = conf_floats["EmulsionDet/zdim"];
	fNCol        = conf_ints["EmulsionDet/col"];
	fNRow     = conf_ints["EmulsionDet/row"];
	fNWall      = conf_ints["EmulsionDet/wall"];
	fNTarget = conf_ints["EmulsionDet/target"];
	WallXDim = conf_floats["EmulsionDet/WallXDim"];
	WallYDim = conf_floats["EmulsionDet/WallYDim"];
	WallZDim = conf_floats["EmulsionDet/WallZDim"];
	TotalWallZDim = conf_floats["EmulsionDet/TotalWallZDim"];
	WallZBorder_offset = conf_floats["EmulsionDet/WallZBorder_offset"];
	EmulsionThickness = conf_floats["EmulsionDet/EmTh"];
	EmulsionX = conf_floats["EmulsionDet/EmX"];
	EmulsionY = conf_floats["EmulsionDet/EmY"];
	PlasticBaseThickness = conf_floats["EmulsionDet/PBTh"];
	EmPlateWidth = conf_floats["EmulsionDet/EPlW"];
	PassiveThickness = conf_floats["EmulsionDet/PassiveTh"];
	AllPlateWidth = conf_floats["EmulsionDet/AllPW"];
	fPassiveOption = conf_ints["EmulsionDet/PassiveOption"];
	BrickPackageX = conf_floats["EmulsionDet/BrPackX"];
	BrickPackageY = conf_floats["EmulsionDet/BrPackY"];
	BrickPackageZ = conf_floats["EmulsionDet/BrPackZ"];
	BrickX = conf_floats["EmulsionDet/BrX"];
	BrickY = conf_floats["EmulsionDet/BrY"];
	BrickZ = conf_floats["EmulsionDet/BrZ"];
	number_of_plates = conf_ints["EmulsionDet/n_plates"];
	TTrackerZ = conf_floats["EmulsionDet/TTz"];
	ShiftX = conf_floats["EmulsionDet/ShiftX"];
	ShiftY = conf_floats["EmulsionDet/ShiftY"];

	TGeoVolume *top=gGeoManager->FindVolumeFast("Detector");
	if(!top)  LOG(ERROR) << "no Detector volume found " ;
	gGeoManager->SetVisLevel(10);

	LOG(INFO) << "fCenterZ:   "<<fCenterZ;
        LOG(INFO) << "    X: "<< XDimension<< "  "<< YDimension<<"   Z: "<<ZDimension;
	LOG(INFO) <<"  BrickX: "<< BrickX<<"  Y: "<< BrickY<< "  Z: "<< BrickZ;
	//Materials 
	InitMedium("vacuum");
	TGeoMedium *vacuum =gGeoManager->GetMedium("vacuum");
	
	InitMedium("air");
	TGeoMedium *air =gGeoManager->GetMedium("air");

	InitMedium("Aluminum");
	TGeoMedium *Al  = gGeoManager->GetMedium("Aluminum");

	InitMedium("PlasticBase");
	TGeoMedium *PBase =gGeoManager->GetMedium("PlasticBase");

	InitMedium("NuclearEmulsion");
	TGeoMedium *NEmu =gGeoManager->GetMedium("NuclearEmulsion");
	
	TGeoMaterial *NEmuMat = NEmu->GetMaterial(); //I need the materials to build the mixture
	TGeoMaterial *PBaseMat = PBase->GetMaterial();

	TGeoMixture * emufilmmixture = new TGeoMixture("EmulsionFilmMixture", 2.00); // two nuclear emulsions separated by the plastic base
	Double_t frac_emu = NEmuMat->GetDensity() * 2 * EmulsionThickness /(NEmuMat->GetDensity() * 2 * EmulsionThickness + PBaseMat->GetDensity() * PlasticBaseThickness);

	emufilmmixture->AddElement(NEmuMat,frac_emu);
	emufilmmixture->AddElement(PBaseMat,1. - frac_emu);

	TGeoMedium *Emufilm = new TGeoMedium("EmulsionFilm",100,emufilmmixture);

	InitMedium("tungstenalloySND");
	TGeoMedium *tungsten = gGeoManager->GetMedium("tungstenalloySND");


	Int_t NPlates = number_of_plates; //Number of doublets emulsion + Pb	


	//TGeoVolume *top = gGeoManager->MakeBox("Top",vacuum,10.,10.,10.);
	//gGeoManager->SetTopVolume(top);

	//Definition of the target box containing emulsion bricks + target trackers (TT) 
         TGeoVolumeAssembly *volTarget  = new TGeoVolumeAssembly("volTarget");

	//
	//  //Volumes definition
	//    //

	
	TGeoBBox *Walltot = new TGeoBBox("walltot",XDimension/2, YDimension/2, TotalWallZDim/2);
        TGeoBBox *Wallint = new TGeoBBox("wallint",WallXDim/2, WallYDim/2, WallZDim/2);
 
        TGeoTranslation * Wallborderpos = new TGeoTranslation("Walborderpos",0,0,WallZBorder_offset);
        Wallborderpos->RegisterYourself();

        TGeoCompositeShape *Wallborder = new TGeoCompositeShape("wallborder","walltot - (wallint:Walborderpos)");
        TGeoVolume *volWallborder = new TGeoVolume("volWallborder", Wallborder, Al);
        volWallborder->SetLineColor(kGray);

        TGeoVolume *volWall = new TGeoVolume("Wall",Wallint,air);
	
	//Rows
	TGeoBBox *Row = new TGeoBBox("row",WallXDim/2, BrickY/2, BrickZ/2);
        TGeoVolume *volRow = new TGeoVolume("Row",Row,air);

	//Bricks
	TGeoBBox *Brick = new TGeoBBox("brick", BrickX/2, BrickY/2, BrickZ/2);
	TGeoVolume *volBrick = new TGeoVolume("Brick",Brick,air);
	volBrick->SetLineColor(kCyan);
	volBrick->SetTransparency(1);

	TGeoBBox *Passive = new TGeoBBox("Passive", EmulsionX/2, EmulsionY/2, PassiveThickness/2);
	TGeoVolume *volPassive = new TGeoVolume("volPassive",Passive,tungsten);
	volPassive->SetTransparency(1);
	volPassive->SetLineColor(kGray);

	for(Int_t n=0; n<NPlates; n++)
	{
		volBrick->AddNode(volPassive, n, new TGeoTranslation(0,0,-BrickZ/2+ EmPlateWidth + PassiveThickness/2 + n*AllPlateWidth)); //LEAD
	}

	TGeoBBox *EmulsionFilm = new TGeoBBox("EmulsionFilm", EmulsionX/2, EmulsionY/2, EmPlateWidth/2);
	TGeoVolume *volEmulsionFilm = new TGeoVolume("Emulsion",EmulsionFilm,Emufilm); //TOP
	volEmulsionFilm->SetLineColor(kBlue);
	LOG(INFO) << "EmulsionDet : Passive option (0: all active, 1: all passive) set to " << fPassiveOption ;
	if (fPassiveOption == 0) AddSensitiveVolume(volEmulsionFilm);
	for(Int_t n=0; n<NPlates+1; n++)
	{
		volBrick->AddNode(volEmulsionFilm, n, new TGeoTranslation(0,0,-BrickZ/2+ EmPlateWidth/2 + n*AllPlateWidth));
	}

	volBrick->SetVisibility(kTRUE);

//alignment
	double dx_survey[fNWall] = {conf_floats["EmulsionDet/Xpos0"],conf_floats["EmulsionDet/Xpos1"],conf_floats["EmulsionDet/Xpos2"],conf_floats["EmulsionDet/Xpos3"],conf_floats["EmulsionDet/Xpos4"]};
	double dy_survey[fNWall] = {conf_floats["EmulsionDet/Ypos0"],conf_floats["EmulsionDet/Ypos1"],conf_floats["EmulsionDet/Ypos2"],conf_floats["EmulsionDet/Ypos3"],conf_floats["EmulsionDet/Ypos4"]};
	double dz_survey[fNWall] = {conf_floats["EmulsionDet/Zpos0"],conf_floats["EmulsionDet/Zpos1"],conf_floats["EmulsionDet/Zpos2"],conf_floats["EmulsionDet/Zpos3"],conf_floats["EmulsionDet/Zpos4"]};

 	top->AddNode(volTarget,1,new TGeoTranslation(0,0,0));

	//adding walls

        Double_t d_cl_z = - ZDimension/2;

	for(int l = 0; l < fNWall; l++)
	  {
		volTarget->AddNode(volWallborder,l,new TGeoTranslation(-dx_survey[l]-XDimension/2., dz_survey[l]+YDimension/2., dy_survey[l]+TotalWallZDim/2.)); //the survey points refer to the down-left corner
		volTarget->AddNode(volWall,l,new TGeoTranslation(-dx_survey[l]-XDimension/2., dz_survey[l]+YDimension/2., dy_survey[l]+TotalWallZDim/2.+WallZBorder_offset)); //the survey points refer to the down-left corner
		d_cl_z += BrickZ + TTrackerZ;
	  }

	//adding rows
	Double_t d_cl_y = -WallYDim/2;
       
        for(int k= 0; k< fNRow; k++)
	  {
	  volWall->AddNode(volRow,k,new TGeoTranslation(0, d_cl_y + BrickY/2,0));
        
	  // 2mm is the distance for the structure that holds the brick
	  d_cl_y += BrickY;
	  }

	//adding columns of bricks
	Double_t d_cl_x = -WallXDim/2;
	for(int j= 0; j < fNCol; j++)
	  {
	    volRow->AddNode(volBrick,j,new TGeoTranslation(d_cl_x+BrickX/2, 0, 0));
	    d_cl_x += BrickX;
	  }
}





Bool_t  EmulsionDet::ProcessHits(FairVolume* vol)
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
    
    // Create EmulsionDetPoint at exit of active volume
    if ( gMC->IsTrackExiting()    ||
        gMC->IsTrackStop()       ||
        gMC->IsTrackDisappeared()   ) {
        fTrackID  = gMC->GetStack()->GetCurrentTrackNumber();
	gMC->CurrentVolID(fVolumeID);

        //finding number of wall, row and column
        Int_t detID = fVolumeID;
        Int_t MaxLevel = gGeoManager->GetLevel();
        const Int_t MaxL = MaxLevel;
        //cout << "MaxLevel = " << MaxL << endl;
        //cout << gMC->CurrentVolPath()<< endl;
	

        Int_t motherV[MaxL];
        Int_t NPlate =0;
        const char *name;
	
        name = gMC->CurrentVolName();
        //cout << name << endl;
        NPlate = detID;
	
        Int_t  NWall = -2, NColumn =-2, NRow =-2;

        for(Int_t i = 0; i <= MaxL;i++)
	  {	 
	    gMC->CurrentVolOffID(i, motherV[i]);         
	    const char *mumname = gMC->CurrentVolOffName(i);                 
	    
	    if(strcmp(mumname, "Brick") == 0) NColumn = (1-motherV[i]); //0 or 1 (0 higher x, 1 lower x, x are negative, so higher x are closer to the beam)
	    if(strcmp(mumname, "Row") == 0) NRow = motherV[i]; // 0 or 1 (0 lower y, 1 higher y)
	    if(strcmp(mumname, "Wall") == 0) NWall = motherV[i]; //0,1,2,3 (increasing along the beam verse)
	    
	  }

        detID = (NWall+1)*1E4+(NRow*2+NColumn+1)*1E3+(NPlate+1);
        fVolumeID = detID;
	//found number of row, column and wall
        //if (NColumn > 2 || NRow > 2 || NWall > 5) cout<<"Debug test for detID "<<detID<<" is "<<NColumn<<" "<<NRow<<" "<<NWall<<" "<<NPlate<<endl;
	if (fELoss == 0. ) { return kFALSE; }
        TParticle* p=gMC->GetStack()->GetCurrentTrack();
	Int_t pdgCode = p->GetPdgCode();
	
        TLorentzVector Pos; 
        gMC->TrackPosition(Pos); 
        Double_t xmean = (fPos.X()+Pos.X())/2. ;      
        Double_t ymean = (fPos.Y()+Pos.Y())/2. ;      
        Double_t zmean = (fPos.Z()+Pos.Z())/2. ;     
        
        TLorentzVector Mom;
        gMC->TrackMomentum(Mom);
        AddHit(fTrackID, fVolumeID, TVector3(xmean, ymean,  zmean),
           TVector3(fMom.Px(), fMom.Py(), fMom.Pz()), fTime, fLength,
           fELoss,pdgCode,TVector3(Pos.X(), Pos.Y(), Pos.Z()),TVector3(Mom.Px(), Mom.Py(), Mom.Pz()) );
	
        // Increment number of muon det points in TParticle
        ShipStack* stack = (ShipStack*) gMC->GetStack();
        stack->AddPoint(kEmulsionDet);
    }
    
    return kTRUE;
}



void EmulsionDet::EndOfEvent()
{
    fEmulsionDetPointCollection->Clear();
}


void EmulsionDet::Register()
{
    
    /** This will create a branch in the output tree called
     TargetPoint, setting the last parameter to kFALSE means:
     this collection will not be written to the file, it will exist
     only during the simulation.
     */
    
    FairRootManager::Instance()->Register("EmulsionDetPoint", "EmulsionDet",
                                          fEmulsionDetPointCollection, kTRUE);
}

TClonesArray* EmulsionDet::GetCollection(Int_t iColl) const
{
    if (iColl == 0) { return fEmulsionDetPointCollection; }
    else { return NULL; }
}

void EmulsionDet::Reset()
{
    fEmulsionDetPointCollection->Clear();
}


EmulsionDetPoint* EmulsionDet::AddHit(Int_t trackID,Int_t detID,
                           TVector3 pos, TVector3 mom,
                           Double_t time, Double_t length,
			    Double_t eLoss, Int_t pdgCode,TVector3 Lpos, TVector3 Lmom)
{
    TClonesArray& clref = *fEmulsionDetPointCollection;
    Int_t size = clref.GetEntriesFast();
    return new(clref[size]) EmulsionDetPoint(trackID,detID, pos, mom,
					time, length, eLoss, pdgCode,Lpos,Lmom);
}
ClassImp(EmulsionDet)
