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

using namespace ShipUnit;

namespace
{
Double_t ycross(Double_t a, Double_t R, Double_t x)
{
    /*
     * ycross:
     *   Compute the positive y-coordinate where the vertical line x intersects
     *   the circle of radius R centered at (a, 0). If the line does not intersect
     *   (i.e., (x-a)^2 > R^2), returns -1 as a flag.
     */
    Double_t y = -1;
    Double_t A = R * R - (x - a) * (x - a);
    if (!(A < 0)) {
        y = TMath::Sqrt(A);
    }
    return y;
}

Double_t integralSqrt(Double_t ynorm)
{
    /*
     * integralSqrt:
     *   Compute the analytic integral ∫₀^{ynorm} sqrt(1 - t^2) dt
     *   = ½ [ ynorm * sqrt(1 - ynorm^2) + arcsin(ynorm) ].
     *   This is used for normalizing the circular segment area.
     */
    Double_t y = 1. / 2. * (ynorm * TMath::Sqrt(1 - ynorm * ynorm) + TMath::ASin(ynorm));
    return y;
}

Double_t fraction(Double_t R, Double_t x, Double_t y)
{
    /*
     * fraction:
     *   Compute the fraction of the circle's total area that lies on one side
     *   of a vertical cut at horizontal distance x from the circle center,
     *   up to the intersection height y = sqrt(R^2 - x^2).
     *   Formula:
     *     F = 2 R^2 ∫₀^{y/R} sqrt(1 - t^2) dt  -  2 x y
     *     result = F / (π R^2)
     */
    Double_t F = 2 * R * R * (integralSqrt(y / R));
    F -= (2 * x * y);
    Double_t result = F / (R * R * TMath::Pi());
    return result;
}

Double_t area(Double_t a, Double_t R, Double_t xL, Double_t xR)
{
    /*
     * area:
     *   Compute the fraction of the full circle (radius R, center at (a,0))
     *   that lies between the vertical boundaries x = xL and x = xR.
     *   Special cases:
     *     - If [xL, xR] fully covers the circle, returns 1.
     *     - If neither boundary intersects the circle, returns -1 (no overlap).
     *   Otherwise, uses ycross() to find intersection heights, fraction()
     *   to get segment areas, and combines them to yield the net fraction.
     */
    Double_t fracL = -1;
    Double_t fracR = -1;
    if (xL <= a - R && xR >= a + R) {
        return 1;
    }

    Double_t leftC = ycross(a, R, xL);
    Double_t rightC = ycross(a, R, xR);
    if (leftC < 0 && rightC < 0) {
        return -1;
    }

    if (!(rightC < 0)) {
        fracR = fraction(R, abs(xR - a), rightC);
    }
    if (!(leftC < 0)) {
        fracL = fraction(R, abs(xL - a), leftC);
    }

    Double_t theAnswer = 0;
    if (!(leftC < 0)) {
        if (xL < a) {
            theAnswer += 1 - fracL;
        } else {
            theAnswer += fracL;
        }
        if (!(rightC < 0)) {
            theAnswer -= 1;
        }
    }
    if (!(rightC < 0)) {
        if (xR > a) {
            theAnswer += 1 - fracR;
        } else {
            theAnswer += fracR;
        }
    }
    return theAnswer;
}
}   // namespace

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
                                   Double_t angle,
                                   Double_t iron,
                                   Double_t sciFi,
                                   Double_t scint,
                                   Int_t layers,
                                   Double_t z,
                                   Double_t field)
{
    fWidth = w;
    fHeight = h;
    fSciFiBendingAngle = angle;
    fIronThick = iron;
    fSciFiThick = sciFi;
    fScintThick = scint;
    fLayers = layers;
    fZCenter = z;
    fFieldY = field;
    fSciFiActiveX = fWidth - fWidth * tan(fSciFiBendingAngle * TMath::DegToRad());
}

// Updated SciFi module builder with fiber placements
void MTCDetector::CreateScintModule(const char* name,
                                    TGeoVolumeAssembly* modMotherVol,
                                    Double_t z_shift,
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
    modMotherVol->SetLineColor(color);
    modMotherVol->SetTransparency(transparency);
    auto scint_volume = new TGeoVolumeAssembly(Form("%s_scint", name));
    modMotherVol->AddNode(scint_volume, 0, new TGeoTranslation(0, 0, z_shift));
    auto scint_mat = new TGeoVolumeAssembly(Form("%s_scint_mat", name));
    scint_volume->AddNode(scint_mat, 0, new TGeoTranslation(0, 0, 0));
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
            scint_mat->AddNode(cellVol, 1e8 + 1e6 + 2e5 + 0e4 + i * nY + j, new TGeoTranslation(x, y, 0));
        }
    }
}

void MTCDetector::CreateSciFiModule(const char* name,
                                    TGeoVolumeAssembly* modMotherVol,
                                    Double_t width,
                                    Double_t height,
                                    Double_t thickness,
                                    Int_t LayerId)
{
    // Define sublayer thicknesses (in cm)
    // These values mimic the GEANT4 setup:
    Double_t lowerIronThick = 0.3;   // 3 mm
    fiberMatThick = 0.135;           // 1.35 mm (each fiber mat)
    Double_t airGap = 0.1;           // 1 mm
    Double_t upperIronThick = 0.3;   // 3 mm
    Double_t zLowerIronInt = -3.5 / 10;
    Double_t zFiberMat1 = -1.325 / 10;
    Double_t zAirGap = -0.15 / 10;
    Double_t zFiberMat2 = 1.025 / 10;
    Double_t zUpperIronInt = 3.2 / 10;
    // Total module thickness = 0.3 + 0.135 + 0.1 + 0.135 + 0.3 ≈ 1.0 cm

    // --- Lower Internal Iron ---
    TGeoBBox* lowerIronBox = new TGeoBBox(Form("%s_lowerIron", name), width / 2, height / 2, lowerIronThick / 2);
    TGeoVolume* lowerIronVol = new TGeoVolume(Form("%s_lowerIron", name), lowerIronBox, gGeoManager->GetMedium("iron"));
    lowerIronVol->SetLineColor(kGray + 1);
    lowerIronVol->SetTransparency(20);
    modMotherVol->AddNode(lowerIronVol, 0, new TGeoTranslation(0, 0, zLowerIronInt));

    // --- Lower Epoxy matrix (replaces SciFiMat layer) ---
    TGeoVolumeAssembly* ScifiVolU = new TGeoVolumeAssembly(Form("%s_scifi_U", name));
    modMotherVol->AddNode(ScifiVolU, 0, new TGeoTranslation(0, 0, 0));
    TGeoBBox* epoxyMatBoxU = new TGeoBBox(Form("%s_epoxyMat", name), width / 2, height / 2, fiberMatThick / 2);
    TGeoVolume* ScifiMatVolU = new TGeoVolume(Form("%s_epoxyMat", name), epoxyMatBoxU, gGeoManager->GetMedium("Epoxy"));
    ScifiMatVolU->SetLineColor(kYellow - 2);
    ScifiMatVolU->SetTransparency(30);
    ScifiMatVolU->SetVisibility(kFALSE);
    ScifiMatVolU->SetVisDaughters(kFALSE);
    ScifiVolU->AddNode(ScifiMatVolU, 0, new TGeoTranslation(0, 0, zFiberMat1));

    // --- Upper Epoxy matrix (replaces SciFiMat layer) ---
    TGeoVolumeAssembly* ScifiVolV = new TGeoVolumeAssembly(Form("%s_scifi_V", name));
    modMotherVol->AddNode(ScifiVolV, 0, new TGeoTranslation(0, 0, 0));
    TGeoBBox* epoxyMatBoxV = new TGeoBBox(Form("%s_epoxyMat", name), width / 2, height / 2, fiberMatThick / 2);
    TGeoVolume* ScifiMatVolV = new TGeoVolume(Form("%s_epoxyMat", name), epoxyMatBoxV, gGeoManager->GetMedium("Epoxy"));
    ScifiMatVolV->SetLineColor(kYellow - 2);
    ScifiMatVolV->SetTransparency(30);
    ScifiMatVolV->SetVisibility(kFALSE);
    ScifiMatVolV->SetVisDaughters(kFALSE);
    ScifiVolV->AddNode(ScifiMatVolV, 0, new TGeoTranslation(0, 0, zFiberMat2));

    // --- Upper Internal Iron ---
    TGeoBBox* upperIronBox = new TGeoBBox(Form("%s_upperIron", name), width / 2, height / 2, upperIronThick / 2);
    TGeoVolume* upperIronVol = new TGeoVolume(Form("%s_upperIron", name), upperIronBox, gGeoManager->GetMedium("iron"));
    upperIronVol->SetLineColor(kGray + 1);
    upperIronVol->SetTransparency(20);
    modMotherVol->AddNode(upperIronVol, 0, new TGeoTranslation(0, 0, zUpperIronInt));

    // -----------------------------
    // Now build the fibers inside each Epoxy block:

    // Common fiber parameters (cm)
    fSciFiActiveY = height;
    Int_t numFiberLayers = 6;
    Double_t layerThick = fiberMatThick / numFiberLayers;
    Double_t fFiberRadius = 0.01125;
    fFiberLength = fSciFiActiveY / cos(fSciFiBendingAngle * TMath::DegToRad())
                   - 2 * fFiberRadius * sin(fSciFiBendingAngle * TMath::DegToRad());
    fFiberPitch = 0.025;
    Int_t fNumFibers = static_cast<Int_t>(fSciFiActiveX / fFiberPitch);

    // --- Define the SciFi fiber volume ---
    TGeoTube* fiberTube = new TGeoTube("FiberTube", 0, fFiberRadius, fFiberLength / 2);
    TGeoVolume* fiberVol = new TGeoVolume("FiberVol", fiberTube, gGeoManager->GetMedium("SciFiMat"));
    AddSensitiveVolume(fiberVol);
    fiberVol->SetLineColor(kMagenta);
    fiberVol->SetTransparency(15);
    fiberVol->SetVisibility(kFALSE);

    // --- Rotations for U/V fibers ---
    TGeoRotation* rotU = new TGeoRotation();
    rotU->RotateY(fSciFiBendingAngle);
    rotU->RotateX(90.);
    TGeoRotation* rotV = new TGeoRotation();
    rotV->RotateY(-fSciFiBendingAngle);
    rotV->RotateX(90.);

    // --- Place U-fibers inside lower Epoxy ---
    for (int layer = 0; layer < numFiberLayers; ++layer) {
        Double_t z0 = -fiberMatThick / 2 + (layer + 0.5) * (layerThick);
        for (int j = 0; j < fNumFibers; ++j) {
            Double_t x0 = -fSciFiActiveX / 2 + (j + 0.5) * fFiberPitch;
            if (layer % 2 == 1) {
                if (j == fNumFibers - 1) {
                    continue;   // Skip the last layer for odd layers
                }
                x0 += fFiberPitch / 2;
            }
            TGeoCombiTrans* ct = new TGeoCombiTrans("", x0, 0, z0, rotU);
            Int_t copyNo = 100000000 + 1000000 + 0 * 100000 + layer * 10000 + j;
            ScifiMatVolU->AddNode(fiberVol, copyNo, ct);
        }
    }

    // --- Place V-fibers inside upper Epoxy ---
    for (int layer = 0; layer < numFiberLayers; ++layer) {
        Double_t z0 = -fiberMatThick / 2 + (layer + 0.5) * (layerThick);
        for (int j = 0; j < fNumFibers; ++j) {
            Double_t x0 = -fSciFiActiveX / 2 + (j + 0.5) * fFiberPitch;
            if (layer % 2 == 1) {
                if (j == fNumFibers - 1) {
                    continue;   // Skip the last layer for odd layers
                }
                x0 += fFiberPitch / 2;
            }
            TGeoCombiTrans* ct = new TGeoCombiTrans("", x0, 0, z0, rotV);
            Int_t copyNo = 100000000 + 1000000 + 1 * 100000 + layer * 10000 + j;
            ScifiMatVolV->AddNode(fiberVol, copyNo, ct);
        }
    }
}

void MTCDetector::ConstructGeometry()
{
    // Initialize media (using FairROOT’s interface)
    InitMedium("SciFiMat");
    TGeoMedium* SciFiMat = gGeoManager->GetMedium("SciFiMat");
    InitMedium("Epoxy");
    TGeoMedium* Epoxy = gGeoManager->GetMedium("Epoxy");
    InitMedium("air");
    TGeoMedium* air = gGeoManager->GetMedium("air");
    TGeoMedium* ironMed = gGeoManager->GetMedium("iron");
    // For the scintillator, you may use the same medium as SciFiMat or another if defined.
    TGeoMedium* scintMed = gGeoManager->GetMedium("SciFiMat");
    InitMedium("silicon");

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
    if (fFieldY != 0)
        ironVol->SetField(new TGeoUniformMagField(0, fFieldY, 0));

    // --- Assemble the layers into the envelope ---
    TGeoVolumeAssembly* sensitiveModule = new TGeoVolumeAssembly("MTC_layer");
    // Define a layer for the SciFi module
    CreateSciFiModule("MTC", sensitiveModule, fWidth, fHeight, fSciFiThick, 1);
    CreateScintModule("MTC",
                      sensitiveModule,
                      fSciFiThick / 2 + fScintThick / 2,
                      fWidth,
                      fHeight,
                      fScintThick,
                      1.0,
                      1.0,
                      scintMed,
                      kAzure + 7,
                      30,
                      1);

    for (Int_t i = 0; i < fLayers; i++) {
        // Compute the center position (z) for the current module
        Double_t zPos = -totalLength / 2 + i * moduleSpacing;

        // Place the Outer Iron layer (shifted down by half the SciFi+scint thickness)
        envVol->AddNode(ironVol, i, new TGeoTranslation(0, 0, zPos + fIronThick / 2));
        // Place the sensitive module (SciFi + Scintillator) at the correct z position
        envVol->AddNode(sensitiveModule, i, new TGeoTranslation(0, 0, zPos + fIronThick + fSciFiThick / 2));
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
        TGeoNavigator* nav = gGeoManager->GetCurrentNavigator();
        Int_t vol_local_id = nav->GetCurrentNode()->GetNumber() % 1000000;   // Local ID within the mat or scint.
        Int_t layer_id = nav->GetMother(3)->GetNumber();                     // Get layer ID.
        fVolumeID = 100000000 + layer_id * 1000000 + vol_local_id;           // 1e8 + layer_id * 1e6 + fibre_local_id;
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
        TLorentzVector Pos;
        gMC->TrackPosition(Pos);
        TLorentzVector Mom;
        gMC->TrackMomentum(Mom);
        Double_t x, y, z;
        if (fVolumeID / 100000 == 3) {
            x = (fPos.X() + Pos.X()) / 2.;
            y = (fPos.Y() + Pos.Y()) / 2.;
            z = (fPos.Z() + Pos.Z()) / 2.;
        } else {
            x = fPos.X();
            y = fPos.Y();
            z = (fPos.Z() + Pos.Z()) / 2.;
        }

        auto hit = AddHit(fTrackID,
                          fVolumeID,
                          TVector3(x, y, z),
                          TVector3(fMom.Px(), fMom.Py(), fMom.Pz()),   // entrance momentum
                          fTime,
                          fLength,
                          fELoss,
                          pdgCode);
        // hit->Print();
        ShipStack* stack = dynamic_cast<ShipStack*>(gMC->GetStack());
        stack->AddPoint(kMTC);
    }
    return kTRUE;
}

void MTCDetector::SiPMOverlap()
{
    if (gGeoManager->FindVolumeFast("SiPMmapVolU") || gGeoManager->FindVolumeFast("SiPMmapVolV")) {
        return;
    }
    Double_t fLengthScifiMat = fSciFiActiveY;
    Double_t fWidthChannel = 0.025 * 2;
    Int_t fNSiPMChan = 128;
    Int_t fNSiPMs = 7;
    Int_t fNMats = 1;
    Double_t fEdge = 0.413 - 0.025 / 2;
    Double_t initial_shift = fFiberLength * sin(fSciFiBendingAngle * TMath::DegToRad()) / 2;
    Double_t fCharr = 64 * fWidthChannel;
    Double_t firstChannelX = -fSciFiActiveX / 2;

    // Contains all plane SiPMs, defined for horizontal fiber plane
    // To obtain SiPM map for vertical fiber plane rotate by 90 degrees around Z
    TGeoVolumeAssembly* SiPMmapVolU = new TGeoVolumeAssembly("SiPMmapVolU");
    TGeoVolumeAssembly* SiPMmapVolV = new TGeoVolumeAssembly("SiPMmapVolV");

    TGeoBBox* ChannelVol_box = new TGeoBBox("ChannelVol", fWidthChannel / 2, fLengthScifiMat / 2, fiberMatThick / 2);
    TGeoVolume* ChannelVol = new TGeoVolume("ChannelVol", ChannelVol_box, gGeoManager->GetMedium("silicon"));
    /*
      Example of fiberID: 123051820, where:
        - 1: MTC unique ID
        - 23: layer number
        - 0: station type (0 for +5 degrees, 1 for -5 degrees, 2 for scint plane)
        - 5: z-layer number (0-5)
        - 1820: local fibre ID within the station
      Example of SiPM global channel (what is seen in the output file): 123004123, where:
        - 1: MTC unique ID
        - 23: layer number
        - 0: station type (0 for +5 degrees, 1 for -5 degrees)
        - 0: mat number (only 0 by June 2025)
        - 4: SiPM number (0-N, where N is the number of SiPMs in the station)
        - 123: number of the SiPM channel (0-127, 128 channels per SiPM)
    */

    int N = fNMats == 1 ? 1 : 0;
    Double_t pos = fEdge + firstChannelX + initial_shift;
    for (int imat = 0; imat < fNMats; imat++) {
        for (int isipms = 0; isipms < fNSiPMs; isipms++) {
            // pos+= fEdge;
            for (int ichannel = 0; ichannel < fNSiPMChan; ichannel++) {
                // +5 degrees
                SiPMmapVolU->AddNode(
                    ChannelVol, 100000 * 0 + imat * 10000 + isipms * 1000 + ichannel, new TGeoTranslation(pos, 0, 0));
                // -5 degrees
                SiPMmapVolV->AddNode(
                    ChannelVol, 100000 * 1 + imat * 10000 + isipms * 1000 + ichannel, new TGeoTranslation(-pos, 0, 0));
                pos += fWidthChannel;
            }
        }
    }
}

void MTCDetector::GetPosition(Int_t fDetectorID, TVector3& A, TVector3& B)
{
    /*
      Example of fiberID: 123051820, where:
        - 1: MTC unique ID
        - 23: layer number
        - 0: station type (0 for +5 degrees, 1 for -5 degrees, 2 for scint plane)
        - 5: z-layer number (0-5)
        - 1820: local fibre ID within the station
      Example of SiPM global channel (what is seen in the output file): 123004123, where:
        - 1: MTC unique ID
        - 23: layer number
        - 0: station type (0 for +5 degrees, 1 for -5 degrees)
        - 0: mat number (only 0 by June 2025)
        - 4: SiPM number (0-N, where N is the number of SiPMs in the station)
        - 123: number of the SiPM channel (0-127, 128 channels per SiPM)
    */

    Int_t station_number = static_cast<int>(fDetectorID / 1e6) % 100;
    Int_t plane_type = static_cast<int>(fDetectorID / 1e5) % 10;   // 0 for horizontal, 1 for vertical
    Int_t mat_number = static_cast<int>(fDetectorID / 1e4) % 10;

    TString sID, stationID;
    sID.Form("%i", fDetectorID);
    stationID.Form("%i", station_number);
    // Basic hierarchy: /cave/MTC_1/MTC_layer_1/MTC_sciFi_mother_1/MTC_sciFi_epoxyMat_U_1/FiberVol_101010187
    TString path = "/cave/MTC_1/MTC_layer_" + stationID
                   + ((plane_type == 0) ? "/MTC_scifi_U_0/MTC_epoxyMat_0/FiberVol_1010"
                                        : "/MTC_scifi_V_0/MTC_epoxyMat_0/FiberVol_1011");
    path += sID(4, 5);
    TGeoNavigator* nav = gGeoManager->GetCurrentNavigator();
    nav->cd(path);
    TGeoNode* W = nav->GetCurrentNode();
    TGeoBBox* S = dynamic_cast<TGeoBBox*>(W->GetVolume()->GetShape());

    Double_t top[3] = {0, 0, (S->GetDZ())};
    Double_t bot[3] = {0, 0, -(S->GetDZ())};
    Double_t Gtop[3], Gbot[3];
    nav->LocalToMaster(top, Gtop);
    nav->LocalToMaster(bot, Gbot);
    A.SetXYZ(Gtop[0], Gtop[1], Gtop[2]);
    B.SetXYZ(Gbot[0], Gbot[1], Gbot[2]);
}

TVector3 MTCDetector::GetLocalPos(Int_t fDetectorID, TVector3* glob)
{
    Int_t station_number = static_cast<int>(fDetectorID / 1e6) % 100;
    Int_t plane_type = static_cast<int>(fDetectorID / 1e5) % 10;   // 0 for horizontal, 1 for vertical
    Int_t mat_number = static_cast<int>(fDetectorID / 1e4) % 10;

    TString sID, stationID;
    sID.Form("%i", fDetectorID);
    stationID.Form("%i", station_number);
    // Basic hierarchy: /cave/MTC_1/MTC_layer_1/MTC_sciFi_mother_1/MTC_sciFi_epoxyMat_U_1/FiberVol_101010187
    TString path = "/cave/MTC_1/MTC_layer_" + stationID + ((plane_type == 0) ? "/MTC_scifi_U_0" : "/MTC_scifi_V_0");
    TGeoNavigator* nav = gGeoManager->GetCurrentNavigator();
    nav->cd(path);
    Double_t aglob[3];
    Double_t aloc[3];
    glob->GetXYZ(aglob);
    nav->MasterToLocal(aglob, aloc);
    return TVector3(aloc[0], aloc[1], aloc[2]);
}

void MTCDetector::GetSiPMPosition(Int_t SiPMChan, TVector3& A, TVector3& B)
{
    /* STMRFFF
        Example of fiberID: 123051820, where:
          - 1: MTC unique ID
          - 23: layer number
          - 0: station type (0 for +5 degrees, 1 for -5 degrees, 2 for scint plane)
          - 5: z-layer number (0-5)
          - 1820: local fibre ID within the station
        Example of SiPM global channel (what is seen in the output file): 123004123, where:
          - 1: MTC unique ID
          - 23: layer number
          - 0: station type (0 for +5 degrees, 1 for -5 degrees)
          - 0: mat number (only 0 by June 2025)
          - 4: SiPM number (0-N, where N is the number of SiPMs in the station)
          - 123: number of the SiPM channel (0-127, 128 channels per SiPM)
    */
    Int_t locNumber = SiPMChan % 1000000;
    Int_t station_number = static_cast<int>(SiPMChan / 1e6) % 100;
    Int_t plane_type = static_cast<int>(SiPMChan / 1e5) % 10;   // 0 for horizontal, 1 for vertical
    Float_t locPosition;
    locPosition = (plane_type == 0 ? SiPMPos_U : SiPMPos_V)[locNumber];   // local position in U/V plane
    TString stationID;
    stationID.Form("%i", station_number);

    Double_t loc[3] = {0, 0, 0};
    TString path = "/cave/MTC_1/MTC_layer_" + stationID
                   + ((plane_type == 0) ? "/MTC_scifi_U_0/MTC_epoxyMat_0" : "/MTC_scifi_V_0/MTC_epoxyMat_0");
    TGeoNavigator* nav = gGeoManager->GetCurrentNavigator();
    Double_t glob[3] = {0, 0, 0};
    loc[0] = locPosition;
    loc[1] = -fFiberLength / 2;
    loc[2] = 7.47;
    nav->cd(path);
    nav->LocalToMaster(loc, glob);
    A.SetXYZ(glob[0], glob[1], glob[2]);
    loc[0] = locPosition;
    loc[1] = fFiberLength / 2;
    loc[2] = 7.47;   // hardcoded for now, for some reason required to get the correct local position
    nav->LocalToMaster(loc, glob);
    B.SetXYZ(glob[0], glob[1], glob[2]);
}

void MTCDetector::SiPMmapping()
{
    // check if containers are already filled
    if (!fibresSiPM_U.empty() || !fibresSiPM_V.empty() || !SiPMPos_U.empty() || !SiPMPos_V.empty()) {
        LOG(WARN) << "SiPM mapping already done, skipping.";
        return;
    }
    Float_t fibresRadius = -1;
    Float_t dSiPM = -1;
    TGeoNode* vol;
    TGeoNode* fibre;
    SiPMOverlap();
    // Loop over both U and V planes
    std::vector<std::pair<const char*, const char*>> sipm_planes = {{"SiPMmapVolU", "MTC_scifi_U"},
                                                                    {"SiPMmapVolV", "MTC_scifi_V"}};
    for (const auto& [sipm_vol, scifi_vol] : sipm_planes) {
        auto sipm = gGeoManager->FindVolumeFast(sipm_vol);
        if (!sipm)
            continue;
        TObjArray* Nodes = sipm->GetNodes();
        auto plane = gGeoManager->FindVolumeFast(scifi_vol);
        if (!plane)
            continue;
        for (int imat = 0; imat < plane->GetNodes()->GetEntries(); imat++) {
            auto mat = static_cast<TGeoNode*>(plane->GetNodes()->At(imat));
            Float_t t1 = mat->GetMatrix()->GetTranslation()[0];
            auto vmat = mat->GetVolume();
            for (int ifibre = 0; ifibre < vmat->GetNodes()->GetEntriesFast(); ifibre++) {
                fibre = static_cast<TGeoNode*>(vmat->GetNodes()->At(ifibre));
                if (fibresRadius < 0) {
                    auto tmp = fibre->GetVolume()->GetShape();
                    auto S = dynamic_cast<TGeoBBox*>(tmp);
                    fibresRadius = S->GetDX();
                }
                Int_t fID =
                    fibre->GetNumber() % 1000000 + imat * 1e4;   // local fibre number, global fibre number = SO+fID
                TVector3 Atop, Bbot;
                GetPosition(fibre->GetNumber(), Atop, Bbot);
                Float_t a = Atop[0];

                //  check for overlap with any of the SiPM channels in the same mat
                for (Int_t nChan = 0; nChan < Nodes->GetEntriesFast(); nChan++) {   // 7 SiPMs total times 128 channels
                    vol = static_cast<TGeoNode*>(Nodes->At(nChan));
                    Int_t N = vol->GetNumber();
                    Float_t xcentre = vol->GetMatrix()->GetTranslation()[0];
                    if (dSiPM < 0) {
                        TGeoBBox* B = dynamic_cast<TGeoBBox*>(vol->GetVolume()->GetShape());
                        dSiPM = B->GetDX();
                    }
                    if (TMath::Abs(xcentre - a) > 4 * fibresRadius) {
                        continue;
                    }   // no need to check further
                    Float_t W = area(a, fibresRadius, xcentre - dSiPM, xcentre + dSiPM);
                    if (W < 0) {
                        continue;
                    }
                    std::array<float, 2> Wa;
                    Wa[0] = W;
                    Wa[1] = a;
                    if (sipm_vol == std::string("SiPMmapVolU")) {
                        fibresSiPM_U[N][fID] = Wa;
                    } else {
                        fibresSiPM_V[N][fID] = Wa;
                    }
                }
            }
        }
        // calculate also local SiPM positions based on fibre positions and their fraction
        // probably an overkill, maximum difference between weighted average and central position < 6 micron.
        if (sipm_vol == std::string("SiPMmapVolU")) {
            for (auto [N, it] : fibresSiPM_U) {
                Float_t m = 0;
                Float_t w = 0;
                for (auto [current_fibre, Wa] : it) {
                    m += Wa[0] * Wa[1];
                    w += Wa[0];
                }
                SiPMPos_U[N] = m / w;
            }
            // make inverse mapping, which fibre is associated to which SiPMs
            for (auto [N, it] : fibresSiPM_U) {
                for (auto [nfibre, Wa] : it) {
                    siPMFibres_U[nfibre][N] = Wa;
                }
            }
        } else if (sipm_vol == std::string("SiPMmapVolV")) {
            for (auto [N, it] : fibresSiPM_V) {
                Float_t m = 0;
                Float_t w = 0;
                for (auto [current_fibre, Wa] : it) {
                    m += Wa[0] * Wa[1];
                    w += Wa[0];
                }
                SiPMPos_V[N] = m / w;
            }
            // make inverse mapping, which fibre is associated to which SiPMs
            for (auto [N, it] : fibresSiPM_V) {
                for (auto [nfibre, Wa] : it) {
                    siPMFibres_V[nfibre][N] = Wa;
                }
            }
        }
    }
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
        return nullptr;
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
