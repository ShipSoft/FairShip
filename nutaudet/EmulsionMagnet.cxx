#include "EmulsionMagnet.h"

#include "TGeoManager.h"
#include "FairRun.h"                    // for FairRun
#include "FairRuntimeDb.h"              // for FairRuntimeDb
#include <iosfwd>                    // for ostream
#include "TList.h"                      // for TListIter, TList (ptr only)
#include "TObjArray.h"                  // for TObjArray
#include "TString.h"                    // for TString

#include "TGeoBBox.h"
#include "TGeoTrd1.h"
#include "TGeoSphere.h"
#include "TGeoCompositeShape.h"
#include "TGeoTube.h"
#include "TGeoMaterial.h"
#include "TGeoMedium.h"
#include "TGeoTrd1.h"
#include "TGeoArb8.h"

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

#include "TGeoTrd2.h" 
#include "TGeoCompositeShape.h"

#include "TGeoUniformMagField.h"
#include "TVector3.h"
#include <stddef.h>                     // for NULL
#include <iostream>                     // for operator<<, basic_ostream,etc
#include <string.h>

using std::cout;
using std::endl;

using namespace ShipUnit;

EmulsionMagnet::~EmulsionMagnet()
{}

EmulsionMagnet::EmulsionMagnet():FairModule("EmulsionMagnet","")
{}

EmulsionMagnet::EmulsionMagnet(const char* name, const Double_t zC,const char* Title):FairModule(name, Title)
{
  fCenterZ = zC; 
}

void EmulsionMagnet::SetDesign(Int_t Design)
{
  fDesign = Design;
  Info("Chosen TP Design (0 no, 1 yes) "," %i", fDesign);
}

void EmulsionMagnet::SetGaps(Double_t Up, Double_t Down)
{
  fGapUpstream = Up;
  fGapDownstream = Down;
}

void EmulsionMagnet::SetMagnetSizes(Double_t X, Double_t Y, Double_t Z)
{
  fMagnetX=X;
  fMagnetY=Y;
  fMagnetZ=Z;
}

void EmulsionMagnet::SetMagnetColumn(Double_t ColX, Double_t ColY, Double_t ColZ)
{
  fColumnX=ColX;
  fColumnY=ColY;
  fColumnZ=ColZ;
}

void EmulsionMagnet::SetBaseDim(Double_t BaseX, Double_t BaseY, Double_t BaseZ)
{
  fBaseX = BaseX;
  fBaseY = BaseY;
  fBaseZ = BaseZ;
}


void EmulsionMagnet::SetCoilParameters(Double_t Radius, Double_t height1, Double_t height2, Double_t Distance)
{
  fCoilR = Radius;
  fCoilH1 = height1; //upper(left)
  fCoilH2 = height2; //lowe(right)
  fCoilDist = Distance;
}

void EmulsionMagnet::SetCoilParameters(Double_t X, Double_t Y, Double_t height1, Double_t height2, Double_t Thickness)
{
  fCoilX = X;
  fCoilY = Y;
  // cout << "fCoilX = "<< fCoilX<< "    fCoilY = "<<fCoilY<<endl;
  fCoilH1 = height1; //upper(left)
  fCoilH2 = height2; //lowe(right)
  fCoilThickness = Thickness;
}

void EmulsionMagnet::SetMagneticField(Double_t B)
{
  fField=B;
}

void EmulsionMagnet::SetPillarDimensions(Double_t X, Double_t Y, Double_t Z)
{
  fPillarX=X;
  fPillarY=Y;
  fPillarZ=Z;
}

void EmulsionMagnet::SetCutDimensions(Double_t CutLength, Double_t CutHeight)
{
  fCutLength = CutLength;
  fCutHeight = CutHeight;
}

void EmulsionMagnet::SetConstantField(Bool_t EmuMagnetConstField)
{
  fConstField = EmuMagnetConstField;
}

Int_t EmulsionMagnet::InitMedium(const char* name)
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

void EmulsionMagnet::ConstructGeometry()
{
  TGeoVolume *top=gGeoManager->GetTopVolume();
    
  InitMedium("iron");
  TGeoMedium *Fe =gGeoManager->GetMedium("iron");
    
  InitMedium("CoilAluminium");
  TGeoMedium *Al  = gGeoManager->GetMedium("CoilAluminium");
    
  InitMedium("CoilCopper");
  TGeoMedium *Cu  = gGeoManager->GetMedium("CoilCopper");
    
  InitMedium("steel");
  TGeoMedium *Steel = gGeoManager->GetMedium("steel");


  gGeoManager->SetVisLevel(10);

  TGeoVolume *tTauNuDet = gGeoManager->GetVolume("tTauNuDet");  
  cout<< "Tau Nu Detector fDesign: "<< fDesign<<endl;
    
  if(fDesign==0)//OLD, TP
    {
      TGeoUniformMagField *magField1 = new TGeoUniformMagField(0.,-fField,0.); //magnetic field in Magnet pillars
      TGeoUniformMagField *magField2 = new TGeoUniformMagField(0.,fField,0.); //magnetic field in target

      TGeoVolumeAssembly *MagnetVol = new TGeoVolumeAssembly("Goliath");
      tTauNuDet->AddNode(MagnetVol,1,new TGeoTranslation(0,0,fCenterZ));
      
      //Iron basis on which the coils are placed
      TGeoBBox *Base = new TGeoBBox(fBaseX/2,fBaseY/2,fBaseZ/2);
      TGeoVolume *volBase = new TGeoVolume("volBase",Base,Fe);
      volBase->SetLineColor(kRed);
      MagnetVol->AddNode(volBase,1,new TGeoTranslation(0, fMagnetY/2 - fBaseY/2, 0)); //upper part
      MagnetVol->AddNode(volBase,2,new TGeoTranslation(0, -fMagnetY/2 + fBaseY/2, 0)); //lower part

      //Coils Description: 2 volumes must be defined being the upper coil in Cu and the lower one in Al and also heghts are different
      TGeoTube *CoilBoxU = new TGeoTube("C",0,fCoilR,fCoilH1/2);
      TGeoVolume *CoilVolUp = new TGeoVolume("CoilVolUp",CoilBoxU, Cu);
      CoilVolUp->SetLineColor(kGreen);
      TGeoTube *CoilBoxD = new TGeoTube("C",0,fCoilR,fCoilH2/2);
      TGeoVolume *CoilVolDown = new TGeoVolume("CoilVolDown",CoilBoxD, Al);
      CoilVolDown->SetLineColor(kGreen);
      
      TGeoRotation *r1 = new TGeoRotation();
      r1->SetAngles(0,90,0);
      TGeoCombiTrans tUp(0, fMagnetY/2 - fBaseY - fCoilH1/2, 0,r1);
      TGeoHMatrix *mUp = new TGeoHMatrix(tUp);
      TGeoCombiTrans tDown(0, -fMagnetY/2 + fBaseY + fCoilH2/2, 0,r1);
      TGeoHMatrix *mDown = new TGeoHMatrix(tDown);

      MagnetVol->AddNode(CoilVolUp,1,mUp);
      MagnetVol->AddNode(CoilVolDown,1,mDown);
      
      //********************* Columns ****************************
    
      //Each column is made of a longer pillar (rectangle + trapezoid) and on top a shorter pillar (rectangle + trapezoid again) 
     
    Double_t base1 = 135, base2 = 78; //basis of the trapezoid
    Double_t side1 = 33, side2 = 125, side3 = 57, side4 = 90; //Sides of the columns
    
    //***** SIDE Left Front ****
    
    //Shorter Pillar: rectangle
    TGeoBBox *LateralS1 = new TGeoBBox("LateralS1",side1/2,fCoilH1/2,base1/2);
    TGeoTranslation *tr1 = new TGeoTranslation(-fMagnetX/2 + side1/2, fMagnetY/2 - fBaseY - fCoilH1/2, -fMagnetZ/2 + base1/2);
    TGeoVolume *volLateralS1 = new TGeoVolume("volLateralS1",LateralS1,Fe);
    volLateralS1->SetLineColor(kRed);
    volLateralS1->SetField(magField1);
    MagnetVol->AddNode(volLateralS1, 1, tr1);
    
    //Shorter Pillar: trapezoid
    
    TGeoArb8 *LateralS2 = new TGeoArb8("LateralS2",fCoilH1/2);
    LateralS2->SetVertex(0, side4, 0);
    LateralS2->SetVertex(1, side1, 0);
    LateralS2->SetVertex(2, side1, base1);
    LateralS2->SetVertex(3, side4, base2);
    LateralS2->SetVertex(4, side4, 0);
    LateralS2->SetVertex(5, side1, 0);
    LateralS2->SetVertex(6, side1, base1);
    LateralS2->SetVertex(7, side4, base2);
    
    TGeoVolume *volLateralS2 = new TGeoVolume("volLateralS2",LateralS2,Fe);
    volLateralS2->SetLineColor(kRed);
    volLateralS2->SetField(magField1);
    
    TGeoRotation *r2 = new TGeoRotation();
    r2->SetAngles(0,90,0);
    TGeoCombiTrans tr3(-fMagnetX/2, fMagnetY/2 - fBaseY - fCoilH1/2, -fMagnetZ/2,r2);
    TGeoHMatrix *m3_a = new TGeoHMatrix(tr3);
    MagnetVol->AddNode(volLateralS2, 1, m3_a);

    //LOWER LATERAL SURFACE
    
    //LONGER RECTANGLE
    TGeoBBox *LateralSurface1low = new TGeoBBox("LateralSurface1low",side1/2,(fCoilDist + fCoilH2)/2,side2/2);
    TGeoVolume *volLateralSurface1low = new TGeoVolume("volLateralSurface1low",LateralSurface1low,Fe);
    volLateralSurface1low->SetLineColor(kRed);
    volLateralSurface1low->SetField(magField1);
    TGeoTranslation *tr1low = new TGeoTranslation(-fMagnetX/2 +side1/2, fMagnetY/2 - fBaseY - fCoilH1 - (fCoilDist + fCoilH2)/2, -fMagnetZ/2 + side2/2);
    MagnetVol->AddNode(volLateralSurface1low, 1, tr1low);;
    
    
    //SHORTER RECTANGLE
    TGeoBBox *LateralSurface2low = new TGeoBBox("LateralSurface2low",side3/2,(fCoilDist + fCoilH2)/2,base2/2);
    TGeoVolume *volLateralSurface2low = new TGeoVolume("volLateralSurface2low",LateralSurface2low,Fe);
    volLateralSurface2low->SetLineColor(kRed);
    TGeoTranslation *tr2low = new TGeoTranslation(-fMagnetX/2 +side1 + side3/2, fMagnetY/2 - fBaseY -fCoilH1 - (fCoilDist + fCoilH2)/2, -fMagnetZ/2 + base2/2);
    MagnetVol->AddNode(volLateralSurface2low, 1, tr2low);
    volLateralSurface2low->SetField(magField1);

    //***** SIDE Right Front ****
    
    //LONGER RECTANGLE
    TGeoTranslation *tr1_b = new TGeoTranslation(-fMagnetX/2 + side1/2, fMagnetY/2 - fBaseY - fCoilH1/2, fMagnetZ/2 - base1/2);
    TGeoVolume *volLateralS1_b = new TGeoVolume("volLateralS1_b",LateralS1,Fe);
    volLateralS1_b->SetLineColor(kRed);
    volLateralS1_b->SetField(magField1);
    MagnetVol->AddNode(volLateralS1_b, 1, tr1_b);
    
    //TRAPEZOID
    TGeoArb8 *LateralS2_b = new TGeoArb8("LateralS2_b",fCoilH1/2);
    LateralS2_b ->SetVertex(0, side4, 0);
    LateralS2_b ->SetVertex(1, side1, 0);
    LateralS2_b ->SetVertex(2, side1, base1);
    LateralS2_b ->SetVertex(3, side4, base2);
    LateralS2_b ->SetVertex(4, side4, 0);
    LateralS2_b ->SetVertex(5, side1, 0);
    LateralS2_b ->SetVertex(6, side1, base1);
    LateralS2_b ->SetVertex(7, side4, base2);
    
    TGeoVolume *volLateralS2_b = new TGeoVolume("volLateralS2_b",LateralS2_b,Fe);
    volLateralS2_b->SetLineColor(kRed);
    volLateralS2_b->SetField(magField1);
    
    TGeoRotation *r2_b = new TGeoRotation();
    r2_b->SetAngles(0,270,0);
    TGeoCombiTrans tr2_b(-fMagnetX/2 , fMagnetY/2 - fBaseY - fCoilH1/2, fMagnetZ/2,r2_b);
    TGeoHMatrix *m3_b = new TGeoHMatrix(tr2_b);
    MagnetVol->AddNode(volLateralS2_b, 1, m3_b);
    
    
    //LOWER LATERAL SURFACE
    
    //LONGER RECTANGLE
    TGeoVolume *volLateralSurface1blow = new TGeoVolume("volLateralSurface1blow",LateralSurface1low,Fe);
    volLateralSurface1blow->SetLineColor(kRed);
    volLateralSurface1blow->SetField(magField1);
    TGeoTranslation *tr1blow = new TGeoTranslation(-fMagnetX/2 +side1/2, fMagnetY/2 - fBaseY - fCoilH1 - (fCoilDist + fCoilH2)/2, fMagnetZ/2 - side2/2);
    MagnetVol->AddNode(volLateralSurface1blow, 1, tr1blow);;
    
    
    //SHORTER RECTANGLE
    TGeoVolume *volLateralSurface2blow = new TGeoVolume("volLateralSurface2blow",LateralSurface2low,Fe);
    volLateralSurface2blow->SetLineColor(kRed);
    volLateralSurface2blow->SetField(magField1);
    TGeoTranslation *tr2blow = new TGeoTranslation(-fMagnetX/2 +side1 + side3/2, fMagnetY/2 - fBaseY - fCoilH1 - (fCoilDist + fCoilH2)/2, fMagnetZ/2 - base2/2);
    MagnetVol->AddNode(volLateralSurface2blow, 1, tr2blow);
    
    
    //***** SIDE left Back ****
    
    
    //LONGER RECTANGLE
    TGeoBBox *LateralS1_d = new TGeoBBox("LateralS1_d",side1/2,(fCoilH1 + fCoilH2 + fCoilDist)/2,base1/2);
    TGeoTranslation *tr1_d = new TGeoTranslation(fMagnetX/2 - side1/2, fMagnetY/2 - fBaseY - (fCoilH1 + fCoilH2 + fCoilDist)/2, -fMagnetZ/2 + base1/2);
    TGeoVolume *volLateralS1_d = new TGeoVolume("volLateralS1_d",LateralS1_d,Fe);
    volLateralS1_d->SetLineColor(kRed);
    volLateralS1_d->SetField(magField1);
    MagnetVol->AddNode(volLateralS1_d, 1, tr1_d);
    
    //TRAPEZOID
    
    TGeoArb8 *LateralS2_d = new TGeoArb8("LateralS2_d",(fCoilH1 + fCoilH2 + fCoilDist)/2);
    LateralS2_d->SetVertex(0, side4, 0);
    LateralS2_d->SetVertex(1, side1, 0);
    LateralS2_d->SetVertex(2, side1, base1);
    LateralS2_d->SetVertex(3, side4, base2);
    LateralS2_d->SetVertex(4, side4, 0);
    LateralS2_d->SetVertex(5, side1, 0);
    LateralS2_d->SetVertex(6, side1, base1);
    LateralS2_d->SetVertex(7, side4, base2);
    
    
    TGeoVolume *volLateralS2_d = new TGeoVolume("volLateralS2_d",LateralS2_d,Fe);
    volLateralS2_d->SetLineColor(kRed);
    volLateralS2_d->SetField(magField1);
    
    TGeoRotation *r2_d = new TGeoRotation();
    r2_d->SetAngles(0,270,180);
    TGeoCombiTrans tr2_d(fMagnetX/2 , fMagnetY/2 - fBaseY - (fCoilH1 + fCoilH2 + fCoilDist)/2, -fMagnetZ/2,r2_d);
    TGeoHMatrix *m3_d = new TGeoHMatrix(tr2_d);
    MagnetVol->AddNode(volLateralS2_d, 1, m3_d);

//***** SIDE right Back ****
    
    
    //LONGER RECTANGLE
    TGeoBBox *LateralS1_c = new TGeoBBox("LateralS1_c",side1/2,(fCoilH1 + fCoilH2 + fCoilDist)/2,base1/2);
    TGeoTranslation *tr1_c = new TGeoTranslation(fMagnetX/2 - side1/2, fMagnetY/2 - fBaseY - (fCoilH1 + fCoilH2 + fCoilDist)/2, fMagnetZ/2 - base1/2);
    TGeoVolume *volLateralS1_c = new TGeoVolume("volLateralS1_c",LateralS1_c,Fe);
    volLateralS1_c->SetLineColor(kRed);
    volLateralS1_c->SetField(magField1);
    MagnetVol->AddNode(volLateralS1_c, 1, tr1_c);
    
    //TRAPEZOID
    
    TGeoArb8 *LateralS2_c = new TGeoArb8("LateralS2_c",(fCoilH1 + fCoilH2 + fCoilDist)/2);
    LateralS2_c ->SetVertex(0, side4, 0);
    LateralS2_c ->SetVertex(1, side1, 0);
    LateralS2_c ->SetVertex(2, side1, base1);
    LateralS2_c ->SetVertex(3, side4, base2);
    LateralS2_c ->SetVertex(4, side4, 0);
    LateralS2_c ->SetVertex(5, side1, 0);
    LateralS2_c ->SetVertex(6, side1, base1);
    LateralS2_c ->SetVertex(7, side4, base2);
    
    TGeoVolume *volLateralS2_c = new TGeoVolume("volLateralS2_c",LateralS2_c,Fe);
    volLateralS2_c->SetLineColor(kRed);
    volLateralS2_c->SetField(magField1);
    
    TGeoRotation *r2_c = new TGeoRotation();
    r2_c->SetAngles(0,90,180);
    TGeoCombiTrans tr2_c(fMagnetX/2 , fMagnetY/2 - fBaseY - (fCoilH1 + fCoilH2 + fCoilDist)/2, fMagnetZ/2,r2_c);
    TGeoHMatrix *m3_c = new TGeoHMatrix(tr2_c);
    MagnetVol->AddNode(volLateralS2_c, 1, m3_c);


    }

  if(fDesign==1) //NEW with magnet
    {
      TGeoUniformMagField *magField1 = new TGeoUniformMagField(-fField,0.,0.); //magnetic field in Magnet pillars
      TGeoUniformMagField *magField2 = new TGeoUniformMagField(fField,0.,0.); //magnetic field in target
      
      TGeoVolumeAssembly *MagnetVol = new TGeoVolumeAssembly("Davide");
      tTauNuDet->AddNode(MagnetVol,1,new TGeoTranslation(0,0,fCenterZ));
    
      //The -0.01*mm is only for drawing reasons
      TGeoBBox *LateralBox = new TGeoBBox("LB",fBaseZ/2,fBaseY/2,(fBaseX-0.01*mm)/2);
      TGeoTube *CoilBox = new TGeoTube("C",0,fCoilR,fCoilH1/2);
    
      TGeoCompositeShape *LateralSurf = new TGeoCompositeShape("LS","LB-C");
    
      TGeoVolume *CoilVol = new TGeoVolume("CoilVol",CoilBox, Cu);
      CoilVol->SetLineColor(kGreen);
      TGeoVolume *LateralSurfVol = new TGeoVolume("LateralSurfVol",LateralSurf, Fe);
      LateralSurfVol->SetLineColor(kRed);

      TGeoRotation *r1 = new TGeoRotation();
      r1->RotateY(90);
      //r1->RotateY(90);
      //r1->RotateY(90);
      r1->RegisterYourself();
      TGeoTranslation *t1r = new TGeoTranslation(-fMagnetX/2+fBaseX/2,0,0);
      TGeoTranslation *t1l = new TGeoTranslation(fMagnetX/2-fBaseX/2,0,0);

      TGeoCombiTrans *trans1r = new TGeoCombiTrans(-fMagnetX/2+fBaseX/2,0,0,r1);
      TGeoCombiTrans *trans1l = new TGeoCombiTrans(fMagnetX/2-fBaseX/2,0,0,r1);
      TGeoHMatrix *m1_r = new TGeoHMatrix("m1_r");
      *m1_r = trans1r;
      TGeoHMatrix *m1_l = new TGeoHMatrix("m1_l");
      *m1_l = trans1l;

      MagnetVol->AddNode(CoilVol,1, m1_r);
      MagnetVol->AddNode(LateralSurfVol,1,m1_r);
      MagnetVol->AddNode(CoilVol,2, m1_l);
      MagnetVol->AddNode(LateralSurfVol,2,m1_l);

      TGeoBBox *ColumnBox = new TGeoBBox(fColumnX/2, fColumnY/2, fColumnZ/2);
      TGeoVolume *ColumnVol = new TGeoVolume("ColumnVol",ColumnBox,Fe);
      ColumnVol->SetField(magField1);
      ColumnVol->SetLineColor(kRed);
      MagnetVol->AddNode(ColumnVol,1,new TGeoTranslation(0,fMagnetY/2-fColumnY/2, -fMagnetZ/2+fColumnZ/2));
      MagnetVol->AddNode(ColumnVol,2,new TGeoTranslation(0,fMagnetY/2-fColumnY/2, fMagnetZ/2-fColumnZ/2));
      MagnetVol->AddNode(ColumnVol,3,new TGeoTranslation(0,-fMagnetY/2+fColumnY/2, -fMagnetZ/2+fColumnZ/2));
      MagnetVol->AddNode(ColumnVol,4,new TGeoTranslation(0,-fMagnetY/2+fColumnY/2, fMagnetZ/2-fColumnZ/2));
    
      TGeoBBox *BaseBox = new TGeoBBox(fCoilDist/2,fColumnY/2, fBaseZ/2);
      TGeoVolume *BaseVol = new TGeoVolume("BaseVol",BaseBox,Fe);
      BaseVol->SetLineColor(kRed);
      MagnetVol->AddNode(BaseVol,1, new TGeoTranslation(0,-fMagnetY/2+fColumnY/2,0));

      TGeoBBox *PillarBox = new TGeoBBox(fPillarX/2,fPillarY/2, fPillarZ/2);
      TGeoVolume *PillarVol = new TGeoVolume("PillarVol",PillarBox,Steel);
      PillarVol->SetLineColor(kGreen+3);
      tTauNuDet->AddNode(PillarVol,1, new TGeoTranslation(-fMagnetX/2+fPillarX/2,-fMagnetY/2-fPillarY/2, fCenterZ-fMagnetZ/2+fPillarZ/2));
      tTauNuDet->AddNode(PillarVol,2, new TGeoTranslation(fMagnetX/2-fPillarX/2,-fMagnetY/2-fPillarY/2, fCenterZ-fMagnetZ/2+fPillarZ/2));
      tTauNuDet->AddNode(PillarVol,3, new TGeoTranslation(-fMagnetX/2+fPillarX/2,-fMagnetY/2-fPillarY/2, fCenterZ+fMagnetZ/2-fPillarZ/2));
      tTauNuDet->AddNode(PillarVol,4, new TGeoTranslation(fMagnetX/2-fPillarX/2,-fMagnetY/2-fPillarY/2, fCenterZ+fMagnetZ/2-fPillarZ/2));
    }

   if(fDesign==3) //NEW with magnet
    {
      //Box for Magnet
      TGeoVolumeAssembly *MagnetVol = new TGeoVolumeAssembly("NudetMagnet");
      tTauNuDet->AddNode(MagnetVol,1,new TGeoTranslation(0,0,fCenterZ));

      TGeoBBox *BaseBox = new TGeoBBox(fBaseX/2,fBaseY/2,fBaseZ/2);
      TGeoVolume *BaseVol = new TGeoVolume("BaseVol",BaseBox,Fe);
      BaseVol->SetLineColor(kRed);
      TGeoBBox *LateralBox = new TGeoBBox(fColumnX/2,fColumnY/2,fColumnZ/2);

      //prepare for triangolar cuts
      LateralBox->SetName("L");
      Double_t delta = 0.1; //to avoid border effects in the cuts (cut is not visualized in viewer, I do not know if it can affect simulation)
      TGeoTrd2  * Model= new TGeoTrd2("Model",fCutHeight/2,0, (fColumnZ+delta)/2,(fColumnZ+delta)/2,(fCutLength+delta)/2); //length and height are not x and y here, because it will be rotated!
      Model->SetName("T");

      const Double_t SemiLateralBoxHeight =(fColumnY - fCutHeight)/2;

      //we need different volumes to place different magnetic fields
      TGeoBBox *SemiLateralBox = new TGeoBBox("SemiLateralBox",(fColumnX)/2, SemiLateralBoxHeight /2, fColumnZ/2);           
      TGeoVolume *volUpLateral = new TGeoVolume("volUpLateral",SemiLateralBox,Fe); //up and down refer to the magnetic field verse
     
      TGeoVolume *volDownLateral = new TGeoVolume("volDownLateral",SemiLateralBox,Fe);       
      SemiLateralBox->SetName("S");       
      volUpLateral->SetLineColor(kRed);
      volDownLateral->SetLineColor(kRed);

      const Double_t MidBoxHeight = fCutHeight/2;

      TGeoBBox *MidLateralBox = new TGeoBBox("MidLateralBox",fColumnX/2, MidBoxHeight/2, fColumnZ/2); 
      MidLateralBox->SetName("M");

     //some boolean operations for triangular cuts

      TGeoRotation rot("rot",90,90,0);
      TGeoRotation rot1("rot1",-90,90,0);
      const TGeoTranslation trans("trans",-fColumnX/2.+ fCutLength/2,0,0);
      TGeoCombiTrans* comb = new TGeoCombiTrans(trans,rot);
      comb->SetName("comb");
      comb->RegisterYourself(); 
      TGeoCompositeShape *cut = new TGeoCompositeShape("CUT", "L-T:comb");


      TGeoTranslation* transcuttop = new TGeoTranslation("transcuttop",0, fCutHeight/2 + SemiLateralBoxHeight/2 ,0); //top and bottom refer to their geometrical positions
      TGeoTranslation* transcuttop1 = new TGeoTranslation("transcuttop1",0, MidBoxHeight/2 ,0);
      TGeoTranslation* transcutbottom = new TGeoTranslation("transcutbottom",0, - fCutHeight/2 - SemiLateralBoxHeight/2  ,0);
      TGeoTranslation* transcutbottom1 = new TGeoTranslation("transcutbottom1",0, -MidBoxHeight/2 ,0);
 
      transcuttop->RegisterYourself();
      transcuttop1->RegisterYourself();
      transcutbottom->RegisterYourself();    
      transcutbottom1->RegisterYourself();  

      TGeoCompositeShape *cuttop = new TGeoCompositeShape("CUTTOP", "CUT - (S:transcuttop) - (S:transcutbottom)"); //triangular cut in the right lateral wall
      TGeoVolume *volcuttop = new TGeoVolume("volcuttop", cuttop, Fe);
      volcuttop->SetLineColor(kRed);  

      const TGeoTranslation transleft("transleft",+fColumnX/2.- fCutLength/2,0,0);
      TGeoCombiTrans* combleft = new TGeoCombiTrans(transleft,rot1);
      combleft->SetName("combleft");
      combleft->RegisterYourself();
      TGeoCompositeShape *cutleft;
      cutleft = new TGeoCompositeShape("CUTLEFT", "L-T:combleft");        
      TGeoCompositeShape *cuttopleft = new TGeoCompositeShape("CUTTOPLEFT", "CUTLEFT - (S:transcuttop) - (S:transcutbottom)"); //triangular cut in the left lateral wall
      TGeoVolume *volcuttopleft = new TGeoVolume("volcuttopleft", cuttopleft, Fe);
      volcuttopleft->SetLineColor(kRed);

      //composite coil
      TGeoBBox *OutcoilBox = new TGeoBBox("OC", fCoilX/2, fCoilH1/2,fMagnetZ/2-fCoilH1/2);
      TGeoBBox *IncoilBox = new TGeoBBox("IC", fCoilX/2,fCoilH2/2,(fMagnetZ-fCoilH1)/2);

      //circular arcs (first two options are radii, not half radii!)
      Double_t OuterRadius = fCoilY + fCoilThickness;

      TGeoTubeSeg *Coillateraltuberightdown = new TGeoTubeSeg("Coillateraltuberightdown",fCoilThickness,OuterRadius, fCoilX/2,90,180);
      TGeoTubeSeg *Coillateraltuberighttup = new TGeoTubeSeg("Coillateraltuberightup",fCoilThickness,OuterRadius, fCoilX/2,0,90);
      TGeoTubeSeg *Coillateraltubeleftup = new TGeoTubeSeg("Coillateraltubeleftup",fCoilThickness,OuterRadius, fCoilX/2,270,360);
      TGeoTubeSeg *Coillateraltubeleftdown = new TGeoTubeSeg("Coillateraltubeleftdown",fCoilThickness,OuterRadius, fCoilX/2,180,270);

      TGeoBBox *Coillateralcenter = new TGeoBBox("Coillateralcenter",fCoilX/2., (fCoilH2-2*fCoilThickness)/2, fCoilY/2.);      

      TGeoRotation rottube("rottube",90,90,0);
      //transformations to combine them
      const TGeoTranslation transtube("transtube",0.,-(fCoilH2-2*fCoilThickness)/2, -fCoilThickness-fCoilY/2);
      const TGeoTranslation transtube1("transtube1",0.,(fCoilH2-2*fCoilThickness)/2, -fCoilThickness-fCoilY/2);
      const TGeoTranslation transtube2("transtube2",0.,-(fCoilH2-2*fCoilThickness)/2,+fCoilThickness+fCoilY/2);
      const TGeoTranslation transtube3("transtube3",0.,(fCoilH2-2*fCoilThickness)/2,+fCoilThickness+fCoilY/2);
      TGeoCombiTrans* combination = new TGeoCombiTrans(transtube,rottube);
      TGeoCombiTrans* combination1 = new TGeoCombiTrans(transtube1,rottube);
      TGeoCombiTrans* combination2 = new TGeoCombiTrans(transtube2,rottube);
      TGeoCombiTrans* combination3 = new TGeoCombiTrans(transtube3,rottube);

      combination->SetName("combination");
      combination->RegisterYourself();  
      combination1->SetName("combination1");
      combination1->RegisterYourself(); 
      combination2->SetName("combination2");
      combination2->RegisterYourself();
      combination3->SetName("combination3");
      combination3->RegisterYourself();
      //adding the shapes and making the volumes
      TGeoCompositeShape * CoilRight = new TGeoCompositeShape("CoilRight","Coillateraltuberightdown:combination+Coillateraltuberightup:combination1+Coillateralcenter");
      TGeoVolume *CoilVolright = new TGeoVolume("CoilVolright",CoilRight,Cu);

      TGeoCompositeShape * CoilLeft = new TGeoCompositeShape("CoilLeft","Coillateraltubeleftdown:combination2+Coillateraltubeleftup:combination3+Coillateralcenter");
      TGeoVolume *CoilVolleft = new TGeoVolume("CoilVolleft",CoilLeft,Cu);



      TGeoBBox *Coil = new TGeoBBox("Coil", fCoilX/2,fCoilY/2, (fMagnetZ-2*OuterRadius)/2); //two times the external radius
      TGeoVolume *CoilVol = new TGeoVolume("CoilVol",Coil, Cu);

      //adding obtained volumes

      MagnetVol->AddNode(BaseVol,1, new TGeoTranslation(0,-fMagnetY/2+fBaseY/2,0));
      MagnetVol->AddNode(BaseVol,2, new TGeoTranslation(0,fMagnetY/2-fBaseY/2,0));   
  
      MagnetVol->AddNode(volUpLateral, 1, new TGeoTranslation(-fMagnetX/2+fColumnX/2, (fCutHeight + (fColumnY - fCutHeight)/2)/2 ,0));
      MagnetVol->AddNode(volDownLateral, 1, new TGeoTranslation(-fMagnetX/2+fColumnX/2, (-fCutHeight - (fColumnY - fCutHeight)/2)/2,0));
      MagnetVol->AddNode(volcuttop, 1, new TGeoTranslation(-fMagnetX/2+fColumnX/2, 0, 0));

      MagnetVol->AddNode(volUpLateral, 2, new TGeoTranslation(fMagnetX/2-fColumnX/2, (-fCutHeight - (fColumnY - fCutHeight)/2)/2 ,0));
      MagnetVol->AddNode(volDownLateral, 2, new TGeoTranslation(fMagnetX/2-fColumnX/2, (+fCutHeight + (fColumnY - fCutHeight)/2)/2,0));
      MagnetVol->AddNode(volcuttopleft,2, new TGeoTranslation(fMagnetX/2-fColumnX/2,0,0));
     
      CoilVolleft->SetLineColor(kGreen);
      MagnetVol->AddNode(CoilVolleft,1,new TGeoTranslation(0,0,-fMagnetZ/2.+fCoilY/2.));
      CoilVolright->SetLineColor(kGreen);
      MagnetVol->AddNode(CoilVolright,1,new TGeoTranslation(0,0,+fMagnetZ/2.-fCoilY/2.));
      CoilVol->SetLineColor(kGreen);
      MagnetVol->AddNode(CoilVol,1,new TGeoTranslation(0,(fCoilH1+fCoilH2)/4,0));
      MagnetVol->AddNode(CoilVol,2,new TGeoTranslation(0,-(fCoilH1+fCoilH2)/4,0));

      //magnetized region
      TGeoVolumeAssembly *volMagRegion = new TGeoVolumeAssembly("volMagRegion");
      MagnetVol->AddNode(volMagRegion, 1, new TGeoTranslation(0,0,0));

      //pillars for the magnet
      TGeoBBox *PillarBox = new TGeoBBox(fPillarX/2,fPillarY/2, fPillarZ/2);
      TGeoVolume *PillarVol = new TGeoVolume("PillarVol",PillarBox,Steel);
      PillarVol->SetLineColor(kGreen+3);
      tTauNuDet->AddNode(PillarVol,1, new TGeoTranslation(-fMagnetX/2+fPillarX/2,-fMagnetY/2-fPillarY/2, fCenterZ-fMagnetZ/2+fPillarZ/2));
      tTauNuDet->AddNode(PillarVol,2, new TGeoTranslation(fMagnetX/2-fPillarX/2,-fMagnetY/2-fPillarY/2, fCenterZ-fMagnetZ/2+fPillarZ/2));
      tTauNuDet->AddNode(PillarVol,3, new TGeoTranslation(-fMagnetX/2+fPillarX/2,-fMagnetY/2-fPillarY/2, fCenterZ+fMagnetZ/2-fPillarZ/2));
      tTauNuDet->AddNode(PillarVol,4, new TGeoTranslation(fMagnetX/2-fPillarX/2,-fMagnetY/2-fPillarY/2, fCenterZ+fMagnetZ/2-fPillarZ/2));


      if (fConstField){ //adding magnetic field if not implemented from nudet field map
      TGeoUniformMagField *magField1 = new TGeoUniformMagField(-fField,0.,0.); //magnetic field in Magnet pillars
      TGeoUniformMagField *magField2 = new TGeoUniformMagField(fField,0.,0.); //magnetic field in target
      TGeoUniformMagField *magField1y = new TGeoUniformMagField(0.,-fField,0.); //down return magnetic field along y
      TGeoUniformMagField *magField2y = new TGeoUniformMagField(0.,fField,0.); //up return magnetic field along y 

      BaseVol->SetField(magField1);
      volUpLateral->SetField(magField2y);
      volDownLateral->SetField(magField1y);
      volMagRegion->SetField(magField2);
      }
    }
}


ClassImp(EmulsionMagnet)
