#include "ShipPixelHit.h"
#include "PixelModules.h"
// #include "PixelDetector.h"
#include "TVector3.h"
#include "TGeoBBox.h"
#include "TGeoNode.h"
#include "TGeoManager.h"
#include "TGeoShape.h"

#include <iostream>
#include <cmath>

// compute PixelPositionMap once


// -----   Standard constructor   ------------------------------------------
ShipPixelHit::ShipPixelHit(Int_t detID,  Float_t digi) : ShipHit(detID, digi) {
}

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

  pixelID.partitionID = partitionID; // DAQ partition, from 0-2
  pixelID.frontEndID = frontEndID; // Front end which was read out, from 0-7
  pixelID.moduleID = (8*partitionID + frontEndID)/2 ; // Id of actual DC module, from 0-11
  pixelID.row      = row; // row on front end / module
  pixelID.column   = column; // column on MODULE

  return pixelID;
}

int32_t ShipPixelHit::GetModule()
{
  HitID pixelID;
  pixelID = GetPixel();
  return pixelID.moduleID;
}

int32_t ShipPixelHit::GetDetectorID(){return fDetectorID; }

void ShipPixelHit::GetPixelXYZ(TVector3 &pixel, int detID) { //, std::shared_ptr <std::unordered_map<int, TVector3>> PixelPositionMap
  if (!ShipPixelHit::PixelPositionMap) {
    ShipPixelHit::PixelPositionMap = ShipPixelHit::MakePositionMap();
  }

  int max_detID = 10000000*2 + 1000000*7 + 1000*336 + 80 ;
  if (detID%1000000 == 0) {
    return;
  }
  if (detID > max_detID) {
    std::cout << "PixelDetector::PixelDecode, detectorID out of range "<<detID<<std::endl;
    return;
  }
  TVector3 pixel_pos = (*ShipPixelHit::PixelPositionMap)[detID];
  pixel.SetX(pixel_pos.X());
  pixel.SetY(pixel_pos.Y());
  pixel.SetZ(pixel_pos.Z());
}


std::shared_ptr <std::unordered_map<int, TVector3>>  ShipPixelHit::MakePositionMap() {
// map unique detectorID to x,y,z position in LOCAL coordinate system. xy (0,0) is on the bottom left of each Front End,
// the raw data counts columns from 1-80 from left to right and rows from 1-336 FROM TOP TO BOTTOM.

  const float mkm = 0.0001;

  const float  z0ref=  -1300.*mkm;
  const float  z1ref=   5200.*mkm;
  const float  z2ref=  24120.*mkm;
  const float  z3ref=  30900.*mkm;
  const float  z4ref=  51000.*mkm;
  const float  z5ref=  57900.*mkm;
  const float  z6ref=  77900.*mkm;
  const float  z7ref=  84600.*mkm;
  const float  z8ref= 104620.*mkm;
  const float  z9ref= 111700.*mkm;
  const float z10ref= 131620.*mkm;
  const float z11ref= 138500.*mkm;

  const float Zref[12]={z0ref, z1ref, z2ref, z3ref, z4ref, z5ref, z6ref, z7ref, z8ref, z9ref, z10ref, z11ref};

  const float  x0ref= (-16800. + 15396.)*mkm       +z0ref*0.0031;
  const float  x1ref= -2310.*mkm       +z1ref*0.0031;
  const float  x2ref=  6960.*mkm       +z2ref*0.0031;
  const float  x3ref=  6940.*mkm       +z3ref*0.0031;
  const float  x4ref= (-16800 + 15285.)*mkm        +z4ref*0.0031;
  const float  x5ref= -2430.*mkm       +z5ref*0.0031;
  const float  x6ref=  6620.*mkm       +z6ref*0.0031;
  const float  x7ref=  6710.*mkm       +z7ref*0.0031;
  const float  x8ref= (-16800 + 15440.)*mkm      +z8ref*0.0031;
  const float  x9ref= -2505.*mkm       +z9ref*0.0031;
  const float x10ref=  6455.*mkm      +z10ref*0.0031;
  const float x11ref=  6320.*mkm      +z11ref*0.0031;

  const float Xref[12] { x0ref, x1ref, x2ref, x3ref, x4ref, x5ref, x6ref, x7ref, x8ref, x9ref, x10ref, x11ref};

  const float  y0ref=   -15.*mkm       +z0ref*0.0068;
  const float  y1ref=    20.*mkm       +z1ref*0.0068;
  const float  y2ref= (-8400 + 7930.)*mkm       +z2ref*0.0068;
  const float  y3ref= (8400 - 8990.)*mkm       +z3ref*0.0068;
  const float  y4ref=  -370.*mkm       +z4ref*0.0068;
  const float  y5ref=  -610.*mkm       +z5ref*0.0068;
  const float  y6ref=  (-8400 + 7200.)*mkm       +z6ref*0.0068;
  const float  y7ref= (8400 - 9285.)*mkm       +z7ref*0.0068;
  const float  y8ref=  -700.*mkm       +z8ref*0.0068;
  const float  y9ref=  -690.*mkm       +z9ref*0.0068;
  const float y10ref=  (-8400 + 7660.)*mkm      +z10ref*0.0068;
  const float y11ref= (8400 - 8850.)*mkm      +z11ref*0.0068;

  const float Yref[12] { y0ref, y1ref, y2ref, y3ref, y4ref, y5ref, y6ref, y7ref, y8ref, y9ref, y10ref, y11ref};

  std::unordered_map<int, TVector3> positionMap;

  int map_index = 0;
  int moduleID = 0;
  float x,x_local,y, y_local;
  for (int partitionID=0; partitionID<3; partitionID++) {
    for (int frontEndID=0;frontEndID<8; frontEndID++ ) {
      for (int column=1; column<81; column++) {
        for (int row=1; row<337; row++) {
          map_index = 10000000*partitionID + 1000000*frontEndID + 1000*row + column;
          moduleID = (8*partitionID + frontEndID)/2;
          if (frontEndID%2==1) {
            // calculate LOCAL x position of hit
            x_local = -0.025 - (80 - column-1)*0.025;
            if (column == 80) x_local -= 0.0225;
          }
          else if (frontEndID%2==0) {
            x_local = 0.0225 + (column-1)*0.025;
            if (column == 80) x_local += 0.025;
          }
          // calculate LOCAL y position of hit
          y_local = 1.6775 - 0.0050*(row-1);
          // transform local to global coordinates
          if (frontEndID == 0){
            x = -y_local;
            y = x_local;
          }
          if (frontEndID == 1 ){
            x = -y_local;
            y = x_local;
          }
          if (frontEndID == 2 ){
            x = y_local;
            y = x_local;
          }
          if (frontEndID == 3 ) {
            x = y_local;
            y = x_local;
          }
          if (frontEndID == 4 ){
            x = -x_local;
            y = -y_local;
          }
          if (frontEndID == 5 ){
            x = -x_local;
            y = -y_local;
          }
          if (frontEndID == 6 ){
            x = -x_local;
            y = y_local;
          }
          if (frontEndID == 7 ){
            x = -x_local;
            y = y_local;
          }
          positionMap[map_index].SetX(x - Xref[moduleID]);
          positionMap[map_index].SetY(y - Yref[moduleID]);
          positionMap[map_index].SetZ(Zref[moduleID]);
        }
      }
    }
  }
  return std::make_shared<std::unordered_map<int, TVector3>>(positionMap);
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
