//
//  Target.cxx
//  
//
//  Created by Annarita Buonaura on 17/01/15.
//
//

#include "Target.h"

#include "TargetPoint.h"

#include "TGeoManager.h"
#include "FairRun.h"                    // for FairRun
#include "FairRuntimeDb.h"              // for FairRuntimeDb
#include "Riosfwd.h"                    // for ostream
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
#include "EmulsionMagnet.h"

#include "TGeoUniformMagField.h"
#include "TVector3.h"

#include <stddef.h>                     // for NULL
#include <iostream>                     // for operator<<, basic_ostream,etc
#include <string.h>

using std::cout;
using std::endl;

using namespace ShipUnit;

Target::Target()
: FairDetector("Target", "",kTRUE),
  fTrackID(-1),
fVolumeID(-1),
fPos(),
fMom(),
fTime(-1.),
fLength(-1.),
fELoss(-1),
fTargetPointCollection(new TClonesArray("TargetPoint"))
{
}

Target::Target(const char* name, const Double_t Ydist, Bool_t Active,const char* Title)
: FairDetector(name, true, ktauTarget),
  fTrackID(-1),
fVolumeID(-1),
fPos(),
fMom(),
fTime(-1.),
fLength(-1.),
fELoss(-1),
fTargetPointCollection(new TClonesArray("TargetPoint"))
{
    Ydistance = Ydist;
}

Target::~Target()
{
    if (fTargetPointCollection) {
        fTargetPointCollection->Delete();
        delete fTargetPointCollection;
    }
}

void Target::Initialize()
{
    FairDetector::Initialize();
}

// -----   Private method InitMedium
Int_t Target::InitMedium(const char* name)
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

void Target::SetDetectorDesign(Int_t Design)
{
  fDesign = Design;
  Info("SetDetectorDesign"," to %i", fDesign);
}

void Target::SetNumberBricks(Double_t col, Double_t row, Double_t wall)
{
  fNCol = col;
  fNRow = row;
  fNWall = wall; 
}

void Target::SetDetectorDimension(Double_t xdim, Double_t ydim, Double_t zdim)
{
    XDimension = xdim;
    YDimension = ydim;
    ZDimension = zdim;
}

void Target::SetEmulsionParam(Double_t EmTh, Double_t EmX, Double_t EmY, Double_t PBTh, Double_t EPlW,Double_t LeadTh, Double_t AllPW)
{
    EmulsionThickness = EmTh;
    EmulsionX = EmX;
    EmulsionY = EmY;
    PlasticBaseThickness = PBTh;
    EmPlateWidth = EPlW;
    LeadThickness = LeadTh;
    AllPlateWidth = AllPW;
}


void Target::SetBrickParam(Double_t BrX, Double_t BrY, Double_t BrZ, Double_t BrPackX, Double_t BrPackY, Double_t BrPackZ)
{
  BrickPackageX = BrPackX;
  BrickPackageY = BrPackY;
  BrickPackageZ = BrPackZ;
  BrickX = BrX;
  BrickY = BrY;
  BrickZ = BrZ;
}

void Target::SetCESParam(Double_t RohG, Double_t LayerCESW,Double_t CESW, Double_t CESPack)
{
  CESPackageZ = CESPack;
    LayerCESWidth = LayerCESW;
    RohacellGap = RohG;
    CESWidth = CESW;
}

void Target::SetCellParam(Double_t CellW)
{
    CellWidth = CellW;
}

void Target::SetTTzdimension(Double_t TTZ)
{
    TTrackerZ = TTZ;
}

void Target::SetConfiguration(Int_t config)
{
  fMagnetConfig=config;
}

void Target::SetMagnetHeight(Double_t Y)
{
  fMagnetY=Y;
}

void Target::SetColumnHeight(Double_t Y)
{
  fColumnY=Y;
}

void Target::SetBaseHeight(Double_t Y)
{
  fBaseY=Y;
}

void Target::SetCoilUpHeight(Double_t H1)
{
  fCoilH1=H1;
}

void Target::SetCoilDownHeight(Double_t H2)
{
  fCoilH2=H2;
}

void Target::SetMagneticField(Double_t B)
{
  fField = B;
}

void Target::ConstructGeometry()
{
  // cout << "Design = " << fDesign << endl;
    TGeoVolume *top=gGeoManager->GetTopVolume();
    
    InitMedium("vacuum");
    TGeoMedium *vacuum =gGeoManager->GetMedium("vacuum");
    
    InitMedium("iron");
    TGeoMedium *Fe =gGeoManager->GetMedium("iron");
    
    InitMedium("CoilAluminium");
    TGeoMedium *Al  = gGeoManager->GetMedium("CoilAluminium");
    
    InitMedium("CoilCopper");
    TGeoMedium *Cu  = gGeoManager->GetMedium("CoilCopper");
    
    InitMedium("NuclearEmulsion");
    TGeoMedium *NEmu =gGeoManager->GetMedium("NuclearEmulsion");
    
    InitMedium("PlasticBase");
    TGeoMedium *PBase =gGeoManager->GetMedium("PlasticBase");
    
    InitMedium("lead");
    TGeoMedium *lead = gGeoManager->GetMedium("lead");
    
    InitMedium("rohacell");
    TGeoMedium *rohacell = gGeoManager->GetMedium("rohacell");

    TGeoVolume *MagnetVol;
    // gGeoManager->SetVisLevel(6);
    
 
   
    TGeoUniformMagField *magField2 = new TGeoUniformMagField(); //magnetic field in target
    //cout << fMagnetConfig<<endl;
    if(fMagnetConfig==0) //NEW
      {
	magField2->SetFieldValue(fField,0,0.);
	MagnetVol=gGeoManager->GetVolume("Davide");
      }
    if(fMagnetConfig==1) //TP
      {
	MagnetVol=gGeoManager->GetVolume("Goliath");
	magField2->SetFieldValue(0.,fField,0.);
      }
    //cout<< fNCol<<"  "<< fNRow<<"  " << fNWall<< endl;
    
    Int_t NPlates = 56; //Number of doublets emulsion + Pb
    Int_t NRohacellGap = 2;
    

    /*cout << "*******************************************" << endl;
    cout << "Layer CES Width = " << LayerCESWidth << endl;
    cout << "CES Width = " << CESWidth << endl;
    cout << "Cell Width = " << CellWidth << endl;
    cout << "*******************************************" << endl;
    */
    
   

    TGeoBBox *TargetBox = new TGeoBBox("TargetBox",XDimension/2, YDimension/2, ZDimension/2);
    TGeoVolume *volTarget = new TGeoVolume("volTarget",TargetBox,vacuum);
    volTarget->SetField(magField2);
    volTarget->SetVisibility(1);
    volTarget->SetVisDaughters(1);
    if(fMagnetConfig==1) //TP
      MagnetVol->AddNode(volTarget,1,new TGeoTranslation(0,-fMagnetY/2+fColumnY+fCoilH2+YDimension/2,0));
    if(fMagnetConfig==0) //NEW
      MagnetVol->AddNode(volTarget,1,new TGeoTranslation(0,-fMagnetY/2+fColumnY+YDimension/2,0));

    
    //
    //Volumes definition
    //

    if(fDesign == 1)
      {    
       	//cout<<"Here"<<endl;
	//Cell = brick + CES
	TGeoBBox *Cell = new TGeoBBox("cell", BrickX/2, BrickY/2, CellWidth/2);
	TGeoVolume *volCell = new TGeoVolume("Cell",Cell,vacuum);

	//Brick
	TGeoBBox *Brick = new TGeoBBox("brick", BrickX/2, BrickY/2, BrickZ/2);
	TGeoVolume *volBrick = new TGeoVolume("Brick",Brick,vacuum);
	volBrick->SetLineColor(kCyan);
	volBrick->SetTransparency(1);
	
	TGeoBBox *EmulsionFilm = new TGeoBBox("EmulsionFilm", EmulsionX/2, EmulsionY/2, EmulsionThickness/2);
	TGeoVolume *volEmulsionFilm = new TGeoVolume("Emulsion",EmulsionFilm,NEmu); //TOP
	TGeoVolume *volEmulsionFilm2 = new TGeoVolume("Emulsion2",EmulsionFilm,NEmu); //BOTTOM
	volEmulsionFilm->SetLineColor(kBlue);
	volEmulsionFilm2->SetLineColor(kBlue);
	AddSensitiveVolume(volEmulsionFilm);
	AddSensitiveVolume(volEmulsionFilm2);
	
	TGeoBBox *PlBase = new TGeoBBox("PlBase", EmulsionX/2, EmulsionY/2, PlasticBaseThickness/2);
	TGeoVolume *volPlBase = new TGeoVolume("PlasticBase",PlBase,PBase);
	volPlBase->SetLineColor(kYellow-4);
	
	TGeoBBox *Lead = new TGeoBBox("Pb", EmulsionX/2, EmulsionY/2, LeadThickness/2);
	TGeoVolume *volLead = new TGeoVolume("Lead",Lead,lead);
	volLead->SetTransparency(1);
	volLead->SetLineColor(kGray);
	//volLead->SetField(magField2);
	
	
	
	for(Int_t n=0; n<NPlates+1; n++)
	  {
	    volBrick->AddNode(volEmulsionFilm2, n, new TGeoTranslation(0,0,-BrickZ/2+BrickPackageZ/2+ EmulsionThickness/2 + n*AllPlateWidth)); //BOTTOM
	    volBrick->AddNode(volEmulsionFilm, n, new TGeoTranslation(0,0,-BrickZ/2+BrickPackageZ/2+3*EmulsionThickness/2+PlasticBaseThickness+n*AllPlateWidth)); //TOP
	    volBrick->AddNode(volPlBase, n, new TGeoTranslation(0,0,-BrickZ/2+BrickPackageZ/2+EmulsionThickness+PlasticBaseThickness/2+n*AllPlateWidth)); //PLASTIC BASE
	  }
	for(Int_t n=0; n<NPlates; n++)
	  {
	    volBrick->AddNode(volLead, n, new TGeoTranslation(0,0,-BrickZ/2+BrickPackageZ/2+ EmPlateWidth + LeadThickness/2 + n*AllPlateWidth)); //LEAD
	  }
	
	volBrick->SetVisibility(kTRUE);
	
	//CES
	
	TGeoBBox *CES = new TGeoBBox("ces", EmulsionX/2, EmulsionY/2, CESWidth/2);
	TGeoVolume *volCES = new TGeoVolume("CES", CES, vacuum);
	volCES->SetTransparency(5);
	volCES->SetLineColor(kYellow-10);
	volCES->SetVisibility(kTRUE);
        
	TGeoBBox *RohGap = new TGeoBBox("RohGap", EmulsionX/2, EmulsionY/2, RohacellGap/2);
	TGeoVolume *volRohGap = new TGeoVolume("RohacellGap",RohGap,rohacell);
	volRohGap->SetTransparency(1);
	volRohGap->SetLineColor(kYellow);
	
	
	TGeoBBox *EmulsionFilmCES = new TGeoBBox("EmulsionFilmCES", EmulsionX/2, EmulsionY/2, EmulsionThickness/2);
	TGeoVolume *volEmulsionFilmCES = new TGeoVolume("EmulsionCES",EmulsionFilmCES,NEmu); //TOP
	TGeoVolume *volEmulsionFilm2CES = new TGeoVolume("Emulsion2CES",EmulsionFilmCES,NEmu); //BOTTOM
	volEmulsionFilmCES->SetLineColor(kBlue);
	volEmulsionFilm2CES->SetLineColor(kBlue);
	AddSensitiveVolume(volEmulsionFilmCES);
	AddSensitiveVolume(volEmulsionFilm2CES);
	
	TGeoBBox *PlBaseCES = new TGeoBBox("PlBaseCES", EmulsionX/2, EmulsionY/2, PlasticBaseThickness/2);
	TGeoVolume *volPlBaseCES = new TGeoVolume("PlasticBaseCES",PlBaseCES,PBase);
	volPlBaseCES->SetLineColor(kYellow);
	
	for(Int_t n=0; n<NRohacellGap+1;n++)
	  {
	    volCES->AddNode(volEmulsionFilm2CES,n, new TGeoTranslation(0,0,-CESWidth/2+CESPackageZ/2+EmulsionThickness/2+n*LayerCESWidth)); //BOTTOM
	    volCES->AddNode(volEmulsionFilmCES, n, new TGeoTranslation(0,0,-CESWidth/2+CESPackageZ/2+3*EmulsionThickness/2+PlasticBaseThickness+n*LayerCESWidth)); //TOP
	    volCES->AddNode(volPlBaseCES, n, new TGeoTranslation(0,0,-CESWidth/2+CESPackageZ/2+EmulsionThickness+PlasticBaseThickness/2+n*LayerCESWidth)); //PLASTIC BASE
	    //	if(n == 2)
	    // cout << "-CESWidth/2+3*EmulsionThickness/2+PlasticBaseThickness+n*LayerCESWidth = " << -CESWidth/2+3*EmulsionThickness/2+PlasticBaseThickness+n*LayerCESWidth << endl;
	  }
	for(Int_t n=0; n<NRohacellGap; n++)
	  {
	    volCES->AddNode(volRohGap, n, new TGeoTranslation(0,0,-CESWidth/2 +CESPackageZ/2+  EmPlateWidth + RohacellGap/2 + n*LayerCESWidth)); //ROHACELL
	  }

	volCell->AddNode(volBrick,1,new TGeoTranslation(0,0,-CellWidth/2 + BrickZ/2));
	volCell->AddNode(volCES,1,new TGeoTranslation(0,0,-CellWidth/2 + BrickZ + CESWidth/2));
    
TGeoBBox *Row = new TGeoBBox("row",XDimension/2, BrickY/2, CellWidth/2);
    TGeoVolume *volRow = new TGeoVolume("Row",Row,vacuum);
    volRow->SetLineColor(20);
    
    Double_t d_cl_x = -XDimension/2;
    for(int j= 0; j < fNCol; j++)
    {
        volRow->AddNode(volCell,j,new TGeoTranslation(d_cl_x+BrickX/2, 0, 0));
        d_cl_x += BrickX;
    }

    TGeoBBox *Wall = new TGeoBBox("wall",XDimension/2, YDimension/2, CellWidth/2);
    TGeoVolume *volWall = new TGeoVolume("Wall",Wall,vacuum);
    
    Double_t d_cl_y = -YDimension/2;
    for(int k= 0; k< fNRow; k++)
    {
        volWall->AddNode(volRow,k,new TGeoTranslation(0, d_cl_y + BrickY/2, 0));
        
        // 2mm is the distance for the structure that holds the brick
        d_cl_y += BrickY + Ydistance;
    }
    
    //Columns
       
    Double_t d_cl_z = - ZDimension/2 + TTrackerZ;
    Double_t d_tt = -ZDimension/2 + TTrackerZ/2;

    for(int l = 0; l < fNWall; l++)
    {
        volTarget->AddNode(volWall,l,new TGeoTranslation(0, 0, d_cl_z +CellWidth/2));
        
        //6 cm is the distance between 2 columns of consecutive Target for TT placement
        d_cl_z += CellWidth + TTrackerZ;
    }
      }

    if(fDesign == 2)
      {
	//cout<<"Here"<<endl;
	
    	//Cell = brick + CES
	TGeoBBox *Cell = new TGeoBBox("cell", BrickX/2, BrickY/2, CellWidth/2);
	TGeoVolume *volCell = new TGeoVolume("Cell",Cell,vacuum);

	TGeoBBox *Brick = new TGeoBBox("brick", BrickX/2, BrickY/2, BrickZ/2);
	TGeoVolume *volBrick = new TGeoVolume("Brick",Brick,lead);
	volBrick->SetLineColor(kCyan);
	volBrick->SetTransparency(1);
	volBrick->SetVisibility(kTRUE);

	TGeoBBox *CES = new TGeoBBox("ces", EmulsionX/2, EmulsionY/2, CESWidth/2);
	TGeoVolume *volCES = new TGeoVolume("CES", CES, rohacell);
	volCES->SetTransparency(5);
	volCES->SetLineColor(kYellow-10);
	volCES->SetVisibility(kTRUE);

	volCell->AddNode(volBrick,1,new TGeoTranslation(0,0,-CellWidth/2 + BrickZ/2));
	volCell->AddNode(volCES,1,new TGeoTranslation(0,0,-CellWidth/2 + BrickZ + CESWidth/2));

	TGeoBBox *Row = new TGeoBBox("row",XDimension/2, BrickY/2, CellWidth/2);
	TGeoVolume *volRow = new TGeoVolume("Row",Row,vacuum);
	volRow->SetLineColor(20);
	
	Double_t d_cl_x = -XDimension/2;
	for(int j= 0; j < fNCol; j++)
	  {
	    volRow->AddNode(volCell,j,new TGeoTranslation(d_cl_x+BrickX/2, 0, 0));
	    d_cl_x += BrickX;
	  }
	
	TGeoBBox *Wall = new TGeoBBox("wall",XDimension/2, YDimension/2, CellWidth/2);
	TGeoVolume *volWall = new TGeoVolume("Wall",Wall,vacuum);
	volWall->SetLineColor(kGray);	
	volWall->SetVisibility(1);
	volWall->SetVisDaughters(1);
	Double_t d_cl_y = -YDimension/2;
	for(int k= 0; k< fNRow; k++)
	  {
	    volWall->AddNode(volRow,k,new TGeoTranslation(0, d_cl_y + BrickY/2, 0));
	    
	    // 2mm is the distance for the structure that holds the brick
	    d_cl_y += BrickY + Ydistance;
	  }
	
	//Columns
	
	Double_t d_cl_z = - ZDimension/2 + TTrackerZ;
	Double_t d_tt = -ZDimension/2 + TTrackerZ/2;
	
	for(int l = 0; l < fNWall; l++)
	  {
	    volTarget->AddNode(volWall,l,new TGeoTranslation(0, 0, d_cl_z +CellWidth/2));
	    
	    //6 cm is the distance between 2 columns of consecutive Target for TT placement
	    d_cl_z += CellWidth + TTrackerZ;
	  }
      }    
}

Bool_t  Target::ProcessHits(FairVolume* vol)
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
        fVolumeID = vol->getMCid();
	Int_t detID=0;
	gMC->CurrentVolID(detID);

	if (fVolumeID == detID) {
	  return kTRUE; }
	fVolumeID = detID;

	gGeoManager->PrintOverlaps();
	
	//cout<< "detID = " << detID << endl;
	Int_t MaxLevel = gGeoManager->GetLevel();
	const Int_t MaxL = MaxLevel;
	//cout << "MaxLevel = " << MaxL << endl;
       	//cout << gMC->CurrentVolPath()<< endl;
	

	Int_t motherV[MaxL];
	Bool_t EmTop = 0, EmBot = 0, EmCESTop = 0, EmCESBot = 0;
	Int_t NPlate =0;
	const char *name;
	
	name = gMC->CurrentVolName();
	//cout << name << endl;

	if(strcmp(name, "Emulsion") == 0)
	  {
	    EmTop=1;
	    NPlate = detID;
	  }
	if(strcmp(name, "Emulsion2") == 0)
	   {
	    EmBot=1;
	    NPlate = detID;
	  }
	if(strcmp(name, "EmulsionCES") == 0)
	  {
	    EmCESTop=1;
	    NPlate = detID;
	  }
	if(strcmp(name, "Emulsion2CES") == 0) 
	  {
	    EmCESBot=1;
	    NPlate = detID;
	  }
	
	Int_t  NWall = 0, NColumn =0, NRow =0;

	for(Int_t i = 0; i < MaxL;i++)
	  {
	    motherV[i] = gGeoManager->GetMother(i)->GetNumber();
	    const char *mumname = gMC->CurrentVolOffName(i);
	    if(motherV[0]==1 && motherV[0]!=detID)
	      {
		if(strcmp(mumname, "Brick") == 0 ||strcmp(mumname, "CES") == 0) NColumn = motherV[i];
		if(strcmp(mumname, "Cell") == 0) NRow = motherV[i];
		if(strcmp(mumname, "Row") == 0) NWall = motherV[i];
	      }
	    else
	      {
		
		if(strcmp(mumname, "Cell") == 0) NColumn = motherV[i];
		if(strcmp(mumname, "Row") == 0) NRow = motherV[i];
		if(strcmp(mumname, "Wall") == 0) NWall = motherV[i];
	      }
	    //cout << i << "   " << motherV[i] << "    name = " << mumname << endl;
	  }
    
	Bool_t BrickorCES = 0;   //Brick = 1 / CES = 0;
	if(EmTop == 1 || EmBot ==1)
	  BrickorCES = 1;
	Bool_t TopBot = 0; //Top = 1 / Bot = 0;
	if(EmTop == 1 || EmCESTop == 1)
	  TopBot = 1;

	Double_t zEnd = 0, zStart =0;
	

	detID = (NWall+1) *1E7 + (NRow+1) * 1E6 + (NColumn+1)*1E4 + BrickorCES *1E3 + (NPlate+1)*1E1 + TopBot*1 ;


	fVolumeID = detID;
	
	if (fELoss == 0. ) { return kFALSE; }
        TParticle* p=gMC->GetStack()->GetCurrentTrack();
	//Int_t MotherID =gMC->GetStack()->GetCurrentParentTrackNumber();
	Int_t fMotherID =p->GetFirstMother();
	Int_t pdgCode = p->GetPdgCode();

	//	cout << "ID = "<< fTrackID << "   pdg = " << pdgCode << ";   M = " << fMotherID << "    Npl = " << NPlate<<";  NCol = " << NColumn << ";  NRow = " << NRow << "; NWall = " << NWall<< "  P = " << fMom.Px() << ", "<< fMom.Py() << ", " << fMom.Pz() << endl;
	
        TLorentzVector Pos; 
        gMC->TrackPosition(Pos); 
        Double_t xmean = (fPos.X()+Pos.X())/2. ;      
        Double_t ymean = (fPos.Y()+Pos.Y())/2. ;      
        Double_t zmean = (fPos.Z()+Pos.Z())/2. ;     
        
	/*AddHit(fTrackID,fVolumeID, TVector3(xmean, ymean,  zmean),
               TVector3(fMom.Px(), fMom.Py(), fMom.Pz()), fTime, fLength,
               fELoss, pdgCode, EmTop, EmBot, EmCESTop,EmCESBot,TT,
	       NPlate,NColumn,NRow,NWall);
	*/
	AddHit(fTrackID,fVolumeID, TVector3(xmean, ymean,  zmean),
               TVector3(fMom.Px(), fMom.Py(), fMom.Pz()), fTime, fLength,
               fELoss, pdgCode);
	
        // Increment number of muon det points in TParticle
        ShipStack* stack = (ShipStack*) gMC->GetStack();
        stack->AddPoint(ktauTarget);
    }
    
    return kTRUE;
}


void Target::DecodeBrickID(Int_t detID, Int_t &NWall, Int_t &NRow, Int_t &NColumn, Int_t &NPlate, Bool_t &EmCESTop, Bool_t &EmCESBot, Bool_t &EmTop, Bool_t &EmBot)
{
  Bool_t BrickorCES = 0, TopBot = 0;
  
  NWall = detID/1E7;
  NRow = (detID - NWall*1E7)/1E6;
  NColumn = (detID - NWall*1E7 -NRow*1E6)/1E4;
  Double_t b = (detID - NWall*1E7 -NRow*1E6 - NColumn*1E4)/1.E3;
  if(b < 1)
    {
      BrickorCES = 0;
      NPlate = (detID - NWall*1E7 -NRow*1E6 - NColumn*1E4 - BrickorCES*1E3)/1E1;
    }
  if(b >= 1)
    {
      BrickorCES = 1;
      NPlate = (detID - NWall*1E7 -NRow*1E6 - NColumn*1E4 - BrickorCES*1E3)/1E1;
    }
  TopBot = (detID - NWall*1E7 -NRow*1E6 - NColumn*1E4- BrickorCES*1E3- NPlate*1E1)/1E0;
  if(BrickorCES == 0)
    {
      if(TopBot == 1) {EmCESTop = 1; EmCESBot =0;}
      if(TopBot == 0) {EmCESTop = 0; EmCESBot = 1;}
    }
  if(BrickorCES == 1)
    {
      if(TopBot == 1) {EmTop = 1; EmBot =0;}
      if(TopBot == 0) {EmTop = 0; EmBot = 1;}
    }
  
  // cout << "NPlate = " << NPlate << ";  NColumn = " << NColumn << ";  NRow = " << NRow << "; NWall = " << NWall << endl;
  // cout << "BrickorCES = " << BrickorCES << ";    TopBot = " << TopBot << endl;
  // cout << "EmCESTop = " << EmCESTop << ";    EmCESBot = " << EmCESBot << endl;
  // cout << "EmTop = " << EmTop << ";    EmBot = " << EmBot << endl;
  // cout << endl;
}


void Target::EndOfEvent()
{
    fTargetPointCollection->Clear();
}


void Target::Register()
{
    
    /** This will create a branch in the output tree called
     TargetPoint, setting the last parameter to kFALSE means:
     this collection will not be written to the file, it will exist
     only during the simulation.
     */
    
    FairRootManager::Instance()->Register("TargetPoint", "Target",
                                          fTargetPointCollection, kTRUE);
}

TClonesArray* Target::GetCollection(Int_t iColl) const
{
    if (iColl == 0) { return fTargetPointCollection; }
    else { return NULL; }
}

void Target::Reset()
{
    fTargetPointCollection->Clear();
}


TargetPoint* Target::AddHit(Int_t trackID,Int_t detID,
                           TVector3 pos, TVector3 mom,
                           Double_t time, Double_t length,
			    Double_t eLoss, Int_t pdgCode)
{
    TClonesArray& clref = *fTargetPointCollection;
    Int_t size = clref.GetEntriesFast();
    //cout << "brick hit called"<< pos.z()<<endl;
    return new(clref[size]) TargetPoint(trackID,detID, pos, mom,
					time, length, eLoss, pdgCode);
}

ClassImp(Target)
