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

MuDISGenerator::MuDISGenerator() : SHiP::Generator(){
  fTree = nullptr;
  fNevents = -1;
  fn = 0;
  fnmu = 0;
  fMat = 0;
  fnmuDis = 0;
  fnmuDisDau = 0;  
}

Bool_t MuDISGenerator::Init(const char* fileName) {
  return Init(fileName,0);
}

Bool_t MuDISGenerator::Init(const std::vector<std::string>& fileNames) {
  return Init(fileNames, 0);
}

Bool_t MuDISGenerator::Init(const std::vector<std::string>& fileNames,
			    const int startEvent) {
  
  if (fileNames.empty()) {
    LOG(error) << "MuDISGenerator: no input files provided. "
               << "Check the -f/--inputFile argument or input file glob.";
    return kFALSE;
  }
  for (const auto& fileName : fileNames) {
    if (fileName.empty()) {
      LOG(error) << "MuDISGenerator: received an empty input file name. "
                 << "Check the -f/--inputFile argument.";
      return kFALSE;
    }
  }

  LOG(info) << "Opening input file to find keys " << fileNames.at(0);
  TFile* testFile = TFile::Open(fileNames.at(0).c_str(), "READ");
  auto testKeys = testFile ? testFile->GetListOfKeys() : nullptr;
  if (testKeys == nullptr) {
    delete testFile;
    LOG(error) << "MuDISGenerator: Error opening input file "
               << fileNames.at(0)
               << ". Check that the path is correct and the file is a readable "
                  "ROOT file.";
    return kFALSE;
  }  
  const bool hasDIStree =
    testKeys->FindObject("MuonDIS") != nullptr;
  testFile->Close();
  delete testFile;

  if (hasDIStree) {
    fTree = new TChain("MuonDIS");
    for (auto& f : fileNames) {
      LOG(info) << "Opening input file " << f;
      fTree->Add(f.c_str());
    }
    int treeEvts = fTree->GetEntries();
    LOG(info) << "Reading " << treeEvts << " entries.";
    fn = 0;
    fnmu = 0;
    fMat = 0;
    fnmuDis = 0;
    fnmuDisDau = 0;
    
    bool ok = finEv.Setup(fTree);
    
    if (!ok) {
      LOG(error)
        << "MuDISGenerator: failed to bind one or more required branches";
      return kFALSE;
    }
    SetNevents();
    LOG(info) << "MuDISGenerator: Initialization successful.";
    return kTRUE;
  }
  return kFALSE;
}

// -----   Default constructor   -------------------------------------------
Bool_t MuDISGenerator::Init(const char* fileName, const int startEvent) {
  std::vector<std::string> fileNames = {fileName};
  return Init(fileNames, startEvent);
}

// -----   Passing the event   ---------------------------------------------
Bool_t MuDISGenerator::ReadEvent(FairPrimaryGenerator* cpg) {
  if (fn>=fNevents) {
    LOG(error) << " Reached total number of DIS events: counter " << fn << " nTot=" << fNevents;
    return kFALSE;
  }
  LOG(debug) << " - Processing input muon " << fnmu
	     << " fMat " << fMat << " fnmuDis " << fnmuDis
	     << " fnmuDisDau " << fnmuDisDau;
  
  if (fTree->GetEntry(fnmu) <= 0){
    LOG(error) << " Error reading event " << fnmu ;
    return kFALSE;
  }
  
  if (fnmu % 10 == 0 && fMat==0 && fnmuDis == 0) {
    LOG(info) << "Info MuDISGenerator: MuDIS original muon event #" << fnmu << " final event #" << fn;
  }
 
  //access the different materials in turn
  MuonDISInBranches & lBr = finEv.br[fMat];
  
  int nDIS = lBr.nDISevts;
  int nDISdau = 0;
  if (lBr.DISparticles!=nullptr) nDISdau = lBr.DISparticles->size();
  LOG(debug) << " nDIS " << nDIS << " nDISdau " << nDISdau << " fMat " << fMat << " local evtNumber " << fn ;

  while (nDIS==0) {
    //if fMat branch has no element, go to the next one already...
    fMat++;
    fnmuDis = 0;
    fnmuDisDau = 0;
    LOG(debug) << " -- switching material" << fMat;
    if (fMat >= nMats) {
      fMat = 0;
      fnmu++;
      LOG(debug) << " -- switching input muon " << fnmu ;
      LOG(debug) << " - Processing input muon " << fnmu
		 << " fMat " << fMat << " fnmuDis " << fnmuDis
		 << " fnmuDisDau " << fnmuDisDau;
    }
    if (fTree->GetEntry(fnmu) <= 0){
      LOG(error) << " Error reading event " << fnmu ;
      return kFALSE;
    }
    lBr = finEv.br[fMat];
    nDIS = lBr.nDISevts;
    nDISdau = 0;
    if (lBr.DISparticles!=nullptr) nDISdau = lBr.DISparticles->size();
    LOG(debug) << " nDIS " << nDIS << " nDISdau " << nDISdau << " fMat " << fMat << " local evtNumber " << fn ;
  
  }
  
  if (nDIS>0){//if fMat branch has elements
    //add also soft tracks up to z_interaction
    //first particle is the original muon with startZ necessarily before vtx_z...
    bool doTracking = false;
    int idxMum = -1;
    int nAdded = 0;
    //LOG(debug) << " --- n soft tracks: " << finEv.mcTrks->size();
    for (auto&& mcTrk : *(finEv.mcTrks)) {
      ShipMCTrack & softP = static_cast<ShipMCTrack&>(mcTrk);
      //LOG(debug) << " ---- start z=" << softP.GetStartZ() << " DIS vtx z=" << (*lBr.DISvz)[fnmuDis];
      if (softP.GetStartZ()<=(*lBr.DISvz)[fnmuDis]) {
	cpg->AddTrack(softP.GetPdgCode(),
		      softP.GetPx(),softP.GetPy(),softP.GetPz(),
		      softP.GetStartX(), softP.GetStartY(), softP.GetStartZ(), 
		      idxMum,
		      doTracking,
		      softP.GetEnergy(),
		      softP.GetStartT(),
		      softP.GetWeight());
	nAdded++;
      }
      if (!doTracking){
	//passed the first track, we want to track the soft particles and they all stem from first one.
	doTracking = true;
	idxMum = 0;
      }
    }
    LOG(debug) << " --- n soft tracks " << finEv.mcTrks->size() << ", added: " << nAdded;
    int nDaughters = (*lBr.nDISdau)[fnmuDis];
    int nDISparts = lBr.DISparticles->size();
    LOG(debug) << " --- Processing dis muon " << fnmuDis << " with " << nDaughters << " daughters and " << nDISparts << " total DIS particles";
    LOG(debug) << " ---- index dau start " << fnmuDisDau;
    //access the independent DIS events
    for (int iD(0);iD<nDaughters;++iD){
      if (fnmuDisDau+iD >= nDISparts) {
	LOG(error) << " -- Error, trying to fetch more daughters than existing in event: size = " << nDISparts << " querying index " << fnmuDisDau+iD << ". Skipping those...";
	continue;
      }
      DISparticle & lDau = (*lBr.DISparticles)[fnmuDisDau+iD];
      cpg->AddTrack(lDau.pid,lDau.px,lDau.py,lDau.pz,
		    (*lBr.DISvx)[fnmuDis],(*lBr.DISvy)[fnmuDis],(*lBr.DISvz)[fnmuDis],
		    0,true, lDau.E,
		    (*lBr.DISvt)[fnmuDis], lBr.wDIS);
    }
    fnmuDisDau += nDaughters;
    LOG(debug) << " ---- index dau end " << fnmuDisDau;
    fnmuDis++;
    LOG(debug) << " --- increment DIS event " << fnmuDis ;
    fn++;
  }//if fMat branch has elements
  else {
    LOG(error) << " Failed to process input muon " << fnmu
	       << " fMat " << fMat << " fnmuDis " << fnmuDis
	       << " fnmuDisDau " << fnmuDisDau << " local event " << fn;
    return kFALSE;
  }
  
  if (fnmuDis >= nDIS){
    fMat++;
    fnmuDis = 0;
    fnmuDisDau = 0;
    LOG(debug) << " -- switching material" << fMat;
    if (fMat >= nMats) {
      fMat = 0;
      fnmu++;
      LOG(debug) << " -- switching input muon " << fnmu ;
    }
  }

  if (fn == fNevents-1) {
    LOG(info) << "-- Reached total number of DIS events: counter " << fn << " nTot=" << fNevents;
  }

  return kTRUE;
}

// -------------------------------------------------------------------------
Int_t MuDISGenerator::GetNevents() {
  return fNevents;
}

void MuDISGenerator::SetNevents() {
  fNevents = 0;
  int treeEvts = fTree->GetEntries();
  LOG(debug) << "fTree has " << treeEvts << " entries.";  
  for (int iEv(0); iEv<treeEvts;++iEv){
    fTree->GetEntry(iEv);
    for (unsigned iM(0);iM<nMats;++iM){
      MuonDISInBranches & lBr = finEv.br[iM];
      fNevents+=lBr.nDISevts;
      LOG(debug) << "-- Adding " << lBr.nDISevts;
    }
  }
  
}
