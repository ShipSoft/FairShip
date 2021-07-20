#include "MuFilterHit.h"
#include "MuFilter.h"
#include "FairRunSim.h"
#include "TGeoNavigator.h"
#include "TGeoManager.h"
#include "TGeoBBox.h"
#include <iomanip> 

Double_t attenuationlength = 30.00; // Change this 
Double_t maxLowDyn = 0.01; // Change this 
Double_t maxHigDyn = 1.0; // Change this 

Double_t speedOfLight = TMath::C() *100./1000000000.0 ; // from m/sec to cm/ns
// -----   Default constructor   -------------------------------------------
MuFilterHit::MuFilterHit()
  : SndlhcHit()
{
 flag = true;
}
// -----   Standard constructor   ------------------------------------------
MuFilterHit::MuFilterHit(Int_t detID, Float_t dLL,Float_t dLR,Float_t dHL,Float_t dHR)
  : SndlhcHit(detID, dLL,dLR,dHL,dHR)
{
 flag = true;
}
// -----   constructor from MuFilterPoint   ------------------------------------------
// SHOULD BE CHANGED TO CONSTRUCTOR FROM ARRAY OF MUFILTERPOINTS !
MuFilterHit::MuFilterHit(int detID, std::vector<MuFilterPoint*> V)
  : SndlhcHit()
{
     MuFilter* module = dynamic_cast<MuFilter*> (FairRunSim::Instance()->GetListOfModules()->FindObject("MuFilter") );
     // get parameters from the MuFilter detector for simulating the digitized information
     // for example:
     //  attLength = module->AttenuationLength();
    //   dynRangeLow = module->dynamicRangeLow();
    //   dynRangeHigh = module->dynamicRangeHigh();
    // not yet implemented !
     fDetectorID  = detID;
     Double_t signalLeft    = 0;
     Double_t signalRight = 0;
     for(auto p = std::begin(V); p!= std::end(V); ++p) {
        
        Double_t signal = (*p)->GetEnergyLoss();
     
      // Find distances from MCPoint centre to ends of bar 
        TVector3 vLeft,vRight;
        TVector3 impact((*p)->GetX(),(*p)->GetY() ,(*p)->GetZ() );
        GetPosition(vLeft, vRight);
        Double_t distance_Left    =  (vLeft-impact).Mag();
        Double_t distance_Right =  (vRight-impact).Mag();
        signalLeft+=signal*TMath::Exp(-distance_Left/attenuationlength);
        signalRight+=signal*TMath::Exp(-distance_Right/attenuationlength);
     }
     // template, to be replaced by proper code
     
     fdigiLowLeft     =  std::min(signalLeft,maxLowDyn) ;        //SiPM low dynamic range, left or top.
     fdigiLowRight  =  std::min(signalRight,maxLowDyn) ;       //SiPM low dynamic range, right or bottom.
     fdigiHighLeft    = std::min(signalLeft,maxHigDyn) ;        //SiPM high dynamic range, left or top.
     fdigiHighRight = std::min(signalRight,maxHigDyn) ;   //SiPM high dynamic range, right or bottom.

     flag = true;
}

void MuFilterHit::GetPosition(TVector3 vLeft, TVector3 vRight) 
{

  int subsystem     = floor(fDetectorID/10000);
  int plane                = floor(fDetectorID/1000) - 10*subsystem;
  int bar_number = fDetectorID%1000;

  TString path = "/cave_1/";
  TString barName;

  switch(subsystem) {
  
  case 1: 
      path+="volVeto_1/volVetoPlane_"+std::to_string(plane)+"_"+std::to_string(plane);
      barName = "/volVetoBar_";
      break;
  case 2: 
      path+="volMuFilter_1/volMuUpstreamDet_"+std::to_string(plane)+"_"+std::to_string(plane+2);
      barName = "/volMuUpstreamBar_";
      break;
  case 3: 
      path+="volMuFilter_1/volMuDownstreamDet_"+std::to_string(plane)+"_"+std::to_string(plane+5);
      barName = "/volMuDownstreamBar_";
      if (bar_number<60){barName+="hor_";}
      else{barName+="ver_";}
      break;
  }

  path += barName+std::to_string(fDetectorID);

  TGeoNavigator* nav = gGeoManager->GetCurrentNavigator();
  nav->cd(path);
  LOG(DEBUG) <<path<<" "<<fDetectorID<<" "<<subsystem<<" "<<bar_number;
  TGeoNode* W = nav->GetCurrentNode();
  TGeoBBox* S = dynamic_cast<TGeoBBox*>(W->GetVolume()->GetShape());

  if (subsystem == 3 and bar_number >59){  // vertical bars
      Double_t top[3] = {0,S->GetDY(), 0};
      Double_t bot[3] = {0,-S->GetDY(),0};
      Double_t Gtop[3],Gbot[3];
      nav->LocalToMaster(top, Gtop);   nav->LocalToMaster(bot, Gbot);
      vLeft.SetXYZ(Gtop[0],Gtop[1],Gtop[2]);
      vRight.SetXYZ(Gbot[0],Gbot[1],Gbot[2]);
    }
    else {     // horizontal bars
      Double_t posXend[3] = {S->GetDX(),0,0};
      Double_t negXend[3] = {-S->GetDX(),0,0};
      Double_t GposXend[3],GnegXend[3];
      nav->LocalToMaster(posXend, GposXend);   nav->LocalToMaster(negXend, GnegXend);
      vLeft.SetXYZ(GposXend[0],GposXend[1],GposXend[2]);
      vRight.SetXYZ(GnegXend[0],GnegXend[1],GnegXend[2]);
    }
}
// -------------------------------------------------------------------------

// -----   Destructor   ----------------------------------------------------
MuFilterHit::~MuFilterHit() { }
// -------------------------------------------------------------------------

// -----   Public method GetEnergy   -------------------------------------------
Float_t MuFilterHit::GetEnergy()
{
  // to be calculated from digis and calibration constants
  Float_t E = 333;
  return E;
}

bool MuFilterHit::isVertical(){
  if  (floor(fDetectorID/10000)==3&&fDetectorID%1000>59) {return kTRUE;}
  else{return kFALSE;}
}

// -----   Public method Print   -------------------------------------------
void MuFilterHit::Print() const
{
  std::cout << "-I- MuFilterHit: MuFilter hit " << " in detector " << fDetectorID << std::endl;
  if ( floor(fDetectorID/10000)==3&&fDetectorID%1000>59) {
  std::cout << "digis:   LowTop:"<<fdigiLowLeft <<" LowBottom:"<< fdigiLowRight <<" HighTop:"<<fdigiHighLeft <<"    HighBottom:" << fdigiHighRight<<std::endl;
  }else{
  std::cout << "digis:   LowLeft:"<<fdigiLowLeft <<" LowRight:"<< fdigiLowRight <<" HighLeft:"<<fdigiHighLeft <<"    HighRight:" << fdigiHighRight<<std::endl;
 }
}
// -------------------------------------------------------------------------

ClassImp(MuFilterHit)

