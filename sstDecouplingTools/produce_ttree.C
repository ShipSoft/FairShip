#include "FairRootManager.h"
#include "ShipMCTrack.h"
#include "TLorentzVector.h"

#include <TBranch.h>
#include <TClonesArray.h>
#include <TFile.h>
#include <TTree.h>
#include <iostream>

// Include class definition for strawtubesPoint if available
#include "prestrawdetectorPoint.h"
#include "strawtubesPoint.h"

int produce_ttree()
{
    const char* input_file_name = "ship.conical.Pythia8-TGeant4.root";
    const char* output_file_name = "inputfile.root";
    const char* tree_name = "cbmsim";
    const char* subtree_name = "prestrawdetectorPoint";

    // Open input file
    TFile* input_file = TFile::Open(input_file_name, "READ");
    if (!input_file || input_file->IsZombie()) {
        std::cerr << "Cannot open input file: " << input_file_name << std::endl;
        return 1;
    }

    // Get main tree
    TTree* tree = dynamic_cast<TTree*>(input_file->Get(tree_name));
    if (!tree) {
        std::cerr << "Cannot find tree named " << tree_name << " in input file." << std::endl;
        return 1;
    }

    // Pointer to TClonesArray of strawtubesPoint objects
    TClonesArray* points = nullptr;
    tree->SetBranchAddress(subtree_name, &points);

    // Output variables
    double px, py, pz, vx, vy, vz;
    int pdgcode;

    // Create output file and new tree
    TFile* output_file = new TFile(output_file_name, "RECREATE");
    TTree* new_tree = new TTree("mytree", "Tree with PrestrawdetectorPoint");

    new_tree->Branch("px", &px, "px/D");
    new_tree->Branch("py", &py, "py/D");
    new_tree->Branch("pz", &pz, "pz/D");
    new_tree->Branch("vx", &vx, "vx/D");
    new_tree->Branch("vy", &vy, "vy/D");
    new_tree->Branch("vz", &vz, "vz/D");
    new_tree->Branch("pdgcode", &pdgcode, "pdgcode/I");

    Long64_t nEntries = tree->GetEntries();
    std::cout << "Total entries: " << nEntries << std::endl;

    for (Long64_t i = 0; i < nEntries; ++i) {
        tree->GetEntry(i);
        int nPoints = points->GetEntriesFast();

        for (int j = 0; j < nPoints; ++j) {
            auto* p = dynamic_cast<prestrawdetectorPoint*>(points->At(j));
            if (!p)
                continue;

            vx = p->GetX();
            vy = p->GetY();
            vz = p->GetZ();
            px = p->GetPx();
            py = p->GetPy();
            pz = p->GetPz();
            pdgcode = p->PdgCode();   // or p->GetPdgCode() depending on definition

            new_tree->Fill();
        }
    }
    new_tree->Print();
    new_tree->Write();
    output_file->Close();
    input_file->Close();

    std::cout << "TTree '" << subtree_name << "' successfully copied to " << output_file_name << std::endl;
    return 0;
}
