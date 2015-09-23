#include <math.h>
#include "TROOT.h"
#include "TPythia6.h"
#include "FairPrimaryGenerator.h"
#include "tPythia6Generator.h"
#include "TRandom1.h"
using std::cout;
using std::endl;
// -----   Default constructor   -------------------------------------------
tPythia6Generator::tPythia6Generator() 
{
  fMom        = 400;  // muon
  fDeepCopy   = kFALSE;  // copy complete pythia event
  fPythia     = TPythia6::Instance();
  fPionKaonDecay = kFALSE;
  fType       = "gamma/mu-";   // muon proton scattering 
  fTarget     = "p+";
}
// -------------------------------------------------------------------------

// -----   Default constructor   -------------------------------------------
Bool_t tPythia6Generator::Init() 
{
  
  fPythia->SetMRPY(1,gRandom->GetSeed());

  cout<<"Muon Momentum "<<fMom<<endl;
  
  if (fPionKaonDecay) {
// let also pion and kaon decay
   fPythia->SetMDCY(fPythia->Pycomp(211),1,100);
   fPythia->SetMDCY(fPythia->Pycomp(321),1,100);
  }
  fPythia->SetMSEL(1);     // msel 2 includes diffractive parts
// fPythia->SetMSUB(91,0);  // elastic scattering
  fPythia->SetPARP(2,2);   // To get below 10 GeV, you have to change PARP(2)

/* compass settings
# CKIN(10) = 100 
# MSEL = 2 # include elastic and diffractive to mbias
# MSTJ = 1  default, string fragmentation
*/

  fPythia->Initialize("FIXT",fType,fTarget,fMom);

  return kTRUE;
}
// -------------------------------------------------------------------------


// -----   Destructor   ----------------------------------------------------
tPythia6Generator::~tPythia6Generator() 
{
}
// -------------------------------------------------------------------------

// -----   Passing the event   ---------------------------------------------
Bool_t tPythia6Generator::ReadEvent(FairPrimaryGenerator* cpg)
{
  Int_t npart = 0;
  while(npart == 0)
    {
      fPythia->GenerateEvent();
// remove all unnecessary stuff
      fPythia->Pyedit(2);
      npart = fPythia->GetN();
    };

  for(Int_t ii=1; ii<fPythia->GetN()+1; ii++){
    Bool_t wanttracking=false;    
    if(fPythia->GetK(ii,1) == 1){ wanttracking=true;}
    Int_t id    = fPythia->GetK(ii,2);
    Double_t z  = fPythia->GetV(ii,3)/10.; 
    Double_t x  = fPythia->GetV(ii,1)/10.;  
    Double_t y  = fPythia->GetV(ii,2)/10.; 
    Double_t pz = fPythia->GetP(ii,3);  
    Double_t px = fPythia->GetP(ii,1);  
    Double_t py = fPythia->GetP(ii,2);  
    Double_t t  = fPythia->GetP(ii,2); // time of production, in mm/c (¼ 3.33 × 10−12 s). 
    Int_t    im = fPythia->GetV(ii,4);
    // cout << "debug p6 "<<id<<" "<< pz << endl;
// copy blind complete pythia event
    if (fDeepCopy || wanttracking){ cpg->AddTrack(id,px,py,pz,x,y,z,im,wanttracking); } 
  }
  return kTRUE;
}

ClassImp(tPythia6Generator)
