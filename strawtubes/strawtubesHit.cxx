#include "strawtubesHit.h"
#include "strawtubes.h"
#include "TVector3.h"
#include "FairRun.h"
#include "FairRunSim.h"
#include "TMath.h"
#include "TRandom1.h"
#include "TRandom3.h"

#include <iostream>
#include <math.h>
using std::cout;
using std::endl;

Double_t speedOfLight = TMath::C() *100./1000000000.0 ; // from m/sec to cm/ns
// -----   Default constructor   -------------------------------------------
strawtubesHit::strawtubesHit()
  : ShipHit()
{
 flag = true;
}
// -----   Standard constructor   ------------------------------------------
strawtubesHit::strawtubesHit(Int_t detID, Float_t tdc)
  : ShipHit(detID,tdc)
{
 flag = true;
}
// -----   constructor from strawtubesPoint   ------------------------------------------
strawtubesHit::strawtubesHit(strawtubesPoint* p, Double_t t0)
  : ShipHit()
{
     TVector3 start = TVector3();
     TVector3 stop  = TVector3();
     fDetectorID = p->GetDetectorID();
     strawtubes* module = dynamic_cast<strawtubes*> (FairRunSim::Instance()->GetListOfModules()->FindObject("Strawtubes") );
     Double_t v_drift       = module->StrawVdrift();
     Double_t sigma_spatial = module->StrawSigmaSpatial();
     module->StrawEndPoints(fDetectorID,start,stop);
     Double_t t_drift = fabs( gRandom->Gaus( p->dist2Wire(), sigma_spatial ) )/v_drift;
     fdigi = t0 + p->GetTime() + t_drift + ( stop[0]-p->GetX() )/ speedOfLight;
     flag = true;
}
// -------------------------------------------------------------------------

// -----   Destructor   ----------------------------------------------------
strawtubesHit::~strawtubesHit() { }
// -------------------------------------------------------------------------

// -----   Public method Print   -------------------------------------------
void strawtubesHit::Print(Int_t detID) const
{
  cout << "-I- strawtubesHit: strawtubes hit " << " in detector " << fDetectorID << endl;
  cout << "  TDC " << fdigi << " ns" << endl;
}
// -------------------------------------------------------------------------

ClassImp(strawtubesHit)

