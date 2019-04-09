#include "TimeDetHit.h"
#include "TimeDet.h"
#include "TVector3.h"
#include "TMath.h"
#include "TRandom1.h"
#include "TRandom3.h"
#include "TGeoManager.h"
#include "TGeoBBox.h"
#include "TGeoNode.h"

#include <iostream>
#include <cmath>

using std::cout;
using std::endl;

Double_t speedOfLight = TMath::C() *100./1000000000.0 ; // from m/sec to cm/ns


// -----   Default constructor   --------------
TimeDetHit::TimeDetHit()
  : ShipHit()
{
 flag = true;
}


// -----   constructor from TimeDetPoint from TimeDetHit-------------------------------
TimeDetHit::TimeDetHit(TimeDetPoint* p, Double_t t0)
  : ShipHit()
{
     fDetectorID = p->GetDetectorID();
     Float_t lpos, lneg;
     Dist(p->GetX(), lpos, lneg);
     Double_t sigma = Resol(lneg); // in ns
     t_1 = gRandom->Gaus( 0, sigma ) + lneg/v_drift + t0 + p->GetTime();
     sigma = Resol(lpos); // in ns
     t_2 = gRandom->Gaus( 0, sigma ) + lpos/v_drift + t0 + p->GetTime();
     flag = true;
}


// -----   Destructor   -------------------------
TimeDetHit::~TimeDetHit() { }

// ---- return time information for a given track extrapolation
std::vector<double>  TimeDetHit::GetTime(Double_t x){
     // calculate distance to left and right end
     Float_t lpos, lneg;
     Dist(x, lpos, lneg);
     Double_t r = Resol(lneg);
     Double_t w1 = 1./(r*r);
     r = Resol(lpos);
     Double_t w2 = 1./(r*r);
     Double_t dt = 1./TMath::Sqrt(w1+w2);
     Double_t t  =  ( (t_1-lneg/v_drift)*w1+(t_2-lpos/v_drift)*w2 )/(w1+w2);
     std::vector<double> m;
     m.push_back(t);
     m.push_back(dt);
     return m;
}
// ---- return mean time information
std::vector<double>  TimeDetHit::GetTime(){
     TGeoBBox* shape =  (TGeoBBox*)gGeoManager->GetVolume("TimeDet")->GetShape();
     Double_t t0  =  (t_1+t_2)/2.-shape->GetDX()/v_drift;
     Float_t lpos, lneg;
     lneg = (t_1-t0)*v_drift;
     lpos = (t_2-t0)*v_drift;
     Float_t r1 = Resol(lneg);
     Float_t r2 = Resol(lpos);
     Double_t dt =  TMath::Sqrt(r1*r1+r2*r2);
     std::vector<double> m;
     m.push_back(t0);
     m.push_back(dt);
     return m;
}
// -----   resolution function-------------------
Double_t TimeDetHit::Resol(Double_t x)
{
  return par[0]*TMath::Exp( (x-par[2])/par[1] )+par[3]; 
}

std::vector<double> TimeDetHit::GetMeasurements(){
 std::vector<double> m;
 m.push_back( t_1);
 m.push_back( t_2);
 return m;
}

// distance to edges
void TimeDetHit::Dist(Float_t x, Float_t& lpos, Float_t& lneg){
     TGeoNode* node  = GetNode();
     auto shape =  dynamic_cast<TGeoBBox*>(node->GetVolume()->GetShape());
     TVector3 pos    = GetXYZ();
     lpos = TMath::Abs( pos.X() + shape->GetDX() - x );
     lneg = TMath::Abs( pos.X() - shape->GetDX() - x );
}
// ----------------------------------------------
TVector3 TimeDetHit::GetXYZ()
{
    TGeoNavigator* nav = gGeoManager->GetCurrentNavigator();
    TGeoNode* node = GetNode();
    auto shape =  dynamic_cast<TGeoBBox*>(node->GetVolume()->GetShape());
    Double_t origin[3] = {shape->GetOrigin()[0],shape->GetOrigin()[1],shape->GetOrigin()[2]};
    Double_t master[3] = {0,0,0};
    nav->LocalToMaster(origin,master);
    TVector3 pos = TVector3(master[0],master[1],master[2]);
    return pos;
}


Double_t TimeDetHit::GetX()
{ TVector3 pos = GetXYZ();
  return pos.X();
}


Double_t TimeDetHit::GetY()
{ TVector3 pos = GetXYZ();
  return pos.Y();
}


Double_t TimeDetHit::GetZ()
{ TVector3 pos = GetXYZ();
  return pos.Z();
}


TGeoNode* TimeDetHit::GetNode()
{
   TGeoNavigator* nav = gGeoManager->GetCurrentNavigator();
   TString path = "/Timing Detector_1/TimeDet_";path+=fDetectorID;
   Bool_t rc = nav->cd(path);
   return nav->GetCurrentNode();
} 


// -----   Public method Print   -----------------------
void TimeDetHit::Print() const
{ 
  cout << "-I- TimeDetHit: TimeDet hit " << " in detector " << fDetectorID << endl;
  cout << "  TDC left " << t_1 << " ns   TDC right " << t_2 << " ns" << endl;
}


// -----------------------------------------------------
ClassImp(TimeDetHit)

