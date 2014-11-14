// -------------------------------------------------------------------
// -----       CosmicsGenerator source file for SHiP             -----
// -----       Version by 11/13/14  by Martin Franke             -----
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
		fTheta = new TF1("f2","cos(x)*cos(x)",TMath::Pi()/2,TMath::Pi());
		fMultipl = new TH1I("fMultipl", "fMultipl",20,1,20);
		fMultipl->Fill(1,230000);
		fMultipl->Fill(2,9000);
		fMultipl->Fill(3,1800);
		fMultipl->Fill(4,800);
		fMultipl->Fill(5,420);
		fMultipl->Fill(6,240);
		fMultipl->Fill(7,170);
		fMultipl->Fill(8,120);
		fMultipl->Fill(9,90);
		fMultipl->Fill(10,70);
		fMultipl->Fill(11,53);
		fMultipl->Fill(12,42);
		fMultipl->Fill(13,34);
		fMultipl->Fill(14,31);
		fMultipl->Fill(15,28);
		fMultipl->Fill(16,21);
		fMultipl->Fill(17,19);
		fMultipl->Fill(18,18);
		fMultipl->Fill(19,17);
		fMultipl->Fill(20,16);		
	};
	virtual ~Co3Rng() {delete rng; delete fTheta; delete fMultipl;};
  
	Float_t randomTheta() {return fTheta->GetRandom();};//!
	Float_t Uniform(Float_t min, Float_t max){return rng->Uniform(min,max);};//!
	Int_t randomMultiplicity(){return (Int_t)fMultipl->GetRandom();};//!
  
 private:
	TRandom3 *rng; //!
	TF1 *fTheta;//!
	TH1I *fMultipl;//!
};

class CosmicsGenerator : public FairGenerator{
 public:
  
	/** constructor,destructor **/
	CosmicsGenerator(){};  
	virtual ~CosmicsGenerator(){
		delete fRandomEngine; 
		cout<<nEvent<<" events with a mean multiplicity of " <<1.0*nTry/nTest<<" muons per event have been generated."<<endl;
		cout<<"There is a total of "<<nInside<<" muons that passed close enough to the detector."<<endl;
		cout<<"Including the given weight this corresponds to "<<weighttest/194880<<" spills (1 spill = 194880 real cosmic muons = 500000 simulated events)."<<endl;
	};
  
	/** public method ReadEvent **/
	Bool_t ReadEvent(FairPrimaryGenerator*);  //!
	//  virtual Bool_t Init(); //!
	virtual Bool_t Init(Float_t zmiddle); //!
  
 private:
	Co3Rng *fRandomEngine;//!
	Float_t getPweight(Float_t P);//!
  
 protected:
	Float_t px,py,pz,x,y,z,w, weighttest, weight, z0, mass;
	Int_t id,nTry,nInside,nEvent,multiplicity,nTest;//!
	
	ClassDef(CosmicsGenerator,1);
};

#endif /* !PNDCoGENERATOR_H */
