#include "muonHit.h"
#include "muonPoint.h"
#include "TVector3.h"
//
#include "TGeoManager.h"
#include "TGeoBBox.h"

#include <iostream>
#include <string>
#include <sstream>
#include <vector>

#include "TRandom3.h"

using std::cout;
using std::endl;

bool muonHit::onlyOnce=false;
const Double_t tileXdim = 10., tileYdim = 20.; // single tile dimension
const Double_t muonTimeResSigma = 0.5; // ns
static std::vector<Int_t> tileXn, tileYn; // n. of tile along X and Y dimension
static std::vector<Double_t> muStxMax;  // dX of the different stations
static std::vector<Double_t> muStyMax;  // dY of the different stations
static std::vector<Double_t> muStzMax;  // dZ of the different stations
static std::vector<Double_t> muStZpos;  // global Z coord in diff. stations

Double_t speedOfLight = TMath::C() *100./1000000000.0 ; // from m/sec to cm/ns
// -----   Default constructor   -------------------------------------------
muonHit::muonHit()
  : ShipHit()
{

}
// -----   Standard constructor   ------------------------------------------
muonHit::muonHit(Int_t detID, Float_t digi, Bool_t isV)
  : ShipHit(detID,digi) 
{
  //
  SetDigi(digi);
  setValidity(isV);
}
// -----   constructor from muonPoint   ------------------------------------------
muonHit::muonHit(muonPoint* p, Double_t t0)
  : ShipHit()
{
//
  TVector3 truePosition = TVector3( p->GetX(), p->GetY(),p->GetZ());
  fdigi = t0 + p->GetTime(); // + drift time,  propagation inside tile + tdc    
  SetDetectorID(DetIDfromXYZ(truePosition));
  SetDigi(SetMuonTimeRes(fdigi));
}
// ----
Int_t muonHit::DetIDfromXYZ(TVector3 p)
{  
    // needs some code to produce a unique detector ID
//
//                    tiles numbering example with present tile dimensions (X=10,Y=20cm):
//                                                            ---------------------------
//                                            muon station 1  |13540|13541...13598|13599|
//                                                           ---------------------------|
//                                           muon station 0  |03540|03541...03598|03599||
// How tiles numbering works:                                |03480|03481...03538|03539|.
// in each station tiles are numbered by rows starting       |                         ||
// from 0. Numbering begins at bottom of the station         ...........................|
// from left to right (looking the muon station from         |                         ||
// em calorimeter). At each tile is added the number         |00060|00061...00118|00119|
// n * 10ˆ4 where n is the station number (0 <= n <= 3).     |00000|00001...00058|00059|
//                                                           ---------------------------
// negative detID means ERROR.
//
    Int_t detID, nStat; // unique detector ID, station number
//
  if (!onlyOnce) {
    stInit();
    onlyOnce = true;
  }
    nStat = -1;
    for(Int_t i=0; i<muStZpos.size(); i++) {
     if (abs(p.Z() - muStZpos[i]) <= muStzMax[i]) { 
       nStat = i;
       break;
     }
    }
//
    if (nStat != -1) {
      detID=(Int_t)((p.X()+muStxMax[nStat])/tileXdim)+tileXn[nStat]
           *(Int_t)((p.Y()+muStyMax[nStat])/tileYdim)+10000*nStat;
    } else {
      detID = -1;
    }
//
    return detID;
}
// ----
TVector3 muonHit::XYZfromDetID(Int_t dID)
{
//
// The center of the tile XYZ coordinates are returned
//
// Negative Z coordinate means ERROR
//
    Int_t nStat; TVector3 p; // station number, center tile coordinate
//
  if (!onlyOnce) {
    stInit();
    onlyOnce = true;
  }
    nStat = -1;
    for(Int_t i=0; i<=muStZpos.size(); i++) {
      if (dID < 10000*i) { 
        nStat = i;
        break;
      }
    }
    if (nStat < 1) {// ERROR! dID too low (nStat=0) or too high (nStat=-1)
      p.SetXYZ(-999999,-999999,-999999);
      return p;
    }

//
    p.SetZ(muStZpos[--nStat]); // now must be 0 <= nstat <= (n. of stations - 1)
    dID -= 10000*(nStat);
//
    Int_t muXpos, muYpos;
    muXpos = tileXdim*((dID%tileXn[nStat])+0.5)-muStxMax[nStat];
    muYpos = tileYdim*((Int_t)(dID/tileXn[nStat])+0.5)-muStyMax[nStat];
    p.SetXYZ(muXpos, muYpos, muStZpos[nStat]);
//
    return p;
//
}
// ----
void muonHit::stInit()
{
//
//
    TGeoShape* muShape; TGeoBBox* muonBox;
    TGeoNavigator* nav = gGeoManager->GetCurrentNavigator();
    Double_t loc[3]={0,0,0}, global[3]={0,0,0};
//
    TString muDet = "cave/MuonDetector_1";
    nav->cd(muDet);
    TGeoNode* node = nav->GetCurrentNode();
    TObjArray* nodes =  node->GetVolume()->GetNodes();
//
    for (Int_t i = 0; i < nodes->GetEntries(); i++) {
      node = (TGeoNode*)nodes->At(i);
      Int_t muStNs = 0;
      if (TString(node->GetName()).Contains("muondet")) {
        nav->cd(muDet+"/"+node->GetName());
        TGeoVolume* volu = node->GetVolume();
        muShape = node->GetVolume()->GetShape();
        muonBox = (TGeoBBox*) muShape;
        muStxMax.push_back(muonBox->GetDX()); muStyMax.push_back(muonBox->GetDY()); 
        muStzMax.push_back(muonBox->GetDZ());
        nav->LocalToMaster(loc,global); muStZpos.push_back(global[2]);
        tileXn.push_back(2*muStxMax.at(muStNs)/tileXdim); 
        tileYn.push_back(2*muStyMax.at(muStNs)/tileYdim);
	muStNs++; // muon stations increment
      }
    }
}
// -------------------------------------------------------------------------
Double_t muonHit::SetMuonTimeRes(Double_t mcTime) {
//
  TRandom3 *rand = new TRandom3(0);
  Double_t cTime = rand->Gaus(mcTime,muonTimeResSigma);
  delete rand;
  return cTime;
}
void muonHit::Print() const {
//
  cout << "-I- muonHit: muon hit " << " in detector " << fDetectorID << endl;
  cout << "  TDC " << fdigi << " ns" << endl;

}
//
void muonHit::setValidity(Bool_t isV){hisV = isV;}
// -----   Destructor   ----------------------------------------------------
muonHit::~muonHit() { 
}
// -------------------------------------------------------------------------


ClassImp(muonHit)

