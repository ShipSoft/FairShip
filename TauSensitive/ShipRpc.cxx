#include "ShipRpc.h"

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

ShipRpc::ShipRpc()
  : FairDetector("ShipRpc",kTRUE, ktauRpc),
    fTrackID(-1),
    fVolumeID(-1),
    fPos(),
    fMom(),
    fTime(-1.),
    fLength(-1.),
    fELoss(-1),
    fShipRpcPointCollection(new TClonesArray("ShipRpcPoint"))
{
}

ShipRpc::ShipRpc(const char* name, const Double_t zRpcL, const Double_t zDriftL, const Double_t DriftL,const Double_t IronL, const Double_t ScintL, const Double_t MiddleG, Bool_t Active,const char* Title)
  : FairDetector(name, Active, ktauRpc),
    fTrackID(-1),
    fVolumeID(-1),
    fPos(),
    fMom(),
    fTime(-1.),
    fLength(-1.),
    fELoss(-1),
    fShipRpcPointCollection(new TClonesArray("ShipRpcPoint"))
{
    zRpcLayer = zRpcL;
    zDriftLayer = zDriftL;
    DriftLenght = DriftL;
    IronLenght = IronL;
    ScintLenght = ScintL;
    MiddleGap = MiddleG;
}

ShipRpc::~ShipRpc()
{
    if (fShipRpcPointCollection) {
        fShipRpcPointCollection->Delete();
        delete fShipRpcPointCollection;
    }
}

void ShipRpc::Initialize()
{
    FairDetector::Initialize();
}

// -----   Private method InitMedium 
Int_t ShipRpc::InitMedium(const char* name)
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

void ShipRpc::ConstructGeometry()
{

    
    Double_t XtrSize = 4.5*m; //Transversal size of the scintillator plane in m
    Double_t YtrSize = 8*m;
    Int_t NScintPlanes = 11; //Number of Scintillator Planes
    
    TGeoVolume *top=gGeoManager->GetTopVolume();
    InitMedium("RPCgas");
    TGeoMedium *RPCmat =gGeoManager->GetMedium("RPCgas");
   
    InitMedium("HPTgas");
    TGeoMedium *HPTmat =gGeoManager->GetMedium("HPTgas");
    
    Double_t Field = 1.57*tesla;
    TGeoUniformMagField *magField = new TGeoUniformMagField(0.,-Field,0.);
    TGeoUniformMagField *RetField     = new TGeoUniformMagField(0.,Field,0.);

    
    Double_t d = 0;
    
    TGeoBBox *ScintLayer = new TGeoBBox("detScint", XtrSize/2, YtrSize/2, ScintLenght/2);
    TGeoVolume *volScintLayer = new TGeoVolume("volScintLayer",ScintLayer,RPCmat);
    volScintLayer->SetLineColor(kMagenta-10);
    volScintLayer->SetField(magField);
    for(Int_t i = 0; i< NScintPlanes; i++)
    {
        d = zRpcLayer - i*(IronLenght+ScintLenght);
        top->AddNode(volScintLayer,i,new TGeoTranslation(0, 0, d));
        AddSensitiveVolume(volScintLayer);
    }

    
    Double_t d1 = d- (MiddleGap + IronLenght+ScintLenght/2); //z coord of the center of the last layer of the first spectrometer
    //  cout << d1 << endl;
    Double_t d2 = 0;
    
    TGeoVolume *volScintLayer2 = new TGeoVolume("volScintLayer2",ScintLayer,RPCmat);
    volScintLayer2->SetLineColor(kMagenta-10);
    volScintLayer2->SetField(RetField);
    for(Int_t i = 0; i< NScintPlanes; i++)
    {
        d2 = d1-i*(IronLenght+ScintLenght);
        top->AddNode(volScintLayer2,i,new TGeoTranslation(0, 0, d2));
        AddSensitiveVolume(volScintLayer2);
    }
    
    //**********
    //Drift tubes behind, within and after the spectro arms (always scintillator planes for now)
    //
    
    TGeoBBox *DriftLayer = new TGeoBBox("detDrift", XtrSize/2, YtrSize/2, DriftLenght/2);
    TGeoVolume *volDriftLayer = new TGeoVolume("volDriftLayer",DriftLayer,HPTmat);
    volDriftLayer->SetLineColor(kBlue-5);
    top->AddNode(volDriftLayer,1,new TGeoTranslation(0,0,zDriftLayer));
    AddSensitiveVolume(volDriftLayer);
    
    
    //NB: 55 cm is the distance between the borders of the last 2 drift tubes
    TGeoVolume *volDriftLayer1 = new TGeoVolume("volDriftLayer1",DriftLayer,HPTmat);
    volDriftLayer1->SetLineColor(kBlue-5);
    Double_t d3 = zDriftLayer - DriftLenght - 55*cm;
    top->AddNode(volDriftLayer1,1,new TGeoTranslation(0,0,d3));
    AddSensitiveVolume(volDriftLayer1);
    
    //Central Drift tubes
    
     TGeoVolume *volDriftLayer2 = new TGeoVolume("volDriftLayer2",DriftLayer,HPTmat);
    volDriftLayer2->SetLineColor(kBlue-5);
    Double_t d4 = d - ScintLenght/2 - IronLenght - 4*cm- DriftLenght/2;
    top->AddNode(volDriftLayer2,1,new TGeoTranslation(0,0,d4));
    AddSensitiveVolume(volDriftLayer2);
    
    //NB: 75cm is the distance between the borders of the central drift tubes
    
     TGeoVolume *volDriftLayer3 = new TGeoVolume("volDriftLayer3",DriftLayer,HPTmat);
    volDriftLayer3->SetLineColor(kBlue-5);
    Double_t d5 = d4 - DriftLenght - 75*cm;
    top->AddNode(volDriftLayer3,1,new TGeoTranslation(0,0,d5));
     AddSensitiveVolume(volDriftLayer3);
    
    //Pre-spectro Drift Tubes
    
     TGeoVolume *volDriftLayer4 = new TGeoVolume("volDriftLayer4",DriftLayer,HPTmat);
    volDriftLayer4->SetLineColor(kBlue-5);
    Double_t d6 = d2 - ScintLenght/2 - IronLenght - 4*cm- DriftLenght/2;
    top->AddNode(volDriftLayer4,1,new TGeoTranslation(0,0,d6));
     AddSensitiveVolume(volDriftLayer4);
    
     TGeoVolume *volDriftLayer5 = new TGeoVolume("volDriftLayer5",DriftLayer,HPTmat);
    volDriftLayer5->SetLineColor(kBlue-5);
    Double_t d7 = d6 - DriftLenght - 55*cm;
    top->AddNode(volDriftLayer5,1,new TGeoTranslation(0,0,d7));
     AddSensitiveVolume(volDriftLayer5);
    
}

Bool_t  ShipRpc::ProcessHits(FairVolume* vol)
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
        //cout << pdgCode << endl;
        AddHit(fTrackID, fVolumeID, TVector3(fPos.X(),  fPos.Y(),  fPos.Z()),
               TVector3(fMom.Px(), fMom.Py(), fMom.Pz()), fTime, fLength,
               fELoss, pdgCode);
        
        // Increment number of muon det points in TParticle
        ShipStack* stack = (ShipStack*) gMC->GetStack();
        stack->AddPoint(ktauRpc);
    }
    
    return kTRUE;
}

void ShipRpc::EndOfEvent()
{
    fShipRpcPointCollection->Clear();
}


void ShipRpc::Register()
{
    
    /** This will create a branch in the output tree called
     ShipRpcPoint, setting the last parameter to kFALSE means:
     this collection will not be written to the file, it will exist
     only during the simulation.
     */
    
    FairRootManager::Instance()->Register("ShipRpcPoint", "ShipRpc",
                                          fShipRpcPointCollection, kTRUE);
}

TClonesArray* ShipRpc::GetCollection(Int_t iColl) const
{
    if (iColl == 0) { return fShipRpcPointCollection; }
    else { return NULL; }
}

void ShipRpc::Reset()
{
    fShipRpcPointCollection->Clear();
}


ShipRpcPoint* ShipRpc::AddHit(Int_t trackID, Int_t detID,
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


ClassImp(ShipRpc)








