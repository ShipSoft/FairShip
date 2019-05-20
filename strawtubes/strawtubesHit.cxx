#include "strawtubesHit.h"
#include "strawtubes.h"
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
     TVector3 stop  = TVector3();
     fDetectorID = p->GetDetectorID();
     strawtubes* module = dynamic_cast<strawtubes*> (FairRunSim::Instance()->GetListOfModules()->FindObject("Strawtubes") );
     Double_t v_drift       = module->StrawVdrift();
     Double_t sigma_spatial = module->StrawSigmaSpatial();
     module->StrawEndPoints(fDetectorID,start,stop);
     Double_t t_drift = fabs( gRandom->Gaus( p->dist2Wire(), sigma_spatial ) )/v_drift;
     fdigi = t0 + p->GetTime() + t_drift + ( stop[0]-p->GetX() )/ speedOfLight;
     flag = true;
}
void strawtubesHit::StrawEndPoints(TVector3 &vbot, TVector3 &vtop)
{
    Int_t statnb = fDetectorID/10000000;
    Int_t vnb =  (fDetectorID - statnb*10000000)/1000000;
    Int_t pnb =  (fDetectorID- statnb*10000000 - vnb*1000000)/100000;
    Int_t lnb =  (fDetectorID - statnb*10000000 - vnb*1000000 - pnb*100000)/10000;
    TString stat = "Tr";stat+=+statnb;stat+="_";stat+=statnb;
    if (statnb==5){stat="Veto_5";}
    TString view;
    switch (vnb) {
	      case 0:
	        view = "_x1";   
                if (statnb==5){view = "_x";}   	      	 
	        break;
	      case 1:  
	      	view = "_u";     
	        break;
	      case 2:
	        view = "_v";
	        break;
	      case 3:
	        view = "_x2";
	        break;
	      default:
	        view = "_x1";}
    TGeoNavigator* nav = gGeoManager->GetCurrentNavigator();
    TString prefix = "Tr";
    if (statnb==5){prefix="Veto";}
    else{prefix+=statnb;}
    prefix+=view;prefix+="_plane_";prefix+=pnb;prefix+="_";
    TString plane = prefix;plane+=statnb;plane+=vnb;plane+=+pnb;plane+="00000";
    TString layer = prefix+"layer_";layer+=lnb;layer+="_";layer+=statnb;layer+=vnb;layer+=pnb;layer+=lnb;layer+="0000";
    TString wire = "wire_";
    if (statnb==5){wire+="veto_";}
    wire+=(fDetectorID+1000);
    if (statnb<3){wire = "wire_12_";wire+=(fDetectorID+1000);}
    TString path = "/";path+=stat;path+="/";path+=plane;path+="/";path+=layer;path+="/";path+=wire;
    Bool_t rc = nav->cd(path);
    if (not rc){
      cout << "strawtubes::StrawDecode, TgeoNavigator failed "<<path<<endl; 
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
strawtubesHit::~strawtubesHit() { }
// -------------------------------------------------------------------------

// -----   Public method Print   -------------------------------------------
void strawtubesHit::Print() const
{
  cout << "-I- strawtubesHit: strawtubes hit " << " in detector " << fDetectorID << endl;
  cout << "  TDC " << fdigi << " ns" << endl;
}
// -------------------------------------------------------------------------

ClassImp(strawtubesHit)

