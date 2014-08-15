#include "veto.h"

#include "vetoPoint.h"


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
#include "TGeoTube.h"
#include "TGeoMaterial.h"
#include "TGeoMedium.h"



#include <iostream>
using std::cout;
using std::endl;

veto::veto()
  : FairDetector("veto", kTRUE, kVETO),
    fTrackID(-1),
    fVolumeID(-1),
    fPos(),
    fMom(),
    fTime(-1.),
    fLength(-1.),
    fELoss(-1),
    fvetoPointCollection(new TClonesArray("vetoPoint"))
{
}

veto::veto(const char* name, Bool_t active)
  : FairDetector(name, active, kVETO),
    fTrackID(-1),
    fVolumeID(-1),
    fPos(),
    fMom(),
    fTime(-1.),
    fLength(-1.),
    fELoss(-1),
    fT0z(-2390.),              //!  z-position of veto station
    fT1z(1510.),               //!  z-position of tracking station 1
    fT2z(1710.),               //!  z-position of tracking station 2
    fT3z(2150.),               //!  z-position of tracking station 3
    fT4z(2370.),               //!  z-position of tracking station 4
    fvetoPointCollection(new TClonesArray("vetoPoint"))
{
}

veto::~veto()
{
  if (fvetoPointCollection) {
    fvetoPointCollection->Delete();
    delete fvetoPointCollection;
  }
}

void veto::Initialize()
{
  FairDetector::Initialize();
//  FairRuntimeDb* rtdb= FairRun::Instance()->GetRuntimeDb();
//  vetoGeoPar* par=(vetoGeoPar*)(rtdb->getContainer("vetoGeoPar"));
}

// -----   Private method InitMedium 
Int_t veto::InitMedium(const char* name) 
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
   return geoBuild->createMedium(ShipMedium);
}
// -------------------------------------------------------------------------


Bool_t  veto::ProcessHits(FairVolume* vol)
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

  // Create vetoPoint at exit of active volume
  if ( gMC->IsTrackExiting()    ||
       gMC->IsTrackStop()       ||
       gMC->IsTrackDisappeared()   ) {
    fTrackID  = gMC->GetStack()->GetCurrentTrackNumber();
    fVolumeID = vol->getMCid();
    if (fELoss == 0. ) { return kFALSE; }
    AddHit(fTrackID, fVolumeID, TVector3(fPos.X(),  fPos.Y(),  fPos.Z()),
           TVector3(fMom.Px(), fMom.Py(), fMom.Pz()), fTime, fLength,
           fELoss);

    // Increment number of veto det points in TParticle
    ShipStack* stack = (ShipStack*) gMC->GetStack();
    stack->AddPoint(kVETO);
  }

  return kTRUE;
}

void veto::EndOfEvent()
{

  fvetoPointCollection->Clear();

}



void veto::Register()
{

  /** This will create a branch in the output tree called
      vetoPoint, setting the last parameter to kFALSE means:
      this collection will not be written to the file, it will exist
      only during the simulation.
  */

  FairRootManager::Instance()->Register("vetoPoint", "veto",
                                        fvetoPointCollection, kTRUE);

}


TClonesArray* veto::GetCollection(Int_t iColl) const
{
  if (iColl == 0) { return fvetoPointCollection; }
  else { return NULL; }
}

void veto::Reset()
{
  fvetoPointCollection->Clear();
}
void veto::SetZpositions(Double32_t z0, Double32_t z1, Double32_t z2, Double32_t z3, Double32_t z4)
{
     fT0z = z0;                //!  z-position of veto station
     fT1z = z1;               //!  z-position of tracking station 1
     fT2z = z2;              //!  z-position of tracking station 2
     fT3z = z3;             //!  z-position of tracking station 3
     fT4z = z4;            //!  z-position of tracking station 4
}

void veto::ConstructGeometry()
{
  /** If you are using the standard ASCII input for the geometry
      just copy this and use it for your detector, otherwise you can
      implement here you own way of constructing the geometry. */
    
    TGeoVolume *top=gGeoManager->GetTopVolume();
    InitMedium("Aluminum");
    TGeoMedium *Al =gGeoManager->GetMedium("Aluminum");
    InitMedium("ShipSens");
    TGeoMedium *Se =gGeoManager->GetMedium("ShipSens");

    TGeoBBox *detbox1 = new TGeoBBox("detbox1", 250, 250, 10);
    TGeoBBox *detbox2 = new TGeoBBox("detbox2", 245, 245, 10);

    TGeoBBox *detSens = new TGeoBBox("detSens", 244, 244, 1);
    
    TGeoCompositeShape *detcomp1 = new TGeoCompositeShape("detcomp1", "detbox1-detbox2");
    TGeoVolume *det1 = new TGeoVolume("vetoX", detcomp1, Al);
    det1->SetLineColor(kRed);
    top->AddNode(det1, 1, new TGeoTranslation(0, 0, fT0z));
    
    for (Int_t i=0; i<4; i++) {
     TString nm = "Sveto_"; nm += i;
     TGeoVolume *Sdet = new TGeoVolume(nm, detSens, Se);
     top->AddNode(Sdet, 1, new TGeoTranslation(0, 0, fT0z-4+i*2.));
     AddSensitiveVolume(Sdet);
    }

    TGeoRotation r0;
    r0.SetAngles(15,0,0);
    TGeoTranslation t0(0, 0, fT0z+20);
    TGeoCombiTrans c0(t0, r0);
    TGeoHMatrix *h0 = new TGeoHMatrix(c0);
    TGeoVolume *det2 = new TGeoVolume("vetoS", detcomp1, Al);
    det2->SetLineColor(kRed);
    top->AddNode(det2, 11, h0);

    // tracking station 1
    TGeoVolume *det3 = new TGeoVolume("Tr1X", detcomp1, Al);
    det3->SetLineColor(kRed-7);
    top->AddNode(det3, 2, new TGeoTranslation(0, 0, fT1z));
    TGeoRotation r1;
    r1.SetAngles(15,0,0);
    TGeoTranslation t1(0, 0, fT1z+20);
    TGeoCombiTrans c1(t1, r1);
    TGeoHMatrix *h1 = new TGeoHMatrix(c1);
    TGeoVolume *det4 = new TGeoVolume("Tr1S", detcomp1, Al);
    det4->SetLineColor(kRed+2);
    top->AddNode(det4, 3, h1);

    for (Int_t i=0; i<4; i++) {
     TString nm = "STr1_"; nm += i;
     TGeoVolume *Sdet = new TGeoVolume(nm, detSens, Se);
     top->AddNode(Sdet, 1, new TGeoTranslation(0, 0, fT1z-4+i*2));
     AddSensitiveVolume(Sdet);
    }

    
    // tracking station 2
    TGeoVolume *det5 = new TGeoVolume("Tr2X", detcomp1, Al);
    det5->SetLineColor(kRed-7);
    top->AddNode(det5, 4, new TGeoTranslation(0, 0, fT2z));
    TGeoRotation r2;
    r2.SetAngles(15,0,0);
    TGeoTranslation t2(0, 0, fT2z+20);
    TGeoCombiTrans c2(t2, r2);
    TGeoHMatrix *h2 = new TGeoHMatrix(c2);
    TGeoVolume *det6 = new TGeoVolume("Tr2S", detcomp1, Al);
    det4->SetLineColor(kRed+2);
    top->AddNode(det6, 5, h2);

    for (Int_t i=0; i<4; i++) {
     TString nm = "STr2_"; nm += i;
     TGeoVolume *Sdet = new TGeoVolume(nm, detSens, Se);
     top->AddNode(Sdet, 1, new TGeoTranslation(0, 0, fT2z-4+i*2));
     AddSensitiveVolume(Sdet);
    }
    
    // tracking station 3
    TGeoVolume *det7 = new TGeoVolume("Tr3X", detcomp1, Al);
    det7->SetLineColor(kOrange+10);
    top->AddNode(det7, 6, new TGeoTranslation(0, 0, fT3z));
    TGeoRotation r3;
    r3.SetAngles(15,0,0);
    TGeoTranslation t3(0, 0, fT3z+20);
    TGeoCombiTrans c3(t3, r3);
    TGeoHMatrix *h3 = new TGeoHMatrix(c3);
    TGeoVolume *det8 = new TGeoVolume("Tr3S", detcomp1, Al);
    det8->SetLineColor(kOrange+4);
    top->AddNode(det8, 7, h3);

    for (Int_t i=0; i<4; i++) {
     TString nm = "STr3_"; nm += i;
     TGeoVolume *Sdet = new TGeoVolume(nm, detSens, Se);
     top->AddNode(Sdet, 1, new TGeoTranslation(0, 0, fT3z-4+i*2));
     AddSensitiveVolume(Sdet);
    }
    
    // tracking station 4
    TGeoVolume *det9 = new TGeoVolume("Tr4X", detcomp1, Al);
    det9->SetLineColor(kOrange+10);
    top->AddNode(det9, 8, new TGeoTranslation(0, 0, fT4z));
    TGeoRotation r4;
    r4.SetAngles(15,0,0);
    TGeoTranslation t4(0, 0, fT4z+20);
    TGeoCombiTrans c4(t4, r4);
    TGeoHMatrix *h4 = new TGeoHMatrix(c4);
    TGeoVolume *det10 = new TGeoVolume("Tr4S", detcomp1, Al);
    det10->SetLineColor(kOrange+4);
    top->AddNode(det10, 9, h4);

    for (Int_t i=0; i<4; i++) {
     TString nm = "STr4_"; nm += i;
     TGeoVolume *Sdet = new TGeoVolume(nm, detSens, Se);
     top->AddNode(Sdet, 1, new TGeoTranslation(0, 0, fT4z-4+i*2));
     AddSensitiveVolume(Sdet);
    }
        
}

vetoPoint* veto::AddHit(Int_t trackID, Int_t detID,
                                      TVector3 pos, TVector3 mom,
                                      Double_t time, Double_t length,
                                      Double_t eLoss)
{
  TClonesArray& clref = *fvetoPointCollection;
  Int_t size = clref.GetEntriesFast();
  // cout << "veto hit called "<< pos.z()<<endl;
  return new(clref[size]) vetoPoint(trackID, detID, pos, mom,
         time, length, eLoss);
}

ClassImp(veto)
