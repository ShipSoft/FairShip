// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#include "MuDISGenerator.h"

#include <cmath>

#include "FairLogger.h"
#include "FairPrimaryGenerator.h"
#include "TFile.h"
#include "TGeoCompositeShape.h"
#include "TGeoEltu.h"
#include "TGeoManager.h"
#include "TGeoNode.h"
#include "TGeoVolume.h"
#include "TMath.h"
#include "TROOT.h"
#include "TRandom.h"
#include "TSystem.h"
#include "TVectorD.h"

// -----   Default constructor   -------------------------------------------
MuDISGenerator::MuDISGenerator() = default;
// -------------------------------------------------------------------------
// -----   Default constructor   -------------------------------------------
Bool_t MuDISGenerator::Init(const char* fileName) {
  LOGF(info, "Opening input file %s", fileName);
  fInputFile = TFile::Open(fileName, "READ");
  if (!fInputFile || fInputFile->IsZombie()) {
    LOG(error) << "MuDISGenerator: error opening input file " << fileName;
    delete fInputFile;
    fInputFile = nullptr;
    return kFALSE;
  }
  fTree = fInputFile->Get<TTree>("MuonDIS");
  if (!fTree) {
    LOG(error) << "MuDISGenerator: cannot find tree MuonDIS in file " << fileName;
    fInputFile->Close();
    delete fInputFile;
    fInputFile = nullptr;
    return kFALSE;
  }
  fNevents = fTree->GetEntries();
  fnmu = 0;
  fnmuDis = 0;
  fnmuDisDau = 0;

  bool ok = finEv.Setup(fTree);
  
  if (!ok) {
    LOG(error)
        << "MuDISGenerator: failed to bind one or more required branches";
    fInputFile->Close();
    delete fInputFile;
    fInputFile = nullptr;
    fTree = nullptr;
    return kFALSE;
  }
  LOG(info) << "MuDISGenerator: Initialization successful.";
  return kTRUE;
}

// -----   Destructor   ----------------------------------------------------
MuDISGenerator::~MuDISGenerator() {
  if (fInputFile) {
    fInputFile->Close();
    fInputFile->Delete();
    delete fInputFile;
  }
}
// -----   Passing the event   ---------------------------------------------
Bool_t MuDISGenerator::ReadEvent(FairPrimaryGenerator* cpg) {
  if (fn>=fNevents) fTree->GetEntry(fn);
  if (fn % 10 == 0) {
    LOG(info) << "Info MuDISGenerator: MuDIS muon event #" << fn;
  }

  cpg->AddTrack(static_cast<int>((*mu)[0]),  // incoming muon track ()
                (*mu)[1], (*mu)[2], (*mu)[3], xmu, ymu, zmu, -1,
                false,  // tracking disabled
                (*mu)[4],
                t_DIS,  // shift time of the incoming muon track wrt t_muon from
                        // the input file.
                w * DIS_multiplicity);  // muon weight associated with a spill*
                                        // DISmultiplicity

  // outgoing DIS particles, [did,dpx,dpy,dpz,E], put density along trajectory
  // as weight, g/cm^2

  w = mparam[0] * mparam[4];  // modify weight, by multiplying with average
                              // density * track length
  int index = 0;
  for (auto&& particle : *dPart) {
    TVectorD* Part = dynamic_cast<TVectorD*>(particle);

    if (index == 0) {
      cpg->AddTrack(static_cast<int>((*Part)[0]), (*Part)[1], (*Part)[2],
                    (*Part)[3], xmu, ymu, zmu, 0, true, (*Part)[4], t_DIS,
                    cross_sec);  // save DIS cross section in MCTrack[1]
    } else {
      cpg->AddTrack(static_cast<int>((*Part)[0]), (*Part)[1], (*Part)[2],
                    (*Part)[3], xmu, ymu, zmu, 0, true, (*Part)[4], t_DIS, w);
    }
    IncrementCounter("dis_particles_stored");
    index += 1;
  }

  // Soft interaction tracks
  bool lfirst = true;  // will skip propagating the first track which is the
                       // input muon that gave the incoming muon

  for (auto&& softParticle : *dPartSoft) {
    TVectorD* SoftPart = dynamic_cast<TVectorD*>(softParticle);
    if ((*SoftPart)[7] > zmu) {
      lfirst = false;
      IncrementCounter("soft_particles_skipped");
      continue;
    }  // Soft interactions after the DIS point are not saved
    Double_t t_soft = (*SoftPart)[8] / 1e9;  // Time in seconds
    cpg->AddTrack(static_cast<int>((*SoftPart)[0]), (*SoftPart)[1],
                  (*SoftPart)[2], (*SoftPart)[3], (*SoftPart)[5],
                  (*SoftPart)[6], (*SoftPart)[7], lfirst ? -1 : 0,
                  lfirst ? false : true, (*SoftPart)[4], t_soft, w);
    lfirst = false;
    IncrementCounter("soft_particles_stored");
  }

  IncrementCounter("generated_events");

  return kTRUE;
}
// -------------------------------------------------------------------------
Int_t MuDISGenerator::GetNevents() { return fNevents; }
