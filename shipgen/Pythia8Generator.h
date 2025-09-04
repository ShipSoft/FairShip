#ifndef SHIPGEN_PYTHIA8GENERATOR_H_
#define SHIPGEN_PYTHIA8GENERATOR_H_

#include "TROOT.h"
#include "FairGenerator.h"
#include "Pythia8/Pythia.h"
#include "FairLogger.h"                 // for FairLogger, MESSAGE_ORIGIN
#include "TTree.h"
#include "GenieGenerator.h"

class FairPrimaryGenerator;

class Pythia8Generator : public FairGenerator
{
 public:

  /** default constructor **/
  Pythia8Generator();

  /** destructor **/
  virtual ~Pythia8Generator();

  /** public method ReadEvent **/
  Bool_t ReadEvent(FairPrimaryGenerator*);
  void SetParameters(char*);
  void Print(); //!

  virtual Bool_t Init(); //!

  void SetMom(Double_t mom) { fMom = mom; };
  void SetId(Double_t id) { fId  = id; };
  void UseRandom1() { fUseRandom1 = kTRUE; fUseRandom3 = kFALSE; };
  void UseRandom3() { fUseRandom1 = kFALSE; fUseRandom3 = kTRUE; };
  void UseExternalFile(const char* x, Int_t i){ fextFile   = x; firstEvent=i; };
  void SetfFDs(Double_t z) { fFDs = z; };
  void SetTarget(TString s, Double_t x,Double_t y ) { targetName = s; xOff=x; yOff=y; };
  void SetTargetCoordinates(Double_t start_z, Double_t end_z)
  {
      startZ = start_z;
      endZ = end_z;
      targetFromGeometry = true;
  };
  Int_t nrOfRetries(){ return fnRetries; };

 private:

#if PYTHIA_VERSION_INTEGER >= 8300
  std::shared_ptr<Pythia8::RndmEngine> fRandomEngine;  //!
#else
  Pythia8::RndmEngine* fRandomEngine;  //!
#endif

 protected:

  Double_t fMom;       // proton momentum
  Int_t    fId;       // target type
  Bool_t fUseRandom1;  // flag to use TRandom1
  Bool_t fUseRandom3;  // flag to use TRandom3 (default)
  const char* fextFile; // read charm and beauty hadrons from external file, decay with Pythia
  Float_t hpx[1], hpy[1], hpz[1], hE[1],hM[1],mpx[1], mpy[1], mpz[1], mE[1],hid[1], mid[1],ck[1];
  Float_t ancestors[16],subprocCodes[16];
  Int_t  fNevents,fn,firstEvent,fShipEventNr;
  TFile* fInputFile;   //! pointer to a file
  FairLogger*  fLogger; //!   don't make it persistent, magic ROOT command
  TTree* fTree;        //!
  Pythia8::Pythia* fPythia;             //!
  Double_t fFDs;       // correction for Pythia6 to match measured Ds production
  Int_t fnRetries;     //
  GenieGenerator* fMaterialInvestigator;  //!
  ClassDef(Pythia8Generator,3);
  TString targetName;
  Double_t xOff;
  Double_t yOff;
  Double_t start[3];
  Double_t end[3];
  Double_t bparam;
  Double_t mparam[10];
  Double_t startZ;
  Double_t endZ;
  Bool_t targetFromGeometry;   // flag to indicate coordinates set from geometry
  Double_t maxCrossSection;
};

#endif  // SHIPGEN_PYTHIA8GENERATOR_H_ /* !PNDP8GENERATOR_H */
