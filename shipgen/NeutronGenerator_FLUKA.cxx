#include <math.h>
#include "TROOT.h"
#include "TFile.h"
#include "FairPrimaryGenerator.h"
#include "NeutronGenerator_FLUKA.h"
#include "FairLogger.h"
#include "TDatabasePDG.h"               // for TDatabasePDG
#include "TMath.h"                      // for Sqrt
#include "TRandom.h"

// read events from ntuples produced by FLUKA
Double_t neutronMass = 939.565379/1000.;
// -----   Default constructor   -------------------------------------------
NeutronGenerator_FLUKA::NeutronGenerator_FLUKA() {}
// -------------------------------------------------------------------------

// -----   Destructor   ----------------------------------------------------
NeutronGenerator_FLUKA::~NeutronGenerator_FLUKA()
{
}
// -------------------------------------------------------------------------

// -----   Passing the event   ---------------------------------------------
Bool_t NeutronGenerator_FLUKA::ReadEvent(FairPrimaryGenerator* cpg)
{
   // neutron rate as function of kinetic energy flat in log10(E) in GeV;
   fn++;
   if (fn %100000==0)  {LOG(INFO)<< "heartbeat event "<<fn;}
   Double_t Ekin = TMath::Power(10,gRandom->Uniform(-13.,-1.));
   Double_t P       = TMath::Sqrt( Ekin*Ekin+2*Ekin*neutronMass);
   Double_t phi = gRandom->Uniform(0,2*TMath::Pi());
   Double_t theta = TMath::ACos(gRandom->Uniform(-1,1));
   Double_t px = P*TMath::Sin(theta)*TMath::Cos(phi);
   Double_t py = P*TMath::Sin(theta)*TMath::Sin(phi);
   Double_t pz = P*TMath::Cos(theta);
   LOG(DEBUG) << "NeutronGenerator_FLUKA: " << Ekin << " " << P << " " << px<<" "<<py<<" "<<pz;
   // place neutrons on sphere covering maximum distance,  ~ 2m
   Double_t R       = 200;
   phi      = gRandom->Uniform(0,2*TMath::Pi());
   theta = TMath::ACos(gRandom->Uniform(-1,1));
   Double_t x = R*TMath::Sin(theta)*TMath::Cos(phi);
   Double_t y = R*TMath::Sin(theta)*TMath::Sin(phi);
   Double_t z = R*TMath::Cos(theta);

   cpg->AddTrack(2112,px,py,pz,x,y,z,-1,true,Ekin+neutronMass,0.,1.,(TMCProcess)0);

   return kTRUE;
}

ClassImp(NeutronGenerator_FLUKA)
