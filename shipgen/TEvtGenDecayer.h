#ifndef SHIPGEN_TEVTGENDECAYER_H_
#define SHIPGEN_TEVTGENDECAYER_H_

// Custom external decayer that uses EvtGen for specific particles (like J/psi)
// and falls back to TPythia8Decayer for others

#include "TVirtualMCDecayer.h"
#include "TPythia8Decayer.h"
#include "TString.h"
#include <vector>

class TClonesArray;
class TLorentzVector;
class EvtGen;
class EvtParticle;

class TEvtGenDecayer : public TVirtualMCDecayer {
public:
   TEvtGenDecayer();
   ~TEvtGenDecayer() override;

   void    Init() override;
   void    Decay(Int_t pdg, TLorentzVector* p) override;
   Int_t   ImportParticles(TClonesArray *particles) override;
   void    SetForceDecay(Int_t type) override;
   void    ForceDecay() override;
   Float_t GetPartialBranchingRatio(Int_t ipart) override;
   Float_t GetLifetime(Int_t kf) override;
   void    ReadDecayTable() override;

   // EvtGen-specific methods
   void    SetEvtGenDecayFile(const char* decayFile);
   void    SetEvtGenParticleFile(const char* particleFile);
   void    AddEvtGenParticle(Int_t pdg);  // Add particle to be handled by EvtGen

   // Access methods
   TPythia8Decayer* GetPythia8Decayer() { return fPythia8Decayer; }


protected:
   Bool_t  UseEvtGenForParticle(Int_t pdg);
   void    DecayWithEvtGen(Int_t pdg, TLorentzVector* p);
   void    DecayWithPythia8(Int_t pdg, TLorentzVector* p);
   void    ConvertEvtGenDecay(EvtParticle* parent);

private:
   TPythia8Decayer* fPythia8Decayer;    // Fallback decayer for non-EvtGen particles
   EvtGen*          fEvtGen;            // EvtGen instance
   TString          fDecayFile;         // EvtGen DECAY.DEC file
   TString          fParticleFile;      // EvtGen particle data file
   std::vector<Int_t> fEvtGenParticles; // List of PDG codes to handle with EvtGen

   // Storage for EvtGen decay products
   TClonesArray*    fEvtGenProducts;    // Array to store converted EvtGen particles
   Bool_t           fHasEvtGenDecay;    // Flag indicating if last decay was from EvtGen

   ClassDefOverride(TEvtGenDecayer, 1)  // External decayer using EvtGen for specific particles
};

#endif  // SHIPGEN_TEVTGENDECAYER_H_
