#include "strawtubesHit.h"

#include "FairLogger.h"
#include "FairRun.h"
#include "FairRunSim.h"
#include "TGeoManager.h"
#include "TGeoShape.h"
#include "TGeoTube.h"
#include "TMath.h"
#include "TRandom1.h"
#include "TRandom3.h"
#include "TVector3.h"
#include "strawtubes.h"

#include <iostream>
#include <math.h>
#include <tuple>
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
    TVector3 stop = TVector3();
    fDetectorID = p->GetDetectorID();
    strawtubes* module =
        dynamic_cast<strawtubes*>(FairRunSim::Instance()->GetListOfModules()->FindObject("Strawtubes"));
    Double_t v_drift = module->StrawVdrift();
    Double_t sigma_spatial = module->StrawSigmaSpatial();
    strawtubes::StrawEndPoints(fDetectorID, start, stop);
    Double_t t_drift = fabs(gRandom->Gaus(p->dist2Wire(), sigma_spatial)) / v_drift;
    fdigi = t0 + p->GetTime() + t_drift + (stop[0] - p->GetX()) / speedOfLight;
    flag = true;
}

// -------------------------------------------------------------------------

// -----   Destructor   ----------------------------------------------------
strawtubesHit::~strawtubesHit() { }
// -------------------------------------------------------------------------

Int_t strawtubesHit::GetStationNumber()
{
    Int_t detID = GetDetectorID();
    const auto decode = strawtubes::StrawDecode(detID);

    return std::get<0>(decode);
}

Int_t strawtubesHit::GetViewNumber()
{
    Int_t detID = GetDetectorID();
    const auto decode = strawtubes::StrawDecode(detID);

    return std::get<1>(decode);
}

Int_t strawtubesHit::GetLayerNumber()
{
    Int_t detID = GetDetectorID();
    const auto decode = strawtubes::StrawDecode(detID);

    return std::get<2>(decode);
}

Int_t strawtubesHit::GetStrawNumber()
{
    Int_t detID = GetDetectorID();
    const auto decode = strawtubes::StrawDecode(detID);

    return std::get<3>(decode);
}

// -----   Public method Print   -------------------------------------------
void strawtubesHit::Print() const
{
  cout << "-I- strawtubesHit: strawtubes hit " << " in detector " << fDetectorID << endl;
  cout << "  TDC " << fdigi << " ns" << endl;
}
// -------------------------------------------------------------------------
