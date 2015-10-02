// -------------------------------------------------------------------
// -----       CosmicsGenerator source file for SHiP             -----
// -----      Version as of 15.09.15  by Martin Franke           -----
// -----       mailto: mfranke(at)physik.hu-berlin.de            -----
// -------------------------------------------------------------------

#ifndef PNDCoGENERATOR_H
#define PNDCoGENERATOR_H 1

#include "TROOT.h"
#include "FairGenerator.h"
#include "TRandom3.h"
#include "TF1.h"
#include "TMath.h"
#include "TH1.h"

using namespace std;
class FairPrimaryGenerator;

class Co3Rng{
	public:
	   Co3Rng() {
			rng = new TRandom3(gRandom->GetSeed());
			fTheta = new TF1("f2","cos(x)*cos(x)",0,TMath::Pi()/2);
			fTheta->SetNpx(10);
			fSpectrumH = new TF1("f4","1400*TMath::Power(x,-2.7)*(1/(1+x/115)+0.054/(1+x/850))",100,1000); // momentum above 100GeV
		};
	   virtual ~Co3Rng() {delete rng; delete fTheta; delete fSpectrumH;};
	   double Uniform(Float_t min, Float_t max){return rng->Uniform(min,max);};
	   TF1 *fSpectrumH; 
	   TF1 *fTheta;
	   double fSpectrumL(double theta, double minE, Bool_t generateP); // momentum below 100GeV
	private:
	   TRandom3 *rng; //!
};

class CosmicsGenerator : public FairGenerator{
 public:
  	/** constructor,destructor **/
	CosmicsGenerator(){};  
	virtual ~CosmicsGenerator(){
		delete fRandomEngine; 
		cout<<nInside<<" events have been generated."<<endl;
		cout<<"There is a total of "<<nInside<<"/"<<nTest<<" muons that passed close enough to the detector."<<endl;
		cout<<"Including the given weight this corresponds to ";
		cout<<weighttest/FluxIntegral/xdist/zdist*10000<<" spills (1 spill = "<<xdist*zdist*FluxIntegral/10000;
		cout<<" real cosmic muons = "<<n_EVENTS<<" simulated events)."<<endl;
	};
  
	/** public method ReadEvent **/
	Bool_t ReadEvent(FairPrimaryGenerator*);  //!
	//  virtual Bool_t Init(); //!
	virtual Bool_t Init(Bool_t largeMom); //!
	
	double z0, yBox,xBox,zBox,xdist, zdist, minE;
	int n_EVENTS;
  
 private:
	Co3Rng *fRandomEngine;//!
  
 protected:
	double P,px,py,pz,x,y,z,weighttest, weight, mass, FluxIntegral, theta;
	int PID,nInside,nTest;//!
	Bool_t high;
	
	void GenerateDynamics();
	Bool_t DetectorBox();
	ClassDef(CosmicsGenerator,4);
};

#endif /* !PNDCoGENERATOR_H */
