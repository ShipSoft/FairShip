#include "MufluxSpectrometerHit.h" 
#include "MufluxSpectrometer.h" 
#include "TVector3.h" 
#include "FairRun.h" 
#include "FairRunSim.h" 
#include "TMath.h" 
#include "TRandom1.h" 
#include "TRandom3.h" 
#include "TGeoManager.h" 
#include "TGeoShape.h" 
#include "TGeoTube.h" 
 
 
#include <iostream> 
#include <cmath> 
 
 
static const Double_t speedOfLight = TMath::C() *100./1000000000.0 ; // from m/sec to cm/ns
static const int channelsPerStation [5] = {0,48,48,192,192}; 


// -----   Standard constructor   ------------------------------------------ 
MufluxSpectrometerHit::MufluxSpectrometerHit(Int_t detID, Float_t ftdc)
  : ShipHit(detID,ftdc), time_over_threshold(167.2), flags(0), channel(0) {}
MufluxSpectrometerHit::MufluxSpectrometerHit(Int_t detID, Float_t ftdc, Float_t signal_width, uint16_t flag, uint16_t ch)
  : ShipHit(detID,ftdc), time_over_threshold(signal_width), flags(flag), channel(ch) {}
// -----   constructor from SpectrometerPoint   ------------------------------------------ 
MufluxSpectrometerHit::MufluxSpectrometerHit(MufluxSpectrometerPoint* p, Double_t t0)
{
     TVector3 start = TVector3(); 
     TVector3 stop  = TVector3(); 
     fDetectorID = p->GetDetectorID(); 
     MufluxSpectrometer* module = dynamic_cast<MufluxSpectrometer*> (FairRunSim::Instance()->GetListOfModules()->FindObject("MufluxSpectrometer") ); 
     Double_t v_drift       = module->TubeVdrift(); 
     Double_t sigma_spatial = module->TubeSigmaSpatial(); 
     module->TubeEndPoints(fDetectorID,start,stop); 
     Double_t t_drift = std::abs( gRandom->Gaus( p->dist2Wire(), sigma_spatial ) )/v_drift;
     fdigi = t0 + t_drift + ( stop[0]-p->GetX() )/ speedOfLight; 
     time_over_threshold = 167.2;
} 

void MufluxSpectrometerHit::MufluxSpectrometerEndPoints(TVector3 &vbot, TVector3 &vtop, bool charm = false)
{ 
     Int_t statnb = fDetectorID/10000000; 
     Int_t vnb =  (fDetectorID - statnb*10000000)/1000000; 
     Int_t pnb =  (fDetectorID- statnb*10000000 - vnb*1000000)/100000; 
     Int_t lnb =  (fDetectorID - statnb*10000000 - vnb*1000000 - pnb*100000)/10000; 
     TString stat = "volDriftTube";stat+=+statnb;stat+="_";stat+=statnb; 
     TString view = "_x"; 
     switch (vnb) {
      case 0:
       if (statnb==1) {view = "_x";}
       else if (statnb==2) {view = "_v";}        
       break;
      case 1:
       if (statnb==1) { view = "_u";}
       else if (statnb==2) { view = "_x";}       
       break;         
      default:
       break;
     }  
     TGeoNavigator* nav = gGeoManager->GetCurrentNavigator(); 
     TString prefix = "Station_"; 
     prefix+=statnb; 
     prefix+=view;prefix+="_plane_";prefix+=pnb;prefix+="_"; 
     TString plane = prefix;plane+=statnb;plane+=vnb;plane+=+pnb;plane+="00000"; 
     TString layer = prefix+"layer_";layer+=lnb;layer+="_";layer+=statnb;layer+=vnb;layer+=pnb;layer+=lnb;layer+="0000"; 
     TString wire = "gas_"; 
     wire+=(fDetectorID); 
     if (statnb<3){wire = "gas_12_";wire+=(fDetectorID);} 
     //TString path = "/volProva_1";path+="/";path+=stat;path+="/";path+=plane;path+="/";path+=layer;path+="/";path+=wire; 
     TString path = "";path+="/";path+=stat;path+="/";path+=plane;path+="/";path+=layer;path+="/";path+=wire; 

     if (charm){
      Int_t snb =   fDetectorID - statnb*10000000 - vnb*1000000 - pnb*100000 - lnb*10000 - 2000;  
      Int_t modulenumber = (snb-1)/12; //as told me by Daniel
      TString module; 
      //level 1: mother volume, same for everyone
      TString mother ="volDriftTubeCharm_1/";
      //level 2: station, plane and module information:
      //example: x_station_3_plane_0_module_1_130000000
      prefix = "x_station_"; 
      stat = prefix + statnb;

      plane = "_plane_";
      plane += pnb;
      module = "_module_";
      module += modulenumber;

      wire = "_";
      if (modulenumber > 0) wire += modulenumber;
      wire += statnb;
      wire += "0";
      wire += pnb;
      wire += "00000";

      path = "/"+mother+stat+plane+module+wire;
      //level 3: now added layer information
      //example name x_station_3_plane_0_module_4_layer_1_430010000
      layer = "_layer_";
      layer += lnb;

      wire = "_";
      if (modulenumber > 0) wire += modulenumber;
      wire += statnb;
      wire += "0";
      wire += pnb;
      wire += lnb;
      wire += "0000";

      path += "/"+stat+plane+module+layer+wire;

      //level 4: gas tube
      //examples: gas_30002016 
      if (modulenumber==4) wire ="short_gas_";
      else wire = "gas_";
      wire += fDetectorID;
      path += "/"+wire;
     }

     Bool_t rc = nav->cd(path); 
     if (not rc){ 
        std::cout << "MufluxSpectrometer::TubeDecode, TGeoNavigator failed "<<path<< std::endl;
        return; 
     }   
     TGeoNode* W = nav->GetCurrentNode(); 
     TGeoTube* S = dynamic_cast<TGeoTube*>(W->GetVolume()->GetShape()); 
     Double_t top[3] = {0,0,S->GetDZ()}; 
     Double_t bot[3] = {0,0,-S->GetDZ()}; 
     Double_t Gtop[3],Gbot[3]; 
     nav->LocalToMaster(top, Gtop);   nav->LocalToMaster(bot, Gbot); 
     vtop.SetXYZ(Gtop[0],Gtop[1],Gtop[2]); 
     vbot.SetXYZ(Gbot[0],Gbot[1],Gbot[2]); 
} 

std::vector<int> MufluxSpectrometerHit::StationInfo(){
     std::vector<int> info;
     Int_t statnb = fDetectorID/10000000;
     Int_t vnb =  (fDetectorID - statnb*10000000)/1000000; 
     Int_t pnb =  (fDetectorID- statnb*10000000 - vnb*1000000)/100000; 
     Int_t lnb =  (fDetectorID - statnb*10000000 - vnb*1000000 - pnb*100000)/10000; 
     TString stat = "volDriftTube";stat+=+statnb;stat+="_";stat+=statnb; 
     Int_t iview = 0;
     switch (vnb) {
      case 0:
       if (statnb==1) {iview = 0;}
       else if (statnb==2) {iview = 2;}
       break;
      case 1:
       if (statnb==1) { iview = 1;}
       else if (statnb==2) { iview = 0;}
       break;
      default:
       break;
     }
     Int_t tdcId = 0;
     Int_t channelID = fDetectorID%1000;
     if (statnb==1 && iview==0){ tdcId = 0;}
     else if (statnb==1 && iview== 1){ tdcId = 0;}
     else if (statnb==2 && iview== 2 && pnb==0){ tdcId = 0;}
     else if (statnb==2 && iview== 2 && pnb==1){ tdcId = 1;}
     else if (statnb==2 && iview== 0){ tdcId = 1;}
     else if (statnb==3 && channelID<25){ tdcId = 4;}
     else if (statnb==3 && !(channelID<25)){ tdcId = 3;}
     else if (statnb==4 && channelID<13 && pnb==0){ tdcId = 3;}
     else if (statnb==4 && channelID<13 && pnb==1){ tdcId = 2;}
     else if (statnb==4 && channelID<37 && !(channelID<13)){ tdcId = 2;}
     else if (statnb==4 && channelID>36){ tdcId = 1;}
     Int_t moduleId = 1;
     if (statnb > 2){ moduleId = int( (channelID-1)/12) + 1 ;}
     info.push_back(statnb);
     info.push_back(vnb);
     info.push_back(pnb);
     info.push_back(lnb);
     info.push_back(iview);
     info.push_back(channelID);
     info.push_back(tdcId);
// make numbering along gasline
     Int_t layer = pnb*2+lnb;
     Int_t nRT   = (channelID-1)*4 + layer;
     if  (statnb > 2){nRT += (statnb-3)*48*4 + 4*48;}
     else if (iview == 1){nRT += 48;}
     else if (iview == 2){nRT += 2*48;}
     else if (statnb == 2){nRT += 3*48;}
     info.push_back(nRT);

// don't know of any nice way to return multiple variables, use python to sort out the mess. 
     return info;
}
// ------------------------------------------------------------------------- 

 
// -----   Destructor   ---------------------------------------------------- 
MufluxSpectrometerHit::~MufluxSpectrometerHit() = default;
// ------------------------------------------------------------------------- 

 
// -----   Public method Print   ------------------------------------------- 
void MufluxSpectrometerHit::Print() const 
{ 
  std::cout << "-I- MufluxSpectrometerHit: MufluxSpectrometer hit " << " in detector " << fDetectorID << std::endl; 
  std::cout << "  TDC " << fdigi << " ns" << std::endl; 
} 
// ------------------------------------------------------------------------- 

 
 ClassImp(MufluxSpectrometerHit) 
