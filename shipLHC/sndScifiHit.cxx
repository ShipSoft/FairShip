#include "sndScifiHit.h"
#include "Scifi.h"
#include "FairRunSim.h"
#include "TGeoNavigator.h"
#include "TGeoManager.h"
#include "TGeoBBox.h"
#include <TRandom.h>
#include <iomanip> 

Float_t sndScifiHit::ly_CDF_landau(Double_t ly){
	Float_t *p;
	if (ly>4.5 && ly<104){
		if(ly<15){p = landau_params1;}
		else if(ly<40){p = landau_params2;}
		else {p = landau_params3;}
		return p[0] + p[1]*ly + p[2]*ly*ly + p[3]*ly*ly*ly + p[4]*ly*ly*ly*ly;
	}else{
		return 0;
	}
}

Float_t sndScifiHit::ly_CDF(Double_t cdf){
	Float_t *p;
	Float_t signal;
	if (cdf<0.0006){
		p = CDF_ly_params1;
		signal = p[0] * TMath::Sqrt(p[1]*(cdf+p[2])) * (1-TMath::Exp(p[3]*cdf)) + p[4];
	}else if (cdf<0.012){
		p = CDF_ly_params2;
		signal = p[0] * TMath::Log(sqrt(cdf)+p[1]) + p[2]*TMath::Exp(p[3]*cdf);
	}else{
		p = CDF_ly_params3;
		Float_t x = std::min(cdf,0.018561405);
		signal = p[0] * TMath::Log((p[1]-p[2]*cdf)/(p[1]+p[2]*x)) + p[3]*x + p[4];
	}
	return signal;
}

// -----   Default constructor   -------------------------------------------
sndScifiHit::sndScifiHit()
  : SndlhcHit()
{
 flag = true;
}
// -----   Standard constructor   ------------------------------------------
sndScifiHit::sndScifiHit(Int_t detID)
  : SndlhcHit(detID)
{
 flag = true;
}
// -----   constructor from ScifiPoint   ------------------------------------------
sndScifiHit::sndScifiHit(int SiPMChan, std::vector<ScifiPoint*> V, std::vector<Float_t> W)
  : SndlhcHit()
{
     Scifi* ScifiDet = dynamic_cast<Scifi*> (FairRunSim::Instance()->GetListOfModules()->FindObject("Scifi") );
     nSiPMs  = 1;
     nSides   = 1;
     for (unsigned int j=0; j<16; ++j){
        signals[j] = -1;
        times[j]    =-1;
     }

     fDetectorID  = SiPMChan;
     Float_t signalTotal    = 0;
     for( int i = 0; i <V.size();i++) {
        
        Double_t signal = V[i]->GetEnergyLoss()*W[i];
     
      // Find distances from MCPoint centre to ends of fibre
        TVector3 vLeft,vRight;
        TVector3 impact(V[i]->GetX(),V[i]->GetY() ,V[i]->GetZ() );
        ScifiDet->GetPosition(V[i]->GetDetectorID(),vLeft, vRight);  // to be checked if left is always correct, horizontal / vertical layers
        Double_t distance_Left    =  (vLeft-impact).Mag();
        signalTotal+= edep_to_ly(signalTotal*1000.)*ly_loss_mean(distance_Left,ly_loss_params); // to MeV
// assumption (T.Ruf): edep_to_ly convertes energy to light yield. Code copied from ScifiCluster.py

     }
     signals[0]= int(roundf( ly_CDF(signalTotal) ));
// assumption (T.Ruf): ly_CDF convertes light yield to digital output. Code copied from ScifiCluster.py
     flag = true;
     if (!(signals[0]>0)){flag=false;}
     LOG(DEBUG) << "signal created";
}

// -----   Destructor   ----------------------------------------------------
sndScifiHit::~sndScifiHit() { }
// -------------------------------------------------------------------------

// -----   Public method GetEnergy   -------------------------------------------
Float_t sndScifiHit::GetEnergy()
{
  // to be calculated from digis and calibration constants, missing!
  return signals[0];
}

Float_t sndScifiHit::ly_loss_mean(Float_t distance, Float_t* params){
//	It returns the light yield depending on the distance to SiPM
	return params[0] * TMath::Exp(params[1] * distance / 100.) + params[2] * TMath::Exp(params[3] * distance / 100.);
}

Float_t sndScifiHit::edep_to_ly(Float_t energy){
	/*
	It returns the light yield calculated from the energy deposit. The calculations are based 
	on the equality of the cumulative distribution functions (CDF) :
	energy => CDF(energy) => CDF(light yield) => ly

	The linear converting range 0.18 MeV < dE < 0.477 MeV corresponds 4.5 < LY < 104 ph.e.

	If energy more then 0.477 MeV the light yield calculated randomly (uniformly in the range) 
	according to the distribution

	Also a little randomness is added to the CDF value with a normal distribution and 
	standard deviation with 'sigma_in_percent' (in percent of the whole range 0 - max CDF)
	*/

	Float_t A = ly_linear_params[0];
	Float_t C = ly_linear_params[1];
	Float_t cdf_raw;
	if (e_min < energy < e_max){
		Float_t ly_lin = A * energy + C;
		cdf_raw = ly_CDF_landau(ly_lin) * k_cdfs_corr;
	}else if (e_max <= energy){
		cdf_raw = CDF_integral * gRandom->Uniform(0., 1.0);
	}else{
		return 0.;
	}
	Float_t cdf_random = gRandom->Gaus(cdf_raw, sigma_in_percent * CDF_integral);

	// Generate again while the CDF value is not in the range
	while (cdf_random < 0 || cdf_random > CDF_integral){
		cdf_random = gRandom->Gaus(cdf_raw, sigma_in_percent * CDF_integral);
	}
	return  cdf_random;
}

// -----   Public method Print   -------------------------------------------
void sndScifiHit::Print()
{
  std::cout << "-I- sndScifiHit: Scifi hit " << " in station " << GetStation();
  if ( isVertical()) {     std::cout << " vertical plane ";}
  else {     std::cout << " horizontal plane ";}
  std::cout << "SiPM nr "<<GetSiPM()<< " SiPM channel "<<GetSiPMChan()<<std::endl;
}
// -------------------------------------------------------------------------

ClassImp(sndScifiHit)

