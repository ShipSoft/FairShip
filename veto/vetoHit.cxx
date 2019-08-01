#include "vetoHit.h"
#include "veto.h"
#include "TVector3.h"
#include "FairRun.h"
#include "FairRunSim.h"
#include "TMath.h"
#include "TRandom1.h"
#include "TRandom3.h"
#include "TGeoManager.h"
#include "TGeoArb8.h"

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
 ft = -1;
 flag = true;
}

// -------------------------------------------------------------------------

// -----   Destructor   ----------------------------------------------------
vetoHit::~vetoHit() { }
// -------------------------------------------------------------------------

TVector3 vetoHit::GetXYZ()
{
    TGeoNavigator* nav = gGeoManager->GetCurrentNavigator();
    TGeoNode* node = GetNode();
    TGeoBBox* shape =  (TGeoBBox*)node->GetVolume()->GetShape();
    Double_t origin[3] = {shape->GetOrigin()[0],shape->GetOrigin()[1],shape->GetOrigin()[2]};
    Double_t master[3] = {0,0,0};
    
    Int_t i;
    const Double_t *tr = node->GetMatrix()->GetTranslation();
    if (!(node->GetMatrix()->IsRotation())) {
       for (i=0; i<3; i++) master[i] = tr[i] + origin[i];
    }
    else{
        const Double_t *rot = node->GetMatrix()->GetRotationMatrix();
        for (i=0; i<3; i++) {
        master[i] = tr[i]
                    + origin[0]*rot[3*i]
                    + origin[1]*rot[3*i+1]
                    + origin[2]*rot[3*i+2];
        }
    }
    
    //nav->LocalToMaster(origin,master);
    TVector3 pos = TVector3(master[0],master[1],master[2]);
    return pos;
} 
Double_t vetoHit::GetX()
{ TVector3 pos = GetXYZ();
  return pos.X();
}
Double_t vetoHit::GetY()
{ TVector3 pos = GetXYZ();
  return pos.Y();
}
Double_t vetoHit::GetZ()
{ TVector3 pos = GetXYZ();
  return pos.Z();
}
TGeoNode* vetoHit::GetNode()
{
   TGeoNode* node;
   TGeoNavigator* nav = gGeoManager->GetCurrentNavigator();
   TString path = "/DecayVolume_1";
   TString seq="VetoLiSc";
   TGeoVolume* assembly = gGeoManager->FindVolumeFast(seq);
   node = assembly->GetNode(fDetectorID);
   return node;
} 

// -----   Public method Print   -------------------------------------------
void vetoHit::Print(Int_t detID) const
{ 
  cout << "-I- vetoHit: veto hit " << " in detector " << fDetectorID << endl;
  cout << "  ADC " << fdigi << " ns" << endl;
}

// -------------------------------------------------------------------------

ClassImp(vetoHit)

