// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#ifndef SHIPGEN_HNLPYTHIA8GENERATOR_H_
#define SHIPGEN_HNLPYTHIA8GENERATOR_H_

#include "FairLogger.h"  // for FairLogger, MESSAGE_ORIGIN
#include "Generator.h"
#include "Pythia8/Pythia.h"
#include "TFile.h"
#include "TROOT.h"
#include "TRandom1.h"
#include "TRandom3.h"
#include "TString.h"
#include "TTree.h"

class FairPrimaryGenerator;

class PyTr1Rng : public Pythia8::RndmEngine {
 public:
  PyTr1Rng() { rng = new TRandom1(gRandom->GetSeed()); };
  virtual ~PyTr1Rng() {};

  Double_t flat() { return rng->Rndm(); };

 private:
  TRandom1* rng;  //!
};

class PyTr3Rng : public Pythia8::RndmEngine {
 public:
  PyTr3Rng() { rng = new TRandom3(gRandom->GetSeed()); };
  virtual ~PyTr3Rng() {};

  Double_t flat() { return rng->Rndm(); };

 private:
  TRandom3* rng;  //!
};

class HNLPythia8Generator : public SHiP::Generator {
 public:
  /** default constructor **/
  HNLPythia8Generator();

  /** destructor **/
  virtual ~HNLPythia8Generator();

  /** public method ReadEvent **/
  Bool_t ReadEvent(FairPrimaryGenerator*) override;
  void SetParameters(char*);
  void Print() { fPythia->settings.listAll(); };
  void List(int id) { fPythia->particleData.list(id); };

  using SHiP::Generator::Init;

  Bool_t Init(const char* inFile) override { return Init(inFile, 0); };

  Bool_t Init(const char* inFile, int startEvent) override {
    LOG(warning) << "Init with files not implemented for HNLPythia8Generator. "
                    "Using default Init() instead";
    return Init();
  };
  Bool_t Init() override;

  void SetMom(Double_t mom) { fMom = mom; };
  void SetId(Double_t id) { fId = id; };
  void SetHNLId(Int_t id) { fHNL = id; };
  void SetLmin(Double_t z) { fLmin = z * 10; };  // Conversion from cm to mm
  void SetLmax(Double_t z) { fLmax = z * 10; };  // Conversion from cm to mm
  void SetSmearBeam(Double_t sb) {
    fsmearBeam = sb * 10;
  };  // Conversion from cm to mm
  void SetPaintRadius(Double_t r) {
    fPaintBeam = r * 10;
  };  // Conversion from cm to mm
  void SetfFDs(Double_t z) { fFDs = z; };
  void UseRandom1() {
    fUseRandom1 = kTRUE;
    fUseRandom3 = kFALSE;
  };
  void UseRandom3() {
    fUseRandom1 = kFALSE;
    fUseRandom3 = kTRUE;
  };

  void UseDeepCopy() { fDeepCopy = kTRUE; };
  Int_t nrOfRetries() { return fnRetries; };
  Pythia8::Pythia* getPythiaInstance() { return fPythia; };
  Pythia8::Pythia* fPythia;  //!
 private:
#if PYTHIA_VERSION_INTEGER >= 8300
  std::shared_ptr<Pythia8::RndmEngine> fRandomEngine;
#else
  Pythia8::RndmEngine* fRandomEngine;  //!
#endif

 protected:
  Double_t fMom;       // proton momentum
  Int_t fHNL;          // HNL ID
  Int_t fId;           // target type
  Bool_t fUseRandom1;  // flag to use TRandom1
  Bool_t fUseRandom3;  // flag to use TRandom3 (default)
  Double_t fLmin;      // m minimum  decay position z
  Double_t fLmax;      // m maximum decay position z
  Int_t fnRetries;     // number of events without any HNL
  Double_t fctau;      // hnl lifetime
  Double_t fFDs;       // correction for Pythia6 to match measured Ds production
  Double_t fsmearBeam;  // finite beam size
  Double_t fPaintBeam;  // beam painting radius
  TFile* fInputFile;    //! pointer to a file
  TTree* fTree;         //!
  Int_t fNevents, fn, fShipEventNr;
  Float_t hpx[1], hpy[1], hpz[1], hE[1], hM[1], mpx[1], mpy[1], mpz[1], mE[1],
      hid[1], mid[1];
  Bool_t fDeepCopy;     // not used
  FairLogger* fLogger;  //!   don't make it persistent, magic ROOT command

  ClassDefOverride(HNLPythia8Generator, 7);
};

#endif  // SHIPGEN_HNLPYTHIA8GENERATOR_H_
