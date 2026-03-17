// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#include "splitcalHit.h"

#include <cmath>
#include <iostream>

#include "FairLogger.h"
#include "FairRun.h"
#include "FairRunSim.h"
#include "TGeoBBox.h"
#include "TGeoManager.h"
#include "TGeoMatrix.h"
#include "TGeoNavigator.h"
#include "TGeoNode.h"
#include "TGeoShape.h"
#include "TGeoVolume.h"
#include "TMath.h"
#include "TRandom1.h"
#include "TRandom3.h"
#include "TVector3.h"
#include "splitcal.h"
#include "splitcalPoint.h"
using std::cout;
using std::endl;

namespace {
constexpr Double_t speedOfLight = 29.9792458;  // TMath::C() * 100 / 1e9, cm/ns
}  // namespace
// -----   Default constructor   -------------------------------------------
splitcalHit::splitcalHit() : SHiP::DetectorHit() {}
// -----   Standard constructor   ------------------------------------------
splitcalHit::splitcalHit(Int_t detID, Float_t tdc)
    : SHiP::DetectorHit(detID, tdc) {}
// -----   constructor from vector of splitcalPoints
// ------------------------------------------
splitcalHit::splitcalHit(const std::vector<splitcalPoint>& points, Double_t t0)
    : SHiP::DetectorHit() {
  // Empty vector check
  if (points.empty()) {
    LOG(error)
        << "splitcalHit constructor called with empty splitcalPoint vector";
    return;
  }

  // Use first point for geometry lookup and detector ID
  const auto& firstPoint = points[0];
  double pointX = firstPoint.GetX();
  double pointY = firstPoint.GetY();
  int detID = firstPoint.GetDetectorID();

  // Sum energy from all points
  double pointE = 0.0;
  for (const auto& point : points) {
    pointE += point.GetEnergyLoss();
  }

  fdigi = t0 + firstPoint.GetTime();
  SetDetectorID(detID);

  TGeoNavigator* navigator = gGeoManager->GetCurrentNavigator();
  navigator->cd("cave/SplitCalDetector_1");
  TGeoVolume* caloVolume = navigator->GetCurrentVolume();
  // caloVolume->PrintNodes();

  std::string stripName = GetDetectorElementName(
      detID);  // it also sets if strip gives x or y coordinate

  int isPrec, nL, nMx, nMy, nS;
  Decoder(detID, isPrec, nL, nMx, nMy, nS);

  SetIDs(isPrec, nL, nMx, nMy, nS);

  TGeoNode* strip = caloVolume->GetNode(stripName.c_str());

  const Double_t* stripCoordinatesLocal = strip->GetMatrix()->GetTranslation();
  Double_t stripCoordinatesMaster[3] = {0., 0., 0.};
  navigator->LocalToMaster(stripCoordinatesLocal, stripCoordinatesMaster);

  TGeoBBox* box = dynamic_cast<TGeoBBox*>(strip->GetVolume()->GetShape());
  double xHalfLength = box->GetDX();
  double yHalfLength = box->GetDY();
  double zHalfLength = box->GetDZ();

  double zPassiveHalfLength = box->GetDZ();

  SetEnergy(pointE);
  if (isPrec == 1)
    SetXYZ(pointX, pointY, stripCoordinatesMaster[2]);
  else
    SetXYZ(stripCoordinatesMaster[0], stripCoordinatesMaster[1],
           stripCoordinatesMaster[2]);
  SetXYZErrors(xHalfLength, yHalfLength,
               2 * (zHalfLength + zPassiveHalfLength));
}

std::string splitcalHit::GetPaddedString(int id) {
  // zero padded string
  int totalLength = 9;
  std::string stringID = std::to_string(id);
  std::string encodedID =
      std::string(totalLength - stringID.length(), '0') + stringID;

  return encodedID;
}

std::string splitcalHit::GetDetectorElementName(int id) {
  std::string encodedID = GetPaddedString(id);
  int isPrec, nL, nMx, nMy, nS;
  Decoder(encodedID, isPrec, nL, nMx, nMy, nS);

  std::string name;
  if (isPrec == 1) {
    name = "ECALdet_gas_";
    SetIsX(true);
    SetIsY(true);
  } else if (nL % 2 == 0) {
    name = "stripGivingY_";
    SetIsX(false);
    SetIsY(true);
  } else {
    name = "stripGivingX_";
    SetIsX(true);
    SetIsY(false);
  }
  name = name + std::to_string(id);

  return name;
}

void splitcalHit::Decoder(const std::string& encodedID, int& isPrecision,
                          int& nLayer, int& nModuleX, int& nModuleY,
                          int& nStrip) {
  std::string substring;

  substring = encodedID.substr(0, 1);
  isPrecision = atoi(substring.c_str());

  substring = encodedID.substr(1, 3);
  nLayer = atoi(substring.c_str());

  substring = encodedID.substr(4, 1);
  nModuleX = atoi(substring.c_str());

  substring = encodedID.substr(5, 1);
  nModuleY = atoi(substring.c_str());

  substring = encodedID.substr(6, 3);
  nStrip = atoi(substring.c_str());
}

void splitcalHit::Decoder(int id, int& isPrecision, int& nLayer, int& nModuleX,
                          int& nModuleY, int& nStrip) {
  std::string encodedID = GetPaddedString(id);
  Decoder(encodedID, isPrecision, nLayer, nModuleX, nModuleY, nStrip);
}

// -------------------------------------------------------------------------

// -----   Public method Print   -------------------------------------------
void splitcalHit::Print() const {
  //  cout << "-I- splitcalHit: splitcal hit " << " in detector " << fDetectorID
  //  << endl; cout << "  TDC " << fdigi << " ns" << endl;
  // std::cout<< "-I- splitcalHit: " <<std::endl;
  std::cout << "------- " << std::endl;
  std::cout << "    (x,y,z) = " << _x << " +- " << _xError << " ,  " << _y
            << " +- " << _yError << " ,  " << _z << " +- " << _zError
            << std::endl;
  std::cout << "    isP, nL, nMx, nMy, nS = " << _isPrecisionLayer << " , "
            << _nLayer << " , " << _nModuleX << " , " << _nModuleY << " , "
            << _nStrip << std::endl;
  std::cout << "------- " << std::endl;
}
// -------------------------------------------------------------------------
