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
ShipPixelHit::ShipPixelHit(int32_t detID,  uint16_t tot) : ShipHit(detID, tot) {}


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

void ShipPixelHit::PixelCenter(TVector3 &pixel)
{
  HitID hitPixelID;
  hitPixelID = GetPixel();
  // build node path for Geant4 geometry
  TGeoNavigator* nav = gGeoManager->GetCurrentNavigator();
  TString module = "volPixelModule_";
          module += hitPixelID.moduleID;
  TString col = "col_";
          col += hitPixelID.column;
  TString row = "row_";
          row += hitPixelID.row;
  TString path ="/";
          path += module;
          path +="/";
          path +=col;
          path +="/";
          path +=row;

  Bool_t rc = nav->cd(path);
  if (not rc)
  {
    std::cout << "PixelDetector::PixelDecode, TGeoNavigator failed "<<path<<std::endl;
    return;
  }
  // get pixel position and write to vector
  TGeoNode* W = nav->GetCurrentNode();
  TGeoBBox* S = dynamic_cast<TGeoBBox*>(W->GetVolume()->GetShape());
  Double_t center[3] = {0,0,S->GetDZ()};
  Double_t Gcenter[3];
  nav->LocalToMaster(center, Gcenter);
  pixel.SetXYZ(Gcenter[0],Gcenter[1],Gcenter[2]);
}

// -----   Destructor   ----------------------------------------------------
// ShipPixelHit::~ShipPixelHit() = default;
// -------------------------------------------------------------------------


// -----   Public method Print   -------------------------------------------
void ShipPixelHit::Print() const
{
  std::cout << "-I- PixelHit: Pixel hit " << " in detector " << fDetectorID << std::endl;
  std::cout << "  ToT " << tot*25 << " ns" << std::endl; //Time over threshold in nanoseconds
}
// -------------------------------------------------------------------------


 ClassImp(ShipPixelHit)
