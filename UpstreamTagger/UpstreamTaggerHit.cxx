#include "UpstreamTaggerHit.h"
#include "UpstreamTagger.h"
#include "TVector3.h"
#include "TMath.h"
#include "TRandom1.h"
#include "TRandom3.h"
#include "TGeoManager.h"
#include "TGeoBBox.h"
#include "TGeoNode.h"
#include "TRandom3.h"

#include <iostream>
#include <cmath>
#include <stdlib.h>     /* srand, rand */
#include <cstdlib>
#include <ctime>
#include <time.h>       /* time */

using std::cout;
using std::endl;

Double_t speedOfLight = TMath::C() *100./1000000000.0 ; // from m/sec to cm/ns

// -----   Default constructor   --------------
UpstreamTaggerHit::UpstreamTaggerHit()
  : ShipHit()
{
 flag = true;
}


// -----   constructor from TimeDetPoint from TimeDetHit-------------------------------
UpstreamTaggerHit::UpstreamTaggerHit(UpstreamTaggerPoint* p, UpstreamTagger* c, Double_t t0)
  : ShipHit()
{
}


// -----   Destructor   -------------------------
UpstreamTaggerHit::~UpstreamTaggerHit() { }

// ---- return time information for a given track extrapolation
std::vector<double>  UpstreamTaggerHit::GetTime(Double_t x){
}
// ---- return mean time information
std::vector<double>  UpstreamTaggerHit::GetTime(){
}

std::vector<double> UpstreamTaggerHit::GetMeasurements(){
}

// distance to edges
void UpstreamTaggerHit::Dist(Float_t x, Float_t& lpos, Float_t& lneg){
}
// ----------------------------------------------
TVector3 UpstreamTaggerHit::GetXYZ()
{
}


Double_t UpstreamTaggerHit::GetX()
{ TVector3 pos = GetXYZ();
  return pos.X();
}


Double_t UpstreamTaggerHit::GetY()
{ TVector3 pos = GetXYZ();
  return pos.Y();
}


Double_t UpstreamTaggerHit::GetZ()
{ TVector3 pos = GetXYZ();
  return pos.Z();
}


TGeoNode* UpstreamTaggerHit::GetNode(Double_t &hit_final, Int_t &mod)
{
}

// -----   Public method Print   -----------------------
void UpstreamTaggerHit::Print() const
{
  cout << "-I- UpstreamTaggerHit: UpstreamTagger hit " << " in detector " << fDetectorID << endl;
  cout << "  TDC left " << t_1 << " ns   TDC right " << t_2 << " ns" << endl;
}


// -----------------------------------------------------
