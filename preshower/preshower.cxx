#include "preshower.h"

#include "preshowerPoint.h"


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
#include "ShipStack.h"

#include "TClonesArray.h"
#include "TVirtualMC.h"
#include "TGeoManager.h"
#include "TGeoBBox.h"
#include "TGeoCompositeShape.h"
#include "TGeoShapeAssembly.h"
#include "TGeoTube.h"
#include "TGeoMaterial.h"
#include "TGeoMedium.h"
#include "TParticle.h"



#include <iostream>
using std::cout;
using std::endl;

preshower::preshower()
  : FairDetector("preshower", kTRUE, kPreshower),
    fTrackID(-1),
    fVolumeID(-1),
    fPos(),
    fMom(),
    fTime(-1.),
    fLength(-1.),
    fELoss(-1),
    fpreshowerPointCollection(new TClonesArray("preshowerPoint"))
{
}

preshower::preshower(const char* name, Bool_t active)
  : FairDetector(name, active, kPreshower),
    fTrackID(-1),
    fVolumeID(-1),
    fPos(),
    fMom(),
    fTime(-1.),
    fLength(-1.),
    fELoss(-1),
    fpreshowerPointCollection(new TClonesArray("preshowerPoint"))
{
}

preshower::~preshower()
{
  if (fpreshowerPointCollection) {
    fpreshowerPointCollection->Delete();
    delete fpreshowerPointCollection;
  }
}

void preshower::Initialize()
{
  FairDetector::Initialize();
//  FairRuntimeDb* rtdb= FairRun::Instance()->GetRuntimeDb();
//  preshowerGeoPar* par=(preshowerGeoPar*)(rtdb->getContainer("preshowerGeoPar"));
}
// -----   Private method InitMedium 
Int_t preshower::InitMedium(const char* name) 
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
Bool_t  preshower::ProcessHits(FairVolume* vol)
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

  // Create preshowerPoint at exit of active volume
  if ( gMC->IsTrackExiting()    ||
       gMC->IsTrackStop()       ||
       gMC->IsTrackDisappeared()   ) {
    fTrackID  = gMC->GetStack()->GetCurrentTrackNumber();
    //fVolumeID = vol->getMCid();
    //cout << "preshower proc "<< fVolumeID<<" "<<vol->GetName()<<" "<<vol->getVolumeId() <<endl;
    //cout << " "<< gGeoManager->FindVolumeFast(vol->GetName())->GetNumber()<<endl;
    fVolumeID = gGeoManager->FindVolumeFast(vol->GetName())->GetNumber();
    if (fELoss == 0. ) { return kFALSE; }
    TParticle* p=gMC->GetStack()->GetCurrentTrack();
    Int_t pdgCode = p->GetPdgCode();
    AddHit(fTrackID, fVolumeID, TVector3(fPos.X(),  fPos.Y(),  fPos.Z()),
           TVector3(fMom.Px(), fMom.Py(), fMom.Pz()), fTime, fLength,
           fELoss,pdgCode);

    // Increment number of preshower det points in TParticle
    ShipStack* stack = (ShipStack*) gMC->GetStack();
    stack->AddPoint(kPreshower);
  }

  return kTRUE;
}

void preshower::EndOfEvent()
{

  fpreshowerPointCollection->Clear();

}



void preshower::Register()
{

  /** This will create a branch in the output tree called
      preshowerPoint, setting the last parameter to kFALSE means:
      this collection will not be written to the file, it will exist
      only during the simulation.
  */

  FairRootManager::Instance()->Register("preshowerPoint", "preshower",
                                        fpreshowerPointCollection, kTRUE);

}


TClonesArray* preshower::GetCollection(Int_t iColl) const
{
  if (iColl == 0) { return fpreshowerPointCollection; }
  else { return NULL; }
}

void preshower::Reset()
{
  fpreshowerPointCollection->Clear();
}

void preshower::SetZStationPosition2(Double_t z0, Double_t z1)
{
  fM0z=z0;
  fM1z=z1;
  //fM2z=z2;
  //fM3z=z3;
}
void preshower::SetZFilterPosition2(Double_t z0, Double_t z1)
{
  fF0z=z0;
  fF1z=z1;
  // fF2z=z2;
}
void preshower::SetActiveThickness(Double_t activeThickness)
{

  fActiveThickness=activeThickness;
}
void preshower::SetFilterThickness2(Double_t filterThickness0,Double_t filterThickness1)
{
  fFilterThickness0=filterThickness0;
  fFilterThickness1=filterThickness1;
}
void preshower::SetXMax(Double_t xMax)
{
  fXMax=xMax;
}
void preshower::SetYMax(Double_t yMax)
{
  fYMax=yMax;
}
void preshower::ConstructGeometry()
{
  /** If you are using the standard ASCII input for the geometry
      just copy this and use it for your detector, otherwise you can
      implement here you own way of constructing the geometry. */
    
    TGeoVolume *top=gGeoManager->GetTopVolume();
    TGeoVolume *tPreshower = new TGeoVolumeAssembly("PreshowerDetector");

    InitMedium("lead");
    InitMedium("Scintillator");
    
    TGeoMedium *Al =gGeoManager->GetMedium("Scintillator");
    TGeoMedium *A2 =gGeoManager->GetMedium("lead");
    
//    TGeoBBox *detbox1 = new TGeoBBox("detbox1", 250, 250, 10);
//    TGeoBBox *detbox2 = new TGeoBBox("detbox2", 245, 245, 10);
    
//    TGeoCompositeShape *detcomp1 = new TGeoCompositeShape("detcomp1", "detbox1-detbox2");    

//    TGeoVolume *detmu1 = new TGeoVolume("MuX", detcomp1, Al);
    TGeoVolume *preshowerdet0 = gGeoManager->MakeBox("preshowerdet0", Al, fXMax, fYMax, fActiveThickness);
    TGeoVolume *preshowerdet1 = gGeoManager->MakeBox("preshowerdet1", Al, fXMax, fYMax, fActiveThickness);
//    TGeoVolume *preshowerdet2 = gGeoManager->MakeBox("preshowerdet2", Al, fXMax, fYMax, fActiveThickness); 
//    TGeoVolume *preshowerdet3 = gGeoManager->MakeBox("preshowerdet3", Al, fXMax, fYMax, fActiveThickness); 
    
    TGeoVolume *preshowerfilter0 = gGeoManager->MakeBox("preshowerfilter0", A2, fXMax, fYMax, fFilterThickness0);
    TGeoVolume *preshowerfilter1 = gGeoManager->MakeBox("preshowerfilter1", A2, fXMax, fYMax, fFilterThickness1);
//    TGeoVolume *preshowerfilter2 = gGeoManager->MakeBox("preshowerfilter2", A2, fXMax, fYMax, fFilterThickness);

    AddSensitiveVolume(preshowerdet0);
    AddSensitiveVolume(preshowerdet1);
    // AddSensitiveVolume(preshowerdet2);
    //AddSensitiveVolume(preshowerdet3);
    preshowerdet0->SetLineColor(kGreen);
    preshowerdet1->SetLineColor(kGreen);
    // preshowerdet2->SetLineColor(kGreen);
    // preshowerdet3->SetLineColor(kGreen);
    preshowerfilter0->SetLineColor(kBlue);
    preshowerfilter1->SetLineColor(kBlue);
    // preshowerfilter2->SetLineColor(kBlue);
    Double_t zStartPreshower = fM0z;
    tPreshower->AddNode(preshowerdet0, 1, new TGeoTranslation(0, 0, fM0z-zStartPreshower));
    tPreshower->AddNode(preshowerfilter0, 1, new TGeoTranslation(0, 0, fF0z-zStartPreshower));
    tPreshower->AddNode(preshowerdet1, 1, new TGeoTranslation(0, 0, fM1z-zStartPreshower));
    tPreshower->AddNode(preshowerfilter1, 1, new TGeoTranslation(0, 0, fF1z-zStartPreshower));
    // tPreshower->AddNode(preshowerdet2, 1, new TGeoTranslation(0, 0, fM2z-zStartPreshower));
    // tPreshower->AddNode(preshowerfilter2, 1, new TGeoTranslation(0, 0, fF2z-zStartPreshower));
    // tPreshower->AddNode(preshowerdet3, 1, new TGeoTranslation(0, 0, fM3z-zStartPreshower));
          //finish assembly and position
    TGeoShapeAssembly* asmb = dynamic_cast<TGeoShapeAssembly*>(tPreshower->GetShape());
    Double_t totLength = asmb->GetDZ();
    top->AddNode(tPreshower, 1, new TGeoTranslation(0, 0,zStartPreshower+totLength));  
}

preshowerPoint* preshower::AddHit(Int_t trackID, Int_t detID,
                                      TVector3 pos, TVector3 mom,
                                      Double_t time, Double_t length,
                                      Double_t eLoss, Int_t pdgCode)
{
  TClonesArray& clref = *fpreshowerPointCollection;
  Int_t size = clref.GetEntriesFast();
  // cout << "preshower hit called"<< pos.z()<<endl;
  return new(clref[size]) preshowerPoint(trackID, detID, pos, mom,
         time, length, eLoss, pdgCode);
}

ClassImp(preshower)
