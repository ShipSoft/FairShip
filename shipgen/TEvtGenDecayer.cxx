#include "TEvtGenDecayer.h"
#include "TClonesArray.h"
#include "TLorentzVector.h"
#include "TParticle.h"
#include "TMCProcess.h"
#include "TSystem.h"
#include "TRandom.h"
#include "FairLogger.h"
#include "TPythia8.h"

// Define EVTGEN_CPP11 for older EvtGen versions to enable MT random generator
// This will become obsolete with newer EvtGen versions
#ifndef EVTGEN_CPP11
#define EVTGEN_CPP11
#endif

// EvtGen includes
#include "EvtGen/EvtGen.hh"
#include "EvtGenBase/EvtParticle.hh"
#include "EvtGenBase/EvtVector4R.hh"
#include "EvtGenBase/EvtRandom.hh"
#include "EvtGenBase/EvtMTRandomEngine.hh"
#include "EvtGenBase/EvtAbsRadCorr.hh"
#include "EvtGenBase/EvtPDL.hh"
#include "EvtGenBase/EvtParticleFactory.hh"
#include "EvtGenBase/EvtId.hh"
#include "EvtGenExternal/EvtExternalGenList.hh"

//_____________________________________________________________________________
TEvtGenDecayer::TEvtGenDecayer()
    : TVirtualMCDecayer(),
      fPythia8Decayer(nullptr),
      fEvtGen(nullptr),
      fDecayFile(""),
      fParticleFile(""),
      fEvtGenProducts(nullptr),
      fHasEvtGenDecay(kFALSE)
{
    // Default constructor
    fEvtGenParticles.clear();
    fEvtGenProducts = new TClonesArray("TParticle");
}

//_____________________________________________________________________________
TEvtGenDecayer::~TEvtGenDecayer()
{
    // Destructor
    if (fPythia8Decayer) delete fPythia8Decayer;
    if (fEvtGen) delete fEvtGen;
    if (fEvtGenProducts) delete fEvtGenProducts;
}

//_____________________________________________________________________________
void TEvtGenDecayer::Init()
{
    // Initialize both EvtGen and Pythia8 decayers

    // Initialize fallback Pythia8 decayer
    fPythia8Decayer = new TPythia8Decayer();
    fPythia8Decayer->Init();

    // Initialize EvtGen if decay files are specified
    if (fDecayFile != "" && fParticleFile != "") {
        // Set up EvtGen random engine with ROOT's random number generator seed
        UInt_t seed = gRandom->GetSeed();

        // Also seed Pythia8 with the same seed for consistency
        TPythia8* pythia8 = TPythia8::Instance();
        if (pythia8) {
            pythia8->Pythia8()->readString(Form("Random:seed = %u", seed));
            pythia8->Pythia8()->readString("Random:setSeed = on");
            pythia8->Pythia8()->init();  // Re-initialize with new seed
            LOG(debug) << "TEvtGenDecayer: Pythia8 RNG seeded with " << seed;
        }

        EvtRandomEngine* randomEngine = new EvtMTRandomEngine(seed);
        EvtRandom::setRandomEngine(randomEngine);

        LOG(info) << "TEvtGenDecayer: Random engine initialized with seed " << seed;

        // Set up external generators with PHOTOS radiative corrections
        std::string photonType("gamma");
        bool useEvtGenRandom(true);
        bool convertPythiaCodes(false);
        std::string pythiaDir("");

        EvtExternalGenList* externalGenList = new EvtExternalGenList(convertPythiaCodes, pythiaDir, photonType, useEvtGenRandom);

        // Get the interface to the radiative correction engine (PHOTOS)
        EvtAbsRadCorr* radCorrEngine = externalGenList->getPhotosModel();
        if (radCorrEngine) {
            LOG(info) << "TEvtGenDecayer: PHOTOS radiative corrections enabled";
        } else {
            LOG(warning) << "TEvtGenDecayer: PHOTOS not available, proceeding without radiative corrections";
        }

        // Get the interface to other external generators
        std::list<EvtDecayBase*> extraModels = externalGenList->getListOfModels();

        // Create EvtGen instance
        fEvtGen = new EvtGen(fDecayFile.Data(), fParticleFile.Data(),
                            randomEngine, radCorrEngine, &extraModels, 1, false);

        LOG(debug) << "TEvtGenDecayer: EvtGen created with " << EvtPDL::entries() << " particle entries";

        LOG(info) << "TEvtGenDecayer: EvtGen initialized with decay file: " << fDecayFile.Data()
                  << ", particle file: " << fParticleFile.Data();
    } else {
        LOG(debug) << "TEvtGenDecayer: No EvtGen files specified, using Pythia8 only";
    }

    // Log summary at end of Init
    LOG(info) << "TEvtGenDecayer initialized - EvtGen: " << (fEvtGen ? "YES" : "NO")
              << ", Pythia8 fallback: " << (fPythia8Decayer ? "YES" : "NO")
              << ", Particles configured for EvtGen: " << fEvtGenParticles.size();

    for (size_t i = 0; i < fEvtGenParticles.size(); i++) {
        LOG(debug) << "  EvtGen particle: PDG " << fEvtGenParticles[i];
    }
}

//_____________________________________________________________________________
void TEvtGenDecayer::Decay(Int_t pdg, TLorentzVector* p)
{
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
Bool_t TEvtGenDecayer::UseEvtGenForParticle(Int_t pdg)
{
    // Check if this particle should be handled by EvtGen
    LOG(debug2) << "UseEvtGenForParticle: Checking PDG " << pdg << " against EvtGen particle list";

    for (Int_t evtGenPdg : fEvtGenParticles) {
        if (pdg == evtGenPdg) {
            LOG(debug2) << "UseEvtGenForParticle: Match found - PDG " << pdg << " should use EvtGen";
            return kTRUE;
        }
    }

    LOG(warning) << "UseEvtGenForParticle: PDG " << pdg << " not in EvtGen particle list, falling back to Pythia8";
    return kFALSE;
}

//_____________________________________________________________________________
void TEvtGenDecayer::DecayWithEvtGen(Int_t pdg, TLorentzVector* p)
{
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
        if (evtId.getId() < 0 || evtId.getId() >= EvtPDL::entries()) {
            LOG(warning) << "TEvtGenDecayer: Invalid EvtId for PDG " << pdg
                        << " (EvtId: " << evtId.getId() << "), falling back to Pythia8";
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

            LOG(debug1) << "TEvtGenDecayer: EvtGen decay products converted and stored";

            // Clean up
            parent->deleteTree();
        } else {
            LOG(warning) << "TEvtGenDecayer: Could not create EvtParticle for PDG " << pdg;
            // Fall back to Pythia8
            DecayWithPythia8(pdg, p);
        }
    } catch (const std::exception& e) {
        LOG(error) << "TEvtGenDecayer: EvtGen exception for PDG " << pdg << ": " << e.what();
        // Fall back to Pythia8 on any exception
        DecayWithPythia8(pdg, p);
    }
}

//_____________________________________________________________________________
void TEvtGenDecayer::ConvertEvtGenDecay(EvtParticle* parent)
{
    // Convert EvtGen decay products to ROOT/GEANT4 format
    // Clear previous decay products
    fEvtGenProducts->Clear();
    fHasEvtGenDecay = kTRUE;

    int nDaughters = parent->getNDaug();
    LOG(debug2) << "ConvertEvtGenDecay: Converting " << nDaughters << " daughter particles";

    // Convert each daughter particle to TParticle format
    for (int i = 0; i < nDaughters; i++) {
        EvtParticle* daughter = parent->getDaug(i);
        EvtVector4R p4 = daughter->getP4();
        int pdgId = EvtPDL::getStdHep(daughter->getId());

        // Create TParticle (ROOT format)
        TParticle* particle = new ((*fEvtGenProducts)[i]) TParticle();
        particle->SetPdgCode(pdgId);
        particle->SetMomentum(p4.get(1), p4.get(2), p4.get(3), p4.get(0)); // px, py, pz, E
        particle->SetProductionVertex(0, 0, 0, 0); // Produced at origin
        particle->SetStatusCode(1); // Stable particle

        LOG(debug2) << "  Daughter " << i << ": PDG=" << pdgId
                   << ", E=" << p4.get(0) << ", px=" << p4.get(1)
                   << ", py=" << p4.get(2) << ", pz=" << p4.get(3);
    }

    LOG(debug1) << "ConvertEvtGenDecay: Stored " << fEvtGenProducts->GetEntriesFast() << " particles";
}

//_____________________________________________________________________________
void TEvtGenDecayer::DecayWithPythia8(Int_t pdg, TLorentzVector* p)
{
    // Decay particle using Pythia8 decayer
    LOG(debug1) << "DecayWithPythia8: Handling PDG " << pdg << " with Pythia8";

    // Mark that this decay will use Pythia8 products
    fHasEvtGenDecay = kFALSE;

    if (fPythia8Decayer) {
        fPythia8Decayer->Decay(pdg, p);
    }
}

//_____________________________________________________________________________
Int_t TEvtGenDecayer::ImportParticles(TClonesArray *particles)
{
    // Import particles - return EvtGen products if available, otherwise delegate to Pythia8
    if (fHasEvtGenDecay && fEvtGenProducts) {
        LOG(debug1) << "ImportParticles: Returning " << fEvtGenProducts->GetEntriesFast() << " EvtGen particles";

        // Copy EvtGen particles to the provided array
        particles->Clear();
        int nParticles = fEvtGenProducts->GetEntriesFast();
        for (int i = 0; i < nParticles; i++) {
            TParticle* srcParticle = static_cast<TParticle*>(fEvtGenProducts->At(i));
            TParticle* destParticle = new ((*particles)[i]) TParticle(*srcParticle);
        }

        // Reset the flag for next decay
        fHasEvtGenDecay = kFALSE;
        return nParticles;
    } else {
        // Fall back to Pythia8
        LOG(debug1) << "ImportParticles: Delegating to Pythia8";
        if (fPythia8Decayer) {
            return fPythia8Decayer->ImportParticles(particles);
        }
        return 0;
    }
}

//_____________________________________________________________________________
void TEvtGenDecayer::SetEvtGenDecayFile(const char* decayFile)
{
    fDecayFile = decayFile;
}

//_____________________________________________________________________________
void TEvtGenDecayer::SetEvtGenParticleFile(const char* particleFile)
{
    fParticleFile = particleFile;
}

//_____________________________________________________________________________
void TEvtGenDecayer::AddEvtGenParticle(Int_t pdg)
{
    fEvtGenParticles.push_back(pdg);
    LOG(info) << "TEvtGenDecayer: Added PDG " << pdg << " to EvtGen particle list"
              << " (Total: " << fEvtGenParticles.size() << ")";
}

//_____________________________________________________________________________
void TEvtGenDecayer::SetForceDecay(Int_t type)
{
    if (fPythia8Decayer) fPythia8Decayer->SetForceDecay(type);
}

//_____________________________________________________________________________
void TEvtGenDecayer::ForceDecay()
{
    if (fPythia8Decayer) fPythia8Decayer->ForceDecay();
}

//_____________________________________________________________________________
Float_t TEvtGenDecayer::GetPartialBranchingRatio(Int_t ipart)
{
    if (fPythia8Decayer) return fPythia8Decayer->GetPartialBranchingRatio(ipart);
    return 0.0;
}

//_____________________________________________________________________________
Float_t TEvtGenDecayer::GetLifetime(Int_t kf)
{
    if (fPythia8Decayer) return fPythia8Decayer->GetLifetime(kf);
    return 0.0;
}

//_____________________________________________________________________________
void TEvtGenDecayer::ReadDecayTable()
{
    if (fPythia8Decayer) fPythia8Decayer->ReadDecayTable();
}
