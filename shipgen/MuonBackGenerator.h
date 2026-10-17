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

class FairMCEventHeader;
class FairPrimaryGenerator;
class ShipMCTrack;
class TTree;
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
  // Attach the muBack_src* branches, the input event of each output event, to
  // an empty output tree before the run; this generator must outlive it.
  Bool_t RegisterOutputBranches(TTree* tree);

 private:
  // Bind the input MCEventHeader for the file the chain has just loaded.
  void BindInputHeader();

 protected:
  Float_t id, parentid, pythiaid, w, px, py, pz, vx, vy, vz, ecut;
  TClonesArray* MCTrack;                   //!
  TClonesArray* vetoPoints;                //!
  std::vector<ShipMCTrack>* MCTrack_vec;   //!
  std::vector<vetoPoint>* vetoPoints_vec;  //!
  Bool_t fUseSTL;  //! flag to indicate if using STL vectors
  TChain* fTree;   //!
  int fNevents;
  float f_zOffset;  //!
  int fn;
  Bool_t fPhiRandomize;
  Double_t fPaintBeam;
  Bool_t fdownScaleDiMuon;
  Bool_t followMuons;
  Int_t fSameSeed;
  Double_t fsmearBeam;
  // Input event of the current output event, -1 where unknown.
  Int_t fSrcFile = -1;                     //! file index in the input chain
  Long64_t fSrcEntry = -1;                 //! entry in that file
  Long64_t fSrcRunID = -1;                 //! input MCEventHeader RunID
  Long64_t fSrcEventID = -1;               //! input MCEventHeader EventID
  FairMCEventHeader* fInHeader = nullptr;  //! input header, cbmsim input only
  Int_t fInHeaderTree = -1;                //! chain file fInHeader is bound to
  Bool_t fHasInHeader = false;             //! that file has an MCEventHeader
};

#endif  // SHIPGEN_MUONBACKGENERATOR_H_ /* !PNDmuGENERATOR_H */
