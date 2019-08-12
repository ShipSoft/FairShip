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
#include "TGeoTrd2.h"
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

void NuTauMudet::SetFeDimensions(Double_t X, Double_t Y, Double_t Z, Double_t Zthin)
{  
  fXFe = X;
  fYFe = Y;
  fZFe = Z;
  fZFethin = Zthin;
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

void NuTauMudet::SetNFeInArm(Int_t N, Int_t Nthin)
{
  fNFe = N;
  fNFethin = Nthin;
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

void NuTauMudet::SetNRpcInTagger(Int_t NmuRpc)
{
  fNmuRpc = NmuRpc;
}

void NuTauMudet::SetSupportTransverseDimensions(Double_t UpperSupportX, Double_t UpperSupportY, Double_t LowerSupportX, Double_t LowerSupportY, Double_t LateralSupportX, Double_t LateralSupportY)
{
  fUpSuppX = UpperSupportX;
  fUpSuppY = UpperSupportY;
  fLowSuppX = LowerSupportX;
  fLowSuppY = LowerSupportY;
  fLatSuppX = LateralSupportX;
  fLatSuppY = LateralSupportY;
}

void NuTauMudet::SetLateralCutSize(Double_t CutHeight , Double_t CutLength){
  fCutHeight = CutHeight;
  fCutLength = CutLength;
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
      TGeoVolumeAssembly *volMudetBox = new TGeoVolumeAssembly("volNuTauMudet");
      tTauNuDet->AddNode(volMudetBox, 1, new TGeoTranslation(0,10*cm,fZcenter));
  
      TGeoVolumeAssembly *volUpYoke = new TGeoVolumeAssembly("volUpYoke");
      volMudetBox->AddNode(volUpYoke,1,new TGeoTranslation(0,fYtot/2 - fYRyoke/2,0));
      volUpYoke->SetField(retFieldU);
    
    
      TGeoBBox *FeYoke = new TGeoBBox("FeYoke",fXtot/2, fYRyoke/2, fZArm/2);
      TGeoVolume *volFeYoke = new TGeoVolume("volFeYoke",FeYoke,Iron);
      volFeYoke->SetLineColor(kGray+1);
  
      TGeoBBox *FeYoke1 = new TGeoBBox("FeYoke1",fXtot/2, fYRyoke_s/2, fZRyoke_s/2);
      TGeoVolume *volFeYoke1 = new TGeoVolume("volFeYoke1",FeYoke1,Iron);
      volFeYoke1->SetLineColor(kGray+1);
    
      TGeoVolumeAssembly *volCoilContainer = new TGeoVolumeAssembly("volCoilContainer");
    
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
    
      TGeoVolumeAssembly *volLowYoke = new TGeoVolumeAssembly("volLowYoke");
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
      TGeoVolumeAssembly *volArm1 = new TGeoVolumeAssembly("volArm1Mudet");
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
    
      TGeoVolumeAssembly *volRpcContainer = new TGeoVolumeAssembly("volRpcContainer");
  
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

      TGeoVolumeAssembly *volArm2 = new TGeoVolumeAssembly("volArm2Mudet");
      TGeoUniformMagField *magField2 = new TGeoUniformMagField(0.,fField,0.); //magnetic field arm2
      volArm2->SetField(magField2);
      volMudetBox ->AddNode(volArm2,1,new TGeoTranslation(0,0,(fGapMiddle+fZArm)/2));
      TGeoVolume *volIron2 = new TGeoVolume("volIron2",IronLayer,Iron);

     //different volumes for second arm
      
      TGeoVolumeAssembly *volRpcContainer2 = new TGeoVolumeAssembly("volRpcContainer2");
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
      Double_t supportasymmetry = fUpSuppY - fLowSuppY; //upper and lower support have different dimensions, so the mother box must be large enough to contain both
      Int_t nr = 1E4;
            
      TGeoVolumeAssembly *volMudetBox = new TGeoVolumeAssembly("volTauNuMudet");
      tTauNuDet->AddNode(volMudetBox, 1, new TGeoTranslation(0,0,fZcenter-(fNmuRpc*fZRpc)/2.));

      TGeoBBox *IronLayer = new TGeoBBox("Iron",fXFe/2, fYFe/2, fZFe/2);
      TGeoVolume *volIron = new TGeoVolume("volIron",IronLayer,Iron);
      volIron->SetLineColor(kGray);

      TGeoBBox *IronLayer1 = new TGeoBBox("Iron",fXFe/2, fYFe/2, fZFethin/2);
      TGeoVolume *volIron1 = new TGeoVolume("volIron1",IronLayer1,Iron);

      //***********************ADDING CUTS AT MID-LATERAL IN WALLS
      IronLayer->SetName("MUDETIRON");
      IronLayer1->SetName("MUDETIRON1");

      Double_t delta = 0.1; //to avoid border effects in the cuts (cut is not visualized in viewer, I do not know if it can affect simulation)
      TGeoTrd2  * Model= new TGeoTrd2("Model",fCutHeight/2,0, (fZFe+delta)/2,(fZFe+delta)/2,(fCutLength+delta)/2); //length and height are not x and y here, because it will be rotated!
      Model->SetName("MUDETTRIANGLE");

      TGeoRotation rot("rot",90,90,0);
      TGeoRotation rot1("rot1",-90,90,0);
      //cut on the right (seen from beam)
      const TGeoTranslation transright("trans",-fXFe/2.+ fCutLength/2,0,0);
      TGeoCombiTrans* combright = new TGeoCombiTrans(transright,rot);
      combright->SetName("MuDetcombright");
      combright->RegisterYourself(); 
      //cut on the left (seen from beam)
      const TGeoTranslation transleft("transleft",+fXFe/2.- fCutLength/2,0,0);
      TGeoCombiTrans* combleft = new TGeoCombiTrans(transleft,rot1);
      combleft->SetName("MuDetcombleft");
      combleft->RegisterYourself();  
      //unique volume, we cut the triangles
      TGeoCompositeShape *mudetcut = new TGeoCompositeShape("MUDETCUT", "(MUDETIRON-MUDETTRIANGLE:MuDetcombright)-MUDETTRIANGLE:MuDetcombleft");   
      mudetcut->SetName("MUDETTRIANGCUT");
      //same, for the thin layers
      TGeoCompositeShape *mudetcut1 = new TGeoCompositeShape("MUDETCUT1", "(MUDETIRON1-MUDETTRIANGLE:MuDetcombright)-MUDETTRIANGLE:MuDetcombleft");   
      mudetcut1->SetName("MUDETTRIANGCUT1");
      //addition of iron support structures
      //support layers, fot thick layers upstream
      TGeoBBox *UpperSupport = new TGeoBBox(fUpSuppX/2., fUpSuppY/2.,fZFe/2.);
      UpperSupport->SetName("MUDETUPSUPPORT");
      TGeoBBox *LowerSupport = new TGeoBBox(fLowSuppX/2., fLowSuppY/2.,fZFe/2.);
      LowerSupport->SetName("MUDETLOWSUPPORT");
      TGeoBBox *LateralSupport = new TGeoBBox(fLatSuppX/2., fLatSuppY/2., fZFe/2.);
      LateralSupport->SetName("MUDETLATERALSUPPORT");
      //support layers, for thin layers downstream
      TGeoBBox *UpperSupport1 = new TGeoBBox(fUpSuppX/2., fUpSuppY/2.,fZFethin/2.); //The 1 shapes have less z thickness
      UpperSupport1->SetName("MUDETUPSUPPORT1");
      TGeoBBox *LowerSupport1 = new TGeoBBox(fLowSuppX/2., fLowSuppY/2.,fZFethin/2.);
      LowerSupport1->SetName("MUDETLOWSUPPORT1");
      TGeoBBox *LateralSupport1 = new TGeoBBox(fLatSuppX/2., fLatSuppY/2.,fZFethin/2.);
      LateralSupport1->SetName("MUDETLATERALSUPPORT1");
      //Translations (left is considered from the beam, positive x)
      TGeoTranslation * upright = new TGeoTranslation("MuDetupright",-fXFe/2.+fUpSuppX/2.,fYFe/2+fUpSuppY/2.,0);
      TGeoTranslation * upleft = new TGeoTranslation("MuDetupleft",+fXFe/2.-fUpSuppX/2.,fYFe/2+fUpSuppY/2.,0); 
      TGeoTranslation * lateralupleft = new TGeoTranslation("MuDetlateralupleft",+fXFe/2.+fLowSuppX/2.,fYFe/2-fLowSuppY/2.,0); 
      TGeoTranslation * lateralupright = new TGeoTranslation("MuDetlateralupright",-fXFe/2.-fLowSuppX/2.,fYFe/2-fLowSuppY/2.,0); 
      TGeoTranslation * laterallowleft = new TGeoTranslation("MuDetlaterallowleft",+fXFe/2.+fLowSuppX/2.,-fYFe/2+fLowSuppY/2.,0); 
      TGeoTranslation * laterallowright = new TGeoTranslation("MuDetlaterallowright",-fXFe/2.-fLowSuppX/2.,-fYFe/2+fLowSuppY/2.,0); 
      TGeoTranslation * lowright = new TGeoTranslation("MuDetlowright",-fXFe/2.+fLowSuppX/2.,-fYFe/2-fLowSuppY/2.,0); 
      TGeoTranslation * lowleft = new TGeoTranslation("MuDetlowleft",+fXFe/2.-fLowSuppX/2.,-fYFe/2-fLowSuppY/2.,0);
      //necessary to put SetName, otherwise it will not find them
      upright->SetName("MuDetupright");
      upright->RegisterYourself();
      upleft->SetName("MuDetupleft");
      upleft->RegisterYourself();
      lowright->SetName("MuDetlowright");
      lowright->RegisterYourself();
      lowleft->SetName("MuDetlowleft");
      lowleft->RegisterYourself();

      lateralupleft->SetName("MuDetlateralupleft");
      lateralupleft->RegisterYourself();
      lateralupright->SetName("MuDetlateralupright");
      lateralupright->RegisterYourself();
      laterallowleft->SetName("MuDetlaterallowleft");
      laterallowleft->RegisterYourself();
      laterallowright->SetName("MuDetlaterallowright");
      laterallowright->RegisterYourself();
      //building composite shapes, writing compositions as TString first to improve readibility
      TString *supportaddition = new TString("MUDETTRIANGCUT+MUDETUPSUPPORT:MuDetupright+MUDETUPSUPPORT:MuDetupleft+MUDETLOWSUPPORT:MuDetlowright+MUDETLOWSUPPORT:MuDetlowleft+MUDETLATERALSUPPORT:MuDetlateralupleft+MUDETLATERALSUPPORT:MuDetlateralupright+MUDETLATERALSUPPORT:MuDetlaterallowleft+MUDETLATERALSUPPORT:MuDetlaterallowright");
      TString *supportaddition1 = new TString("MUDETTRIANGCUT1+MUDETUPSUPPORT1:MuDetupright+MUDETUPSUPPORT1:MuDetupleft+MUDETLOWSUPPORT1:MuDetlowright+MUDETLOWSUPPORT1:MuDetlowleft+MUDETLOWSUPPORT:MuDetlowleft+MUDETLATERALSUPPORT1:MuDetlateralupleft+MUDETLATERALSUPPORT1:MuDetlateralupright+MUDETLATERALSUPPORT1:MuDetlaterallowleft+MUDETLATERALSUPPORT1:MuDetlaterallowright");
      TGeoCompositeShape * SupportedIronLayer = new TGeoCompositeShape("SupportedIronLayer",supportaddition->Data());
      TGeoCompositeShape * SupportedIronLayer1 = new TGeoCompositeShape("SupportedIronLayer1",supportaddition1->Data());

      TGeoVolume *MudetIronLayer = new TGeoVolume("MudetIronLayer", SupportedIronLayer, Iron);
      MudetIronLayer->SetLineColor(kGray);
      TGeoVolume *MudetIronLayer1 = new TGeoVolume("MudetIronLayer1", SupportedIronLayer1, Iron);
      MudetIronLayer1->SetLineColor(kGray);

      for(Int_t i = 0; i < fNFe; i++)
	{
          double dz = -fZtot/2+i*fZFe+fZFe/2+i*fZRpc+(fNmuRpc*fZRpc/2);
          volMudetBox->AddNode(MudetIronLayer,nr + 100 + i, new TGeoTranslation(0, 0, dz));
	}
      for(Int_t i = 0; i < fNFethin; i++)
	{	  
          double dz = -fZtot/2+fNFe*(fZRpc+fZFe)+i*fZFethin+fZFethin/2+i*fZRpc+(fNmuRpc*fZRpc/2);
          volMudetBox->AddNode(MudetIronLayer1,nr + 100 + fNFe + i, new TGeoTranslation(0, 0,dz));
	}
      //*****************************RPC LAYERS****************************************
      TGeoVolumeAssembly *volRpcContainer = new TGeoVolumeAssembly("volRpcContainer");
  
      TGeoBBox *Strip = new TGeoBBox("Strip",fXStrip/2, fYStrip/2, fZStrip/2);
      TGeoVolume *volStrip = new TGeoVolume("volStrip",Strip,Cu);
      volStrip->SetLineColor(kGreen);
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
       
      TGeoVolumeAssembly *volRpcContainer1 = new TGeoVolumeAssembly("volRpcContainer1");
  
      TGeoBBox *Strip1  = new TGeoBBox("Strip1",fXStrip/2+fdeltax/2, fYStrip/2+fdeltay/2, fZStrip/2);
      TGeoVolume *volStrip1  = new TGeoVolume("volStrip1",Strip1,Cu);
      volStrip1->SetLineColor(kBlue);
      volRpcContainer1->AddNode(volStrip1,1,new TGeoTranslation (0,0,-3.25*mm));
      volRpcContainer1->AddNode(volStrip1,2,new TGeoTranslation (0,0,3.25*mm));
      TGeoBBox *PETinsulator1 = new TGeoBBox("PETinsulator1", fXPet/2+fdeltax/2, fYPet/2+fdeltay/2, fZPet/2);
      TGeoVolume *volPETinsulator1 = new TGeoVolume("volPETinsulator1", PETinsulator1, bakelite);
      volPETinsulator1->SetLineColor(kYellow);
      volRpcContainer1->AddNode(volPETinsulator1,1,new TGeoTranslation(0,0,-3.1*mm));
      volRpcContainer1->AddNode(volPETinsulator1,2,new TGeoTranslation(0,0, 3.1*mm));
      TGeoBBox *Electrode1 = new TGeoBBox("Electrode1",fXEle/2+fdeltax/2, fYEle/2+fdeltay/2, fZEle/2);
      TGeoVolume *volElectrode1 = new TGeoVolume("volElectrode1",Electrode1,bakelite);
      volElectrode1->SetLineColor(kGreen);
      volRpcContainer1->AddNode(volElectrode1,1,new TGeoTranslation(0,0,-2*mm));
      volRpcContainer1->AddNode(volElectrode1,2,new TGeoTranslation(0,0, 2*mm));
      TGeoBBox *RpcGas1 = new TGeoBBox("RpcGas1", fXGas/2+fdeltax/2, fYGas/2+fdeltay/2, fZGas/2);
      TGeoVolume *volRpc1 = new TGeoVolume("volRpc1",RpcGas1,RPCmat);
      volRpc1->SetLineColor(kCyan);
      volRpcContainer1->AddNode(volRpc1,1,new TGeoTranslation(0,0,0));
   
      AddSensitiveVolume(volRpc);
      AddSensitiveVolume(volRpc1);
    
      for(Int_t i = 0; i < fNRpc; i++)
	{
         double dz = -fZtot/2 + (i+1)*fZFe + i*fZRpc + fZRpc/2+(fNmuRpc*fZRpc/2);
         if (i >= fNFe) dz = dz - (i + 1 - fNFe) * (fZFe - fZFethin);
         volMudetBox->AddNode(volRpcContainer,nr + i,new TGeoTranslation(0, 0, dz));          
	}
      for(Int_t i = 0; i < fNmuRpc; i++)
	{
         double dz = -fZtot/2 + fNFe* fZFe + fNFethin*fZFethin + fNRpc*fZRpc + i*fZRpc + fZRpc/2+(fNmuRpc*fZRpc/2);
         volMudetBox->AddNode(volRpcContainer1,nr + fNRpc + i,new TGeoTranslation(0, 0, dz));
	}
    
      TGeoBBox *Pillar1Box = new TGeoBBox(fPillarX/2,fPillarY/2, fPillarZ/2);
      TGeoVolume *Pillar1Vol = new TGeoVolume("Pillar1Vol",Pillar1Box,Steel);
      Pillar1Vol->SetLineColor(kGreen+3);

      tTauNuDet->AddNode(Pillar1Vol,1, new TGeoTranslation(-fXtot/2+fPillarX/2,-fYtot/2-fPillarY/2,fZcenter-fZtot/2+fPillarZ/2));
      tTauNuDet->AddNode(Pillar1Vol,2, new TGeoTranslation(fXtot/2-fPillarX/2,-fYtot/2-fPillarY/2,fZcenter-fZtot/2 +fPillarZ/2));
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
