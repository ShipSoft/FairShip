// SciFi.cxx
//  SciFi, twelve scifi modules physically connected two by two.

#include "SciFi.h"
//#include "MagneticSciFi.h"
#include "SciFiPoint.h"
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
#include "TGeoArb8.h"
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

SciFi::SciFi()
  : FairDetector("HighPrecisionTrackers",kTRUE, kSciFi),
  fTrackID(-1),
  fPdgCode(),
  fVolumeID(-1),
  fPos(),
  fMom(),
  fTime(-1.),
  fLength(-1.),
  fELoss(-1),
  fSciFiPointCollection(new TClonesArray("SciFiPoint"))
{
}

SciFi::SciFi(const char* name, const Double_t DX, const Double_t DY, const Double_t DZ, Bool_t Active,const char* Title)
  : FairDetector(name, Active, kSciFi),
  fTrackID(-1),
  fPdgCode(),
  fVolumeID(-1),
  fPos(),
  fMom(),
  fTime(-1.),
  fLength(-1.),
  fELoss(-1),
  fSciFiPointCollection(new TClonesArray("SciFiPoint"))
{
  DimX = DX;
  DimY = DY;
  DimZ = DZ;
}

SciFi::~SciFi()
{
  if (fSciFiPointCollection) {
    fSciFiPointCollection->Delete();
    delete fSciFiPointCollection;
  }
}

void SciFi::Initialize()
{
  FairDetector::Initialize();
}

// -----   Private method InitMedium
Int_t SciFi::InitMedium(const char* name)
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

void SciFi::SetBoxParam(Double_t SX, Double_t SY, Double_t SZ, Double_t zBox)
{
  SBoxX = SX;
  SBoxY = SY;
  SBoxZ = SZ;
  zBoxPosition = zBox;
}
//dimensions of SciFi stations
void SciFi::SetStationDimensions(Double_t SciFiStationDX, Double_t SciFiStationDY, Double_t SciFiStationDZ)
{
  DimX = SciFiStationDX;
  DimY = SciFiStationDY;
  DimZ = SciFiStationDZ;
}


void SciFi::SetStationPositions(Int_t nstation, Double_t posx, Double_t posy, Double_t posz)
{
  xs[nstation] = posx;
  ys[nstation] = posy;
  zs[nstation] = posz;
}

void SciFi::SetStationNumber(Int_t nSciFistations)
{
  nSciFi = nSciFistations;
}






//
void SciFi::ConstructGeometry()
{

  InitMedium("silicon");
  TGeoMedium *Silicon = gGeoManager->GetMedium("silicon");

  TGeoVolume *top = gGeoManager->GetTopVolume();

  //computing the largest offsets in order to set SciFiBox dimensions correctly
  Double_t offsetxmax = 0., offsetymax = 0.;
  for (int istation = 0; istation < nSciFi; istation++){
    if (TMath::Abs(xs[istation]) > offsetxmax) offsetxmax = TMath::Abs(xs[istation]);
    if (TMath::Abs(ys[istation]) > offsetymax) offsetymax = TMath::Abs(ys[istation]);
  }
  TGeoVolumeAssembly *volSciFiBox = new TGeoVolumeAssembly("volSciFiBox");
  //positioning the mother volume
  top->AddNode(volSciFiBox, 1, new TGeoTranslation(0,0,zBoxPosition)); 


  TGeoBBox *SciFiy = new TGeoBBox("SciFiy", DimX/2, DimY/2, DimZ/2); //long along y
  TGeoVolume *volSciFiy = new TGeoVolume("volSciFiy",SciFiy,Silicon);
  volSciFiy->SetLineColor(kBlue-5);
  AddSensitiveVolume(volSciFiy);

  TGeoBBox *SciFix = new TGeoBBox("SciFix", (DimX)/2, (DimY)/2, DimZ/2); //long along x
  TGeoVolume *volSciFix = new TGeoVolume("volSciFix",SciFix,Silicon);
  volSciFix->SetLineColor(kBlue-5);
  AddSensitiveVolume(volSciFix);

  //id convention: 1{a}{b}, a = number of pair (from 1 to 4), b = element of the pair (1 or 2)
  Int_t SciFiIDlist[8] = {111,112,121,122,131,132,141,142};

  //Alternated scifi stations optimized for y and x measurements
  Bool_t vertical[12] = {kTRUE,kTRUE,kFALSE,kFALSE,kFALSE,kFALSE,kTRUE,kTRUE};

  for (int iscifi = 0; iscifi < nSciFi; iscifi++){
    if (vertical[iscifi]) volSciFiBox->AddNode(volSciFiy, SciFiIDlist[iscifi], new TGeoTranslation(xs[iscifi],ys[iscifi],-SBoxZ/2.+ zs[iscifi])); //compensation for the Node offset
    else volSciFiBox->AddNode(volSciFix, SciFiIDlist[iscifi], new TGeoTranslation(xs[iscifi],ys[iscifi],-SBoxZ/2.+ zs[iscifi]));
  }

}

Bool_t  SciFi::ProcessHits(FairVolume* vol)
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

    if (fELoss == 0. ) { return kFALSE; }
    TParticle* p=gMC->GetStack()->GetCurrentTrack();
    Int_t pdgCode = p->GetPdgCode();
    //Int_t fMotherID =p->GetFirstMother();
    gMC->CurrentVolID(fVolumeID);

    TLorentzVector Pos;
    gMC->TrackPosition(Pos);
    Double_t xmean = (fPos.X()+Pos.X())/2. ;
    Double_t ymean = (fPos.Y()+Pos.Y())/2. ;
    Double_t zmean = (fPos.Z()+Pos.Z())/2. ;

    AddHit(fTrackID, fVolumeID, TVector3(xmean, ymean,  zmean), TVector3(fMom.Px(), fMom.Py(), fMom.Pz()), fTime, fLength,fELoss, pdgCode);

    // Increment number of muon det points in TParticle
    ShipStack* stack = (ShipStack*) gMC->GetStack();
    stack->AddPoint(kSciFi);
  }

  return kTRUE;
}

void SciFi::EndOfEvent()
{
  fSciFiPointCollection->Clear();
}


void SciFi::Register()
{

  /** This will create a branch in the output tree called
    SciFiPoint, setting the last parameter to kFALSE means:
    this collection will not be written to the file, it will exist
    only during the simulation.
    */

  FairRootManager::Instance()->Register("SciFiPoint", "SciFi",
      fSciFiPointCollection, kTRUE);
}

// -----   Public method to Decode volume info  -------------------------------------------

TClonesArray* SciFi::GetCollection(Int_t iColl) const
{
  if (iColl == 0) { return fSciFiPointCollection; }
  else { return NULL; }
}

void SciFi::Reset()
{
  fSciFiPointCollection->Clear();
}


SciFiPoint* SciFi::AddHit(Int_t trackID, Int_t detID,
    TVector3 pos, TVector3 mom,
    Double_t time, Double_t length,
    Double_t eLoss, Int_t pdgCode)

{
  TClonesArray& clref = *fSciFiPointCollection;
  Int_t size = clref.GetEntriesFast();

  return new(clref[size]) SciFiPoint(trackID, detID, pos, mom,time, length, eLoss, pdgCode);
}


ClassImp(SciFi)
