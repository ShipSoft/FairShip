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
    : ShipHit(detID, digi), detectorID(detID), ToT(digi*25){}


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

void ShipPixelHit::MakePositionMap(std::map<int, TVector3> positionMap) {
  const float mkm = 0.0001;
  float  z0ref=  -1300.*mkm;
  float  z1ref=   5200.*mkm;
  float  z2ref=  24120.*mkm;
  float  z3ref=  30900.*mkm;
  float  z4ref=  51000.*mkm;
  float  z5ref=  57900.*mkm;
  float  z6ref=  77900.*mkm;
  float  z7ref=  84600.*mkm;
  float  z8ref= 104620.*mkm;
  float  z9ref= 111700.*mkm;
  float z10ref= 131620.*mkm;
  float z11ref= 138500.*mkm;

  float Zref[12]={z0ref, z1ref, z2ref, z3ref, z4ref, z5ref, z6ref, z7ref, z8ref, z9ref, z10ref, z11ref};

  int map_index=0;
  for (int partID=0; partID<3; partID++) {
    for (int moduleID=0;moduleID<8; moduleID++ ) {
      for (int column=1; column<81; column++) {
        for (int row=1; row<337; row++) {
          map_index = 10000000*partID + 1000000*moduleID + 1000*row + column;
          positionMap[map_index].SetX(0.025 + (column-1)*0.025);
          if (column == 80) positionMap[map_index].SetX(0.025 + (column-2)*0.025 + 0.0225);
          positionMap[map_index].SetY(0.0050*(row-1) + 0.0025);
          positionMap[map_index].SetZ(Zref[(moduleID + 1)/2 * (partID+1)]);
        }
      }
    }
  }
}

void ShipPixelHit::EndPoints(TVector3 &pixel, int detID, std::map<int, TVector3> &positionMap {

  int max_detID = 10000000*2 + 1000000*8 + 1000*336 + 160 ;
  if (detID > max_detID) {
    std::cout << "PixelDetector::PixelDecode, TGeoNavigator failed "<<path<<std::endl;
    return;
  }
  pixel_pos = positionMap[detID]
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
  std::cout << "  ToT " << ToT*25 << " ns" << std::endl; //Time over threshold in nanoseconds
}
// -------------------------------------------------------------------------


 ClassImp(ShipPixelHit)
