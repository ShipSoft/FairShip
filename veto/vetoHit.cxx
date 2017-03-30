#include "vetoHit.h"
#include "veto.h"
#include "TVector3.h"
#include "FairRun.h"
#include "FairRunSim.h"
#include "TMath.h"
#include "TRandom1.h"
#include "TRandom3.h"
#include "TGeoManager.h"

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
    Int_t iseq   = fDetectorID/100000;
    Int_t corner = (fDetectorID-100000*iseq)/10000;
    Int_t key    = fDetectorID%10000;
    TString seq="T";
    if (corner==1){  seq+=iseq; seq+="LiScC";}
    else          {  seq+=iseq; seq+="LiSc";}
    TGeoVolume* assembly = gGeoManager->FindVolumeFast(seq);
    TGeoNode* node = assembly->GetNode(key-1);
    TGeoMatrix* transl = node->GetMatrix();
    TVector3 pos;
    pos.SetXYZ(transl->GetTranslation()[0],transl->GetTranslation()[1],transl->GetTranslation()[2]);
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
    Int_t iseq   = fDetectorID/100000;
    Int_t corner = (fDetectorID-100000*iseq)/10000;
    Int_t key    = fDetectorID%10000;
    TString seq="T";
    if (corner==1){  seq+=iseq; seq+="LiScC";}
    else          {  seq+=iseq; seq+="LiSc";}
    TGeoVolume* assembly = gGeoManager->FindVolumeFast(seq);
    TGeoNode* node = assembly->GetNode(key-1);
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

