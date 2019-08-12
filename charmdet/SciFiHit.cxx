#include "SciFiHit.h"
#include <iostream>
#include "TGeoBBox.h"
#include "TGeoNode.h"
#include "TGeoManager.h"
#include "TGeoShape.h"
#include "TVector3.h"

//SciFiHit::SciFiHit(Int_t detID, Float_t digi) : ShipHit(detID, digi) {}

SciFiHit::SciFiHit(Int_t detID, Int_t layerID, uint16_t ch, uint8_t board, uint32_t hitTime, uint16_t fineTime, int flags, bool triggerFlag): ShipHit(detID, layerID), ch(ch), board(board), hitTime(hitTime), fineTime(fineTime), flags(flags), triggerFlag(triggerFlag){}

void SciFiHit::GetSciFiXYZ(TVector3 &v, int detID)
{
  TGeoNavigator* nav = gGeoManager->GetCurrentNavigator();
  double origin[3] = {0,0,0};
  double scifiboxcenter[3] = {0,0,0}; // CHANGE  
  TGeoNode *scifiboxnode = nav->GetCurrentNode();
  scifiboxnode->LocalToMaster(origin,scifiboxcenter);
  
  TGeoVolume *scifibox = nav->GetCurrentVolume();
  double scifiboxdz = ((TGeoBBox*) scifibox->GetShape())->GetDZ(); //semithickness
  
  int32_t partitionID;
  const int boardId = (fDetectorID) / pow(10,5);
  const int ch = (fDetectorID - boardId * pow(10,5));

  // layer (0,1,..,7) 
  int layer = ch/1536;

  double gap_die  = 0.0220;// cm
  double gap_SiPM = 0.0400;// cm
  double ch_width = 0.0250;// cm

  // defining coordinates
  double x,y,z;

  // defining z reference positions
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

  // how much the channels should be shifted so that channels ranges btw 0-1535
  int nshift = layer*1536;  

  // channel in each layer ranging from 0-1535
  int ch_layer = ch - nshift; 

  //compute half layer width to be entered in the middle of the plane
  double half_layer = 1536./2 * ch_width + 6 * gap_die + 5.5 * gap_SiPM;

  // how many half dies 0-23
  int mult = ch_layer/64;

  // set position to the middle of the channel
  double mid_ch_position = 0.025/2; // cm

  // shift to add to the position due to dead regions
  double shift = int(mult/2) * (gap_die +  gap_SiPM) + (mult%2) * gap_die;

  //first station only x defined for X and U planes
  if(layer==0) {
    x = - ( ch_layer*ch_width + shift - half_layer ) - mid_ch_position;
    y = 0;
  }
  else if(layer==1){
    x = -( ch_layer*ch_width + shift - half_layer ) - mid_ch_position;
    y = 0;
  }

  //first station only y defined for Y and V planes
  else if(layer==2){
    x = 0;
    y = - ( ch_layer*ch_width + shift - half_layer ) - mid_ch_position;
  }
  else if(layer==3) {
    x = 0;
    y = - ( ch_layer*ch_width + shift - half_layer ) - mid_ch_position;
  }
  //second station only y defined for Y and V planes
  else if(layer==4) {
    x = 0;
    y = - ( ch_layer*ch_width + shift - half_layer ) - mid_ch_position;
  }
  else if(layer==5){
    x = 0;
    y = - ( ch_layer*ch_width + shift - half_layer ) - mid_ch_position;
  }
  //second station only x defined for X and U planes
  else if(layer==6){
    x = ( ch_layer*ch_width + shift - half_layer ) + mid_ch_position;
    y = 0;
  }
  else if(layer==7) {
    x = ( ch_layer*ch_width + shift - half_layer) + mid_ch_position;
    y = 0;
  }

  //translation from z = 0 to start of the box
  //z = z + scifiboxcenter[2] - scifiboxdz;

  v.SetXYZ(x,y,z);

}

ClassImp(SciFiHit)
