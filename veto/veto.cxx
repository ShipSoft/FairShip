
// 09/07/2024
// SBT software contact: anupama.reghunath@cern.ch
/**
 * @file veto.cxx
 * @brief Implementation of the Veto detector class.
 *
 * This file contains the definitions for the Veto class used in the
 * FairShip Software. The class is responsible for simulating the Decay Vessel(helium) + integrated SBT geometry and
 * interactions.
 */

#include "veto.h"

#include "FairGeoBuilder.h"
#include "FairGeoInterface.h"
#include "FairGeoLoader.h"
#include "FairGeoMedia.h"
#include "FairGeoNode.h"
#include "FairGeoVolume.h"
#include "FairLogger.h"   /// for FairLogger, MESSAGE_ORIGIN
#include "FairRootManager.h"
#include "FairRun.h"
#include "FairRuntimeDb.h"
#include "FairVolume.h"
#include "ShipDetectorList.h"
#include "ShipStack.h"
#include "TClonesArray.h"
#include "TGeoArb8.h"
#include "TGeoBBox.h"
#include "TGeoBoolNode.h"
#include "TGeoCompositeShape.h"
#include "TGeoCone.h"
#include "TGeoEltu.h"
#include "TGeoManager.h"
#include "TGeoMaterial.h"
#include "TGeoShapeAssembly.h"
#include "TGeoSphere.h"
#include "TGeoTube.h"
#include "TMath.h"
#include "TParticle.h"
#include "TVirtualMC.h"
#include "vetoPoint.h"

#include <iostream>
#include <math.h>
#include <vector>

Double_t cm = 1;          // cm
Double_t m = 100 * cm;    //  m
Double_t mm = 0.1 * cm;   //  mm

/**
 * @brief Constructor for the Veto class.
 *
 * Initializes the veto detector with the given parameters.
 *
 */
veto::veto()
    : FairDetector("Veto", kTRUE, kVETO)
    , fTrackID(-1)
    , fVolumeID(-1)
    , fPos()
    , fMom()
    , fTime(-1.)
    , fLength(-1.)
    , fELoss(-1)
    , fvetoPointCollection(new TClonesArray("vetoPoint"))
    , fFastMuon(kFALSE)
    , fFollowMuon(kFALSE)
{
    fUseSupport = 1;
    fLiquidVeto = 1;
}

/**
 * @brief Destructor for the Veto class.
 *
 * Cleans up any resources used by the Veto detector.
 */
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
}

TGeoVolume* veto::GeoTrapezoid(TString xname,
                               Double_t z_thick,
                               Double_t x_thick_start,
                               Double_t x_thick_end,
                               Double_t y_thick_start,
                               Double_t y_thick_end,
                               Int_t color,
                               TGeoMedium* material,
                               Bool_t sens = kFALSE)
{
    Double_t dz = z_thick / 2;
    Double_t dx1 = x_thick_start / 2 - 1.E-6;
    Double_t dx2 = x_thick_end / 2 - 1.E-6;
    Double_t dy1 = y_thick_start / 2 - 1.E-6;
    Double_t dy2 = y_thick_end / 2 - 1.E-6;
    TGeoArb8* T1 = new TGeoArb8("T1" + xname, dz + 1.E-6);
    T1->SetVertex(0, -dx1, -dy1);
    T1->SetVertex(1, -dx1, dy1);
    T1->SetVertex(2, dx1, dy1);
    T1->SetVertex(3, dx1, -dy1);
    T1->SetVertex(4, -dx2, -dy2);
    T1->SetVertex(5, -dx2, dy2);
    T1->SetVertex(6, dx2, dy2);
    T1->SetVertex(7, dx2, -dy2);

    TGeoVolume* T = new TGeoVolume(xname, T1, material);
    T->SetLineColor(color);
    if (sens) {
        AddSensitiveVolume(T);
    }   // and make the volumes sensitive..
    return T;
}

TGeoVolume* veto::GeoTrapezoidHollow(TString xname,
                                     Double_t wallthick,
                                     Double_t z_thick,
                                     Double_t x_thick_start,
                                     Double_t x_thick_end,
                                     Double_t y_thick_start,
                                     Double_t y_thick_end,
                                     Int_t color,
                                     TGeoMedium* material,
                                     Bool_t sens = kFALSE)
{

    Double_t dx_start = x_thick_start / 2;
    Double_t dy_start = y_thick_start / 2;
    Double_t dx_end = x_thick_end / 2;
    Double_t dy_end = y_thick_end / 2;
    Double_t dz = z_thick / 2;

    TString nm = xname.ReplaceAll("-", "");   // otherwise it will try to subtract "-" in TGeoComposteShape
    Double_t dx1 = dx_start + wallthick;
    Double_t dx2 = dx_end + wallthick;
    Double_t dy1 = dy_start + wallthick;
    Double_t dy2 = dy_end + wallthick;

    TGeoArb8* T2 = new TGeoArb8("T2" + nm, dz);
    T2->SetVertex(0, -dx1, -dy1);
    T2->SetVertex(1, -dx1, dy1);
    T2->SetVertex(2, dx1, dy1);
    T2->SetVertex(3, dx1, -dy1);
    T2->SetVertex(4, -dx2, -dy2);
    T2->SetVertex(5, -dx2, dy2);
    T2->SetVertex(6, dx2, dy2);
    T2->SetVertex(7, dx2, -dy2);

    Double_t tdx1 = dx_start;
    Double_t tdx2 = dx_end;
    Double_t tdy1 = dy_start;
    Double_t tdy2 = dy_end;
    TGeoArb8* T1 = new TGeoArb8("T1" + nm, dz + 1.E-6);
    T1->SetVertex(0, -tdx1, -tdy1);
    T1->SetVertex(1, -tdx1, tdy1);
    T1->SetVertex(2, tdx1, tdy1);
    T1->SetVertex(3, tdx1, -tdy1);
    T1->SetVertex(4, -tdx2, -tdy2);
    T1->SetVertex(5, -tdx2, tdy2);
    T1->SetVertex(6, tdx2, tdy2);
    T1->SetVertex(7, tdx2, -tdy2);

    TGeoCompositeShape* T321 = new TGeoCompositeShape("T3" + nm, "T2" + nm + "-T1" + nm);
    TGeoVolume* T = new TGeoVolume(xname, T321, material);
    T->SetLineColor(color);
    // and make the volumes sensitive..
    if (sens) {
        AddSensitiveVolume(T);
    }
    return T;
}

double veto::wx(double z)
{   // calculate x thickness at z

    double wx1 = VetoStartInnerX;
    double wx2 = VetoEndInnerX;
    double z1 = 0 * m;
    double z2 = 50 * m;

    return (wx1 + (z - z1) * (wx2 - wx1) / (z2 - z1));
}

double veto::wy(double z)
{   // calculate y thickness at z

    double wy1 = VetoStartInnerY;
    double wy2 = VetoEndInnerY;
    double z1 = 0 * m;
    double z2 = 50 * m;

    return (wy1 + (z - z1) * (wy2 - wy1) / (z2 - z1));
}

TGeoVolume* veto::GeoSideObj(TString xname,
                             double dz,
                             double a1,
                             double b1,
                             double a2,
                             double b2,
                             double dA,
                             double dB,
                             Int_t color,
                             TGeoMedium* material,
                             Bool_t sens = kFALSE)
{

    // a1- width in X, at the beginning
    // b1- width in Y, at the beginning
    // a2- width in X, at the end
    // b2- width in Y, at the end

    TGeoArb8* T1 = new TGeoArb8(dz);
    T1->SetVertex(0, 0, 0);
    T1->SetVertex(1, 0, b1);
    T1->SetVertex(2, a1, b1);
    T1->SetVertex(3, a1, 0);

    T1->SetVertex(4, dA, dB);
    T1->SetVertex(5, dA, dB + b2);
    T1->SetVertex(6, dA + a2, dB + b2);
    T1->SetVertex(7, dA + a2, dB);

    TGeoVolume* T = new TGeoVolume(xname, T1, material);
    T->SetLineColor(color);
    // and make the volumes sensitive..
    if (sens) {
        AddSensitiveVolume(T);
    }
    return T;
}

TGeoVolume* veto::GeoCornerLiSc1(TString xname,
                                 double dz,
                                 bool isClockwise,
                                 double a1,
                                 double a2,
                                 double b1,
                                 double b2,
                                 double dA,
                                 double dB,
                                 Int_t color,
                                 TGeoMedium* material,
                                 Bool_t sens = kFALSE)
{

    TGeoArb8* T1 = new TGeoArb8(dz);

    if (isClockwise) {

        T1->SetVertex(0, 0, 0);
        T1->SetVertex(1, 0, b1);
        T1->SetVertex(2, a1 + b1, b1);
        T1->SetVertex(3, a1, 0);

        T1->SetVertex(4, dA, dB);
        T1->SetVertex(5, dA, dB + b2);
        T1->SetVertex(6, dA + a2 + b2, dB + b2);
        T1->SetVertex(7, dA + a2, dB);
    } else {
        T1->SetVertex(0, 0, 0);
        T1->SetVertex(1, -a1, 0);
        T1->SetVertex(2, -(a1 + b1), b1);
        T1->SetVertex(3, 0, b1);

        T1->SetVertex(4, -dA, dB);
        T1->SetVertex(5, -(dA + a2), dB);
        T1->SetVertex(6, -(dA + a2 + b2), dB + b2);
        T1->SetVertex(7, -dA, dB + b2);
    }

    TGeoVolume* T = new TGeoVolume(xname, T1, material);
    T->SetLineColor(color);
    // and make the volumes sensitive..
    if (sens) {
        AddSensitiveVolume(T);
    }
    return T;
}

TGeoVolume* veto::GeoCornerLiSc2(TString xname,
                                 double dz,
                                 bool isClockwise,
                                 double a1,
                                 double a2,
                                 double b1,
                                 double b2,
                                 double dA,
                                 double dB,
                                 Int_t color,
                                 TGeoMedium* material,
                                 Bool_t sens = kFALSE)
{

    TGeoArb8* T1 = new TGeoArb8(dz);

    if (isClockwise) {
        T1->SetVertex(0, 0, 0);
        T1->SetVertex(1, 0, a1);
        T1->SetVertex(2, b1, a1 + b1);
        T1->SetVertex(3, b1, 0);

        T1->SetVertex(4, dB, dA);
        T1->SetVertex(5, dB, dA + a2);
        T1->SetVertex(6, dB + b2, dA + a2 + b2);
        T1->SetVertex(7, dB + b2, dA);
    } else {
        T1->SetVertex(0, 0, 0);
        T1->SetVertex(1, b1, 0);
        T1->SetVertex(2, b1, -(a1 + b1));
        T1->SetVertex(3, 0, -a1);

        T1->SetVertex(4, dB, -dA);
        T1->SetVertex(5, dB + b2, -dA);
        T1->SetVertex(6, dB + b2, -(dA + a2 + b2));
        T1->SetVertex(7, dB, -(dA + a2));
    }

    TGeoVolume* T = new TGeoVolume(xname, T1, material);
    T->SetLineColor(color);
    // and make the volumes sensitive.
    if (sens) {
        AddSensitiveVolume(T);
    }
    return T;
}

TGeoVolumeAssembly* veto::GeoCornerRib(TString xname,
                                       double ribThick,
                                       double lt1,
                                       double lt2,
                                       double dz,
                                       double slopeX,
                                       double slopeY,
                                       Int_t color,
                                       TGeoMedium* material,
                                       Bool_t sens = kFALSE)
{

    Double_t wz = dz * 2;
    double d = ribThick * sqrt(2) / 2;
    double dx = slopeX * wz;
    double dy = slopeY * wz;

    TGeoArb8* T1 = new TGeoArb8(dz);
    T1->SetVertex(0, lt1, lt1 - d);
    T1->SetVertex(1, 0, -d);
    T1->SetVertex(2, 0, 0);
    T1->SetVertex(3, lt1, lt1);

    T1->SetVertex(4, dx + lt2, dy + lt2 - d);
    T1->SetVertex(5, dx, dy - d);
    T1->SetVertex(6, dx, dy);
    T1->SetVertex(7, dx + lt2, dy + lt2);

    TGeoArb8* T2 = new TGeoArb8(dz);
    T2->SetVertex(0, lt1 - d, lt1);
    T2->SetVertex(1, lt1, lt1);
    T2->SetVertex(2, 0, 0);
    T2->SetVertex(3, -d, 0);

    T2->SetVertex(4, dx + lt2 - d, dy + lt2);
    T2->SetVertex(5, dx + lt2, dy + lt2);
    T2->SetVertex(6, dx, dy);
    T2->SetVertex(7, dx - d, dy);

    TGeoVolume* T1v = new TGeoVolume("part", T1, material);
    TGeoVolume* T2v = new TGeoVolume("part", T2, material);
    T1v->SetLineColor(color);
    T2v->SetLineColor(color);
    if (sens) {
        AddSensitiveVolume(T1v);
    }
    if (sens) {
        AddSensitiveVolume(T2v);
    }

    TGeoVolumeAssembly* T = new TGeoVolumeAssembly(xname);
    T->AddNode(T1v, 1, new TGeoTranslation(0, 0, 0));
    T->AddNode(T2v, 2, new TGeoTranslation(0, 0, 0));
    return T;
}

int veto::makeId(double z, double x, double y)
{
    double Z = z / 10;
    double r = sqrt(x * x + y * y);
    double phi = 999;
    if (y >= 0)
        phi = acos(x / r);
    else
        phi = -acos(x / r) + 2 * TMath::Pi();

    phi = phi * 180 / TMath::Pi();
    return (int)Z * 1000000 + (int)r * 1000 + (int)phi;
}

int veto::liscId(TString ShapeTypeName, int blockNr, int Zlayer, int number, int position)
{

    int id = 999999;
    int ShapeType = -1;

    if (ShapeTypeName == "LiScX")
        ShapeType = 1;
    else if (ShapeTypeName == "LiScY")
        ShapeType = 2;
    else if (ShapeTypeName == "LiSc_S3")
        ShapeType = 3;
    else if (ShapeTypeName == "LiSc_S4")
        ShapeType = 4;
    else if (ShapeTypeName == "LiSc_S5")
        ShapeType = 5;
    else if (ShapeTypeName == "LiSc_S6")
        ShapeType = 6;

    if (ShapeType < 0)
        id = 999999;
    else
        id = ShapeType * 100000 + blockNr * 10000 + Zlayer * 100 + number * 10 + position;

    return id;
}

void veto::AddBlock(TGeoVolumeAssembly* tInnerWall,
                    TGeoVolumeAssembly* tDecayVacuum,
                    TGeoVolumeAssembly* tOuterWall,
                    TGeoVolumeAssembly* tLongitRib,
                    TGeoVolumeAssembly* tVerticalRib,
                    TGeoVolumeAssembly* ttLiSc,
                    int& liScCounter,
                    int blockNr,
                    int nx,
                    int ny,
                    double z1,
                    double z2,
                    double Zshift,
                    double cell_thickness_z,
                    double wallThick,
                    double liscThick1,
                    double liscThick2,
                    double ribThick)
{

    TString blockName = "block";
    blockName += blockNr;

    int ribColor = 15;

    double wz = (z2 - z1);
    double slX = (wx(z2) - wx(z1)) / 2 / wz;
    double slY = (wy(z2) - wy(z1)) / 2 / wz;

    double dZ = (cell_thickness_z - ribThick) / 2;   // half space between ribs

    double tX = 0;
    double tY = 0;
    double tZ = 0;
    TString name("");

    double idX = 0;
    double idY = 0;
    double idZ = 0;

    /// inner wall
    TString nameInnerWall = (TString)tInnerWall->GetName() + "_" + blockName;
    TGeoVolume* TIW =
        GeoTrapezoidHollow(nameInnerWall, wallThick, wz, wx(z1), wx(z2), wy(z1), wy(z2), ribColor, supportMedIn);
    tInnerWall->AddNode(TIW, 0, new TGeoTranslation(0, 0, Zshift));

    /// decay vacuum
    TString nameDecayVacuum = (TString)tDecayVacuum->GetName() + "_" + blockName;
    TGeoVolume* TDV = GeoTrapezoid(nameDecayVacuum, wz, wx(z1), wx(z2), wy(z1), wy(z2), 1, decayVolumeMed);
    TDV->SetVisibility(kFALSE);
    tDecayVacuum->AddNode(TDV, 0, new TGeoTranslation(0, 0, Zshift));

    /// outer wall
    TString nameOuterWall = (TString)tOuterWall->GetName() + "_" + blockName;
    TGeoVolume* TOW = GeoTrapezoidHollow(nameOuterWall,
                                         wallThick,
                                         wz,
                                         wx(z1) + 2 * (wallThick + liscThick1),
                                         wx(z2) + 2 * (wallThick + liscThick2),
                                         wy(z1) + 2 * (wallThick + liscThick1),
                                         wy(z2) + 2 * (wallThick + liscThick2),
                                         ribColor,
                                         supportMedIn);
    tOuterWall->AddNode(TOW, 0, new TGeoTranslation(0, 0, Zshift));

    /// define longitudinal ribs

    std::vector<TGeoVolume*> vLongitRibX(nx);
    std::vector<TGeoVolume*> vLongitRibY(ny);

    double z1_x_thickness_1 = wx(z1 + ribThick) + 2 * (wallThick + liscThick1);
    double z1_x_thickness_2 = wx(z1 + cell_thickness_z) + 2 * (wallThick + liscThick1);

    double z1_x1_Step = (z1_x_thickness_1 - nx * ribThick) / (nx + 1);
    double z1_x2_Step = (z1_x_thickness_2 - nx * ribThick) / (nx + 1);

    double z1_y_thickness_1 = wy(z1 + ribThick) + 2 * (wallThick + liscThick1);
    double z1_y_thickness_2 = wy(z1 + cell_thickness_z) + 2 * (wallThick + liscThick1);

    double z1_y1_Step = (z1_y_thickness_1 - ny * ribThick) / (ny + 1);
    double z1_y2_Step = (z1_y_thickness_2 - ny * ribThick) / (ny + 1);

    double z1_x1, z1_x2, z1_y1, z1_y2;

    z1_x1 = z1_x_thickness_1 / 2;
    z1_x2 = z1_x_thickness_2 / 2;

    z1_y1 = z1_y_thickness_1 / 2 - liscThick1;
    z1_y2 = z1_y_thickness_2 / 2 - liscThick2;

    for (int i = 0; i < nx; i++) {

        z1_x1 = z1_x1 - z1_x1_Step;
        z1_x2 = z1_x2 - z1_x2_Step;

        name = "";
        name.Form("vLongitRibX_%s_phi%d", blockName.Data(), makeId(0, z1_x1, z1_y1));
        vLongitRibX.at(i) = GeoSideObj(
            name, dZ, ribThick, liscThick1, ribThick, liscThick2, z1_x2 - z1_x1, z1_y2 - z1_y1, ribColor, supportMedIn);

        z1_x1 = z1_x1 - ribThick;
        z1_x2 = z1_x2 - ribThick;
    }

    z1_y1 = z1_y_thickness_1 / 2;
    z1_y2 = z1_y_thickness_2 / 2;

    z1_x1 = z1_x_thickness_1 / 2 - liscThick1;
    z1_x2 = z1_x_thickness_2 / 2 - liscThick2;

    for (int i = 0; i < ny; i++) {

        z1_y1 = z1_y1 - z1_y1_Step;
        z1_y2 = z1_y2 - z1_y2_Step;

        name = "";
        name.Form("vLongitRibY_%s_phi%d", blockName.Data(), makeId(0, z1_x1, z1_y1));
        vLongitRibY.at(i) = GeoSideObj(
            name, dZ, liscThick1, ribThick, liscThick2, ribThick, z1_x2 - z1_x1, z1_y2 - z1_y1, ribColor, supportMedIn);
        z1_y1 = z1_y1 - ribThick;
        z1_y2 = z1_y2 - ribThick;
    }

    /// define corner ribs

    name = "CornerRib_L_" + blockName + "_id";
    TGeoVolumeAssembly* CornerRib_L =
        GeoCornerRib(name, ribThick, liscThick1, liscThick2, dZ, slX, slY, ribColor, supportMedIn);
    name = "CornerRib_R_" + blockName + "_id";
    TGeoVolumeAssembly* CornerRib_R =
        GeoCornerRib(name, ribThick, liscThick1, liscThick2, dZ, slY, slX, ribColor, supportMedIn);

    for (double zi = z1; zi < z2; zi += cell_thickness_z) {

        int Zlayer = (int)zi / cell_thickness_z + 1;

        /// define & place vertical ribs
        TString nameVR("");
        nameVR.Form("VetoVerticalRib_z%d", (int)zi);
        TGeoVolume* TVR = GeoTrapezoidHollow(nameVR,
                                             liscThick1,
                                             ribThick,
                                             wx(zi) + 2 * wallThick,
                                             wx(zi + ribThick) + 2 * wallThick,
                                             wy(zi) + 2 * wallThick,
                                             wy(zi + ribThick) + 2 * wallThick,
                                             ribColor,
                                             supportMedIn);
        tZ = Zshift - wz / 2 + zi - z1 + ribThick / 2;

        tVerticalRib->AddNode(TVR, 0, new TGeoTranslation(0, 0, tZ));

        if (z2 - zi < cell_thickness_z)
            continue;

        tX = wx(zi + ribThick) / 2 + wallThick;
        tY = wy(zi + ribThick) / 2 + wallThick;
        tZ = tZ + cell_thickness_z / 2;

        /// place corner ribs
        tLongitRib->AddNode(
            CornerRib_L, makeId(zi, tX, tY), new TGeoCombiTrans(tX, tY, tZ, new TGeoRotation("r", 0, 0, 0)));
        tLongitRib->AddNode(
            CornerRib_L, makeId(zi, -tX, -tY), new TGeoCombiTrans(-tX, -tY, tZ, new TGeoRotation("r", 0, 0, 180)));
        tLongitRib->AddNode(
            CornerRib_R, makeId(zi, -tX, tY), new TGeoCombiTrans(-tX, tY, tZ, new TGeoRotation("r", 0, 0, 90)));
        tLongitRib->AddNode(
            CornerRib_R, makeId(zi, tX, -tY), new TGeoCombiTrans(tX, -tY, tZ, new TGeoRotation("r", 0, 0, 270)));

        double zi_x_thickness_1 = wx(zi + ribThick) + 2 * (wallThick + liscThick1);
        double zi_x_thickness_2 = wx(zi + cell_thickness_z) + 2 * (wallThick + liscThick1);

        double zi_x1_Step = (zi_x_thickness_1 - nx * ribThick) / (nx + 1);
        double zi_x2_Step = (zi_x_thickness_2 - nx * ribThick) / (nx + 1);

        double zi_y_thickness_1 = wy(zi + ribThick) + 2 * (wallThick + liscThick1);
        double zi_y_thickness_2 = wy(zi + cell_thickness_z) + 2 * (wallThick + liscThick1);

        double zi_y1_Step = (zi_y_thickness_1 - ny * ribThick) / (ny + 1);
        double zi_y2_Step = (zi_y_thickness_2 - ny * ribThick) / (ny + 1);

        double zi_x1, zi_x2, zi_y1, zi_y2;

        zi_x1 = zi_x_thickness_1 / 2 - liscThick1;
        zi_x2 = zi_x_thickness_2 / 2 - liscThick1;

        zi_y1 = zi_y_thickness_1 / 2;
        zi_y2 = zi_y_thickness_2 / 2;

        name = "";
        name.Form("LiSc_S4_%d", liscId("LiSc_S4", blockNr, Zlayer, 0, 0));
        TGeoVolume* LiSc_S4 = GeoCornerLiSc2(name,
                                             dZ,
                                             0,
                                             zi_y1_Step - liscThick1,
                                             zi_y2_Step - liscThick2,
                                             liscThick1,
                                             liscThick2,
                                             zi_y2_Step - zi_y1_Step,
                                             zi_x2 - zi_x1,
                                             kMagenta - 10,
                                             vetoMed,
                                             true);
        ttLiSc->AddNode(LiSc_S4,
                        liscId("LiSc_S4", blockNr, Zlayer, 0, 1),
                        new TGeoCombiTrans(zi_x1, -(zi_y1 - zi_y1_Step), tZ, new TGeoRotation("r", 0, 0, 0)));
        ttLiSc->AddNode(LiSc_S4,
                        liscId("LiSc_S4", blockNr, Zlayer, 0, 2),
                        new TGeoCombiTrans(-zi_x1, (zi_y1 - zi_y1_Step), tZ, new TGeoRotation("r", 0, 0, 180)));

        name = "";
        name.Form("LiSc_S6_%d", liscId("LiSc_S6", blockNr, Zlayer, ny, 0));
        TGeoVolume* LiSc_S6 = GeoCornerLiSc2(name,
                                             dZ,
                                             1,
                                             zi_y1_Step - liscThick1,
                                             zi_y2_Step - liscThick2,
                                             liscThick1,
                                             liscThick2,
                                             zi_y2_Step - zi_y1_Step,
                                             zi_x2 - zi_x1,
                                             kMagenta - 10,
                                             vetoMed,
                                             true);
        ttLiSc->AddNode(LiSc_S6,
                        liscId("LiSc_S6", blockNr, Zlayer, ny, 1),
                        new TGeoCombiTrans(zi_x1, (zi_y1 - zi_y1_Step), tZ, new TGeoRotation("r", 0, 0, 0)));
        ttLiSc->AddNode(LiSc_S6,
                        liscId("LiSc_S6", blockNr, Zlayer, ny, 2),
                        new TGeoCombiTrans(-zi_x1, -(zi_y1 - zi_y1_Step), tZ, new TGeoRotation("r", 0, 0, 180)));

        for (int i = 0; i < ny; i++) {

            zi_y1 = zi_y1 - zi_y1_Step;
            zi_y2 = zi_y2 - zi_y2_Step;

            tLongitRib->AddNode(vLongitRibY.at(i),
                                makeId(zi, zi_x1, zi_y1),
                                new TGeoCombiTrans(zi_x1, (zi_y1 - ribThick), tZ, new TGeoRotation("r", 0, 0, 0)));
            tLongitRib->AddNode(vLongitRibY.at(i),
                                makeId(zi, -zi_x1, -zi_y1),
                                new TGeoCombiTrans(-zi_x1, -(zi_y1 - ribThick), tZ, new TGeoRotation("r", 0, 0, 180)));

            if (i > 0) {

                name = "";
                name.Form("LiScY_%d", liscId("LiScY", blockNr, Zlayer, i, 0));
                TGeoVolume* LiScY = GeoSideObj(name,
                                               dZ,
                                               liscThick1,
                                               zi_y1_Step,
                                               liscThick2,
                                               zi_y2_Step,
                                               zi_x2 - zi_x1,
                                               zi_y2 - zi_y1,
                                               kMagenta - 10,
                                               vetoMed,
                                               true);
                ttLiSc->AddNode(LiScY,
                                liscId("LiScY", blockNr, Zlayer, i, 1),
                                new TGeoCombiTrans(zi_x1, zi_y1, tZ, new TGeoRotation("r", 0, 0, 0)));
                ttLiSc->AddNode(LiScY,
                                liscId("LiScY", blockNr, Zlayer, i, 2),
                                new TGeoCombiTrans(-zi_x1, -zi_y1, tZ, new TGeoRotation("r", 0, 0, 180)));
            }

            zi_y1 = zi_y1 - ribThick;
            zi_y2 = zi_y2 - ribThick;
        }

        zi_x1 = zi_x_thickness_1 / 2;
        zi_x2 = zi_x_thickness_2 / 2;

        zi_y1 = zi_y_thickness_1 / 2 - liscThick1;
        zi_y2 = zi_y_thickness_2 / 2 - liscThick1;

        name = "";
        name.Form("LiSc_S3_%d", liscId("LiSc_S3", blockNr, Zlayer, 0, 0));

        TGeoVolume* LiSc_S3 = GeoCornerLiSc1(name,
                                             dZ,
                                             0,
                                             zi_x1_Step - liscThick1 - ribThick / sqrt(2),
                                             zi_x2_Step - liscThick2 - ribThick / sqrt(2),
                                             liscThick1,
                                             liscThick2,
                                             zi_x2_Step - zi_x1_Step - ribThick / 2,
                                             zi_y2 - zi_y1,
                                             kMagenta - 10,
                                             vetoMed,
                                             true);
        ttLiSc->AddNode(LiSc_S3,
                        liscId("LiSc_S3", blockNr, Zlayer, 0, 1),
                        new TGeoCombiTrans(-(zi_x1 - zi_x1_Step), zi_y1, tZ, new TGeoRotation("r", 0, 0, 0)));
        ttLiSc->AddNode(LiSc_S3,
                        liscId("LiSc_S3", blockNr, Zlayer, 0, 2),
                        new TGeoCombiTrans((zi_x1 - zi_x1_Step), -zi_y1, tZ, new TGeoRotation("r", 0, 0, 180)));

        name = "";
        name.Form("LiSc_S5_%d", liscId("LiSc_S5", blockNr, Zlayer, nx, 0));

        TGeoVolume* LiSc_S5 = GeoCornerLiSc1(name,
                                             dZ,
                                             1,
                                             zi_x1_Step - liscThick1 - ribThick / sqrt(2),
                                             zi_x2_Step - liscThick2 - ribThick / sqrt(2),
                                             liscThick1,
                                             liscThick2,
                                             zi_x2_Step - zi_x1_Step - ribThick / 2,
                                             zi_y2 - zi_y1,
                                             kMagenta - 10,
                                             vetoMed,
                                             true);
        ttLiSc->AddNode(LiSc_S5,
                        liscId("LiSc_S5", blockNr, Zlayer, nx, 1),
                        new TGeoCombiTrans((zi_x1 - zi_x1_Step), zi_y1, tZ, new TGeoRotation("r", 0, 0, 0)));
        ttLiSc->AddNode(LiSc_S5,
                        liscId("LiSc_S5", blockNr, Zlayer, nx, 2),
                        new TGeoCombiTrans(-(zi_x1 - zi_x1_Step), -zi_y1, tZ, new TGeoRotation("r", 0, 0, 180)));

        for (int i = 0; i < nx; i++) {
            zi_x1 = zi_x1 - zi_x1_Step;
            zi_x2 = zi_x2 - zi_x2_Step;

            tLongitRib->AddNode(vLongitRibX.at(i),
                                makeId(zi, zi_x1, zi_y1),
                                new TGeoCombiTrans((zi_x1 - ribThick), zi_y1, tZ, new TGeoRotation("r", 0, 0, 0)));
            tLongitRib->AddNode(vLongitRibX.at(i),
                                makeId(zi, -zi_x1, -zi_y1),
                                new TGeoCombiTrans(-(zi_x1 - ribThick), -zi_y1, tZ, new TGeoRotation("r", 0, 0, 180)));

            if (i > 0) {

                name = "";
                name.Form("LiScX_%d", liscId("LiScX", blockNr, Zlayer, i, 0));
                TGeoVolume* LiScX = GeoSideObj(name,
                                               dZ,
                                               zi_x1_Step,
                                               liscThick1,
                                               zi_x2_Step,
                                               liscThick2,
                                               zi_x2 - zi_x1,
                                               zi_y2 - zi_y1,
                                               kMagenta - 10,
                                               vetoMed,
                                               true);
                ttLiSc->AddNode(LiScX,
                                liscId("LiScX", blockNr, Zlayer, i, 1),
                                new TGeoCombiTrans(zi_x1, zi_y1, tZ, new TGeoRotation("r", 0, 0, 0)));
                ttLiSc->AddNode(LiScX,
                                liscId("LiScX", blockNr, Zlayer, i, 2),
                                new TGeoCombiTrans(-zi_x1, -zi_y1, tZ, new TGeoRotation("r", 0, 0, 180)));
            }

            zi_x1 = zi_x1 - ribThick;
            zi_x2 = zi_x2 - ribThick;
        }
    }
}

TGeoVolume* veto::MakeSegments()
{

    TGeoVolumeAssembly* tTankVol = new TGeoVolumeAssembly("T2");

    Double_t cell_thickness_z0 = 800 * mm;   // length of the first cell along z (800mm) 2024 version
    Double_t cell_thickness_z = 820 * mm;    // length of the cell along z (820mm) 2024 version

    TString nameInnerWall = "VetoInnerWall";
    TGeoVolumeAssembly* tInnerWall = new TGeoVolumeAssembly(nameInnerWall);

    TString nameDecayVacuum = "DecayVacuum";
    TGeoVolumeAssembly* tDecayVacuum = new TGeoVolumeAssembly(nameDecayVacuum);

    TString nameOuterWall = "VetoOuterWall";
    TGeoVolumeAssembly* tOuterWall = new TGeoVolumeAssembly(nameOuterWall);

    TString nameLongitRib = "VetoLongitRib";
    TGeoVolumeAssembly* tLongitRib = new TGeoVolumeAssembly(nameLongitRib);

    TString nameVerticalRib = "VetoVerticalRib";
    TGeoVolumeAssembly* tVerticalRib = new TGeoVolumeAssembly(nameVerticalRib);

    TString nameLiSc = "VetoLiSc";
    TGeoVolumeAssembly* ttLiSc = new TGeoVolumeAssembly(nameLiSc);
    int liScCounter = 0;

    int nx = 2;   // number of Longitudinal ribs on X
    int ny = 3;   // number of Longitudinal ribs on Y

    double wallThick = f_InnerSupportThickness;
    double liscThick = f_VetoThickness;
    double ribThick = f_RibThickness;

    //******************************** Block1 **************************************
    double z1 = 0 * m;
    double z2 = 800 * mm;
    double wz = (z2 - z1);

    double slX = (wx(z2) - wx(z1)) / 2 / wz;
    double slY = (wy(z2) - wy(z1)) / 2 / wz;

    double Zshift = wz / 2;   // calibration of Z position

    AddBlock(tInnerWall,
             tDecayVacuum,
             tOuterWall,
             tLongitRib,
             tVerticalRib,
             ttLiSc,
             liScCounter,
             1,
             nx,
             ny,
             z1,
             z2,
             Zshift,
             cell_thickness_z0,
             wallThick,
             liscThick,
             liscThick,
             ribThick);

    //******************************** Block2 **************************************

    Zshift += wz / 2;

    z1 = 800 * mm;
    z2 = 50.0 * m;
    wz = (z2 - z1);

    Zshift += wz / 2;

    AddBlock(tInnerWall,
             tDecayVacuum,
             tOuterWall,
             tLongitRib,
             tVerticalRib,
             ttLiSc,
             liScCounter,
             2,
             nx,
             ny,
             z1,
             z2,
             Zshift,
             cell_thickness_z,
             wallThick,
             liscThick,
             liscThick,
             ribThick);

    double zi = z2;

    TString nameVR("");
    nameVR.Form("VetoVerticalRib_z%d", (int)zi);
    TGeoVolume* TVR = GeoTrapezoidHollow(nameVR,
                                         liscThick,
                                         ribThick,
                                         wx(zi) + 2 * wallThick,
                                         wx(zi + ribThick) + 2 * wallThick,
                                         wy(zi) + 2 * wallThick,
                                         wy(zi + ribThick) + 2 * wallThick,
                                         15,
                                         supportMedIn);
    double tZ = Zshift - wz / 2 + zi - z1 + ribThick / 2;

    tVerticalRib->AddNode(TVR, 0, new TGeoTranslation(0, 0, tZ));

    tTankVol->AddNode(tInnerWall, 0, new TGeoTranslation(0, 0, 0));
    tTankVol->AddNode(tDecayVacuum, 0, new TGeoTranslation(0, 0, 0));
    tTankVol->AddNode(tOuterWall, 0, new TGeoTranslation(0, 0, 0));
    tTankVol->AddNode(tVerticalRib, 0, new TGeoTranslation(0, 0, 0));
    tTankVol->AddNode(tLongitRib, 0, new TGeoTranslation(0, 0, 0));
    tTankVol->AddNode(ttLiSc, 0, new TGeoTranslation(0, 0, 0));

    return tTankVol;
}

// -----   Private method InitMedium
Int_t veto::InitMedium(const char* name)
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

// -------------------------------------------------------------------------
/**
 * @brief Processes a hit in the veto detector.
 *
 * This method is called whenever a hit is registered in the veto detector.
 * It processes the hit information and records the relevant data.
 *
 * @param x X-coordinate of the hit.
 * @param y Y-coordinate of the hit.
 * @param z Z-coordinate of the hit.
 * @param time Time of the hit.
 * @param energy Energy deposited by the hit.
 * @return True if the hit was processed successfully, false otherwise.
 */
Bool_t veto::ProcessHits(FairVolume* vol)
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

    // Create vetoPoint at exit of active volume
    if (gMC->IsTrackExiting() || gMC->IsTrackStop() || gMC->IsTrackDisappeared()) {
        if (fELoss == 0.) {
            return kFALSE;
        }

        fTrackID = gMC->GetStack()->GetCurrentTrackNumber();

        Int_t veto_uniqueId;
        gMC->CurrentVolID(veto_uniqueId);
        TParticle* p = gMC->GetStack()->GetCurrentTrack();
        Int_t pdgCode = p->GetPdgCode();
        TLorentzVector pos;
        gMC->TrackPosition(pos);
        TLorentzVector Mom;
        gMC->TrackMomentum(Mom);
        Double_t xmean = (fPos.X() + pos.X()) / 2.;
        Double_t ymean = (fPos.Y() + pos.Y()) / 2.;
        Double_t zmean = (fPos.Z() + pos.Z()) / 2.;
        AddHit(fTrackID,
               veto_uniqueId,
               TVector3(xmean, ymean, zmean),
               TVector3(fMom.Px(), fMom.Py(), fMom.Pz()),
               fTime,
               fLength,
               fELoss,
               pdgCode,
               TVector3(pos.X(), pos.Y(), pos.Z()),
               TVector3(Mom.Px(), Mom.Py(), Mom.Pz()));

        // Increment number of veto det points in TParticle
        ShipStack* stack = (ShipStack*)gMC->GetStack();
        stack->AddPoint(kVETO);
    }

    return kTRUE;
}

void veto::EndOfEvent()
{

    fvetoPointCollection->Clear();
}

void veto::PreTrack()
{
    if (!fFastMuon) {
        return;
    }
    if (TMath::Abs(gMC->TrackPid()) != 13) {
        gMC->StopTrack();
    }
}
void veto::Register()   // create a branch in the output tree
{

    FairRootManager::Instance()->Register(
        "vetoPoint",
        "veto",
        fvetoPointCollection,
        kTRUE);   // kFALSE -> this collection will not be written to the file, will exist only during simulation.
}

TClonesArray* veto::GetCollection(Int_t iColl) const
{
    if (iColl == 0) {
        return fvetoPointCollection;
    } else {
        return NULL;
    }
}

void veto::Reset()
{
    fvetoPointCollection->Clear();
}

/**
 * @brief Constructs the detector geometry.
 *
 * This function is responsible for setting up the geometry of the DecayVolume+SBT detector.
 * It is called during the detector's construction phase.
 */

void veto::ConstructGeometry()
{

    TGeoVolume* top = gGeoManager->GetTopVolume();

    InitMedium("vacuums");
    InitMedium("Aluminum");
    InitMedium("helium");
    InitMedium("Scintillator");
    InitMedium("steel");

    gGeoManager->SetNsegments(100);

    vetoMed = gGeoManager->GetMedium(vetoMed_name);   //! medium of veto counter, liquid or plastic scintillator
    supportMedIn = gGeoManager->GetMedium(supportMedIn_name);       //! medium of support structure, iron, balloon
    supportMedOut = gGeoManager->GetMedium(supportMedOut_name);     //! medium of support structure, aluminium, balloon
    decayVolumeMed = gGeoManager->GetMedium(decayVolumeMed_name);   // decay volume, air/helium/vacuum
    LOG(INFO) << "veto: Decay Volume medium set as: " <<  decayVolumeMed_name;
    TGeoVolume* tDecayVol = new TGeoVolumeAssembly("DecayVolume");

    TGeoVolume* seg = MakeSegments();
    tDecayVol->AddNode(seg, 1, new TGeoTranslation(0, 0, 0));
    top->AddNode(tDecayVol, 1, new TGeoTranslation(0, 0, zStartDecayVol));   //));

    // only for fastMuon simulation, otherwise output becomes too big
    if (fFastMuon && fFollowMuon) {
        const char* Vol = "TGeoVolume";
        const char* Cavern = "Cavern";
        const char* Ain = "AbsorberAdd";
        const char* Aout = "AbsorberAddCore";
        TObjArray* volumelist = gGeoManager->GetListOfVolumes();
        int lastvolume = volumelist->GetLast();
        int volumeiterator = 0;
        while (volumeiterator <= lastvolume) {
            const char* volumename = volumelist->At(volumeiterator)->GetName();
            const char* classname = volumelist->At(volumeiterator)->ClassName();
            if (strstr(classname, Vol)) {
                if (strstr(volumename, Cavern) || strstr(volumename, Ain) || strstr(volumename, Aout)) {
                    AddSensitiveVolume(gGeoManager->GetVolume(volumename));
                    LOG(INFO) << "veto: made sensitive for following muons: " << volumename;
                }
            }
            volumeiterator++;
        }
    }
}

vetoPoint* veto::AddHit(Int_t trackID,
                        Int_t detID,
                        TVector3 pos,
                        TVector3 mom,
                        Double_t time,
                        Double_t length,
                        Double_t eLoss,
                        Int_t pdgCode,
                        TVector3 Lpos,
                        TVector3 Lmom)
{
    TClonesArray& clref = *fvetoPointCollection;
    Int_t size = clref.GetEntriesFast();
    return new (clref[size]) vetoPoint(trackID, detID, pos, mom, time, length, eLoss, pdgCode, Lpos, Lmom);
}
