//
//  Box.cxx
//  Target file: 10 different run configurations can be done, setting the number of the variable nrun.
//
//
//

#include "Box.h"

#include "BoxPoint.h"

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

Box::Box()
: FairDetector("Box", "",kTRUE),
  fTrackID(-1),
fVolumeID(-1),
fPos(),
fMom(),
fTime(-1.),
fLength(-1.),
fELoss(-1),
fBoxPointCollection(new TClonesArray("BoxPoint"))
{
}

Box::Box(const char* name, const Double_t BX, const Double_t BY, const Double_t BZ,const Double_t zBox, Bool_t Active,const char* Title)
: FairDetector(name, true, kBox1),
  fTrackID(-1),
fVolumeID(-1),
fPos(),
fMom(),
fTime(-1.),
fLength(-1.),
fELoss(-1),
fBoxPointCollection(new TClonesArray("BoxPoint"))
{
    BoxX = BX;
    BoxY = BY;
    BoxZ = BZ;
    zBoxPosition = zBox;
}

Box::~Box()
{
    if (fBoxPointCollection) {
        fBoxPointCollection->Delete();
        delete fBoxPointCollection;
    }
}

void Box::Initialize()
{
    FairDetector::Initialize();
}

void Box::SetEmulsionParam(Double_t EmTh, Double_t EmX, Double_t EmY, Double_t PBTh, Double_t EPlW,Double_t MolybdenumTh, Double_t AllPW)
{
    EmulsionThickness = EmTh;
    EmulsionX = EmX;
    EmulsionY = EmY;
    PlasticBaseThickness = PBTh;
    EmPlateWidth = EPlW;
    MolybdenumThickness = MolybdenumTh;
    AllPlateWidth = AllPW;
}

void Box::SetBrickParam(Double_t BrX, Double_t BrY, Double_t BrZ, Double_t BrPackX, Double_t BrPackY, Double_t BrPackZ)
{
  BrickPackageX = BrPackX;
  BrickPackageY = BrPackY;
  BrickPackageZ = BrPackZ;
  BrickX = BrX;
  BrickY = BrY;
  BrickZ = BrZ;
}

void Box::SetPassiveParam(Double_t PX, Double_t PY, Double_t PZ)
{
  PassiveX = PX;
  PassiveY = PY;
  PassiveZ = PZ;

}

void Box::SetTargetParam(Double_t TX, Double_t TY, Double_t TZ){
  TargetX = TX; 
  TargetY = TY;
  TargetZ = TZ;
}

void Box::SetCoolingParam(Double_t CoolX, Double_t CoolY, Double_t CoolZ){
  CoolingX = CoolX; 
  CoolingY = CoolY;
  CoolingZ = CoolZ;
}

void Box::SetCoatingParam(Double_t CoatX, Double_t CoatY, Double_t CoatZ){
  CoatingX = CoatX;
  CoatingY = CoatY;
  CoatingZ = CoatZ;

}


// -----   Private method InitMedium
Int_t Box::InitMedium(const char* name)
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



void Box::ConstructGeometry()
{
    InitMedium("tantalum");
    TGeoMedium *tantalum = gGeoManager->GetMedium("tantalum");
       
    InitMedium("vacuum");
    TGeoMedium *vacuum = gGeoManager->GetMedium("vacuum");

    InitMedium("molybdenum");
    TGeoMedium *molybdenum = gGeoManager->GetMedium("molybdenum");

    InitMedium("tungsten");
    TGeoMedium *tungsten = gGeoManager->GetMedium("tungsten");
    
    InitMedium("Scintillator");
    TGeoMedium *scint =gGeoManager->GetMedium("Scintillator");

    InitMedium("H2O");
    TGeoMedium *water = gGeoManager->GetMedium("H2O");
    
    TGeoVolume *top= gGeoManager->GetTopVolume(); 
    /* TGeoBBox *BOX1 = new TGeoBBox(BoxX/2,BoxY/2,BoxZ/2);
    TGeoVolume *VBOX1 = new TGeoVolume("volBox", BOX1,vacuum);
    //VBOX1->SetLineColor(kRed);
    // top->AddNode(VBOX1,1,new TGeoTranslation(0,0,zBoxPosition));
    VBOX1->SetTransparency(1);
    //AddSensitiveVolume(VBOX1);
    */


    //begin passive material part (pre target)
    //TGeoBBox *Passive = new TGeoBBox("Passive", PassiveX/2, PassiveY/2, PassiveZ/2);
    //TGeoVolume *volPassive = new TGeoVolume("volPassive", Passive, molybdenum);
    //volPassive->SetLineColor(kRed);
    //volPassive->SetVisibility(kTRUE);
    //top->AddNode(volPassive,1, new TGeoTranslation(0,0,zBoxPosition));
    
    
    //begin brick part
    Int_t nreplica = 0; //number of emulsion films activated;
    Int_t nmol3 = 0; //number of molybdenum blocks of 3mm;
    Int_t nmol2 = 0; //number of molybdenum blocks of 2mm;
    Int_t nw3 = 0; //number of tungsten blocks of 3mm;
    Int_t nw2 = 0; //number of tungsten blocks of 2mm;
    Int_t ncoating = 0;
    Int_t ncooling = 0;

    Int_t nmegamol1 = 0;
    Int_t nmegamol2 = 0;
    Int_t nmegamol3 = 0;
    Int_t nmegamol4 = 0;
    Int_t nmegaw1 = 0;
    Int_t nmegaw2 = 0;
    Int_t nmegaw3 = 0;
    Int_t nmegaw4 = 0;

    //Int_t NPlates = 56; //Number of doublets emulsion + Pb
    Int_t NPlates = 54;
    InitMedium("NuclearEmulsion");
    TGeoMedium *NEmu = gGeoManager->GetMedium("NuclearEmulsion");

    InitMedium("PlasticBase");
    TGeoMedium *PBase = gGeoManager->GetMedium("PlasticBase");

   

    //TGeoBBox *Brick = new TGeoBBox("brick", BoxX/2, BoxY/2, BoxZ/2);
    //TGeoBBox *Brick = new TGeoBBox("brick", BrickX/2, BrickY/2, BrickZ/2);
    //TGeoVolume *volBrick = new TGeoVolume("Brick",Brick,vacuum);
    //volBrick->SetLineColor(kCyan);
    //volBrick->SetTransparency(1);

    // top->AddNode(volBrick,1,new TGeoTranslation(0,0,zBoxPosition+PassiveZ));

         

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
	
        //volumes not used in the new configuration
	//TGeoVolume *volMolybdenum = new TGeoVolume("Molybdenum",Molybdenum,molybdenum);
        //TGeoVolume *volMolybdenum = new TGeoVolume("Molybdenum",Molybdenum,tungsten); 
	//volMolybdenum->SetTransparency(1);
	//volMolybdenum->SetLineColor(kGray);
	//volMolybdenum->SetField(magField2);
	//volumes not used in the new configuration
	
	/*	for(Int_t n=0; n<NPlates+1; n++) //primo brick realizzato, tipo OPERA
	  {
	    volBrick->AddNode(volEmulsionFilm2, n, new TGeoTranslation(0,0,-BrickZ/2+BrickPackageZ/2+ EmulsionThickness/2 + n*AllPlateWidth)); //BOTTOM
	    volBrick->AddNode(volEmulsionFilm, n, new TGeoTranslation(0,0,-BrickZ/2+BrickPackageZ/2+3*EmulsionThickness/2+PlasticBaseThickness+n*AllPlateWidth)); //TOP
	    volBrick->AddNode(volPlBase, n, new TGeoTranslation(0,0,-BrickZ/2+BrickPackageZ/2+EmulsionThickness+PlasticBaseThickness/2+n*AllPlateWidth)); //PLASTIC BASE
	  }
	for(Int_t n=0; n<NPlates; n++)
	  {
	    volBrick->AddNode(volMolybdenum, n, new TGeoTranslation(0,0,-BrickZ/2+BrickPackageZ/2+ EmPlateWidth + MolybdenumThickness/2 + n*AllPlateWidth)); //LEAD
	  }
           // volBrick->AddNode(volCoating, 1, new TGeoTranslation(0,0,-CoatingZ/2-BrickZ/2)); //tantalum
	
	   volBrick->SetVisibility(kTRUE);*/

	

      //starting to simulate SHiP target
     Double_t xTarget = 10.;
     Double_t yTarget = 10.;
     Double_t zTarget = TargetZ;

     Double_t zposition = 0;
     const int nbricks = 10;
     bool activate[nbricks];
     bool add[nbricks];

     for (int i = 0; i < nbricks;i++){
      add[i] = false;
      activate[i] = false;
     }
     const int nrun = 1; //what run do you want to do? (insert a number from 1 to 10)
     activate[nrun-1] = true;
     
     for (int i = 0; i < nrun;i++){
      add[i] = true;
     }

     int index = 0;
     
     TGeoBBox *Target = new TGeoBBox("Target", TargetX/2, TargetY/2, TargetZ/2); //for the moment I will use numbers instead of variables.
     TGeoVolume *volTarget = new TGeoVolume("volTarget", Target, vacuum);
     volTarget->SetTransparency(1);
     //top->AddNode(volTarget,1,new TGeoTranslation(0,0,zBoxPosition-65));     
     top->AddNode(volTarget,1,new TGeoTranslation(0,0,zBoxPosition-TargetZ/2));
     TGeoBBox *Cooling = new TGeoBBox("Cooling", CoolingX/2, CoolingY/2, CoolingZ/2); //water slips to cool the target
     TGeoVolume *volCooling = new TGeoVolume("volCooling", Cooling, PBase);
     volCooling->SetLineColor(kCyan);
  
     TGeoBBox *Coating = new TGeoBBox("Coating", CoatingX/2, CoatingY/2, CoatingZ/2);
     TGeoVolume *volCoating = new TGeoVolume("volCoating", Coating, tantalum);
     volCoating->SetLineColor(kRed);

     TGeoBBox *Mol3mm = new TGeoBBox("Mol3mm", xTarget/2, yTarget/2, 0.3/2);
     TGeoVolume *volMol3mm = new TGeoVolume("volMol3mm", Mol3mm, molybdenum);
     volMol3mm->SetLineColor(kGray);

     TGeoBBox *Mol2mm = new TGeoBBox("Mol2mm", xTarget/2, yTarget/2, 0.2/2);
     TGeoVolume *volMol2mm = new TGeoVolume("volMol2mm", Mol2mm, molybdenum);
     volMol2mm->SetLineColor(kGray);

     TGeoBBox *Mol1 = new TGeoBBox("Mol1", xTarget/2, yTarget/2, 7.8/2);
     TGeoVolume *volMol1 = new TGeoVolume("volMol1", Mol1, molybdenum); //1, then 2 at the end of the molybdenum row
     volMol1->SetLineColor(kGray);

     TGeoBBox *Mol2 = new TGeoBBox("Mol2", xTarget/2, yTarget/2, 2.3/2); // 7
     TGeoVolume *volMol2 = new TGeoVolume("volMol2", Mol2, molybdenum);
     volMol2->SetLineColor(kGray);

     TGeoBBox *Mol3 = new TGeoBBox("Mol3", xTarget/2, yTarget/2, 4.8/2); // 2
     TGeoVolume *volMol3 = new TGeoVolume("volMol3", Mol3, molybdenum);
     volMol3->SetLineColor(kGray);

     TGeoBBox *Mol4 = new TGeoBBox("Mol4", xTarget/2, yTarget/2, 6.3/2); // 1
     TGeoVolume *volMol4 = new TGeoVolume("volMol4", Mol4, molybdenum);
     volMol4->SetLineColor(kGray);

     TGeoBBox *W3mm = new TGeoBBox("W3mm", xTarget/2, yTarget/2, 0.3/2);
     TGeoVolume *volW3mm = new TGeoVolume("volW3mm", W3mm, tungsten);
     volW3mm->SetLineColor(kSpring);
     
     TGeoBBox *W2mm = new TGeoBBox("W2mm", xTarget/2, yTarget/2, 0.2/2);
     TGeoVolume *volW2mm = new TGeoVolume("volW2mm", W2mm, tungsten);
     volW2mm->SetLineColor(kSpring);

     TGeoBBox *W4_5mm = new TGeoBBox("W4_5mm", xTarget/2, yTarget/2, 0.45/2);
     TGeoVolume *volW4_5mm = new TGeoVolume("volW4_5mm", W4_5mm, tungsten);
     volW4_5mm->SetLineColor(kSpring);

     TGeoBBox *W1 = new TGeoBBox("W1", xTarget/2, yTarget/2, 4.8/2); // 1
     TGeoVolume *volW1 = new TGeoVolume("volW1", W1, tungsten);
     volW1->SetLineColor(kSpring);

     TGeoBBox *W2 = new TGeoBBox("W2", xTarget/2, yTarget/2, 7.8/2); // 1
     TGeoVolume *volW2 = new TGeoVolume("volW2", W2, tungsten);
     volW2->SetLineColor(kSpring);

     TGeoBBox *W3 = new TGeoBBox("W3", xTarget/2, yTarget/2, 9.8/2); // 1
     TGeoVolume *volW3 = new TGeoVolume("volW3", W3, tungsten);
     volW3->SetLineColor(kSpring);

     TGeoBBox *W4 = new TGeoBBox("W4", xTarget/2, yTarget/2, 8.7/2); // 4
     TGeoVolume *volW4 = new TGeoVolume("volW4", W4, tungsten);
     volW4->SetLineColor(kSpring);
     
     Double_t myPlateWidth = + 0.3 + AllPlateWidth - MolybdenumThickness;
     //Run 1 (26 + 8 + 7)
     if (activate[index]){
       NPlates = 26;  
       for(Int_t n=0; n<NPlates+1; n++)
	 {
	   if (add[index]) volTarget->AddNode(volEmulsionFilm2, nreplica, new TGeoTranslation(0,0,-zTarget/2+BrickPackageZ/2+ EmulsionThickness/2 + n*myPlateWidth)); //BOTTOM
	   if (add[index]) volTarget->AddNode(volEmulsionFilm, nreplica, new TGeoTranslation(0,0,-zTarget/2+BrickPackageZ/2+3*EmulsionThickness/2+PlasticBaseThickness+n*myPlateWidth)); //TOP
	   if (add[index]) volTarget->AddNode(volPlBase, nreplica, new TGeoTranslation(0,0,-zTarget/2+BrickPackageZ/2+EmulsionThickness+PlasticBaseThickness/2+n*myPlateWidth)); //PLASTIC BASE
           nreplica++;
	 }
        
        if (add[index]) volTarget->AddNode(volCoating, ncoating, new TGeoTranslation(0,0,-zTarget/2+BrickPackageZ/2 - CoatingZ/2));
        ncoating++;
	for(Int_t n=0; n<NPlates; n++)
	  {
            
	    if (add[index]) volTarget->AddNode(volMol3mm, nmol3, new TGeoTranslation(0,0,-zTarget/2+BrickPackageZ/2+ EmPlateWidth + 0.3/2 + n*myPlateWidth));
            nmol3++;

	  }
	
	if (add[index]) volTarget->AddNode(volCoating, ncoating, new TGeoTranslation(0,0,-zTarget/2+BrickPackageZ/2+ EmPlateWidth + CoatingZ/2 + NPlates*myPlateWidth));
	//another emulsion after tantalium
        if (add[index]) volTarget->AddNode(volEmulsionFilm2, nreplica, new TGeoTranslation(0,0,-zTarget/2+BrickPackageZ/2+ EmulsionThickness/2 + CoatingZ + (NPlates)*myPlateWidth + AllPlateWidth - 0.3)); //BOTTOM
	   if (add[index]) volTarget->AddNode(volEmulsionFilm, nreplica, new TGeoTranslation(0,0,-zTarget/2+BrickPackageZ/2+3*EmulsionThickness/2+PlasticBaseThickness+ CoatingZ + (NPlates)*myPlateWidth + AllPlateWidth - 0.3)); //TOP
	   if (add[index]) volTarget->AddNode(volPlBase, nreplica, new TGeoTranslation(0,0,-zTarget/2+BrickPackageZ/2+EmulsionThickness+PlasticBaseThickness/2+CoatingZ + (NPlates)*myPlateWidth+ AllPlateWidth - 0.3)); //PLASTIC BASE
           nreplica++;
        
	if (add[index]) volTarget->AddNode(volCooling, ncooling, new TGeoTranslation(0,0,-zTarget/2+BrickPackageZ/2+ EmPlateWidth + CoolingZ/2 + CoatingZ + AllPlateWidth - 0.3	+ NPlates*myPlateWidth));
        ncoating++;
        ncooling++;
	
	zposition = -zTarget/2+BrickPackageZ/2+ EmPlateWidth + CoolingZ + CoatingZ + NPlates * myPlateWidth + AllPlateWidth - 0.3;

      NPlates = 8;
    for(Int_t n=0; n<NPlates+1; n++)
    {
	   if (add[index]) volTarget->AddNode(volEmulsionFilm2, nreplica, new TGeoTranslation(0,0, zposition + CoatingZ + EmulsionThickness/2 + n*myPlateWidth)); //BOTTOM
	   if (add[index]) volTarget->AddNode(volEmulsionFilm, nreplica, new TGeoTranslation(0,0, zposition + CoatingZ + 3 * EmulsionThickness/2 +PlasticBaseThickness+n*myPlateWidth)); //TOP
	   if (add[index]) volTarget->AddNode(volPlBase, nreplica, new TGeoTranslation(0,0, zposition + CoatingZ + EmulsionThickness + PlasticBaseThickness/2+n*myPlateWidth)); //PLASTIC BASE
          nreplica++;
	  }
        if (add[index]) volTarget->AddNode(volCoating, ncoating, new TGeoTranslation(0,0,zposition + CoatingZ/2));
	ncoating++;
	for(Int_t n=0; n<NPlates; n++)
	  {
            //volTarget->AddNode(volCoating, 2*n , new TGeoTranslation(0,0,-zTarget/2+BrickPackageZ/2+ EmPlateWidth + CoatingZ/2 + n*myPlateWidth));
	    if (add[index]) volTarget->AddNode(volMol3mm, nmol3, new TGeoTranslation(0,0,zposition + CoatingZ + EmPlateWidth + 0.3/2 + n*myPlateWidth)); //LEAD
	    nmol3++;
	  }
         if (add[index]) volTarget->AddNode(volCoating, ncoating, new TGeoTranslation(0,0, zposition + CoatingZ + EmPlateWidth + CoatingZ/2 + NPlates*myPlateWidth));
	  ncoating++;
	  if (add[index]) volTarget->AddNode(volCooling, ncooling, new TGeoTranslation(0,0, zposition + CoatingZ + EmPlateWidth + CoolingZ/2 + CoatingZ + NPlates*myPlateWidth + AllPlateWidth - 0.3));
	  ncooling++;
          
          //another emulsion after tantalium
       if (add[index]) volTarget->AddNode(volEmulsionFilm2, nreplica, new TGeoTranslation(0,0, zposition + CoatingZ + EmulsionThickness/2 + (NPlates)*myPlateWidth + AllPlateWidth - 0.3 + CoatingZ)); //BOTTOM
	  if (add[index]) volTarget->AddNode(volEmulsionFilm2, nreplica, new TGeoTranslation(0,0, zposition + CoatingZ + 3 * EmulsionThickness/2 +PlasticBaseThickness+(NPlates)*myPlateWidth + AllPlateWidth - 0.3 + CoatingZ)); //TOP
	  if (add[index]) volTarget->AddNode(volPlBase, nreplica, new TGeoTranslation(0,0, zposition + CoatingZ + EmulsionThickness + PlasticBaseThickness/2+(NPlates)*myPlateWidth + AllPlateWidth - 0.3 + CoatingZ)); //PLASTIC BASE
           nreplica++;
  zposition = zposition + AllPlateWidth - 0.3 + EmPlateWidth + CoolingZ + 2 * CoatingZ + (NPlates) * myPlateWidth;

    NPlates = 7;
    for(Int_t n=0; n<NPlates+1; n++)
    {
	   if (add[index]) volTarget->AddNode(volEmulsionFilm2, nreplica, new TGeoTranslation(0,0, zposition + CoatingZ + EmulsionThickness/2 + n*myPlateWidth)); //BOTTOM
	   if (add[index]) volTarget->AddNode(volEmulsionFilm, nreplica, new TGeoTranslation(0,0, zposition + CoatingZ + 3 * EmulsionThickness/2 +PlasticBaseThickness+n*myPlateWidth)); //TOP
	   if (add[index]) volTarget->AddNode(volPlBase, nreplica, new TGeoTranslation(0,0, zposition + CoatingZ + EmulsionThickness + PlasticBaseThickness/2+n*myPlateWidth)); //PLASTIC BASE
          nreplica++;
	  }
        if (add[index]) volTarget->AddNode(volCoating, ncoating, new TGeoTranslation(0,0,zposition + CoatingZ/2));
	ncoating++;
	for(Int_t n=0; n<NPlates; n++)
	  {
            //volTarget->AddNode(volCoating, 2*n , new TGeoTranslation(0,0,-zTarget/2+BrickPackageZ/2+ EmPlateWidth + CoatingZ/2 + n*myPlateWidth));
	    if (add[index]) volTarget->AddNode(volMol3mm, nmol3, new TGeoTranslation(0,0,zposition + CoatingZ + EmPlateWidth + 0.3/2 + n*myPlateWidth)); //LEAD
	    nmol3++;
	  }
         if (add[index]) volTarget->AddNode(volCoating, ncoating, new TGeoTranslation(0,0, zposition + CoatingZ + EmPlateWidth + CoatingZ/2 + NPlates*myPlateWidth));
	  ncoating++;
	 if (add[index+1]) volTarget->AddNode(volCooling, ncooling, new TGeoTranslation(0,0, zposition + CoatingZ + EmPlateWidth + CoolingZ/2 + CoatingZ + NPlates*myPlateWidth + AllPlateWidth - 0.3));
	  ncooling++;
          
          //another emulsion after tantalium
       if (add[index]) volTarget->AddNode(volEmulsionFilm2, nreplica, new TGeoTranslation(0,0, zposition + CoatingZ + EmulsionThickness/2 + (NPlates)*myPlateWidth + AllPlateWidth - 0.3 + CoatingZ)); //BOTTOM
	  if (add[index]) volTarget->AddNode(volEmulsionFilm2, nreplica, new TGeoTranslation(0,0, zposition + CoatingZ + 3 * EmulsionThickness/2 +PlasticBaseThickness+(NPlates)*myPlateWidth + AllPlateWidth - 0.3 + CoatingZ)); //TOP
	  if (add[index]) volTarget->AddNode(volPlBase, nreplica, new TGeoTranslation(0,0, zposition + CoatingZ + EmulsionThickness + PlasticBaseThickness/2+(NPlates)*myPlateWidth + AllPlateWidth - 0.3 + CoatingZ)); //PLASTIC BASE
           nreplica++;
  zposition = zposition + AllPlateWidth - 0.3 + EmPlateWidth + CoolingZ + 2 * CoatingZ + (NPlates) * myPlateWidth;
     }
     //1 of 78, 2 of 23
     else{
       
       zposition = -zTarget/2;
       
       if (add[index]) volTarget->AddNode(volCoating, ncoating, new TGeoTranslation(0, 0, -zTarget/2 + CoatingZ/2));
       ncoating++;
       if (add[index]) volTarget->AddNode(volMol1, nmegamol1, new TGeoTranslation(0, 0, -zTarget/2 + CoatingZ + 7.8/2));
       nmegamol1++;
       if (add[index]) volTarget->AddNode(volCoating, ncoating, new TGeoTranslation(0, 0, -zTarget/2 + CoatingZ + 7.8 + CoatingZ/2));
       if (add[index]) volTarget->AddNode(volCooling, ncooling, new TGeoTranslation(0, 0, -zTarget/2 + 2 * CoatingZ  + 7.8 + CoolingZ/2));
       ncoating++;
       ncooling++;
       zposition = -zTarget/2 + 2 * CoatingZ + CoolingZ + 7.8 ;

       if (add[index]) volTarget->AddNode(volCoating, ncoating, new TGeoTranslation(0, 0, zposition + CoatingZ/2 ));
	 ncoating++;
       if (add[index]) volTarget->AddNode(volMol2, nmegamol2, new TGeoTranslation(0, 0, zposition + CoatingZ + 2.3/2 ));
	 nmegamol2++;
       if (add[index]) volTarget->AddNode(volCoating, ncoating, new TGeoTranslation(0, 0, zposition + CoatingZ + 2.3 + CoatingZ/2));
       if (add[index]) volTarget->AddNode(volCooling, ncooling, new TGeoTranslation(0, 0, zposition + 2 * CoatingZ + 2.3 + CoolingZ/2));
       ncoating++;
       ncooling++;
       zposition = zposition + (2 * CoatingZ + 2.3 + CoolingZ);

       if (add[index]) volTarget->AddNode(volCoating, ncoating, new TGeoTranslation(0, 0, zposition + CoatingZ/2 ));
	 ncoating++;
       if (add[index]) volTarget->AddNode(volMol2, nmegamol2, new TGeoTranslation(0, 0, zposition + CoatingZ + 2.3/2 ));
	 nmegamol2++;
       if (add[index]) volTarget->AddNode(volCoating, ncoating, new TGeoTranslation(0, 0, zposition + CoatingZ + 2.3 + CoatingZ/2));
       if (add[index]) volTarget->AddNode(volCooling, ncooling, new TGeoTranslation(0, 0, zposition + 2 * CoatingZ + 2.3 + CoolingZ/2));
       ncoating++;
       ncooling++;
     if (add[index])  zposition = zposition + (2 * CoatingZ + 2.3 + CoolingZ);
     }
     
     index++;
     
    //Run 2
   
      if (activate[index]){
	NPlates = 6;
	for(Int_t n=0; n<NPlates+1; n++)
	  {
	    if (add[index]) volTarget->AddNode(volEmulsionFilm2, nreplica, new TGeoTranslation(0,0, zposition + CoatingZ + EmulsionThickness/2 + n*myPlateWidth)); //BOTTOM
	    if (add[index]) volTarget->AddNode(volEmulsionFilm, nreplica, new TGeoTranslation(0,0, zposition + CoatingZ + 3 * EmulsionThickness/2 +PlasticBaseThickness+n*myPlateWidth)); //TOP
	    if (add[index]) volTarget->AddNode(volPlBase, nreplica, new TGeoTranslation(0,0, zposition + CoatingZ + EmulsionThickness + PlasticBaseThickness/2+n*myPlateWidth)); //PLASTIC BASE
	    nreplica++;
	  }
        if (add[index]) volTarget->AddNode(volCoating, ncoating, new TGeoTranslation(0,0,zposition + CoatingZ/2));
	ncoating++;
	for(Int_t n=0; n<NPlates; n++)
	  {
            //volTarget->AddNode(volCoating, 2*n , new TGeoTranslation(0,0,-zTarget/2+BrickPackageZ/2+ EmPlateWidth + CoatingZ/2 + n*myPlateWidth));
	    if (add[index]) volTarget->AddNode(volMol3mm, nmol3, new TGeoTranslation(0,0,zposition + CoatingZ + EmPlateWidth + 0.3/2 + n*myPlateWidth)); //LEAD
	    nmol3++;
	  }
         if (add[index]) volTarget->AddNode(volCoating, ncoating, new TGeoTranslation(0,0, zposition + CoatingZ + EmPlateWidth + CoatingZ/2 + NPlates*myPlateWidth));
	  ncoating++;
	  if (add[index]) volTarget->AddNode(volCooling, ncooling, new TGeoTranslation(0,0, zposition + CoatingZ + EmPlateWidth + CoolingZ/2 + CoatingZ + NPlates*myPlateWidth + AllPlateWidth - 0.3));
	  ncooling++;
          
          //another emulsion after tantalium
       if (add[index]) volTarget->AddNode(volEmulsionFilm2, nreplica, new TGeoTranslation(0,0, zposition + CoatingZ + EmulsionThickness/2 + (NPlates)*myPlateWidth + AllPlateWidth - 0.3 + CoatingZ)); //BOTTOM
	  if (add[index]) volTarget->AddNode(volEmulsionFilm2, nreplica, new TGeoTranslation(0,0, zposition + CoatingZ + 3 * EmulsionThickness/2 +PlasticBaseThickness+(NPlates)*myPlateWidth + AllPlateWidth - 0.3 + CoatingZ)); //TOP
	  if (add[index]) volTarget->AddNode(volPlBase, nreplica, new TGeoTranslation(0,0, zposition + CoatingZ + EmulsionThickness + PlasticBaseThickness/2+(NPlates)*myPlateWidth + AllPlateWidth - 0.3 + CoatingZ)); //PLASTIC BASE
           nreplica++;
	   zposition = zposition + AllPlateWidth - 0.3 + EmPlateWidth + CoolingZ + 2 * CoatingZ + (NPlates) * myPlateWidth;

	   NPlates = 8;
	   for(int i = 0; i < 4; i++){
	     for(Int_t n=0; n<NPlates+1; n++)
	       {
		 if (add[index]) volTarget->AddNode(volEmulsionFilm2, nreplica, new TGeoTranslation(0,0, zposition + CoatingZ + EmulsionThickness/2 + n*myPlateWidth)); //BOTTOM
		 if (add[index]) volTarget->AddNode(volEmulsionFilm, nreplica, new TGeoTranslation(0,0, zposition + CoatingZ + 3 * EmulsionThickness/2 +PlasticBaseThickness+n*myPlateWidth)); //TOP
		 if (add[index]) volTarget->AddNode(volPlBase, nreplica, new TGeoTranslation(0,0, zposition + CoatingZ + EmulsionThickness + PlasticBaseThickness/2+n*myPlateWidth)); //PLASTIC BASE
		 nreplica++;
	       }
	     if (add[index]) volTarget->AddNode(volCoating, ncoating, new TGeoTranslation(0,0,zposition + CoatingZ/2));
	     ncoating++;
	     for(Int_t n=0; n<NPlates; n++)
	       {
		 //volTarget->AddNode(volCoating, 2*n , new TGeoTranslation(0,0,-zTarget/2+BrickPackageZ/2+ EmPlateWidth + CoatingZ/2 + n*myPlateWidth));
		 if (add[index]) volTarget->AddNode(volMol3mm, nmol3, new TGeoTranslation(0,0,zposition + CoatingZ + EmPlateWidth + 0.3/2 + n*myPlateWidth)); //LEAD
	    nmol3++;
	       }
	     if (add[index]) volTarget->AddNode(volCoating, ncoating, new TGeoTranslation(0,0, zposition + CoatingZ + EmPlateWidth + CoatingZ/2 + NPlates*myPlateWidth));
	     ncoating++;
	     if ((add[index+1]) || (i!=3)) volTarget->AddNode(volCooling, ncooling, new TGeoTranslation(0,0, zposition + CoatingZ + EmPlateWidth + CoolingZ/2 + CoatingZ + NPlates*myPlateWidth + AllPlateWidth - 0.3));
	     ncooling++;
	     
	     //another emulsion after tantalium
	     if (add[index]) volTarget->AddNode(volEmulsionFilm2, nreplica, new TGeoTranslation(0,0, zposition + CoatingZ + EmulsionThickness/2 + (NPlates)*myPlateWidth + AllPlateWidth - 0.3 + CoatingZ)); //BOTTOM
	     if (add[index]) volTarget->AddNode(volEmulsionFilm2, nreplica, new TGeoTranslation(0,0, zposition + CoatingZ + 3 * EmulsionThickness/2 +PlasticBaseThickness+(NPlates)*myPlateWidth + AllPlateWidth - 0.3 + CoatingZ)); //TOP
	     if (add[index]) volTarget->AddNode(volPlBase, nreplica, new TGeoTranslation(0,0, zposition + CoatingZ + EmulsionThickness + PlasticBaseThickness/2+(NPlates)*myPlateWidth + AllPlateWidth - 0.3 + CoatingZ)); //PLASTIC BASE
	     nreplica++;
	     zposition = zposition + AllPlateWidth - 0.3 + EmPlateWidth + CoolingZ + 2 * CoatingZ + (NPlates) * myPlateWidth;
	   }
      }
       //5 of 23
      else{
	for (int i = 0; i < 5; i++){
	  if (add[index]) volTarget->AddNode(volCoating, ncoating, new TGeoTranslation(0, 0, zposition + CoatingZ/2 ));
	  ncoating++;
	  if (add[index]) volTarget->AddNode(volMol2, nmegamol2, new TGeoTranslation(0, 0, zposition + CoatingZ + 2.3/2 ));
	  nmegamol2++;
	  if (add[index]) volTarget->AddNode(volCoating, ncoating, new TGeoTranslation(0, 0, zposition + CoatingZ + 2.3 + CoatingZ/2));
	  if (add[index]) volTarget->AddNode(volCooling, ncooling, new TGeoTranslation(0, 0, zposition + 2 * CoatingZ + 2.3 + CoolingZ/2));
	  ncoating++;
	  ncooling++;
	  zposition = zposition + (2 * CoatingZ + 2.3 + CoolingZ);
	}
      }
      index++;
      
      //Run 3 (16+16+21)
      
      if (activate[index]){
	NPlates = 16;
	for(Int_t n=0; n<NPlates+1; n++)
	  {
	    if (add[index]) volTarget->AddNode(volEmulsionFilm2, nreplica, new TGeoTranslation(0,0, zposition + CoatingZ + EmulsionThickness/2 + n*myPlateWidth)); //BOTTOM
	    if (add[index]) volTarget->AddNode(volEmulsionFilm, nreplica, new TGeoTranslation(0,0, zposition + CoatingZ + 3 * EmulsionThickness/2 +PlasticBaseThickness+n*myPlateWidth)); //TOP
	    if (add[index]) volTarget->AddNode(volPlBase, nreplica, new TGeoTranslation(0,0, zposition + CoatingZ + EmulsionThickness + PlasticBaseThickness/2+n*myPlateWidth)); //PLASTIC BASE
	    nreplica++;
	  }
        if (add[index]) volTarget->AddNode(volCoating, ncoating, new TGeoTranslation(0,0,zposition + CoatingZ/2));
	ncoating++;
	for(Int_t n=0; n<NPlates; n++)
	  {
            //volTarget->AddNode(volCoating, 2*n , new TGeoTranslation(0,0,-zTarget/2+BrickPackageZ/2+ EmPlateWidth + CoatingZ/2 + n*myPlateWidth));
	    if (add[index]) volTarget->AddNode(volMol3mm, nmol3, new TGeoTranslation(0,0,zposition + CoatingZ + EmPlateWidth + 0.3/2 + n*myPlateWidth)); //LEAD
	    nmol3++;
	  }
	if (add[index]) volTarget->AddNode(volCoating, ncoating, new TGeoTranslation(0,0, zposition + CoatingZ + EmPlateWidth + CoatingZ/2 + NPlates*myPlateWidth));
	ncoating++;
	if (add[index]) volTarget->AddNode(volCooling, ncooling, new TGeoTranslation(0,0, zposition + CoatingZ + EmPlateWidth + CoolingZ/2 + CoatingZ + NPlates*myPlateWidth + AllPlateWidth - 0.3));
	ncooling++;
        
	//another emulsion after tantalium
	if (add[index]) volTarget->AddNode(volEmulsionFilm2, nreplica, new TGeoTranslation(0,0, zposition + CoatingZ + EmulsionThickness/2 + (NPlates)*myPlateWidth + AllPlateWidth - 0.3 + CoatingZ)); //BOTTOM
	if (add[index]) volTarget->AddNode(volEmulsionFilm2, nreplica, new TGeoTranslation(0,0, zposition + CoatingZ + 3 * EmulsionThickness/2 +PlasticBaseThickness+(NPlates)*myPlateWidth + AllPlateWidth - 0.3 + CoatingZ)); //TOP
	if (add[index]) volTarget->AddNode(volPlBase, nreplica, new TGeoTranslation(0,0, zposition + CoatingZ + EmulsionThickness + PlasticBaseThickness/2+(NPlates)*myPlateWidth + AllPlateWidth - 0.3 + CoatingZ)); //PLASTIC BASE
	nreplica++;
	zposition = zposition + AllPlateWidth - 0.3 + EmPlateWidth + CoolingZ + 2 * CoatingZ + (NPlates) * myPlateWidth;

	NPlates = 16;
	 for(Int_t n=0; n<NPlates+1; n++)
	   {
	     if (add[index]) volTarget->AddNode(volEmulsionFilm2, nreplica, new TGeoTranslation(0,0, zposition + CoatingZ + EmulsionThickness/2 + n*myPlateWidth)); //BOTTOM
	     if (add[index]) volTarget->AddNode(volEmulsionFilm, nreplica, new TGeoTranslation(0,0, zposition + CoatingZ + 3 * EmulsionThickness/2 +PlasticBaseThickness+n*myPlateWidth)); //TOP
	     if (add[index]) volTarget->AddNode(volPlBase, nreplica, new TGeoTranslation(0,0, zposition + CoatingZ + EmulsionThickness + PlasticBaseThickness/2+n*myPlateWidth)); //PLASTIC BASE
          nreplica++;
	   }
        if (add[index]) volTarget->AddNode(volCoating, ncoating, new TGeoTranslation(0,0,zposition + CoatingZ/2));
	ncoating++;
	for(Int_t n=0; n<NPlates; n++)
	  {
            //volTarget->AddNode(volCoating, 2*n , new TGeoTranslation(0,0,-zTarget/2+BrickPackageZ/2+ EmPlateWidth + CoatingZ/2 + n*myPlateWidth));
	    if (add[index]) volTarget->AddNode(volMol3mm, nmol3, new TGeoTranslation(0,0,zposition + CoatingZ + EmPlateWidth + 0.3/2 + n*myPlateWidth)); //LEAD
	    nmol3++;
	  }
	if (add[index]) volTarget->AddNode(volCoating, ncoating, new TGeoTranslation(0,0, zposition + CoatingZ + EmPlateWidth + CoatingZ/2 + NPlates*myPlateWidth));
	ncoating++;
	if (add[index]) volTarget->AddNode(volCooling, ncooling, new TGeoTranslation(0,0, zposition + CoatingZ + EmPlateWidth + CoolingZ/2 + CoatingZ + NPlates*myPlateWidth + AllPlateWidth - 0.3));
	ncooling++;
        
	//another emulsion after tantalium
	if (add[index]) volTarget->AddNode(volEmulsionFilm2, nreplica, new TGeoTranslation(0,0, zposition + CoatingZ + EmulsionThickness/2 + (NPlates)*myPlateWidth + AllPlateWidth - 0.3 + CoatingZ)); //BOTTOM
	if (add[index]) volTarget->AddNode(volEmulsionFilm2, nreplica, new TGeoTranslation(0,0, zposition + CoatingZ + 3 * EmulsionThickness/2 +PlasticBaseThickness+(NPlates)*myPlateWidth + AllPlateWidth - 0.3 + CoatingZ)); //TOP
	if (add[index]) volTarget->AddNode(volPlBase, nreplica, new TGeoTranslation(0,0, zposition + CoatingZ + EmulsionThickness + PlasticBaseThickness/2+(NPlates)*myPlateWidth + AllPlateWidth - 0.3 + CoatingZ)); //PLASTIC BASE
	nreplica++;
	zposition = zposition + AllPlateWidth - 0.3 + EmPlateWidth + CoolingZ + 2 * CoatingZ + (NPlates) * myPlateWidth;

	NPlates = 21;
	 for(Int_t n=0; n<NPlates+1; n++)
	   {
	     if (add[index]) volTarget->AddNode(volEmulsionFilm2, nreplica, new TGeoTranslation(0,0, zposition + CoatingZ + EmulsionThickness/2 + n*myPlateWidth)); //BOTTOM
	     if (add[index]) volTarget->AddNode(volEmulsionFilm, nreplica, new TGeoTranslation(0,0, zposition + CoatingZ + 3 * EmulsionThickness/2 +PlasticBaseThickness+n*myPlateWidth)); //TOP
	     if (add[index]) volTarget->AddNode(volPlBase, nreplica, new TGeoTranslation(0,0, zposition + CoatingZ + EmulsionThickness + PlasticBaseThickness/2+n*myPlateWidth)); //PLASTIC BASE
          nreplica++;
	   }
        if (add[index]) volTarget->AddNode(volCoating, ncoating, new TGeoTranslation(0,0,zposition + CoatingZ/2));
	ncoating++;
	for(Int_t n=0; n<NPlates; n++)
	  {
            //volTarget->AddNode(volCoating, 2*n , new TGeoTranslation(0,0,-zTarget/2+BrickPackageZ/2+ EmPlateWidth + CoatingZ/2 + n*myPlateWidth));
	    if (add[index]) volTarget->AddNode(volMol3mm, nmol3, new TGeoTranslation(0,0,zposition + CoatingZ + EmPlateWidth + 0.3/2 + n*myPlateWidth)); //LEAD
	    nmol3++;
	  }
	if (add[index]) volTarget->AddNode(volCoating, ncoating, new TGeoTranslation(0,0, zposition + CoatingZ + EmPlateWidth + CoatingZ/2 + NPlates*myPlateWidth));
	ncoating++;
	if (add[index+1]) volTarget->AddNode(volCooling, ncooling, new TGeoTranslation(0,0, zposition + CoatingZ + EmPlateWidth + CoolingZ/2 + CoatingZ + NPlates*myPlateWidth + AllPlateWidth - 0.3));
	ncooling++;
        
	//another emulsion after tantalium
	if (add[index]) volTarget->AddNode(volEmulsionFilm2, nreplica, new TGeoTranslation(0,0, zposition + CoatingZ + EmulsionThickness/2 + (NPlates)*myPlateWidth + AllPlateWidth - 0.3 + CoatingZ)); //BOTTOM
	if (add[index]) volTarget->AddNode(volEmulsionFilm2, nreplica, new TGeoTranslation(0,0, zposition + CoatingZ + 3 * EmulsionThickness/2 +PlasticBaseThickness+(NPlates)*myPlateWidth + AllPlateWidth - 0.3 + CoatingZ)); //TOP
	if (add[index]) volTarget->AddNode(volPlBase, nreplica, new TGeoTranslation(0,0, zposition + CoatingZ + EmulsionThickness + PlasticBaseThickness/2+(NPlates)*myPlateWidth + AllPlateWidth - 0.3 + CoatingZ)); //PLASTIC BASE
	nreplica++;
	zposition = zposition + AllPlateWidth - 0.3 + EmPlateWidth + CoolingZ + 2 * CoatingZ + (NPlates) * myPlateWidth;
      }
//2 da 48 e 1 da 63
      else{
	for (int i = 0; i < 2; i++){	  
	  if (add[index]) volTarget->AddNode(volCoating, ncoating,  new TGeoTranslation(0, 0, zposition + CoatingZ/2));
	  ncoating++;
	  if (add[index]) volTarget->AddNode(volMol3, nmegamol3,  new TGeoTranslation(0, 0, zposition + CoatingZ + 4.8/2.));
	  nmegamol3++;
	  if (add[index]) volTarget->AddNode(volCoating, ncoating,  new TGeoTranslation(0, 0, zposition+ CoatingZ + CoatingZ/2 + 4.8));
	  ncoating++;
	  if (add[index]) volTarget->AddNode(volCooling, ncooling,  new TGeoTranslation(0, 0, zposition + 2* CoatingZ + CoolingZ/2 + 4.8));
	  ncooling++;
	if (add[index])  zposition = zposition + (2 * CoatingZ + 4.8 + CoolingZ);
	}
	     if (add[index]) volTarget->AddNode(volCoating, ncoating,  new TGeoTranslation(0, 0, zposition + CoatingZ/2));
	     ncoating++;
	     if (add[index]) volTarget->AddNode(volMol4, nmegamol4,  new TGeoTranslation(0, 0, zposition + CoatingZ + 6.3/2.));
	     nmegamol4++;
	     if (add[index]) volTarget->AddNode(volCoating, ncoating,  new TGeoTranslation(0, 0, zposition+ CoatingZ + CoatingZ/2 + 6.3));
	     ncoating++;
	     if (add[index]) volTarget->AddNode(volCooling, ncooling,  new TGeoTranslation(0, 0, zposition + 2* CoatingZ + CoolingZ/2 + 6.3));
	     ncooling++;
	     zposition = zposition + (2 * CoatingZ + 6.3 + CoolingZ);
      }

      index++;

      //Run 4(26+26)
      if (activate[index]){
	NPlates = 26;
	for(Int_t n=0; n<NPlates+1; n++)
	  {
	    if (add[index]) volTarget->AddNode(volEmulsionFilm2, nreplica, new TGeoTranslation(0,0, zposition + CoatingZ + EmulsionThickness/2 + n*myPlateWidth)); //BOTTOM
	    if (add[index]) volTarget->AddNode(volEmulsionFilm, nreplica, new TGeoTranslation(0,0, zposition + CoatingZ + 3 * EmulsionThickness/2 +PlasticBaseThickness+n*myPlateWidth)); //TOP
	    if (add[index]) volTarget->AddNode(volPlBase, nreplica, new TGeoTranslation(0,0, zposition + CoatingZ + EmulsionThickness + PlasticBaseThickness/2+n*myPlateWidth)); //PLASTIC BASE
	    nreplica++;
	  }
	if (add[index]) volTarget->AddNode(volCoating, ncoating, new TGeoTranslation(0,0,zposition + CoatingZ/2));
	ncoating++;
	for(Int_t n=0; n<NPlates; n++)
	  {
            //volTarget->AddNode(volCoating, 2*n , new TGeoTranslation(0,0,-zTarget/2+BrickPackageZ/2+ EmPlateWidth + CoatingZ/2 + n*myPlateWidth));
	    if (add[index]) volTarget->AddNode(volMol3mm, nmol3, new TGeoTranslation(0,0,zposition + CoatingZ + EmPlateWidth + 0.3/2 + n*myPlateWidth));
	    nmol3++;
	  }
	if (add[index]) volTarget->AddNode(volCoating, ncoating, new TGeoTranslation(0,0, zposition + CoatingZ + EmPlateWidth + CoatingZ/2 + NPlates*myPlateWidth));
	if (add[index]) volTarget->AddNode(volCooling, ncooling, new TGeoTranslation(0,0, zposition + CoatingZ + EmPlateWidth + CoolingZ/2 + CoatingZ + NPlates*myPlateWidth + AllPlateWidth - 0.3 ));
	ncoating++;
	ncooling++;
	
	//another emulsion after tantalium
	if (add[index]) volTarget->AddNode(volEmulsionFilm2, nreplica, new TGeoTranslation(0,0, zposition + CoatingZ + EmulsionThickness/2 + (NPlates)*myPlateWidth + AllPlateWidth - 0.3 + CoatingZ)); //BOTTOM
	if (add[index]) volTarget->AddNode(volEmulsionFilm2, nreplica, new TGeoTranslation(0,0, zposition + CoatingZ + 3 * EmulsionThickness/2 +PlasticBaseThickness+(NPlates)*myPlateWidth + AllPlateWidth - 0.3 + CoatingZ)); //TOP
	if (add[index]) volTarget->AddNode(volPlBase, nreplica, new TGeoTranslation(0,0, zposition + CoatingZ + EmulsionThickness + PlasticBaseThickness/2+(NPlates)*myPlateWidth + AllPlateWidth - 0.3 + CoatingZ)); //PLASTIC BASE
	nreplica++;
	zposition = zposition + AllPlateWidth - 0.3 + EmPlateWidth + CoolingZ + 2 * CoatingZ + (NPlates) * myPlateWidth;

	NPlates = 26;
	for(Int_t n=0; n<NPlates+1; n++)
	  {
	    if (add[index]) volTarget->AddNode(volEmulsionFilm2, nreplica, new TGeoTranslation(0,0, zposition + CoatingZ + EmulsionThickness/2 + n*myPlateWidth)); //BOTTOM
	    if (add[index]) volTarget->AddNode(volEmulsionFilm, nreplica, new TGeoTranslation(0,0, zposition + CoatingZ + 3 * EmulsionThickness/2 +PlasticBaseThickness+n*myPlateWidth)); //TOP
	    if (add[index]) volTarget->AddNode(volPlBase, nreplica, new TGeoTranslation(0,0, zposition + CoatingZ + EmulsionThickness + PlasticBaseThickness/2+n*myPlateWidth)); //PLASTIC BASE
	    nreplica++;
	  }
	if (add[index]) volTarget->AddNode(volCoating, ncoating, new TGeoTranslation(0,0,zposition + CoatingZ/2));
	ncoating++;
	for(Int_t n=0; n<NPlates; n++)
	  {
            //volTarget->AddNode(volCoating, 2*n , new TGeoTranslation(0,0,-zTarget/2+BrickPackageZ/2+ EmPlateWidth + CoatingZ/2 + n*myPlateWidth));
	    if (add[index]) volTarget->AddNode(volMol3mm, nmol3, new TGeoTranslation(0,0,zposition + CoatingZ + EmPlateWidth + 0.3/2 + n*myPlateWidth));
	    nmol3++;
	  }
	if (add[index]) volTarget->AddNode(volCoating, ncoating, new TGeoTranslation(0,0, zposition + CoatingZ + EmPlateWidth + CoatingZ/2 + NPlates*myPlateWidth));
	if (add[index+1]) volTarget->AddNode(volCooling, ncooling, new TGeoTranslation(0,0, zposition + CoatingZ + EmPlateWidth + CoolingZ/2 + CoatingZ + NPlates*myPlateWidth + AllPlateWidth - 0.3 ));
	ncoating++;
	ncooling++;
	
	//another emulsion after tantalium
	if (add[index]) volTarget->AddNode(volEmulsionFilm2, nreplica, new TGeoTranslation(0,0, zposition + CoatingZ + EmulsionThickness/2 + (NPlates)*myPlateWidth + AllPlateWidth - 0.3 + CoatingZ)); //BOTTOM
	if (add[index]) volTarget->AddNode(volEmulsionFilm2, nreplica, new TGeoTranslation(0,0, zposition + CoatingZ + 3 * EmulsionThickness/2 +PlasticBaseThickness+(NPlates)*myPlateWidth + AllPlateWidth - 0.3 + CoatingZ)); //TOP
	if (add[index]) volTarget->AddNode(volPlBase, nreplica, new TGeoTranslation(0,0, zposition + CoatingZ + EmulsionThickness + PlasticBaseThickness/2+(NPlates)*myPlateWidth + AllPlateWidth - 0.3 + CoatingZ)); //PLASTIC BASE
	nreplica++;
	zposition = zposition + AllPlateWidth - 0.3 + EmPlateWidth + CoolingZ + 2 * CoatingZ + (NPlates) * myPlateWidth;
      }
      //2 of 78
    else{
      for (int i = 0; i < 2; i++){
       if (add[index]) volTarget->AddNode(volCoating, ncoating, new TGeoTranslation(0, 0, zposition + CoatingZ/2));
       ncoating++;
       if (add[index]) volTarget->AddNode(volMol1, nmegamol1, new TGeoTranslation(0, 0, zposition + CoatingZ + 7.8/2));
       nmegamol1++;
       if (add[index]) volTarget->AddNode(volCoating, ncoating, new TGeoTranslation(0, 0, zposition + CoatingZ + 7.8 + CoatingZ/2));
       if (add[index]) volTarget->AddNode(volCooling, ncooling, new TGeoTranslation(0, 0, zposition + 2 * CoatingZ  + 7.8 + CoolingZ/2));
       ncoating++;
       ncooling++;
       zposition = zposition + (2 * CoatingZ + 7.8 + CoolingZ);
      }
    }

      index++;
    
     //begin second part, with tungsten

      //Run 5 (16 + 26)
        
      if (activate[index]){
	NPlates = 16; 
	for(Int_t n=0; n<NPlates+1; n++)
	  {
	    if (add[index]) volTarget->AddNode(volEmulsionFilm2, nreplica, new TGeoTranslation(0,0,zposition + CoatingZ + EmulsionThickness/2 + n*myPlateWidth)); //BOTTOM
	    if (add[index]) volTarget->AddNode(volEmulsionFilm, nreplica, new TGeoTranslation(0,0, zposition + CoatingZ + 3 * EmulsionThickness/2 +PlasticBaseThickness+n*myPlateWidth)); //TOP
	    if (add[index]) volTarget->AddNode(volPlBase, nreplica, new TGeoTranslation(0,0,zposition + CoatingZ + EmulsionThickness + PlasticBaseThickness/2+n*myPlateWidth)); //PLASTIC BASE
	    nreplica++;
	  }
	if (add[index]) volTarget->AddNode(volCoating, ncoating, new TGeoTranslation(0,0,zposition + CoatingZ/2));
	ncoating++;
	for(Int_t n=0; n<NPlates; n++)
	  {
            //volTarget->AddNode(volCoating, 2*n , new TGeoTranslation(0,0,-zTarget/2+BrickPackageZ/2+ EmPlateWidth + CoatingZ/2 + n*myPlateWidth));
	    if (add[index]) volTarget->AddNode(volW3mm, nw3, new TGeoTranslation(0,0,zposition + CoatingZ + EmPlateWidth + 0.3/2 + n*myPlateWidth)); 
	    nw3++;
	  }
	if (add[index]) volTarget->AddNode(volCoating, ncoating, new TGeoTranslation(0,0,zposition + CoatingZ + EmPlateWidth + CoatingZ/2 + NPlates*myPlateWidth));
	if (add[index]) volTarget->AddNode(volCooling, ncooling, new TGeoTranslation(0,0,zposition + CoatingZ + EmPlateWidth + CoolingZ/2 + CoatingZ + NPlates*myPlateWidth + AllPlateWidth - 0.3));
	ncoating++;
	ncooling++;
	//zposition = zposition + EmPlateWidth + CoolingZ + 2 * CoatingZ + NPlates * myPlateWidth;
	
//another emulsion after tantalium
	if (add[index]) volTarget->AddNode(volEmulsionFilm2, nreplica, new TGeoTranslation(0,0, zposition + CoatingZ + EmulsionThickness/2 + (NPlates)*myPlateWidth + AllPlateWidth - 0.3 + CoatingZ)); //BOTTOM
	if (add[index]) volTarget->AddNode(volEmulsionFilm2, nreplica, new TGeoTranslation(0,0, zposition + CoatingZ + 3 * EmulsionThickness/2 +PlasticBaseThickness+(NPlates)*myPlateWidth + AllPlateWidth - 0.3 + CoatingZ)); //TOP
	if (add[index]) volTarget->AddNode(volPlBase, nreplica, new TGeoTranslation(0,0, zposition + CoatingZ + EmulsionThickness + PlasticBaseThickness/2+(NPlates)*myPlateWidth + AllPlateWidth - 0.3 + CoatingZ)); //PLASTIC BASE
	nreplica++;
	zposition = zposition + AllPlateWidth - 0.3 + EmPlateWidth + CoolingZ + 2 * CoatingZ + (NPlates) * myPlateWidth;

	NPlates = 26; 
	for(Int_t n=0; n<NPlates+1; n++)
	  {
	    if (add[index]) volTarget->AddNode(volEmulsionFilm2, nreplica, new TGeoTranslation(0,0,zposition + CoatingZ + EmulsionThickness/2 + n*myPlateWidth)); //BOTTOM
	    if (add[index]) volTarget->AddNode(volEmulsionFilm, nreplica, new TGeoTranslation(0,0, zposition + CoatingZ + 3 * EmulsionThickness/2 +PlasticBaseThickness+n*myPlateWidth)); //TOP
	    if (add[index]) volTarget->AddNode(volPlBase, nreplica, new TGeoTranslation(0,0,zposition + CoatingZ + EmulsionThickness + PlasticBaseThickness/2+n*myPlateWidth)); //PLASTIC BASE
	    nreplica++;
	  }
	if (add[index]) volTarget->AddNode(volCoating, ncoating, new TGeoTranslation(0,0,zposition + CoatingZ/2));
	ncoating++;
	for(Int_t n=0; n<NPlates; n++)
	  {
            //volTarget->AddNode(volCoating, 2*n , new TGeoTranslation(0,0,-zTarget/2+BrickPackageZ/2+ EmPlateWidth + CoatingZ/2 + n*myPlateWidth));
	    if (add[index]) volTarget->AddNode(volW3mm, nw3, new TGeoTranslation(0,0,zposition + CoatingZ + EmPlateWidth + 0.3/2 + n*myPlateWidth)); 
	    nw3++;
	  }
	if (add[index]) volTarget->AddNode(volCoating, ncoating, new TGeoTranslation(0,0,zposition + CoatingZ + EmPlateWidth + CoatingZ/2 + NPlates*myPlateWidth));
	if (add[index+1]) volTarget->AddNode(volCooling, ncooling, new TGeoTranslation(0,0,zposition + CoatingZ + EmPlateWidth + CoolingZ/2 + CoatingZ + NPlates*myPlateWidth + AllPlateWidth - 0.3));
	ncoating++;
	ncooling++;
	//zposition = zposition + EmPlateWidth + CoolingZ + 2 * CoatingZ + NPlates * myPlateWidth;
        //another emulsion after tantalium
	if (add[index]) volTarget->AddNode(volEmulsionFilm2, nreplica, new TGeoTranslation(0,0, zposition + CoatingZ + EmulsionThickness/2 + (NPlates)*myPlateWidth + AllPlateWidth - 0.3 + CoatingZ)); //BOTTOM
	if (add[index]) volTarget->AddNode(volEmulsionFilm2, nreplica, new TGeoTranslation(0,0, zposition + CoatingZ + 3 * EmulsionThickness/2 +PlasticBaseThickness+(NPlates)*myPlateWidth + AllPlateWidth - 0.3 + CoatingZ)); //TOP
	if (add[index]) volTarget->AddNode(volPlBase, nreplica, new TGeoTranslation(0,0, zposition + CoatingZ + EmulsionThickness + PlasticBaseThickness/2+(NPlates)*myPlateWidth + AllPlateWidth - 0.3 + CoatingZ)); //PLASTIC BASE
	nreplica++;
	zposition = zposition + AllPlateWidth - 0.3 + EmPlateWidth + CoolingZ + 2 * CoatingZ + (NPlates) * myPlateWidth;
     }
      //1 of 48 and 1 of 78
     else{
     if (add[index]) volTarget->AddNode(volCoating, ncoating,  new TGeoTranslation(0, 0, zposition + CoatingZ/2));
     ncoating++;
     if (add[index]) volTarget->AddNode(volW1, nmegaw1,  new TGeoTranslation(0, 0, zposition + CoatingZ + 4.8/2.));
     nmegaw1++;
     if (add[index]) volTarget->AddNode(volCoating, ncoating,  new TGeoTranslation(0, 0, zposition+ CoatingZ + CoatingZ/2 + 4.8));
     if (add[index]) volTarget->AddNode(volCooling, ncooling,  new TGeoTranslation(0, 0, zposition + 2* CoatingZ + CoolingZ/2 + 4.8));
     ncoating++;
     ncooling++;
     zposition = zposition + (2 * CoatingZ + 4.8 + CoolingZ);
     if (add[index]) volTarget->AddNode(volCoating, ncoating,  new TGeoTranslation(0, 0, zposition + CoatingZ/2));
     ncoating++;
     if (add[index]) volTarget->AddNode(volW2, nmegaw2,  new TGeoTranslation(0, 0, zposition + CoatingZ + 7.8/2.));
     nmegaw2++;
     if (add[index]) volTarget->AddNode(volCoating, ncoating,  new TGeoTranslation(0, 0, zposition+ CoatingZ + CoatingZ/2 + 7.8));
     if (add[index]) volTarget->AddNode(volCooling, ncooling,  new TGeoTranslation(0, 0, zposition + 2* CoatingZ + CoolingZ/2 + 7.8));
     ncoating++;
     ncooling++;
     zposition = zposition + (2 * CoatingZ + 7.8 + CoolingZ); 
     }
      
     index++;

     //Run 6
     NPlates = 33;   
     if (activate[index]){
       for(Int_t n=0; n<NPlates+1; n++)
	 {
	   if (add[index]) volTarget->AddNode(volEmulsionFilm2, nreplica, new TGeoTranslation(0,0,zposition + CoatingZ + EmulsionThickness/2 + n*myPlateWidth)); //BOTTOM
	   if (add[index]) volTarget->AddNode(volEmulsionFilm, nreplica, new TGeoTranslation(0,0, zposition + CoatingZ + 3 * EmulsionThickness/2 +PlasticBaseThickness+n*myPlateWidth)); //TOP
	   if (add[index]) volTarget->AddNode(volPlBase, nreplica, new TGeoTranslation(0,0,zposition + CoatingZ + EmulsionThickness + PlasticBaseThickness/2+n*myPlateWidth)); //PLASTIC BASE
           nreplica++;
	 }
        if (add[index]) volTarget->AddNode(volCoating, ncoating, new TGeoTranslation(0,0,zposition + CoatingZ/2));
	ncoating++;
	for(Int_t n=0; n<NPlates; n++)
	  {
            //volTarget->AddNode(volCoating, 2*n , new TGeoTranslation(0,0,-zTarget/2+BrickPackageZ/2+ EmPlateWidth + CoatingZ/2 + n*myPlateWidth));
	    if (add[index]) volTarget->AddNode(volW3mm, nw3, new TGeoTranslation(0,0,zposition + CoatingZ + EmPlateWidth + 0.3/2 + n*myPlateWidth));
	    nw3++;
	  }
	if (add[index]) volTarget->AddNode(volCoating, ncoating, new TGeoTranslation(0,0,zposition + CoatingZ + EmPlateWidth + CoatingZ/2 + NPlates*myPlateWidth));
	if (add[index+1]) volTarget->AddNode(volCooling, ncooling, new TGeoTranslation(0,0,zposition + CoatingZ + EmPlateWidth + CoolingZ/2 + CoatingZ + NPlates*myPlateWidth + AllPlateWidth - 0.3));
	ncoating++;
	ncooling++;
	//zposition = zposition + EmPlateWidth + CoolingZ + 2 * CoatingZ + NPlates * myPlateWidth;

        //another emulsion after tantalium
	if (add[index]) volTarget->AddNode(volEmulsionFilm2, nreplica, new TGeoTranslation(0,0, zposition + CoatingZ + EmulsionThickness/2 + (NPlates)*myPlateWidth + AllPlateWidth - 0.3 + CoatingZ)); //BOTTOM
	if (add[index]) volTarget->AddNode(volEmulsionFilm2, nreplica, new TGeoTranslation(0,0, zposition + CoatingZ + 3 * EmulsionThickness/2 +PlasticBaseThickness+(NPlates)*myPlateWidth + AllPlateWidth - 0.3 + CoatingZ)); //TOP
	if (add[index]) volTarget->AddNode(volPlBase, nreplica, new TGeoTranslation(0,0, zposition + CoatingZ + EmulsionThickness + PlasticBaseThickness/2+(NPlates)*myPlateWidth + AllPlateWidth - 0.3 + CoatingZ)); //PLASTIC BASE
	nreplica++;
	zposition = zposition + AllPlateWidth - 0.3 + EmPlateWidth + CoolingZ + 2 * CoatingZ + (NPlates) * myPlateWidth;
     }
     //1 da 98
     else{
       if (add[index]) volTarget->AddNode(volCoating, ncoating,  new TGeoTranslation(0, 0, zposition + CoatingZ/2));
       ncoating++;
       if (add[index]) volTarget->AddNode(volW3, nmegaw3,  new TGeoTranslation(0, 0, zposition + CoatingZ + 9.8/2.));
       nmegaw3++;
       if (add[index]) volTarget->AddNode(volCoating, ncoating,  new TGeoTranslation(0, 0, zposition+ CoatingZ + CoatingZ/2 + 9.8));
       if (add[index]) volTarget->AddNode(volCooling, ncooling,  new TGeoTranslation(0, 0, zposition + 2* CoatingZ + CoolingZ/2 + 9.8));
       ncoating++;
       ncooling++;
       zposition = zposition + (2 * CoatingZ + 9.8 + CoolingZ);
     }
     
     index++;

      //Run 7,8,9,10

     NPlates = 29;
     if (add[index]) volTarget->AddNode(volCoating, ncoating, new TGeoTranslation(0,0,zposition + CoatingZ/2));
     ncoating++;
    for (int i = 0; i < 4; i++){   
     if (activate[index]){
       for(Int_t n=0; n<NPlates+1; n++)
	 {
	   if (add[index]) volTarget->AddNode(volEmulsionFilm2, nreplica, new TGeoTranslation(0,0,zposition + CoatingZ + EmulsionThickness/2 + n*myPlateWidth)); //BOTTOM
	   if (add[index]) volTarget->AddNode(volEmulsionFilm, nreplica, new TGeoTranslation(0,0, zposition + CoatingZ + 3 * EmulsionThickness/2 +PlasticBaseThickness+n*myPlateWidth)); //TOP
	   if (add[index]) volTarget->AddNode(volPlBase, nreplica, new TGeoTranslation(0,0,zposition + CoatingZ + EmulsionThickness + PlasticBaseThickness/2+n*myPlateWidth)); //PLASTIC BASE
           nreplica++;
	 }
       //  if (add[index]) volTarget->AddNode(volCoating, ncoating, new TGeoTranslation(0,0,zposition + CoatingZ/2));
       //	ncoating++;
	for(Int_t n=0; n<NPlates; n++)
	  {
            //volTarget->AddNode(volCoating, 2*n , new TGeoTranslation(0,0,-zTarget/2+BrickPackageZ/2+ EmPlateWidth + CoatingZ/2 + n*myPlateWidth));
	    if (add[index]) volTarget->AddNode(volW3mm, nw3, new TGeoTranslation(0,0,zposition + CoatingZ + EmPlateWidth + 0.3/2 + n*myPlateWidth));
	    nw3++;
	  }
	if ((add[index]) && (i == 3)) {
	  volTarget->AddNode(volCoating, ncoating, new TGeoTranslation(0,0,zposition + CoatingZ + EmPlateWidth + CoatingZ/2 + NPlates*myPlateWidth));
	  ncoating++;//only the last one must have the coating
	}
	//if (add[index]) volTarget->AddNode(volCooling, ncooling, new TGeoTranslation(0,0,zposition + CoatingZ + EmPlateWidth + CoolingZ/2 + CoatingZ + NPlates*myPlateWidth)); 
	//ncoating++;
	//ncooling++;
	zposition = zposition + EmPlateWidth + NPlates * myPlateWidth; //niente cooling nè coating negli ultimi run
     }
      // 1 da 85.5
      else{
	//if (add[index]) volTarget->AddNode(volCoating, ncoating,  new TGeoTranslation(0, 0, zposition + CoatingZ/2));
	// ncoating++;
	if (add[index]) volTarget->AddNode(volW4, nmegaw4,  new TGeoTranslation(0, 0, zposition + CoatingZ + 8.7/2.));
	nmegaw4++;
	if (add[index] && (i == 3)){
	  volTarget->AddNode(volCoating, ncoating,  new TGeoTranslation(0, 0, zposition+ CoatingZ + CoatingZ/2 + 8.7));
	  ncoating++;
	}
	zposition = zposition +  8.7; //neither cooling either coating in these runs
      }
     index++;
    }
}
     
    





Bool_t  Box::ProcessHits(FairVolume* vol)
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
    
    // Create BoxPoint at exit of active volume
    if ( gMC->IsTrackExiting()    ||
        gMC->IsTrackStop()       ||
        gMC->IsTrackDisappeared()   ) {
        fTrackID  = gMC->GetStack()->GetCurrentTrackNumber();
        gMC->CurrentVolID(fVolumeID);

	//gGeoManager->PrintOverlaps();		
	
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
        stack->AddPoint(kBox1);
    }
    
    return kTRUE;
}



void Box::EndOfEvent()
{
    fBoxPointCollection->Clear();
}


void Box::Register()
{
    
    /** This will create a branch in the output tree called
     TargetPoint, setting the last parameter to kFALSE means:
     this collection will not be written to the file, it will exist
     only during the simulation.
     */
    
    FairRootManager::Instance()->Register("BoxPoint", "Box",
                                          fBoxPointCollection, kTRUE);
}

TClonesArray* Box::GetCollection(Int_t iColl) const
{
    if (iColl == 0) { return fBoxPointCollection; }
    else { return NULL; }
}

void Box::Reset()
{
    fBoxPointCollection->Clear();
}


BoxPoint* Box::AddHit(Int_t trackID,Int_t detID,
                           TVector3 pos, TVector3 mom,
                           Double_t time, Double_t length,
			    Double_t eLoss, Int_t pdgCode)
{
    TClonesArray& clref = *fBoxPointCollection;
    Int_t size = clref.GetEntriesFast();
    return new(clref[size]) BoxPoint(trackID,detID, pos, mom,
					time, length, eLoss, pdgCode);
}
ClassImp(Box)








