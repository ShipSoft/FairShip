#include <math.h>
#include "TSystem.h"
#include "TROOT.h"
#include "TMath.h"
#include "FairPrimaryGenerator.h"
#include "TDatabasePDG.h"               // for TDatabasePDG
#include "HNLPythia8Generator.h"
const Double_t cm = 10.; // pythia units are mm
const Double_t c_light = 2.99792458e+10; // speed of light in cm/sec (c_light   = 2.99792458e+8 * m/s)
const Bool_t debug = false;
//using namespace Pythia8;

// -----   Default constructor   -------------------------------------------
HNLPythia8Generator::HNLPythia8Generator()
{
  fId         = 2212; // proton
  fMom        = 400;  // proton
  fHNL        = 9900015;    // HNL  pdg code
  fLmin       = 5000.*cm;    // mm minimum  decay position z  ROOT units !
  fLmax       = 12000.*cm;   // mm maximum decay position z
  fFDs        = 7.7/10.4;    // correction for Pythia6 to match measured Ds production
  fextFile    = "";
  fInputFile  = NULL;
  fnRetries   = 0;
  fShipEventNr = 0;
  fPythia =  new Pythia8::Pythia();
}
// -------------------------------------------------------------------------

// -----   Default constructor   -------------------------------------------
Bool_t HNLPythia8Generator::Init()
{
  if ( debug ){List(9900015);}
  fLogger = FairLogger::GetLogger();
  if (fUseRandom1) fRandomEngine = new PyTr1Rng();
  if (fUseRandom3) fRandomEngine = new PyTr3Rng();
  fPythia->setRndmEnginePtr(fRandomEngine);
  fn = 0;
  if (fextFile && *fextFile) {
     if (0 == strncmp("/eos",fextFile,4) ) {
     TString tmp = gSystem->Getenv("EOSSHIP");
     tmp+=fextFile;
     fInputFile  = TFile::Open(tmp); 
     fLogger->Info(MESSAGE_ORIGIN,"Open external file with charm or beauty hadrons on eos: %s",tmp.Data());
     if (!fInputFile) {
      fLogger->Fatal(MESSAGE_ORIGIN, "Error opening input file. You may have forgotten to provide a krb5 token. Try kinit username@lxplus.cern.ch");
      return kFALSE; }
    }else{
      fLogger->Info(MESSAGE_ORIGIN,"Open external file with charm or beauty hadrons: %s",fextFile);
      fInputFile  = new TFile(fextFile);
      if (!fInputFile) {
       fLogger->Fatal(MESSAGE_ORIGIN, "Error opening input file");
     return kFALSE; }
    }
    if (fInputFile->IsZombie()) {
     fLogger->Fatal(MESSAGE_ORIGIN, "File is corrupted");
     return kFALSE; }
     fTree = (TTree *)fInputFile->Get("pythia6");
     fNevents = fTree->GetEntries();
     fn = firstEvent;
     fTree->SetBranchAddress("id",&hid);                // particle id
     fTree->SetBranchAddress("px",&hpx);   // momentum
     fTree->SetBranchAddress("py",&hpy);
     fTree->SetBranchAddress("pz",&hpz);
     fTree->SetBranchAddress("E",&hE);
     fTree->SetBranchAddress("M",&hM);
     fTree->SetBranchAddress("mid",&mid);   // mother
     fTree->SetBranchAddress("mpx",&mpx);   // momentum
     fTree->SetBranchAddress("mpy",&mpy);
     fTree->SetBranchAddress("mpz",&mpz);
     fTree->SetBranchAddress("mE",&mE);
  }else{
     if ( debug ){std::cout<<"Beam Momentum "<<fMom<<std::endl;}
     fPythia->settings.mode("Beams:idA",  fId);
     fPythia->settings.mode("Beams:idB",  2212);
     fPythia->settings.mode("Beams:frameType",  2);
     fPythia->settings.parm("Beams:eA",fMom);
     fPythia->settings.parm("Beams:eB",0.);
  }
  TDatabasePDG* pdgBase = TDatabasePDG::Instance();
  Double_t root_ctau = pdgBase->GetParticle(fHNL)->Lifetime();
  if ( debug ){std::cout<<"tau root "<<root_ctau<< "[s] ctau root = " << root_ctau*3e10 << "[cm]"<<std::endl;}
  fctau = fPythia->particleData.tau0(fHNL); //* 3.3333e-12
  if ( debug ){std::cout<<"ctau pythia "<<fctau<<"[mm]"<<std::endl;}
  if ( debug ){List(9900015);}
  fPythia->init();
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
   std::vector<int> hnls; // pythia indices of HNL particles
   do {

   if (fextFile && *fextFile) {
// take charm or beauty hadron from external file
// correct for too much Ds produced by pythia6
    bool x = true;
    while(x){
     if (fn==fNevents) {fLogger->Warning(MESSAGE_ORIGIN, "End of input file. Rewind.");}
     fTree->GetEntry(fn%fNevents);
     fn++;
     if ( int(fabs(hid[0]) ) != 431){ x = false; }
     else {
       Double_t rnr = gRandom->Uniform(0,1);
       if( rnr<fFDs ) { x = false; };
       //cout<<"what is x "<<x<<" id "<<int(fabs(hid[0]))<<" rnr " << rnr <<" "<< fFDs <<std::endl ;
     }
    }
   fPythia->event.reset();
   fPythia->event.append( (Int_t)hid[0], 1, 0, 0, hpx[0],  hpy[0],  hpz[0],  hE[0],  hM[0], 0., 9. );
   }
  fPythia->next();
   for(int i=0; i<fPythia->event.size(); i++){
// find first HNL
      if (abs(fPythia->event[i].id())==fHNL){
          hnls.push_back( i );
      }
   }
   iHNL = hnls.size();
   if ( iHNL == 0 ){
     //fLogger->Info(MESSAGE_ORIGIN,"Event without HNL. Retry.");
     //fPythia->event.list();
     fnRetries+=1; // can happen if phasespace does not allow charm hadron to decay to HNL
   }else{
   int r =  int( gRandom->Uniform(0,iHNL) );
   // cout << " ----> debug 2 " << r  <<  endl;
   int i =  hnls[r];
         // production vertex
         zp =fPythia->event[i].zProd();
         xp =fPythia->event[i].xProd();
         yp =fPythia->event[i].yProd();
         tp =fPythia->event[i].tProd();
         // momentum
         pz =fPythia->event[i].pz();
         px =fPythia->event[i].px();
         py =fPythia->event[i].py();
         e  =fPythia->event[i].e();
         // old decay vertex
         Int_t ida =fPythia->event[i].daughter1();
         zd =fPythia->event[ida].zProd();
         xd =fPythia->event[ida].xProd();
         yd =fPythia->event[ida].yProd();
         td =fPythia->event[ida].tProd();
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
         im  = (Int_t)fPythia->event[i].mother1();
         zm  =fPythia->event[im].zProd();
         xm  =fPythia->event[im].xProd();
         ym  =fPythia->event[im].yProd();
         pmz =fPythia->event[im].pz();
         pmx =fPythia->event[im].px();
         pmy =fPythia->event[im].py();
         em  =fPythia->event[im].e();
         tm  =fPythia->event[im].tProd();
// foresee finite beam size
         Double_t dx=0;
         Double_t dy=0;
         if (fsmearBeam>0){
            Double_t test = fsmearBeam*fsmearBeam;
            Double_t Rsq  = test+1.;
            while(Rsq>test){
               dx = gRandom->Uniform(-1.,1.) * fsmearBeam;
               dy = gRandom->Uniform(-1.,1.) * fsmearBeam;
               Rsq = dx*dx+dy*dy;
            }
         }
         if (fextFile && *fextFile) {
// take grand mother particle from input file, to know if primary or secondary production
          cpg->AddTrack((Int_t)mid[0],mpx[0],mpy[0],mpz[0],xm/cm+dx,ym/cm+dy,zm/cm,-1,false,mE[0],0.,1.);
	  cpg->AddTrack((Int_t)fPythia->event[im].id(),pmx,pmy,pmz,xm/cm+dx,ym/cm+dy,zm/cm,0,false,em,tm/cm/c_light,w); // convert pythia's (x,y,z[mm], t[mm/c]) to ([cm], [s])
	  cpg->AddTrack(fHNL, px, py, pz, xp/cm+dx,yp/cm+dy,zp/cm, 1,false,e,tp/cm/c_light,w);
         }else{
	  cpg->AddTrack((Int_t)fPythia->event[im].id(),pmx,pmy,pmz,xm/cm+dx,ym/cm+dy,zm/cm,-1,false,em,tm/cm/c_light,w); // convert pythia's (x,y,z[mm], t[mm/c]) to ([cm], [s])
	  cpg->AddTrack(fHNL, px, py, pz, xp/cm+dx,yp/cm+dy,zp/cm, 0,false,e,tp/cm/c_light,w);
         }
         // bookkeep the indices of stored particles
         dec_chain.push_back( im );
         dec_chain.push_back(  i );
         //cout << endl << " insert mother pdg=" <<fPythia->event[im].id() << " pmz = " << pmz << " [GeV],  zm = " << zm << " [mm] tm = " << tm << " [mm/c]" << endl;
         //cout << " ----> insert HNL =" << fHNL << " pz = " << pz << " [GeV] zp = " << zp << " [mm] tp = " << tp << " [mm/c]" << endl;
         iHNL = i;
    }
   } while ( iHNL == 0 ); // ----------- avoid rare empty events w/o any HNL's produced

   if (fShipEventNr%100==0) {
      fLogger->Info(MESSAGE_ORIGIN,"ship event %i / pythia event-nr %i",fShipEventNr,fn);
    }
   fShipEventNr += 1;
   // fill a container with pythia indices of the HNL decay chain
   for(int k=0; k<fPythia->event.size(); k++){
     // if daughter of HNL, copy
     im =fPythia->event[k].mother1();
     while (im>0){
      if ( im == iHNL ){break;} // pick the decay products of only 1 chosen HNL
      // if ( abs(fPythia->event[im].id())==fHNL && im == iHNL ){break;}
      else {im =fPythia->event[im].mother1();}
     }
     if (im < 1) {continue;}
     dec_chain.push_back( k );
   }

   // go over daughters and store them on the stack, starting from 2 to account for HNL and its mother
   for(std::vector<int>::iterator it = dec_chain.begin() + 2; it != dec_chain.end(); ++it){
     // pythia index of the paricle to store
     int k = *it;
     // find mother position on the output stack: impy -> im
     int impy =fPythia->event[k].mother1();
     std::vector<int>::iterator itm = std::find( dec_chain.begin(), dec_chain.end(), impy);
     im =-1;  // safety
     if ( itm != dec_chain.end() )
       im = itm - dec_chain.begin(); // convert iterator into sequence number

     Bool_t wanttracking=false;
     if(fPythia->event[k].isFinal()){ wanttracking=true;}
     pz =fPythia->event[k].pz();
     px =fPythia->event[k].px();
     py =fPythia->event[k].py();
     e  =fPythia->event[k].e();
     if (fextFile && *fextFile) {im+=1;}
     cpg->AddTrack((Int_t)fPythia->event[k].id(),px,py,pz,xS/cm,yS/cm,zS/cm,im,wanttracking,e,tS/cm/c_light,w);
     // std::cout <<k<< " insert pdg =" <<fPythia->event[k].id() << " pz = " << pz << " [GeV] zS = " << zS << " [mm] tS = " << tS << "[mm/c]" <<  endl;
  }
  return kTRUE;
}
// -------------------------------------------------------------------------
void HNLPythia8Generator::SetParameters(char* par)
{
  // Set Parameters
   fPythia->readString(par);
    if ( debug ){std::cout<<"fPythia->readString(\""<<par<<"\")"<<std::endl;}
}

// -------------------------------------------------------------------------

ClassImp(HNLPythia8Generator)
