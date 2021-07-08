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

  int subsystem     = floor(fDetectorID/1e+4);
  int plane                = floor(fDetectorID/1e+3) - 10*subsystem;
  int bar_number = fDetectorID - subsystem*1e+4 - plane*1e+3;

  TString path = "FAIRGeom/cave_1/";
  std::stringstream sstream;
  sstream << std::setfill('0') << std::setw(3) << bar_number;
  TString sbar_number =  sstream.str();

  switch(subsystem) {    
  
  case 1: 
      path+"volVeto_1/";
      //int digit_2 = floor(fDetectorID/1e+3) - 10;
      if (plane == 0) {
        path+="volVetoPlane_0_0/volVetoBar_10";
        //int bar_number = fDetectorID- digit_1*1e+4 - digit_2*1e+3;
        path+=sbar_number;
        }
      else if (plane == 1) {
        path+="volVetoPlane_1_1/volVetoBar_11";
        //int bar_number = fDetectorID - digit_1*1e+4 - digit_2*1e+3;
       path+=sbar_number;
        }
      break;
    
    case 2: 
      path+="volMuFilter_1/";
      if (plane == 0) {
        path+="volMuUpstreamDet_0_2/volMuUpstreamBar_20";
        path+=sbar_number;
        }
      else if (plane == 1) {
        path+="volVetoPlane_1_3/volVetoBar_21";
        //int bar_number = fDetectorID - digit_1*1e+4 - digit_2*1e+3;
        path+=sbar_number;
        }
      else if (plane == 2) {
        path+="volVetoPlane_2_4/volVetoBar_22";
        //int bar_number = fDetectorID - digit_1*1e+4 - digit_2*1e+3;
        path+=sbar_number;
        }
      else if (plane == 3) {
        path+="volVetoPlane_3_5/volVetoBar_23";
        //int bar_number = fDetectorID - digit_1*1e+4 - digit_2*1e+3;
       path+=sbar_number;
        }
      else if (plane == 4) {
        path+="volVetoPlane_4_6/volVetoBar_24";
        //int bar_number = fDetectorID - digit_1*1e+4 - digit_2*1e+3;
       path+=bar_number;
        }                                     
      break;

    case 3: 
      path+="volMuFilter_1/";
      if (plane == 0) {
        path+="volMuDownstreamDet_0_5/volMuDownstreamBar_";
        //int bar_number = fDetectorID - digit_1*1e+4 - digit_2*1e+3;
        if ( bar_number < 60 ) {  path+="hor_"+sbar_number;}
        else {   path+="ver_"+sbar_number;}
      break;
      if (plane == 1) {
        path+="volMuDownstreamDet_1_6/volMuDownstreamBar_";
        //int bar_number = fDetectorID - digit_1*1e+4 - digit_2*1e+3;
        if ( bar_number < 60 ) { path+="hor_"+sbar_number;}
        else {path+="ver_"+sbar_number;}
        }
      break;
      if (plane == 2) {
        path+="volMuDownstreamDet_2_7/volMuDownstreamBar_";
        //int bar_number = fDetectorID - digit_1*1e+4 - digit_2*1e+3;
        if ( bar_number < 60 ) { path+="hor_"+sbar_number; }
        else { path+="ver_"+sbar_number; }
        }
      break;
  }

    TGeoNavigator* nav = gGeoManager->GetCurrentNavigator();
    nav->cd(path);
    TGeoNode* W = nav->GetCurrentNode();
    TGeoBBox* S = dynamic_cast<TGeoBBox*>(W->GetVolume()->GetShape());

    if (subsystem == 3 and bar_number >59){

      Double_t top[3] = {0,S->GetDY(), 0}; // Why z? Surely the straws go in x or y?
      Double_t bot[3] = {0,-S->GetDY(),0};
      Double_t Gtop[3],Gbot[3];
      nav->LocalToMaster(top, Gtop);   nav->LocalToMaster(bot, Gbot);
      vLeft.SetXYZ(Gtop[0],Gtop[1],Gtop[2]);
      vRight.SetXYZ(Gbot[0],Gbot[1],Gbot[2]);
    }
    else {
      Double_t posXend[3] = {S->GetDX(),0,0};
      Double_t negXend[3] = {-S->GetDX(),0,0};
      Double_t GposXend[3],GnegXend[3];
      nav->LocalToMaster(posXend, GposXend);   nav->LocalToMaster(negXend, GnegXend);
      vLeft.SetXYZ(GposXend[0],GposXend[1],GposXend[2]);
      vRight.SetXYZ(GnegXend[0],GnegXend[1],GnegXend[2]);

    }
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

// -----   Public method Print   -------------------------------------------
void MuFilterHit::Print() const
{
  std::cout << "-I- MuFilterHit: MuFilter hit " << " in detector " << fDetectorID << std::endl;
  std::cout << "digis:   LowLeft:"<<fdigiLowLeft <<" LowRight:"<< fdigiLowRight <<" HighLeft:"<<fdigiHighLeft <<" HighRight:" << fdigiHighRight<<std::endl;
}
// -------------------------------------------------------------------------

ClassImp(MuFilterHit)

