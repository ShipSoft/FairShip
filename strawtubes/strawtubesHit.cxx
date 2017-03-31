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
    TGeoNode* T =  gGeoManager->GetTopVolume()->FindNode(stat);
    TString plane = "Tr";plane+=statnb;plane+=view;plane+="_plane_";plane+=pnb;plane+="_";plane+=+statnb;plane+=vnb;plane+=+pnb;plane+="00000";
    TGeoNode* P = T->GetVolume()->FindNode(plane);
    TString layer = "Tr";layer+=statnb;layer+=view;layer+="_plane_";layer+=pnb;layer+="_layer_";layer+=lnb;layer+="_";layer+=statnb;layer+=vnb;layer+=pnb;layer+=lnb;layer+="0000";
    TGeoNode* L = P->GetVolume()->FindNode(layer);
    TString wire = "wire_"+fDetectorID;wire+=1000;
    if (statnb<3){wire = "wire_12_";wire+=(fDetectorID+1000);}
    TGeoNode* W =  L->GetVolume()->FindNode(wire);
    TGeoTube* S = dynamic_cast<TGeoTube*>(W->GetVolume()->GetShape());
    Double_t top[3] = {0,0,S->GetDZ()};
    Double_t bot[3] = {0,0,-S->GetDZ()};
    Double_t Gtop[3],Gbot[3];
    W->LocalToMaster(top, Gtop);   W->LocalToMaster(bot, Gbot);
    std::copy(Gtop, Gtop+3, top); std::copy(Gbot,Gbot+3,bot);
    L->LocalToMaster(top, Gtop);   L->LocalToMaster(bot, Gbot);
    std::copy(Gtop, Gtop+3, top); std::copy(Gbot,Gbot+3,bot);
    P->LocalToMaster(top, Gtop);   P->LocalToMaster(bot, Gbot);
    std::copy(Gtop, Gtop+3, top); std::copy(Gbot,Gbot+3,bot);
    T->LocalToMaster(top, Gtop);   T->LocalToMaster(bot, Gbot);
    vtop.SetXYZ(Gtop[0],Gtop[1],Gtop[2]);
    vbot.SetXYZ(Gbot[0],Gbot[1],Gbot[2]);
}

// -------------------------------------------------------------------------

// -----   Destructor   ----------------------------------------------------
strawtubesHit::~strawtubesHit() { }
// -------------------------------------------------------------------------

// -----   Public method Print   -------------------------------------------
void strawtubesHit::Print(Int_t detID) const
{
  cout << "-I- strawtubesHit: strawtubes hit " << " in detector " << fDetectorID << endl;
  cout << "  TDC " << fdigi << " ns" << endl;
}
// -------------------------------------------------------------------------

ClassImp(strawtubesHit)

