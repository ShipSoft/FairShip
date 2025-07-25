#include "ShipMuonShield.h"

#include "FairGeoBuilder.h"
#include "FairGeoInterface.h"
#include "FairGeoMedia.h"
#include "FairLogger.h"      /// for FairLogger, MESSAGE_ORIGIN
#include "FairRuntimeDb.h"   // for FairRuntimeDb
#include "ShipUnit.h"
#include "TFile.h"
#include "TGeoBBox.h"
#include "TGeoBoolNode.h"
#include "TGeoCompositeShape.h"
#include "TGeoManager.h"
#include "TGeoMaterial.h"
#include "TGeoTrd1.h"
#include "TGeoTube.h"
#include "TObjArray.h"   // for TObjArray
#include "TString.h"     // for TString

#include <iostream>   // for operator<<, basic_ostream, etc

using ShipUnit::cm;
using ShipUnit::m;
using ShipUnit::mm;
using ShipUnit::tesla;

ShipMuonShield::~ShipMuonShield() {}
ShipMuonShield::ShipMuonShield() : FairModule("ShipMuonShield", "") {}

ShipMuonShield::ShipMuonShield(std::vector<double> in_params,
                               Double_t z,
                               const Bool_t WithConstShieldField,
                               const Bool_t SC_key)
    : FairModule("MuonShield", "ShipMuonShield")
{
  for(size_t i = 0; i < in_params.size(); i++){
      shield_params.push_back(in_params[i]);
  }
  fWithConstShieldField = WithConstShieldField;
  fSC_mag = SC_key;
  dZ1 = in_params[0];
  dZ2 = in_params[1];
  dZ3 = in_params[2];
  dZ4 = in_params[3];
  dZ5 = in_params[4];
  dZ6 = in_params[5];
  dZ7 = in_params[6];
  fMuonShieldHalfLength = dZ1 + dZ2 + dZ3 + dZ4 + dZ5 + dZ6 + dZ7;
  z_end_of_proximity_shielding = z;
}

// -----   Private method InitMedium
Int_t ShipMuonShield::InitMedium(TString name)
{
   static FairGeoLoader *geoLoad=FairGeoLoader::Instance();
   static FairGeoInterface *geoFace=geoLoad->getGeoInterface();
   static FairGeoMedia *media=geoFace->getMedia();
   static FairGeoBuilder *geoBuild=geoLoad->getGeoBuilder();

   FairGeoMedium *ShipMedium=media->getMedium(name);

   if (!ShipMedium)
     Fatal("InitMedium","Material %s not defined in media file.", name.Data());
   TGeoMedium* medium=gGeoManager->GetMedium(name);
   if (medium)
     return ShipMedium->getMediumIndex();
   return geoBuild->createMedium(ShipMedium);
}


void ShipMuonShield::SetSNDSpace(Bool_t hole, Double_t hole_dx, Double_t hole_dy)
{
  snd_hole = hole;
  snd_hole_dx = hole_dx / 2.; // since the hole is cut in 2 halves, we need to divide the width by 2
  snd_hole_dy = hole_dy;
}

void ShipMuonShield::CreateArb8(TString                         arbName,
                                TGeoMedium*                     medium,
                                Double_t                        dZ,
                                std::array<Double_t,16>         corners,
                                Int_t                           color,
                                TGeoUniformMagField*            magField,
                                TGeoVolume*                     tShield,
                                Double_t                        x_translation,
                                Double_t                        y_translation,
                                Double_t                        z_translation) {
  TGeoVolume* magVol = nullptr;

  if (snd_hole &&
      (arbName == "Magn6_MiddleMagL" || arbName == "Magn6_MiddleMagR")) {
    //
    // 1) Raw Arb8 “shape”
    //
    TString shapeName = arbName + "_shape";
    gGeoManager->MakeArb8(shapeName,
                         medium,
                         dZ,
                         corners.data());

    //
    // 2) Void box that’s 0.1 mm smaller on each half-length
    //
    constexpr double eps = 0.01;  // mm anti-overlap
    double void_dx = snd_hole_dx - eps;
    double void_dy = snd_hole_dy - eps;
    TString voidName = arbName + "_void";
    gGeoManager->MakeBox(voidName,
                         medium,
                         void_dx,
                         void_dy,
                         dZ);

    //
    // 3) Single named translation for the subtraction
    //
    Double_t shift = (corners[1] > 0 ? -void_dx : void_dx);
    TString transName = arbName + "_t";
    auto* tr = new TGeoTranslation(transName.Data(),
                                   shift,
                                   0.0,
                                   0.0);
    tr->RegisterYourself();

    //
    // 4) Composite shape: <shape> minus the translated <void>
    //
    TString compName = arbName + "_comp";
    TString expr     = TString::Format("%s - %s:%s",
                                       shapeName.Data(),
                                       voidName.Data(),
                                       transName.Data());
    auto* compShape = new TGeoCompositeShape(compName.Data(),
                                             expr.Data());

    //
    // 5) Wrap the composite in a volume
    //
    magVol = new TGeoVolume(arbName,
                            compShape,
                            medium);
  }
  else {
    // original uncut magnet
    magVol = gGeoManager->MakeArb8(arbName,
                                   medium,
                                   dZ,
                                   corners.data());
  }

  // common settings
  magVol->SetLineColor(color);
  if (fWithConstShieldField) {
    magVol->SetField(magField);
  }
  tShield->AddNode(magVol, 1,
                   new TGeoTranslation(x_translation,
                                       y_translation,
                                       z_translation));
}

void ShipMuonShield::CreateMagnet(TString magnetName,TGeoMedium* medium,TGeoVolume *tShield,TGeoUniformMagField *fields[4],FieldDirection fieldDirection,
				  Double_t dX, Double_t dY, Double_t dX2, Double_t dY2,
          Double_t ratio_yoke_1, Double_t ratio_yoke_2,
          Double_t dY_yoke_1, Double_t dY_yoke_2,
          Double_t dZ,
				  Double_t middleGap,Double_t middleGap2,
				  Double_t gap,Double_t gap2, Double_t Z, Bool_t NotMagnet,
          Bool_t SC_key = false)
  {
    Double_t coil_gap,coil_gap2;
    Int_t color[4] = {45,31,30,38};
    gap = std::ceil(std::max(100. / dY, gap));
    gap2 = std::ceil(std::max(100. / dY2, gap2));
    coil_gap = gap;
    coil_gap2 = gap2;

    Double_t anti_overlap = 0.1; // gap between fields in the
						   // corners for mitred joints
						   // (Geant goes crazy when
						   // they touch each other)

    std::array<Double_t, 16> cornersMainL = {
      middleGap,
      -(dY +dY_yoke_1)- anti_overlap,
      middleGap,
      dY + dY_yoke_1- anti_overlap,
      dX + middleGap,
      dY- anti_overlap,
      dX + middleGap,
      -(dY- anti_overlap),
      middleGap2,
      -(dY2 + dY_yoke_2- anti_overlap), middleGap2,
      dY2 + dY_yoke_2- anti_overlap,
      dX2 + middleGap2,
      dY2- anti_overlap,
      dX2 + middleGap2,
      -(dY2- anti_overlap)
      };

      std::array<Double_t, 16> cornersTL = {
        middleGap + dX,dY,
        middleGap,
        dY + dY_yoke_1,
        dX + ratio_yoke_1*dX + middleGap + coil_gap,
        dY + dY_yoke_1,
        dX + middleGap + coil_gap,
        dY,
        middleGap2 + dX2,
        dY2,
        middleGap2,
        dY2 + dY_yoke_2,
        dX2 + ratio_yoke_2*dX2 + middleGap2 + coil_gap2,
        dY2 + dY_yoke_2,
        dX2 + middleGap2 + coil_gap2,
        dY2
      };

      std::array<Double_t, 16> cornersMainSideL = {
        dX + middleGap + gap,
        -(dY),
        dX + middleGap + gap,
        dY,
        dX + ratio_yoke_1*dX + middleGap + gap,
        dY + dY_yoke_1,
        dX + ratio_yoke_1*dX + middleGap + gap,
        -(dY + dY_yoke_1),
        dX2 + middleGap2 + gap2,
        -(dY2),
        dX2 + middleGap2 + gap2,
        dY2,
        dX2 + ratio_yoke_2*dX2 + middleGap2 + gap2,
        dY2 + dY_yoke_2,
        dX2 + ratio_yoke_2*dX2 + middleGap2 + gap2,
        -(dY2 + dY_yoke_2)
      };
      // SC part
    if(SC_key){
      cornersMainL = {
      middleGap, -(dY + 3*dX - anti_overlap),
      middleGap, dY + 3*dX - anti_overlap,
      dX + middleGap, dY - anti_overlap,
      dX + middleGap, -(dY - anti_overlap),
      middleGap2, -(dY2 + 3*dX2 - anti_overlap),
      middleGap2, dY2 + 3*dX2 - anti_overlap,
      dX2 + middleGap2, dY2 - anti_overlap,
      dX2 + middleGap2, -(dY2 - anti_overlap)
        };

      cornersTL = {middleGap + dX,
                    dY,
                    middleGap,
                    dY + 3*dX,
                    4 * dX + middleGap + coil_gap,
                    dY + 3*dX,
                    dX + middleGap + coil_gap,
                    dY,
                    middleGap2 + dX2,
                    dY2,
                    middleGap2,
                    dY2 + 3*dX2,
                    4 * dX2 + middleGap2 + coil_gap2,
                    dY2 + 3*dX2,
                    dX2 + middleGap2 + coil_gap2,
                    dY2};

      cornersMainSideL ={
      dX + middleGap + gap, -(dY - anti_overlap),
      dX + middleGap + gap, dY - anti_overlap,
      4 * dX + middleGap + gap, dY + 3*dX - anti_overlap,
      4 * dX + middleGap + gap, -(dY + 3*dX - anti_overlap),
      dX2 + middleGap2 + gap2, -(dY2 - anti_overlap),
      dX2 + middleGap2 + gap2, dY2 - anti_overlap,
      4 * dX2 + middleGap2 + gap2, dY2 + 3*dX2 - anti_overlap,
      4 * dX2 + middleGap2 + gap2, -(dY2 + 3*dX2 - anti_overlap)
      };
    }
    std::array<Double_t, 16> cornersMainR, cornersCLBA,
       cornersMainSideR, cornersCLTA, cornersCRBA,
       cornersCRTA, cornersTR, cornersBL, cornersBR;
    // Use symmetries to define remaining magnets
    for (int i = 0; i < 16; ++i) {
      cornersMainR[i] = -cornersMainL[i];
      cornersMainSideR[i] = -cornersMainSideL[i];
      cornersCRTA[i] = -cornersCLBA[i];
      cornersBR[i] = -cornersTL[i];
    }
    // Need to change order as corners need to be defined clockwise
    for (int i = 0, j = 4; i < 8; ++i) {
      j = (11 - i) % 8;
      cornersCLTA[2 * j] = cornersCLBA[2 * i];
      cornersCLTA[2 * j + 1] = -cornersCLBA[2 * i + 1];
      cornersTR[2 * j] = -cornersTL[2 * i];
      cornersTR[2 * j + 1] = cornersTL[2 * i + 1];
    }
    for (int i = 0; i < 16; ++i) {
      cornersCRBA[i] = -cornersCLTA[i];
      cornersBL[i] = -cornersTR[i];
    }

    TString str1L = "_MiddleMagL";
    TString str1R = "_MiddleMagR";
    TString str2 = "_MagRetL";
    TString str3 = "_MagRetR";
    TString str4 = "_MagCLB";
    TString str5 = "_MagCLT";
    TString str6 = "_MagCRT";
    TString str7 = "_MagCRB";
    TString str8 = "_MagTopLeft";
    TString str9 = "_MagTopRight";
    TString str10 = "_MagBotLeft";
    TString str11 = "_MagBotRight";

    switch (fieldDirection){

    case FieldDirection::up:
      CreateArb8(magnetName + str1L, medium, dZ, cornersMainL, color[0], fields[0], tShield,  0, 0, Z);
      CreateArb8(magnetName + str1R, medium, dZ, cornersMainR, color[0], fields[0], tShield,  0, 0, Z);
      CreateArb8(magnetName + str2, medium, dZ, cornersMainSideL, color[1], fields[1], tShield,  0, 0, Z);
      CreateArb8(magnetName + str3, medium, dZ, cornersMainSideR, color[1], fields[1], tShield,  0, 0, Z);
      CreateArb8(magnetName + str8, medium, dZ, cornersTL, color[3], fields[3], tShield,  0, 0, Z);
      CreateArb8(magnetName + str9, medium, dZ, cornersTR, color[2], fields[2], tShield,  0, 0, Z);
      CreateArb8(magnetName + str10, medium, dZ, cornersBL, color[2], fields[2], tShield,  0, 0, Z);
      CreateArb8(magnetName + str11, medium, dZ, cornersBR, color[3], fields[3], tShield,  0, 0, Z);
      break;
    case FieldDirection::down:
      CreateArb8(magnetName + str1L, medium, dZ, cornersMainL, color[1], fields[1], tShield,  0, 0, Z);
      CreateArb8(magnetName + str1R, medium, dZ, cornersMainR, color[1], fields[1], tShield,  0, 0, Z);
      CreateArb8(magnetName + str2, medium, dZ, cornersMainSideL, color[0], fields[0], tShield,  0, 0, Z);
      CreateArb8(magnetName + str3, medium, dZ, cornersMainSideR, color[0], fields[0], tShield,  0, 0, Z);
      CreateArb8(magnetName + str8, medium, dZ, cornersTL, color[2], fields[2], tShield,  0, 0, Z);
      CreateArb8(magnetName + str9, medium, dZ, cornersTR, color[3], fields[3], tShield,  0, 0, Z);
      CreateArb8(magnetName + str10, medium, dZ, cornersBL, color[3], fields[3], tShield,  0, 0, Z);
      CreateArb8(magnetName + str11, medium, dZ, cornersBR, color[2], fields[2], tShield,  0, 0, Z);
      break;
    }
  }

Int_t ShipMuonShield::Initialize(std::vector<TString> &magnetName,
				std::vector<FieldDirection> &fieldDirection,
				std::vector<Double_t> &dXIn, std::vector<Double_t> &dYIn,
				std::vector<Double_t> &dXOut, std::vector<Double_t> &dYOut,
        std::vector<Double_t> &ratio_yokesIn, std::vector<Double_t> &ratio_yokesOut,
        std::vector<Double_t> &dY_yokeIn, std::vector<Double_t> &dY_yokeOut,
				std::vector<Double_t> &dZ, std::vector<Double_t> &midGapIn,
				std::vector<Double_t> &midGapOut,
        std::vector<Double_t> &Bgoal,
				std::vector<Double_t> &gapIn, std::vector<Double_t> &gapOut,
				std::vector<Double_t> &Z) {
  const Int_t nMagnets = 7;
  LOG(INFO) << " Initialize the MS ";
  magnetName.reserve(nMagnets);
  fieldDirection.reserve(nMagnets);
  for (auto i :
       {&dXIn, &dXOut, &dYIn, &dYOut, &dZ, &midGapIn, &midGapOut,
	&ratio_yokesIn , &ratio_yokesOut, &dY_yokeIn, &dY_yokeOut, &Bgoal, &gapIn, &gapOut, &Z}) {
    i->reserve(nMagnets);
  }

  Double_t z_gap = 10 * cm;   // fixed distance between magnets in Z-axis

  magnetName = {"MagnAbsorb", "Magn1", "Magn2", "Magn3",
    "Magn4",       "Magn5",       "Magn6"};

  fieldDirection = {
FieldDirection::up,   FieldDirection::up,   FieldDirection::up,
FieldDirection::up,   FieldDirection::down,   FieldDirection::down,
FieldDirection::down };

  std::vector<Double_t> params;
  params = shield_params;

  const int offset = nMagnets;
  const int nParams = 13;


  for (Int_t i = 0; i < nMagnets; ++i) {
    dXIn[i] = params[offset + i * nParams + 0];
    dXOut[i] = params[offset + i * nParams + 1];
    dYIn[i] = params[offset + i * nParams + 2];
    dYOut[i] = params[offset + i * nParams + 3];
    gapIn[i] = params[offset + i * nParams + 4];
    gapOut[i] = params[offset + i * nParams + 5];
    ratio_yokesIn[i] = params[offset + i * nParams + 6];
    ratio_yokesOut[i] = params[offset + i * nParams + 7];
    dY_yokeIn[i] = params[offset + i * nParams + 8];
    dY_yokeOut[i] = params[offset + i * nParams + 9];
    midGapIn[i] = params[offset + i * nParams + 10];
    midGapOut[i] = params[offset + i * nParams + 11];
    Bgoal[i] = params[offset + i * nParams + 12];
  }

  dZ[0] = dZ1 - z_gap / 2;
  Z[0] = z_end_of_proximity_shielding + dZ[0] + z_gap;
  dZ[1] = dZ2 - z_gap / 2;
  Z[1] = Z[0] + dZ[0] + dZ[1] + z_gap;
  dZ[2] = dZ3 - z_gap / 2;
  Z[2] = Z[1] + dZ[1] + dZ[2] + 2 * z_gap;
  dZ[3] = dZ4 - z_gap / 2;
  Z[3] = Z[2] + dZ[2] + dZ[3] + z_gap;
  dZ[4] = dZ5 - z_gap / 2;
  Z[4] = Z[3] + dZ[3] + dZ[4] + z_gap;
  dZ[5] = dZ6 - z_gap / 2;
  Z[5] = Z[4] + dZ[4] + dZ[5] + z_gap;
  dZ[6] = dZ7 - z_gap / 2;
  Z[6] = Z[5] + dZ[5] + dZ[6] + z_gap;

  return nMagnets;
}
void ShipMuonShield::ConstructGeometry()
{
    TGeoVolume *top=gGeoManager->GetTopVolume();
    TGeoVolume* tShield = new TGeoVolumeAssembly("MuonShieldArea");
    InitMedium("iron");
    TGeoMedium* iron = gGeoManager->GetMedium("iron");

    std::vector<TString> magnetName;
    std::vector<FieldDirection> fieldDirection;
    std::vector<Double_t> dXIn, dYIn, dXOut, dYOut, dZf, midGapIn, midGapOut, ratio_yokesIn, ratio_yokesOut, dY_yokeIn,
        dY_yokeOut, gapIn, gapOut, Bgoal, Z;
    const Int_t nMagnets = Initialize(magnetName,
                                      fieldDirection,
                                      dXIn,
                                      dYIn,
                                      dXOut,
                                      dYOut,
                                      ratio_yokesIn,
                                      ratio_yokesOut,
                                      dY_yokeIn,
                                      dY_yokeOut,
                                      dZf,
                                      midGapIn,
                                      midGapOut,
                                      Bgoal,
                                      gapIn,
                                      gapOut,
                                      Z);

    // Create TCC8 tunnel around muon shield

    std::array<double, 7> fieldScale = {{1., 1., 1., 1., 1., 1., 1.}};
    for (Int_t nM = 0; nM < (nMagnets); nM++) {
        if (dZf[nM] < 1e-5 || dXIn[nM] == 0){
                    continue;
                  }
        Double_t ironField_s = Bgoal[nM] * fieldScale[nM] * tesla;
        TGeoUniformMagField *magFieldIron_s = new TGeoUniformMagField(0.,ironField_s,0.);
        TGeoUniformMagField *RetField_s     = new TGeoUniformMagField(0.,-ironField_s,0.);
        TGeoUniformMagField *ConRField_s    = new TGeoUniformMagField(-ironField_s,0.,0.);
        TGeoUniformMagField *ConLField_s    = new TGeoUniformMagField(ironField_s,0.,0.);
        TGeoUniformMagField *fields_s[4] = {magFieldIron_s,RetField_s,ConRField_s,ConLField_s};
        // Create the magnet
        CreateMagnet(magnetName[nM], iron, tShield, fields_s, fieldDirection[nM],
          dXIn[nM], dYIn[nM], dXOut[nM], dYOut[nM],  ratio_yokesIn[nM], ratio_yokesOut[nM], dY_yokeIn[nM], dY_yokeOut[nM], dZf[nM],
          midGapIn[nM], midGapOut[nM], gapIn[nM], gapOut[nM], Z[nM], nM==0, nM == 3 && fSC_mag);
        }

      // Place in origin of SHiP coordinate system as subnodes placed correctly
      top->AddNode(tShield, 1);

      Double_t z_gap = 10 * cm;
      Double_t absorber_offset = z_gap;
      Double_t absorber_half_length = (dZf[0]);

      // Absorber

      auto abs = new TGeoBBox("absorber", 4.995 * m - 0.002 * m, 3.75 * m, absorber_half_length - 0.002 * m);
      auto *absorber_shift = new TGeoTranslation("absorber_shift", 1.435 * m, 2.05 * m, 0);
      absorber_shift->RegisterYourself();

      const std::vector<TString> absorber_magnets = {"MagnAbsorb"};
      const std::vector<TString> magnet_components = {
        "_MiddleMagL", "_MiddleMagR",  "_MagRetL",    "_MagRetR",
        "_MagTopLeft", "_MagTopRight", "_MagBotLeft", "_MagBotRight",
    };
      TString absorber_magnet_components;
      for (auto &&magnet_component : magnet_components) {
          absorber_magnet_components += ("-" + absorber_magnets[0] + magnet_component);
      }

      TGeoCompositeShape* absorberShape =
          new TGeoCompositeShape("Absorber", "absorber:absorber_shift" + absorber_magnet_components);

      TGeoVolume *absorber = new TGeoVolume("AbsorberVol", absorberShape, iron);
      absorber->SetLineColor(42); // brown / light red
      tShield->AddNode(
          absorber,
          1,
          new TGeoTranslation(0,
                              0,
                              z_end_of_proximity_shielding + absorber_half_length + absorber_offset));   // - Passive?
}
