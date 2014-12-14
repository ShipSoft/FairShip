// -------------------------------------------------------------------
// -----       CosmicsGenerator source file for SHiP             -----
// -----       Version by 01.12.14  by Martin Franke             -----
// -----       mailto: mfranke(at)physik.hu-berlin.de            -----
// -------------------------------------------------------------------

#include "TROOT.h"
#include "FairPrimaryGenerator.h"
#include "CosmicsGenerator.h"
#include "TDatabasePDG.h"               // for TDatabasePDG
#include "TMath.h"

using namespace std;

Bool_t CosmicsGenerator::Init(Float_t zmiddle){
	//general
	fRandomEngine = new Co3Rng();
	TDatabasePDG* pdgBase = TDatabasePDG::Instance();
	mass = pdgBase->GetParticle(13)->Mass(); // muons!

	// coordinate system
	xdist = 3000; // production area size [cm]
	zdist = 9000; // production area size [cm]
	yTop = 600; // box top layer [cm]-> also change weight3 accordingly when varying
	z0 = zmiddle; // relative coordinate system [cm] (Z_muonstation + (Z_veto - 2 * Z_Tub1))/2,... Z_veto <0 ! ->z0 = 716
	cout<<"!!!!!!!!!!!!!!!!!! z0: "<<z0<<endl;

	// weights
	Float_t weight1 = 174*xdist*zdist/10000/500000; // expected #muons per spill/ #simulated events per spill 174*30*90/500000
	Float_t weight2 = 1.0/0.0830872; // 1/(mean momentum weight), P_max-P_min/(3*174/2pi)
	Float_t weight3 = 5.174808; // MC average of nTry/nEvents 5.174808003 +- 0.000024766
	weight = weight1 * weight2 / weight3;

	// running
	y = 2000; //all muons start 20m over beam axis
	nTry =0;  nInside = 0;  nEvent = 0; nTest = 0; weighttest = 0; // book keeping
	return kTRUE;
}

Float_t CosmicsGenerator::getPweight(Float_t P){
	// implementation of the cosmic muon spectrum at sea evel
	if (P<100){return 22*TMath::Power(P,-0.6 -0.285*TMath::Log(P));}
	else{return 1400*TMath::Power(P,-2.7)*(1/(1+P/115)+0.054/(1+P/850));}
}

// -----   Passing the event   ---------------------------------------------
Bool_t CosmicsGenerator::ReadEvent(FairPrimaryGenerator* cpg){
	Bool_t hit = 0;

	do{
		// shower characteristics
		multiplicity = fRandomEngine->randomMultiplicity();
		Float_t showerPhi = fRandomEngine->Uniform(0,2*TMath::Pi());
		Float_t showerTheta = fRandomEngine->randomTheta();

		for(Int_t m = 0;m < multiplicity; m++){
			// muon momentum and spectrum weight
			Float_t P = fRandomEngine->Uniform(0.1,1000);
			w = getPweight(P) * weight;

			// shower direction with small variations for individual muons
			Float_t phi = showerPhi + TMath::Pi()*fRandomEngine->Uniform(-1,1)/180;
			Float_t theta = showerTheta + TMath::Pi()*fRandomEngine->Uniform(-1,1)/180*2*TMath::Sin(showerTheta)*TMath::Cos(showerTheta);

			//momentum components
			px = TMath::Sin(phi)*TMath::Sin(theta)*P;
			pz = TMath::Cos(phi)*TMath::Sin(theta)*P;
			py = TMath::Cos(theta)*P;

			// start position, area 1120 m^2
			x = fRandomEngine->Uniform(-xdist/2,xdist/2);
			z = fRandomEngine->Uniform(z0 - zdist/2, z0 + zdist/2);

			// claim for flight through a box surrounding the detector
			if((TMath::Abs(x-(y+yTop)*px/py) < 300 && TMath::Abs(z-z0-(y+yTop)*pz/py) < 3650) || (TMath::Abs(x-(y-yTop)*px/py) < 300 && TMath::Abs(z-z0-(y-yTop)*pz/py) <  3650)|| (TMath::Abs(y-(x+300)*py/px)<yTop && TMath::Abs(z-z0-(x+300)*pz/px)<3650) || (TMath::Abs(y-(x-300)*py/px)<yTop && TMath::Abs(z-z0-(x-300)*pz/px)<3650)){
				//muon or anti-muon
				if (fRandomEngine->Uniform(0,1) < 1.0/2.278){id = 13;}
				else{id = -13;}
				// transfer to Geant4
				cpg->AddTrack(id,px,py,pz,x,y,z,-1,true,TMath::Sqrt(P*P+mass*mass),0,w);  // -1 = Mother ID, true = tracking, SQRT(x) = Energy, 0 = t
				hit = 1; nInside++;
			}
			nTry++; weighttest += w;
		}
		nTest++;
	}while(!hit);
	nEvent++;
	if (!nEvent%10000){cout<<nEvent/10000<<"10k events have been simulated"<<endl;}
	return kTRUE;
}

// -------------------------------------------------------------------------

ClassImp(CosmicsGenerator)
