//
//  Target.cxx
//
//
//  Created by Annarita Buonaura on 17/01/15.
//
//

#include "Target.h"

#include "FairGeoBuilder.h"
#include "FairGeoInterface.h"
#include "FairGeoLoader.h"
#include "FairGeoMedia.h"
#include "FairGeoMedium.h"
#include "FairGeoNode.h"
#include "FairGeoTransform.h"
#include "FairGeoVolume.h"
#include "FairRootManager.h"
#include "FairRun.h"   // for FairRun
#include "FairRun.h"
#include "FairRuntimeDb.h"   // for FairRuntimeDb
#include "FairRuntimeDb.h"
#include "FairVolume.h"
#include "ShipDetectorList.h"
#include "ShipStack.h"
#include "ShipUnit.h"
#include "TClonesArray.h"
#include "TGeoArb8.h"
#include "TGeoBBox.h"
#include "TGeoCompositeShape.h"
#include "TGeoManager.h"
#include "TGeoMaterial.h"
#include "TGeoMedium.h"
#include "TGeoTrd1.h"
#include "TGeoTube.h"
#include "TGeoUniformMagField.h"
#include "TList.h"       // for TListIter, TList (ptr only)
#include "TObjArray.h"   // for TObjArray
#include "TParticle.h"
#include "TParticleClassPDG.h"
#include "TParticlePDG.h"
#include "TString.h"   // for TString
#include "TVector3.h"
#include "TVirtualMC.h"
#include "TVirtualMCStack.h"
#include "TargetPoint.h"

#include <iosfwd>     // for ostream
#include <iostream>   // for operator<<, basic_ostream,etc
#include <stddef.h>   // for NULL
#include <string.h>
#include <tuple>

using std::cout;
using std::endl;

using namespace ShipUnit;

Target::Target()
    : FairDetector("Target", "", kTRUE)
    , fTrackID(-1)
    , fVolumeID(-1)
    , fPos()
    , fMom()
    , fTime(-1.)
    , fLength(-1.)
    , fELoss(-1)
    , fTargetPointCollection(new TClonesArray("TargetPoint"))
{}

Target::Target(const char* name, const Double_t Ydist, Bool_t Active, const char* Title)
    : FairDetector(name, true, ktauTarget)
    , fTrackID(-1)
    , fVolumeID(-1)
    , fPos()
    , fMom()
    , fTime(-1.)
    , fLength(-1.)
    , fELoss(-1)
    , fTargetPointCollection(new TClonesArray("TargetPoint"))
{
    Ydistance = Ydist;
}

Target::~Target()
{
    if (fTargetPointCollection) {
        fTargetPointCollection->Delete();
        delete fTargetPointCollection;
    }
}

void Target::Initialize()
{
    FairDetector::Initialize();
}

// -----   Private method InitMedium
Int_t Target::InitMedium(const char* name)
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
    if (medium != NULL)
        return ShipMedium->getMediumIndex();
    return geoBuild->createMedium(ShipMedium);
}

//--------------Options for detector construction
void Target::SetDetectorDesign(Int_t Design)
{
    fDesign = Design;
    Info("SetDetectorDesign", " to %i", fDesign);
}

void Target::MakeNuTargetPassive(Bool_t a)
{
    fPassive = a;
}

void Target::MergeTopBot(Bool_t SingleEmFilm)
{
    fsingleemulsionfilm = SingleEmFilm;
}

//--------------------------

void Target::SetNumberBricks(Double_t col, Double_t row, Double_t wall)
{
    fNCol = col;
    fNRow = row;
    fNWall = wall;
}

void Target::SetNumberTargets(Int_t target)
{
    fNTarget = target;
}

void Target::SetTargetWallDimension(Double_t WallXDim_, Double_t WallYDim_, Double_t WallZDim_)
{
    WallXDim = WallXDim_;
    WallYDim = WallYDim_;
    WallZDim = WallZDim_;
}

void Target::SetDetectorDimension(Double_t xdim, Double_t ydim, Double_t zdim)
{
    XDimension = xdim;
    YDimension = ydim;
    ZDimension = zdim;
}

void Target::SetEmulsionParam(Double_t EmTh,
                              Double_t EmX,
                              Double_t EmY,
                              Double_t PBTh,
                              Double_t EPlW,
                              Double_t LeadTh,
                              Double_t AllPW)
{
    EmulsionThickness = EmTh;
    EmulsionX = EmX;
    EmulsionY = EmY;
    PlasticBaseThickness = PBTh;
    EmPlateWidth = EPlW;
    LeadThickness = LeadTh;
    AllPlateWidth = AllPW;
}

void Target::SetBrickParam(Double_t BrX,
                           Double_t BrY,
                           Double_t BrZ,
                           Double_t BrPackX,
                           Double_t BrPackY,
                           Double_t BrPackZ,
                           Int_t number_of_plates_)
{
    BrickPackageX = BrPackX;
    BrickPackageY = BrPackY;
    BrickPackageZ = BrPackZ;
    BrickX = BrX;
    BrickY = BrY;
    BrickZ = BrZ;
    number_of_plates = number_of_plates_;
}

void Target::SetCellParam(Double_t CellW)
{
    CellWidth = CellW;
}

void Target::SetTTzdimension(Double_t TTZ)
{
    TTrackerZ = TTZ;
}

void Target::SetMagnetHeight(Double_t Y)
{
    fMagnetY = Y;
}

void Target::SetColumnHeight(Double_t Y)
{
    fColumnY = Y;
}

void Target::SetBaseHeight(Double_t Y)
{
    fMagnetBaseY = Y;
}

void Target::SetCoilUpHeight(Double_t H1)
{
    fCoilH1 = H1;
}

void Target::SetCoilDownHeight(Double_t H2)
{
    fCoilH2 = H2;
}

void Target::SetMagneticField(Double_t B)
{
    fField = B;
}

void Target::SetCenterZ(Double_t z)
{
    fCenterZ = z;
}

void Target::SetBaseDimension(Double_t x, Double_t y, Double_t z)
{
    fBaseX = x;
    fBaseY = y;
    fBaseZ = z;
}

void Target::SetPillarDimension(Double_t x, Double_t y, Double_t z)
{
    fPillarX = x;
    fPillarY = y;
    fPillarZ = z;
}

void Target::SetHpTParam(Int_t n,
                         Double_t dd,
                         Double_t DZ)   // need to know about HPT.cxx geometry to place additional targets
{
    fnHpT = n;
    fHpTDistance = dd;
    fHpTDZ = DZ;
}

void Target::ConstructGeometry()
{
    // cout << "Design = " << fDesign << endl;

    InitMedium("air");
    TGeoMedium* air = gGeoManager->GetMedium("air");

    InitMedium("PlasticBase");
    TGeoMedium* PBase = gGeoManager->GetMedium("PlasticBase");

    InitMedium("NuclearEmulsion");
    TGeoMedium* NEmu = gGeoManager->GetMedium("NuclearEmulsion");

    TGeoMaterial* NEmuMat = NEmu->GetMaterial();   // I need the materials to build the mixture
    TGeoMaterial* PBaseMat = PBase->GetMaterial();

    Double_t rho_film = (NEmuMat->GetDensity() * 2 * EmulsionThickness + PBaseMat->GetDensity() * PlasticBaseThickness)
                        / (2 * EmulsionThickness + PlasticBaseThickness);
    Double_t frac_emu =
        NEmuMat->GetDensity() * 2 * EmulsionThickness
        / (NEmuMat->GetDensity() * 2 * EmulsionThickness + PBaseMat->GetDensity() * PlasticBaseThickness);

    if (fsingleemulsionfilm)
        cout << "TARGET PRINTOUT: Single volume for emulsion film chosen: average density: " << rho_film
             << " fraction in mass of emulsion " << frac_emu << endl;

    TGeoMixture* emufilmmixture =
        new TGeoMixture("EmulsionFilmMixture", 2.00);   // two nuclear emulsions separated by the plastic base

    emufilmmixture->AddElement(NEmuMat, frac_emu);
    emufilmmixture->AddElement(PBaseMat, 1. - frac_emu);

    TGeoMedium* Emufilm = new TGeoMedium("EmulsionFilm", 100, emufilmmixture);

    InitMedium("lead");
    TGeoMedium* lead = gGeoManager->GetMedium("lead");

    InitMedium("tungsten");
    TGeoMedium* tungsten = gGeoManager->GetMedium("tungsten");

    InitMedium("Concrete");
    TGeoMedium* Conc = gGeoManager->GetMedium("Concrete");

    InitMedium("steel");
    TGeoMedium* Steel = gGeoManager->GetMedium("steel");

    Int_t NPlates = number_of_plates;   // Number of doublets emulsion + Pb

    // Definition of the target box containing emulsion bricks + target trackers (TT)
    TGeoBBox* TargetBox = new TGeoBBox("TargetBox", XDimension / 2, YDimension / 2, ZDimension / 2);
    TGeoVolume* volTarget = new TGeoVolume("volTarget", TargetBox, air);

    //
    // Volumes definition
    //

    TGeoBBox* Cell = new TGeoBBox("cell", BrickX / 2, BrickY / 2, CellWidth / 2);
    TGeoVolume* volCell = new TGeoVolume("Cell", Cell, air);

    // Brick
    TGeoBBox* Brick = new TGeoBBox("brick", BrickX / 2, BrickY / 2, BrickZ / 2);
    TGeoVolume* volBrick = new TGeoVolume("Brick", Brick, air);
    volBrick->SetLineColor(kCyan);
    volBrick->SetTransparency(1);
    // need to separate the two cases, now with a ternary operator
    auto* Absorber = new TGeoBBox("Absorber", EmulsionX / 2, EmulsionY / 2, LeadThickness / 2);
    auto* volAbsorber = new TGeoVolume("volAbsorber", Absorber, tungsten);

    volAbsorber->SetTransparency(1);
    volAbsorber->SetLineColor(kGray);
    for (Int_t n = 0; n < NPlates; n++) {
        volBrick->AddNode(
            volAbsorber,
            n,
            new TGeoTranslation(
                0, 0, -BrickZ / 2 + BrickPackageZ / 2 + EmPlateWidth + LeadThickness / 2 + n * AllPlateWidth));
    }
    if (fsingleemulsionfilm) {   // simplified configuration, unique sensitive layer for the whole emulsion plate
        TGeoBBox* EmulsionFilm = new TGeoBBox("EmulsionFilm", EmulsionX / 2, EmulsionY / 2, EmPlateWidth / 2);
        TGeoVolume* volEmulsionFilm = new TGeoVolume("Emulsion", EmulsionFilm, Emufilm);   // TOP
        volEmulsionFilm->SetLineColor(kBlue);

        if (fPassive == 0) {
            AddSensitiveVolume(volEmulsionFilm);
        }

        for (Int_t n = 0; n < NPlates + 1; n++) {
            volBrick->AddNode(
                volEmulsionFilm,
                n,
                new TGeoTranslation(0, 0, -BrickZ / 2 + BrickPackageZ / 2 + EmPlateWidth / 2 + n * AllPlateWidth));
        }
    } else {   // more accurate configuration, two emulsion films divided by a plastic base
        TGeoBBox* EmulsionFilm = new TGeoBBox("EmulsionFilm", EmulsionX / 2, EmulsionY / 2, EmulsionThickness / 2);
        TGeoVolume* volEmulsionFilm = new TGeoVolume("Emulsion", EmulsionFilm, NEmu);     // TOP
        TGeoVolume* volEmulsionFilm2 = new TGeoVolume("Emulsion2", EmulsionFilm, NEmu);   // BOTTOM
        volEmulsionFilm->SetLineColor(kBlue);
        volEmulsionFilm2->SetLineColor(kBlue);

        if (fPassive == 0) {
            AddSensitiveVolume(volEmulsionFilm);
            AddSensitiveVolume(volEmulsionFilm2);
        }
        TGeoBBox* PlBase = new TGeoBBox("PlBase", EmulsionX / 2, EmulsionY / 2, PlasticBaseThickness / 2);
        TGeoVolume* volPlBase = new TGeoVolume("PlasticBase", PlBase, PBase);
        volPlBase->SetLineColor(kYellow - 4);
        for (Int_t n = 0; n < NPlates + 1; n++) {
            volBrick->AddNode(
                volEmulsionFilm2,
                n,
                new TGeoTranslation(
                    0, 0, -BrickZ / 2 + BrickPackageZ / 2 + EmulsionThickness / 2 + n * AllPlateWidth));   // BOTTOM
            volBrick->AddNode(volEmulsionFilm,
                              n,
                              new TGeoTranslation(0,
                                                  0,
                                                  -BrickZ / 2 + BrickPackageZ / 2 + 3 * EmulsionThickness / 2
                                                      + PlasticBaseThickness + n * AllPlateWidth));   // TOP
            volBrick->AddNode(volPlBase,
                              n,
                              new TGeoTranslation(0,
                                                  0,
                                                  -BrickZ / 2 + BrickPackageZ / 2 + EmulsionThickness
                                                      + PlasticBaseThickness / 2
                                                      + n * AllPlateWidth));   // PLASTIC BASE
        }
    }

    volBrick->SetVisibility(kTRUE);
    TGeoVolume* top = gGeoManager->GetTopVolume();
    TGeoVolumeAssembly* tTauNuDet = new TGeoVolumeAssembly("tTauNuDet");
    top->AddNode(tTauNuDet, 1, new TGeoTranslation(0, 0, 0));

    tTauNuDet->AddNode(volTarget, 1, new TGeoTranslation(0, 0, fCenterZ));
    TGeoBBox* Row = new TGeoBBox("row", WallXDim / 2, BrickY / 2, WallZDim / 2);
    TGeoVolume* volRow = new TGeoVolume("Row", Row, air);
    volRow->SetLineColor(20);

    Double_t d_cl_x = -WallXDim / 2;
    for (int j = 0; j < fNCol; j++) {
        volRow->AddNode(volBrick, j, new TGeoTranslation(d_cl_x + BrickX / 2, 0, 0));
        d_cl_x += BrickX;
    }
    TGeoBBox* Wall = new TGeoBBox("wall", WallXDim / 2, WallYDim / 2, WallZDim / 2);
    TGeoVolume* volWall = new TGeoVolume("Wall", Wall, air);
    volWall->SetLineColor(kGreen);

    Double_t d_cl_y = -WallYDim / 2;
    for (int k = 0; k < fNRow; k++) {
        volWall->AddNode(volRow, k, new TGeoTranslation(0, d_cl_y + BrickY / 2, 0));

        // 2mm is the distance for the structure that holds the brick
        d_cl_y += BrickY + Ydistance;
    }
    // Columns

    Double_t d_cl_z = -ZDimension / 2 + TTrackerZ;
    for (int l = 0; l < fNWall; l++) {
        volTarget->AddNode(volWall, l, new TGeoTranslation(0, 0, d_cl_z + BrickZ / 2));

        // 6 cm is the distance between 2 columns of consecutive Target for TT placement
        d_cl_z += BrickZ + TTrackerZ;
    }
}   // end construct geometry

Bool_t Target::ProcessHits(FairVolume* vol)
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

    // Create muonPoint at exit of active volume
    if (gMC->IsTrackExiting() || gMC->IsTrackStop() || gMC->IsTrackDisappeared()) {
        fTrackID = gMC->GetStack()->GetCurrentTrackNumber();
        // Int_t fTrackID  = gMC->GetStack()->GetCurrentTrackNumber();
        gMC->CurrentVolID(fVolumeID);
        Int_t detID = fVolumeID;
        // gGeoManager->PrintOverlaps();

        // cout<< "detID = " << detID << endl;
        Int_t MaxLevel = gGeoManager->GetLevel();
        const Int_t MaxL = MaxLevel;
        // cout << "MaxLevel = " << MaxL << endl;
        // cout << gMC->CurrentVolPath()<< endl;

        Int_t motherV[MaxL];
        Bool_t EmTop = false;
        Int_t NPlate = 0;
        const char* name;

        name = gMC->CurrentVolName();
        // cout << name << endl;

        if (strcmp(name, "Emulsion") == 0) {
            NPlate = detID;
            EmTop = 1;
        }
        if (strcmp(name, "Emulsion2") == 0) {
            NPlate = detID;
            EmTop = 0;
        }

        Int_t NWall = 0, NColumn = 0, NRow = 0;

        for (Int_t i = 0; i < MaxL; i++) {
            motherV[i] = gGeoManager->GetMother(i)->GetNumber();
            const char* mumname = gMC->CurrentVolOffName(i);
            if (motherV[0] == 1 && motherV[0] != detID) {
                if (strcmp(mumname, "Brick") == 0)
                    NColumn = motherV[i];
                if (strcmp(mumname, "Cell") == 0)
                    NRow = motherV[i];
                if (strcmp(mumname, "Row") == 0)
                    NWall = motherV[i];
                if ((strcmp(mumname, "Wall") == 0) && (motherV[i] == 2))
                    NWall += fNWall;
            } else {

                if (strcmp(mumname, "Cell") == 0)
                    NColumn = motherV[i];
                if (strcmp(mumname, "Row") == 0)
                    NRow = motherV[i];
                if (strcmp(mumname, "Wall") == 0)
                    NWall = motherV[i];
                if ((strcmp(mumname, "volTarget") == 0) && (motherV[i] == 2))
                    NWall += fNWall;
            }
            // cout << i << "   " << motherV[i] << "    name = " << mumname << endl;
        }

        detID = (NWall + 1) * 1E7 + (NRow + 1) * 1E6 + (NColumn + 1) * 1E4 + (NPlate + 1) * 1E1 + EmTop;

        fVolumeID = detID;

        if (fELoss == 0.) {
            return kFALSE;
        }
        TParticle* p = gMC->GetStack()->GetCurrentTrack();
        // Int_t MotherID =gMC->GetStack()->GetCurrentParentTrackNumber();
        Int_t pdgCode = p->GetPdgCode();

        TLorentzVector Pos;
        gMC->TrackPosition(Pos);
        Double_t xmean = (fPos.X() + Pos.X()) / 2.;
        Double_t ymean = (fPos.Y() + Pos.Y()) / 2.;
        Double_t zmean = (fPos.Z() + Pos.Z()) / 2.;

        AddHit(fTrackID,
               fVolumeID,
               TVector3(xmean, ymean, zmean),
               TVector3(fMom.Px(), fMom.Py(), fMom.Pz()),
               fTime,
               fLength,
               fELoss,
               pdgCode);

        // Increment number of muon det points in TParticle
        ShipStack* stack = dynamic_cast<ShipStack*>(gMC->GetStack());
        stack->AddPoint(ktauTarget);
    }

    return kTRUE;
}

std::tuple<Int_t, Int_t, Int_t, Int_t, Bool_t> Target::DecodeBrickID(Int_t detID)
{
    //! Decode detectorID into a struct with info about the film position in the target:
    /*
     \param detID detectorID for the TargetPoint
     \return a struct providing the wall, row, column and plate number (starting from 1),
        as well as a boolean for top/bottom emulsion layer.
        Examples:
         11010031 -> Wall 1, Row 1, Column 1, Plate 3, true;
         31010150 -> Wall 3, Row 1, Column 1, Plate 15, false;
    */
    auto divt_E7 = std::div(detID, 1E7);

    Int_t NWall = divt_E7.quot;
    auto divt_E6 = std::div(divt_E7.rem, 1E6);

    Int_t NRow = divt_E6.quot;
    auto divt_E4 = std::div(divt_E6.rem, 1E4);

    Int_t NColumn = divt_E4.quot;
    auto divt_E1 = std::div(divt_E4.rem, 1E1);

    Int_t NPlate = divt_E1.quot;
    Bool_t EmTop = static_cast<Bool_t>(divt_E1.rem);

    return std::make_tuple(NWall, NRow, NColumn, NPlate, EmTop);
}

void Target::EndOfEvent()
{
    fTargetPointCollection->Clear();
}

void Target::Register()
{

    /** This will create a branch in the output tree called
        TargetPoint, setting the last parameter to kFALSE means:
        this collection will not be written to the file, it will exist
        only during the simulation.
    */

    FairRootManager::Instance()->Register("TargetPoint", "Target", fTargetPointCollection, kTRUE);
}

TClonesArray* Target::GetCollection(Int_t iColl) const
{
    if (iColl == 0) {
        return fTargetPointCollection;
    } else {
        return NULL;
    }
}

void Target::Reset()
{
    fTargetPointCollection->Clear();
}

TargetPoint* Target::AddHit(Int_t trackID,
                            Int_t detID,
                            TVector3 pos,
                            TVector3 mom,
                            Double_t time,
                            Double_t length,
                            Double_t eLoss,
                            Int_t pdgCode)
{
    TClonesArray& clref = *fTargetPointCollection;
    Int_t size = clref.GetEntriesFast();
    // cout << "brick hit called"<< pos.z()<<endl;
    return new (clref[size]) TargetPoint(trackID, detID, pos, mom, time, length, eLoss, pdgCode);
}
