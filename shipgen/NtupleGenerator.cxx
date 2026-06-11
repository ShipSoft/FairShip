// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#include "NtupleGenerator.h"

#include <cmath>

#include "FairPrimaryGenerator.h"
#include "TDatabasePDG.h"  // for TDatabasePDG
#include "TFile.h"
#include "TMath.h"  // for Sqrt
#include "TROOT.h"

// read events from ntuples produced

// -----   Default constructor   -------------------------------------------
NtupleGenerator::NtupleGenerator()
    : fInputFile(nullptr),
      fTree(nullptr),
      fLogger(nullptr),
      fNevents(0),
      fn(0) {}
// -------------------------------------------------------------------------
// -----   Default constructor   -------------------------------------------
Bool_t NtupleGenerator::Init(const char* fileName) { return Init(fileName, 0); }
// -----   Default constructor   -------------------------------------------
Bool_t NtupleGenerator::Init(const char* fileName, const int startEvent) {
  if (startEvent < 0) {
    LOG(error) << "NtupleGenerator: startEvent must be >= 0, got "
               << startEvent;
    return kFALSE;
  }

  LOG(info) << "NtupleGenerator: Opening input file " << fileName;
  fInputFile = TFile::Open(fileName, "READ");
  if (!fInputFile || fInputFile->IsZombie()) {
    LOG(error) << "NtupleGenerator: Error opening input file " << fileName;
    delete fInputFile;
    fInputFile = nullptr;
    return kFALSE;
  }

  fTree = dynamic_cast<TTree*>(fInputFile->Get("ntuple"));
  if (!fTree) {
    LOG(error) << "NtupleGenerator: Cannot find tree ntuple in file "
               << fileName;
    fInputFile->Close();
    delete fInputFile;
    fInputFile = nullptr;
    return kFALSE;
  }

  fNevents = fTree->GetEntries();
  if (startEvent >= fNevents) {
    LOG(error) << "NtupleGenerator: startEvent " << startEvent
               << " is out of range for " << fNevents << " entries";
    fInputFile->Close();
    delete fInputFile;
    fInputFile = nullptr;
    fTree = nullptr;
    return kFALSE;
  }

  fn = startEvent;
  bool ok = true;
  ok &= (fTree->SetBranchAddress("id", &id) >= 0);
  if (fTree->FindBranch("parentid")) {
    ok &= (fTree->SetBranchAddress("parentid", &parentid) >= 0);
  }  // parent id
  if (fTree->FindBranch("tof")) {
    ok &= (fTree->SetBranchAddress("tof", &tof) >= 0);
  }  // time of flight
  ok &= (fTree->SetBranchAddress("Nmeas", &Nmeas) >= 0);
  ok &= (fTree->SetBranchAddress("Ezero", &Ezero) >= 0);
  ok &= (fTree->SetBranchAddress("w", &w) >= 0);
  ok &= (fTree->SetBranchAddress("x", &vx) >= 0);
  ok &= (fTree->SetBranchAddress("y", &vy) >= 0);
  ok &= (fTree->SetBranchAddress("z", &vz) >= 0);
  ok &= (fTree->SetBranchAddress("px", &px) >= 0);
  ok &= (fTree->SetBranchAddress("py", &py) >= 0);
  ok &= (fTree->SetBranchAddress("pz", &pz) >= 0);
  ok &= (fTree->SetBranchAddress("volid", &volid) >= 0);
  ok &= (fTree->SetBranchAddress("procid", &procid) >= 0);
  if (!ok) {
    LOG(error)
        << "NtupleGenerator: failed to bind one or more required branches";
    fInputFile->Close();
    delete fInputFile;
    fInputFile = nullptr;
    fTree = nullptr;
    return kFALSE;
  }
  return kTRUE;
}
// -------------------------------------------------------------------------

// -----   Destructor   ----------------------------------------------------
NtupleGenerator::~NtupleGenerator() {
  // cout << "destroy Ntuple" << endl;
  if (fInputFile) {
    fInputFile->Close();
    fInputFile->Delete();
    delete fInputFile;
  }
}
// -------------------------------------------------------------------------

// -----   Passing the event   ---------------------------------------------
Bool_t NtupleGenerator::ReadEvent(FairPrimaryGenerator* cpg) {
  while (fn < fNevents) {
    fTree->GetEntry(fn);
    fn++;
    if (fn % 10000 == 0) {
      LOG(info) << "NtupleGenerator: reading event " << fn;
    }
    // test if muon survives:
    Int_t i = Nmeas - 3;
    Float_t r2 = (vx[i] * vx[i] + vy[i] * vy[i]);
    if (procid[Nmeas - 1] == 2 && r2 < 9) {
      break;
    }
  }
  if (fn == fNevents) {
    LOG(info) << "NtupleGenerator: no more input events";
    return kFALSE;
  }
  TDatabasePDG* pdgBase = TDatabasePDG::Instance();
  Double_t mass = pdgBase->GetParticle(id)->Mass();
  Double_t e =
      TMath::Sqrt(px[0] * px[0] + py[0] * py[0] + pz[0] * pz[0] + mass * mass);
  tof = 0;
  // first, original muon
  cpg->AddTrack(id, px[0], py[0], pz[0], vx[0] * 100., vy[0] * 100.,
                vz[0] * 100., -1., false, e, tof, w);
  Int_t i = Nmeas - 1;
  // second, surviving muon, extrapolate back to end of muon shield, z=20m
  Double_t zscor = 20.;
  Double_t lam = (zscor - vz[i]) / pz[i];
  Double_t xscor = vx[i] + lam * px[i];
  Double_t yscor = vy[i] + lam * py[i];
  e = TMath::Sqrt(px[i] * px[i] + py[i] * py[i] + pz[i] * pz[i] + mass * mass);
  cpg->AddTrack(id, px[i], py[i], pz[i], xscor * 100., yscor * 100.,
                zscor * 100., 0, true, e, tof, w);
  return kTRUE;
}

// -------------------------------------------------------------------------
Int_t NtupleGenerator::GetNevents() { return fNevents; }
