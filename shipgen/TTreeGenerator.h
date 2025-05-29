// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#ifndef SHIPGEN_TTREEGENERATOR_H_
#define SHIPGEN_TTREEGENERATOR_H_

#include "FairPrimaryGenerator.h"
#include "Generator.h"
#include "TFile.h"
#include "TString.h"
#include "TTree.h"

class FairPrimaryGenerator;

namespace SHiP {

/**
 * @class TTreeGenerator
 * @brief A FairRoot generator that reads particle data from ROOT TTrees
 *
 * The expected TTree structure contains the following branches:
 * - px, py, pz: Particle momentum components (GeV/c)
 * - x, y, z: Particle position coordinates (cm)
 * - id: PDG particle identification code
 * - w: Event weight factor
 */
class TTreeGenerator : public Generator {
 public:
  TTreeGenerator();
  ~TTreeGenerator() override;

  using Generator::Init;
  Bool_t Init(const char* fileName, int startEvent) override;
  Bool_t Init(const char* fileName) override;
  Bool_t ReadEvent(FairPrimaryGenerator* primGen) override;

  Long64_t GetNEvents() const { return fNEvents; }
  Long64_t GetCurrentEvent() const { return fCurrentEvent; }
  void SetTreeName(const char* treeName) { fTreeName = treeName; }

 private:
  TFile* fInputFile;  //!< Input ROOT file pointer
  TTree* fInputTree;  //!< Input TTree pointer
  TString fTreeName;  //!< Name of the TTree to read

  Long64_t fNEvents;       //!< Total number of events in the tree
  Long64_t fCurrentEvent;  //!< Current event index (0-based)

  Double_t fPx;      //!< Particle momentum x-component (GeV/c)
  Double_t fPy;      //!< Particle momentum y-component (GeV/c)
  Double_t fPz;      //!< Particle momentum z-component (GeV/c)
  Double_t fX;       //!< Particle position x-coordinate (cm)
  Double_t fY;       //!< Particle position y-coordinate (cm)
  Double_t fZ;       //!< Particle position z-coordinate (cm)
  Int_t fPdgId;      //!< PDG particle identification code
  Double_t fWeight;  //!< Event weight factor

  void InitBranches();
};

}  // namespace SHiP

#endif  // SHIPGEN_TTREEGENERATOR_H_
