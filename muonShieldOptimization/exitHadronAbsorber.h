// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#ifndef MUONSHIELDOPTIMIZATION_EXITHADRONABSORBER_H_
#define MUONSHIELDOPTIMIZATION_EXITHADRONABSORBER_H_

#include "Detector.h"
#include "TFile.h"
#include "TNtuple.h"
#include "vetoPoint.h"
#include <set>

class FairVolume;

struct TrackBuffer {
    Int_t pdg;
    Double_t px, py, pz, e;
    Double_t x, y, z, t;
    Double_t polx, poly, polz;
    Double_t weight;
    Int_t parentID;
};

class exitHadronAbsorber : public SHiP::Detector<vetoPoint> {
 public:
  exitHadronAbsorber(const char* Name, Bool_t Active);
  exitHadronAbsorber();

  void Initialize() override;

  Bool_t ProcessHits(FairVolume* v = nullptr) override;

  void Register() override;

  void ConstructGeometry() override;

  void FinishRun() override;
  void PreTrack() override;
  virtual void PostTrack();
  virtual void BeginEvent();

  inline void SetEnergyCut(Float_t emax) { EMax = emax; }
  inline void SetOnlyMuons() { fOnlyMuons = kTRUE; }
  inline void SetOpt4DP() { withNtuple = kTRUE; }
  inline void SkipNeutrinos() { fSkipNeutrinos = kTRUE; }
  inline void SetZposition(Float_t x) { fzPos = x; }
  inline void SetVetoPointName(TString name) { fVetoName = name; }
  inline void SetCylindricalPlane() { fCylindricalPlane = kTRUE; }
  inline void SetUseCaveCoordinates() { fUseCaveCoordinates = kTRUE; }

 private:
  Int_t fUniqueID;
  Bool_t fOnlyMuons;         //! flag if only muons should be stored
  Bool_t fSkipNeutrinos;     //! flag if neutrinos should be ignored
  TString fVetoName;         // name to save veto collection
  Double_t fzPos;            //!  zPos, optional
  Bool_t withNtuple;         //! special option for Dark Photon physics studies
  TNtuple* fNtuple;          //!
  Float_t EMax;              //! max energy to transport
  Bool_t fCylindricalPlane;  //! cylindrical sensPlane flag
  Bool_t fUseCaveCoordinates;  //! set position from cave

  int32_t fNsplits;
  std::vector<TrackBuffer> fSecondaryBuffer;
  std::set<Int_t> fCloneTracks;


  TFile* fout;               //!
  TClonesArray* fElectrons;  //!
  Int_t index;
  ClassDefOverride(exitHadronAbsorber, 0)
};

#endif  // MUONSHIELDOPTIMIZATION_EXITHADRONABSORBER_H_
