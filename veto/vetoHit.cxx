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
    nav->LocalToMaster(origin,master);
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
   if (fDetectorID<999999){ // liquid scintillator
    Int_t iseq   = fDetectorID/100000;
    Int_t corner = (fDetectorID-100000*iseq)/10000;
    Int_t key    = fDetectorID%10000;
    TString seq="T";
    if (corner==1){  seq+=iseq; seq+="LiScC";}
    else          {  seq+=iseq; seq+="LiSc";}
    TGeoVolume* assembly = gGeoManager->FindVolumeFast(seq);
    node = assembly->GetNode(key-1);
    path += "/T";path+=iseq;path+="_1/";path+=seq;path+="_0/";path+=node->GetName();
    nav->cd(path);
   }
   if (fDetectorID>999999){ // plastic scintillator ABBCCCD
    TString nodeName="T";TString temp="_";
    Int_t A = int(fDetectorID/1000000);
    Int_t B = int((fDetectorID-A*1000000)/10000);
    Int_t C = int((fDetectorID-A*1000000-B*10000)/10);
    Int_t D = fDetectorID%10;
    Int_t vetoNr = fDetectorID;
    if (A==1){
      nodeName+="2decayVolVeto";
      path+="/T2_1/T2decayVol_0/";
    }else if (A==2){
      nodeName+="2OuterwallVeto";
      path += "/T2_1/";
    }else if (A==3){
      nodeName+="1decayVolVeto";
      path+="/T1_1/T1decayVol_0/";     
    }else {
      nodeName+="1OuterwallVeto";
      path += "/T1_1/";
    }
    if (D>3){
      path += "vleft_5/";
      temp += D;temp+="V";
      D=D-4;vetoNr=fDetectorID-4;} 
    else {path += "vleft_1/";}
    if (D==3){nodeName+="X";}
    if (D==1){nodeName+="Y";}
    if (D==2){nodeName+="T1";}
    if (D==0){nodeName+="T2";}
    if (D==1||D==3){
     if (C==0){nodeName+="DwTr";}
     else if (C==1){nodeName+="UpTr";}
     else {nodeName+="Rect";}
     if (B!=99){nodeName+="1";}
     if (B==99){nodeName+="2";}
    }else {nodeName+="_";nodeName+=C;nodeName+="V";}
    path+=nodeName;path+="_";path+=vetoNr;
    nav->cd(path);
    node=nav->GetCurrentNode();
   }
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

