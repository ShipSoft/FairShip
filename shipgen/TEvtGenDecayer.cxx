// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#include "TEvtGenDecayer.h"

#include "FairLogger.h"
#include "TClonesArray.h"
#include "TLorentzVector.h"
#include "TMCProcess.h"
#include "TParticle.h"
#include "TRandom.h"
#include "TSystem.h"

// Pythia8 includes
#include "Pythia8/Pythia.h"

// EvtGen includes
#include "EvtGen/EvtGen.hh"
#include "EvtGenBase/EvtAbsRadCorr.hh"
#include "EvtGenBase/EvtId.hh"
#include "EvtGenBase/EvtMTRandomEngine.hh"
#include "EvtGenBase/EvtPDL.hh"
#include "EvtGenBase/EvtParticle.hh"
#include "EvtGenBase/EvtParticleFactory.hh"
#include "EvtGenBase/EvtRandom.hh"
#include "EvtGenBase/EvtVector4R.hh"
#include "EvtGenExternal/EvtExternalGenList.hh"

namespace {
// Pythia8 gives vertices in mm and times in mm/c, TParticle in cm and s.
constexpr double kMmToCm = 0.1;
constexpr double kMmOverCToS = 1e-3 / 299792458.;
// Pythia8 accepts Random:seed in [1, 900000000]; 0 and negative values mean
// a time-based and the default seed respectively.
constexpr UInt_t kPythiaMaxSeed = 900000000;
// Products with a proper lifetime above this (c tau0 in mm) are handed back
// to the VMC undecayed: weakly decaying hadrons and tau fly and decay in
// the transport, strong and electromagnetic decays happen in Pythia8.
constexpr double kMaxTau0 = 1e-3;
}  // namespace

//_____________________________________________________________________________
TEvtGenDecayer::TEvtGenDecayer()
    : TVirtualMCDecayer(),
      fPythia(std::make_unique<Pythia8::Pythia>()),
      fEvtGen(nullptr),
      fDecayFile(""),
      fParticleFile(""),
      fEvtGenProducts(nullptr),
      fHasEvtGenDecay(kFALSE) {
  // Default constructor
  fEvtGenParticles.clear();
  fEvtGenProducts = new TClonesArray("TParticle");
  // Decays only: no hard process, no beams.
  fPythia->readString("ProcessLevel:all = off");
}

//_____________________________________________________________________________
TEvtGenDecayer::~TEvtGenDecayer() {
  // Destructor
  if (fEvtGen) delete fEvtGen;
  if (fEvtGenProducts) delete fEvtGenProducts;
}

//_____________________________________________________________________________
void TEvtGenDecayer::Init() {
  // Initialize both EvtGen and Pythia8 decayers

  // Both generators are seeded from ROOT's random number generator, so that
  // jobs with different seeds get different decays.
  UInt_t seed = gRandom->GetSeed();

  // Initialize the Pythia8 decayer
  const UInt_t pythiaSeed = seed == 0 ? 1 : 1 + (seed - 1) % kPythiaMaxSeed;
  fPythia->readString("Random:setSeed = on");
  fPythia->readString(Form("Random:seed = %u", pythiaSeed));
  if (!fPythia->init()) {
    LOG(fatal) << "TEvtGenDecayer: Pythia8 initialisation failed";
  }
  LOG(info) << "TEvtGenDecayer: Pythia8 seeded with " << pythiaSeed;

  // Keep weakly decaying products (strange, charm and bottom hadrons, tau)
  // for the transport, which decays them where they actually decay.
  // ParticleDecays:limitTau0 cannot be used: it would also keep the particle
  // that the transport asks to decay.
  for (auto& [id, entry] : fPythia->particleData) {
    if (entry->tau0() > kMaxTau0) entry->setMayDecay(false);
  }

  // Initialize EvtGen if decay files are specified
  if (fDecayFile != "" && fParticleFile != "") {
    // Set up EvtGen random engine with ROOT's random number generator seed
    EvtRandomEngine* randomEngine = new EvtMTRandomEngine(seed);
    EvtRandom::setRandomEngine(randomEngine);

    LOG(info) << "TEvtGenDecayer: Random engine initialized with seed " << seed;

    // Set up external generators with PHOTOS radiative corrections
    std::string photonType("gamma");
    bool useEvtGenRandom(true);
    bool convertPythiaCodes(false);
    std::string pythiaDir("");

    EvtExternalGenList* externalGenList = new EvtExternalGenList(
        convertPythiaCodes, pythiaDir, photonType, useEvtGenRandom);

    // Get the interface to the radiative correction engine (PHOTOS)
    EvtAbsRadCorr* radCorrEngine = externalGenList->getPhotosModel();
    if (radCorrEngine) {
      LOG(info) << "TEvtGenDecayer: PHOTOS radiative corrections enabled";
    } else {
      LOG(warning) << "TEvtGenDecayer: PHOTOS not available, proceeding "
                      "without radiative corrections";
    }

    // Get the interface to other external generators
    std::list<EvtDecayBase*> extraModels = externalGenList->getListOfModels();

    // Create EvtGen instance
    fEvtGen = new EvtGen(fDecayFile.Data(), fParticleFile.Data(), randomEngine,
                         radCorrEngine, &extraModels, 1, false);

    LOG(debug) << "TEvtGenDecayer: EvtGen created with " << EvtPDL::entries()
               << " particle entries";

    LOG(info) << "TEvtGenDecayer: EvtGen initialized with decay file: "
              << fDecayFile.Data()
              << ", particle file: " << fParticleFile.Data();
  } else {
    LOG(debug)
        << "TEvtGenDecayer: No EvtGen files specified, using Pythia8 only";
  }

  // Log summary at end of Init
  LOG(info) << "TEvtGenDecayer initialized - EvtGen: "
            << (fEvtGen ? "YES" : "NO")
            << ", Particles configured for EvtGen: " << fEvtGenParticles.size();

  for (size_t i = 0; i < fEvtGenParticles.size(); i++) {
    LOG(debug) << "  EvtGen particle: PDG " << fEvtGenParticles[i];
  }
}

//_____________________________________________________________________________
void TEvtGenDecayer::Decay(Int_t pdg, TLorentzVector* p) {
  // Main decay method - route to EvtGen or Pythia8 based on particle type

  // Debug output for decay calls (highest verbosity)
  LOG(debug2) << "TEvtGenDecayer::Decay called for PDG " << pdg
              << " (E=" << p->E() << ", p=" << p->P() << ")";

  // Check if this particle should use EvtGen
  Bool_t useEvtGen = UseEvtGenForParticle(pdg);
  Bool_t evtGenAvailable = (fEvtGen != nullptr);

  LOG(debug1) << "UseEvtGenForParticle(" << pdg << ") = " << useEvtGen
              << ", EvtGen available = " << evtGenAvailable;

  if (useEvtGen && evtGenAvailable) {
    LOG(debug) << "Routing PDG " << pdg << " to EvtGen";
    DecayWithEvtGen(pdg, p);
  } else {
    LOG(debug) << "Routing PDG " << pdg << " to Pythia8 fallback";
    DecayWithPythia8(pdg, p);
  }
}

//_____________________________________________________________________________
Bool_t TEvtGenDecayer::UseEvtGenForParticle(Int_t pdg) {
  // Check if this particle should be handled by EvtGen
  LOG(debug2) << "UseEvtGenForParticle: Checking PDG " << pdg
              << " against EvtGen particle list";

  for (Int_t evtGenPdg : fEvtGenParticles) {
    if (pdg == evtGenPdg) {
      LOG(debug2) << "UseEvtGenForParticle: Match found - PDG " << pdg
                  << " should use EvtGen";
      return kTRUE;
    }
  }

  LOG(debug) << "UseEvtGenForParticle: PDG " << pdg
             << " not in EvtGen particle list, falling back to Pythia8";
  return kFALSE;
}

//_____________________________________________________________________________
void TEvtGenDecayer::DecayWithEvtGen(Int_t pdg, TLorentzVector* p) {
  // Decay particle using EvtGen

  if (!fEvtGen) {
    // Fall back to Pythia8 if EvtGen not available
    DecayWithPythia8(pdg, p);
    return;
  }

  LOG(debug1) << "DecayWithEvtGen: Decaying PDG " << pdg << " with EvtGen";

  try {
    // Convert TLorentzVector to EvtGen format
    EvtVector4R p4(p->E(), p->Px(), p->Py(), p->Pz());

    // Get EvtGen particle ID from PDG code
    EvtId evtId = EvtPDL::evtIdFromStdHep(pdg);

    // Check if EvtId is valid before creating particle
    if (evtId.getId() < 0 ||
        static_cast<size_t>(evtId.getId()) >= EvtPDL::entries()) {
      LOG(warning) << "TEvtGenDecayer: Invalid EvtId for PDG " << pdg
                   << " (EvtId: " << evtId.getId()
                   << "), falling back to Pythia8";
      DecayWithPythia8(pdg, p);
      return;
    }

    // Create EvtGen particle
    EvtParticle* parent = EvtParticleFactory::particleFactory(evtId, p4);

    if (parent) {
      // Generate decay
      fEvtGen->generateDecay(parent);

      // Convert EvtGen decay products to ROOT format
      ConvertEvtGenDecay(parent);

      LOG(debug1)
          << "TEvtGenDecayer: EvtGen decay products converted and stored";

      // Clean up
      parent->deleteTree();
    } else {
      LOG(warning) << "TEvtGenDecayer: Could not create EvtParticle for PDG "
                   << pdg;
      // Fall back to Pythia8
      DecayWithPythia8(pdg, p);
    }
  } catch (const std::exception& e) {
    LOG(error) << "TEvtGenDecayer: EvtGen exception for PDG " << pdg << ": "
               << e.what();
    // Fall back to Pythia8 on any exception
    DecayWithPythia8(pdg, p);
  }
}

//_____________________________________________________________________________
void TEvtGenDecayer::ConvertEvtGenDecay(EvtParticle* parent) {
  // Convert EvtGen decay products to ROOT/GEANT4 format
  // Clear previous decay products
  fEvtGenProducts->Clear();
  fHasEvtGenDecay = kTRUE;

  int nDaughters = parent->getNDaug();
  LOG(debug2) << "ConvertEvtGenDecay: Converting " << nDaughters
              << " daughter particles";

  // Convert each daughter particle to TParticle format
  for (int i = 0; i < nDaughters; i++) {
    EvtParticle* daughter = parent->getDaug(i);
    EvtVector4R p4 = daughter->getP4();
    int pdgId = EvtPDL::getStdHep(daughter->getId());

    // Create TParticle (ROOT format)
    TParticle* particle = new ((*fEvtGenProducts)[i]) TParticle();
    particle->SetPdgCode(pdgId);
    particle->SetMomentum(p4.get(1), p4.get(2), p4.get(3),
                          p4.get(0));           // px, py, pz, E
    particle->SetProductionVertex(0, 0, 0, 0);  // Produced at origin
    particle->SetStatusCode(1);                 // Stable particle

    LOG(debug2) << "  Daughter " << i << ": PDG=" << pdgId
                << ", E=" << p4.get(0) << ", px=" << p4.get(1)
                << ", py=" << p4.get(2) << ", pz=" << p4.get(3);
  }

  LOG(debug1) << "ConvertEvtGenDecay: Stored "
              << fEvtGenProducts->GetEntriesFast() << " particles";
}

//_____________________________________________________________________________
void TEvtGenDecayer::DecayWithPythia8(Int_t pdg, TLorentzVector* p) {
  // Decay particle using Pythia8 decayer
  LOG(debug1) << "DecayWithPythia8: Handling PDG " << pdg << " with Pythia8";

  // Mark that this decay will use Pythia8 products
  fHasEvtGenDecay = kFALSE;

  // The record holds only the decaying particle (no system entry), decayed
  // in its production vertex at the origin.
  Pythia8::Event& event = fPythia->event;
  event.clear();
  event.append(pdg, 11, 0, 0, p->Px(), p->Py(), p->Pz(), p->E(), p->M());
  // Geant4 hands over only particles it wants decayed: decay this one even
  // though its species is kept stable for products, then let Pythia8 decay
  // the short-lived products.
  Pythia8::ParticleData& particleData = fPythia->particleData;
  const bool mayDecay = particleData.mayDecay(pdg);
  particleData.mayDecay(pdg, true);
  bool decayed = fPythia->moreDecays(0);
  particleData.mayDecay(pdg, mayDecay);
  decayed = decayed && fPythia->moreDecays();
  if (!decayed) {
    LOG(warning) << "TEvtGenDecayer: Pythia8 failed to decay PDG " << pdg;
  }
}

//_____________________________________________________________________________
Int_t TEvtGenDecayer::ImportParticles(TClonesArray* particles) {
  // Import particles - return EvtGen products if available, otherwise delegate
  // to Pythia8
  if (fHasEvtGenDecay && fEvtGenProducts) {
    LOG(debug1) << "ImportParticles: Returning "
                << fEvtGenProducts->GetEntriesFast() << " EvtGen particles";

    // Copy EvtGen particles to the provided array
    particles->Clear();
    int nParticles = fEvtGenProducts->GetEntriesFast();
    for (int i = 0; i < nParticles; i++) {
      TParticle* srcParticle = static_cast<TParticle*>(fEvtGenProducts->At(i));
      new ((*particles)[i]) TParticle(*srcParticle);
    }

    // Reset the flag for next decay
    fHasEvtGenDecay = kFALSE;
    return nParticles;
  }
  // Pythia8 record: the decaying particle, its decay products and any further
  // decays. Status 1 marks the final particles, which the VMC tracks.
  particles->Clear();
  const Pythia8::Event& event = fPythia->event;
  int nParticles = 0;
  for (int i = 0; i < event.size(); i++) {
    const Pythia8::Particle& part = event[i];
    new ((*particles)[nParticles++]) TParticle(
        part.id(), part.isFinal() ? 1 : 0, part.mother1(), part.mother2(),
        part.daughter1(), part.daughter2(), part.px(), part.py(), part.pz(),
        part.e(), part.xProd() * kMmToCm, part.yProd() * kMmToCm,
        part.zProd() * kMmToCm, part.tProd() * kMmOverCToS);
  }
  LOG(debug1) << "ImportParticles: Returning " << nParticles
              << " Pythia8 particles";
  return nParticles;
}

//_____________________________________________________________________________
bool TEvtGenDecayer::ReadString(const char* setting) {
  return fPythia->readString(setting);
}

//_____________________________________________________________________________
void TEvtGenDecayer::SetEvtGenDecayFile(const char* decayFile) {
  fDecayFile = decayFile;
}

//_____________________________________________________________________________
void TEvtGenDecayer::SetEvtGenParticleFile(const char* particleFile) {
  fParticleFile = particleFile;
}

//_____________________________________________________________________________
void TEvtGenDecayer::AddEvtGenParticle(Int_t pdg) {
  fEvtGenParticles.push_back(pdg);
  LOG(info) << "TEvtGenDecayer: Added PDG " << pdg << " to EvtGen particle list"
            << " (Total: " << fEvtGenParticles.size() << ")";
}

//_____________________________________________________________________________
void TEvtGenDecayer::SetForceDecay(Int_t /*type*/) {
  // Forced decay channels are not supported; configure the decay tables with
  // ReadString (Pythia8) or the EvtGen decay file instead.
  LOG(warning) << "TEvtGenDecayer::SetForceDecay is not implemented";
}

//_____________________________________________________________________________
void TEvtGenDecayer::ForceDecay() {
  LOG(warning) << "TEvtGenDecayer::ForceDecay is not implemented";
}

//_____________________________________________________________________________
Float_t TEvtGenDecayer::GetPartialBranchingRatio(Int_t /*ipart*/) {
  return 0.0;
}

//_____________________________________________________________________________
Float_t TEvtGenDecayer::GetLifetime(Int_t kf) {
  // Proper lifetime in s (Pythia8 tau0 is in mm/c)
  return fPythia->particleData.tau0(kf) * kMmOverCToS;
}

//_____________________________________________________________________________
void TEvtGenDecayer::ReadDecayTable() {}
