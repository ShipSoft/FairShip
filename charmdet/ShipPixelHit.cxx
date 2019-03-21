#include "ShipPixelHit.h"
// #include "PixelDetector.h"
#include "TVector3.h"
#include "TGeoBBox.h"
#include "TGeoNode.h"
#include "TGeoManager.h"
#include "TGeoShape.h"

#include <iostream>
#include <cmath>

// -----   Standard constructor   ------------------------------------------
ShipPixelHit::ShipPixelHit(Int_t detID,  Float_t digi)
    : ShipHit(detID, digi) {}


HitID ShipPixelHit::GetPixel()
{
  int32_t partitionID, frontEndID, row, column;
  HitID pixelID;
  partitionID = fDetectorID/10000000;
  frontEndID = (fDetectorID - partitionID*10000000)/1000000;
  row = (fDetectorID - partitionID*10000000 - frontEndID*1000000)/1000;
  column = (fDetectorID - partitionID*10000000 - frontEndID*1000000 - row*1000);
  // stitch together 2 Front ends to one module
  if ((frontEndID%2)==0) column += 80;

  pixelID.partitionID = partitionID;
  pixelID.frontEndID = frontEndID;
  pixelID.moduleID = (partitionID*frontEndID)/2;
  pixelID.row      = row;
  pixelID.column   = column;

  return pixelID;
}

int32_t ShipPixelHit::GetModule()
{
  HitID pixelID;
  pixelID = GetPixel();
  return pixelID.moduleID;
}

int32_t ShipPixelHit::GetDetectorID(){return fDetectorID; }

void ShipPixelHit::EndPoints(TVector3 &pixel, int detID, std::unordered_map<int, TVector3> &positionMap) {

  int max_detID = 10000000*2 + 1000000*8 + 1000*336 + 160 ;
  if (detID > max_detID) {
    std::cout << "PixelDetector::PixelDecode, detectorID out of range "<<detID<<std::endl;
    return;
  }
  TVector3 pixel_pos = positionMap[detID];
  pixel.SetX(pixel_pos.X());
  pixel.SetY(pixel_pos.Y());
  pixel.SetZ(pixel_pos.Z());
}

// -----   Destructor   ----------------------------------------------------
// ShipPixelHit::~ShipPixelHit() = default;
// -------------------------------------------------------------------------


// -----   Public method Print   -------------------------------------------
void ShipPixelHit::Print()
{
  std::cout << "-I- PixelHit: Pixel hit " << " in module " << GetModule() << std::endl;
  std::cout << "  ToT " << fdigi*25 << " ns" << std::endl; //Time over threshold in nanoseconds
}
// -------------------------------------------------------------------------


 ClassImp(ShipPixelHit)
