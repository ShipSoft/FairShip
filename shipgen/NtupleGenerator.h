// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#ifndef SHIPGEN_NTUPLEGENERATOR_H_
#define SHIPGEN_NTUPLEGENERATOR_H_

#include "FairLogger.h"  // for FairLogger, MESSAGE_ORIGIN
#include "ShipGenerator.h"
#include "TROOT.h"
#include "TTree.h"  // for TTree

class FairPrimaryGenerator;

class NtupleGenerator : public Ship::Generator {
 public:
  /** default constructor **/
  NtupleGenerator();

  /** destructor **/
  virtual ~NtupleGenerator();

  /** public method ReadEvent **/
  using Ship::Generator::Init;
  Bool_t ReadEvent(FairPrimaryGenerator*) override;
  Bool_t Init(const char*, int) override;
  Bool_t Init(const char*) override;
  Int_t GetNevents();

 private:
 protected:
  Int_t id, Nmeas, volid[500], procid[500], parentid;
  Float_t Ezero, tof;
  Double_t w;
  Float_t px[500], py[500], pz[500], vx[500], vy[500], vz[500];
  TFile* fInputFile;
  TTree* fTree;
  FairLogger* fLogger;  //!   don't make it persistent, magic ROOT command
  int fNevents;
  int fn;
  ClassDefOverride(NtupleGenerator, 1);
};

#endif  // SHIPGEN_NTUPLEGENERATOR_H_ /* !PNDntGENERATOR_H */
