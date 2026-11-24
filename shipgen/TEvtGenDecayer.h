// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#ifndef SHIPGEN_TEVTGENDECAYER_H_
#define SHIPGEN_TEVTGENDECAYER_H_

// External decayer for the VMC: EvtGen decays the particles registered with
// AddEvtGenParticle (e.g. J/psi), Pythia8 decays all others.

#include <memory>
#include <vector>

#include "TString.h"
#include "TVirtualMCDecayer.h"

class TClonesArray;
class TLorentzVector;
class EvtGen;
class EvtParticle;
namespace Pythia8 {
class Pythia;
}

class TEvtGenDecayer : public TVirtualMCDecayer {
 public:
  TEvtGenDecayer();
  ~TEvtGenDecayer() override;

  void Init() override;
  void Decay(Int_t pdg, TLorentzVector* p) override;
  Int_t ImportParticles(TClonesArray* particles) override;
  void SetForceDecay(Int_t type) override;
  void ForceDecay() override;
  Float_t GetPartialBranchingRatio(Int_t ipart) override;
  Float_t GetLifetime(Int_t kf) override;
  void ReadDecayTable() override;

  // EvtGen-specific methods
  void SetEvtGenDecayFile(const char* decayFile);
  void SetEvtGenParticleFile(const char* particleFile);
  void AddEvtGenParticle(Int_t pdg);  // Add particle to be handled by EvtGen

  // Pythia8 settings for the fallback decayer, applied by Init(). Call before
  // Init(); later settings need another Pythia8::Pythia::init().
  bool ReadString(const char* setting);
  Pythia8::Pythia* GetPythia() { return fPythia.get(); }

 protected:
  Bool_t UseEvtGenForParticle(Int_t pdg);
  void DecayWithEvtGen(Int_t pdg, TLorentzVector* p);
  void DecayWithPythia8(Int_t pdg, TLorentzVector* p);
  void ConvertEvtGenDecay(EvtParticle* parent);

 private:
  std::unique_ptr<Pythia8::Pythia> fPythia;  //! Decays non-EvtGen particles
  EvtGen* fEvtGen;                           // EvtGen instance
  TString fDecayFile;                        // EvtGen DECAY.DEC file
  TString fParticleFile;                     // EvtGen particle data file
  std::vector<Int_t>
      fEvtGenParticles;  // List of PDG codes to handle with EvtGen

  // Storage for EvtGen decay products
  TClonesArray* fEvtGenProducts;  // Array to store converted EvtGen particles
  Bool_t fHasEvtGenDecay;  // Flag indicating if last decay was from EvtGen
};

#endif  // SHIPGEN_TEVTGENDECAYER_H_
