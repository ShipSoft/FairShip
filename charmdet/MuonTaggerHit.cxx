#include "MuonTaggerHit.h"
#include <iostream>
#include "TGeoBBox.h"
#include "TGeoNode.h"
#include "TGeoManager.h" 
#include "TGeoShape.h" 
#include "TVector3.h" 

MuonTaggerHit::MuonTaggerHit(Int_t detID, Float_t digi) : ShipHit(detID, digi) {}


void MuonTaggerHit::EndPoints(TVector3 &vbot, TVector3 &vtop) {
// method to get strip endpoints from TGeoNavigator
  Int_t statnb = fDetectorID/10000;
  Int_t orientationnb = (fDetectorID-statnb*10000)/1000;  //1=vertical, 0=horizontal
  if (orientationnb > 1) {
     std::cout << "MuonTagger::StripEndPoints, not a sensitive volume "<<fDetectorID<<std::endl;              
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
       std::cout << "MuonTagger::StripEndPoints, TGeoNavigator failed "<<path<<std::endl; 
       return;
  }  
  TGeoNode* W = nav->GetCurrentNode();
  TGeoBBox* S = dynamic_cast<TGeoBBox*>(W->GetVolume()->GetShape());
  Double_t top[3] = {S->GetDX(),S->GetDY(),S->GetDZ()};
  Double_t bot[3] = {-S->GetDX(),-S->GetDY(),-S->GetDZ()};
  Double_t Gtop[3],Gbot[3];
  nav->LocalToMaster(top, Gtop);
  nav->LocalToMaster(bot, Gbot);
  if (orientationnb ==0) {
     vtop.SetXYZ(Gbot[0],(Gbot[1]+Gtop[1])/2.,(Gtop[2]+Gbot[2])/2.);    
     vbot.SetXYZ(Gtop[0],(Gbot[1]+Gtop[1])/2.,(Gtop[2]+Gbot[2])/2.);      
  }     
  if (orientationnb ==1) {
     vtop.SetXYZ((Gbot[0]+Gtop[0])/2.,Gbot[1],(Gtop[2]+Gbot[2])/2.);    
     vbot.SetXYZ((Gbot[0]+Gtop[0])/2.,Gtop[1],(Gtop[2]+Gbot[2])/2.);      
  }      
}

ClassImp(MuonTaggerHit)
