// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#ifndef SHIPGEN_MUONBACKGENERATOR_H_
#define SHIPGEN_MUONBACKGENERATOR_H_

#include <vector>

#include "FairLogger.h"  // for FairLogger, MESSAGE_ORIGIN
#include "Generator.h"
#include "TChain.h"  // for TChain
#include "TClonesArray.h"
#include "TROOT.h"

class FairPrimaryGenerator;
class ShipMCTrack;
class vetoPoint;

class MuonBackGenerator : public SHiP::Generator {
 public:
  /** default constructor **/
  MuonBackGenerator();

  /** destructor **/
  ~MuonBackGenerator() override;

  /** public method ReadEvent **/
  Bool_t ReadEvent(FairPrimaryGenerator*) override;
  Bool_t Init(const char*, int) override;
  Bool_t Init(const char*) override;
  Bool_t Init(const std::vector<std::string>&, int) override;
  Bool_t Init(const std::vector<std::string>&) override;

  Int_t GetNevents();
  void CloseFile();
  void FollowAllParticles() { followMuons = false; };
  void SetSmearBeam(Double_t sb) { fsmearBeam = sb; };
  void SetPaintRadius(Double_t r) { fPaintBeam = r; };
  void SetSameSeed(Int_t s) {
    LOGF(info, "Seed: %d", s);
    fSameSeed = s;
  };
  void SetPhiRandomize(Bool_t phiRandomize) { fPhiRandomize = phiRandomize; };
  Bool_t checkDiMuon(Int_t muIndex);
  void SetDownScaleDiMuon() { fdownScaleDiMuon = kTRUE; };
  Long64_t GetScannedEntries() const { return fScannedEntries; }
  Long64_t GetAcceptedEntries() const { return fAcceptedEntries; }
  Long64_t GetSelectedMuons() const { return fSelectedMuons; }
  Long64_t GetTransportedTracks() const { return fTransportedTracks; }

 private:
 protected:
  Float_t id, parentid, pythiaid, w, px, py, pz, vx, vy, vz, ecut;
  TClonesArray* MCTrack;                   //!
  TClonesArray* vetoPoints;                //!
  std::vector<ShipMCTrack>* MCTrack_vec;   //!
  std::vector<vetoPoint>* vetoPoints_vec;  //!
  Bool_t fUseSTL;     //! flag to indicate if using STL vectors
  TFile* fInputFile;  //!
  TChain* fTree;      //!
  int fNevents;
  float f_zOffset;  //!
  int fn;
  Bool_t fPhiRandomize;
  Double_t fPaintBeam;
  Bool_t fdownScaleDiMuon;
  Bool_t followMuons;
  Int_t fSameSeed;
  Double_t fsmearBeam;
  Long64_t fScannedEntries;
  Long64_t fAcceptedEntries;
  Long64_t fSelectedMuons;
  Long64_t fTransportedTracks;
};

#endif  // SHIPGEN_MUONBACKGENERATOR_H_ /* !PNDmuGENERATOR_H */
