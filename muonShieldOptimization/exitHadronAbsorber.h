// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#ifndef MUONSHIELDOPTIMIZATION_EXITHADRONABSORBER_H_
#define MUONSHIELDOPTIMIZATION_EXITHADRONABSORBER_H_

#include "Detector.h"
#include "TFile.h"
#include "TNtuple.h"
#include "vetoPoint.h"

class FairVolume;

<<<<<<< HEAD
class exitHadronAbsorber : public SHiP::Detector<vetoPoint> {
=======
struct TrackBuffer {
    Int_t pdg;
    Double_t px, py, pz, e;
    Double_t x, y, z, t;
    Double_t polx, poly, polz;
    Double_t weight;
    Int_t parentID;
};

class exitHadronAbsorber : public FairDetector, public ISTLPointContainer {
>>>>>>> 8e56f36c6 (Pion-kaon splitting in exitHadronAbsorber)
 public:
  exitHadronAbsorber(const char* Name, Bool_t Active);
  exitHadronAbsorber();

  void Initialize() override;

  Bool_t ProcessHits(FairVolume* v = nullptr) override;

  void Register() override;

  void ConstructGeometry() override;

  void FinishRun() override;
  void PreTrack() override;

<<<<<<< HEAD
  inline void SetEnergyCut(Float_t emax) { EMax = emax; }
=======
  /**      has to be called after each event to reset the containers      */
  virtual void Reset();

  /**      Update track indices in points after track pruning      */
  void UpdatePointTrackIndices(const std::map<Int_t, Int_t>& indexMap);

  /**      Create the detector geometry        */
  void ConstructGeometry();

  /** The following methods can be implemented if you need to make
   *  any optional action in your detector during the transport.
   */

  virtual void CopyClones(TClonesArray* cl1, TClonesArray* cl2, Int_t offset) {
    ;
  }
  virtual void SetSpecialPhysicsCuts() { ; }
  virtual void EndOfEvent();
  virtual void FinishPrimary() { ; }
  virtual void FinishRun();
  virtual void BeginPrimary() { ; }
  virtual void PreTrack();
  virtual void PostTrack();
  // virtual void Stepping();
  virtual void BeginEvent();  //  { ; }

  vetoPoint* AddHit(Int_t eventID, Int_t trackID, Int_t detID, TVector3 pos,
                    TVector3 mom, Double_t time, Double_t length,
                    Double_t eLoss, Int_t pdgcode, TVector3 Lpos,
                    TVector3 Lmom);
  inline void SetEnergyCut(Float_t emax) {
    EMax = emax;
  }  // min energy to be copied to Geant4
>>>>>>> 8e56f36c6 (Pion-kaon splitting in exitHadronAbsorber)
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
<<<<<<< HEAD
  Bool_t fCylindricalPlane;  //! cylindrical sensPlane flag
  Bool_t fUseCaveCoordinates;  //! set position from cave
=======
  int32_t fNsplits;
  std::vector<TrackBuffer> fSecondaryBuffer;
  bool fIsSplitting;

  Bool_t fCylindricalPlane;  //! flag if the sensPlane to be created should be
                             //! cylindrical (by default it is not)
  Bool_t fUseCaveCoordinates;  //! set position from cave rather than from muon
                               //! shield, default is false
>>>>>>> 8e56f36c6 (Pion-kaon splitting in exitHadronAbsorber)

  TFile* fout;               //!
  TClonesArray* fElectrons;  //!
  Int_t index;
<<<<<<< HEAD
  ClassDefOverride(exitHadronAbsorber, 0)
=======
  /** container for data points */
  std::vector<vetoPoint>* fexitHadronAbsorberPointCollection;

  ClassDef(exitHadronAbsorber, 0)
>>>>>>> 8e56f36c6 (Pion-kaon splitting in exitHadronAbsorber)
};

#endif  // MUONSHIELDOPTIMIZATION_EXITHADRONABSORBER_H_
