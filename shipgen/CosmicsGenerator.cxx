// -------------------------------------------------------------------------
// -----       CosmicsGenerator source file for SHiP                   -----
// -----         Created 11/07/14  by Martin Franke                    -----
// -----      Version for elliptical detector Design                   -----
// -------------------------------------------------------------------------
#include <math.h>
#include "TROOT.h"
#include "FairPrimaryGenerator.h"
#include "CosmicsGenerator.h"
#include "TDatabasePDG.h"               // for TDatabasePDG
#include "TMath.h"                      

using namespace std; 
// 

// -----   Default constructor   -------------------------------------------
//Bool_t CosmicsGenerator::Init(){
//   Init(0.0);
//   return kTRUE;
//}

Bool_t CosmicsGenerator::Init(Float_t targetZ){
	fRandomEngine = new Co3Rng();
   TDatabasePDG* pdgBase = TDatabasePDG::Instance();
   mass = pdgBase->GetParticle(13)->Mass(); // muons!
   nTry =0;  nInside = 0;  nEvent = 0; nTest = 0; weighttest = 0;
   weight1 = weight1 = 194880.0/500000; // expected muons/nEvents: 2*pi/3*spectrum_integral*A = 194880/500000
	Float_t weight2 = 1.0/0.0590640; // mean momentum weight 0.059064085 +- 0.000002794
	Float_t weight3 = 4.0595; // MC average of nTry/nEvents 4.059523910 +- 0.000151934
	weight = weight1 * weight2 / weight3;
	//cout<< "TARGETZ = "<<targetZ<<endl;
	z0 = -targetZ; // dependend on target position
	zmiddle = 1000;
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
			z = fRandomEngine->Uniform(z0 + zmiddle - 4000, z0 + zmiddle + 4000);
			
			// claim for flight close to the actual detector
			if((TMath::Abs(x-(y+600)*px/py) < 300 && TMath::Abs(z-z0 -zmiddle -(y+600)*pz/py) < 3050) || (TMath::Abs(x-(y-600)*px/py) < 300 && TMath::Abs(z-z0 -zmiddle -(y-600)*pz/py) <  3050)|| abs(y - (x+300)*py/px)<600 && abs(z-z0-zmiddle-(x+300)*pz/px)<3050 || abs(y - (x-300)*py/px)<600 && abs(z-z0-zmiddle-(x-300)*pz/px)<3050){
				//muon or anti-muon
				if (fRandomEngine->Uniform(0,1) < 1.0/2.278){id = 13;}
				else{id = -13;} 
				
				Float_t e = TMath::Sqrt(P*P+mass*mass); // energy
				
				// transfer to Geant4
				cpg->AddTrack(id,px,py,pz,x,y,z,-1,true,e,0,w);  // -1 = Mother ID, true = tracking
				hit = 1; nInside++; 
		   }
		   nTry++;
			weighttest += w;
		}
		nTest++;
	}while(!hit);
	nEvent++;
   if (nEvent%1000 == 0){cout<<nEvent/1000<<"k events have been simulated"<<endl;}
  
   return kTRUE;
}

// -------------------------------------------------------------------------

ClassImp(CosmicsGenerator)
