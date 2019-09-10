#include <math.h>
#include "TSystem.h"
#include "TROOT.h"
#include "TMath.h"
#include "FairPrimaryGenerator.h"
#include "TDatabasePDG.h"               // for TDatabasePDG
#include "DPPythia8Generator.h"
#include "Pythia8/Pythia.h"
const Double_t cm = 10.; // pythia units are mm
const Double_t c_light = 2.99792458e+10; // speed of light in cm/sec (c_light   = 2.99792458e+8 * m/s)
const Int_t debug = 1;

// -----   Default constructor   -------------------------------------------
DPPythia8Generator::DPPythia8Generator() 
{
  //fHadDecay = false;
  fId         = 2212; // proton
  fMom        = 400;  // proton
  fDP        = 9900015;    // DP  pdg code
  fLmin       = 5000.*cm;    // mm minimum  decay position z  ROOT units !
  fLmax       = 12000.*cm;   // mm maximum decay position z
  fFDs        = 7.7/10.4;    // correction for Pythia6 to match measured Ds production
  fpbrem = kFALSE;
  fpbremPDF = 0;
  fdy = kFALSE;
  fDPminM = 0.5;
  fextFile    = "";
  fInputFile  = NULL;
  fnRetries   = 0;
  fnDPtot = 0;
  fShipEventNr = 0;
  fPythia =  new Pythia8::Pythia();
  //fPythiaHadDecay =  new Pythia8::Pythia();
}
// -------------------------------------------------------------------------

// -----   Default constructor   -------------------------------------------
Bool_t DPPythia8Generator::Init() 
{
  fLogger = FairLogger::GetLogger();
  if (fUseRandom1) fRandomEngine = new PyTr1Rng();
  if (fUseRandom3) fRandomEngine = new PyTr3Rng();
  fPythia->setRndmEnginePtr(fRandomEngine);
  //fPythiaHadDecay->setRndmEnginePtr(fRandomEngine);
  fn = 0;
  if (fextFile && *fextFile){
    /*if (0 == strncmp("/eos",fextFile,4) ) {
     if (0 == strncmp("/eos",fextFile,4) ) {
     TString tmp = gSystem->Getenv("EOSSHIP");
     tmp+=fextFile;
     fInputFile  = TFile::Open(tmp); 
     fLogger->Info(MESSAGE_ORIGIN,""Open external file with charm or beauty hadrons on eos: %s",tmp->Data());
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
    */ 
  }
  else if (!fpbrem){ 
    if ( debug ){std::cout<<"Beam Momentum "<<fMom<<std::endl;}
    fPythia->settings.mode("Beams:idA",  fId);
    fPythia->settings.mode("Beams:idB",  2212);
    fPythia->settings.mode("Beams:frameType",  2);
    fPythia->settings.parm("Beams:eA",fMom);
    fPythia->settings.parm("Beams:eB",0.);

    if (fdy) fPythia->settings.parm("PhaseSpace:mHatMin",fDPminM);

  }
  else {
    if (!fpbremPDF) {
      //std::cout << " Failed in retrieving dark photon PDF for production by proton bremstrahlung! Exiting..." << std::endl;
      fLogger->Fatal(MESSAGE_ORIGIN, "Failed in retrieving dark photon PDF for production by proton bremstrahlung!");
      return kFALSE;
    }
  }
  /*if (fHadDecay) {
    std::cout << " ******************************** " << std::endl
	      << " ** Initialise Pythia for e+e-->hadrons " << std::endl
	      << " ******************************** " << std::endl
	      << " Mass of the A: " << fPythia->particleData.m0(fDP) << " GeV" << std::endl;
    fPythiaHadDecay->settings.mode("Beams:idA",  11);
    fPythiaHadDecay->settings.mode("Beams:idB",  -11);
    fPythiaHadDecay->settings.mode("Beams:frameType",  1);
    fPythiaHadDecay->settings.parm("Beams:eCM",10);
    fPythiaHadDecay->readString("WeakSingleBoson:ffbar2ffbar(s:gm) = on");
    //fPythiaHadDecay->readString("23:isResonance = true")
     //force to hadrons
    fPythiaHadDecay->readString("23:onMode = off");
    fPythiaHadDecay->readString("23:onIfAny = 1 2 3 4 5");
    }*/
  TDatabasePDG* pdgBase = TDatabasePDG::Instance();
  Double_t root_ctau = pdgBase->GetParticle(fDP)->Lifetime();
  //fPythia->particleData.readString("4900023:useBreitWigner = false");
  if ( debug ){
    std::cout<<"Final particle parameters for PDGID " << fDP << ":" << std::endl;
    List(fDP);
  }
  if ( debug ){std::cout<<"tau root PDG database "<<root_ctau<< "[s] ctau root = " << root_ctau*3e10 << "[cm]"<<std::endl;}
  fctau = fPythia->particleData.tau0(fDP); //* 3.3333e-12
  if ( debug ){std::cout<<"ctau pythia "<<fctau<<"[mm]"<<std::endl;}
  int initPass = fPythia->init();
  if ( debug ){std::cout<<"Pythia initialisation bool: " << initPass << std::endl;}

  if (!initPass) {
    fLogger->Fatal(MESSAGE_ORIGIN, "Pythia initialisation failed");
    return kFALSE;
  }

  return kTRUE;
  //if (fHadDecay) fPythiaHadDecay->init();
  //return kTRUE;
}
// -------------------------------------------------------------------------


// -----   Destructor   ----------------------------------------------------
DPPythia8Generator::~DPPythia8Generator() 
{
}
// -------------------------------------------------------------------------

// -----   Passing the event   ---------------------------------------------
Bool_t DPPythia8Generator::ReadEvent(FairPrimaryGenerator* cpg)
{
   Double_t tp,tS,zp,xp,yp,zS,xS,yS,pz,px,py,e,w;  
   Double_t tm,zm,xm,ym,pmz,pmx,pmy,em;
   //Double_t td,zd,xd,yd;
   Int_t im;
// take DP decay of Pythia, move it to the SHiP decay region
// recalculate decay time 
// weight event with exp(-t_ship/tau_DP) / exp(-t_pythia/tau_DP) 

   int iDP = 0; // index of the chosen DP, also ensures that at least 1 DP is produced
   std::vector<int> dec_chain; // pythia indices of the particles to be stored on the stack
   std::vector<int> dpvec; // pythia indices of DP particles
   bool hadDecay = false;
   do {
     
     if (fextFile && *fextFile){
       // take charm or beauty hadron from external file
       // correct for too much Ds produced by pythia6
       /*bool x = true; 
	 while(x){ 
	 if (fn==fNevents) {fLogger->Warning(MESSAGE_ORIGIN, "End of input file. Rewind.");}
	 fTree->GetEntry(fn%fNevents);
	 fn++;
	 if ( int(fabs(hid[0]) ) != 431){ x = false; }
	 else {
	 Double_t rnr = gRandom->Uniform(0,1);
	 if( rnr<fFDs ) { x = false; };
	 //std::cout<<"what is x "<<x<<" id "<<int(fabs(hid[0]))<<" rnr " << rnr <<" "<< fFDs <<std::endl ;
	 }
	 }          
	 fPythia->event.reset();
	 fPythia->event.append( (Int_t)hid[0], 1, 0, 0, hpx[0],  hpy[0],  hpz[0],  hE[0],  hM[0], 0., 9. );
       */
     }
     //bit for proton brem
     if (fpbrem){
       fPythia->event.reset();
       double dpmom = 0;
       double thetain = 0;
       fpbremPDF->GetRandom2(dpmom, thetain);
       double dpm = fPythia->particleData.m0(fDP);
       double dpe = sqrt(dpmom*dpmom+dpm*dpm);
       double phiin = 2. * M_PI * gRandom->Rndm();
       
       if ( debug > 1){std::cout << " Adding DP gun with p " 
		 << dpmom 
		 << " m " << dpm
		 << " e " << dpe
		 << " theta,phi " << thetain << "," << phiin << std::endl << std::flush;}
       fPythia->event.append( fDP, 1, 0, 0, dpmom * sin(thetain) * cos(phiin), dpmom * sin(thetain) * sin(phiin), dpmom * cos(thetain), dpe, dpm); 
     }

     if (!fPythia->next()) fLogger->Fatal(MESSAGE_ORIGIN, "fPythia->next() failed");

     //fPythia->event.list();
     for(int i=0; i<fPythia->event.size(); i++){
       // find all DP
       if (abs(fPythia->event[i].id())==fDP){
	 dpvec.push_back( i );
       }
     }
     iDP = dpvec.size();
     fnDPtot += iDP;
     if ( iDP == 0 ){
       //fLogger->Info(MESSAGE_ORIGIN,"Event without DP. Retry.");
       //fPythia->event.list();
       fnRetries+=1; // can happen if phasespace does not allow meson to decay to DP
     }else{
       //for mesons, could have more than one ... but for DY prod, need to take the last one...
       //int r =  int( gRandom->Uniform(0,iDP) );
       int r =  iDP-1;
       // std::cout << " ----> debug 2 " << r  <<  std::endl;
       int i =  dpvec[r];
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
       //Int_t ida =fPythia->event[i].daughter1();
       std::cout << " Debug: decay product of A: " 
		 << fPythia->event[fPythia->event[i].daughter1()].id() << " " 
		 << fPythia->event[fPythia->event[i].daughter2()].id()
		 << std::endl;
       //hadDecay = abs(fPythia->event[ida].id())!=11 && abs(fPythia->event[ida].id())!=13 && abs(fPythia->event[ida].id())!=15;

       //zd =fPythia->event[ida].zProd();
       //xd =fPythia->event[ida].xProd();
       //yd =fPythia->event[ida].yProd();
       //td =fPythia->event[ida].tProd();  
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
       if (fextFile && *fextFile){
	 // take grand mother particle from input file, to know if primary or secondary production
	 //cpg->AddTrack((Int_t)mid[0],mpx[0],mpy[0],mpz[0],xm/cm+dx,ym/cm+dy,zm/cm,-1,false,mE[0],0.,1.);
	 //cpg->AddTrack((Int_t)fPythia->event[im].id(),pmx,pmy,pmz,xm/cm+dx,ym/cm+dy,zm/cm,0,false,em,tm/cm/c_light,w); // convert pythia's (x,y,z[mm], t[mm/c]) to ([cm], [s])
	 //cpg->AddTrack(fDP, px, py, pz, xp/cm+dx,yp/cm+dy,zp/cm, 1,false,e,tp/cm/c_light,w); 
       }else{
	 cpg->AddTrack((Int_t)fPythia->event[im].id(),pmx,pmy,pmz,xm/cm+dx,ym/cm+dy,zm/cm,-1,false,em,tm/cm/c_light,w); // convert pythia's (x,y,z[mm], t[mm/c]) to ([cm], [s])
	 cpg->AddTrack(fDP, px, py, pz, xp/cm+dx,yp/cm+dy,zp/cm, 0,false,e,tp/cm/c_light,w); 
       }
       // bookkeep the indices of stored particles
       dec_chain.push_back( im );
       dec_chain.push_back(  i );
       if (debug>1) std::cout << std::endl << " insert mother id " << im << " pdg=" <<fPythia->event[im].id() << " pmz = " << pmz << " [GeV],  zm = " << zm << " [mm] tm = " << tm << " [mm/c]" << std::endl;
       if (debug>1) std::cout << " ----> insert DP id " << i << " pdg=" << fDP << " pz = " << pz << " [GeV] zp = " << zp << " [mm] tp = " << tp << " [mm/c]" << std::endl;
       iDP = i; 
     }
   } while ( iDP == 0 ); // ----------- avoid rare empty events w/o any DP's produced
   
   if (fShipEventNr%100==0) {
     fLogger->Info(MESSAGE_ORIGIN,"ship event %i / pythia event-nr %i",fShipEventNr,fn);
   }
   fShipEventNr += 1;
   // fill a container with pythia indices of the DP decay chain
   if (debug>1) std::cout << "Filling daughter particles" << std::endl;
   //if (!hadDecay){
     for(int k=0; k<fPythia->event.size(); k++){
       // if daughter of DP, copy
       if (debug>1) std::cout <<k<< " pdg =" <<fPythia->event[k].id() << " mum " << fPythia->event[k].mother1() << std::endl;
       im =fPythia->event[k].mother1();
       while (im>0){
	 if ( im == iDP ){break;} // pick the decay products of only 1 chosen DP
	 // if ( abs(fPythia->event[im].id())==fDP && im == iDP ){break;}
	 else {im =fPythia->event[im].mother1();}
       }
       if (im < 1) {
	 if (debug>1) std::cout << "reject" << std::endl;
	 continue;
       }
       if (debug>1) std::cout << "accept" << std::endl;
       dec_chain.push_back( k );
     }
     //}
     /*else {
     //get decay from e+e- collision.....
     fPythiaHadDecay->settings.parm("Beams:eCM",20);
     fPythiaHadDecay->next();
     for (int k=0; k<fPythiaHadDecay->event.size(); k++){
       fPythia->event.append( fPythiaHadDecay->event[k].id(),fPythiaHadDecay->event[k].status() ,fPythiaHadDecay->event[k].mother1() , fPythiaHadDecay->event[k].mother2(), fPythiaHadDecay->event[k].daughter1(), fPythiaHadDecay->event[k].daughter2(), fPythiaHadDecay->event[k].col(), fPythiaHadDecay->event[k].acol(), fPythiaHadDecay->event[k].px(),  fPythiaHadDecay->event[k].py(),  fPythiaHadDecay->event[k].pz(),  fPythiaHadDecay->event[k].e(),  fPythiaHadDecay->event[k].m(), 0., 9. );
       dec_chain.push_back( fPythia->event.size()-1 );
       std::cout << " Adding decay product: " << k << " "
		 << fPythiaHadDecay->event[k].id() << " " 
		 << fPythiaHadDecay->event[k].status() << " " 
		 << fPythiaHadDecay->event[k].mother1() << " "
		 << fPythiaHadDecay->event[k].mother2() << " "
		 << std::endl;
     }
     }*/
   
     // go over daughters and store them on the stack, starting from 2 to account for DP and its mother
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
     if (fextFile && *fextFile){im+=1;};
     cpg->AddTrack((Int_t)fPythia->event[k].id(),px,py,pz,xS/cm,yS/cm,zS/cm,im,wanttracking,e,tS/cm/c_light,w);
     // std::cout <<k<< " insert pdg =" <<fPythia->event[k].id() << " pz = " << pz << " [GeV] zS = " << zS << " [mm] tS = " << tS << "[mm/c]" <<  std::endl;
   }
   return kTRUE;
}
// -------------------------------------------------------------------------
void DPPythia8Generator::SetParameters(char* par)
{
  // Set Parameters
   fPythia->readString(par);
    if ( debug ){std::cout<<"fPythia->readString(\""<<par<<"\")"<<std::endl;}
} 

// -------------------------------------------------------------------------

ClassImp(DPPythia8Generator)
