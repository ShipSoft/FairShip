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
  fHNL        = 0;    // HNL  if set to !=0, for example 9900015, only track 
  fDeepCopy   = false;  // copy complete pythia event
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
  if (fHNL>0){ cout<<"Switch to HNLPythia8Generator for HNL production, not anymore supported with Pythia8Generstor"<<endl;}
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
// only send HNL decay products to G4
              if (fHNL != 0){
                Int_t im = fPythia.event[i].mother1();
                if (fPythia.event[im].id()==fHNL ){
// for the moment, hardcode 110m is maximum decay length
                 Double_t z = fPythia.event[i].zProd();
                 Double_t x = abs(fPythia.event[i].xProd());  
                 Double_t y = abs(fPythia.event[i].yProd());  
                 if ( z < 11000. && z > 7000. && x<250. && y<250.) {
                   npart++;
                 }
               }
              }
	      else {npart++;}
	    }; 
	};
// happens if a charm particle being produced which does decay without producing a HNL. Try another event.  
//       if (npart == 0){ fPythia.event.list();}
    };

// copy blind complete pythia event
  if (fDeepCopy){
   for(Int_t ii=0; ii<fPythia.event.size(); ii++){
    Bool_t wanttracking=false;
    if(fPythia.event[ii].isFinal()){ wanttracking=true;}
    Double_t z  = fPythia.event[ii].zProd();
    Double_t x  = fPythia.event[ii].xProd();  
    Double_t y  = fPythia.event[ii].yProd();  
    Double_t pz = fPythia.event[ii].pz();
    Double_t px = fPythia.event[ii].px();  
    Double_t py = fPythia.event[ii].py();  
    Int_t    im = fPythia.event[ii].mother1(); 
    // cout<<"debug p8->geant4 full copy "<< wanttracking << " "<< ii <<  " " << fPythia.event[ii].id()<< " "<< im <<" "<<x<<" "<< y<<" "<< z <<endl;
    cpg->AddTrack((Int_t)fPythia.event[ii].id(),px,py,pz,x,y,z,im,wanttracking);
   } 
  }
  else {

// only add stable particles, except for parents of HNL decay products
  for(Int_t ii=0; ii<fPythia.event.size(); ii++){
    if(fPythia.event[ii].isFinal())
      {
        Bool_t wanttracking=true;
        if (fHNL != 0){
           Int_t im = fPythia.event[ii].mother1();
           // take only one HNL / event, by construction, all charm decay to HNL
           if ( fPythia.event[im].id() != fHNL) {wanttracking=false;}
        }           
        if (  wanttracking ) {
          Double_t z  = fPythia.event[ii].zProd();
          Double_t x  = fPythia.event[ii].xProd();  
          Double_t y  = fPythia.event[ii].yProd();  
          Double_t pz = fPythia.event[ii].pz();
          Double_t px = fPythia.event[ii].px();  
          Double_t py = fPythia.event[ii].py();  
         // does not work  Int_t    im = fPythia.event[fPythia.event[ii].mother1()].id();  // mother in pythia event, not put on stack, store at least ID
          Int_t    im =  -1;
          // cout<<"debug p8->geant4 "<< wanttracking << " "<< ii <<  " " << fPythia.event[ii].id()<< " "<< im <<" "<<x<<" "<< y<<" "<< z <<endl;
          if (fHNL != 0){im=1;}  
	  cpg->AddTrack((Int_t)fPythia.event[ii].id(),px,py,pz,x,y,z,im,wanttracking);
        }
//    virtual void AddTrack(Int_t pdgid, Double_t px, Double_t py, Double_t pz,
//                          Double_t vx, Double_t vy, Double_t vz, Int_t parent=-1,Bool_t wanttracking=true,Double_t e=-9e9);
    };
    if (fHNL != 0 && fPythia.event[ii].id() == fHNL){
         Int_t im = (Int_t)fPythia.event[ii].mother1();
         Double_t z  = fPythia.event[im].zProd();
         Double_t x  = fPythia.event[im].xProd();  
         Double_t y  = fPythia.event[im].yProd();  
         Double_t pz = fPythia.event[im].pz();
         Double_t px = fPythia.event[im].px();  
         Double_t py = fPythia.event[im].py();  
	 cpg->AddTrack((Int_t)fPythia.event[im].id(),px,py,pz,x,y,z,-1,false);   
         z  = fPythia.event[ii].zProd();
         x  = fPythia.event[ii].xProd();  
         y  = fPythia.event[ii].yProd();  
         pz = fPythia.event[ii].pz();
         px = fPythia.event[ii].px();  
         py = fPythia.event[ii].py();  
	 cpg->AddTrack((Int_t)fPythia.event[ii].id(),px,py,pz,x,y,z, 0,false);            
      };
  }
 }
// make separate container ??
  //    FairRootManager *ioman =FairRootManager::Instance();
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
void Pythia8Generator::GetPythiaInstance(int arg){
  fPythia.particleData.list(arg) ; 
  cout<<"canDecay "<<fPythia.particleData.canDecay(arg)<<" "<<fPythia.particleData.mayDecay(arg)<<endl ; 
}
// -------------------------------------------------------------------------

ClassImp(Pythia8Generator)
