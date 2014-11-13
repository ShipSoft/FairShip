// -------------------------------------------------------------------
// -----       CosmicsGenerator source file for SHiP             -----
// -----       Version by 11/13/14  by Martin Franke             -----
// -------------------------------------------------------------------
#include <math.h>
#include "TROOT.h"
#include "FairPrimaryGenerator.h"
#include "CosmicsGenerator.h"
#include "TDatabasePDG.h"               // for TDatabasePDG
#include "TMath.h"                      

using namespace std; 

//Bool_t CosmicsGenerator::Init(){
//   Init(0.0);
//   return kTRUE;
//}

Bool_t CosmicsGenerator::Init(Float_t zmiddle){
	fRandomEngine = new Co3Rng();
	TDatabasePDG* pdgBase = TDatabasePDG::Instance();
	mass = pdgBase->GetParticle(13)->Mass(); // muons!
	nTry =0;  nInside = 0;  nEvent = 0; nTest = 0; weighttest = 0;
	Float_t weight1 = 194880.0/500000; // expected #muons per spill/ #simulated events per spill 174*14*80/500000
	Float_t weight2 = 1.0/0.0830872; // 1/(mean momentum weight), P_max-P_min/(3*174/2pi)
	Float_t weight3 = 3.99363; // MC average of nTry/nEvents 3.993634059 +- 0.000027617
	weight = weight1 * weight2 / weight3;
	z0 = zmiddle; // (2*Z_muonstation-Z_vessel)/2
	return kTRUE;
}

Float_t CosmicsGenerator::getPweight(Float_t P){
	if (P<100){return 22*TMath::Power(P,-0.6 -0.285*TMath::Log(P));}
	else{return 1400*TMath::Power(P,-2.7)*(1/(1+P/115)+0.054/(1+P/850));} 	
}

// -----   Passing the event   ---------------------------------------------
Bool_t CosmicsGenerator::ReadEvent(FairPrimaryGenerator* cpg){

	Bool_t hit = 0;
	y = 2000; //20m over beam axis
      
	do{
		// shower characteristics
		multiplicity = fRandomEngine->randomMultiplicity();
		Float_t showerPhi = fRandomEngine->Uniform(0,2*TMath::Pi());
		Float_t showerTheta = fRandomEngine->randomTheta();
	
		for(Int_t m = 0;m < multiplicity; m++){	
			// muon momentum
			Float_t P = fRandomEngine->Uniform(0.1,1000);
			// spectrum weight for momentum P
			w = getPweight(P) * weight;	
    			
			// shower direction with small variations for individual muons
			Float_t phi = showerPhi + TMath::Pi()*fRandomEngine->Uniform(-1,1)/180;
			Float_t theta = showerTheta + TMath::Pi()*fRandomEngine->Uniform(-1,1)/180*2*TMath::Sin(showerTheta)*TMath::Cos(showerTheta);
   
			//momentum components
			px = TMath::Sin(phi)*TMath::Sin(theta)*P; 
			pz = TMath::Cos(phi)*TMath::Sin(theta)*P;
			py = TMath::Cos(theta)*P;
			
			// start position, area 1120 m^2
			x = fRandomEngine->Uniform(-700,700);
			z = fRandomEngine->Uniform(z0 - 4000, z0 + 4000);
			
			// claim for flight close to the actual detector
			if((TMath::Abs(x-(y+600)*px/py) < 300 && TMath::Abs(z-z0-(y+600)*pz/py) < 3050) || (TMath::Abs(x-(y-600)*px/py) < 300 && TMath::Abs(z-z0-(y-600)*pz/py) <  3050)|| abs(y-(x+300)*py/px)<600 && abs(z-z0-(x+300)*pz/px)<3050 || abs(y-(x-300)*py/px)<600 && abs(z-z0-(x-300)*pz/px)<3050){
				//muon or anti-muon
				if (fRandomEngine->Uniform(0,1) < 1.0/2.278){id = 13;}
				else{id = -13;} 
								
				// transfer to Geant4
				cpg->AddTrack(id,px,py,pz,x,y,z,-1,true,TMath::Sqrt(P*P+mass*mass),0,w);  // -1 = Mother ID, true = tracking, SQQRT(x) = Energy, 0 = t
				hit = 1; nInside++; 
			}
			nTry++; weighttest += w;
		}
		nTest++;
	}while(!hit);
	nEvent++;
	//if (nEvent%1000 == 0){cout<<nEvent/10000<<"10k events have been simulated"<<endl;}
  
	return kTRUE;
}

// -------------------------------------------------------------------------

ClassImp(CosmicsGenerator)
