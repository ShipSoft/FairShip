#include "MagneticSpectrometer.h"

#include "ShipRpcPoint.h"

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

MagneticSpectrometer::MagneticSpectrometer()
  : FairDetector("MagneticSpectrometer",kTRUE, ktauRpc),
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

MagneticSpectrometer::MagneticSpectrometer(const char* name, const Double_t zMSC, const Double_t zSize, const Double_t FeSlab, const Double_t RpcW, const Double_t ArmW, const Double_t GapV, const Double_t MGap, const Double_t Mfield, Double_t HPTW, Double_t RetYokeH, Bool_t Active,const char* Title)
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
    zMSCenter = zMSC;
    zSizeMS = zSize;
    IronSlabWidth = FeSlab;
    RpcWidth = RpcW;
    ArmWidth = ArmW;
    GapFromVessel = GapV;
    MiddleGap = MGap;
    MagneticField = Mfield;
    HPTWidth = HPTW;
    ReturnYokeH = RetYokeH;
}

void MagneticSpectrometer::SetCoilParameters(Double_t CoilH, Double_t CoilW, Int_t N, Double_t CoilG)
{
    CoilHeight = CoilH;
    CoilWidth = CoilW;
    CoilGap = CoilG;
    NCoils = N;
}

MagneticSpectrometer::~MagneticSpectrometer()
{
    if (fShipRpcPointCollection) {
        fShipRpcPointCollection->Delete();
        delete fShipRpcPointCollection;
    }
}

void MagneticSpectrometer::Initialize()
{
    FairDetector::Initialize();
}

// -----   Private method InitMedium 
Int_t MagneticSpectrometer::InitMedium(const char* name)
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

void MagneticSpectrometer::ConstructGeometry()
{
    Double_t XtrSize = 4*m; //Transversal size of the magnetic spectrometer
    Double_t YtrSize_Hpt = 8*m;
    Double_t YtrSize_Fe = 8.2*m;
    Double_t YtrSize_Rpc = 8*m;
    Double_t YtrSize_tot = 8.2*m + 2*ReturnYokeH;

    
    Int_t NSlabs = 12; //Number of Fe slabs (= n rpc+1) inside each arm of the spectrometer
    
    TGeoVolume *top = gGeoManager->GetTopVolume();
    
    InitMedium("RPCgas");
    TGeoMedium *RPCmat =gGeoManager->GetMedium("RPCgas");
   
    InitMedium("HPTgas");
    TGeoMedium *HPTmat =gGeoManager->GetMedium("HPTgas");
    
    InitMedium("vacuum");
    TGeoMedium *vacuum =gGeoManager->GetMedium("vacuum");
    
    InitMedium("iron");
    TGeoMedium *Iron =gGeoManager->GetMedium("iron");
    
    InitMedium("copper");
    TGeoMedium *Cu =gGeoManager->GetMedium("copper");
    
    InitMedium("Concrete");
    TGeoMedium *Conc =gGeoManager->GetMedium("Concrete");
    
    TGeoUniformMagField *magField1 = new TGeoUniformMagField(0.,-MagneticField,0.); //magnetic field arm1
    TGeoUniformMagField *magField2 = new TGeoUniformMagField(0.,MagneticField,0.); //magnetic field arm2
    TGeoUniformMagField *retFieldU    = new TGeoUniformMagField(0.,0.,-MagneticField); //magnetic field up return yoke
    TGeoUniformMagField *retFieldL   = new TGeoUniformMagField(0.,0.,MagneticField); //magnetic field low return yoke
    
    Double_t d = 0;
    
    TGeoBBox *MSBox = new TGeoBBox("MagneticSpectrometerBox", XtrSize/2 +10*cm, YtrSize_tot/2, zSizeMS/2);
    TGeoVolume *volMSBox = new TGeoVolume("volMagneticSpectrometer", MSBox, vacuum);
    top->AddNode(volMSBox, 1, new TGeoTranslation(0,10*cm,zMSCenter));
    
    TGeoBBox *UpYokeBox = new TGeoBBox("UpYokeBox", XtrSize/2+10*cm, ReturnYokeH/2, (2*ArmWidth + MiddleGap)/2);
    TGeoVolume *volUpYoke = new TGeoVolume("volUpYoke",UpYokeBox,vacuum);
    volMSBox->AddNode(volUpYoke,1,new TGeoTranslation(0,YtrSize_tot/2 - ReturnYokeH/2,0));
    volUpYoke->SetField(retFieldU);
    
    
    TGeoBBox *FeYoke = new TGeoBBox("FeYoke",XtrSize/2, ReturnYokeH/2, ArmWidth/2);
    TGeoVolume *volFeYoke = new TGeoVolume("volFeYoke",FeYoke,Iron);
    volFeYoke->SetLineColor(kGray+1);
  
    TGeoBBox *FeYoke1 = new TGeoBBox("FeYoke1",XtrSize/2, (ReturnYokeH - 30*cm)/2, MiddleGap/2);
    TGeoVolume *volFeYoke1 = new TGeoVolume("volFeYoke1",FeYoke1,Iron);
    volFeYoke1->SetLineColor(kGray+1);
    
    TGeoBBox *CoilContainer = new TGeoBBox("CoilContainer",XtrSize/2, CoilHeight/2, 40*cm);
    TGeoVolume *volCoilContainer = new TGeoVolume("volCoilContainer",CoilContainer,vacuum);
    
    TGeoBBox *Coil = new TGeoBBox("Coil",XtrSize/2, CoilHeight/2, CoilWidth/2);
    TGeoVolume *volCoil = new TGeoVolume("volCoil",Coil,Cu);
    volCoil->SetLineColor(kOrange -5);
    for(int i = 0; i < NCoils; i++)
    {
        volCoilContainer->AddNode(volCoil, i, new TGeoTranslation(0,0, -40*cm + CoilWidth/2 + i*(CoilGap + CoilWidth)));
    }
    
    //vertical coils
    TGeoBBox *CoilV = new TGeoBBox("CoilV",CoilHeight/2, (90*cm)/2 , CoilWidth/2);
    TGeoVolume *volCoilV = new TGeoVolume("volCoilV",CoilV,Cu);
    volCoilV->SetLineColor(kOrange -5);
    for(int i = 0; i < NCoils; i++)
    {
        volUpYoke->AddNode(volCoilV, i, new TGeoTranslation(XtrSize/2+10*cm - CoilHeight/2,0, -40*cm + CoilWidth/2 + i*(CoilGap + CoilWidth)));
    }
    for(int i = 0; i < NCoils; i++)
    {
        volUpYoke->AddNode(volCoilV, i, new TGeoTranslation(-XtrSize/2-10*cm + CoilHeight/2,0, -40*cm + CoilWidth/2 + i*(CoilGap + CoilWidth)));
    }

    
    volUpYoke->AddNode(volFeYoke,1, new TGeoTranslation(0,0,- (ArmWidth + MiddleGap)/2));
    volUpYoke->AddNode(volFeYoke,2, new TGeoTranslation(0,0,(ArmWidth + MiddleGap)/2));
    volUpYoke->AddNode(volFeYoke1,1,new TGeoTranslation(0,0,0));
    volUpYoke->AddNode(volCoilContainer,1,new TGeoTranslation(0,ReturnYokeH/2 - CoilHeight/2,0)); //up
    volUpYoke->AddNode(volCoilContainer,2,new TGeoTranslation(0,-ReturnYokeH/2 + CoilHeight/2,0)); //low
    
    TGeoBBox *LowYokeBox = new TGeoBBox("LowYokeBox", XtrSize/2 +10*cm, ReturnYokeH/2, (2*ArmWidth + MiddleGap)/2);
    TGeoVolume *volLowYoke = new TGeoVolume("volLowYoke",LowYokeBox,vacuum);
    volMSBox->AddNode(volLowYoke,1,new TGeoTranslation(0,-YtrSize_tot/2 + ReturnYokeH/2,0));
    volLowYoke->SetField(retFieldL);
   
    //vertical coils
    for(int i = 0; i < NCoils; i++)
    {
        volLowYoke->AddNode(volCoilV, i, new TGeoTranslation(XtrSize/2+10*cm - CoilHeight/2,0, -40*cm + CoilWidth/2 + i*(CoilGap + CoilWidth)));
    }
    for(int i = 0; i < NCoils; i++)
    {
        volLowYoke->AddNode(volCoilV, i, new TGeoTranslation(-XtrSize/2-10*cm + CoilHeight/2,0, -40*cm + CoilWidth/2 + i*(CoilGap + CoilWidth)));
    }
    
    volLowYoke->AddNode(volFeYoke,3, new TGeoTranslation(0,0,- (ArmWidth + MiddleGap)/2));
    volLowYoke->AddNode(volFeYoke,4, new TGeoTranslation(0,0,(ArmWidth + MiddleGap)/2));
    volLowYoke->AddNode(volFeYoke1,1,new TGeoTranslation(0,0,0));
    volLowYoke->AddNode(volCoilContainer,3,new TGeoTranslation(0,ReturnYokeH/2 - CoilHeight/2,0)); //up
    volLowYoke->AddNode(volCoilContainer,4,new TGeoTranslation(0,-ReturnYokeH/2 + CoilHeight/2,0)); //low
    
    
    TGeoBBox *Arm1Box = new TGeoBBox("Arm1MSBox", XtrSize/2, YtrSize_Fe/2, ArmWidth/2);
    TGeoVolume *volArm1 = new TGeoVolume("volArm1MS", Arm1Box,vacuum);
    volMSBox ->AddNode(volArm1,1,new TGeoTranslation(0,0,-(MiddleGap+ArmWidth)/2));
    volArm1->SetField(magField1);

    
    TGeoBBox *IronLayer = new TGeoBBox("Iron",XtrSize/2, YtrSize_Fe/2, IronSlabWidth/2);
    TGeoVolume *volIron = new TGeoVolume("volIron",IronLayer,Iron);
    for(Int_t i = 0; i < NSlabs; i++)
    {
        volArm1->AddNode(volIron,i,new TGeoTranslation(0, 0, -ArmWidth/2+i*(IronSlabWidth +RpcWidth) +IronSlabWidth/2));
    }
    
    TGeoBBox *RpcLayer = new TGeoBBox("Rpc", XtrSize/2, YtrSize_Rpc/2, RpcWidth/2);
    TGeoVolume *volRpc = new TGeoVolume("volRpc",RpcLayer,RPCmat);
    volRpc->SetLineColor(kMagenta-10);
    AddSensitiveVolume(volRpc);
    
    for(Int_t i = 0; i < NSlabs-1; i++)
    {
        volArm1->AddNode(volRpc,i,new TGeoTranslation(0, -YtrSize_Fe/2 + YtrSize_Rpc/2, -ArmWidth/2+(i+1)*IronSlabWidth + i*RpcWidth +RpcWidth/2));
    }
    
    TGeoBBox *Arm2Box = new TGeoBBox("Arm2MSBox", XtrSize/2, YtrSize_Fe/2, ArmWidth/2);
    TGeoVolume *volArm2 = new TGeoVolume("volArm2MS", Arm2Box,vacuum);
    volMSBox ->AddNode(volArm2,1,new TGeoTranslation(0,0,(MiddleGap+ArmWidth)/2));
    volArm2->SetField(magField2);
    
    for(Int_t i = 0; i < NSlabs; i++)
    {
        volArm2->AddNode(volIron,i+NSlabs,new TGeoTranslation(0, 0, -ArmWidth/2+i*(IronSlabWidth +RpcWidth) +IronSlabWidth/2));
    }
    
    for(Int_t i = 0; i < NSlabs-1; i++)
    {
        volArm2->AddNode(volRpc,i+NSlabs-1,new TGeoTranslation(0, -YtrSize_Fe/2 + YtrSize_Rpc/2, -ArmWidth/2+(i+1)*IronSlabWidth + i*RpcWidth +RpcWidth/2));
    }
    
    
    //**********
    //Drift tubes behind, within and after the spectro arms (always scintillator planes for now)
    //
    
    TGeoBBox *HPT = new TGeoBBox("HPT", XtrSize/2, YtrSize_Hpt/2, HPTWidth/2);
    TGeoVolume *volHPT = new TGeoVolume("volHPT",HPT,HPTmat);
    volHPT->SetLineColor(kBlue-5);
    AddSensitiveVolume(volHPT);
    
    //1 closer to Goliath
     volMSBox->AddNode(volHPT,1,new TGeoTranslation(0,-10*cm,-zSizeMS/2 + HPTWidth/2));
    
    //2 closer to Arm1
    //NB: 55 cm is the distance between the borders of the last 2 drift tubes
    volMSBox->AddNode(volHPT,2,new TGeoTranslation(0,-10*cm,-zSizeMS/2 + 3*HPTWidth/2 +55*cm));
   
    
    //Central Drift tubes // 3 closer to Arm1, 4 closer to Arm2
    volMSBox->AddNode(volHPT,3,new TGeoTranslation(0,-10*cm,-72*cm/2 - HPTWidth/2));

    
    //NB: 72cm is the distance between the borders of the central drift tubes
    volMSBox->AddNode(volHPT,4,new TGeoTranslation(0,-10*cm,72*cm/2 + HPTWidth/2));
   
    
    //After spectro Drift Tubes 5 closer to Arm, 6 closer to decay vessel
    
    volMSBox->AddNode(volHPT,5,new TGeoTranslation(0,-10*cm,zSizeMS/2 - 3*HPTWidth/2 - 55*cm));
    volMSBox->AddNode(volHPT,6,new TGeoTranslation(0,-10*cm,zSizeMS/2 - HPTWidth/2));
  
    //********
    //Sensitive Volume for Barbara studies placed in top volume. It is at 1 cm from HPT number 6
    //
    //TGeoBBox *Plane = new TGeoBBox("Plane", XtrSize/2, 11*m/2, 0.1*cm/2);
    //TGeoVolume *volPlane = new TGeoVolume("volPlane",Plane,vacuum);
    //volPlane->SetLineColor(kRed-5);
    //AddSensitiveVolume(volPlane);
    //top->AddNode(volPlane, 1, new TGeoTranslation(0,0,zMSCenter + zSizeMS/2+ 1*cm + 0.1*cm/2));
    
    //10 cm of Concrete on which the whole Magnetic Spectrometer volume will be placed
    TGeoBBox *Base = new TGeoBBox("Base", XtrSize/2, 10*cm/2, ArmWidth+MiddleGap/2);
    TGeoVolume *volBase = new TGeoVolume("volBase",Base,Conc);
    volBase->SetLineColor(kYellow-3);
    top->AddNode(volBase,1, new TGeoTranslation(0,-YtrSize_tot/2 + 10*cm/2,zMSCenter));
}

Bool_t  MagneticSpectrometer::ProcessHits(FairVolume* vol)
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
       // Int_t MotherID =p->GetFirstMother();
        //cout <<mp->GetPdgCode();
        //cout << endl;
        TLorentzVector Pos; 
        gMC->TrackPosition(Pos); 
        Double_t xmean = (fPos.X()+Pos.X())/2. ;      
        Double_t ymean = (fPos.Y()+Pos.Y())/2. ;      
        Double_t zmean = (fPos.Z()+Pos.Z())/2. ;     
        AddHit(fTrackID, fVolumeID, TVector3(xmean, ymean,  zmean),
               TVector3(fMom.Px(), fMom.Py(), fMom.Pz()), fTime, fLength,
               fELoss, pdgCode);
        
        // Increment number of muon det points in TParticle
        ShipStack* stack = (ShipStack*) gMC->GetStack();
        stack->AddPoint(ktauRpc);
    }
    
    return kTRUE;
}

void MagneticSpectrometer::EndOfEvent()
{
    fShipRpcPointCollection->Clear();
}


void MagneticSpectrometer::Register()
{
    
    /** This will create a branch in the output tree called
     ShipRpcPoint, setting the last parameter to kFALSE means:
     this collection will not be written to the file, it will exist
     only during the simulation.
     */
    
    FairRootManager::Instance()->Register("ShipRpcPoint", "MagneticSpectrometer",
                                          fShipRpcPointCollection, kTRUE);
}

TClonesArray* MagneticSpectrometer::GetCollection(Int_t iColl) const
{
    if (iColl == 0) { return fShipRpcPointCollection; }
    else { return NULL; }
}

void MagneticSpectrometer::Reset()
{
    fShipRpcPointCollection->Clear();
}


ShipRpcPoint* MagneticSpectrometer::AddHit(Int_t trackID, Int_t detID,
                        TVector3 pos, TVector3 mom,
                        Double_t time, Double_t length,
                        Double_t eLoss, Int_t pdgCode)
{
    TClonesArray& clref = *fShipRpcPointCollection;
    Int_t size = clref.GetEntriesFast();
    //cout << "ShipRpctau hit called"<< pos.z()<<endl;
    return new(clref[size]) ShipRpcPoint(trackID, detID, pos, mom,
                                      time, length, eLoss, pdgCode);
}


ClassImp(MagneticSpectrometer)








