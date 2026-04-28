// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#ifndef SHIPGEN_GENIEGENERATOR_H_
#define SHIPGEN_GENIEGENERATOR_H_

#include "FairLogger.h"  // for FairLogger, MESSAGE_ORIGIN
#include "Generator.h"
#include "TF1.h"  // for TF1
#include "TH1.h"  // for TH1
#include "TH2.h"  // for TH2
#include "TROOT.h"
#include "TTree.h"  // for TTree
#include "TVector3.h"
#include "vector"

class FairPrimaryGenerator;

class GenieGenerator : public SHiP::Generator {
 public:
  /** default constructor **/
  GenieGenerator();

  /** destructor **/
  ~GenieGenerator() override;

  /** public method ReadEvent **/
  using SHiP::Generator::Init;
  Bool_t OldReadEvent(FairPrimaryGenerator*);
  Bool_t ReadEvent(FairPrimaryGenerator*) override;
  Bool_t Init(const char*, int) override;
  Bool_t Init(const char*) override;
  Int_t GetNevents();
  void NuOnly() { fNuOnly = true; }
  void SetPositions(Double_t zTa, Double_t zS = -3400., Double_t zE = 2650.) {
    ztarget = zTa;
    startZ = zS;
    endZ = zE;
  }
  void AddBox(TVector3 dVec, TVector3 box);
  Long64_t GetGeneratedEvents() const { return fGeneratedEvents; }
  Long64_t GetCCEvents() const { return fCCEvents; }
  Long64_t GetNuEElasticEvents() const { return fNuEElasticEvents; }
  Long64_t GetInteractionSamplingTrials() const { return fInteractionSamplingTrials; }
  Long64_t GetOutgoingLeptonsStored() const { return fOutgoingLeptonsStored; }
  Long64_t GetOutgoingHadronsStored() const { return fOutgoingHadronsStored; }

 private:
  std::vector<double> Rotate(Double_t x, Double_t y, Double_t z, Double_t px,
                             Double_t py, Double_t pz);

 private:
 protected:
  Double_t Yvessel, Xvessel, Lvessel, ztarget, startZ, endZ;
  Double_t Ev, pxv, pyv, pzv, El, pxl, pyl, pzl, vtxx, vtxy, vtxz, vtxt;
  Double_t Ef[500], pxf[500], pyf[500], pzf[500];
  Int_t pdgf[500];
  std::vector<TVector3> dVecs;
  std::vector<TVector3> m_boxes;
  Bool_t cc, nuel;
  Int_t nf, neu;
  FairLogger* fLogger;  //!   don't make it persistent, magic ROOT command
  TFile* fInputFile;
  TTree* fTree;
  int fNevents;
  int fn;
  bool fFirst, fNuOnly;
  Long64_t fGeneratedEvents;
  Long64_t fCCEvents;
  Long64_t fNuEElasticEvents;
  Long64_t fInteractionSamplingTrials;
  Long64_t fOutgoingLeptonsStored;
  Long64_t fOutgoingHadronsStored;
  Double_t fznu0, fznu11, fXnu11, fYnu11;
  Double_t fEntrDz_inner, fEntrDz_outer, fEntrZ_inner, fEntrZ_outer, fEntrA,
      fEntrB, fL1z, fScintDz;
  TH1D* pxhist[3000];        //!
  TH1D* pyslice[3000][100];  //!
};

#endif  // SHIPGEN_GENIEGENERATOR_H_ /* !PNDGeGENERATOR_H */
