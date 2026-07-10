#include "SiWCalo.h"

#include "ShipDetectorList.h"
#include "ShipStack.h"
#include "ShipUnit.h"
#include "SiWCaloPoint.h"

// ROOT / TGeo headers
#include "TGeoBBox.h"
#include "TGeoCompositeShape.h"
#include "TGeoManager.h"
#include "TGeoMaterial.h"
#include "TGeoMedium.h"
#include "TGeoTrd1.h"
#include "TGeoTrd2.h"
#include "TGeoVolume.h"
#include "TParticle.h"
#include "TVector3.h"

// FairROOT headers
#include "FairGeoBuilder.h"
#include "FairGeoInterface.h"
#include "FairGeoLoader.h"
#include "FairGeoMedia.h"
#include "FairGeoNode.h"
#include "FairGeoVolume.h"
#include "FairRootManager.h"
#include "FairRun.h"
#include "FairRuntimeDb.h"
#include "FairVolume.h"

// Additional standard headers
#include "TClonesArray.h"
#include "TString.h"  // for TString
#include "TVirtualMC.h"

using namespace ShipUnit;

SiWCalo::SiWCalo()
    : FairDetector("SiWCalo", kTRUE, kSiWCalo),
      fTrackID(-1),
      fPdgCode(),
      fVolumeID(-1),
      fPos(),
      fMom(),
      fTime(-1.),
      fLength(-1.),
      fELoss(-1),
      fSiWCaloPointCollection(new TClonesArray("SiWCaloPoint")) {}

SiWCalo::SiWCalo(const char* name, Bool_t Active, const char* Title)
    : FairDetector(name, Active, kSiWCalo),
      fTrackID(-1),
      fPdgCode(),
      fVolumeID(-1),
      fPos(),
      fMom(),
      fTime(-1.),
      fLength(-1.),
      fELoss(-1),
      fSiWCaloPointCollection(new TClonesArray("SiWCaloPoint")) {}

SiWCalo::~SiWCalo() {
  if (fSiWCaloPointCollection) {
    fSiWCaloPointCollection->Delete();
    delete fSiWCaloPointCollection;
  }
}

void SiWCalo::Initialize() { FairDetector::Initialize(); }

// -----   Private method InitMedium
Int_t SiWCalo::InitMedium(const char* name) {
  static FairGeoLoader* geoLoad = FairGeoLoader::Instance();
  static FairGeoInterface* geoFace = geoLoad->getGeoInterface();
  static FairGeoMedia* media = geoFace->getMedia();
  static FairGeoBuilder* geoBuild = geoLoad->getGeoBuilder();

  FairGeoMedium* ShipMedium = media->getMedium(name);

  if (!ShipMedium) {
    Fatal("InitMedium", "Material %s not defined in media file.", name);
    return -1111;
  }
  TGeoMedium* medium = gGeoManager->GetMedium(name);
  if (medium != nullptr) return ShipMedium->getMediumIndex();
  return geoBuild->createMedium(ShipMedium);
}

void SiWCalo::SetSiWCaloParameters(Double_t targetWidth, Double_t targetHeight,
                                   Double_t sensorWidth, Double_t sensorLength,
                                   Int_t nLayers, Double_t zPosition,
                                   Double_t targetThickness, Double_t NPixels,
                                   Double_t targetSpacing,
                                   Double_t moduleOffset) {
  fTargetWidth = targetWidth;
  fTargetHeight = targetHeight;
  fSensorWidth = sensorWidth;
  fSensorLength = sensorLength;
  fLayers = nLayers;
  fZPosition = zPosition;
  fTargetThickness = targetThickness;
  fNPixels = NPixels;
  fTargetSpacing = targetSpacing;
  fModuleOffset = moduleOffset;
}

TGeoVolume* SiWCalo::CreateSiliconPlanes(const char* name, Double_t width,
                                         Double_t length, Double_t spacing,
                                         Double_t NPixels, TGeoMedium* silicon,
                                         Int_t layerId) {
  // ------------------------------------------------------------
  // Pixel segmentation
  // ------------------------------------------------------------
  // Factor 2 because now we're considering 2x2 ASUS array
  const Int_t nPixX =
      NPixels;  // In one line there are 4 asics with 8 pixels each => 32 pixels
  const Int_t nPixY = NPixels;  // 32X32=1024 pixels

  Double_t pixX = width / nPixX;
  Double_t pixY = length / nPixY;

  // ------------------------------------------------------------
  // Sensor shape and logical volume
  // ------------------------------------------------------------
  TGeoBBox* SensorShape =
      new TGeoBBox("SensorShape", width / 2.0, length / 2.0,
                   0.65 * mm / 2.0);  // This is the Si sensor thickness!

  TGeoVolume* SensorVolume =
      new TGeoVolume("SensorVolume", SensorShape, silicon);

  SensorVolume->SetLineColor(kRed);
  SensorVolume->SetTransparency(40);

  // ------------------------------------------------------------
  // Pixel segmentation: X then Y
  // ------------------------------------------------------------
  auto* XCells = SensorVolume->Divide("PIXELX",
                                      1,  // X axis
                                      nPixX, -width / 2.0, pixX);

  auto* Pixels = XCells->Divide("PIXELY",
                                2,  // Y axis
                                nPixY, -length / 2.0, pixY);

  // Only the deepest volume is sensitive
  AddSensitiveVolume(Pixels);

  // ------------------------------------------------------------
  // Tracking station (top-level container)
  // ------------------------------------------------------------
  TGeoVolumeAssembly* trackingStation = new TGeoVolumeAssembly(name);

  // ------------------------------------------------------------
  // Single pixel layer
  // ------------------------------------------------------------
  TGeoVolumeAssembly* layer = new TGeoVolumeAssembly("PixelLayer");

  Int_t sensor_id = layerId << 5;  // keep ID scheme compatible

  layer->AddNode(SensorVolume, sensor_id, new TGeoTranslation(0, 0, 0));

  trackingStation->AddNode(layer, 0);

  // ------------------------------------------------------------
  // Return top-level object
  // ------------------------------------------------------------
  return trackingStation;
}

void SiWCalo::ConstructGeometry() {
  InitMedium("tungstenalloySND");
  TGeoMedium* tungsten = gGeoManager->GetMedium("tungstenalloySND");
  InitMedium("air");
  TGeoMedium* air = gGeoManager->GetMedium("air");
  InitMedium("silicon");
  TGeoMedium* Silicon = gGeoManager->GetMedium("silicon");

  // TODO: Add full real material sandwich

  Double_t totalLength = fLayers * fTargetSpacing;

  // --- Create an envelope volume for the detector (green, semi-transparent)
  // ---
  auto envBox = new TGeoBBox("SiWCalo_env", fTargetWidth / 2.,
                             fTargetHeight / 2., totalLength / 2.);
  auto envVol = new TGeoVolume("SiWCalo", envBox, air);
  envVol->SetLineColor(kGreen);
  envVol->SetTransparency(50);

  auto target = new TGeoBBox("Target", fTargetWidth / 2., fTargetHeight / 2.,
                             fTargetThickness / 2.);
  auto targetVol = new TGeoVolume("TargetVol", target, tungsten);
  targetVol->SetLineColor(kGray);
  targetVol->SetTransparency(40);

  for (Int_t i = 0; i < fLayers; i++) {
    // Compute the center position (z) for the current W layer
    Double_t zPos = -totalLength / 2 + i * fTargetSpacing;

    // Place the tungsten layer
    envVol->AddNode(targetVol, i,
                    new TGeoTranslation(0, 0, zPos + fTargetThickness / 2.));

    TGeoVolume* siliconPlanes = CreateSiliconPlanes(
        "TrackerPlane", fSensorWidth, fSensorLength,
        fTargetSpacing - fTargetThickness - 2. * fModuleOffset, fNPixels,
        Silicon, i);
    envVol->AddNode(
        siliconPlanes, i,
        new TGeoTranslation(0, 0, zPos + fTargetThickness + fModuleOffset));
  }

  // Finally, add the envelope to the top volume with the global z offset
  // fZCenter
  gGeoManager->GetTopVolume()->AddNode(envVol, 1,
                                       new TGeoTranslation(0, 0, fZPosition));
}

Bool_t SiWCalo::ProcessHits(FairVolume* vol) {
  /** This method is called from the MC stepping */
  // Set parameters at entrance of volume. Reset ELoss.
  if (gMC->IsTrackEntering()) {
    fELoss = 0.;
    fTime = gMC->TrackTime() * 1.0e09;
    fLength = gMC->TrackLength();
    gMC->TrackPosition(fPos);
    gMC->TrackMomentum(fMom);
  }

  // Sum energy loss for all steps in the active volume
  fELoss += gMC->Edep();

  // Create SiWCaloPoint at exit of active volume
  if (gMC->IsTrackExiting() || gMC->IsTrackStop() ||
      gMC->IsTrackDisappeared()) {
    if (fELoss == 0.) {
      return kFALSE;
    }

    TParticle* p = gMC->GetStack()->GetCurrentTrack();
    fTrackID = gMC->GetStack()->GetCurrentTrackNumber();
    Int_t pdgCode = p->GetPdgCode();
    TLorentzVector Pos;
    gMC->TrackPosition(Pos);
    TLorentzVector Mom;
    gMC->TrackMomentum(Mom);

    Double_t xmean = (fPos.X() + Pos.X()) / 2.;
    Double_t ymean = (fPos.Y() + Pos.Y()) / 2.;
    Double_t zmean = (fPos.Z() + Pos.Z()) / 2.;

    AddHit(fTrackID, fVolumeID, TVector3(xmean, ymean, zmean),
           TVector3(fMom.Px(), fMom.Py(), fMom.Pz()), fTime, fLength, fELoss,
           pdgCode);

    ShipStack* stack = dynamic_cast<ShipStack*>(gMC->GetStack());
    stack->AddPoint(kSiWCalo);
  }
  return kTRUE;
}

void SiWCalo::EndOfEvent() { fSiWCaloPointCollection->Clear(); }

void SiWCalo::Register() {
  TString name = "SiWCaloPoint";
  TString title = "SiWCalo";
  FairRootManager::Instance()->Register(name, title, fSiWCaloPointCollection,
                                        kTRUE);
  LOG(debug) << this->GetName() << ", Register() says: registered " << name
             << " collection";
}

TClonesArray* SiWCalo::GetCollection(Int_t iColl) const {
  if (iColl == 0) {
    return fSiWCaloPointCollection;
  } else {
    return NULL;
  }
}

void SiWCalo::Reset() { fSiWCaloPointCollection->Clear(); }

SiWCaloPoint* SiWCalo::AddHit(Int_t trackID, Int_t detID, TVector3 pos,
                              TVector3 mom, Double_t time, Double_t length,
                              Double_t eLoss, Int_t pdgCode) {
  TClonesArray& clref = *fSiWCaloPointCollection;
  Int_t size = clref.GetEntriesFast();
  return new (clref[size])
      SiWCaloPoint(trackID, detID, pos, mom, time, length, eLoss, pdgCode);
}
