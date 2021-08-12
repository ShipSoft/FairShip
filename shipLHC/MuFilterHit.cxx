#include "MuFilterHit.h"
#include "MuFilter.h"
#include "FairRunSim.h"
#include "TGeoNavigator.h"
#include "TGeoManager.h"
#include "TGeoBBox.h"
#include <iomanip> 

Double_t speedOfLight = TMath::C() *100./1000000000.0 ; // from m/sec to cm/ns
// -----   Default constructor   -------------------------------------------
MuFilterHit::MuFilterHit()
  : SndlhcHit()
{
 flag = true;
}
// -----   Standard constructor   ------------------------------------------
MuFilterHit::MuFilterHit(Int_t detID)
  : SndlhcHit(detID)
{
 flag = true;
}
// -----   constructor from MuFilterPoint   ------------------------------------------
MuFilterHit::MuFilterHit(int detID, std::vector<MuFilterPoint*> V)
  : SndlhcHit()
{
     MuFilter* MuFilterDet = dynamic_cast<MuFilter*> (FairRunSim::Instance()->GetListOfModules()->FindObject("MuFilter") );
     // get parameters from the MuFilter detector for simulating the digitized information
     Float_t attLength            = MuFilterDet->AttenuationLength();
     Float_t siPMcalibration = MuFilterDet->GetSiPMcalibration();
     nSiPMs  = MuFilterDet->GetnSiPMs(detID);
     nSides   = MuFilterDet->GetnSides(detID);
     for (unsigned int j=0; j<16; ++j){
        signals[j] = -1;
        times[j]    =-1;
     }
     LOG(DEBUG) << "detid "<<detID<< " size "<<nSiPMs<< "  side "<<nSides;

     Float_t dynRangeLow   = MuFilterDet->GetDynRangeLow();
     Float_t dynRangeHigh  = MuFilterDet->GetDynRangeHigh();

     fDetectorID  = detID;
     Float_t signalLeft    = 0;
     Float_t signalRight = 0;
     for(auto p = std::begin(V); p!= std::end(V); ++p) {
        
        Double_t signal = (*p)->GetEnergyLoss();
     
      // Find distances from MCPoint centre to ends of bar 
        TVector3 vLeft,vRight;
        TVector3 impact((*p)->GetX(),(*p)->GetY() ,(*p)->GetZ() );
        MuFilterDet->GetPosition(fDetectorID,vLeft, vRight);
        Double_t distance_Left    =  (vLeft-impact).Mag();
        Double_t distance_Right =  (vRight-impact).Mag();
        signalLeft+=signal*TMath::Exp(-distance_Left/attLength);
        signalRight+=signal*TMath::Exp(-distance_Right/attLength);
     }
     // downstream, only top is readout; missing, which channels have high/low dynamic range?
     for (unsigned int j=0; j<nSiPMs; ++j){
        signals[j] = signalRight/float(nSiPMs);   // most simplest model, divide signal individually.
        // times[j] = ?
        if (nSides>1){ 
            signals[j+nSiPMs] = signalLeft/float(nSiPMs);   // most simplest model, divide signal individually.
        }
     }
     flag = true;
     LOG(DEBUG) << "signal created";
}

// -----   Destructor   ----------------------------------------------------
MuFilterHit::~MuFilterHit() { }
// -------------------------------------------------------------------------

// -----   Public method GetEnergy   -------------------------------------------
Float_t MuFilterHit::GetEnergy()
{
  // to be calculated from digis and calibration constants, missing!
  Float_t E = 0;
  for (unsigned int j=0; j<nSiPMs; ++j){
        E+=signals[j];
        if (nSides>1){ E+=signals[j+nSiPMs];}
  }
  return E;
}

bool MuFilterHit::isVertical(){
  if  (floor(fDetectorID/10000)==3&&fDetectorID%1000>59) {return kTRUE;}
  else{return kFALSE;}
}

// -----   Public method Print   -------------------------------------------
void MuFilterHit::Print() const
{
  std::cout << "-I- MuFilterHit: MuFilter hit " << " in detector " << fDetectorID;

  if ( floor(fDetectorID/10000)==3&&fDetectorID%1000>59) {
     std::cout << " with vertical bars"<<std::endl;
     std::cout << "digis:";
     for (unsigned int j=0; j<nSiPMs; ++j){
         std::cout << signals[j] <<" ";
     }
  }else{
     std::cout << " with horizontal bars"<<std::endl;
     std::cout << "digis:";
     for (unsigned int j=0; j<nSiPMs; ++j){
         std::cout << signals[j] <<" ";
     }
 }
std::cout << std::endl;
}
// -------------------------------------------------------------------------

ClassImp(MuFilterHit)

