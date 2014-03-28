#include <math.h>
#include "TROOT.h"
#include "Pythia.h"
#include "FairPrimaryGenerator.h"
//#include "FairGenerator.h"

#include "Pythia8Generator.h"

using namespace Pythia8;

// -----   Default constructor   -------------------------------------------
Pythia8Generator::Pythia8Generator() 
{
  fUseRandom1 = kFALSE; 
  fUseRandom3 = kTRUE;
  fId         = 2212; // proton
  fMom        = 400;  // proton
}
// -------------------------------------------------------------------------

// -----   Default constructor   -------------------------------------------
Bool_t Pythia8Generator::Init() 
{
  if (fUseRandom1) fRandomEngine = new PyTr1Rng();
  if (fUseRandom3) fRandomEngine = new PyTr3Rng();
  
  fPythia.setRndmEnginePtr(fRandomEngine);
  
  cout<<"Beam Momentum "<<fMom<<endl;
  fPythia.init(fId, 2212, 0., 0., fMom, 0., 0., 0.);
  return kTRUE;
}
// -------------------------------------------------------------------------


// -----   Destructor   ----------------------------------------------------
Pythia8Generator::~Pythia8Generator() 
{
}
// -------------------------------------------------------------------------

// -----   Passing the event   ---------------------------------------------
Bool_t Pythia8Generator::ReadEvent(FairPrimaryGenerator* cpg)
{
  Int_t npart = 0;
  while(npart == 0)
    {
      fPythia.next();
      for(int i=0; i<fPythia.event.size(); i++)
	{
	  if(fPythia.event[i].isFinal())
	    {
	      npart++;
	    };
	};
    };
  
  for(Int_t ii=0; ii<fPythia.event.size(); ii++)
    if(fPythia.event[ii].isFinal())
      {
	cpg->AddTrack((Int_t)fPythia.event[ii].id(),
		      (Double_t)fPythia.event[ii].px(),(Double_t)fPythia.event[ii].py(),(Double_t)fPythia.event[ii].pz(), 
		      0.,0.,0.);
      };
  
  return kTRUE;
}
// -------------------------------------------------------------------------
void Pythia8Generator::SetParameters(char* par)
{
  // Set Parameters
    fPythia.readString(par);
    cout<<"fPythia.readString(\""<<par<<"\")"<<endl;
}

// -------------------------------------------------------------------------
void Pythia8Generator::Print(){
  fPythia.settings.listAll();
}
// -------------------------------------------------------------------------

ClassImp(Pythia8Generator)
