/**
 * @file TTreeGenerator.cxx
 * @brief Implementation of TTreeGenerator class
 * @author Oliver Lantwin
 * @date 2025/05/29
 */

#include "TTreeGenerator.h"

#include "FairLogger.h"

namespace ship
{

//==============================================================================
// Constructors and Destructor
//==============================================================================

TTreeGenerator::TTreeGenerator()
    : FairGenerator()
    , fInputFile(nullptr)
    , fInputTree(nullptr)
    , fFileName("")
    , fTreeName("events")
    , fNEvents(0)
    , fCurrentEvent(0)
    , fPx(0)
    , fPy(0)
    , fPz(0)
    , fX(0)
    , fY(0)
    , fZ(0)
    , fPdgId(0)
    , fWeight(1.0)
{}

TTreeGenerator::TTreeGenerator(const char* fileName, const char* treeName)
    : FairGenerator()
    , fInputFile(nullptr)
    , fInputTree(nullptr)
    , fFileName(fileName)
    , fTreeName(treeName)
    , fNEvents(0)
    , fCurrentEvent(0)
    , fPx(0)
    , fPy(0)
    , fPz(0)
    , fX(0)
    , fY(0)
    , fZ(0)
    , fPdgId(0)
    , fWeight(1.0)
{}

TTreeGenerator::~TTreeGenerator()
{
    if (fInputFile) {
        fInputFile->Close();
        delete fInputFile;
    }
}

//==============================================================================
// Public Methods
//==============================================================================

Bool_t TTreeGenerator::Init()
{
    if (fFileName.IsNull()) {
        LOG(ERROR) << "TTreeGenerator: No input file specified!";
        return kFALSE;
    }

    // Open input file
    fInputFile = TFile::Open(fFileName.Data(), "READ");
    if (!fInputFile || fInputFile->IsZombie()) {
        LOG(ERROR) << "TTreeGenerator: Cannot open file " << fFileName.Data();
        return kFALSE;
    }

    // Get input tree
    fInputTree = dynamic_cast<TTree*>(fInputFile->Get(fTreeName.Data()));
    if (!fInputTree) {
        LOG(ERROR) << "TTreeGenerator: Cannot find tree " << fTreeName.Data() << " in file " << fFileName.Data();
        return kFALSE;
    }

    fNEvents = fInputTree->GetEntries();
    LOG(INFO) << "TTreeGenerator: Found " << fNEvents << " events in tree";

    // Initialize branch addresses
    InitBranches();

    return kTRUE;
}

Bool_t TTreeGenerator::ReadEvent(FairPrimaryGenerator* primGen)
{
    if (!fInputTree || fCurrentEvent >= fNEvents) {
        return kFALSE;
    }

    // Read current event
    fInputTree->GetEntry(fCurrentEvent);

    // Add primary particle
    // Position in cm, momentum in GeV/c
    primGen->AddTrack(fPdgId, fPx, fPy, fPz, fX, fY, fZ);

    // Set event weight if needed
    // Note: FairRoot may handle weights differently depending on version
    // This is a placeholder - adjust according to your FairRoot version

    fCurrentEvent++;

    return kTRUE;
}

Bool_t TTreeGenerator::SkipEvents(Int_t count)
{
    fCurrentEvent += count;
    if (fCurrentEvent >= fNEvents) {
        fCurrentEvent = fNEvents;
        return kFALSE;
    }
    return kTRUE;
}

Bool_t TTreeGenerator::RewindEvents()
{
    fCurrentEvent = 0;
    return kTRUE;
}

void TTreeGenerator::SetInput(const char* fileName, const char* treeName)
{
    fFileName = fileName;
    fTreeName = treeName;
}

//==============================================================================
// Private Methods
//==============================================================================

void TTreeGenerator::InitBranches()
{
    if (!fInputTree)
        return;

    // Set branch addresses
    fInputTree->SetBranchAddress("px", &fPx);
    fInputTree->SetBranchAddress("py", &fPy);
    fInputTree->SetBranchAddress("pz", &fPz);
    fInputTree->SetBranchAddress("x", &fX);
    fInputTree->SetBranchAddress("y", &fY);
    fInputTree->SetBranchAddress("z", &fZ);
    fInputTree->SetBranchAddress("id", &fPdgId);
    fInputTree->SetBranchAddress("w", &fWeight);
}

}   // namespace ship
