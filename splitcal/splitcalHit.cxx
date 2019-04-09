#include "splitcalHit.h"
#include "splitcal.h"
#include "TVector3.h"
#include "FairRun.h"
#include "FairRunSim.h"
#include "TMath.h"
#include "TRandom1.h"
#include "TRandom3.h"
#include "TGeoManager.h"
#include "TGeoNode.h"
#include "TGeoMatrix.h"
#include "TGeoVolume.h"
#include "TGeoNavigator.h"
#include "TGeoShape.h"
#include "TGeoBBox.h"

#include <iostream>
#include <math.h>
using std::cout;
using std::endl;

Double_t speedOfLight = TMath::C() *100./1000000000.0 ; // from m/sec to cm/ns
// -----   Default constructor   -------------------------------------------
splitcalHit::splitcalHit()
  : ShipHit()
{
 flag = true;
}
// -----   Standard constructor   ------------------------------------------
splitcalHit::splitcalHit(Int_t detID, Float_t tdc)
  : ShipHit(detID,tdc)
{
 flag = true;
}
// -----   constructor from splitcalPoint   ------------------------------------------
splitcalHit::splitcalHit(splitcalPoint* p, Double_t t0)
  : ShipHit()
{

  flag = true;

  double pointX =  p->GetX();
  double pointY =  p->GetY();
  double pointZ =  p->GetZ();
  double pointT =  p->GetTime();
  double pointE =  p->GetEnergyLoss();
  int detID =  p->GetDetectorID();

  //fdigi = t0 + t; 
  fdigi = t0 ;  
  // SetDigi(SetTimeRes(fdigi));
  SetDetectorID(detID);

  TGeoNavigator* navigator = gGeoManager->GetCurrentNavigator();
  navigator->cd("cave/SplitCalDetector_1");
  TGeoVolume* caloVolume = navigator->GetCurrentVolume();
  // caloVolume->PrintNodes();

  std::string stripName = GetDetectorElementName(detID); // it also sets if strip gives x or y coordinate

  int isPrec, nL, nMx, nMy, nS;
  Decoder(detID, isPrec, nL, nMx, nMy, nS);

  SetIDs(isPrec, nL, nMx, nMy, nS);

  TGeoNode* strip = caloVolume->GetNode(stripName.c_str()); 

  const Double_t* stripCoordinatesLocal = strip->GetMatrix()->GetTranslation();
  Double_t stripCoordinatesMaster[3] = {0.,0.,0.};
  navigator->LocalToMaster(stripCoordinatesLocal, stripCoordinatesMaster);

  TGeoBBox* box = (TGeoBBox*)strip->GetVolume()->GetShape();
  double xHalfLength = box->GetDX();
  double yHalfLength = box->GetDY();
  double zHalfLength = box->GetDZ();
  
  TGeoNode* passiveLayer = caloVolume->GetNode("ECALfilter_200000"); // they are all the same
  TGeoBBox* boxPassive = (TGeoBBox*)passiveLayer->GetVolume()->GetShape();
  double zPassiveHalfLength = box->GetDZ();

  // std::cout<< "----------------------"<<std::endl;
  // std::cout<< "-- pointX = " << pointX << std::endl; 
  // std::cout<< "-- pointY = " << pointY << std::endl; 
  // std::cout<< "-- pointZ = " << pointZ << std::endl; 
  // std::cout<< "-- detID = " << detID << std::endl;
  // std::cout<< "-- stripName = " << stripName << std::endl;
  // std::cout<< "-- isPrec = " << isPrec << std::endl;
  // std::cout<< "-- nL = " << nL << std::endl;
  // std::cout<< "-- nMx = " << nMx << std::endl;
  // std::cout<< "-- nMy = " << nMy << std::endl;
  // std::cout<< "-- nS = " << nS << std::endl;    
  // std::cout<< "-- stripCoordinatesLocal[0] = " << stripCoordinatesLocal[0] << std::endl;
  // std::cout<< "-- stripCoordinatesLocal[1] = " << stripCoordinatesLocal[1] << std::endl;
  // std::cout<< "-- stripCoordinatesLocal[2] = " << stripCoordinatesLocal[2] << std::endl;
  // std::cout<< "-- stripCoordinatesMaster[0] = " << stripCoordinatesMaster[0] << std::endl;
  // std::cout<< "-- stripCoordinatesMaster[1] = " << stripCoordinatesMaster[1] << std::endl;
  // std::cout<< "-- stripCoordinatesMaster[2] = " << stripCoordinatesMaster[2] << std::endl;


  // TGeoNode* check = navigator->FindNode(pointX,pointY,pointZ);

  SetEnergy(pointE);
  if (isPrec==1) SetXYZ(pointX,pointY,stripCoordinatesMaster[2]);
  else  SetXYZ(stripCoordinatesMaster[0], stripCoordinatesMaster[1], stripCoordinatesMaster[2]);
  SetXYZErrors(xHalfLength,yHalfLength,2*(zHalfLength+zPassiveHalfLength));
  

}



std::string splitcalHit::GetPaddedString(int& id){ 

  //zero padded string 
  int totalLength = 9; 
  std::string stringID = std::to_string(id);
  std::string encodedID = std::string(totalLength - stringID.length(), '0') + stringID;
 
 return encodedID;

}

std::string splitcalHit::GetDetectorElementName(int& id){

  std::string encodedID = GetPaddedString(id);
  //std::cout << "-- encodedID = " << encodedID <<std::endl;
  int isPrec, nL, nMx, nMy, nS;
  Decoder(encodedID, isPrec, nL, nMx, nMy, nS);

  std::string name;
  if (isPrec==1) {
    name = "ECALdet_gas_";
    SetIsX(true);
    SetIsY(true);
  } else if (nL%2==0) {
    name = "stripGivingY_"; 
    SetIsX(false);
    SetIsY(true);
  } else {
    name = "stripGivingX_";
    SetIsX(true);
    SetIsY(false);
  }
  name = name + std::to_string(id);
  // std::cout << "--GetDetectorElementName - name  = " << name <<std::endl;

  return name;

}

void splitcalHit::Decoder(std::string& encodedID, int& isPrecision, int& nLayer, int& nModuleX,  int& nModuleY, int& nStrip){

  std::string subtring;

  subtring = encodedID.substr(0, 1);
  isPrecision = atoi(subtring.c_str());

  subtring = encodedID.substr(1,3);
  nLayer = atoi(subtring.c_str());

  subtring = encodedID.substr(4,1); 
  nModuleX = atoi(subtring.c_str());

  subtring = encodedID.substr(5,1); 
  nModuleY = atoi(subtring.c_str());

  subtring = encodedID.substr(6,3);
  nStrip = atoi(subtring.c_str());

}

void splitcalHit::Decoder(int& id, int& isPrecision, int& nLayer, int& nModuleX,  int& nModuleY, int& nStrip){

  std::string encodedID = GetPaddedString(id);
  Decoder(encodedID, isPrecision, nLayer, nModuleX, nModuleY, nStrip);

}


double splitcalHit::GetEnergyWeightForIndex(int index){

  int iw = 0;
  for(size_t i=0; i<_vecClusterIndices.size(); i++) {
    if (_vecClusterIndices.at(i) == index) {
      iw = i;
      break; 
    }
  }
  return _vecEnergyWeights.at(iw); 
}


double splitcalHit::GetEnergyForCluster(int i){

  double unweightedEnergy = GetEnergy();
  double weight = GetEnergyWeightForIndex(i);
  double energy = unweightedEnergy*weight;
  return energy;

}

// -------------------------------------------------------------------------

// -----   Destructor   ----------------------------------------------------
splitcalHit::~splitcalHit() { }
// -------------------------------------------------------------------------

// -----   Public method Print   -------------------------------------------
void splitcalHit::Print() const
{
  //  cout << "-I- splitcalHit: splitcal hit " << " in detector " << fDetectorID << endl;
  //  cout << "  TDC " << fdigi << " ns" << endl;
  // std::cout<< "-I- splitcalHit: " <<std::endl;
  std::cout<< "------- " <<std::endl;
  std::cout<< "    (x,y,z) = " 
	   << _x << " +- " << _xError << " ,  "
	   << _y << " +- " << _yError << " ,  "
	   << _z << " +- " << _zError <<std::endl;  
  std::cout<< "    isP, nL, nMx, nMy, nS = " 
	   << _isPrecisionLayer << " , "  
	   << _nLayer << " , "  
	   << _nModuleX << " , " 
	   << _nModuleY << " , " 
	   << _nStrip << std::endl;
   std::cout<< "------- " <<std::endl;
}
// -------------------------------------------------------------------------

ClassImp(splitcalHit)

