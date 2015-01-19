#include <math.h>
#include "TROOT.h"
#include "TMath.h"
#include "Pythia.h"
#include "FairPrimaryGenerator.h"
#include "TDatabasePDG.h"               // for TDatabasePDG

#include "HNLPythia8Generator.h"
#include "Pythia8Generator.h"

const Double_t cm = 10.; // pythia units are mm
const Double_t c_light = 2.99792458e+10; // speed of light in cm/sec (c_light   = 2.99792458e+8 * m/s)
const Bool_t debug = false;
using namespace Pythia8;

// -----   Default constructor   -------------------------------------------
HNLPythia8Generator::HNLPythia8Generator() 
{
  fId         = 2212; // proton
  fMom        = 400;  // proton
  fHNL        = 9900015;    // HNL  pdg code
  fLmin       = 5000.*cm;    // mm minimum  decay position z  ROOT units !
  fLmax       = 12000.*cm;   // mm maximum decay position z
}
// -------------------------------------------------------------------------

// -----   Default constructor   -------------------------------------------
Bool_t HNLPythia8Generator::Init() 
{
  if ( debug ){List(9900015);}
  if (fUseRandom1) fRandomEngine = new PyTr1Rng();
  if (fUseRandom3) fRandomEngine = new PyTr3Rng();
  fPythia.setRndmEnginePtr(fRandomEngine);

  if ( debug ){cout<<"Beam Momentum "<<fMom<<endl;}
  fPythia.init(fId, 2212, 0., 0., fMom, 0., 0., 0.);
  TDatabasePDG* pdgBase = TDatabasePDG::Instance();
  Double_t root_ctau = pdgBase->GetParticle(fHNL)->Lifetime();
  if ( debug ){cout<<"tau root "<<root_ctau<< "[s] ctau root = " << root_ctau*3e10 << "[cm]"<<endl;}
  fctau = fPythia.particleData.tau0(fHNL); //* 3.3333e-12
  if ( debug ){cout<<"ctau pythia "<<fctau<<"[mm]"<<endl;}
  if ( debug ){List(9900015);}
  
  return kTRUE;
}
// -------------------------------------------------------------------------


// -----   Destructor   ----------------------------------------------------
HNLPythia8Generator::~HNLPythia8Generator() 
{
}
// -------------------------------------------------------------------------

// -----   Passing the event   ---------------------------------------------
Bool_t HNLPythia8Generator::ReadEvent(FairPrimaryGenerator* cpg)
{
   Double_t tp,td,tS,zp,xp,yp,zd,xd,yd,zS,xS,yS,pz,px,py,e,w;  
   Double_t tm,zm,xm,ym,pmz,pmx,pmy,em;  
   Int_t im;
// take HNL decay of Pythia, move it to the SHiP decay region
// recalculate decay time 
// weight event with exp(-t_ship/tau_HNL) / exp(-t_pythia/tau_HNL) 

   int iHNL = 0; // index of the chosen HNL (the 1st one), also ensures that at least 1 HNL is produced
   std::vector<int> dec_chain; // pythia indices of the particles to be stored on the stack
   do {

   fPythia.next();
   for(int i=0; i<fPythia.event.size(); i++){
// find first HNL
      if (abs(fPythia.event[i].id())==fHNL){
         // production vertex
         zp = fPythia.event[i].zProd();
         xp = fPythia.event[i].xProd();  
         yp = fPythia.event[i].yProd();  
         tp = fPythia.event[i].tProd();  
         // momentum
         pz = fPythia.event[i].pz();
         px = fPythia.event[i].px();  
         py = fPythia.event[i].py();  
         e  = fPythia.event[i].e();  
         // old decay vertex
         Int_t ida = fPythia.event[i].daughter1();
         zd = fPythia.event[ida].zProd();
         xd = fPythia.event[ida].xProd();  
         yd = fPythia.event[ida].yProd();  
         td = fPythia.event[ida].tProd();  
         // new decay vertex
         Double_t LS = gRandom->Uniform(fLmin,fLmax); // mm, G4 and Pythia8 units
         Double_t p = TMath::Sqrt(px*px+py*py+pz*pz); 
         Double_t lam = LS/p;   
         xS = xp + lam * px;
         yS = yp + lam * py;
         zS = zp + lam * pz;
         Double_t gam  = e/TMath::Sqrt(e*e-p*p); 
         Double_t beta = p/e; 
         tS = tp + LS/beta; // units ? [mm/c] + [mm/beta] (beta is dimensionless speed, and c=1 here)
                            // if one would use [s], then tS = tp/(cm*c_light) + (LS/cm)/(beta*c_light) = tS/(cm*c_light) i.e. units look consisent
         w = TMath::Exp(-LS/(beta*gam*fctau))*( (fLmax-fLmin)/(beta*gam*fctau) );
         im  = (Int_t)fPythia.event[i].mother1();
         zm  = fPythia.event[im].zProd();
         xm  = fPythia.event[im].xProd();  
         ym  = fPythia.event[im].yProd();  
         pmz = fPythia.event[im].pz();
         pmx = fPythia.event[im].px();  
         pmy = fPythia.event[im].py();  
         em  = fPythia.event[im].e();  
         tm  = fPythia.event[im].tProd();  
	 cpg->AddTrack((Int_t)fPythia.event[im].id(),pmx,pmy,pmz,xm/cm,ym/cm,zm/cm,-1,false,em,tm/cm/c_light,w); // convert pythia's (x,y,z[mm], t[mm/c]) to ([cm], [s])
	 cpg->AddTrack(fHNL, px, py, pz, xp/cm,yp/cm,zp/cm, 0,false,e,tp/cm/c_light,w); 
         // bookkeep the indices of stored particles
         dec_chain.push_back( im );
         dec_chain.push_back(  i );
         //cout << endl << " insert mother pdg=" << fPythia.event[im].id() << " pmz = " << pmz << " [GeV],  zm = " << zm << " [mm] tm = " << tm << " [mm/c]" << endl;
         //cout << " ----> insert HNL =" << fHNL << " pz = " << pz << " [GeV] zp = " << zp << " [mm] tp = " << tp << " [mm/c]" << endl;
         iHNL = i;
         break;
    }
   } 

   } while ( iHNL == 0 ); // ----------- avoid rare empty events w/o any HNL's produced


   // fill a container with pythia indices of the HNL decay chain
   for(int k=0; k<fPythia.event.size(); k++){
     // if daughter of HNL, copy
     im = fPythia.event[k].mother1();
     while (im>0){
      if ( im == iHNL ){break;} // pick the decay products of only 1 chosen HNL
      // if ( abs(fPythia.event[im].id())==fHNL && im == iHNL ){break;}
      else {im = fPythia.event[im].mother1();}
     }
     if (im < 1) {continue;}
     dec_chain.push_back( k );
   }

   // go over daughters and store them on the stack, starting from 2 to account for HNL and its mother
   for(std::vector<int>::iterator it = dec_chain.begin() + 2; it != dec_chain.end(); ++it){
     // pythia index of the paricle to store
     int k = *it;
     // find mother position on the output stack: impy -> im
     int impy = fPythia.event[k].mother1();
     std::vector<int>::iterator itm = std::find( dec_chain.begin(), dec_chain.end(), impy);
     im =-1;  // safety
     if ( itm != dec_chain.end() )
       im = itm - dec_chain.begin(); // convert iterator into sequence number

     Bool_t wanttracking=false;
     if(fPythia.event[k].isFinal()){ wanttracking=true;}
     pz = fPythia.event[k].pz();
     px = fPythia.event[k].px();  
     py = fPythia.event[k].py();  
     e  = fPythia.event[k].e();  
     zp = fPythia.event[k].zProd() + (zS-zd);
     xp = fPythia.event[k].xProd() + (xS-xd);  
     yp = fPythia.event[k].yProd() + (yS-yd);  
     tp = fPythia.event[k].tProd() + (tS-td);  
     cpg->AddTrack((Int_t)fPythia.event[k].id(),px,py,pz,xS/cm,yS/cm,zS/cm,im,wanttracking,e,tp/cm/c_light,w);
     //cout << "insert pdg =" << fPythia.event[k].id() << " pz = " << pz << " [GeV] zS = " << zS << " [mm] tp = " << tp << "[mm/c]" <<  endl;
   }
  return kTRUE;
}
// -------------------------------------------------------------------------
void HNLPythia8Generator::SetParameters(char* par)
{
  // Set Parameters
    fPythia.readString(par);
    if ( debug ){cout<<"fPythia.readString(\""<<par<<"\")"<<endl;}
} 

// -------------------------------------------------------------------------

ClassImp(HNLPythia8Generator)
