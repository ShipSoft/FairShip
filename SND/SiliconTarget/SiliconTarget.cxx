#include "SiliconTarget.h"

#include "ShipDetectorList.h"
#include "ShipStack.h"
#include "ShipUnit.h"
#include "SiliconTargetPoint.h"

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
#include "TString.h"   // for TString
#include "TVirtualMC.h"

using namespace ShipUnit;

SiliconTarget::SiliconTarget()
    : FairDetector("SiliconTarget", kTRUE, kSiliconTarget)
    , fTrackID(-1)
    , fPdgCode()
    , fVolumeID(-1)
    , fPos()
    , fMom()
    , fTime(-1.)
    , fLength(-1.)
    , fELoss(-1)
    , fSiliconTargetPointCollection(new TClonesArray("SiliconTargetPoint"))
{}

SiliconTarget::SiliconTarget(const char* name, Bool_t Active, const char* Title)
    : FairDetector(name, Active, kSiliconTarget)
    , fTrackID(-1)
    , fPdgCode()
    , fVolumeID(-1)
    , fPos()
    , fMom()
    , fTime(-1.)
    , fLength(-1.)
    , fELoss(-1)
    , fSiliconTargetPointCollection(new TClonesArray("SiliconTargetPoint"))
{}

SiliconTarget::~SiliconTarget()
{
    if (fSiliconTargetPointCollection) {
        fSiliconTargetPointCollection->Delete();
        delete fSiliconTargetPointCollection;
    }
}

void SiliconTarget::Initialize()
{
    FairDetector::Initialize();
}

// -----   Private method InitMedium
Int_t SiliconTarget::InitMedium(const char* name)
{
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
    if (medium != nullptr)
        return ShipMedium->getMediumIndex();
    return geoBuild->createMedium(ShipMedium);
}

void SiliconTarget::SetSiliconTargetParameters(Double_t targetWidth,
                                               Double_t targetHeight,
                                               Double_t sensorWidth,
                                               Double_t sensorLength,
                                               Int_t nLayers,
                                               Double_t zPosition,
                                               Double_t targetThickness,
                                               Double_t targetSpacing,
                                               Double_t moduleOffset)
{

    fTargetWidth = targetWidth;
    fTargetHeight = targetHeight;
    fSensorWidth = sensorWidth;
    fSensorLength = sensorLength;
    fLayers = nLayers;
    fZPosition = zPosition;
    fTargetThickness = targetThickness;
    fTargetSpacing = targetSpacing;
    fModuleOffset = moduleOffset;
}

TGeoVolume* SiliconTarget::CreateSiliconPlanes(const char* name,
                                               Double_t width,
                                               Double_t length,
                                               Double_t spacing,
                                               TGeoMedium* silicon,
                                               Int_t layerId)
{
    Double_t strip_pitch = 75.5 * um;
    Int_t nRows = 2;
    Int_t nCols = 4;
    Int_t nPlanes = 2;

    TGeoBBox* SensorShape = new TGeoBBox("SensorShape", width / 2, length / 2, 0.3 * mm / 2);
    TGeoVolume* SensorVolume = new TGeoVolume("SensorVolume", SensorShape, silicon);
    SensorVolume->SetLineColor(kRed);
    SensorVolume->SetTransparency(40);

    auto* Strips = SensorVolume->Divide("SLICEX", 1, 1298, -width / 2, strip_pitch);
    AddSensitiveVolume(Strips);

    TGeoVolumeAssembly* trackingStation = new TGeoVolumeAssembly("TrackingStation");
    // Each tracking station consists of X and Y planes
    for (Int_t plane = 0; plane < nPlanes; plane++) {
        TGeoVolumeAssembly* trackerPlane = new TGeoVolumeAssembly("TrackerPlane");
        // Each plane consists of 8 modules
        for (Int_t column = 0; column < nCols; column++) {
            for (Int_t row = 0; row < nRows; row++) {
                Int_t sensor_id = (layerId << 5) + (plane << 4) + (column << 2) + (row << 1);
                // Add 1mm gap between sensors for realistic placement
                trackerPlane->AddNode(SensorVolume,
                                      sensor_id,
                                      new TGeoTranslation((-1.5 * width - 2. * mm) + (column * width + column * 1 * mm),
                                                          (length / 2. + 0.5 * mm) - row * (length + 1. * mm),
                                                          0));
            }
        }
        if (plane == 0) {
            trackingStation->AddNode(trackerPlane, plane);
        } else if (plane == 1) {
            // Rotate the second plane by 90 degrees and translate such that the planes are evenly spaced.
            trackingStation->AddNode(
                trackerPlane,
                plane,
                new TGeoCombiTrans(TGeoTranslation(0, 0, spacing), TGeoRotation("y_rot", 0, 0, 90)));
        }
    }

    return trackingStation;
}
void SiliconTarget::ConstructGeometry()
{
    InitMedium("tungstenalloySND");
    TGeoMedium* tungsten = gGeoManager->GetMedium("tungstenalloySND");
    InitMedium("air");
    TGeoMedium* air = gGeoManager->GetMedium("air");
    InitMedium("silicon");
    TGeoMedium* Silicon = gGeoManager->GetMedium("silicon");

    Double_t totalLength = fLayers * fTargetSpacing;

    // --- Create an envelope volume for the detector (green, semi-transparent) ---
    auto envBox = new TGeoBBox("SiliconTarget_env", fTargetWidth / 2., fTargetHeight / 2., totalLength / 2.);
    auto envVol = new TGeoVolume("SiliconTarget", envBox, air);
    envVol->SetLineColor(kGreen);
    envVol->SetTransparency(50);

    auto target = new TGeoBBox("Target", fTargetWidth / 2., fTargetHeight / 2., fTargetThickness / 2.);
    auto targetVol = new TGeoVolume("TargetVol", target, tungsten);
    targetVol->SetLineColor(kGray);
    targetVol->SetTransparency(40);

    for (Int_t i = 0; i < fLayers; i++) {
        // Compute the center position (z) for the current W layer
        Double_t zPos = -totalLength / 2 + i * fTargetSpacing;

        // Place the tungsten layer
        envVol->AddNode(targetVol, i, new TGeoTranslation(0, 0, zPos + fTargetThickness / 2.));

        TGeoVolume* siliconPlanes = CreateSiliconPlanes("TrackerPlane",
                                                        fSensorWidth,
                                                        fSensorLength,
                                                        fTargetSpacing - fTargetThickness - 2. * fModuleOffset,
                                                        Silicon,
                                                        i);
        envVol->AddNode(siliconPlanes, i, new TGeoTranslation(0, 0, zPos + fTargetThickness + fModuleOffset));
    }

    // Finally, add the envelope to the top volume with the global z offset fZCenter
    gGeoManager->GetTopVolume()->AddNode(envVol, 1, new TGeoTranslation(0, 0, fZPosition));
}

Bool_t SiliconTarget::ProcessHits(FairVolume* vol)
{
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

    // Create SiliconTargetPoint at exit of active volume
    if (gMC->IsTrackExiting() || gMC->IsTrackStop() || gMC->IsTrackDisappeared()) {

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

        Int_t strip_id = 0;
        Int_t sensor_id = 0;
        gMC->CurrentVolID(strip_id);
        gMC->CurrentVolOffID(1, sensor_id);
        fVolumeID = (sensor_id << 12) + strip_id;

        AddHit(fTrackID,
               fVolumeID,
               TVector3(xmean, ymean, zmean),
               TVector3(fMom.Px(), fMom.Py(), fMom.Pz()),
               fTime,
               fLength,
               fELoss,
               pdgCode);

        ShipStack* stack = dynamic_cast<ShipStack*>(gMC->GetStack());
        stack->AddPoint(kSiliconTarget);
    }
    return kTRUE;
}

void SiliconTarget::EndOfEvent()
{
    fSiliconTargetPointCollection->Clear();
}

void SiliconTarget::Register()
{
    TString name = "SiliconTargetPoint";
    TString title = "SiliconTarget";
    FairRootManager::Instance()->Register(name, title, fSiliconTargetPointCollection, kTRUE);
    LOG(debug) << this->GetName() << ", Register() says: registered " << name << " collection";
}

TClonesArray* SiliconTarget::GetCollection(Int_t iColl) const
{
    if (iColl == 0) {
        return fSiliconTargetPointCollection;
    } else {
        return NULL;
    }
}

void SiliconTarget::Reset()
{
    fSiliconTargetPointCollection->Clear();
}

SiliconTargetPoint* SiliconTarget::AddHit(Int_t trackID,
                                          Int_t detID,
                                          TVector3 pos,
                                          TVector3 mom,
                                          Double_t time,
                                          Double_t length,
                                          Double_t eLoss,
                                          Int_t pdgCode)
{
    TClonesArray& clref = *fSiliconTargetPointCollection;
    Int_t size = clref.GetEntriesFast();
    return new (clref[size]) SiliconTargetPoint(trackID, detID, pos, mom, time, length, eLoss, pdgCode);
}
