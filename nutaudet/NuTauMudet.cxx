#include "NuTauMudet.h"
#include "ShipRpcPoint.h"
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
#include "TParticle.h"
#include "TVector3.h"

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

NuTauMudet::NuTauMudet()
  : FairDetector("NuTauMudet",kTRUE, ktauRpc),
    fTrackID(-1),
    fPdgCode(),
    fVolumeID(-1),
    fPos(),
    fMom(),
    fTime(-1.),
    fLength(-1.),
    fELoss(-1),
    fShipRpcPointCollection(new TClonesArray("ShipRpcPoint"))
{
}

NuTauMudet::NuTauMudet(const char* name, const Double_t Zcenter,Bool_t Active,const char* Title)
  : FairDetector(name, Active, ktauRpc),
    fTrackID(-1),
    fPdgCode(),
    fVolumeID(-1),
    fPos(),
    fMom(),
    fTime(-1.),
    fLength(-1.),
    fELoss(-1),
    fShipRpcPointCollection(new TClonesArray("ShipRpcPoint"))
{
  fZcenter = Zcenter;
}

void NuTauMudet::SetDesign(Int_t Design)
{  
  fDesign = Design;
  cout <<" Mag Spectro Design "<< fDesign<<endl;
}

void NuTauMudet::SetTotDimensions(Double_t X, Double_t Y, Double_t Z)
{  
  fXtot = X;
  fYtot = Y;
  fZtot = Z;
}

void NuTauMudet::SetFeDimensions(Double_t X, Double_t Y, Double_t Z)
{  
  fXFe = X;
  fYFe = Y;
  fZFe = Z;
}

void NuTauMudet::SetRpcDimDifferences(Double_t deltax, Double_t deltay) //now the last RPCs and iron slabs are larger than the others
{
  fdeltax = deltax;
  fdeltay = deltay;
}

void NuTauMudet::SetRpcDimensions(Double_t X, Double_t Y, Double_t Z)
{  
  fXRpc = X;
  fYRpc = Y;
  fZRpc = Z;
}

void NuTauMudet::SetRpcGasDimensions(Double_t X, Double_t Y, Double_t Z)
{  
  fXGas = X;
  fYGas = Y;
  fZGas = Z;
}

void NuTauMudet::SetRpcPETDimensions(Double_t X, Double_t Y, Double_t Z)
{  
  fXPet = X;
  fYPet = Y;
  fZPet = Z;
}

void NuTauMudet::SetRpcElectrodeDimensions(Double_t X, Double_t Y, Double_t Z)
{  
  fXEle = X;
  fYEle = Y;
  fZEle = Z;
}

void NuTauMudet::SetRpcStripDimensions(Double_t X, Double_t Y, Double_t Z)
{  
  fXStrip = X;
  fYStrip = Y;
  fZStrip = Z;
}

void NuTauMudet::SetReturnYokeDimensions(Double_t X, Double_t Y, Double_t Z)
{  
  fXRyoke = X;
  fYRyoke = Y;
  fZRyoke = Z;
}

void NuTauMudet::SetSmallerYokeDimensions(Double_t X, Double_t Y, Double_t Z)
{  
  fXRyoke_s = X;
  fYRyoke_s = Y;
  fZRyoke_s = Z;
}

void NuTauMudet::SetMagneticField(Double_t B)
{
  fField =B;
}

void NuTauMudet::SetGapDownstream(Double_t Gap)
{
  fGapDown = Gap;
}

void NuTauMudet::SetGapMiddle(Double_t Gap)
{
  fGapMiddle = Gap;
}

void NuTauMudet::SetZDimensionArm(Double_t Z)
{
  fZArm = Z;
}

void NuTauMudet::SetNFeInArm(Int_t N)
{
  fNFe = N;
}

void NuTauMudet::SetNRpcInArm(Int_t N)
{
  fNRpc = N;
}

void NuTauMudet::SetCoilParameters(Double_t CoilH, Double_t CoilW, Int_t N, Double_t CoilG)
{
  fCoilH = CoilH;
  fCoilW = CoilW;
  fCoilGap = CoilG;
  fNCoil = N;
}


void NuTauMudet::SetPillarDimensions(Double_t X, Double_t Y, Double_t Z)
{
  fPillarX = X;
  fPillarY = Y;
  fPillarZ = Z;
}


NuTauMudet::~NuTauMudet()
{
  if (fShipRpcPointCollection) {
    fShipRpcPointCollection->Delete();
    delete fShipRpcPointCollection;
  }
}

void NuTauMudet::Initialize()
{
  FairDetector::Initialize();
}

// -----   Private method InitMedium 
Int_t NuTauMudet::InitMedium(const char* name)
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

void NuTauMudet::ConstructGeometry()
{
  TGeoVolume *top = gGeoManager->GetTopVolume();
  TGeoVolumeAssembly *tTauNuDet = new TGeoVolumeAssembly("tTauNuDet");
  top->AddNode(tTauNuDet, 1, new TGeoTranslation(0, 0, 0));

  InitMedium("RPCgas");
  TGeoMedium *RPCmat =gGeoManager->GetMedium("RPCgas");
   
  InitMedium("vacuum");
  TGeoMedium *vacuum =gGeoManager->GetMedium("vacuum");
    
  InitMedium("Bakelite");
  TGeoMedium *bakelite =gGeoManager->GetMedium("Bakelite");  

  InitMedium("iron");
  TGeoMedium *Iron =gGeoManager->GetMedium("iron");

  InitMedium("steel");
  TGeoMedium *Steel =gGeoManager->GetMedium("steel");
    
  InitMedium("copper");
  TGeoMedium *Cu =gGeoManager->GetMedium("copper");
    
  InitMedium("Concrete");
  TGeoMedium *Conc =gGeoManager->GetMedium("Concrete");
    
  TGeoUniformMagField *retFieldU    = new TGeoUniformMagField(0.,0.,-fField); //magnetic field up return yoke
  TGeoUniformMagField *retFieldL   = new TGeoUniformMagField(0.,0.,fField); //magnetic field low return yoke
    
  Double_t d = 0;

  if(fDesign!=3)
    {
      TGeoBBox *MudetBox = new TGeoBBox("NuTauMudetBox", fXRyoke/2, fYtot/2, fZtot/2);
      TGeoVolume *volMudetBox = new TGeoVolume("volNuTauMudet", MudetBox, vacuum);
      tTauNuDet->AddNode(volMudetBox, 1, new TGeoTranslation(0,10*cm,fZcenter));
  
      
      TGeoBBox *UpYokeBox = new TGeoBBox("UpYokeBox", fXRyoke/2, fYRyoke/2, fZRyoke/2);
      TGeoVolume *volUpYoke = new TGeoVolume("volUpYoke",UpYokeBox,vacuum);
      volMudetBox->AddNode(volUpYoke,1,new TGeoTranslation(0,fYtot/2 - fYRyoke/2,0));
      volUpYoke->SetField(retFieldU);
    
    
      TGeoBBox *FeYoke = new TGeoBBox("FeYoke",fXtot/2, fYRyoke/2, fZArm/2);
      TGeoVolume *volFeYoke = new TGeoVolume("volFeYoke",FeYoke,Iron);
      volFeYoke->SetLineColor(kGray+1);
  
      TGeoBBox *FeYoke1 = new TGeoBBox("FeYoke1",fXtot/2, fYRyoke_s/2, fZRyoke_s/2);
      TGeoVolume *volFeYoke1 = new TGeoVolume("volFeYoke1",FeYoke1,Iron);
      volFeYoke1->SetLineColor(kGray+1);
    
      TGeoBBox *CoilContainer = new TGeoBBox("CoilContainer",fXtot/2, fCoilH/2, 40*cm);
      TGeoVolume *volCoilContainer = new TGeoVolume("volCoilContainer",CoilContainer,vacuum);
    
      TGeoBBox *Coil = new TGeoBBox("Coil",fXtot/2, fCoilH/2, fCoilW/2);
      TGeoVolume *volCoil = new TGeoVolume("volCoil",Coil,Cu);
      volCoil->SetLineColor(kOrange -5);
      for(int i = 0; i < fNCoil; i++)
	{
	  volCoilContainer->AddNode(volCoil, i, new TGeoTranslation(0,0, -40*cm + fCoilW/2 + i*(fCoilGap + fCoilW)));
	}
    
      //vertical coils
      TGeoBBox *CoilV = new TGeoBBox("CoilV",fCoilH/2, fYRyoke/2 , fCoilW/2);
      TGeoVolume *volCoilV = new TGeoVolume("volCoilV",CoilV,Cu);
      volCoilV->SetLineColor(kOrange -5);
      for(int i = 0; i < fNCoil; i++)
	{
	  volUpYoke->AddNode(volCoilV, i, new TGeoTranslation(fXRyoke/2 - fCoilH/2,0, -40*cm + fCoilW/2 + i*(fCoilGap + fCoilW)));
	}
      for(int i = 0; i < fNCoil; i++)
	{
	  volUpYoke->AddNode(volCoilV, i, new TGeoTranslation(-fXRyoke/2 + fCoilH/2,0, -40*cm + fCoilW/2 + i*(fCoilGap + fCoilW)));
	}

      //cout <<"fZArm: " << fZArm<< endl;
    
      volUpYoke->AddNode(volFeYoke,1, new TGeoTranslation(0,0,- (fZArm + fGapMiddle)/2));
      volUpYoke->AddNode(volFeYoke,2, new TGeoTranslation(0,0,(fZArm + fGapMiddle)/2));
      volUpYoke->AddNode(volFeYoke1,1,new TGeoTranslation(0,0,0));
      volUpYoke->AddNode(volCoilContainer,1,new TGeoTranslation(0,fYRyoke/2 - fCoilH/2,0)); //up
      volUpYoke->AddNode(volCoilContainer,2,new TGeoTranslation(0,-fYRyoke/2 + fCoilH/2,0)); //low
    
      TGeoBBox *LowYokeBox = new TGeoBBox("LowYokeBox", fXRyoke/2, fYRyoke/2, fZRyoke/2);
      TGeoVolume *volLowYoke = new TGeoVolume("volLowYoke",LowYokeBox,vacuum);
      volMudetBox->AddNode(volLowYoke,1,new TGeoTranslation(0,-fYtot/2 + fYRyoke/2,0));
      volLowYoke->SetField(retFieldL);
   
      //vertical coils
      for(int i = 0; i < fNCoil; i++)
	{
	  volLowYoke->AddNode(volCoilV, i, new TGeoTranslation(fXRyoke/2 - fCoilH/2,0, -40*cm + fCoilW/2 + i*(fCoilGap + fCoilW)));
	}
      for(int i = 0; i < fNCoil; i++)
	{
	  volLowYoke->AddNode(volCoilV, i, new TGeoTranslation(-fXRyoke/2 + fCoilH/2,0, -40*cm + fCoilW/2 + i*(fCoilGap + fCoilW)));
	}
    
      volLowYoke->AddNode(volFeYoke,3, new TGeoTranslation(0,0,- (fZArm + fGapMiddle)/2));
      volLowYoke->AddNode(volFeYoke,4, new TGeoTranslation(0,0,(fZArm + fGapMiddle)/2));
      volLowYoke->AddNode(volFeYoke1,1,new TGeoTranslation(0,0,0));
      volLowYoke->AddNode(volCoilContainer,3,new TGeoTranslation(0,fYRyoke/2- fCoilH/2,0)); //up
      volLowYoke->AddNode(volCoilContainer,4,new TGeoTranslation(0,-fYRyoke/2 + fCoilH/2,0)); //low

      Int_t ArmNumber = 1;
      TGeoBBox *Arm1Box = new TGeoBBox("Arm1MudetBox", fXFe/2, fYFe/2, fZArm/2);
      TGeoVolume *volArm1 = new TGeoVolume("volArm1Mudet", Arm1Box,vacuum);
      TGeoUniformMagField *magField1 = new TGeoUniformMagField(0.,-fField,0.); //magnetic field arm1
      volArm1->SetField(magField1);
      volMudetBox ->AddNode(volArm1,ArmNumber,new TGeoTranslation(0,0,-(fGapMiddle+fZArm)/2));
    
      Int_t nr =  ArmNumber*1E4;

      TGeoBBox *IronLayer = new TGeoBBox("Iron",fXFe/2, fYFe/2, fZFe/2);
      TGeoVolume *volIron = new TGeoVolume("volIron",IronLayer,Iron);
      //volIron->SetField(magField1);

      for(Int_t i = 0; i < fNFe; i++)
	{
	  volArm1->AddNode(volIron,nr + 100 + i, new TGeoTranslation(0, 0, -fZArm/2+i*(fZFe +fZRpc) +fZFe/2));
	}
    
      TGeoBBox *RpcContainer = new TGeoBBox("RpcContainer", fXRpc/2, fYRpc/2, fZRpc/2);
      TGeoVolume *volRpcContainer = new TGeoVolume("volRpcContainer",RpcContainer,vacuum);
  
      TGeoBBox *Strip = new TGeoBBox("Strip",fXStrip/2, fYStrip/2, fZStrip/2);
      TGeoVolume *volStrip = new TGeoVolume("volStrip",Strip,Cu);
      volStrip->SetLineColor(kRed);
      volRpcContainer->AddNode(volStrip,1,new TGeoTranslation (0,0,-3.25*mm));
      volRpcContainer->AddNode(volStrip,2,new TGeoTranslation (0,0,3.25*mm));
      TGeoBBox *PETinsulator = new TGeoBBox("PETinsulator", fXPet/2, fYPet/2, fZPet/2);
      TGeoVolume *volPETinsulator = new TGeoVolume("volPETinsulator", PETinsulator, bakelite);
      volPETinsulator->SetLineColor(kYellow);
      volRpcContainer->AddNode(volPETinsulator,1,new TGeoTranslation(0,0,-3.1*mm));
      volRpcContainer->AddNode(volPETinsulator,2,new TGeoTranslation(0,0, 3.1*mm));
      TGeoBBox *Electrode = new TGeoBBox("Electrode",fXEle/2, fYEle/2, fZEle/2);
      TGeoVolume *volElectrode = new TGeoVolume("volElectrode",Electrode,bakelite);
      volElectrode->SetLineColor(kGreen);
      volRpcContainer->AddNode(volElectrode,1,new TGeoTranslation(0,0,-2*mm));
      volRpcContainer->AddNode(volElectrode,2,new TGeoTranslation(0,0, 2*mm));
      TGeoBBox *RpcGas = new TGeoBBox("RpcGas", fXGas/2, fYGas/2, fZGas/2);
      TGeoVolume *volRpc = new TGeoVolume("volRpc",RpcGas,RPCmat);
      volRpc->SetLineColor(kCyan);
      volRpcContainer->AddNode(volRpc,1,new TGeoTranslation(0,0,0));
   
      AddSensitiveVolume(volRpc);
    
      for(Int_t i = 0; i < fNRpc; i++)
	{
	  volArm1->AddNode(volRpcContainer,nr + i,new TGeoTranslation(0, -fYFe/2 + fYRpc/2, -fZArm/2+(i+1)*fZFe + i*fZRpc +fZRpc/2));
	}
    
      ArmNumber = 2;
      nr =  ArmNumber*1E4;

      TGeoBBox *Arm2Box = new TGeoBBox("Arm2MudetBox",fXFe/2, fYFe/2, fZArm/2);
      TGeoVolume *volArm2 = new TGeoVolume("volArm2Mudet", Arm2Box,vacuum);
      TGeoUniformMagField *magField2 = new TGeoUniformMagField(0.,fField,0.); //magnetic field arm2
      volArm2->SetField(magField2);
      volMudetBox ->AddNode(volArm2,1,new TGeoTranslation(0,0,(fGapMiddle+fZArm)/2));
      TGeoVolume *volIron2 = new TGeoVolume("volIron2",IronLayer,Iron);

     //different volumes for second arm
      
      TGeoVolume *volRpcContainer2 = new TGeoVolume("volRpcContainer2",RpcContainer,vacuum);
      TGeoVolume *volStrip2 = new TGeoVolume("volStrip2",Strip,Cu);
      
      volStrip2->SetLineColor(kRed);
      volRpcContainer2->AddNode(volStrip2,1,new TGeoTranslation (0,0,-3.25*mm));
      volRpcContainer2->AddNode(volStrip2,2,new TGeoTranslation (0,0,3.25*mm));

      TGeoVolume *volPETinsulator2 = new TGeoVolume("volPETinsulator2", PETinsulator, bakelite);
      volPETinsulator2->SetLineColor(kYellow);
      volRpcContainer2->AddNode(volPETinsulator2,1,new TGeoTranslation(0,0,-3.1*mm));
      volRpcContainer2->AddNode(volPETinsulator2,2,new TGeoTranslation(0,0, 3.1*mm));

      TGeoVolume *volElectrode2 = new TGeoVolume("volElectrode2",Electrode,bakelite);
      volElectrode2->SetLineColor(kGreen);
      volRpcContainer2->AddNode(volElectrode2,1,new TGeoTranslation(0,0,-2*mm));
      volRpcContainer2->AddNode(volElectrode2,2,new TGeoTranslation(0,0, 2*mm));
   
      TGeoVolume *volRpc2 = new TGeoVolume("volRpc2",RpcGas,RPCmat);
      volRpc2->SetLineColor(kCyan);
      volRpcContainer2->AddNode(volRpc2,1,new TGeoTranslation(0,0,0));
      AddSensitiveVolume(volRpc2);
   
      for(Int_t i = 0; i < fNFe; i++)
	{
	  volArm2->AddNode(volIron2,nr + 100 + i,new TGeoTranslation(0, 0, -fZArm/2+i*(fZFe +fZRpc) +fZFe/2));
	}
    
      for(Int_t i = 0; i < fNRpc; i++)
	{
	  volArm2->AddNode(volRpcContainer2, nr + i,new TGeoTranslation(0, -fYFe/2 + fYRpc/2, -fZArm/2+(i+1)*fZFe + i*fZRpc +fZRpc/2));
	}
    
      //10 cm of Concrete on which the whole Magnetic Spectrometer volume (HPT included) will be placed
      TGeoBBox *Base = new TGeoBBox("Base", fXtot/2, 10*cm/2, fZtot/2);
      TGeoVolume *volBase = new TGeoVolume("volBase",Base,Conc);
      volBase->SetLineColor(kYellow-3);

      tTauNuDet->AddNode(volBase,1, new TGeoTranslation(0,-fYtot/2 + 10*cm/2,fZcenter));


      TGeoBBox *Pillar1Box = new TGeoBBox(fPillarX/2,fPillarY/2, fPillarZ/2);
      TGeoVolume *Pillar1Vol = new TGeoVolume("Pillar1Vol",Pillar1Box,Steel);
      Pillar1Vol->SetLineColor(kGreen+3);

      tTauNuDet->AddNode(Pillar1Vol,1, new TGeoTranslation(-fXtot/2+fPillarX/2,-fYtot/2-fPillarY/2,fZcenter-fZArm/2 - fGapMiddle/2 +fPillarZ/2));
      tTauNuDet->AddNode(Pillar1Vol,2, new TGeoTranslation(fXtot/2-fPillarX/2,-fYtot/2-fPillarY/2,fZcenter-fZArm/2 - fGapMiddle/2 +fPillarZ/2));
      tTauNuDet->AddNode(Pillar1Vol,3, new TGeoTranslation(-fXtot/2+fPillarX/2,-fYtot/2-fPillarY/2,fZcenter+fZArm/2+fGapMiddle/2-fPillarZ/2));
      tTauNuDet->AddNode(Pillar1Vol,4, new TGeoTranslation(fXtot/2-fPillarX/2,-fYtot/2-fPillarY/2,fZcenter+fZArm/2+fGapMiddle/2-fPillarZ/2));
    }
  if(fDesign==3)
    {
      Int_t nr = 1E4;
      TGeoBBox *LargedetBox = new TGeoBBox("LargedetBox", fXtot/2, fYtot/2, (2*fZFe+3*fZRpc)/2);  
      TGeoBBox *SmalldetBox = new TGeoBBox("SmalldetBox", fXtot/2, (fYtot-fdeltay)/2, fZtot/2); //solving overlapping with pillars->dividing box to an union of two different boxes
 
      TGeoTranslation *translationlarge = new TGeoTranslation(0,0,(fZtot-2*fZFe-3*fZRpc)/2);
      translationlarge->SetName("translationlarge");
      translationlarge->RegisterYourself();
      TGeoTranslation *translationsmall = new TGeoTranslation(0,0,0);
      translationsmall->SetName("translationsmall");
      translationsmall->RegisterYourself();
      TGeoCompositeShape *MudetBox = new TGeoCompositeShape("MudetBox", "LargedetBox:translationlarge + SmalldetBox:translationsmall");
            
      TGeoVolume *volMudetBox = new TGeoVolume("volTauNuMudet", MudetBox, vacuum);
      tTauNuDet->AddNode(volMudetBox, 1, new TGeoTranslation(0,0,fZcenter));

      TGeoBBox *IronLayer = new TGeoBBox("Iron",fXFe/2, fYFe/2, fZFe/2);
      TGeoVolume *volIron = new TGeoVolume("volIron",IronLayer,Iron);

     TGeoBBox *IronLayer1 = new TGeoBBox("Iron",fXFe/2 -fdeltax/2, fYFe/2 -fdeltay/2, fZFe/2);
     TGeoVolume *volIron1 = new TGeoVolume("volIron1",IronLayer1,Iron);

      for(Int_t i = 0; i < fNFe; i++)
	{
	  if (i >= (fNFe-2)) volMudetBox->AddNode(volIron,nr + 100 + i, new TGeoTranslation(0, 0,-fZtot/2+i*fZFe+fZFe/2+(i+1)*fZRpc));
          else volMudetBox->AddNode(volIron1,nr + 100 + i, new TGeoTranslation(0, 0,-fZtot/2+i*fZFe+fZFe/2+(i+1)*fZRpc));
	}

      TGeoBBox *RpcContainer = new TGeoBBox("RpcContainer", fXRpc/2, fYRpc/2, fZRpc/2);
      TGeoVolume *volRpcContainer = new TGeoVolume("volRpcContainer",RpcContainer,vacuum);
  
      TGeoBBox *Strip = new TGeoBBox("Strip",fXStrip/2, fYStrip/2, fZStrip/2);
      TGeoVolume *volStrip = new TGeoVolume("volStrip",Strip,Cu);
      volStrip->SetLineColor(kRed);
      volRpcContainer->AddNode(volStrip,1,new TGeoTranslation (0,0,-3.25*mm));
      volRpcContainer->AddNode(volStrip,2,new TGeoTranslation (0,0,3.25*mm));
      TGeoBBox *PETinsulator = new TGeoBBox("PETinsulator", fXPet/2, fYPet/2, fZPet/2);
      TGeoVolume *volPETinsulator = new TGeoVolume("volPETinsulator", PETinsulator, bakelite);
      volPETinsulator->SetLineColor(kYellow);
      volRpcContainer->AddNode(volPETinsulator,1,new TGeoTranslation(0,0,-3.1*mm));
      volRpcContainer->AddNode(volPETinsulator,2,new TGeoTranslation(0,0, 3.1*mm));
      TGeoBBox *Electrode = new TGeoBBox("Electrode",fXEle/2, fYEle/2, fZEle/2);
      TGeoVolume *volElectrode = new TGeoVolume("volElectrode",Electrode,bakelite);
      volElectrode->SetLineColor(kGreen);
      volRpcContainer->AddNode(volElectrode,1,new TGeoTranslation(0,0,-2*mm));
      volRpcContainer->AddNode(volElectrode,2,new TGeoTranslation(0,0, 2*mm));
      TGeoBBox *RpcGas = new TGeoBBox("RpcGas", fXGas/2, fYGas/2, fZGas/2);
      TGeoVolume *volRpc = new TGeoVolume("volRpc",RpcGas,RPCmat);
      volRpc->SetLineColor(kCyan);
      volRpcContainer->AddNode(volRpc,1,new TGeoTranslation(0,0,0));
   
      TGeoBBox *RpcContainer1 = new TGeoBBox("RpcContainer1", fXRpc/2 -fdeltax/2, fYRpc/2-fdeltay/2, fZRpc/2);
      TGeoVolume *volRpcContainer1 = new TGeoVolume("volRpcContainer1",RpcContainer1,vacuum);
  
      TGeoBBox *Strip1  = new TGeoBBox("Strip1",fXStrip/2-fdeltax/2, fYStrip/2-fdeltay/2, fZStrip/2);
      TGeoVolume *volStrip1  = new TGeoVolume("volStrip1",Strip1,Cu);
      volStrip1->SetLineColor(kRed);
      volRpcContainer1->AddNode(volStrip1,1,new TGeoTranslation (0,0,-3.25*mm));
      volRpcContainer1->AddNode(volStrip1,2,new TGeoTranslation (0,0,3.25*mm));
      TGeoBBox *PETinsulator1 = new TGeoBBox("PETinsulator1", fXPet/2-fdeltax/2, fYPet/2-fdeltay/2, fZPet/2);
      TGeoVolume *volPETinsulator1 = new TGeoVolume("volPETinsulator1", PETinsulator1, bakelite);
      volPETinsulator1->SetLineColor(kYellow);
      volRpcContainer1->AddNode(volPETinsulator1,1,new TGeoTranslation(0,0,-3.1*mm));
      volRpcContainer1->AddNode(volPETinsulator1,2,new TGeoTranslation(0,0, 3.1*mm));
      TGeoBBox *Electrode1 = new TGeoBBox("Electrode1",fXEle/2-fdeltax/2, fYEle/2-fdeltay/2, fZEle/2);
      TGeoVolume *volElectrode1 = new TGeoVolume("volElectrode1",Electrode1,bakelite);
      volElectrode1->SetLineColor(kGreen);
      volRpcContainer1->AddNode(volElectrode1,1,new TGeoTranslation(0,0,-2*mm));
      volRpcContainer1->AddNode(volElectrode1,2,new TGeoTranslation(0,0, 2*mm));
      TGeoBBox *RpcGas1 = new TGeoBBox("RpcGas1", fXGas/2-fdeltax/2, fYGas/2-fdeltay/2, fZGas/2);
      TGeoVolume *volRpc1 = new TGeoVolume("volRpc1",RpcGas1,RPCmat);
      volRpc1->SetLineColor(kCyan);
      volRpcContainer1->AddNode(volRpc1,1,new TGeoTranslation(0,0,0));
   
      AddSensitiveVolume(volRpc);
      AddSensitiveVolume(volRpc1);
    
      for(Int_t i = 0; i < fNRpc; i++)
	{
	  if (i >= (fNRpc-3)) volMudetBox->AddNode(volRpcContainer,nr + i,new TGeoTranslation(0, 0, -fZtot/2+i*fZFe + i*fZRpc +fZRpc/2));
          else volMudetBox->AddNode(volRpcContainer1,nr + i,new TGeoTranslation(0, 0, -fZtot/2+i*fZFe + i*fZRpc +fZRpc/2));
	}
    
      TGeoBBox *Pillar1Box = new TGeoBBox(fPillarX/2,fPillarY/2, fPillarZ/2);
      TGeoVolume *Pillar1Vol = new TGeoVolume("Pillar1Vol",Pillar1Box,Steel);
      Pillar1Vol->SetLineColor(kGreen+3);

      tTauNuDet->AddNode(Pillar1Vol,1, new TGeoTranslation(-fXtot/2+fdeltax/2+fPillarX/2,-fYtot/2+fdeltay/2-fPillarY/2,fZcenter-fZtot/2+fPillarZ/2));
      tTauNuDet->AddNode(Pillar1Vol,2, new TGeoTranslation(fXtot/2-fdeltax/2-fPillarX/2,-fYtot/2+fdeltay/2-fPillarY/2,fZcenter-fZtot/2 +fPillarZ/2));
      //      tTauNuDet->AddNode(Pillar1Vol,3, new TGeoTranslation(-fXtot/2+fPillarX/2,-fYtot/2-fPillarY/2,fZcenter+fZtot/2-fPillarZ/2)); //eventually two pillars at the end. Now muon det is followed by veto, so its steel pillar supports both
      //tTauNuDet->AddNode(Pillar1Vol,4, new TGeoTranslation(fXtot/2-fPillarX/2,-fYtot/2-fPillarY/2,fZcenter+fZtot/2-fPillarZ/2));
    }

}


Bool_t  NuTauMudet::ProcessHits(FairVolume* vol)
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
    Int_t detID=0;
    gMC->CurrentVolID(detID);

    // cout<< "detID = " << detID << endl;
    Int_t MaxLevel = gGeoManager->GetLevel();
    const Int_t MaxL = MaxLevel;
    //cout << "MaxLevel = " << MaxL << endl;
    //cout << gMC->CurrentVolPath()<< endl;
    Int_t NRpc =0;
    const char *name;
    name = gMC->CurrentVolName();
    //cout << name << endl;
    Int_t motherID = gGeoManager->GetMother(0)->GetNumber();
    const char *mumname = gMC->CurrentVolOffName(0);
    //cout<<mumname<<"   "<< motherID<<endl;
    detID = motherID;
    //cout<< "detID = " << detID << endl;
    //cout<<endl;
    fVolumeID = detID;

    TLorentzVector Pos; 
    gMC->TrackPosition(Pos); 
    Double_t xmean = (fPos.X()+Pos.X())/2. ;      
    Double_t ymean = (fPos.Y()+Pos.Y())/2. ;      
    Double_t zmean = (fPos.Z()+Pos.Z())/2. ;     
     
    AddHit(fTrackID, fVolumeID, TVector3(xmean, ymean,  zmean), TVector3(fMom.Px(), fMom.Py(), fMom.Pz()), fTime, fLength,fELoss, pdgCode);
        
    // Increment number of muon det points in TParticle
    ShipStack* stack = (ShipStack*) gMC->GetStack();
    stack->AddPoint(ktauRpc);
  }
    
  return kTRUE;
}

void NuTauMudet::EndOfEvent()
{
  fShipRpcPointCollection->Clear();
}


void NuTauMudet::Register()
{
    
  /** This will create a branch in the output tree called
      ShipRpcPoint, setting the last parameter to kFALSE means:
      this collection will not be written to the file, it will exist
      only during the simulation.
  */
    
  FairRootManager::Instance()->Register("ShipRpcPoint", "NuTauMudet",
					fShipRpcPointCollection, kTRUE);
}

// -----   Public method to Decode volume info  -------------------------------------------
// -----   returns hpt, arm, rpc numbers -----------------------------------
void NuTauMudet::DecodeVolumeID(Int_t detID,int &nARM,int &nRPC)
{
  nARM =  detID/1E4;
  nRPC =  detID - nARM*1E4;
}

TClonesArray* NuTauMudet::GetCollection(Int_t iColl) const
{
  if (iColl == 0) { return fShipRpcPointCollection; }
  else { return NULL; }
}

void NuTauMudet::Reset()
{
  fShipRpcPointCollection->Clear();
}


ShipRpcPoint* NuTauMudet::AddHit(Int_t trackID, Int_t detID,
					   TVector3 pos, TVector3 mom,
					   Double_t time, Double_t length,
					   Double_t eLoss, Int_t pdgCode)

{
  TClonesArray& clref = *fShipRpcPointCollection;
  Int_t size = clref.GetEntriesFast();
  //cout << "ShipRpctau hit called"<< pos.z()<<endl;
  //    return new(clref[size]) ShipRpcPoint(trackID, detID, pos, mom,time, length, eLoss, pdgCode,NArm, NRpc, NHpt);
  return new(clref[size]) ShipRpcPoint(trackID, detID, pos, mom,time, length, eLoss, pdgCode);
}


ClassImp(NuTauMudet)
