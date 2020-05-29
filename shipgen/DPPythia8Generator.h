#ifndef DPP8GENERATOR_H
#define DPP8GENERATOR_H 1
// Avoid the inclusion of dlfcn.h by Pyhtia.h that CINT is not able to process
//#ifdef __CINT__
//#define _DLFCN_H_
//#define _DLFCN_H
//#endif

#include "TROOT.h"
#include "TString.h"
#include "TFile.h"
#include "TTree.h"
#include "TH2F.h"
#include "FairGenerator.h"
#include "Pythia8/Pythia.h"
#include "TRandom1.h"
#include "TRandom3.h"
#include "FairLogger.h"                 // for FairLogger, MESSAGE_ORIGIN
#include "HNLPythia8Generator.h"

class FairPrimaryGenerator;

class DPPythia8Generator : public FairGenerator
{
 public:
  
  /** default constructor **/
  DPPythia8Generator();
  
  /** destructor **/
  virtual ~DPPythia8Generator();
  
  /** public method ReadEvent **/
  Bool_t ReadEvent(FairPrimaryGenerator*);
  void SetParameters(char*);
  void Print(){fPythia->settings.listAll(); };  //!
  void List(int id){fPythia->particleData.list(id);}; //!
  
  //void SetDecayToHadrons(){
  //std::cout << " INFO: Adding decay to hadrons." << std::endl;
  //fHadDecay = true; 
  //};

  virtual Bool_t Init(); //!
  
  void SetMom(Double_t mom) { fMom = mom; };
  Double_t GetMom() { return fMom; };
  void SetId(Double_t id) { fId  = id; };
  void SetDPId(Int_t id) { fDP = id; };
  Int_t GetDPId() { return fDP; };
  void SetLmin(Double_t z) { fLmin = z*10; };
  void SetLmax(Double_t z) { fLmax = z*10; };
  void SetSmearBeam(Double_t sb) { fsmearBeam = sb; };
  void SetfFDs(Double_t z) { fFDs = z; };
  void UseRandom1() { fUseRandom1 = kTRUE; fUseRandom3 = kFALSE; };
  void UseRandom3() { fUseRandom1 = kFALSE; fUseRandom3 = kTRUE; };
  void UseExternalFile(const char* x, Int_t i){ fextFile   = x; firstEvent=i; };
  void SetPbrem(TH2F *pdf) {
    fpbrem = kTRUE;
    fpbremPDF = pdf;
  };
  Bool_t IsPbrem() { return fpbrem; };
  void SetDY(){
    fdy = kTRUE;
  };

  Double_t MinDPMass() { return fDPminM; };
  void SetMinDPMass(Double_t m){
    fDPminM = m;
  };

  void UseDeepCopy(){ fDeepCopy   = kTRUE; };
  Int_t nrOfRetries(){ return fnRetries; };
  Int_t nrOfDP(){ return fnDPtot; };
  Pythia8::Pythia* getPythiaInstance(){return fPythia;};
  Pythia8::Pythia* fPythia;             //!
  //Pythia8::Pythia* fPythiaHadDecay;             //!
 private:
  
 Pythia8::RndmEngine* fRandomEngine;  //!
   
 protected:

  //Bool_t fHadDecay;    //select hadronic decay
  Double_t fMom;       // proton energy
  Int_t    fDP;       // DP ID
  Int_t    fId;        // target type
  Bool_t fUseRandom1;  // flag to use TRandom1
  Bool_t fUseRandom3;  // flag to use TRandom3 (default)
  Bool_t fpbrem;       //flag to do proton bremstrahlung production (default is false)
  TH2F *fpbremPDF;     // pointer to TH2 containing PDF(p,theta) to have a dark photon with momentum p and angle theta to be produced by pbrem.
  Bool_t fdy;          // flag to do Drell-Yan QCD production
  Double_t fDPminM;    //Minimum mass, in GeV, for the DP produced in ffbar to DP QCD production.
  Double_t fLmin;      // m minimum  decay position z
  Double_t fLmax;      // m maximum decay position z
  Int_t fnRetries;     // number of events without any DP 
  Int_t fnDPtot;       // total number of DP from multiple mesons in single collision
  Double_t fctau;      // dark photon lifetime 
  Double_t fFDs;       // correction for Pythia6 to match measured Ds production
  Double_t fsmearBeam; // finite beam size
  const char* fextFile; // read charm and beauty hadrons from external file, decay with Pythia
  TFile* fInputFile;   //! pointer to a file
  TTree* fTree;        //! 
  Int_t  fNevents,fn,firstEvent,fShipEventNr;
  Float_t hpx[1], hpy[1], hpz[1], hE[1],hM[1],mpx[1], mpy[1], mpz[1], mE[1],hid[1], mid[1];
  Bool_t fDeepCopy;    // not used
  FairLogger*  fLogger; //!   don't make it persistent, magic ROOT command

  ClassDef(DPPythia8Generator,2);
};

#endif /* !PNDH8GENERATOR_H */
