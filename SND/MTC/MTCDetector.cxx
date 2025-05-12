// MTC detector specific headers
#include "MTCDetector.h"

#include "MtcDetPoint.h"
#include "ShipDetectorList.h"
#include "ShipStack.h"
#include "ShipUnit.h"

// ROOT / TGeo headers
#include "TGeoBBox.h"
#include "TGeoCompositeShape.h"
#include "TGeoManager.h"
#include "TGeoMaterial.h"
#include "TGeoMedium.h"
#include "TGeoPara.h"
#include "TGeoTrd1.h"
#include "TGeoTrd2.h"
#include "TGeoTube.h"
#include "TGeoUniformMagField.h"
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
#include "TList.h"       // for TListIter, TList (ptr only)
#include "TObjArray.h"   // for TObjArray
#include "TString.h"     // for TString
#include "TVirtualMC.h"

#include <iosfwd>     // for ostream
#include <iostream>   // for operator<<, basic_ostream, etc
#include <stddef.h>   // for NULL
using std::cout;
using std::endl;
using namespace ShipUnit;

MTCDetector::MTCDetector()
    : FairDetector("MTC", kTRUE, kMTC)
    , fTrackID(-1)
    , fPdgCode()
    , fVolumeID(-1)
    , fPos()
    , fMom()
    , fTime(-1.)
    , fLength(-1.)
    , fELoss(-1)
    , fMTCDetectorPointCollection(new TClonesArray("MtcDetPoint"))
{}

MTCDetector::MTCDetector(const char* name, Bool_t Active, const char* Title, Int_t DetId)
    : FairDetector(name, Active, kMTC)
    , fTrackID(-1)
    , fVolumeID(-1)
    , fPos()
    , fMom()
    , fTime(-1.)
    , fLength(-1.)
    , fELoss(-1)
    , fMTCDetectorPointCollection(new TClonesArray("MtcDetPoint"))
{}

MTCDetector::~MTCDetector()
{
    if (fMTCDetectorPointCollection) {
        fMTCDetectorPointCollection->Delete();
        delete fMTCDetectorPointCollection;
    }
}

// -----   Private method InitMedium
Int_t MTCDetector::InitMedium(const char* name)
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

void MTCDetector::SetMTCParameters(Double_t w,
                                   Double_t h,
                                   Double_t iron,
                                   Double_t sciFi,
                                   Double_t scint,
                                   Int_t layers,
                                   Double_t z,
                                   Double_t field)
{
    fWidth = w;
    fHeight = h;
    fIronThick = iron;
    fSciFiThick = sciFi;
    fScintThick = scint;
    fLayers = layers;
    fZCenter = z;
    fFieldY = field;
}


// Updated SciFi module builder with fiber placements
TGeoVolume* MTCDetector::CreateSegmentedLayer(const char* name,
                                              Double_t width,
                                              Double_t height,
                                              Double_t thickness,
                                              Double_t cellSizeX,
                                              Double_t cellSizeY,
                                              TGeoMedium* material,
                                              Int_t color,
                                              Double_t transparency,
                                              Int_t LayerId)
{
    auto mother = new TGeoBBox(Form("%s_mother", name), width / 2, height / 2, thickness / 2);
    auto motherVol = new TGeoVolume(Form("%s_mother", name), mother, material);
    motherVol->SetLineColor(color);
    motherVol->SetTransparency(transparency);

    auto cell = new TGeoBBox(Form("%s_cell", name), cellSizeX / 2, cellSizeY / 2, thickness / 2);
    auto cellVol = new TGeoVolume(Form("%s_cell", name), cell, material);
    cellVol->SetLineColor(color);
    cellVol->SetTransparency(transparency);
    AddSensitiveVolume(cellVol);
    Int_t nX = Int_t(width / cellSizeX);
    Int_t nY = Int_t(height / cellSizeY);

    for (Int_t i = 0; i < nX; i++) {
        for (Int_t j = 0; j < nY; j++) {
            Double_t x = -width / 2 + cellSizeX * (i + 0.5);
            Double_t y = -height / 2 + cellSizeY * (j + 0.5);
            motherVol->AddNode(cellVol, 30000000 + LayerId * 100000 + i * nY + j, new TGeoTranslation(x, y, 0));
        }
    }
    return motherVol;
}

TGeoVolume* MTCDetector::CreateSciFiModule(const char* name,
                                           Double_t width,
                                           Double_t height,
                                           Double_t thickness,
                                           Int_t LayerId)
{
    // Define sublayer thicknesses (in cm)
    // These values mimic the GEANT4 setup:
    Double_t lowerIronThick = 0.3;    // 3 mm
    Double_t fiberMatThick = 0.135;   // 1.35 mm (each fiber mat)
    Double_t airGap = 0.1;            // 1 mm
    Double_t upperIronThick = 0.3;    // 3 mm
    Double_t zLowerIronInt = -3.5 / 10;
    Double_t zFiberMat1 = -1.325 / 10;
    Double_t zAirGap = -0.15 / 10;
    Double_t zFiberMat2 = 1.025 / 10;
    Double_t zUpperIronInt = 3.2 / 10;
    // Total module thickness = 0.3 + 0.135 + 0.1 + 0.135 + 0.3 ≈ 1.0 cm

    // Create the mother volume for the SciFi module
    auto modMother = new TGeoBBox(Form("%s_mother", name), width / 2, height / 2, thickness / 2);
    auto modMotherVol = new TGeoVolume(Form("%s_mother", name), modMother, gGeoManager->GetMedium("SciFiMat"));
    // AddSensitiveVolume(modMotherVol);
    modMotherVol->SetLineColor(kGreen + 2);
    modMotherVol->SetTransparency(40);

    // --- Lower Internal Iron ---
    auto lowerIronBox = new TGeoBBox(Form("%s_lowerIron", name), width / 2, height / 2, lowerIronThick / 2);
    auto lowerIronVol = new TGeoVolume(Form("%s_lowerIron", name), lowerIronBox, gGeoManager->GetMedium("iron"));
    lowerIronVol->SetLineColor(kGray + 1);
    lowerIronVol->SetTransparency(20);
    // AddSensitiveVolume(lowerIronVol);
    modMotherVol->AddNode(lowerIronVol, 1, new TGeoTranslation(0, 0, zLowerIronInt));

    // --- Fiber Mat U (Lower SciFi Mat) ---
    auto fiberMatBoxU = new TGeoBBox(Form("%s_fiberMat_U", name), width / 2, height / 2, fiberMatThick / 2);
    auto fiberMatVolU = new TGeoVolume(Form("%s_fiberMat_U", name), fiberMatBoxU, gGeoManager->GetMedium("SciFiMat"));
    // AddSensitiveVolume(fiberMatVolU);
    modMotherVol->AddNode(fiberMatVolU, 1, new TGeoTranslation(0, 0, zFiberMat1));

    // --- Fiber Mat V (Upper SciFi Mat) ---
    auto fiberMatBoxV = new TGeoBBox(Form("%s_fiberMat_V", name), width / 2, height / 2, fiberMatThick / 2);
    auto fiberMatVolV = new TGeoVolume(Form("%s_fiberMat_V", name), fiberMatBoxV, gGeoManager->GetMedium("SciFiMat"));
    // AddSensitiveVolume(fiberMatVolV);
    modMotherVol->AddNode(fiberMatVolV, 2, new TGeoTranslation(0, 0, zFiberMat2));

    // --- Upper Internal Iron ---
    auto upperIronBox = new TGeoBBox(Form("%s_upperIron", name), width / 2, height / 2, upperIronThick / 2);
    auto upperIronVol = new TGeoVolume(Form("%s_upperIron", name), upperIronBox, gGeoManager->GetMedium("iron"));
    upperIronVol->SetLineColor(kGray + 1);
    upperIronVol->SetTransparency(20);
    modMotherVol->AddNode(upperIronVol, 1, new TGeoTranslation(0, 0, zUpperIronInt));

    // -----------------------------
    // Now, build the fiber arrays inside each fiber mat.
    // Create a daughter "mother" volume in each fiber mat to hold the fibers.
    Int_t fiber_layer_number = 1;
    auto sciFiLayerMotherUBox = new TGeoBBox(
        Form("%s_SciFiLayerMother_U", name), width / 2, height / 2, fiberMatThick / 2 / fiber_layer_number);
    auto sciFiLayerMotherUVol =
        new TGeoVolume(Form("%s_SciFiLayerMother_U", name), sciFiLayerMotherUBox, gGeoManager->GetMedium("SciFiMat"));
    AddSensitiveVolume(sciFiLayerMotherUVol);
    for (int j = 0; j < fiber_layer_number; j++) {
        Double_t zCenter = -fiberMatThick / 2 + (j + 0.5) * fiberMatThick / fiber_layer_number;
        fiberMatVolU->AddNode(
            sciFiLayerMotherUVol, 10000000 + LayerId * 100000 + j, new TGeoTranslation(0, 0, zCenter));
    }

    auto sciFiLayerMotherVBox = new TGeoBBox(
        Form("%s_SciFiLayerMother_V", name), width / 2, height / 2, fiberMatThick / 2 / fiber_layer_number);
    auto sciFiLayerMotherVVol =
        new TGeoVolume(Form("%s_SciFiLayerMother_V", name), sciFiLayerMotherVBox, gGeoManager->GetMedium("SciFiMat"));
    AddSensitiveVolume(sciFiLayerMotherVVol);
    for (int j = 0; j < fiber_layer_number; j++) {
        Double_t zCenter = -fiberMatThick / 2 + (j + 0.5) * fiberMatThick / fiber_layer_number;
        fiberMatVolV->AddNode(
            sciFiLayerMotherVVol, 20000000 + LayerId * 100000 + j, new TGeoTranslation(0, 0, zCenter));
    }
    return modMotherVol;
}

void MTCDetector::ConstructGeometry()
{
    // Initialize media (using FairROOT’s interface)
    InitMedium("SciFiMat");
    TGeoMedium* SciFiMat = gGeoManager->GetMedium("SciFiMat");
    TGeoMedium* air = gGeoManager->GetMedium("air");
    TGeoMedium* ironMed = gGeoManager->GetMedium("iron");
    // For the scintillator, you may use the same medium as SciFiMat or another if defined.
    TGeoMedium* scintMed = gGeoManager->GetMedium("SciFiMat");
    gGeoManager->SetVisLevel(4);
    gGeoManager->SetTopVisible();

    // Define the module spacing based on three sublayers:
    //   fIronThick (outer iron), fSciFiThick (SciFi module/fiber module), fScintThick (scintillator)
    Double_t moduleSpacing = fIronThick + fSciFiThick + fScintThick;
    Double_t totalLength = fLayers * moduleSpacing;

    // --- Create an envelope volume for the detector (green, semi-transparent) ---
    auto envBox = new TGeoBBox("MTC_env", fWidth / 2, fHeight / 2, totalLength / 2);
    auto envVol = new TGeoVolume("MTC", envBox, air);
    envVol->SetLineColor(kGreen);
    envVol->SetTransparency(50);

    // --- Outer Iron Layer (gray) ---
    auto ironBox = new TGeoBBox("MTC_iron", fWidth / 2, fHeight / 2, fIronThick / 2);
    auto ironVol = new TGeoVolume("MTC_iron", ironBox, ironMed);
    ironVol->SetLineColor(kGray + 1);
    ironVol->SetTransparency(20);
    // Enable the field in the iron volume
    if (fFieldY != 0) ironVol->SetField(new TGeoUniformMagField(0, fFieldY, 0));

    // --- Assemble the layers into the envelope ---
    for (Int_t i = 0; i < fLayers; i++) {
        // Compute the center position (z) for the current module
        Double_t zPos = -totalLength / 2 + i * moduleSpacing;

        // Place the Outer Iron layer (shifted down by half the SciFi+scint thickness)
        envVol->AddNode(ironVol, i, new TGeoTranslation(0, 0, zPos + fIronThick / 2));
        // Create a SciFi module with the current detector id 'i'
        TGeoVolume* sciFiModuleVol = CreateSciFiModule("MTC_sciFi", fWidth, fHeight, fSciFiThick, i);
        envVol->AddNode(sciFiModuleVol, i, new TGeoTranslation(0, 0, zPos + fIronThick + fSciFiThick / 2));
        TGeoVolume* scintVol =
            CreateSegmentedLayer("MTC_scint", fWidth, fHeight, fScintThick, 1.0, 1.0, scintMed, kAzure + 7, 30, i);
        // Place the Scintillator layer (shifted up by half the iron thickness)
        envVol->AddNode(scintVol, i, new TGeoTranslation(0, 0, zPos + fIronThick + fSciFiThick + fScintThick / 2));
    }

    // Finally, add the envelope to the top volume with the global z offset fZCenter
    gGeoManager->GetTopVolume()->AddNode(envVol, 1, new TGeoTranslation(0, 0, fZCenter));
}
// Standard FairDetector methods
void MTCDetector::Initialize()
{
    FairDetector::Initialize();
}

Bool_t MTCDetector::ProcessHits(FairVolume* vol)
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

    // Create vetoPoint when exiting active volume
    if (gMC->IsTrackExiting() || gMC->IsTrackStop() || gMC->IsTrackDisappeared()) {

        if (fELoss == 0.) {
            return kFALSE;
        }   // if you do not want hits with zero eloss

        TParticle* p = gMC->GetStack()->GetCurrentTrack();
        fTrackID = gMC->GetStack()->GetCurrentTrackNumber();
        Int_t pdgCode = p->GetPdgCode();
        Int_t detID;
        gMC->CurrentVolID(detID);
        TLorentzVector Pos;
        gMC->TrackPosition(Pos);
        TLorentzVector Mom;
        gMC->TrackMomentum(Mom);
        Double_t x, y, z;
        if (detID / 10000000 == 3) {
            x = (fPos.X() + Pos.X()) / 2.;
            y = (fPos.Y() + Pos.Y()) / 2.;
            z = (fPos.Z() + Pos.Z()) / 2.;
            }
            else {
            x = fPos.X();
            y = fPos.Y();
            z = (fPos.Z() + Pos.Z()) / 2.;
            }

        AddHit(fTrackID,
                detID,
                TVector3(x, y, z),
                TVector3(fMom.Px(), fMom.Py(), fMom.Pz()),   // entrance momentum
                fTime,
                fLength,
                fELoss,
                pdgCode);
        ShipStack* stack = dynamic_cast<ShipStack*>(gMC->GetStack());
        stack->AddPoint(kMTC);
    }
    return kTRUE;
}

void MTCDetector::Register()
{
    TString name = "MtcDetPoint";
    TString title = "MTC";
    FairRootManager::Instance()->Register(name, title, fMTCDetectorPointCollection, kTRUE);
    LOG(DEBUG) << this->GetName() << ", Register() says: registered " << name << " collection";
}

TClonesArray* MTCDetector::GetCollection(Int_t iColl) const
{
    if (iColl == 0) {
        return fMTCDetectorPointCollection;
    } else {
        return NULL;
    }
}

void MTCDetector::Reset()
{
    fMTCDetectorPointCollection->Clear();
}

void MTCDetector::EndOfEvent()
{
    fMTCDetectorPointCollection->Clear();
}

MtcDetPoint* MTCDetector::AddHit(Int_t trackID,
                                 Int_t detID,
                                 TVector3 pos,
                                 TVector3 mom,
                                 Double_t time,
                                 Double_t length,
                                 Double_t eLoss,
                                 Int_t pdgCode)
{
    TClonesArray& clref = *fMTCDetectorPointCollection;
    Int_t size = clref.GetEntriesFast();
    return new (clref[size]) MtcDetPoint(trackID, detID, pos, mom, time, length, eLoss, pdgCode);
}
