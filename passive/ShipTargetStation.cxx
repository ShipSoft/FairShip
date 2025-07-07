#include "ShipTargetStation.h"

#include "FairGeoBuilder.h"
#include "FairGeoMedia.h"
#include "FairLogger.h"
#include "FairRun.h"         // for FairRun
#include "FairRuntimeDb.h"   // for FairRuntimeDb
#include "ShipUnit.h"
#include "TGeoBBox.h"
#include "TGeoCompositeShape.h"
#include "TGeoManager.h"
#include "TGeoMaterial.h"
#include "TGeoMedium.h"
#include "TGeoShapeAssembly.h"
#include "TGeoTube.h"
#include "TList.h"       // for TListIter, TList (ptr only)
#include "TObjArray.h"   // for TObjArray
#include "TString.h"     // for TString

using ShipUnit::mm;

ShipTargetStation::~ShipTargetStation() {}
ShipTargetStation::ShipTargetStation()
    : FairModule("ShipTargetStation", "")
{}

ShipTargetStation::ShipTargetStation(const char* name,
                                     const Double_t tl,
                                     const Double_t tz,
                                     const TargetVersion tV,
                                     const int nS,
                                     const char* Title)
    : FairModule(name, Title)
{
    fTargetLength = tl;
    fTargetZ = tz;
    fTV = tV;
    fnS = nS;
}

// -----   Private method InitMedium
Int_t ShipTargetStation::InitMedium(const char* name)
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

void ShipTargetStation::ConstructGeometry()
{
    TGeoVolume* top = gGeoManager->GetTopVolume();

    InitMedium("tungsten");
    TGeoMedium* tungsten = gGeoManager->GetMedium("tungsten");
    InitMedium("molybdenum");
    TGeoMedium* mo = gGeoManager->GetMedium("molybdenum");
    InitMedium("iron");
    TGeoMedium* iron = gGeoManager->GetMedium("iron");
    InitMedium("copper");
    TGeoMedium* copper = gGeoManager->GetMedium("copper");

    InitMedium("H2O");
    TGeoMedium* water = gGeoManager->GetMedium("H2O");

    double He_T = 363.15;               // in K, use average 90 degrees C.
    double He_P = 1.6e6 * 6.241509e3;   // 16 bar in MeV/mm3
    InitMedium("PressurisedHe90");
    TGeoMedium* pressurised_He = gGeoManager->GetMedium("PressurisedHe90");

    // CAMM- dirty fix to have pressure and temperature correct for Geant4.
    // Should fix this properly in future...
    TGeoMaterial* fixedCooler = pressurised_He->GetMaterial();
    fixedCooler->SetTemperature(He_T);
    fixedCooler->SetPressure(He_P);
    TGeoMedium* cooler = (fTV == TargetVersion::Jun25) ? pressurised_He : water;

    LOG(INFO) << "-- Target cooler: " << cooler->GetName() << " T=" << cooler->GetMaterial()->GetTemperature()
              << " K, P=" << cooler->GetMaterial()->GetPressure() << " MeV/mm3";

    TGeoVolume* tTarget = new TGeoVolumeAssembly("TargetArea");

    Double_t zPos = 0.;
    Int_t slots = fnS;
    slots = slots - 1;

    TGeoVolume* target;
    TGeoVolume* slit;
    // Double_t zPos =  fTargetZ - fTargetLength/2.;
    for (Int_t i = 0; i < fnS; i++) {   // loop on layers
        TString nmi = "Target_";
        nmi += i + 1;
        TString sm = "Slit_";
        sm += i + 1;
        TGeoMedium* material;
        if (fM.at(i) == "molybdenum") {
            material = mo;
        };
        if (fM.at(i) == "tungsten") {
            material = tungsten;
        };

        target = gGeoManager->MakeTube(nmi, material, 0., fDiameter / 2., fL.at(i) / 2.);
        if (fM.at(i) == "molybdenum") {
            target->SetLineColor(28);
        } else {
            target->SetLineColor(38);
        };   // silver/blue
        tTarget->AddNode(target, 1, new TGeoTranslation(0, 0, zPos + fL.at(i) / 2.));
        if (i < slots) {
            slit = gGeoManager->MakeTube(sm, cooler, 0., fDiameter / 2., fG.at(i) / 2.);
            slit->SetLineColor(7);   // cyan
            tTarget->AddNode(slit, 1, new TGeoTranslation(0, 0, zPos + fL.at(i) + fG.at(i) / 2.));
            zPos += fL.at(i) + fG.at(i);
        } else {
            zPos += fL.at(i);
        }
    }   // loop on layers

    // Proximity shielding

    double start_of_target = fTargetZ - fTargetLength / 2.;
    fTargetLength = 1586.4 * mm;  // Make shielding independent of actual target length
    double shielding_width = 1600 * mm;
    double shielding_length = 3000 * mm;
    double proximity_shielding_height = 1126 * mm;
    double proximity_shielding_thickness = 250 * mm;
    double proximity_shielding_thickness_front = 550 * mm;
    double proximity_shielding_hole_diameter = 200 * mm;
    double proximity_shielding_hole_height = 735 * mm;
    double proximity_shielding_distance_after_target = 96.1 * mm;
    double shielding_position = start_of_target + fTargetLength + proximity_shielding_distance_after_target
                                             + proximity_shielding_thickness - shielding_length / 2;
    auto proximity_shielding_envelope = new TGeoBBox("proximity_shielding_envelope",
                                                     shielding_width / 2,
                                                     proximity_shielding_height / 2,
                                                     shielding_length / 2);
    auto proximity_shielding_inner = new TGeoBBox(
        "proximity_shielding_inner",
        shielding_width / 2 - proximity_shielding_thickness,
        proximity_shielding_height / 2,
        (shielding_length - (proximity_shielding_thickness_front + proximity_shielding_thickness)) / 2);
    auto proximity_shielding_hole = new TGeoTube(
        "proximity_shielding_hole", 0, proximity_shielding_hole_diameter / 2, proximity_shielding_thickness_front / 2);
    auto proximity_shielding_inner_shift = new TGeoTranslation(
        "proximity_shielding_inner_shift", 0, 0, (proximity_shielding_thickness_front - proximity_shielding_thickness) / 2);
    proximity_shielding_inner_shift->RegisterYourself();
    auto proximity_shielding_hole_shift =
        new TGeoTranslation("proximity_shielding_hole_shift",
                            0,
                            proximity_shielding_hole_height - proximity_shielding_height / 2,
                            -shielding_length / 2 + proximity_shielding_thickness_front / 2);
    proximity_shielding_hole_shift->RegisterYourself();
    auto proximity_shielding_shape =
        new TGeoCompositeShape("proximity_shielding_shape",
                               "proximity_shielding_envelope"
                               "- proximity_shielding_inner:proximity_shielding_inner_shift"
                               "- proximity_shielding_hole:proximity_shielding_hole_shift");
    auto proximity_shielding = new TGeoVolume("proximity_shielding", proximity_shielding_shape, copper);
    auto proximity_shielding_centre =
        new TGeoTranslation(
            0., -(proximity_shielding_hole_height - proximity_shielding_height / 2), shielding_position);

    top->AddNode(proximity_shielding, 1, proximity_shielding_centre);

    // Iron shielding
    double top_shielding_height = 600 * mm;
    double bottom_shielding_height = 545 * mm;
    auto top_shielding = gGeoManager->MakeBox(
        "top_shielding", iron, shielding_width / 2, top_shielding_height / 2, shielding_length / 2);
    top->AddNode(
        top_shielding,
        1,
        new TGeoTranslation(0.,
                            top_shielding_height / 2 + proximity_shielding_height - proximity_shielding_hole_height,
                            shielding_position));
    auto bottom_shielding = gGeoManager->MakeBox(
        "bottom_shielding", iron, shielding_width / 2, bottom_shielding_height / 2, shielding_length / 2);
    top->AddNode(bottom_shielding,
                 1,
                 new TGeoTranslation(
                     0., -bottom_shielding_height / 2 - proximity_shielding_hole_height, shielding_position));
    double pedestal_length = 2170 * mm;
    double pedestal_width = 1070 * mm;
    double pedestal_height = 150 * mm;
    auto shielding_pedestal =
        gGeoManager->MakeBox("shielding_pedestal", iron, pedestal_width / 2, pedestal_height / 2, pedestal_length / 2);
    top->AddNode(
        shielding_pedestal,
        1,
        new TGeoTranslation(0.,
                            pedestal_height / 2 - proximity_shielding_hole_height,
                            shielding_position - shielding_length / 2 + 565 * mm + pedestal_length / 2));

    top->AddNode(tTarget, 1, new TGeoTranslation(0, 0, start_of_target));
}
