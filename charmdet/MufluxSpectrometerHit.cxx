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
#include <math.h> 
using std::cout; 
using std::endl; 
 
 
Double_t speedOfLight = TMath::C() *100./1000000000.0 ; // from m/sec to cm/ns 
// -----   Default constructor   ------------------------------------------- 
MufluxSpectrometerHit::MufluxSpectrometerHit() 
  : ShipHit() 
{ 
  flags &= DriftTubes::Valid; 
} 
// -----   Standard constructor   ------------------------------------------ 
MufluxSpectrometerHit::MufluxSpectrometerHit(Int_t detID, Float_t ftdc) 
  : ShipHit(detID,ftdc) 
{ 
  flags &= DriftTubes::Valid; 
} 
//
MufluxSpectrometerHit::MufluxSpectrometerHit(Int_t detID, Float_t ftdc, uint16_t flag) 
  : ShipHit(detID,ftdc), flags(flag) {}
// -----   constructor from SpectrometerPoint   ------------------------------------------ 
MufluxSpectrometerHit::MufluxSpectrometerHit(MufluxSpectrometerPoint* p, Double_t t0) 
  : ShipHit() 
{ 
     TVector3 start = TVector3(); 
     TVector3 stop  = TVector3(); 
     fDetectorID = p->GetDetectorID(); 
     MufluxSpectrometer* module = dynamic_cast<MufluxSpectrometer*> (FairRunSim::Instance()->GetListOfModules()->FindObject("MufluxSpectrometer") ); 
     Double_t v_drift       = module->TubeVdrift(); 
     Double_t sigma_spatial = module->TubeSigmaSpatial(); 
     module->TubeEndPoints(fDetectorID,start,stop); 
     Double_t t_drift = fabs( gRandom->Gaus( p->dist2Wire(), sigma_spatial ) )/v_drift; 
     fdigi = t0 + t_drift + ( stop[0]-p->GetX() )/ speedOfLight; 
     flags &= DriftTubes::Valid; 
} 

void MufluxSpectrometerHit::MufluxSpectrometerEndPoints(TVector3 &vbot, TVector3 &vtop) 
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
     Bool_t rc = nav->cd(path); 
     if (not rc){ 
        cout << "MufluxSpectrometer::TubeDecode, TGeoNavigator failed "<<path<<endl;
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

 
// ------------------------------------------------------------------------- 

 
// -----   Destructor   ---------------------------------------------------- 
MufluxSpectrometerHit::~MufluxSpectrometerHit() { } 
// ------------------------------------------------------------------------- 

 
// -----   Public method Print   ------------------------------------------- 
void MufluxSpectrometerHit::Print() const 
{ 
     cout << "-I- MufluxSpectrometerHit: MufluxSpectrometer hit " << " in detector " << fDetectorID << endl; 
     cout << "  TDC " << fdigi << " ns" << endl; 
} 
// ------------------------------------------------------------------------- 

 
 ClassImp(MufluxSpectrometerHit) 
