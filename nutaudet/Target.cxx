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

Target::Target(const char* name, const Double_t Ydist, Bool_t Active, const char* Title)
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

//--------------Options for detector construction
void Target::SetDetectorDesign(Int_t Design)
{
  fDesign = Design;
  Info("SetDetectorDesign"," to %i", fDesign);
}

void Target::MakeNuTargetPassive(Bool_t a)
{
  fPassive=a;
}

void Target::MergeTopBot(Bool_t SingleEmFilm)
{
  fsingleemulsionfilm=SingleEmFilm;
}

//--------------------------

void Target::SetNumberBricks(Double_t col, Double_t row, Double_t wall)
{
  fNCol = col;
  fNRow = row;
  fNWall = wall; 
}

void Target::SetNumberTargets(Int_t target)
{
  fNTarget = target;
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
  fMagnetBaseY=Y;
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

void Target::SetCenterZ(Double_t z)
{
  fCenterZ = z;
}

void Target::SetBaseDimension(Double_t x, Double_t y, Double_t z)
{
  fBaseX=x; 
  fBaseY=y;
  fBaseZ=z;
}


void Target::SetPillarDimension(Double_t x, Double_t y, Double_t z)
{
  fPillarX=x; 
  fPillarY=y;
  fPillarZ=z;
}

void Target::SetHpTParam(Int_t n, Double_t dd, Double_t DZ) //need to know about HPT.cxx geometry to place additional targets
{
 fnHpT = n;
 fHpTDistance = dd;
 fHpTDZ = DZ;
}

void Target::ConstructGeometry()
{
  // cout << "Design = " << fDesign << endl;
  TGeoVolume *top=gGeoManager->GetTopVolume();
    
  InitMedium("iron");
  TGeoMedium *Fe =gGeoManager->GetMedium("iron");
    
  InitMedium("CoilAluminium");
  TGeoMedium *Al  = gGeoManager->GetMedium("CoilAluminium");
    
  InitMedium("CoilCopper");
  TGeoMedium *Cu  = gGeoManager->GetMedium("CoilCopper");
    
  InitMedium("PlasticBase");
  TGeoMedium *PBase =gGeoManager->GetMedium("PlasticBase");     

  InitMedium("NuclearEmulsion");
  TGeoMedium *NEmu =gGeoManager->GetMedium("NuclearEmulsion");
  
  TGeoMaterial *NEmuMat = NEmu->GetMaterial(); //I need the materials to build the mixture
  TGeoMaterial *PBaseMat = PBase->GetMaterial();

  Double_t rho_film = (NEmuMat->GetDensity() * 2 * EmulsionThickness +  PBaseMat->GetDensity() * PlasticBaseThickness)/(2* EmulsionThickness  + PlasticBaseThickness);
  Double_t frac_emu = NEmuMat->GetDensity() * 2 * EmulsionThickness /(NEmuMat->GetDensity() * 2 * EmulsionThickness + PBaseMat->GetDensity() * PlasticBaseThickness);

  if (fsingleemulsionfilm) cout<<"TARGET PRINTOUT: Single volume for emulsion film chosen: average density: "<<rho_film<<" fraction in mass of emulsion "<<frac_emu<<endl;

  TGeoMixture * emufilmmixture = new TGeoMixture("EmulsionFilmMixture", 2.00); // two nuclear emulsions separated by the plastic base

  emufilmmixture->AddElement(NEmuMat,frac_emu);
  emufilmmixture->AddElement(PBaseMat,1. - frac_emu);
  
  TGeoMedium *Emufilm = new TGeoMedium("EmulsionFilm",100,emufilmmixture);

  InitMedium("lead");
  TGeoMedium *lead = gGeoManager->GetMedium("lead");
    
  InitMedium("rohacell");
  TGeoMedium *rohacell = gGeoManager->GetMedium("rohacell");

  InitMedium("Concrete");
  TGeoMedium *Conc =gGeoManager->GetMedium("Concrete");

  InitMedium("steel");
  TGeoMedium *Steel =gGeoManager->GetMedium("steel");


  Int_t NPlates = 56; //Number of doublets emulsion + Pb
  Int_t NRohacellGap = 2;

  //Definition of the target box containing emulsion bricks + (CES if fDesign = 0 o 1) + target trackers (TT) 
  TGeoBBox *TargetBox = new TGeoBBox("TargetBox",XDimension/2, YDimension/2, ZDimension/2);
  TGeoVolumeAssembly *volTarget = new TGeoVolumeAssembly("volTarget");
      
  // In both fDesign=0 & fDesign=1 the emulsion target is inserted within a magnet
  if(fDesign!=2)
    {
      TGeoVolume *MagnetVol;

      //magnetic field in target
      TGeoUniformMagField *magField2 = new TGeoUniformMagField(); 

      if(fDesign==1) //TP
	{
	  magField2->SetFieldValue(fField,0,0.);
	  MagnetVol=gGeoManager->GetVolume("Davide");
	}
      if(fDesign==0) //NEW
	{
	  MagnetVol=gGeoManager->GetVolume("Goliath");
	  magField2->SetFieldValue(0.,fField,0.);
	}
      if(fDesign==3)
	{
	  magField2->SetFieldValue(fField,0,0.);
	  MagnetVol=gGeoManager->GetVolume("NudetMagnet");
	}

      //Definition of the target box containing emulsion bricks + CES + target trackers (TT) 
      if (fDesign != 3) volTarget->SetField(magField2);
      volTarget->SetVisibility(1);
      volTarget->SetVisDaughters(1);
      if(fDesign==0) //TP
	MagnetVol->AddNode(volTarget,1,new TGeoTranslation(0,-fMagnetY/2+fColumnY+fCoilH2+YDimension/2,0));
      if(fDesign==1) //NEW
	MagnetVol->AddNode(volTarget,1,new TGeoTranslation(0,-fMagnetY/2+fColumnY+YDimension/2,0));
      if(fDesign==3){        
        TGeoVolume *volMagRegion=gGeoManager->GetVolume("volMagRegion");
        Double_t ZDimMagnetizedRegion = ((TGeoBBox*) volMagRegion->GetShape())->GetDZ() * 2.; //n.d.r. DZ is the semidimension 
        for (int i = 0; i < fNTarget; i++){
         volMagRegion->AddNode(volTarget,i+1,new TGeoTranslation(0,0, -ZDimMagnetizedRegion/2 + ZDimension/2. + i*(ZDimension + 3 * fHpTDZ + 2* fHpTDistance)));
        }
       }
    }

    
    
    
    

    
  //
  //Volumes definition
  //
   
  TGeoVolumeAssembly *volCell = new TGeoVolumeAssembly("Cell");
    
  //Brick
  TGeoVolumeAssembly *volBrick = new TGeoVolumeAssembly("Brick");
  volBrick->SetLineColor(kCyan);
  volBrick->SetTransparency(1);   
    
  TGeoBBox *Lead = new TGeoBBox("Pb", EmulsionX/2, EmulsionY/2, LeadThickness/2);
  TGeoVolume *volLead = new TGeoVolume("Lead",Lead,lead);
  volLead->SetTransparency(1);
  volLead->SetLineColor(kGray);
  //volLead->SetField(magField2);
    
  for(Int_t n=0; n<NPlates; n++)
    {
      volBrick->AddNode(volLead, n, new TGeoTranslation(0,0,-BrickZ/2+BrickPackageZ/2+ EmPlateWidth + LeadThickness/2 + n*AllPlateWidth)); //LEAD
    }
  if (fsingleemulsionfilm){  //simplified configuration, unique sensitive layer for the whole emulsion plate
   TGeoBBox *EmulsionFilm = new TGeoBBox("EmulsionFilm", EmulsionX/2, EmulsionY/2, EmPlateWidth/2);
   TGeoVolume *volEmulsionFilm = new TGeoVolume("Emulsion",EmulsionFilm,Emufilm); //TOP
   volEmulsionFilm->SetLineColor(kBlue);

   if(fPassive==0)
    {
      AddSensitiveVolume(volEmulsionFilm);
    }
    
   for(Int_t n=0; n<NPlates+1; n++)
    {
      volBrick->AddNode(volEmulsionFilm, n, new TGeoTranslation(0,0,-BrickZ/2+BrickPackageZ/2+ EmPlateWidth/2 + n*AllPlateWidth));
    }
   }
  else { //more accurate configuration, two emulsion films divided by a plastic base
   TGeoBBox *EmulsionFilm = new TGeoBBox("EmulsionFilm", EmulsionX/2, EmulsionY/2, EmulsionThickness/2);
   TGeoVolume *volEmulsionFilm = new TGeoVolume("Emulsion",EmulsionFilm,NEmu); //TOP
   TGeoVolume *volEmulsionFilm2 = new TGeoVolume("Emulsion2",EmulsionFilm,NEmu); //BOTTOM
   volEmulsionFilm->SetLineColor(kBlue);
   volEmulsionFilm2->SetLineColor(kBlue);

   if(fPassive==0)
     {
       AddSensitiveVolume(volEmulsionFilm);
       AddSensitiveVolume(volEmulsionFilm2);
     }
   TGeoBBox *PlBase = new TGeoBBox("PlBase", EmulsionX/2, EmulsionY/2, PlasticBaseThickness/2);
   TGeoVolume *volPlBase = new TGeoVolume("PlasticBase",PlBase,PBase);
   volPlBase->SetLineColor(kYellow-4);
   for(Int_t n=0; n<NPlates+1; n++)
    {
      volBrick->AddNode(volEmulsionFilm2, n, new TGeoTranslation(0,0,-BrickZ/2+BrickPackageZ/2+ EmulsionThickness/2 + n*AllPlateWidth)); //BOTTOM
      volBrick->AddNode(volEmulsionFilm, n, new TGeoTranslation(0,0,-BrickZ/2+BrickPackageZ/2+3*EmulsionThickness/2+PlasticBaseThickness+n*AllPlateWidth)); //TOP
      volBrick->AddNode(volPlBase, n, new TGeoTranslation(0,0,-BrickZ/2+BrickPackageZ/2+EmulsionThickness+PlasticBaseThickness/2+n*AllPlateWidth)); //PLASTIC BASE
    }    
 }
    
  volBrick->SetVisibility(kTRUE);

  //The CES is required only in the option with magnet surrounding the emulsion target
  if(fDesign!=2)
    {    
      //CES
      TGeoVolumeAssembly *volCES = new TGeoVolumeAssembly("CES");
      volCES->SetTransparency(5);
      volCES->SetLineColor(kYellow-10);
      volCES->SetVisibility(kTRUE);
    
      TGeoBBox *RohGap = new TGeoBBox("RohGap", EmulsionX/2, EmulsionY/2, RohacellGap/2);
      TGeoVolume *volRohGap = new TGeoVolume("RohacellGap",RohGap,rohacell);
      volRohGap->SetTransparency(1);
      volRohGap->SetLineColor(kYellow);
    
      for(Int_t n=0; n<NRohacellGap; n++)
	{
	  volCES->AddNode(volRohGap, n, new TGeoTranslation(0,0,-CESWidth/2 +CESPackageZ/2+  EmPlateWidth + RohacellGap/2 + n*LayerCESWidth)); //ROHACELL
	}
      if(fsingleemulsionfilm){ //simplified configuration, unique sensitive layer for the whole emulsion plate
       TGeoBBox *EmulsionFilmCES = new TGeoBBox("EmulsionFilmCES", EmulsionX/2, EmulsionY/2, EmPlateWidth/2);
       TGeoVolume *volEmulsionFilmCES = new TGeoVolume("EmulsionCES",EmulsionFilmCES,Emufilm); //TOP
       volEmulsionFilmCES->SetLineColor(kBlue);
       if(fPassive==0)
	{
	  AddSensitiveVolume(volEmulsionFilmCES);
	}
    
       for(Int_t n=0; n<NRohacellGap+1;n++)
	{
	  volCES->AddNode(volEmulsionFilmCES,n, new TGeoTranslation(0,0,-CESWidth/2+CESPackageZ/2+EmPlateWidth/2+n*LayerCESWidth)); 
	}

      }
      else{ //more accurate configuration, two emulsion films divided by a plastic base
    
       TGeoBBox *EmulsionFilmCES = new TGeoBBox("EmulsionFilmCES", EmulsionX/2, EmulsionY/2, EmulsionThickness/2);
       TGeoVolume *volEmulsionFilmCES = new TGeoVolume("EmulsionCES",EmulsionFilmCES,NEmu); //TOP
       TGeoVolume *volEmulsionFilm2CES = new TGeoVolume("Emulsion2CES",EmulsionFilmCES,NEmu); //BOTTOM
       volEmulsionFilmCES->SetLineColor(kBlue);
       volEmulsionFilm2CES->SetLineColor(kBlue);
       if(fPassive==0)
 	{
 	  AddSensitiveVolume(volEmulsionFilmCES);
 	  AddSensitiveVolume(volEmulsionFilm2CES);
 	}
       //CES PLASTIC BASE
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

      }
    
      volCell->AddNode(volBrick,1,new TGeoTranslation(0,0,-CellWidth/2 + BrickZ/2));
      volCell->AddNode(volCES,1,new TGeoTranslation(0,0,-CellWidth/2 + BrickZ + CESWidth/2));
    
      TGeoVolumeAssembly *volRow = new TGeoVolumeAssembly("Row");
      volRow->SetLineColor(20);
    
      Double_t d_cl_x = -XDimension/2;
      for(int j= 0; j < fNCol; j++)
	{
	  volRow->AddNode(volCell,j,new TGeoTranslation(d_cl_x+BrickX/2, 0, 0));
	  d_cl_x += BrickX;
	}

      TGeoVolumeAssembly *volWall = new TGeoVolumeAssembly("Wall");
    
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


  //in fDesign==2 the emulsion target is not surrounded by a magnet => no magnetic field inside
  //In the no Magnetic field option, no CES is needed => only brick walls + TT
  if(fDesign==2)
    {
      EmulsionMagnet emuMag;

      TGeoVolume *tTauNuDet = gGeoManager->GetVolume("tTauNuDet");  
      cout<< "Tau Nu Detector fMagnetConfig: "<< fDesign<<endl;
    
      tTauNuDet->AddNode(volTarget,1,new TGeoTranslation(0,0,fCenterZ));
	
   
      TGeoVolumeAssembly *volRow = new TGeoVolumeAssembly("Row");
      volRow->SetLineColor(20);
    
      Double_t d_cl_x = -XDimension/2;
      for(int j= 0; j < fNCol; j++)
	{
	  volRow->AddNode(volBrick,j,new TGeoTranslation(d_cl_x+BrickX/2, 0, 0));
	  d_cl_x += BrickX;
	}
      TGeoVolumeAssembly *volWall = new TGeoVolumeAssembly("Wall");
    
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
	  volTarget->AddNode(volWall,l,new TGeoTranslation(0, 0, d_cl_z +BrickZ/2));
        
	  //6 cm is the distance between 2 columns of consecutive Target for TT placement
	  d_cl_z += BrickZ + TTrackerZ;
	}
      
      TGeoBBox *Base = new TGeoBBox("Base", fBaseX/2, fBaseY/2, fBaseZ/2);
      TGeoVolume *volBase = new TGeoVolume("volBase",Base,Conc);
      volBase->SetLineColor(kYellow-3);
      tTauNuDet->AddNode(volBase,1, new TGeoTranslation(0,-YDimension/2 - fBaseY/2,fCenterZ));

      if(fDesign==2)
	{
	  TGeoBBox *PillarBox = new TGeoBBox(fPillarX/2,fPillarY/2, fPillarZ/2);
	  TGeoVolume *PillarVol = new TGeoVolume("PillarVol",PillarBox,Steel);
	  PillarVol->SetLineColor(kGreen+3);
	  tTauNuDet->AddNode(PillarVol,1, new TGeoTranslation(-XDimension/2+fPillarX/2,-YDimension/2-fBaseY-fPillarY/2, fCenterZ-ZDimension/2+fPillarZ/2));
	  tTauNuDet->AddNode(PillarVol,2, new TGeoTranslation(XDimension/2-fPillarX/2,-YDimension/2-fBaseY-fPillarY/2, fCenterZ-ZDimension/2+fPillarZ/2));
	  tTauNuDet->AddNode(PillarVol,3, new TGeoTranslation(-XDimension/2+fPillarX/2,-YDimension/2-fBaseY-fPillarY/2, fCenterZ+ZDimension/2-fPillarZ/2));
	  tTauNuDet->AddNode(PillarVol,4, new TGeoTranslation(XDimension/2-fPillarX/2,-YDimension/2-fBaseY-fPillarY/2, fCenterZ+ZDimension/2-fPillarZ/2));
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
    gMC->CurrentVolID(fVolumeID);
    Int_t detID = fVolumeID;
    //gGeoManager->PrintOverlaps();
	
    //cout<< "detID = " << detID << endl;
    Int_t MaxLevel = gGeoManager->GetLevel();
    const Int_t MaxL = MaxLevel;
    //cout << "MaxLevel = " << MaxL << endl;
    //cout << gMC->CurrentVolPath()<< endl;
	

    Int_t motherV[MaxL];
//   Bool_t EmTop = 0, EmBot = 0, EmCESTop = 0, EmCESBot = 0;
    Bool_t EmBrick = 0, EmCES = 0, EmTop;
    Int_t NPlate =0;
    const char *name;
	
    name = gMC->CurrentVolName();
    //cout << name << endl;

    if(strcmp(name, "Emulsion") == 0)
      {
	EmBrick=1;
	NPlate = detID;
        EmTop=1;
      }
    if(strcmp(name, "Emulsion2") == 0)
      {
	EmBrick=1;
	NPlate = detID;
        EmTop=0;
      }
    if(strcmp(name, "EmulsionCES") == 0)
      {
	EmCES=1;
	NPlate = detID;
        EmTop=1;
      }
    if(strcmp(name, "Emulsion2CES") == 0)
      {
	EmCES=1;
	NPlate = detID;
        EmTop=0;
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
            if((strcmp(mumname, "Wall") == 0)&& (motherV[i]==2)) NWall += fNWall;
	  }
	else
	  {
		
	    if(strcmp(mumname, "Cell") == 0) NColumn = motherV[i];
	    if(strcmp(mumname, "Row") == 0) NRow = motherV[i];
	    if(strcmp(mumname, "Wall") == 0) NWall = motherV[i];
             if((strcmp(mumname, "volTarget") == 0) && (motherV[i]==2)) NWall += fNWall;
	  }
	//cout << i << "   " << motherV[i] << "    name = " << mumname << endl;
      }
    
    Bool_t BrickorCES = 0;   //Brick = 1 / CES = 0;
    if(EmBrick==1)
      BrickorCES = 1;

    Double_t zEnd = 0, zStart =0;
	

    detID = (NWall+1) *1E7 + (NRow+1) * 1E6 + (NColumn+1)*1E4 + BrickorCES *1E3 + (NPlate+1)*1E1 + EmTop*1 ;


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
        
   
    AddHit(fTrackID,fVolumeID, TVector3(xmean, ymean,  zmean),
	   TVector3(fMom.Px(), fMom.Py(), fMom.Pz()), fTime, fLength,
	   fELoss, pdgCode);
	
    // Increment number of muon det points in TParticle
    ShipStack* stack = (ShipStack*) gMC->GetStack();
    stack->AddPoint(ktauTarget);
  }
    
  return kTRUE;
}


void Target::DecodeBrickID(Int_t detID, Int_t &NWall, Int_t &NRow, Int_t &NColumn, Int_t &NPlate, Bool_t &EmCES, Bool_t &EmBrick, Bool_t &EmTop)
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
//      NPlate = detID - NWall*1E7 -NRow*1E6 - NColumn*1E4 - BrickorCES*1E3;
    }
  if(b >= 1)
    {
      BrickorCES = 1;
      NPlate = (detID - NWall*1E7 -NRow*1E6 - NColumn*1E4 - BrickorCES*1E3)/1E1;
//      NPlate = detID - NWall*1E7 -NRow*1E6 - NColumn*1E4 - BrickorCES*1E3;
    }
  EmTop = (detID - NWall*1E7 -NRow*1E6 - NColumn*1E4- BrickorCES*1E3- NPlate*1E1)/1E0;
  if(BrickorCES == 0)
    {
      EmCES = 1; EmBrick =0;
    }
  if(BrickorCES == 1)
    {
      EmBrick = 1; EmCES =0;
    }
  
  // cout << "NPlate = " << NPlate << ";  NColumn = " << NColumn << ";  NRow = " << NRow << "; NWall = " << NWall << endl;
  // cout << "BrickorCES = " << BrickorCES <<endl;
  // cout << "EmCES = " << EmCES << ";    EmBrick = " << EmBick << endl;
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
