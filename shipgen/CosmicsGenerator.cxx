// -------------------------------------------------------------------
// -----       CosmicsGenerator source file for SHiP             -----
// -----      Version as of 15.09.15 by Martin Franke            -----
// -----       mailto: mfranke(at)physik.hu-berlin.de            -----
// -------------------------------------------------------------------

#include "TROOT.h"
#include "FairPrimaryGenerator.h"
#include "CosmicsGenerator.h"
#include "TDatabasePDG.h"               // for TDatabasePDG
#include "TMath.h"

using namespace std;

// -----  necessary functions  -----------------------------------------
double Co3Rng::fSpectrumL(double theta, double minE, Bool_t generateP = 1){
	// 2 Options: a) generateP, b) calcInt
	// see doi: 10.1016/j.nuclphysbps.2005.07.056. for flux details
	// ad a) returns a random P between minE and 100GeV taken from the
	//       zenith angle dependend momentum distribution
	//       Here, the inverse of the function is computed and a random
	//       number between 0 and 1 mapped to the interval [minE, 100[ GeV
	// ad b) return the momentum-integrated flux for a given zenith angle
	//       from minE to 100 GeV. Result in cm-2s-1

	theta = 180*theta/TMath::Pi(); // theta in degrees
	double a = -0.8816/10000 /(1/theta  -0.1117/1000 * theta) - 0.1096 - 0.01966*TMath::Exp(-0.02040*theta);
	double b = 0.4169/100 /(1/theta  -0.9891/10000 * theta) + 4.0395 - 4.3118*TMath::Exp(0.9235/1000*theta);
	double btilde = b  + 1.0/TMath::Ln10();
	double gamma = sqrt(-TMath::Ln10()*a);
	double offset = 0.5*btilde/a;
	double norm = TMath::Erf(gamma*(TMath::Log(100)+offset)) - TMath::Erf(gamma*(offset + TMath::Log(minE)));

	if (generateP){
		double r3 = rng->Uniform();
		return exp(TMath::ErfInverse(r3*norm+TMath::Erf(gamma*(offset + TMath::Log(minE))))/gamma-offset);
	}
	else{
		double c = -0.3516/1000 * theta*theta + 0.8861/100 * theta - 2.5985 -0.8745/100000*TMath::Exp(0.1457*theta);
		double scale = 0.5*TMath::Sqrt(TMath::Pi())/gamma * TMath::Power(10,(-0.25/a*btilde*btilde + c));
		return scale * norm;
	}
}

Bool_t CosmicsGenerator::DetectorBox(){
	// check, if a given staring setup x,y,z,px,py,pz will lead to a
	// close enough to the detector

	if ((TMath::Abs(x-(y+yBox)*px/py) < xBox && TMath::Abs(z-z0-(y+yBox)*pz/py) < zBox) ||
       (TMath::Abs(x-(y-yBox)*px/py) < xBox && TMath::Abs(z-z0-(y-yBox)*pz/py) < zBox) ||
       (TMath::Abs(y-(x+xBox)*py/px) < yBox && TMath::Abs(z-z0-(x+xBox)*pz/px) < zBox) ||
       (TMath::Abs(y-(x-xBox)*py/px) < yBox && TMath::Abs(z-z0-(x-xBox)*pz/px) < zBox)) {
		return true;
	}
	return false;
}

void CosmicsGenerator::GenerateDynamics(){
	// generate starting conditions for CM until the DetectorBox is hit
	do{
		weighttest += weight;	nTest++; //book keeping
		//momentum components
		double phi = fRandomEngine->Uniform(0,2*TMath::Pi());
		theta = fRandomEngine->fTheta->GetRandom();
		px = TMath::Sin(phi)*TMath::Sin(theta);
		pz = TMath::Cos(phi)*TMath::Sin(theta);
		py = -TMath::Cos(theta);
		//staring location
		x = fRandomEngine->Uniform(-xdist/2,xdist/2);
		z = fRandomEngine->Uniform(z0 - zdist/2, z0 + zdist/2);
	}while(!DetectorBox());
	nInside++;
}
// -----   Initiate the CMBG   -----------------------------------------
Bool_t CosmicsGenerator::Init(Bool_t largeMom){
	//general
	fRandomEngine = new Co3Rng();
	TDatabasePDG* pdgBase = TDatabasePDG::Instance();
	mass = pdgBase->GetParticle(13)->Mass(); // muons!
	cout<<"----------------------------------------------------------------------"<<endl;
	cout<<"configuration for the CMBG as defined in $FAIRSHIP/python/CMBG_conf.py: "<<endl;
	cout<<"x_dist:  "<<xdist<<endl;
	cout<<"z_dist:  "<<zdist<<endl;
	cout<<"x_box:   "<<xBox<<endl;
	cout<<"y_box:   "<<yBox<<endl;
	cout<<"z_box:   "<<zBox<<endl;
	cout<<"n_EVENTS:"<<n_EVENTS<<endl;
	cout<<"minE:    "<<minE<<endl<<endl;
	if (xdist*zdist*n_EVENTS == 0){cout<<"check the configuration for unphysical behavior."<<endl<<"We stop the execution."<<endl<<endl; return kFALSE;}

	high = largeMom;
	if (high) cout<<"Simulation for high momentum"<<endl;
	else cout<<"Simulation for low momentum"<<endl;

	// calculating weights for this run
	// weight_flux: expected #muons per spill/ #simulated events per spill: FluxIntegral*xdist*zdist/EVENTS;
	//              the respective integrals are calculated from the fluxes
	// weight_DetectorBox: only consider CM hitting the DetectorBox
	//                     this is gained from a MC test of 10xEVENTS events
	double weight_flux, weight_DetectorBox;
	FluxIntegral = 0;
	if (!high) { // momentum range 1 GeV - 100 GeV
		if (minE > 100) {cout<<"choose minE < 100 !"<<endl; return kFALSE;}
		double dt = TMath::Pi()/2/100;
		for (double t= dt/2; t< TMath::Pi()/2; t += dt){
			FluxIntegral += fRandomEngine->fSpectrumL(t, minE, 0);
		}
		FluxIntegral = 2*TMath::Pi()/3*FluxIntegral*dt*10000;
		cout<< "LowE CM flux with P < minE = "<<minE<<" : "<<FluxIntegral<< "m-2s-1"<<endl;
	}
	else { // momentum range 100 GeV - 1000 GeV
		FluxIntegral = 2*TMath::Pi()/3*fRandomEngine->fSpectrumH->Integral(100,1000);
		cout<< "HighE CM flux: "<<FluxIntegral<< "m-2s-1"<<endl;
	}
	weight_flux = FluxIntegral*xdist*zdist/n_EVENTS/10000;
	nInside = 0;  nTest = 0; weighttest = 0; // book keeping
	y = 1900; //all muons start 19m over beam axis
	for (; nInside < 10*n_EVENTS;){
		GenerateDynamics();
	}
	weight_DetectorBox = 0.10 * nTest/n_EVENTS;
	weight = weight_flux / weight_DetectorBox;
	cout<<"weight_DetectorBox: "<< weight_DetectorBox<<", weight: "<< weight<<endl;
	cout<<"----------------------------------------------------------------------"<<endl<<endl;
	nInside = 0;  nTest = 0; weighttest = 0; // book keeping

	return kTRUE;
}
// -----   Passing the event   -----------------------------------------
Bool_t CosmicsGenerator::ReadEvent(FairPrimaryGenerator* cpg){
	// muon or anti-muon
	PID = 26*(fRandomEngine->Uniform(0,1) < 1.0/2.278) - 13;
	// starting conditions
	GenerateDynamics();
	//momentum in the two regions, < or > 100 GeV
	if (!high) P = fRandomEngine->fSpectrumL(theta, minE);
	else P = fRandomEngine->fSpectrumH->GetRandom();
	px = px*P;
	py = py*P;
	pz = pz*P;
	// transfer to Geant4
	cpg->AddTrack(PID,px,py,pz,x,y,z,-1,true,TMath::Sqrt(P*P+mass*mass),0,weight);  // -1 = Mother ID, true = tracking, SQRT(x) = Energy, 0 = t
	if (!nInside%10000){cout<<nInside/10000<<"10k events have been simulated"<<endl;}
	return kTRUE;
}
// ---------------------------------------------------------------------

ClassImp(CosmicsGenerator)
