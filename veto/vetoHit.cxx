#include "vetoHit.h"
#include "veto.h"
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
vetoHit::vetoHit()
  : ShipHit()
{
 flag = true;
}
// -----   Standard constructor   ------------------------------------------
vetoHit::vetoHit(Int_t detID, Float_t adc)
  : ShipHit(detID,adc)
{
 flag = true;
}
// -----   constructor from vetoPoint   ------------------------------------------
vetoHit::vetoHit(vetoPoint* p, Double_t t0)
  : ShipHit()
{
    flag = true;
}
// -------------------------------------------------------------------------

// -----   Destructor   ----------------------------------------------------
vetoHit::~vetoHit() { }
// -------------------------------------------------------------------------

// -----   Public method Print   -------------------------------------------
void vetoHit::Print(Int_t detID) const
{
  cout << "-I- vetoHit: veto hit " << " in detector " << fDetectorID << endl;
  cout << "  ADC " << fdigi << " ns" << endl;
}
// -------------------------------------------------------------------------

ClassImp(vetoHit)

