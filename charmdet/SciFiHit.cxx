#include "SciFiHit.h"
#include <iostream>
#include "TGeoBBox.h"
#include "TGeoNode.h"
#include "TGeoManager.h"
#include "TGeoShape.h"
#include "TVector3.h"

//SciFiHit::SciFiHit(Int_t detID, Float_t digi) : ShipHit(detID, digi) {}

SciFiHit::SciFiHit(Int_t detID, Float_t digi, uint32_t hitTime, uint16_t fineTime, int flags, bool triggerFlag): ShipHit(detID, digi), hitTime(hitTime), fineTime(fineTime), flags(flags), triggerFlag(triggerFlag){}

/*
void SciFiHit::EndPoints(TVector3 &vbot, TVector3 &vtop) {
// method to get strip endpoints from TGeoNavigator
  Int_t statnb = fDetectorID/10000;
  Int_t orientationnb = (fDetectorID-statnb*10000)/1000;  //1=vertical, 0=horizontal
  if (orientationnb > 1) {
     std::cout << "SciFi::StripEndPoints, not a sensitive volume "<<fDetectorID<<std::endl;
     return;
  }
  TString stat="VMuonBox_1/VSensitive";stat+=+statnb;stat+="_";stat+=statnb;
  TString striptype;
  if (orientationnb == 0) {
    striptype = "Hstrip_";
    if (fDetectorID%1000==116 || fDetectorID%1000==1){striptype = "Hstrip_ext_";}
  }
  if (orientationnb == 1) {
    striptype = "Vstrip_";
    if (fDetectorID%1000 == 184){striptype = "Vstrip_L_";}
    if (fDetectorID%1000 == 1){striptype = "Vstrip_R_";}
  }  TGeoNavigator* nav = gGeoManager->GetCurrentNavigator();
  TString path = "";path+="/";path+=stat;path+="/"+striptype;path+=fDetectorID;
  Bool_t rc = nav->cd(path);
  if (not rc){
       std::cout << "SciFi::StripEndPoints, TGeoNavigator failed "<<path<<std::endl;
       return;
  }
  TGeoNode* W = nav->GetCurrentNode();
  TGeoBBox* S = dynamic_cast<TGeoBBox*>(W->GetVolume()->GetShape());
  Double_t top[3] = {0,0,S->GetDZ()};
  Double_t bot[3] = {0,0,-S->GetDZ()};
  Double_t Gtop[3],Gbot[3];
  nav->LocalToMaster(top, Gtop);
  nav->LocalToMaster(bot, Gbot);
  vtop.SetXYZ(Gbot[0],Gbot[1],Gbot[2]);
  vbot.SetXYZ(Gtop[0],Gtop[1],Gtop[2]);
}
*/


void SciFiHit::GetSciFiXYZ(TVector3 &v, int detID)
{
  TGeoNavigator* nav = gGeoManager->GetCurrentNavigator();
  double origin[3] = {0,0,0};
  double scifiboxcenter[3] = {0,0,0}; // CHANGE  
  TGeoNode *scifiboxnode = nav->GetCurrentNode();
  scifiboxnode->LocalToMaster(origin,scifiboxcenter);
  
  TGeoVolume *scifibox = nav->GetCurrentVolume();
  double scifiboxdz = ((TGeoBBox*) scifibox->GetShape())->GetDZ(); //semithickness
  

  const int nlayers = 8; // 0 - 1 -2 - .. - 7 => layer5 or 6 was not working

  int32_t partitionID;
  unsigned int ch_layer;
  unsigned int boardId;

  partitionID = fDetectorID / pow(10,6);
  boardId = (fDetectorID - partitionID * pow(10,6)) / pow(10,5);
  ch_layer = (fDetectorID - partitionID * pow(10,6) - boardId * pow(10,5));
  

  // layer (0,1,..,7)
  unsigned int layer = boardId/3;

  double gap_die=0.220;// cm
  double gap_SiPM=0.400;
  double ch_width=0.250;// cm

  // defining coordinates
  int x,y,z;

  //angle in radiants for layers U and V (5 deg)
  double radiants=2.5/180*TMath::Pi();

  //compute half layer width to be entered in the middle of the plane
  double half_layer=1536/2*0.250+6*gap_die+5.5*gap_SiPM;

  //z positions inside a station
  double zpos[4]={0., 18.05, 39.5, 57.55};

  //layer inside a station (0,1,2,3)
  int el=layer%4;

  //z position defined as: 
  z=zpos[el]+int(layer/4)*160;

  //how many half dies
  int mult=int(ch_layer/64);

  //shift to add to the position due to dead regions
  double shift=int(mult/2)*gap_die+int(mult/2)*gap_SiPM+(mult%2)*gap_die;

  //computation of the angle for the considered layer
  double angle=radiants;

  //first station only x defined for X and U planes
  if(layer==0) {
    x = - ( ch_layer*0.250 + shift - half_layer );
    y = 0;
  }
  else if(layer==1){
    x = -( ch_layer*0.250 + shift - half_layer ) - 200*sin(angle);
    y = 0;
  }

  //first station only y defined for Y and V planes
  else if(layer==2){
    x = 0;
    y = - ( ch_layer*0.250 + shift - half_layer ) + 200*sin(angle);
  }
  else if(layer==3) {
    x = 0;
    y = - ( ch_layer*0.250 + shift - half_layer );
  }
  //second station only y defined for Y and V planes
  else if(layer==4) {
    x = 0;
    y = - ( ch_layer*0.250 + shift - half_layer );
  }
  else if(layer==5){
    x = 0;
    y = - ( ch_layer*0.250 + shift - half_layer ) - 200*sin(angle);
  }
  //second station only x defined for X and U planes
  else if(layer==6){
    x = ( ch_layer*0.250 + shift - half_layer ) + 200*sin(angle);
    y = 0;
  }
  else if(layer==7) {
    x = ( ch_layer*0.250 + shift - half_layer);
    y = 0;
  }
  //translation from z = 0 to start of the box
  z = z + scifiboxcenter[2] - scifiboxdz;
  v.SetXYZ(x,y,z);

}

ClassImp(SciFiHit)
