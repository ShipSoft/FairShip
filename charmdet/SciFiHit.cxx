#include "SciFiHit.h"
#include <iostream>
#include "TGeoBBox.h"
#include "TGeoNode.h"
#include "TGeoManager.h"
#include "TGeoShape.h"
#include "TVector3.h"

//SciFiHit::SciFiHit(Int_t detID, Float_t digi) : ShipHit(detID, digi) {}

SciFiHit::SciFiHit(Int_t detID, Float_t digi, uint16_t ch, uint8_t board, uint32_t hitTime, uint16_t fineTime, int flags, bool triggerFlag): ShipHit(detID, digi), ch(ch), board(board), hitTime(hitTime), fineTime(fineTime), flags(flags), triggerFlag(triggerFlag){}

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

  boardId = (fDetectorID) / pow(10,5);
  ch_layer = (fDetectorID - boardId * pow(10,5));

  // layer (0,1,..,7)
  unsigned int layer = boardId/3;

  double gap_die  = 0.0220;// cm
  double gap_SiPM = 0.0400;// cm
  double ch_width = 0.0250;// cm

  // defining coordinates
  int x,y,z;

  //angle in radiants for layers U and V (2.5 deg)
  double angle = 2.5 / 180 * TMath::Pi();

  //compute half layer width to be entered in the middle of the plane
  double half_layer = 1536/2 * ch_width + 6 * gap_die + 5.5 * gap_SiPM;

  double z_midpoint_Ref[8];
  z_midpoint_Ref[0] =  581.3250;
  z_midpoint_Ref[1] =  584.8138;
  z_midpoint_Ref[2] =  588.3025;
  z_midpoint_Ref[3] =  591.7912;
  z_midpoint_Ref[4] =  595.2800;
  z_midpoint_Ref[5] =  598.7688;
  z_midpoint_Ref[6] =  602.2575;
  z_midpoint_Ref[7] =  605.7463;

  z=z_midpoint_Ref[layer];

  //how many half dies
  int mult = int(ch_layer/64);

  //shift to add to the position due to dead regions
  double shift = int(mult/2) * gap_die + int(mult/2) * gap_SiPM + (mult%2) * gap_die;

  //first station only x defined for X and U planes
  if(layer==0) {
    x = - ( ch_layer*ch_width + shift - half_layer );
    y = 0;
  }
  else if(layer==1){
    x = -( ch_layer*ch_width + shift - half_layer ) - 20*sin(angle);
    y = 0;
  }

  //first station only y defined for Y and V planes
  else if(layer==2){
    x = 0;
    y = - ( ch_layer*ch_width + shift - half_layer ) + 20*sin(angle);
  }
  else if(layer==3) {
    x = 0;
    y = - ( ch_layer*ch_width + shift - half_layer );
  }
  //second station only y defined for Y and V planes
  else if(layer==4) {
    x = 0;
    y = - ( ch_layer*ch_width + shift - half_layer );
  }
  else if(layer==5){
    x = 0;
    y = - ( ch_layer*ch_width + shift - half_layer ) - 20*sin(angle);
  }
  //second station only x defined for X and U planes
  else if(layer==6){
    x = ( ch_layer*ch_width + shift - half_layer ) + 20*sin(angle);
    y = 0;
  }
  else if(layer==7) {
    x = ( ch_layer*ch_width + shift - half_layer);
    y = 0;
  }
  //translation from z = 0 to start of the box
  z = z + scifiboxcenter[2] - scifiboxdz;
  v.SetXYZ(x,y,z);

}

ClassImp(SciFiHit)
