#include "EvtCalcGenerator.h"

#include "FairLogger.h"
#include "FairPrimaryGenerator.h"
#include "ShipUnit.h"
#include "TDatabasePDG.h"
#include "TFile.h"
#include "TMath.h"

#include <math.h>

using namespace ShipUnit;

// -----   Default constructor   -------------------------------------------
EvtCalcGenerator::EvtCalcGenerator() {}
// -------------------------------------------------------------------------
// -----   Default constructor   -------------------------------------------
Bool_t EvtCalcGenerator::Init(const char* fileName)
{
    return Init(fileName, 0);
}
// -----   Default constructor   -------------------------------------------
Bool_t EvtCalcGenerator::Init(const char* fileName, const int firstEvent)
{

    fInputFile = std::unique_ptr<TFile>(TFile::Open(fileName, "read"));
    LOGF(info, "Info EvtCalcGenerator: Opening input file %s", fileName);

    fTree = std::unique_ptr<TTree>(dynamic_cast<TTree*>(fInputFile->Get("LLP_tree")));
    fNevents = fTree->GetEntries();
    fn = firstEvent;

    auto *branches = fTree->GetListOfBranches();
    nBranches = branches->GetEntries();
    branchVars.resize(nBranches);

    for (int i = 0; i < nBranches; ++i) {
        auto *branch = dynamic_cast<TBranch *>(branches->At(i));
        if (fTree->FindBranch(branch->GetName())) {
            fTree->SetBranchAddress(branch->GetName(), &branchVars[i]);
        }
    }

    return kTRUE;
}
// -----   Destructor   ----------------------------------------------------
EvtCalcGenerator::~EvtCalcGenerator() {}

// -- Generalized branch access --------------------------------------------
Double_t EvtCalcGenerator::GetBranchValue(const std::unique_ptr<TTree>& tree, int index) const {
    if (index < branchVars.size()) {
        return branchVars[index];
    } else {
        throw std::out_of_range("Branch index out of range");
    }
}
// -- Generalized daughter variable access ---------------------------------
Double_t EvtCalcGenerator::GetDaughterValue(const std::unique_ptr<TTree>& tree, int dauID, int offset) const {
    int baseIndex = 10 + (dauID * 6);
    return GetBranchValue(tree, baseIndex + offset);
}

// -- Wrapper functions ----------------------------------------------------
// -------------------------------------------------------------------------
Double_t EvtCalcGenerator::GetNdaughters(const std::unique_ptr<TTree>& tree) const {
    return GetBranchValue(tree, nBranches-1);
}

// -- LLP properties ------------------------------------------------------
Double_t EvtCalcGenerator::GetMotherPx(const std::unique_ptr<TTree>& tree) const { return GetBranchValue(tree, static_cast<int>(BranchIndices::MotherPx)); }
Double_t EvtCalcGenerator::GetMotherPy(const std::unique_ptr<TTree>& tree) const { return GetBranchValue(tree, static_cast<int>(BranchIndices::MotherPy)); }
Double_t EvtCalcGenerator::GetMotherPz(const std::unique_ptr<TTree>& tree) const { return GetBranchValue(tree, static_cast<int>(BranchIndices::MotherPz)); }
Double_t EvtCalcGenerator::GetMotherE(const std::unique_ptr<TTree>& tree) const  { return GetBranchValue(tree, static_cast<int>(BranchIndices::MotherE)); }

// -- Vertex properties ---------------------------------------------------
Double_t EvtCalcGenerator::GetVx(const std::unique_ptr<TTree>& tree) const { return GetBranchValue(tree, static_cast<int>(BranchIndices::Vx)); }
Double_t EvtCalcGenerator::GetVy(const std::unique_ptr<TTree>& tree) const { return GetBranchValue(tree, static_cast<int>(BranchIndices::Vy)); }
Double_t EvtCalcGenerator::GetVz(const std::unique_ptr<TTree>& tree) const { return GetBranchValue(tree, static_cast<int>(BranchIndices::Vz)); }

// -- Decay probability ---------------------------------------------------
Double_t EvtCalcGenerator::GetDecayProb(const std::unique_ptr<TTree>& tree) const { return GetBranchValue(tree, static_cast<int>(BranchIndices::DecayProb)); }

// -- Daughter properties ------------------------------------------------
Double_t EvtCalcGenerator::GetDauPx(const std::unique_ptr<TTree>& tree, int dauID) const { return GetDaughterValue(tree, dauID, 0); }
Double_t EvtCalcGenerator::GetDauPy(const std::unique_ptr<TTree>& tree, int dauID) const { return GetDaughterValue(tree, dauID, 1); }
Double_t EvtCalcGenerator::GetDauPz(const std::unique_ptr<TTree>& tree, int dauID) const { return GetDaughterValue(tree, dauID, 2); }
Double_t EvtCalcGenerator::GetDauE(const std::unique_ptr<TTree>& tree, int dauID) const  { return GetDaughterValue(tree, dauID, 3); }
Double_t EvtCalcGenerator::GetDauPDG(const std::unique_ptr<TTree>& tree, int dauID) const  { return GetDaughterValue(tree, dauID, 5); }

// -----   Passing the event   -------------------------------------------
Bool_t EvtCalcGenerator::ReadEvent(FairPrimaryGenerator* cpg)
{
    if (fn == fNevents) {
        LOG(WARNING) << "End of input file. Rewind.";
        fn = 0;
    }

    fTree->GetEntry(fn);
    fn++;
    if (fn % 100 == 0)
        LOGF(info, "Info EvtCalcGenerator: event nr %s", fn);

    Ndau = GetNdaughters(fTree);
    // Vertex coordinates in the SHiP reference frame, expressed in [cm]
    Double_t space_unit_conv = 100.;                                     // m to cm
    Double_t coord_shift = (zDecayVolume - ztarget) / space_unit_conv;   // units m
    Double_t vx_transf = GetVx(fTree) * space_unit_conv;                           // units cm
    Double_t vy_transf = GetVy(fTree) * space_unit_conv;                           // units cm
    Double_t vz_transf = (GetVz(fTree) - coord_shift) * space_unit_conv;           // units cm

    Double_t c = 2.99792458e+10;   // speed of light [cm/s]
    Double_t tof = TMath::Sqrt(vx_transf * vx_transf + vy_transf * vy_transf + vz_transf * vz_transf) / c;
    Double_t decay_prob = GetDecayProb(fTree);
    Double_t pdg_dau    = 0;

    // Mother LLP
    Bool_t wanttracking = false;
    Double_t pdg_llp = 999;   // Geantino, placeholder
    
    cpg->AddTrack(
        pdg_llp, GetMotherPx(fTree), GetMotherPy(fTree), GetMotherPz(fTree), 
        vx_transf, vy_transf, vz_transf, -1., wanttracking, 
        GetMotherE(fTree), tof, decay_prob);

    wanttracking = true;

    // Secondaries
    for (int iPart = 0; iPart < Ndau; ++iPart) {
        pdg_dau = GetDauPDG(fTree, iPart);
        if ( pdg_dau != -999) {
            cpg->AddTrack(pdg_dau,
                    GetDauPx(fTree, iPart),
                    GetDauPy(fTree, iPart),
                    GetDauPz(fTree, iPart),
                    vx_transf,
                    vy_transf,
                    vz_transf,
                    0.,
                    wanttracking,
                    GetDauE(fTree, iPart),
                    tof,
                    decay_prob);
        }
    }

    return kTRUE;
}

