//
//  Box.cxx 
//  Target file: 6  different run configurations can be done, setting the number of the variable nrun.
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

#include <stddef.h>                     // for NULL
#include <iostream>                     // for operator<<, basic_ostream,etc
#include <string.h>

#include "TGeoTrd2.h"

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
    zBoxPosition = zBox;
    ch1r6 = false; //default configuration is with lead target
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

void Box::SetGapGeometry(Double_t distancePassive2ECC){ 
  distPas2ECC = distancePassive2ECC;
}

void Box::SetEmulsionParam(Double_t EmTh, Double_t EmX, Double_t EmY, Double_t PBTh, Double_t EPlW,Double_t PasSlabTh, Double_t AllPW)
{
    EmulsionThickness = EmTh;
    EmulsionX = EmX;
    EmulsionY = EmY;
    PlasticBaseThickness = PBTh;
    EmPlateWidth = EPlW;
    PassiveSlabThickness = PasSlabTh;
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


void Box::SetTargetParam(Double_t TX, Double_t TY, Double_t TZ){
  TargetX = TX; 
  TargetY = TY;
  TargetZ = TZ;
}

void Box::SetPassiveComposition(Double_t Molblock1Z, Double_t Molblock2Z, Double_t Molblock3Z, Double_t Molblock4Z, Double_t Wblock1Z, Double_t Wblock2Z, Double_t Wblock3Z, Double_t Wblock3_5Z, Double_t Wblock4Z){
  Mol1Z = Molblock1Z;
  Mol2Z = Molblock2Z;
  Mol3Z = Molblock3Z;
  Mol4Z = Molblock4Z;
  W1Z = Wblock1Z;
  W2Z = Wblock2Z;
  W3Z = Wblock3Z;
  W3_5Z = Wblock3_5Z;
  W4Z = Wblock4Z;
}

void Box::SetPassiveSampling(Double_t Passive3mmZ, Double_t Passive2mmZ, Double_t Passive1mmZ){
  Pas3mmZ = Passive3mmZ;
  Pas2mmZ = Passive2mmZ;
  Pas1mmZ = Passive1mmZ;
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

void Box::SetTargetDesign(Bool_t Julytarget){
  fJulytarget = Julytarget;
}

void Box::SetRunNumber(Int_t RunNumber){		
  nrun = RunNumber;
  if (RunNumber==16){ //special case, CH1 run with a tungsten target
    nrun = 1;
    ch1r6 = true;
  }		
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

void Box::AddEmulsionFilm(Double_t zposition, Int_t nreplica, TGeoVolume * volTarget, TGeoVolume * volEmulsionFilm, TGeoVolume   * volEmulsionFilm2, TGeoVolume * volPlBase){
   //emulsion IDs now go from 1 to a maximum of 57 for top layers, from 10000 to a maximum of 10057 for bottom layers
	 volTarget->AddNode(volEmulsionFilm2, nreplica+10000, new TGeoTranslation(0,0,zposition + EmulsionThickness/2)); //BOTTOM
	 volTarget->AddNode(volEmulsionFilm, nreplica, new TGeoTranslation(0,0,zposition +3 * EmulsionThickness/2 +PlasticBaseThickness)); //TOP
	 volTarget->AddNode(volPlBase, nreplica, new TGeoTranslation(0,0, zposition + EmulsionThickness + PlasticBaseThickness/2));
}

void Box::ConstructGeometry()
{
    InitMedium("tantalum");
    TGeoMedium *tantalum = gGeoManager->GetMedium("tantalum");       

    InitMedium("molybdenum");
    TGeoMedium *molybdenum = gGeoManager->GetMedium("molybdenum");

    InitMedium("tungsten");
    TGeoMedium *tungsten = gGeoManager->GetMedium("tungsten");
    
    InitMedium("Scintillator");
    TGeoMedium *scint =gGeoManager->GetMedium("Scintillator");

    InitMedium("H2O");
    TGeoMedium *water = gGeoManager->GetMedium("H2O");

    InitMedium("NuclearEmulsion");
    TGeoMedium *NEmu = gGeoManager->GetMedium("NuclearEmulsion");

    InitMedium("PlasticBase");
    TGeoMedium *PBase = gGeoManager->GetMedium("PlasticBase");

    InitMedium("lead");
    TGeoMedium *lead = gGeoManager->GetMedium("lead");    
    
    TGeoVolume *top= gGeoManager->GetTopVolume(); 

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

    
    if (fJulytarget == true){   
      //begin brick part (July testbeam)
      //Int_t NPlates = 19; //Number of doublets emulsion + Pb (two interaction lengths for 3 mm lead slabs)
      Int_t NPlates[6] = {28,28,56,56,56,56}; //when we consider 1 mm lead slabs
     
      Int_t NBlocks[6] = {1, 2, 2, 3, 4, 5}; //last active, other passive
      Int_t NBricks;

      if (nrun > 6 || nrun == 0) NBricks = 6; //Run 0 means 6 active bricks
      else NBricks = NBlocks[nrun-1];

      bool activate[NBricks];

      if (nrun > 0){ //passive red blocks followed by an ECC brick
      for (int i = 0; i<NBricks; i++) activate[i] = false;
      activate[NBricks-1]=true;
      }
      else  for (int i = 0; i<NBricks; i++) activate[i] = true;      
     
      Double_t zPasLead = NPlates[5] * PassiveSlabThickness;   
      if (nrun == 2) zPasLead = zPasLead/2; //in CH2 only half of a passive block      

      //computing target z for the different configurations

      if (nrun == 1) TargetZ = NPlates[nrun-1] * AllPlateWidth + EmPlateWidth; //CH1
      else if (nrun == 2) TargetZ = zPasLead + NPlates[nrun-1] * AllPlateWidth + EmPlateWidth; //CH2
      else if (nrun > 2 && nrun <= 6) TargetZ = NPlates[nrun-1] * AllPlateWidth + EmPlateWidth + zPasLead*(nrun-2) + distPas2ECC;//CH3-CH6      
      else if (nrun > 6) TargetZ = zPasLead * NBricks; //all passive 
      else TargetZ = (NPlates[5] * AllPlateWidth + EmPlateWidth)*NBricks;          

      TGeoVolumeAssembly *volTarget = new TGeoVolumeAssembly("volTarget");
      volTarget->SetLineColor(kCyan);
      volTarget->SetTransparency(1);
      
      top->AddNode(volTarget,1,new TGeoTranslation(0,0,zBoxPosition-TargetZ/2)); //Box ends at origin           
 
      TGeoVolume *volPasLead = NULL;
      if (nrun > 1){
      TGeoBBox *PasLead = new TGeoBBox("PasLead", EmulsionX/2, EmulsionY/2, zPasLead/2);
      volPasLead = new TGeoVolume("volPasLead",PasLead,lead);
      volPasLead->SetTransparency(1);
      volPasLead->SetLineColor(kRed);
      }
    
      TGeoBBox *Passiveslab = new TGeoBBox("Passiveslab", EmulsionX/2, EmulsionY/2, PassiveSlabThickness/2);
      TGeoVolume *volPassiveslab = new TGeoVolume("volPassiveslab",Passiveslab,lead);
      if (ch1r6) volPassiveslab->SetMedium(tungsten);
      volPassiveslab->SetTransparency(1);
      volPassiveslab->SetLineColor(kGray);
      
      Int_t nfilm = 1, nlead = 1, npassiveslab = 1;
      Double_t zpoint = -TargetZ/2;

      for (Int_t irun = 0; irun < NBricks; irun++){ //irun is the index, nrun is the number of the configuration run
        if (activate[irun]){
         
         if (nrun > 2) zpoint = zpoint + distPas2ECC;	  
	 
         for(Int_t n=0; n<NPlates[nrun-1]+1; n++) //adding emulsions
	    {
	      AddEmulsionFilm(zpoint + n*AllPlateWidth, nfilm, volTarget, volEmulsionFilm, volEmulsionFilm2, volPlBase);
	      nfilm++;
	    }
           
	 for(Int_t n=0; n<NPlates[nrun-1]; n++) //adding 1 mm lead plates
	    {
              volTarget->AddNode(volPassiveslab, npassiveslab, new TGeoTranslation(0,0,zpoint + EmPlateWidth + PassiveSlabThickness/2 + n*AllPlateWidth));
              npassiveslab++;
	    }	
	 zpoint = zpoint + NPlates[nrun-1] *AllPlateWidth + EmPlateWidth;
	}

	else if (volPasLead != NULL) { //only passive layer of lead, first is skipped
	 volTarget->AddNode(volPasLead,nlead,new TGeoTranslation(0,0,zpoint + zPasLead/2));
	 zpoint = zpoint + zPasLead;
         nlead++;
	}
	
      }    
   
    }
    else{
      //
      //begin SHIP replica target part
      Int_t nreplica = 0; //number of emulsion films activated;
      Int_t nmol3 = 0; //number of molybdenum blocks of 3mm;
      Int_t nmol2 = 0; //number of molybdenum blocks of 2mm;
      Int_t nmol1 = 0; //number of molybdenum blocks of 1mm;
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
      Int_t nmegaw3_5 = 0;
    
      Int_t nair = 0;    
     
      //volPlBase->SetLineColor(kBlue);	
      //starting to simulate SHiP target
      Double_t xTarget = TargetX;
      Double_t yTarget = TargetY;
      Double_t zTarget = TargetZ;
      
      Double_t zposition = 0;
      const int nbricks = 14;
      bool activate[nbricks];
      bool add[nbricks];
      
      //nrun = 1: first configuration, nrun = 2: second configuration, nrun > 2: all SHiP replica passive, nrun = 0: all SHiP replica, with the first 11 blocks active
      
      /*     for (int i = 0; i < nbricks;i++){
	     add[i] = false;
	     activate[i] = false;
      if ((nrun == 0) || (nrun > 2)) add[i] = true;  
      if ((nrun == 0) && (i < 3)) activate[i] = true;      
      }
      
      if ((nrun > 0) || (nrun < 2)) activate[nrun-1] = true;     
      
      for (int i = 0; i < nrun;i++){
      add[i] = true;
      }*/
      
      for (int i = 0; i < nbricks;i++){ //the number of possible configurations increased from 2 to 6
	add[i] = false;
	activate[i] = false;
	if ((nrun == 0) || (nrun > 6)) add[i] = true;  
	if ((nrun == 0) && (i < 7)) activate[i] = true;              
     }
      
      if ((nrun > 0) || (nrun < 6)) activate[nrun-1] = true;     
      
      for (int i = 0; i < nrun;i++){
	add[i] = true;
      }
      
      int index = 0;   
     
      TGeoVolumeAssembly *volTarget = new TGeoVolumeAssembly("volTarget");
      volTarget->SetTransparency(1);

      top->AddNode(volTarget,1,new TGeoTranslation(0,0,zBoxPosition-TargetZ/2));
      TGeoBBox *Cooling = new TGeoBBox("Cooling", CoolingX/2, CoolingY/2, CoolingZ/4); //water slips to cool the target (i split in half, to put an other emulsion in the middle
      TGeoVolume *volCooling = new TGeoVolume("volCooling", Cooling, PBase);
      volCooling->SetLineColor(kCyan);      
      
      TGeoBBox *Coating = new TGeoBBox("Coating", CoatingX/2, CoatingY/2, CoatingZ/2);
      TGeoVolume *volCoating = new TGeoVolume("volCoating", Coating, tantalum);
      volCoating->SetLineColor(kRed);      
      
      TGeoBBox *Mol3mm = new TGeoBBox("Mol3mm", xTarget/2, yTarget/2, PassiveSlabThickness/2);
      TGeoVolume *volMol3mm = new TGeoVolume("volMol3mm", Mol3mm, molybdenum);
      volMol3mm->SetLineColor(kGray);      
      
      TGeoBBox *Mol2mm = new TGeoBBox("Mol2mm", xTarget/2, yTarget/2, Pas2mmZ/2);
      TGeoVolume *volMol2mm = new TGeoVolume("volMol2mm", Mol2mm, molybdenum);
      volMol2mm->SetLineColor(kGray);     
      
      TGeoBBox *Mol1mm = new TGeoBBox("Mol1mm", xTarget/2, yTarget/2, Pas1mmZ/2);
      TGeoVolume *volMol1mm = new TGeoVolume("volMol1mm", Mol1mm, molybdenum);
      volMol1mm->SetLineColor(kGray);
      
      TGeoBBox *Mol1 = new TGeoBBox("Mol1", xTarget/2, yTarget/2, Mol1Z/2);
      TGeoVolume *volMol1 = new TGeoVolume("volMol1", Mol1, molybdenum); //1, then 2 at the end of the molybdenum row
      volMol1->SetLineColor(kGray);      

     TGeoBBox *Mol2 = new TGeoBBox("Mol2", xTarget/2, yTarget/2, Mol2Z/2); // 7
     TGeoVolume *volMol2 = new TGeoVolume("volMol2", Mol2, molybdenum);
     volMol2->SetLineColor(kGray);
     
     TGeoBBox *Mol3 = new TGeoBBox("Mol3", xTarget/2, yTarget/2, Mol3Z/2); // 2
     TGeoVolume *volMol3 = new TGeoVolume("volMol3", Mol3, molybdenum);
     volMol3->SetLineColor(kGray);
     
     TGeoBBox *Mol4 = new TGeoBBox("Mol4", xTarget/2, yTarget/2, Mol4Z/2); // 1
     TGeoVolume *volMol4 = new TGeoVolume("volMol4", Mol4, molybdenum);
     volMol4->SetLineColor(kGray);     
    
     TGeoBBox *W1 = new TGeoBBox("W1", xTarget/2, yTarget/2, W1Z/2); // 1
     TGeoVolume *volW1 = new TGeoVolume("volW1", W1, tungsten);
     volW1->SetLineColor(kSpring);     

     TGeoBBox *W2 = new TGeoBBox("W2", xTarget/2, yTarget/2, W2Z/2); // 1
     TGeoVolume *volW2 = new TGeoVolume("volW2", W2, tungsten);
     volW2->SetLineColor(kSpring);    

     TGeoBBox *W3 = new TGeoBBox("W3", xTarget/2, yTarget/2, W3Z/2); // 1
     TGeoVolume *volW3 = new TGeoVolume("volW3", W3, tungsten);
     volW3->SetLineColor(kSpring);   

     TGeoBBox *W4 = new TGeoBBox("W4", xTarget/2, yTarget/2, W4Z/2); // 1
     TGeoVolume *volW4 = new TGeoVolume("volW4", W4, tungsten);
     volW4->SetLineColor(kSpring);    
     
     TGeoBBox *W3_5 = new TGeoBBox("W3_5", xTarget/2, yTarget/2, W3_5Z/2); // recently added slab, I call it 3_5
     TGeoVolume *volW3_5 = new TGeoVolume("volW3_5", W3_5, tungsten);
     volW3_5->SetLineColor(kSpring);
     
     Double_t myPlateWidth = AllPlateWidth;
     Int_t NPlates;
       zposition = -zTarget/2; //zposition defines start position of each block
       if (activate[index]){
	 //RUN 1A
	 NPlates = 13;
       //most bottom emulsion film
	 if (add[index]) volTarget->AddNode(volEmulsionFilm2, nreplica, new TGeoTranslation(0,0,zposition + EmulsionThickness/2)); //BOTTOM
	 if (add[index]) volTarget->AddNode(volEmulsionFilm, nreplica, new TGeoTranslation(0,0,zposition +3 * EmulsionThickness/2 +PlasticBaseThickness)); //TOP
	 if (add[index]) volTarget->AddNode(volPlBase, nreplica, new TGeoTranslation(0,0, zposition + EmulsionThickness + PlasticBaseThickness/2)); //PLASTIC BASE
	 nreplica++;
	 
	 for(Int_t n=0; n<NPlates+1; n++)
	   {
	     if (add[index]) volTarget->AddNode(volEmulsionFilm2, nreplica, new TGeoTranslation(0,0,zposition + EmPlateWidth + CoatingZ + EmulsionThickness/2 + n*AllPlateWidth)); //BOTTOM
	     if (add[index]) volTarget->AddNode(volEmulsionFilm, nreplica, new TGeoTranslation(0,0,zposition + EmPlateWidth + CoatingZ + 3 * EmulsionThickness/2 +PlasticBaseThickness+n*AllPlateWidth)); //TOP
	     if (add[index]) volTarget->AddNode(volPlBase, nreplica, new TGeoTranslation(0,0, zposition + EmPlateWidth + CoatingZ + EmulsionThickness + PlasticBaseThickness/2+n*AllPlateWidth)); //PLASTIC BASE
	     nreplica++;
	   }
	 
	 if (add[index]) volTarget->AddNode(volCoating, ncoating, new TGeoTranslation(0,0, zposition + EmPlateWidth + CoatingZ/2));
	 ncoating++;
	 for(Int_t n=0; n<NPlates; n++)
	   {
	     
	     if (add[index]) volTarget->AddNode(volMol3mm, nmol3, new TGeoTranslation(0,0,zposition + EmPlateWidth + CoatingZ + EmPlateWidth + PassiveSlabThickness/2 + n*AllPlateWidth));
	     nmol3++;
	     
	   }
	 zposition =  zposition + 2 * EmPlateWidth + CoatingZ + (NPlates) * AllPlateWidth;
       }
       else{ //1A diventa passivo
	 if (add[index]) volTarget->AddNode(volCoating, ncoating, new TGeoTranslation(0, 0, zposition + CoatingZ/2));
	 ncoating++;
	 NPlates = 13;
	 for(Int_t n=0; n<NPlates; n++)
	   {	     
	     if (add[index]) volTarget->AddNode(volMol3mm, nmol3, new TGeoTranslation(0,0,zposition + CoatingZ + n*PassiveSlabThickness + PassiveSlabThickness/2.));
	     nmol3++;	     
	   }
	 zposition = zposition + CoatingZ + NPlates *PassiveSlabThickness;
       }             
       index++;
       //FINE RUN 1A//////////////////////////////////////////////////////////////////////
      

       //RUN 1B       
        if (activate[index]){
       NPlates = 12;
       //most bottom emulsion film
       if (add[index]) volTarget->AddNode(volEmulsionFilm2, nreplica, new TGeoTranslation(0,0,zposition + EmulsionThickness/2)); //BOTTOM
       if (add[index]) volTarget->AddNode(volEmulsionFilm, nreplica, new TGeoTranslation(0,0,zposition +3 * EmulsionThickness/2 +PlasticBaseThickness)); //TOP
       if (add[index]) volTarget->AddNode(volPlBase, nreplica, new TGeoTranslation(0,0, zposition + EmulsionThickness + PlasticBaseThickness/2)); //PLASTIC BASE
       nreplica++;
       
       for(Int_t n=0; n<NPlates+1; n++)
	 {
	   if (add[index]) volTarget->AddNode(volEmulsionFilm2, nreplica, new TGeoTranslation(0,0,zposition  + EmulsionThickness/2 + n*AllPlateWidth)); //BOTTOM
	   if (add[index]) volTarget->AddNode(volEmulsionFilm, nreplica, new TGeoTranslation(0,0,zposition + 3 * EmulsionThickness/2 +PlasticBaseThickness+n*AllPlateWidth)); //TOP
	   if (add[index]) volTarget->AddNode(volPlBase, nreplica, new TGeoTranslation(0,0, zposition + EmulsionThickness + PlasticBaseThickness/2+n*AllPlateWidth)); //PLASTIC BASE
           nreplica++;
	 }
       
	for(Int_t n=0; n<NPlates; n++)
	  {            
	    if (add[index]) volTarget->AddNode(volMol3mm, nmol3, new TGeoTranslation(0,0,zposition + EmPlateWidth + PassiveSlabThickness/2 + n*AllPlateWidth));
            nmol3++;
	  }

	//una in più da 2 mm
	if (add[index]) volTarget->AddNode(volMol2mm, nmol2, new TGeoTranslation(0,0,zposition + EmPlateWidth + NPlates *AllPlateWidth + Pas2mmZ/2));
	nmol2++;
	if (add[index]) volTarget->AddNode(volEmulsionFilm2, nreplica, new TGeoTranslation(0,0, zposition + EmulsionThickness/2 + (NPlates)*AllPlateWidth + EmPlateWidth + Pas2mmZ)); //BOTTOM
	if (add[index]) volTarget->AddNode(volEmulsionFilm, nreplica, new TGeoTranslation(0,0, zposition  + 3 * EmulsionThickness/2 +PlasticBaseThickness+(NPlates)*AllPlateWidth + EmPlateWidth + Pas2mmZ)); //TOP
	if (add[index]) volTarget->AddNode(volPlBase, nreplica, new TGeoTranslation(0,0, zposition + EmulsionThickness + PlasticBaseThickness/2+(NPlates)*AllPlateWidth + EmPlateWidth + Pas2mmZ)); //PLASTIC BASE
	nreplica++;
	zposition = zposition + EmPlateWidth + Pas2mmZ;
	
	if (add[index]) volTarget->AddNode(volCoating, ncoating, new TGeoTranslation(0,0,zposition + EmPlateWidth + CoatingZ/2 + NPlates*AllPlateWidth));
        ncoating++;
	//another emulsion after tantalium
        if (add[index]) volTarget->AddNode(volEmulsionFilm2, nreplica, new TGeoTranslation(0,0,zposition + EmulsionThickness/2 + (NPlates)*AllPlateWidth + EmPlateWidth + CoatingZ)); //BOTTOM
	   if (add[index]) volTarget->AddNode(volEmulsionFilm, nreplica, new TGeoTranslation(0,0,zposition + 3 * EmulsionThickness/2 +PlasticBaseThickness+(NPlates)*AllPlateWidth + EmPlateWidth + CoatingZ)); //TOP
	   if (add[index]) volTarget->AddNode(volPlBase, nreplica, new TGeoTranslation(0,0,zposition + EmulsionThickness + PlasticBaseThickness/2+(NPlates)*AllPlateWidth + EmPlateWidth + CoatingZ)); //PLASTIC BASE
           nreplica++;
        
	if (add[index+1]) volTarget->AddNode(volCooling, ncooling, new TGeoTranslation(0,0,zposition + CoolingZ/4 + CoatingZ + NPlates*AllPlateWidth + EmPlateWidth + EmPlateWidth));
	if (add[index+1]) ncooling++;	
	if (add[index+1]) volTarget->AddNode(volCooling, ncooling, new TGeoTranslation(0,0,zposition + EmPlateWidth + CoolingZ/2 + CoolingZ/4  + CoatingZ + NPlates*AllPlateWidth + EmPlateWidth));     
        if (add[index+1]) ncooling++;
        if (add[index+1]) volTarget->AddNode(volCoating, ncoating, new TGeoTranslation(0,0,zposition + EmPlateWidth + CoolingZ  + CoatingZ + NPlates*AllPlateWidth + EmPlateWidth + CoatingZ/2));
        if (add[index+1]) ncoating++;
        if (add[index+1]) zposition = zposition + CoolingZ + CoatingZ;		

	zposition =  zposition + EmPlateWidth + EmPlateWidth + CoatingZ + (NPlates) * AllPlateWidth;

	}
	else{
	  NPlates = 12;
	  for(Int_t n=0; n<NPlates; n++)
	    {	     
	      if (add[index]) volTarget->AddNode(volMol3mm, nmol3, new TGeoTranslation(0,0,zposition + n*PassiveSlabThickness + PassiveSlabThickness/2.));
	      nmol3++;	     
	    }

	  //another of 2mm
          if (add[index]) volTarget->AddNode(volMol2mm, nmol2, new TGeoTranslation(0,0,zposition + NPlates*PassiveSlabThickness + Pas2mmZ/2));
	  zposition = zposition + Pas2mmZ;

	  if (add[index]) volTarget->AddNode(volCoating, ncoating, new TGeoTranslation(0, 0, zposition + NPlates *PassiveSlabThickness + CoatingZ/2));
	  ncoating++;
	  if (add[index]) volTarget->AddNode(volCooling, ncooling, new TGeoTranslation(0, 0, zposition + CoatingZ  +  NPlates *PassiveSlabThickness + CoolingZ/4));
	  ncooling++;
	  if (add[index]) volTarget->AddNode(volCooling, ncooling, new TGeoTranslation(0, 0, zposition + CoatingZ  + NPlates *PassiveSlabThickness + CoolingZ/2 + CoolingZ/4));
	  ncooling++;
	  if (add[index]) volTarget->AddNode(volCoating, ncoating, new TGeoTranslation(0, 0, zposition + NPlates *PassiveSlabThickness + CoatingZ + CoolingZ + CoatingZ/2));
	  ncoating++;

	  zposition = zposition + 2 * CoatingZ + NPlates *PassiveSlabThickness + CoolingZ;
	}	             
        index++;
        //Fine RUN 1B

	//RUN 1C
	if (activate[index]){
	  NPlates = 7;
	  for(Int_t n=0; n<NPlates+1; n++)
	    {
	      if (add[index]) volTarget->AddNode(volEmulsionFilm2, nreplica, new TGeoTranslation(0,0, zposition + EmulsionThickness/2 + n*AllPlateWidth)); //BOTTOM
	      if (add[index]) volTarget->AddNode(volEmulsionFilm, nreplica, new TGeoTranslation(0,0, zposition + 3 * EmulsionThickness/2 +PlasticBaseThickness+n*AllPlateWidth)); //TOP
	      if (add[index]) volTarget->AddNode(volPlBase, nreplica, new TGeoTranslation(0,0, zposition + EmulsionThickness + PlasticBaseThickness/2+n*AllPlateWidth)); //PLASTIC BASE
	      nreplica++;
	    }
	  for(Int_t n=0; n<NPlates; n++)
	    {
	      if (add[index]) volTarget->AddNode(volMol3mm, nmol3, new TGeoTranslation(0,0,zposition + EmPlateWidth + PassiveSlabThickness/2 + n*AllPlateWidth)); //LEAD
	      nmol3++;
	    }
	  //una in più da 1 mm
	  if (add[index]) volTarget->AddNode(volMol1mm, nmol1, new TGeoTranslation(0,0,zposition + EmPlateWidth + NPlates *AllPlateWidth + Pas1mmZ/2));
	  nmol1++;
	  if (add[index]) volTarget->AddNode(volEmulsionFilm2, nreplica, new TGeoTranslation(0,0, zposition + EmulsionThickness/2 + (NPlates)*AllPlateWidth + EmPlateWidth + Pas1mmZ)); //BOTTOM
	  if (add[index]) volTarget->AddNode(volEmulsionFilm, nreplica, new TGeoTranslation(0,0, zposition  + 3 * EmulsionThickness/2 +PlasticBaseThickness+(NPlates)*AllPlateWidth  + EmPlateWidth + Pas1mmZ)); //TOP
	  if (add[index]) volTarget->AddNode(volPlBase, nreplica, new TGeoTranslation(0,0, zposition + EmulsionThickness + PlasticBaseThickness/2+(NPlates)*AllPlateWidth + EmPlateWidth + Pas1mmZ)); //PLASTIC BASE
	  nreplica++;
	  zposition = zposition + EmPlateWidth + Pas1mmZ;

	  if (add[index]) volTarget->AddNode(volCoating, ncoating, new TGeoTranslation(0,0, zposition + EmPlateWidth + CoatingZ/2 + NPlates*AllPlateWidth));
	  ncoating++;
	  //another emulsion after tantalium
	  if (add[index]) volTarget->AddNode(volEmulsionFilm2, nreplica, new TGeoTranslation(0,0, zposition + EmulsionThickness/2 + (NPlates)*AllPlateWidth + EmPlateWidth + CoatingZ)); //BOTTOM
	  if (add[index]) volTarget->AddNode(volEmulsionFilm, nreplica, new TGeoTranslation(0,0, zposition + 3 * EmulsionThickness/2 +PlasticBaseThickness+(NPlates)*AllPlateWidth + EmPlateWidth + CoatingZ)); //TOP
	  if (add[index]) volTarget->AddNode(volPlBase, nreplica, new TGeoTranslation(0,0, zposition + EmulsionThickness + PlasticBaseThickness/2+(NPlates)*AllPlateWidth + EmPlateWidth + CoatingZ)); //PLASTIC BASE
	  nreplica++;

	  if (add[index]) volTarget->AddNode(volCooling, ncooling, new TGeoTranslation(0,0, zposition + EmPlateWidth + CoolingZ/4 + CoatingZ + NPlates*AllPlateWidth + EmPlateWidth));
	  ncooling++;
	  //another emulsion in the middle of PET
	  if (add[index]) volTarget->AddNode(volEmulsionFilm2, nreplica, new TGeoTranslation(0,0, zposition + EmulsionThickness/2 + (NPlates)*AllPlateWidth + EmPlateWidth + CoatingZ + EmPlateWidth + CoolingZ/2)); //BOTTOM
	  if (add[index]) volTarget->AddNode(volEmulsionFilm, nreplica, new TGeoTranslation(0,0, zposition + 3 * EmulsionThickness/2 +PlasticBaseThickness+(NPlates)*AllPlateWidth + EmPlateWidth + CoatingZ+ EmPlateWidth + CoolingZ/2)); //TOP
	  if (add[index]) volTarget->AddNode(volPlBase, nreplica, new TGeoTranslation(0,0, zposition + EmulsionThickness + PlasticBaseThickness/2+(NPlates)*AllPlateWidth + EmPlateWidth + CoatingZ+ EmPlateWidth + CoolingZ/2)); //PLASTIC BASE
	  nreplica++;
	  if (add[index]) volTarget->AddNode(volCooling, ncooling, new TGeoTranslation(0,0, zposition + EmPlateWidth + CoolingZ/2 + CoolingZ/4  + CoatingZ + NPlates*AllPlateWidth + EmPlateWidth + EmPlateWidth));
	  ncooling++;          
	  
	  //another emulsion after PET (if present)
	  if (add[index]) volTarget->AddNode(volEmulsionFilm2, nreplica, new TGeoTranslation(0,0, zposition + EmulsionThickness/2 + (NPlates)*AllPlateWidth + EmPlateWidth + CoatingZ + EmPlateWidth + CoolingZ + EmPlateWidth)); //BOTTOM
	  if (add[index]) volTarget->AddNode(volEmulsionFilm, nreplica, new TGeoTranslation(0,0, zposition + 3 * EmulsionThickness/2 +PlasticBaseThickness+(NPlates)*AllPlateWidth + EmPlateWidth + CoatingZ+ EmPlateWidth + CoolingZ + EmPlateWidth)); //TOP
	  if (add[index]) volTarget->AddNode(volPlBase, nreplica, new TGeoTranslation(0,0, zposition + EmulsionThickness + PlasticBaseThickness/2+(NPlates)*AllPlateWidth + EmPlateWidth + CoatingZ+ EmPlateWidth + CoolingZ + EmPlateWidth)); //PLASTIC BASE
	  nreplica++;
	  zposition = zposition + EmPlateWidth + 3 * EmPlateWidth + CoolingZ + CoatingZ + (NPlates) * AllPlateWidth;
	  
	  NPlates = 7;
    for(Int_t n=0; n<NPlates+1; n++)
      {
	if (add[index]) volTarget->AddNode(volEmulsionFilm2, nreplica, new TGeoTranslation(0,0, zposition + CoatingZ + EmulsionThickness/2 + n*AllPlateWidth)); //BOTTOM
	if (add[index]) volTarget->AddNode(volEmulsionFilm, nreplica, new TGeoTranslation(0,0, zposition + CoatingZ + 3 * EmulsionThickness/2 +PlasticBaseThickness+n*AllPlateWidth)); //TOP
	if (add[index]) volTarget->AddNode(volPlBase, nreplica, new TGeoTranslation(0,0, zposition + CoatingZ + EmulsionThickness + PlasticBaseThickness/2+n*AllPlateWidth)); //PLASTIC BASE
	nreplica++;
      }
    if (add[index]) volTarget->AddNode(volCoating, ncoating, new TGeoTranslation(0,0,zposition + CoatingZ/2));
    ncoating++;
    for(Int_t n=0; n<NPlates; n++)
      {
	if (add[index]) volTarget->AddNode(volMol3mm, nmol3, new TGeoTranslation(0,0,zposition + CoatingZ + EmPlateWidth + PassiveSlabThickness/2 + n*AllPlateWidth)); //LEAD
	    nmol3++;
      }
    //una in più da 1 mm
    if (add[index]) volTarget->AddNode(volMol1mm, nmol1, new TGeoTranslation(0,0,zposition + CoatingZ + EmPlateWidth + NPlates *AllPlateWidth + Pas1mmZ/2));
    nmol1++;
    if (add[index]) volTarget->AddNode(volEmulsionFilm2, nreplica, new TGeoTranslation(0,0, zposition + CoatingZ + EmulsionThickness/2 + (NPlates)*AllPlateWidth + EmPlateWidth + Pas1mmZ)); //BOTTOM
    if (add[index]) volTarget->AddNode(volEmulsionFilm, nreplica, new TGeoTranslation(0,0, zposition + CoatingZ + 3 * EmulsionThickness/2 +PlasticBaseThickness+(NPlates)*AllPlateWidth + EmPlateWidth + Pas1mmZ)); //TOP
    if (add[index]) volTarget->AddNode(volPlBase, nreplica, new TGeoTranslation(0,0, zposition + CoatingZ + EmulsionThickness + PlasticBaseThickness/2+(NPlates)*AllPlateWidth + EmPlateWidth + Pas1mmZ)); //PLASTIC BASE
    nreplica++;
    
    
    if (add[index]) volTarget->AddNode(volCoating, ncoating, new TGeoTranslation(0,0, zposition + CoatingZ + EmPlateWidth + CoatingZ/2 + NPlates*AllPlateWidth + EmPlateWidth + Pas1mmZ ));
    ncoating++;
     //another emulsion after tantalium
    if (add[index]) volTarget->AddNode(volEmulsionFilm2, nreplica, new TGeoTranslation(0,0, zposition + 2 * CoatingZ + (NPlates)*AllPlateWidth + EmPlateWidth + EmPlateWidth + Pas1mmZ  + EmulsionThickness/2)); //BOTTOM
    if (add[index]) volTarget->AddNode(volEmulsionFilm, nreplica, new TGeoTranslation(0,0, zposition + CoatingZ +(NPlates)*AllPlateWidth + EmPlateWidth + CoatingZ + EmPlateWidth + Pas1mmZ + 3 * EmulsionThickness/2 +PlasticBaseThickness)); //TOP
    if (add[index]) volTarget->AddNode(volPlBase, nreplica, new TGeoTranslation(0,0, zposition + CoatingZ +(NPlates)*AllPlateWidth + EmPlateWidth + CoatingZ + EmPlateWidth + Pas1mmZ + EmulsionThickness + PlasticBaseThickness/2)); //PLASTIC BASE
    nreplica++;
   

    if (add[index+1]) volTarget->AddNode(volCooling, ncooling, new TGeoTranslation(0,0, zposition + CoatingZ + EmPlateWidth + CoolingZ/4 + CoatingZ + NPlates*AllPlateWidth + EmPlateWidth + EmPlateWidth + Pas1mmZ));
    ncooling++;
    if (add[index+1]) volTarget->AddNode(volCooling, ncooling, new TGeoTranslation(0,0, zposition + CoatingZ + CoolingZ/2 + CoolingZ/4  + CoatingZ + NPlates*AllPlateWidth + EmPlateWidth + EmPlateWidth + EmPlateWidth + Pas1mmZ));
    if (add[index+1]) ncooling++;
    if (add[index+1]) zposition = zposition + CoolingZ;

    if (add[index+1]) volTarget->AddNode(volCoating, ncoating, new TGeoTranslation(0,0, zposition + 2* CoatingZ  + NPlates*AllPlateWidth + EmPlateWidth + EmPlateWidth + EmPlateWidth + Pas1mmZ + CoatingZ/2));
    ncooling++;

    if (add[index+1]) zposition = zposition + CoatingZ;
    
  zposition = zposition + 2 * EmPlateWidth + 2 * CoatingZ + (NPlates) * AllPlateWidth + EmPlateWidth + Pas1mmZ;
	}
	else{
	  if (add[index]) volTarget->AddNode(volMol2, nmegamol2, new TGeoTranslation(0, 0, zposition + Mol2Z/2 ));
	 nmegamol2++;
	 if (add[index]) volTarget->AddNode(volCoating, ncoating, new TGeoTranslation(0, 0, zposition + Mol2Z + CoatingZ/2));
	 if (add[index]) volTarget->AddNode(volCooling, ncooling, new TGeoTranslation(0, 0, zposition + 1 * CoatingZ + Mol2Z + CoolingZ/4));
	 ncooling++;
	 if (add[index]) volTarget->AddNode(volCooling, ncooling, new TGeoTranslation(0, 0, zposition + 1 * CoatingZ + Mol2Z + CoolingZ/4 + CoolingZ/2));	
	 ncoating++;
	 ncooling++;
	 zposition = zposition + (1 * CoatingZ + Mol2Z + CoolingZ);
	 
	 if (add[index]) volTarget->AddNode(volCoating, ncoating, new TGeoTranslation(0, 0, zposition + CoatingZ/2 ));
	 ncoating++;
	 if (add[index]) volTarget->AddNode(volMol2, nmegamol2, new TGeoTranslation(0, 0, zposition + CoatingZ + Mol2Z/2 ));
	 nmegamol2++;
	 if (add[index]) volTarget->AddNode(volCoating, ncoating, new TGeoTranslation(0, 0, zposition + CoatingZ + Mol2Z + CoatingZ/2));
	  	 
	 if (add[index]) volTarget->AddNode(volCooling, ncooling, new TGeoTranslation(0, 0, zposition + 2 * CoatingZ + Mol2Z + CoolingZ/4));
	 ncooling++;	 
	 
	 if (add[index]) volTarget->AddNode(volCooling, ncooling, new TGeoTranslation(0, 0, zposition + 2 * CoatingZ + Mol2Z + CoolingZ/2 + CoolingZ/4));
         if (add[index]) volTarget->AddNode(volCoating, ncoating, new TGeoTranslation(0,0,zposition + 2 * CoatingZ + Mol2Z + CoolingZ + CoatingZ/2));
	 ncoating++;
	 ncooling++;
	 zposition = zposition + (3 * CoatingZ + Mol2Z + CoolingZ);        
	}
	
	index++;
        //FINE RUN 1C

	//RUN 2A, 2B
	  NPlates = 7;
	  for(int i = 0; i < 2; i++){
	    if(activate[index]){
	    for(Int_t n=0; n<NPlates+1; n++)
	      {
		if (add[index]) volTarget->AddNode(volEmulsionFilm2, nreplica, new TGeoTranslation(0,0, zposition + EmulsionThickness/2 + n*AllPlateWidth)); //BOTTOM
		if (add[index]) volTarget->AddNode(volEmulsionFilm, nreplica, new TGeoTranslation(0,0, zposition + 3 * EmulsionThickness/2 +PlasticBaseThickness+n*AllPlateWidth)); //TOP
		if (add[index]) volTarget->AddNode(volPlBase, nreplica, new TGeoTranslation(0,0, zposition + EmulsionThickness + PlasticBaseThickness/2+n*AllPlateWidth)); //PLASTIC BASE
		nreplica++;
	      }
	    for(Int_t n=0; n<NPlates; n++)
	      {
		if (add[index]) volTarget->AddNode(volMol3mm, nmol3, new TGeoTranslation(0,0,zposition + EmPlateWidth + PassiveSlabThickness/2 + n*AllPlateWidth)); //LEAD
	    nmol3++;
	      }

	    //una in più da 1 mm
	    if (add[index]) volTarget->AddNode(volMol1mm, nmol1, new TGeoTranslation(0,0,zposition + EmPlateWidth + NPlates *AllPlateWidth + Pas1mmZ/2));
	    nmol1++;
	    if (add[index]) volTarget->AddNode(volEmulsionFilm2, nreplica, new TGeoTranslation(0,0, zposition + EmulsionThickness/2 + (NPlates)*AllPlateWidth + EmPlateWidth + Pas1mmZ)); //BOTTOM
	    if (add[index]) volTarget->AddNode(volEmulsionFilm, nreplica, new TGeoTranslation(0,0, zposition + 3 * EmulsionThickness/2 +PlasticBaseThickness+(NPlates)*AllPlateWidth + EmPlateWidth + Pas1mmZ)); //TOP
	    if (add[index]) volTarget->AddNode(volPlBase, nreplica, new TGeoTranslation(0,0, zposition + EmulsionThickness + PlasticBaseThickness/2+(NPlates)*AllPlateWidth + EmPlateWidth + Pas1mmZ)); //PLASTIC BASE
	    nreplica++;
            zposition = zposition + EmPlateWidth + Pas1mmZ;

	    if (add[index]) volTarget->AddNode(volCoating, ncoating, new TGeoTranslation(0,0, zposition + EmPlateWidth + CoatingZ/2 + NPlates*AllPlateWidth));
	    ncoating++;
	    if (add[index]) volTarget->AddNode(volCooling, ncooling, new TGeoTranslation(0,0, zposition + EmPlateWidth + CoolingZ/4 + CoatingZ + NPlates*AllPlateWidth + EmPlateWidth));
	    ncooling++;
	    //another emulsion in the middle of PET
	    if (add[index]) volTarget->AddNode(volEmulsionFilm2, nreplica, new TGeoTranslation(0,0, zposition + EmulsionThickness/2 + (NPlates)*AllPlateWidth + EmPlateWidth + CoatingZ + EmPlateWidth + CoolingZ/2)); //BOTTOM
	    if (add[index]) volTarget->AddNode(volEmulsionFilm, nreplica, new TGeoTranslation(0,0, zposition + 3 * EmulsionThickness/2 +PlasticBaseThickness+(NPlates)*AllPlateWidth + EmPlateWidth + CoatingZ+ EmPlateWidth + CoolingZ/2)); //TOP
	    if (add[index]) volTarget->AddNode(volPlBase, nreplica, new TGeoTranslation(0,0, zposition + EmulsionThickness + PlasticBaseThickness/2+(NPlates)*AllPlateWidth + EmPlateWidth + CoatingZ+ EmPlateWidth + CoolingZ/2)); //PLASTIC BASE
	    nreplica++;
	    if (add[index]) volTarget->AddNode(volCooling, ncooling, new TGeoTranslation(0,0, zposition + EmPlateWidth + CoolingZ/4 + CoolingZ/2 + CoatingZ + NPlates*AllPlateWidth + EmPlateWidth + EmPlateWidth));
	    ncooling++;
	    
	    //another emulsion after tantalium
	    if (add[index]) volTarget->AddNode(volEmulsionFilm2, nreplica, new TGeoTranslation(0,0, zposition + EmulsionThickness/2 + (NPlates)*AllPlateWidth + EmPlateWidth + CoatingZ)); //BOTTOM
	    if (add[index]) volTarget->AddNode(volEmulsionFilm, nreplica, new TGeoTranslation(0,0, zposition + 3 * EmulsionThickness/2 +PlasticBaseThickness+(NPlates)*AllPlateWidth + EmPlateWidth + CoatingZ)); //TOP
	    if (add[index]) volTarget->AddNode(volPlBase, nreplica, new TGeoTranslation(0,0, zposition + EmulsionThickness + PlasticBaseThickness/2+(NPlates)*AllPlateWidth + EmPlateWidth + CoatingZ)); //PLASTIC BASE
	    nreplica++;
	    
	    //another emulsion after PET (if present)
	    if (add[index]) volTarget->AddNode(volEmulsionFilm2, nreplica, new TGeoTranslation(0,0, zposition + EmulsionThickness/2 + (NPlates)*AllPlateWidth + EmPlateWidth + CoatingZ + EmPlateWidth + CoolingZ + EmPlateWidth)); //BOTTOM
	    if (add[index]) volTarget->AddNode(volEmulsionFilm, nreplica, new TGeoTranslation(0,0, zposition + 3 * EmulsionThickness/2 +PlasticBaseThickness+(NPlates)*AllPlateWidth + EmPlateWidth + CoatingZ+ EmPlateWidth + CoolingZ + EmPlateWidth)); //TOP
	    if (add[index]) volTarget->AddNode(volPlBase, nreplica, new TGeoTranslation(0,0, zposition + EmulsionThickness + PlasticBaseThickness/2+(NPlates)*AllPlateWidth + EmPlateWidth + CoatingZ+ EmPlateWidth + CoolingZ + EmPlateWidth)); //PLASTIC BASE
	    nreplica++;

	    if (add[index]) volTarget->AddNode(volCoating, ncoating, new TGeoTranslation(0,0, zposition + EmPlateWidth + 3*EmPlateWidth + CoolingZ + CoatingZ + (NPlates) * AllPlateWidth + CoatingZ/2));
	    ncoating++;
	    
	    zposition = zposition + EmPlateWidth + 3*EmPlateWidth + CoolingZ + CoatingZ + (NPlates) * AllPlateWidth + CoatingZ;

	    for(Int_t n=0; n<NPlates+1; n++)
	      {
		if (add[index]) volTarget->AddNode(volEmulsionFilm2, nreplica, new TGeoTranslation(0,0, zposition + EmulsionThickness/2 + n*AllPlateWidth)); //BOTTOM
		if (add[index]) volTarget->AddNode(volEmulsionFilm, nreplica, new TGeoTranslation(0,0, zposition + 3 * EmulsionThickness/2 +PlasticBaseThickness+n*AllPlateWidth)); //TOP
		if (add[index]) volTarget->AddNode(volPlBase, nreplica, new TGeoTranslation(0,0, zposition + EmulsionThickness + PlasticBaseThickness/2+n*AllPlateWidth)); //PLASTIC BASE
		nreplica++;
	      }
	    for(Int_t n=0; n<NPlates; n++)
	      {
		if (add[index]) volTarget->AddNode(volMol3mm, nmol3, new TGeoTranslation(0,0,zposition + EmPlateWidth + PassiveSlabThickness/2 + n*AllPlateWidth)); //LEAD
	    nmol3++;
	      }

	    //una in più da 1 mm
	    if (add[index]) volTarget->AddNode(volMol1mm, nmol1, new TGeoTranslation(0,0,zposition + EmPlateWidth + NPlates *AllPlateWidth + Pas1mmZ/2));
	    nmol1++;
	    if (add[index]) volTarget->AddNode(volEmulsionFilm2, nreplica, new TGeoTranslation(0,0, zposition + EmulsionThickness/2 + (NPlates)*AllPlateWidth + EmPlateWidth + Pas1mmZ)); //BOTTOM
	    if (add[index]) volTarget->AddNode(volEmulsionFilm, nreplica, new TGeoTranslation(0,0, zposition + 3 * EmulsionThickness/2 +PlasticBaseThickness+(NPlates)*AllPlateWidth + EmPlateWidth + Pas1mmZ)); //TOP
	    if (add[index]) volTarget->AddNode(volPlBase, nreplica, new TGeoTranslation(0,0, zposition + EmulsionThickness + PlasticBaseThickness/2+(NPlates)*AllPlateWidth + EmPlateWidth + Pas1mmZ)); //PLASTIC BASE
	    nreplica++;
            zposition = zposition + EmPlateWidth + Pas1mmZ;

	    if (add[index]) volTarget->AddNode(volCoating, ncoating, new TGeoTranslation(0,0, zposition + EmPlateWidth + CoatingZ/2 + NPlates*AllPlateWidth));
	    ncoating++;
	    //emulsion after tantalum
	    if (add[index]) volTarget->AddNode(volEmulsionFilm2, nreplica, new TGeoTranslation(0,0, zposition + EmPlateWidth + CoatingZ + NPlates*AllPlateWidth + EmulsionThickness/2)); //BOTTOM
	    if (add[index]) volTarget->AddNode(volEmulsionFilm, nreplica, new TGeoTranslation(0,0, zposition + EmPlateWidth + CoatingZ + NPlates*AllPlateWidth + 3 * EmulsionThickness/2 +PlasticBaseThickness)); //TOP
	    if (add[index]) volTarget->AddNode(volPlBase, nreplica, new TGeoTranslation(0,0, zposition + EmPlateWidth + CoatingZ + NPlates*AllPlateWidth + EmulsionThickness + PlasticBaseThickness/2)); //PLASTIC BASE
	    nreplica++;	    	    

	    if (add[index+1]) volTarget->AddNode(volCooling, ncooling, new TGeoTranslation(0,0, zposition + 2 * EmPlateWidth + CoolingZ/4 + CoatingZ + NPlates*AllPlateWidth));
	    if (add[index+1]) ncooling++;            
	    if (add[index+1]) volTarget->AddNode(volCooling, ncooling, new TGeoTranslation(0,0, zposition + 2 * EmPlateWidth + CoolingZ/4 + CoolingZ/2 + CoatingZ + NPlates*AllPlateWidth));
	    if (add[index+1]) ncooling++;	    	  	   
	    if (add[index+1]) volTarget->AddNode(volCoating, ncoating, new TGeoTranslation(0,0, zposition + 2 * EmPlateWidth + CoolingZ + CoatingZ + (NPlates) * AllPlateWidth + CoatingZ/2));
	    if (add[index+1]) ncoating++;
            if (add[index+1]) zposition = zposition + CoatingZ + CoolingZ;	    	    


	    zposition = zposition + 2 * EmPlateWidth + (NPlates) * AllPlateWidth + CoatingZ;	    
	    }
	    else{
		if (add[index]) volTarget->AddNode(volMol2, nmegamol2, new TGeoTranslation(0, 0, zposition + Mol2Z/2 ));
		nmegamol2++;
		if (add[index]) volTarget->AddNode(volCoating, ncoating, new TGeoTranslation(0, 0, zposition + Mol2Z + CoatingZ/2));
		if (add[index]) volTarget->AddNode(volCooling, ncooling, new TGeoTranslation(0, 0, zposition + CoatingZ + Mol2Z + CoolingZ/4));
		ncooling++;
		if (add[index]) volTarget->AddNode(volCooling, ncooling, new TGeoTranslation(0, 0, zposition + CoatingZ + Mol2Z + CoolingZ/4 + CoolingZ/2));
		ncoating++;
		ncooling++;
                if (add[index]) volTarget->AddNode(volCoating, ncoating, new TGeoTranslation(0, 0, zposition + CoatingZ + CoolingZ + Mol2Z + CoatingZ/2));
                ncoating++;
		zposition = zposition + (2 * CoatingZ + 2.2 + CoolingZ);

		if (add[index]) volTarget->AddNode(volMol2, nmegamol2, new TGeoTranslation(0, 0, zposition + Mol2Z/2 ));
		nmegamol2++;
		if (add[index]) volTarget->AddNode(volCoating, ncoating, new TGeoTranslation(0, 0, zposition + Mol2Z + CoatingZ/2));
		if (add[index]) volTarget->AddNode(volCooling, ncooling, new TGeoTranslation(0, 0, zposition + CoatingZ + Mol2Z + CoolingZ/4));
		ncooling++;
		if (add[index]) volTarget->AddNode(volCooling, ncooling, new TGeoTranslation(0, 0, zposition + CoatingZ + Mol2Z + CoolingZ/4 + CoolingZ/2));
		ncoating++;
		ncooling++;
	        if (add[index]) volTarget->AddNode(volCoating, ncoating, new TGeoTranslation(0, 0, zposition + CoatingZ + Mol2Z + CoolingZ + CoatingZ/2));
                ncoating++;
		zposition = zposition + (2 * CoatingZ + Mol2Z + CoolingZ);
	    }	   
	    index++;
	    
	  }    
          //RUN 2C
	  if (activate[index]){
	    NPlates = 7;
	    for(Int_t n=0; n<NPlates+1; n++)
	      {
		if (add[index]) volTarget->AddNode(volEmulsionFilm2, nreplica, new TGeoTranslation(0,0, zposition + EmulsionThickness/2 + n*AllPlateWidth)); //BOTTOM
		if (add[index]) volTarget->AddNode(volEmulsionFilm, nreplica, new TGeoTranslation(0,0, zposition + 3 * EmulsionThickness/2 +PlasticBaseThickness+n*AllPlateWidth)); //TOP
		if (add[index]) volTarget->AddNode(volPlBase, nreplica, new TGeoTranslation(0,0, zposition + EmulsionThickness + PlasticBaseThickness/2+n*AllPlateWidth)); //PLASTIC BASE
		nreplica++;
	      }	    
	    // ncoating++;
	    for(Int_t n=0; n<NPlates; n++)
	      {
		//volTarget->AddNode(volCoating, 2*n , new TGeoTranslation(0,0,-zTarget/2+BrickPackageZ/2+ EmPlateWidth + CoatingZ/2 + n*AllPlateWidth));
		if (add[index]) volTarget->AddNode(volMol3mm, nmol3, new TGeoTranslation(0,0,zposition + EmPlateWidth + PassiveSlabThickness/2 + n*AllPlateWidth)); //LEAD
		nmol3++;
	      }
	    //una in più da 1 mm
	    if (add[index]) volTarget->AddNode(volMol1mm, nmol1, new TGeoTranslation(0,0,zposition + EmPlateWidth + NPlates *AllPlateWidth + Pas1mmZ/2));
	    nmol1++;
	    if (add[index]) volTarget->AddNode(volEmulsionFilm2, nreplica, new TGeoTranslation(0,0, zposition + EmulsionThickness/2 + (NPlates)*AllPlateWidth + EmPlateWidth + Pas1mmZ)); //BOTTOM
	    if (add[index]) volTarget->AddNode(volEmulsionFilm, nreplica, new TGeoTranslation(0,0, zposition + 3 * EmulsionThickness/2 +PlasticBaseThickness+(NPlates)*AllPlateWidth + EmPlateWidth + Pas1mmZ)); //TOP
	    if (add[index]) volTarget->AddNode(volPlBase, nreplica, new TGeoTranslation(0,0, zposition + EmulsionThickness + PlasticBaseThickness/2+(NPlates)*AllPlateWidth + EmPlateWidth + Pas1mmZ)); //PLASTIC BASE
	    nreplica++;
	    
	    if (add[index]) volTarget->AddNode(volCoating, ncoating, new TGeoTranslation(0,0, zposition + EmPlateWidth + CoatingZ/2 + NPlates*AllPlateWidth + EmPlateWidth + Pas1mmZ));
	    ncoating++;
	    if (add[index+1]) volTarget->AddNode(volCooling, ncooling, new TGeoTranslation(0,0, zposition + EmPlateWidth + CoolingZ/4 + CoatingZ + NPlates*AllPlateWidth + EmPlateWidth + EmPlateWidth + Pas1mmZ));
	    ncooling++;
	    //another emulsion after tantalium
	  if (add[index]) volTarget->AddNode(volEmulsionFilm2, nreplica, new TGeoTranslation(0,0, zposition  + EmulsionThickness/2 + (NPlates)*AllPlateWidth + EmPlateWidth + CoatingZ + EmPlateWidth + Pas1mmZ)); //BOTTOM
	  if (add[index]) volTarget->AddNode(volEmulsionFilm, nreplica, new TGeoTranslation(0,0, zposition + 3 * EmulsionThickness/2 +PlasticBaseThickness+(NPlates)*AllPlateWidth + EmPlateWidth + CoatingZ + EmPlateWidth + Pas1mmZ)); //TOP
	  if (add[index]) volTarget->AddNode(volPlBase, nreplica, new TGeoTranslation(0,0, zposition + EmulsionThickness + PlasticBaseThickness/2+(NPlates)*AllPlateWidth + EmPlateWidth + CoatingZ + EmPlateWidth + Pas1mmZ)); //PLASTIC BASE
	  nreplica++;

	    if (add[index+1]) volTarget->AddNode(volCooling, ncooling, new TGeoTranslation(0,0, zposition + CoolingZ/2 + CoolingZ/4 + CoatingZ + NPlates*AllPlateWidth + EmPlateWidth  + EmPlateWidth + EmPlateWidth + Pas1mmZ));	   
	  ncooling++;                    
	  
          if (add[index+1]) volTarget->AddNode(volCoating, ncoating, new TGeoTranslation(0,0,zposition +(NPlates)*AllPlateWidth + CoatingZ+ EmPlateWidth + CoolingZ + EmPlateWidth + EmPlateWidth + Pas1mmZ + CoatingZ/2));
	  ncoating++;	  	  

          if (add[index+1]) zposition = zposition + CoolingZ + CoatingZ;

	  zposition = zposition + EmPlateWidth + CoatingZ + (NPlates) * AllPlateWidth + EmPlateWidth + Pas1mmZ;	
	  
	}
	else{
	    if (add[index]) volTarget->AddNode(volMol2, nmegamol2, new TGeoTranslation(0, 0, zposition + Mol2Z/2 ));
	    nmegamol2++;
	    if (add[index]) volTarget->AddNode(volCoating, ncoating, new TGeoTranslation(0, 0, zposition + Mol2Z + CoatingZ/2));
            ncoating++;
	    if (add[index]) volTarget->AddNode(volCooling, ncooling, new TGeoTranslation(0, 0, zposition + CoatingZ + Mol2Z + CoolingZ/4));
	    ncooling++;
	    if (add[index]) volTarget->AddNode(volCooling, ncooling, new TGeoTranslation(0, 0, zposition + CoatingZ + Mol2Z + CoolingZ/4 + CoolingZ/2));
	    ncooling++;
	    if (add[index]) volTarget->AddNode(volCoating, ncoating, new TGeoTranslation(0, 0, zposition + CoatingZ + Mol2Z + CoolingZ + CoatingZ/2 ));
	    ncoating++;
	    zposition = zposition + (2 * CoatingZ + Mol2Z + CoolingZ);
	}       
	   index++;	   
   
      //Run 3 (16+16+20)
      
      if (activate[index]){
	NPlates = 16;
	for(Int_t n=0; n<NPlates+1; n++)
	  {
	    if (add[index]) volTarget->AddNode(volEmulsionFilm2, nreplica, new TGeoTranslation(0,0, zposition + EmulsionThickness/2 + n*AllPlateWidth)); //BOTTOM
	    if (add[index]) volTarget->AddNode(volEmulsionFilm, nreplica, new TGeoTranslation(0,0, zposition + 3 * EmulsionThickness/2 +PlasticBaseThickness+n*AllPlateWidth)); //TOP
	    if (add[index]) volTarget->AddNode(volPlBase, nreplica, new TGeoTranslation(0,0, zposition + EmulsionThickness + PlasticBaseThickness/2+n*AllPlateWidth)); //PLASTIC BASE
	    nreplica++;
	  }
	for(Int_t n=0; n<NPlates; n++)
	  {
            //volTarget->AddNode(volCoating, 2*n , new TGeoTranslation(0,0,-zTarget/2+BrickPackageZ/2+ EmPlateWidth + CoatingZ/2 + n*AllPlateWidth));
	    if (add[index]) volTarget->AddNode(volMol3mm, nmol3, new TGeoTranslation(0,0,zposition + EmPlateWidth + PassiveSlabThickness/2 + n*AllPlateWidth)); //LEAD
	    nmol3++;
	  }
	if (add[index]) volTarget->AddNode(volCoating, ncoating, new TGeoTranslation(0,0, zposition + EmPlateWidth + CoatingZ/2 + NPlates*AllPlateWidth));
	ncoating++;
	if (add[index]) volTarget->AddNode(volCooling, ncooling, new TGeoTranslation(0,0, zposition + EmPlateWidth + CoolingZ/4 + CoatingZ + NPlates*AllPlateWidth + EmPlateWidth));
	ncooling++;
	//another emulsion in the middle of PET
       if (add[index]) volTarget->AddNode(volEmulsionFilm2, nreplica, new TGeoTranslation(0,0, zposition + EmulsionThickness/2 + (NPlates)*AllPlateWidth + EmPlateWidth + CoatingZ + EmPlateWidth + CoolingZ/2)); //BOTTOM
       if (add[index]) volTarget->AddNode(volEmulsionFilm, nreplica, new TGeoTranslation(0,0, zposition + 3 * EmulsionThickness/2 +PlasticBaseThickness+(NPlates)*AllPlateWidth + EmPlateWidth + CoatingZ+ EmPlateWidth + CoolingZ/2)); //TOP
       if (add[index]) volTarget->AddNode(volPlBase, nreplica, new TGeoTranslation(0,0, zposition + EmulsionThickness + PlasticBaseThickness/2+(NPlates)*AllPlateWidth + EmPlateWidth + CoatingZ+ EmPlateWidth + CoolingZ/2)); //PLASTIC BASE
       nreplica++;
       if (add[index]) volTarget->AddNode(volCooling, ncooling, new TGeoTranslation(0,0, zposition + EmPlateWidth + CoolingZ/4+ CoolingZ/2 + CoatingZ + NPlates*AllPlateWidth + EmPlateWidth + EmPlateWidth));
	ncooling++;
	
	//another emulsion after tantalium
	if (add[index]) volTarget->AddNode(volEmulsionFilm2, nreplica, new TGeoTranslation(0,0, zposition + EmulsionThickness/2 + (NPlates)*AllPlateWidth + EmPlateWidth + CoatingZ)); //BOTTOM
	if (add[index]) volTarget->AddNode(volEmulsionFilm, nreplica, new TGeoTranslation(0,0, zposition + 3 * EmulsionThickness/2 +PlasticBaseThickness+(NPlates)*AllPlateWidth + EmPlateWidth + CoatingZ)); //TOP
	if (add[index]) volTarget->AddNode(volPlBase, nreplica, new TGeoTranslation(0,0, zposition + EmulsionThickness + PlasticBaseThickness/2+(NPlates)*AllPlateWidth + EmPlateWidth + CoatingZ)); //PLASTIC BASE
	nreplica++;

	 //another emulsion after PET (if present)
       if (add[index]) volTarget->AddNode(volEmulsionFilm2, nreplica, new TGeoTranslation(0,0, zposition + EmulsionThickness/2 + (NPlates)*AllPlateWidth + EmPlateWidth + CoatingZ + EmPlateWidth + CoolingZ + EmPlateWidth)); //BOTTOM
	  if (add[index]) volTarget->AddNode(volEmulsionFilm, nreplica, new TGeoTranslation(0,0, zposition + 3 * EmulsionThickness/2 +PlasticBaseThickness+(NPlates)*AllPlateWidth + EmPlateWidth + CoatingZ+ EmPlateWidth + CoolingZ + EmPlateWidth)); //TOP
	  if (add[index]) volTarget->AddNode(volPlBase, nreplica, new TGeoTranslation(0,0, zposition + EmulsionThickness + PlasticBaseThickness/2+(NPlates)*AllPlateWidth + EmPlateWidth + CoatingZ+ EmPlateWidth + CoolingZ + EmPlateWidth)); //PLASTIC BASE
           nreplica++;
	
	zposition = zposition + EmPlateWidth + 3*EmPlateWidth + CoolingZ + CoatingZ + (NPlates) * AllPlateWidth;

	NPlates = 16;
	 for(Int_t n=0; n<NPlates+1; n++)
	   {
	     if (add[index]) volTarget->AddNode(volEmulsionFilm2, nreplica, new TGeoTranslation(0,0, zposition + CoatingZ + EmulsionThickness/2 + n*AllPlateWidth)); //BOTTOM
	     if (add[index]) volTarget->AddNode(volEmulsionFilm, nreplica, new TGeoTranslation(0,0, zposition + CoatingZ + 3 * EmulsionThickness/2 +PlasticBaseThickness+n*AllPlateWidth)); //TOP
	     if (add[index]) volTarget->AddNode(volPlBase, nreplica, new TGeoTranslation(0,0, zposition + CoatingZ + EmulsionThickness + PlasticBaseThickness/2+n*AllPlateWidth)); //PLASTIC BASE
          nreplica++;
	   }
        if (add[index]) volTarget->AddNode(volCoating, ncoating, new TGeoTranslation(0,0,zposition + CoatingZ/2));
	ncoating++;
	for(Int_t n=0; n<NPlates; n++)
	  {            
	    if (add[index]) volTarget->AddNode(volMol3mm, nmol3, new TGeoTranslation(0,0,zposition + CoatingZ + EmPlateWidth + PassiveSlabThickness/2 + n*AllPlateWidth)); //LEAD
	    nmol3++;
	  }
	if (add[index]) volTarget->AddNode(volCoating, ncoating, new TGeoTranslation(0,0, zposition + CoatingZ + EmPlateWidth + CoatingZ/2 + NPlates*AllPlateWidth));
	ncoating++;
	if (add[index]) volTarget->AddNode(volCooling, ncooling, new TGeoTranslation(0,0, zposition + CoatingZ + EmPlateWidth + CoolingZ/4 + CoatingZ + NPlates*AllPlateWidth + EmPlateWidth));
	ncooling++;
	//another emulsion in the middle of PET
       if (add[index]) volTarget->AddNode(volEmulsionFilm2, nreplica, new TGeoTranslation(0,0, zposition + CoatingZ + EmulsionThickness/2 + (NPlates)*AllPlateWidth + EmPlateWidth + CoatingZ + EmPlateWidth + CoolingZ/2)); //BOTTOM
	  if (add[index]) volTarget->AddNode(volEmulsionFilm, nreplica, new TGeoTranslation(0,0, zposition + CoatingZ + 3 * EmulsionThickness/2 +PlasticBaseThickness+(NPlates)*AllPlateWidth + EmPlateWidth + CoatingZ+ EmPlateWidth + CoolingZ/2)); //TOP
	  if (add[index]) volTarget->AddNode(volPlBase, nreplica, new TGeoTranslation(0,0, zposition + CoatingZ + EmulsionThickness + PlasticBaseThickness/2+(NPlates)*AllPlateWidth + EmPlateWidth + CoatingZ+ EmPlateWidth + CoolingZ/2)); //PLASTIC BASE
           nreplica++;
	if (add[index]) volTarget->AddNode(volCooling, ncooling, new TGeoTranslation(0,0, zposition + CoatingZ + EmPlateWidth + CoolingZ/2 + CoolingZ/4 + CoatingZ + NPlates*AllPlateWidth + EmPlateWidth + EmPlateWidth));
	ncooling++;
        
	//another emulsion after tantalium
	if (add[index]) volTarget->AddNode(volEmulsionFilm2, nreplica, new TGeoTranslation(0,0, zposition + CoatingZ + EmulsionThickness/2 + (NPlates)*AllPlateWidth + EmPlateWidth + CoatingZ)); //BOTTOM
	if (add[index]) volTarget->AddNode(volEmulsionFilm, nreplica, new TGeoTranslation(0,0, zposition + CoatingZ + 3 * EmulsionThickness/2 +PlasticBaseThickness+(NPlates)*AllPlateWidth + EmPlateWidth + CoatingZ)); //TOP
	if (add[index]) volTarget->AddNode(volPlBase, nreplica, new TGeoTranslation(0,0, zposition + CoatingZ + EmulsionThickness + PlasticBaseThickness/2+(NPlates)*AllPlateWidth + EmPlateWidth + CoatingZ)); //PLASTIC BASE
	nreplica++;

	 //another emulsion after PET (if present)
       if (add[index]) volTarget->AddNode(volEmulsionFilm2, nreplica, new TGeoTranslation(0,0, zposition + CoatingZ + EmulsionThickness/2 + (NPlates)*AllPlateWidth + EmPlateWidth + CoatingZ + EmPlateWidth + CoolingZ + EmPlateWidth)); //BOTTOM
	  if (add[index]) volTarget->AddNode(volEmulsionFilm, nreplica, new TGeoTranslation(0,0, zposition + CoatingZ + 3 * EmulsionThickness/2 +PlasticBaseThickness+(NPlates)*AllPlateWidth + EmPlateWidth + CoatingZ+ EmPlateWidth + CoolingZ + EmPlateWidth)); //TOP
	  if (add[index]) volTarget->AddNode(volPlBase, nreplica, new TGeoTranslation(0,0, zposition + CoatingZ + EmulsionThickness + PlasticBaseThickness/2+(NPlates)*AllPlateWidth + EmPlateWidth + CoatingZ+ EmPlateWidth + CoolingZ + EmPlateWidth)); //PLASTIC BASE
           nreplica++;
	
	zposition = zposition + EmPlateWidth + 3*EmPlateWidth + CoolingZ + 2 * CoatingZ + (NPlates) * AllPlateWidth;

	NPlates = 20;
	 for(Int_t n=0; n<NPlates+1; n++)
	   {
	     if (add[index]) volTarget->AddNode(volEmulsionFilm2, nreplica, new TGeoTranslation(0,0, zposition + CoatingZ + EmulsionThickness/2 + n*AllPlateWidth)); //BOTTOM
	     if (add[index]) volTarget->AddNode(volEmulsionFilm, nreplica, new TGeoTranslation(0,0, zposition + CoatingZ + 3 * EmulsionThickness/2 +PlasticBaseThickness+n*AllPlateWidth)); //TOP
	     if (add[index]) volTarget->AddNode(volPlBase, nreplica, new TGeoTranslation(0,0, zposition + CoatingZ + EmulsionThickness + PlasticBaseThickness/2+n*AllPlateWidth)); //PLASTIC BASE
          nreplica++;
	   }
        if (add[index]) volTarget->AddNode(volCoating, ncoating, new TGeoTranslation(0,0,zposition + CoatingZ/2));
	ncoating++;
	for(Int_t n=0; n<NPlates; n++)
	  {            
	    if (add[index]) volTarget->AddNode(volMol3mm, nmol3, new TGeoTranslation(0,0,zposition + CoatingZ + EmPlateWidth + PassiveSlabThickness/2 + n*AllPlateWidth)); //LEAD
	    nmol3++;
	  }
	if (add[index]) volTarget->AddNode(volCoating, ncoating, new TGeoTranslation(0,0, zposition + CoatingZ + EmPlateWidth + CoatingZ/2 + NPlates*AllPlateWidth));
	ncoating++;
	if (add[index+1]) volTarget->AddNode(volCooling, ncooling, new TGeoTranslation(0,0, zposition + CoatingZ + EmPlateWidth + CoolingZ/4 + CoatingZ + NPlates*AllPlateWidth + EmPlateWidth));
	ncooling++;
	//another emulsion in the middle of PET
       if (add[index+1]) volTarget->AddNode(volEmulsionFilm2, nreplica, new TGeoTranslation(0,0, zposition + CoatingZ + EmulsionThickness/2 + (NPlates)*AllPlateWidth + EmPlateWidth + CoatingZ + EmPlateWidth + CoolingZ/2)); //BOTTOM
	  if (add[index+1]) volTarget->AddNode(volEmulsionFilm, nreplica, new TGeoTranslation(0,0, zposition + CoatingZ + 3 * EmulsionThickness/2 +PlasticBaseThickness+(NPlates)*AllPlateWidth + EmPlateWidth + CoatingZ+ EmPlateWidth + CoolingZ/2)); //TOP
	  if (add[index+1]) volTarget->AddNode(volPlBase, nreplica, new TGeoTranslation(0,0, zposition + CoatingZ + EmulsionThickness + PlasticBaseThickness/2+(NPlates)*AllPlateWidth + EmPlateWidth + CoatingZ+ EmPlateWidth + CoolingZ/2)); //PLASTIC BASE
           nreplica++;
	if (add[index+1]) volTarget->AddNode(volCooling, ncooling, new TGeoTranslation(0,0, zposition + CoatingZ + EmPlateWidth + CoolingZ/4 + CoolingZ/2 + CoatingZ + NPlates*AllPlateWidth + EmPlateWidth + EmPlateWidth));
	ncooling++;
        
	//another emulsion after tantalium
	if (add[index]) volTarget->AddNode(volEmulsionFilm2, nreplica, new TGeoTranslation(0,0, zposition + CoatingZ + EmulsionThickness/2 + (NPlates)*AllPlateWidth + EmPlateWidth + CoatingZ)); //BOTTOM
	if (add[index]) volTarget->AddNode(volEmulsionFilm, nreplica, new TGeoTranslation(0,0, zposition + CoatingZ + 3 * EmulsionThickness/2 +PlasticBaseThickness+(NPlates)*AllPlateWidth + EmPlateWidth + CoatingZ)); //TOP
	if (add[index]) volTarget->AddNode(volPlBase, nreplica, new TGeoTranslation(0,0, zposition + CoatingZ + EmulsionThickness + PlasticBaseThickness/2+(NPlates)*AllPlateWidth + EmPlateWidth + CoatingZ)); //PLASTIC BASE
	nreplica++;

	 //another emulsion after PET (if present)
       if (add[index+1]) volTarget->AddNode(volEmulsionFilm2, nreplica, new TGeoTranslation(0,0, zposition + CoatingZ + EmulsionThickness/2 + (NPlates)*AllPlateWidth + EmPlateWidth + CoatingZ + EmPlateWidth + CoolingZ + EmPlateWidth)); //BOTTOM
	  if (add[index+1]) volTarget->AddNode(volEmulsionFilm, nreplica, new TGeoTranslation(0,0, zposition + CoatingZ + 3 * EmulsionThickness/2 +PlasticBaseThickness+(NPlates)*AllPlateWidth + EmPlateWidth + CoatingZ+ EmPlateWidth + CoolingZ + EmPlateWidth)); //TOP
	  if (add[index+1]) volTarget->AddNode(volPlBase, nreplica, new TGeoTranslation(0,0, zposition + CoatingZ + EmulsionThickness + PlasticBaseThickness/2+(NPlates)*AllPlateWidth + EmPlateWidth + CoatingZ+ EmPlateWidth + CoolingZ + EmPlateWidth)); //PLASTIC BASE
	  nreplica++;
	  
	zposition = zposition + EmPlateWidth + 3 * EmPlateWidth + CoolingZ + 2 * CoatingZ + (NPlates) * AllPlateWidth;
      }
//2 da 48 e 1 da 63
      else{
	for (int i = 0; i < 2; i++){	  
	  if (add[index]) volTarget->AddNode(volMol3, nmegamol3,  new TGeoTranslation(0, 0, zposition + Mol3Z/2.));
	  nmegamol3++;
	  if (add[index]) volTarget->AddNode(volCoating, ncoating,  new TGeoTranslation(0, 0, zposition + CoatingZ/2 + Mol3Z));
	  ncoating++;
	  if (add[index]) volTarget->AddNode(volCooling, ncooling,  new TGeoTranslation(0, 0, zposition + CoatingZ + CoolingZ/4 + Mol3Z));
	  ncooling++;
	  if (add[index]) volTarget->AddNode(volCooling, ncooling,  new TGeoTranslation(0, 0, zposition + CoatingZ + CoolingZ/4 + CoolingZ/2 + Mol3Z));
	  ncooling++;
          if (add[index]) volTarget->AddNode(volCoating, ncoating,  new TGeoTranslation(0, 0, zposition + CoatingZ + CoolingZ + Mol3Z + CoatingZ/2));
	  ncoating++;
	if (add[index])  zposition = zposition + (2 * CoatingZ + Mol3Z + CoolingZ);
	}
	     if (add[index]) volTarget->AddNode(volMol4, nmegamol4,  new TGeoTranslation(0, 0, zposition + Mol4Z/2.));
	     nmegamol4++;
	     if (add[index]) volTarget->AddNode(volCoating, ncoating,  new TGeoTranslation(0, 0, zposition+ CoatingZ/2 + Mol4Z));
	     ncoating++;
	     if (add[index]) volTarget->AddNode(volCooling, ncooling,  new TGeoTranslation(0, 0, zposition + CoatingZ + CoolingZ/4 + Mol4Z));
	     ncooling++;
	     if (add[index]) volTarget->AddNode(volCooling, ncooling,  new TGeoTranslation(0, 0, zposition + CoatingZ + CoolingZ/4 + CoolingZ/2 + Mol4Z));
	     ncooling++;
	     zposition = zposition + (CoatingZ + Mol4Z + CoolingZ);
      }

      index++;    
      for (int i = 0; i < 2; i++){
       if (add[index]) volTarget->AddNode(volCoating, ncoating, new TGeoTranslation(0, 0, zposition + CoatingZ/2));
       ncoating++;
       if (add[index]) volTarget->AddNode(volMol1, nmegamol1, new TGeoTranslation(0, 0, zposition + CoatingZ + Mol1Z/2));
       nmegamol1++;
       if (add[index]) volTarget->AddNode(volCoating, ncoating, new TGeoTranslation(0, 0, zposition + CoatingZ + Mol1Z + CoatingZ/2));
       if (add[index]) volTarget->AddNode(volCooling, ncooling, new TGeoTranslation(0, 0, zposition + 2 * CoatingZ  + Mol1Z + CoolingZ/4));
       ncooling++;
       if (add[index]) volTarget->AddNode(volCooling, ncooling, new TGeoTranslation(0, 0, zposition + 2 * CoatingZ  + Mol1Z + CoolingZ/2 + CoolingZ/4));
       ncoating++;
       ncooling++;
       zposition = zposition + (2 * CoatingZ + Mol1Z + CoolingZ);
      }    

      index++;
    
     //begin second part, with tungsten

      
      //1 of 48 and 1 of 78
     if (add[index]) volTarget->AddNode(volCoating, ncoating,  new TGeoTranslation(0, 0, zposition + CoatingZ/2));
     ncoating++;
     if (add[index]) volTarget->AddNode(volW1, nmegaw1,  new TGeoTranslation(0, 0, zposition + CoatingZ + W1Z/2.));
     nmegaw1++;
     if (add[index]) volTarget->AddNode(volCoating, ncoating,  new TGeoTranslation(0, 0, zposition+ CoatingZ + CoatingZ/2 + W1Z));
     if (add[index]) volTarget->AddNode(volCooling, ncooling,  new TGeoTranslation(0, 0, zposition + 2* CoatingZ + CoolingZ/4 + W1Z));
     ncooling++;
     if (add[index]) volTarget->AddNode(volCooling, ncooling,  new TGeoTranslation(0, 0, zposition + 2* CoatingZ + CoolingZ/2 + CoolingZ/4 + W1Z));
     ncoating++;
     ncooling++;
     zposition = zposition + (2 * CoatingZ + W1Z + CoolingZ);
     if (add[index]) volTarget->AddNode(volCoating, ncoating,  new TGeoTranslation(0, 0, zposition + CoatingZ/2));
     ncoating++;
     if (add[index]) volTarget->AddNode(volW2, nmegaw2,  new TGeoTranslation(0, 0, zposition + CoatingZ + W2Z/2.));
     nmegaw2++;
     if (add[index]) volTarget->AddNode(volCoating, ncoating,  new TGeoTranslation(0, 0, zposition+ CoatingZ + CoatingZ/2 + W2Z));
     if (add[index]) volTarget->AddNode(volCooling, ncooling,  new TGeoTranslation(0, 0, zposition + 2* CoatingZ + CoolingZ/4 + W2Z));
     ncooling++;
     if (add[index]) volTarget->AddNode(volCooling, ncooling,  new TGeoTranslation(0, 0, zposition + 2* CoatingZ + CoolingZ/4 + CoolingZ/2 + W2Z));
     ncoating++;
     ncooling++;
     zposition = zposition + (2 * CoatingZ + W2Z + CoolingZ);      
      
     index++;

     //Run 6
     //1 da 98
       if (add[index]) volTarget->AddNode(volCoating, ncoating,  new TGeoTranslation(0, 0, zposition + CoatingZ/2));
       ncoating++;
       if (add[index]) volTarget->AddNode(volW3, nmegaw3,  new TGeoTranslation(0, 0, zposition + CoatingZ + W3Z/2.));
       nmegaw3++;
       if (add[index]) volTarget->AddNode(volCoating, ncoating,  new TGeoTranslation(0, 0, zposition+ CoatingZ + CoatingZ/2 + W3Z));
       if (add[index]) volTarget->AddNode(volCooling, ncooling,  new TGeoTranslation(0, 0, zposition + 2* CoatingZ + CoolingZ/4 + W3Z));
       ncooling++;
       if (add[index]) volTarget->AddNode(volCooling, ncooling,  new TGeoTranslation(0, 0, zposition + 2* CoatingZ + CoolingZ/2 + CoolingZ/4 + W3Z));
       ncoating++;
       ncooling++;
       zposition = zposition + (2 * CoatingZ + W3Z + CoolingZ);     
     
     index++;

     //new slab, W made of 19.70 mm
	if (add[index]) volTarget->AddNode(volCoating, ncoating,  new TGeoTranslation(0, 0, zposition + CoatingZ/2));
	ncoating++;
	if (add[index]) volTarget->AddNode(volW3_5, nmegaw3_5,  new TGeoTranslation(0, 0, zposition + CoatingZ + W3_5Z/2.));
	nmegaw3_5++;
       if (add[index]) volTarget->AddNode(volCoating, ncoating,  new TGeoTranslation(0, 0, zposition+ CoatingZ + CoatingZ/2 + W3_5Z));
       if (add[index]) volTarget->AddNode(volCooling, ncooling,  new TGeoTranslation(0, 0, zposition + 2* CoatingZ + CoolingZ/4 + W3_5Z));
       ncooling++;
       if (add[index]) volTarget->AddNode(volCooling, ncooling,  new TGeoTranslation(0, 0, zposition + 2* CoatingZ + CoolingZ/2 + CoolingZ/4 + W3_5Z));
       ncoating++;
       ncooling++;
       zposition = zposition +  W3_5Z + 2 * CoatingZ + CoolingZ; //neither cooling either coating in these runs
     
     
      //Run 7,8,9,10

     if (add[index]) volTarget->AddNode(volCoating, ncoating, new TGeoTranslation(0,0,zposition + CoatingZ/2));
     ncoating++;
    for (int i = 0; i < 4; i++){        
      // 1 da 85.5
	if (add[index]) volTarget->AddNode(volCoating, ncoating,  new TGeoTranslation(0, 0, zposition + CoatingZ/2));
	ncoating++;
	if (add[index]) volTarget->AddNode(volW4, nmegaw4,  new TGeoTranslation(0, 0, zposition + CoatingZ + W4Z/2.));
	nmegaw4++;
       if (add[index] && i < 3) volTarget->AddNode(volCoating, ncoating,  new TGeoTranslation(0, 0, zposition+ CoatingZ + CoatingZ/2 + W4Z));
       if (add[index] && i < 3) volTarget->AddNode(volCooling, ncooling,  new TGeoTranslation(0, 0, zposition + 2* CoatingZ + CoolingZ/4 + W4Z));
       ncooling++;
       if (add[index] && i < 3) volTarget->AddNode(volCooling, ncooling,  new TGeoTranslation(0, 0, zposition + 2* CoatingZ + CoolingZ/2 + CoolingZ/4 + W4Z));
       ncoating++;
       ncooling++;
	zposition = zposition +  W4Z + 2 * CoatingZ + CoolingZ; //neither cooling either coating in these runs      
	index++;
    }
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








