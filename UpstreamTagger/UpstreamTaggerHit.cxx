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
UpstreamTaggerHit::UpstreamTaggerHit(UpstreamTaggerPoint* p, Double_t t0)
  : ShipHit()
{
  
     fDetectorID = p->GetDetectorID();
            
     Double_t a, b, c;
     a = p->GetX(); b = p->GetY(); c = p->GetZ();     
     const Double_t * point1[3];
     point1[0] = &a; point1[1] = &b; point1[2] = &c;
     point_final[0] = *point1[0];point_final[1] = *point1[1];point_final[2] = *point1[2];
     
     Double_t a1, b1, c1;
     a1 = p->GetPx(); b1 = p->GetPy(); c1 = p->GetPz();
     mom[0] = &a1; mom[1] = &b1; mom[2] = &c1;

     Float_t lpos, lneg;
     Dist(p->GetX(), lpos, lneg);
     Double_t sigma = T_resol; // in ns
     t_1 = gRandom->Gaus( 0, sigma ) + lneg/v_drift + t0 + p->GetTime();
     t_2 = gRandom->Gaus( 0, sigma ) + lpos/v_drift + t0 + p->GetTime();
     
}


// -----   Destructor   -------------------------
UpstreamTaggerHit::~UpstreamTaggerHit() { }

// ---- return time information for a given track extrapolation
std::vector<double>  UpstreamTaggerHit::GetTime(Double_t x){
     // calculate distance to left and right end
     Float_t lpos, lneg;
     Dist(x, lpos, lneg);
     Double_t dt = T_resol;
     Double_t t  =  ( (t_1-lneg/v_drift) + (t_2-lpos/v_drift) )/2;
     std::vector<double> m;
     m.push_back(t);
     m.push_back(dt);
     return m;
}
// ---- return mean time information
std::vector<double>  UpstreamTaggerHit::GetTime(){
     TGeoBBox* shape =  (TGeoBBox*)gGeoManager->GetVolume("UpstreamTagger")->GetShape();     
     Double_t t0;
     if(RpcModule < 6)
       t0 =  (t_1+t_2)/2. - 114.5/v_drift;// strip length = 229 cm in x
     else
       t0 =  (t_1+t_2)/2. - 55.5/v_drift;// strip length = 111 cm in y
     Double_t dt =  T_resol; 
     std::vector<double> m;
     m.push_back(t0);
     m.push_back(dt);
     return m;
}

std::vector<double> UpstreamTaggerHit::GetMeasurements(){
 std::vector<double> m;
 m.push_back( t_1);
 m.push_back( t_2);
 return m;
}

// distance to edges
void UpstreamTaggerHit::Dist(Float_t x, Float_t& lpos, Float_t& lneg){

     Double_t hit_final;
     Int_t mod;
     TGeoNode* node  = GetNode(hit_final, mod);
     auto shape =  dynamic_cast<TGeoBBox*>(node->GetVolume()->GetShape());
     TVector3 pos    = GetXYZ();
     if(mod > 0 && mod < 6){
       lpos = TMath::Abs( pos.X() + 114.5 - hit_final ); // strip length = 229 cm in x
       lneg = TMath::Abs( pos.X() - 114.5 - hit_final );
     }
     else if (mod >= 6){
       lpos = TMath::Abs( pos.Y() + 55.5 - hit_final ); // strip length = 111 cm in y
       lneg = TMath::Abs( pos.Y() - 55.5 - hit_final );
     }
}
// ----------------------------------------------
TVector3 UpstreamTaggerHit::GetXYZ()
{
    Double_t hit_final;
    Int_t mod;
    TGeoNavigator* nav = gGeoManager->GetCurrentNavigator();
    TGeoNode* node = GetNode(hit_final, mod);
    auto shape =  dynamic_cast<TGeoBBox*>(node->GetVolume()->GetShape());
    Double_t origin[3] = {shape->GetOrigin()[0],shape->GetOrigin()[1],shape->GetOrigin()[2]};
    Double_t master[3] = {0,0,0};
    nav->LocalToMaster(origin,master);
    TVector3 pos = TVector3(master[0],master[1],master[2]);
    return pos;
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
   TGeoNavigator* nav = gGeoManager->GetCurrentNavigator();
   mod = 0;

   Double_t XHit1 = point_final[0];
   Double_t YHit1 = point_final[1];
   Double_t ZHit1 = point_final[2];

   const Double_t PxHit1 = *mom[0];
   const Double_t PyHit1 = *mom[1];
   const Double_t PzHit1 = *mom[2];

   
   Double_t module1[11][3];
   Double_t det_zGlassPos1 = 0.2;
   Double_t det_yGlassPos1 = 105;
   Double_t det_xGlassPos1 = 223;
   Double_t det_zGlassBorderPos1 = 0.2;
   Double_t det_yGlassBorderPos1 = 1.0;
   Double_t det_xGlassBorderPos1 = 1.0;
   Double_t det_zAlPos1 = 1.1503;
   Double_t det_dzAlPos1 = 0.1;

   Double_t ybox_fulldet1 = 499;
   Double_t xbox_fulldet1 = 233.4; //cm 
   Double_t zbox_fulldet1 = 17.0024;
   Double_t z_space_layers1 = 0.2;  
   Double_t extra_y1 = 6.5;
   Double_t det_yStripPos1 = 3.1;
   Double_t det_xStripPos64_1 = 3.3;
   Double_t det_zStripPos1 = 0.0003;

   Double_t det_zPos1 = -2497.0000;
   
 //First Layer of full Rpc detector covering 2.23 x 4.99 meters with 32 strips
  module1[1][0] = 0; module1[1][1] = ((ybox_fulldet1/2.0) - ((det_yGlassPos1)/2.0));  module1[1][2] = (-(zbox_fulldet1/2.0) + (det_zAlPos1/2.0) + det_dzAlPos1);
  module1[2][0] = 0; module1[2][1] = 0; module1[2][2] = (-(zbox_fulldet1/2.0) + (det_zAlPos1/2.0) + det_dzAlPos1);
  module1[3][0] = 0; module1[3][1] = -((ybox_fulldet1/2.0) - ((det_yGlassPos1)/2.0)); module1[3][2] = (-(zbox_fulldet1/2.0) + (det_zAlPos1/2.0) + det_dzAlPos1);
   
  //Second Layer of full Rpc detector covering 2.23 x 4.99 meters with 32 strips
  module1[4][0] = 0; module1[4][1] = ((ybox_fulldet1/2.0) - ((det_yGlassPos1)) - ((det_yGlassPos1)/2.0) + extra_y1); module1[4][2] = (-(zbox_fulldet1/2.0) + det_zAlPos1 + det_dzAlPos1*3.0 + z_space_layers1 + (det_zAlPos1/2.0)); 
  module1[5][0] = 0; module1[5][1] = -((ybox_fulldet1/2.0) - ((det_yGlassPos1)) - ((det_yGlassPos1)/2.0) + extra_y1);  module1[5][2] = (-(zbox_fulldet1/2.0) + det_zAlPos1 + det_dzAlPos1*3.0 + z_space_layers1 + (det_zAlPos1/2.0));

  //Third Layer of full Rpc detector covering 2.23 x 4.99 meters with 64 strips
  module1[6][0] = 0; module1[6][1] = ((ybox_fulldet1/2.0) - ((det_yGlassPos1)/2.0));  module1[6][2] = (-(zbox_fulldet1/2.0) + (det_zAlPos1*2.0) + det_dzAlPos1*5.0 + (z_space_layers1*2.0) + (det_zAlPos1/2.0));
  module1[7][0] = 0; module1[7][1] = 0; module1[7][2] = (-(zbox_fulldet1/2.0) + (det_zAlPos1*2.0) + det_dzAlPos1*5.0 + (z_space_layers1*3.0) + (det_zAlPos1/2.0));
  module1[8][0] = 0; module1[8][1] = -((ybox_fulldet1/2.0) - ((det_yGlassPos1)/2.0)); module1[8][2] = (-(zbox_fulldet1/2.0) + (det_zAlPos1*2.0) + det_dzAlPos1*5.0 + (z_space_layers1*2.0) + (det_zAlPos1/2.0));
   
  //Fourth Layer of full Rpc detector covering 2.23 x 4.99 meters with 64 strips
  module1[9][0] = 0; module1[9][1] = ((ybox_fulldet1/2.0) - ((det_yGlassPos1)) - ((det_yGlassPos1)/2.0) + extra_y1); module1[9][2] = (-(zbox_fulldet1/2.0) + (det_zAlPos1*3.0) + det_dzAlPos1*7.0 + (z_space_layers1*3.0) + (det_zAlPos1/2.0)); 
  module1[10][0] = 0; module1[10][1] = -((ybox_fulldet1/2.0) - ((det_yGlassPos1)) - ((det_yGlassPos1)/2.0) + extra_y1);  module1[10][2] = (-(zbox_fulldet1/2.0) + (det_zAlPos1*3.0) + det_dzAlPos1*7.0 + (z_space_layers1*3.0) + (det_zAlPos1/2.0));
  
  
  Double_t Ymodule1 = -1000;
  Double_t Zmodule1 = 0;
  Double_t Xmodule11 = -1000;
  Double_t Zmodule11 = 0;
  Double_t dist1 = 1000;

  Int_t flag0 = 1;
  
  for(int i = 1; i<= 10; i++){

    if(XHit1 >= module1[i][0] - (det_xGlassPos1)/2.0 && XHit1 <= module1[i][0] + (det_xGlassPos1)/2.0 && YHit1 >= module1[i][1] - (det_yGlassPos1)/2.0 && YHit1 <= module1[i][1] + (det_yGlassPos1)/2.0 && ZHit1 >= det_zPos1 + (module1[i][2] - (det_zAlPos1+2*det_dzAlPos1)/2.0) && ZHit1 <= det_zPos1 + (module1[i][2] + (det_zAlPos1+2*det_dzAlPos1)/2.0)){

      
       if(fabs(det_zPos1 + module1[i][2] - ZHit1) < dist1){

	 if (flag0){
	   RpcDetector = 1;
	   mod = i;
	 }
	 else{
	   RpcDetector = 2;
	   mod = i+10;
	 }

	 if(i < 6){
	   Zmodule1 = det_zPos1 + module1[i][2] + det_zAlPos1 - det_zStripPos1;
	   Ymodule1 = module1[i][1] - (det_yGlassPos1 + 2*det_yGlassBorderPos1)/2.0 + 1.5; 
	 }
	 else{
	   Zmodule11 = det_zPos1 + module1[i][2] + det_zAlPos1 - det_zStripPos1;
	   Xmodule11 = module1[i][0] - (det_xGlassPos1 + 2*det_xGlassBorderPos1)/2.0 + 2.175;
	 } 
	 dist1 = fabs(det_zPos1 + module1[i][2] - ZHit1);
       }
    }
    if(i == 10 && flag0){
       Double_t tmp = -module1[6][2];     
       Double_t tmp1 = -module1[4][2];     
       Double_t tmp2 = -module1[1][2];     
      
       module1[1][2] = -module1[9][2];
       module1[2][2] = -module1[9][2];
       module1[3][2] = -module1[9][2];
       module1[4][2] = tmp;
       module1[5][2] = tmp;

       module1[6][2] = tmp1;
       module1[7][2] = tmp1;
       module1[8][2] = tmp1;
       module1[9][2] = tmp2;
       module1[10][2] = tmp2;
       
       i = 0;
       flag0 = 0;
     }
  }
 
   Double_t glass = -1;
   if(fDetectorID == 169)
     glass = 1;
   else if(fDetectorID == 170)
     glass = 2;
   else if(fDetectorID == 171)
     glass = 3;
   if(fDetectorID == 238)
     glass = 4;
   else if(fDetectorID == 239)
     glass = 5;
   else if(fDetectorID == 240)
     glass = 6;
      
   Int_t Strip = -1;			
   Int_t str = -1;
   Double_t X = -1;
   Double_t Y = -1;
 
   if(Zmodule1 != 0){

     Double_t Z = Zmodule1 - ZHit1;
     X = XHit1 + (Z*(PxHit1/TMath::Sqrt(PxHit1*PxHit1 + PyHit1*PyHit1 + PzHit1*PzHit1))); 
     Y = YHit1 + (Z*(PyHit1/TMath::Sqrt(PxHit1*PxHit1 + PyHit1*PyHit1 + PzHit1*PzHit1))); 
   
     Double_t count_strips = -1;
     Int_t counter = 0;

     for(int i = 1; i <= 32; i++){

       count_strips = Ymodule1 + i*(det_yStripPos1+0.15);
       counter++;
	 
       if(Y >= (count_strips - 3.25) && Y < count_strips){
	   
	 if(Y > count_strips - 0.075)
	   Strip = counter + 1;
	 else
	   Strip = counter;

	 if(Y > count_strips - (3.25/2.0))
	   str = 2;
	 else
	   str = 1; 
	 	   
	 break;
       }
     }
   }
   
   if(Zmodule11 != 0){

     Double_t Z = Zmodule11 - ZHit1;
     X = XHit1 + (Z*(PxHit1/TMath::Sqrt(PxHit1*PxHit1 + PyHit1*PyHit1 + PzHit1*PzHit1))); 
     Y = YHit1 + (Z*(PyHit1/TMath::Sqrt(PxHit1*PxHit1 + PyHit1*PyHit1 + PzHit1*PzHit1))); 
   
     Double_t count_strips = -1;
     Int_t counter = 0;

     for(int i = 1; i <= 64; i++){

       count_strips = Xmodule11 + i*(det_xStripPos64_1+0.15);
       counter++;
	 
       if(X >= (count_strips - 3.45) && X < count_strips){
	   
	 if(X > count_strips - 0.075)
	   Strip = counter + 1;
	 else
	   Strip = counter;

	 if(X > count_strips - (3.45/2.0))
	   str = 2;
	 else
	   str = 1; 
	 	   
	 break;
       }
     }
   }
   
   RpcModule1 = mod;
   RpcGlass = glass;
   RpcStrip = Strip;
   Rpc_NeighbourStrip = str;

   if(Zmodule1 != 0)
     hit_final = X;
   if(Zmodule11 != 0)
     hit_final = Y;

   TString path, path1;
   
   if(mod >=6 && mod <= 10 || mod >= 16){
     path = "/cave_1/Upstream_Tagger_1/UpstreamTagger1_";path+=mod;path+="/glass_upstreamtagger_";path+=fDetectorID;
     Bool_t rc = nav->cd(path);
   }
   else{
     path1 = "/cave_1/Upstream_Tagger_1/UpstreamTagger_";path1+=mod;path1+="/glass_upstreamtagger_";path1+=fDetectorID;
     Bool_t rc = nav->cd(path1);
   }
   
   return nav->GetCurrentNode();
} 

// -----   Public method Print   -----------------------
void UpstreamTaggerHit::Print() const
{ 
  cout << "-I- UpstreamTaggerHit: UpstreamTagger hit " << " in detector " << fDetectorID << endl;
  cout << "  TDC left " << t_1 << " ns   TDC right " << t_2 << " ns" << endl;
}


// -----------------------------------------------------
ClassImp(UpstreamTaggerHit)

