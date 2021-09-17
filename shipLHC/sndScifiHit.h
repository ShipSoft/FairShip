#ifndef SNDSCIFIHIT_H
#define SNDSCIFIHIT_H 1

#include "SndlhcHit.h"
#include "ScifiPoint.h"
#include "TObject.h"
#include "TVector3.h"

class sndScifiHit : public SndlhcHit
{
  public:

    /** Default constructor **/
    sndScifiHit();
    sndScifiHit(Int_t detID);
    // Constructor from MuFilterPoint
    sndScifiHit(int detID,std::vector<ScifiPoint*>,std::vector<Float_t>);

 /** Destructor **/
    virtual ~sndScifiHit();

    /** Output to screen **/
	void Print() ;
	Float_t GetEnergy();

	void setInvalid() {flag = false;}
	bool isValid() const {return flag;}
	Int_t GetStation(){return int(fDetectorID/10000000);}
	bool isVertical(){
		if ( int(fDetectorID/100000)%10 == 1){return true;}
		else{return (false);}
	}
	Int_t  GetMat(){return ( int(fDetectorID/100000)%10);}
	Int_t  GetSiPM(){return ( int(fDetectorID/10000)%10);}
	Int_t GetSiPMChan(){return ( fDetectorID%1000);}
	Int_t GetChannelID(){return fDetectorID;}

  private:
    /** Copy constructor **/
    sndScifiHit(const sndScifiHit& hit);
    sndScifiHit operator=(const sndScifiHit& hit);
    Float_t ly_loss_mean(Float_t distance, Float_t* params);
    Float_t edep_to_ly(Float_t energy);
    Float_t ly_CDF_landau(Double_t ly);
    Float_t ly_CDF(Double_t cdf);

    Float_t flag;   ///< flag

// get parameters from the Scifi detector for simulating the digitized information
	Float_t ly_loss_params[4] = {20.78, -0.26, 7.89, -3.06};

/*  Energy deposit converts in the light yield range linearly. Energy less then 0.18 MeV gives doesn't registered.
 Energy more then 0.477 MeV converts randomly with approximation distribution.*/
	Float_t e_min =  0.18;
	Float_t e_max = 0.477;

/* Parameters that are used for linear conversion of deposit energy to the range 
 equal to the light yield range */
	Float_t ly_linear_params[2] = {332.882, -58.7085};

// The coefficient between the maximums of CDF(E) and CDF(LY), a little differs 
	Double_t k_cdfs_corr = 0.993076766938;
// The maximum value of the CDF integral 
	Double_t CDF_integral = 0.0185640424;

/* The addition of a little randomness in the converting from the energy distibution to 
 the light yield distibution */
	Float_t sigma_in_percent = 0.01;

/* Get a CDF value from LY (actually from an energy deposit which preliminarily linearly 
 converted to the range of the light yield (4.5 - 104 ph.e.) */
	Float_t landau_params1[5] = {0.001038, -0.000378, 3.53e-05,0.,0.};
	Float_t landau_params2[5] = {-0.001986, -0.0003014, 7.031e-05, -2.067e-06, 1.892e-08};
	Float_t landau_params3[5] = {-0.007149, 0.001056, -1.779e-05, 1.41e-07, -4.29e-10};

// Get a light yield value from a CDF values
	Float_t CDF_ly_params1[5] = {89., 4.152, 0.0001574, -1.326e+04, 4.3};  // (0., 0.0006)
	Float_t CDF_ly_params2[5] = {158, 1.035, 0.24, 217,0};  // (0.0006, 0.012)
	Float_t CDF_ly_params3[5] = {9.36, 335.984, -18100, -400, 15};  // (0.012, 0.018561405)

    ClassDef(sndScifiHit,1);

};

#endif
