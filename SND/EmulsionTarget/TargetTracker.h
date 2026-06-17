// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

//
//  TargetTracker.h
//
//
//  Created by Annarita Buonaura on 17/01/15.
//
//

#ifndef SND_EMULSIONTARGET_TARGETTRACKER_H_
#define SND_EMULSIONTARGET_TARGETTRACKER_H_

#include "Detector.h"
#include "TTPoint.h"

class FairVolume;

class TargetTracker : public SHiP::Detector<TTPoint> {
 public:
  TargetTracker(const char* name, Double_t TTX, Double_t TTY, Double_t TTZ,
                Bool_t Active, const char* Title = "TargetTrackers");
  TargetTracker();

  void ConstructGeometry() override;

  void SetSciFiParam(Double_t scifimat_width_, Double_t scifimat_hor_,
                     Double_t scifimat_vert_, Double_t scifimat_z_,
                     Double_t support_z_, Double_t honeycomb_z_);
  void SetNumberSciFi(Int_t n_hor_planes_, Int_t n_vert_planes_);
  void SetTargetTrackerParam(Double_t TTX, Double_t TTY, Double_t TTZ);
  void SetBrickParam(Double_t CellW);
  void SetTotZDimension(Double_t Zdim);
  void DecodeTTID(Int_t detID, Int_t& NTT, int& nplane, Bool_t& ishor);
  void SetNumberTT(Int_t n);
  void SetDesign(Int_t Design);

  /**       this method is called for each step during simulation
   *       (see FairMCApplication::Stepping())
   */
  Bool_t ProcessHits(FairVolume* v = nullptr) override;

  TargetTracker(const TargetTracker&) = delete;
  TargetTracker& operator=(const TargetTracker&) = delete;

  ClassDefOverride(TargetTracker, 4);

 protected:
  Double_t TTrackerX;
  Double_t TTrackerY;
  Double_t TTrackerZ;

  Double_t scifimat_width;
  Double_t scifimat_hor;
  Double_t scifimat_vert;
  Double_t scifimat_z;
  Double_t support_z;
  Double_t honeycomb_z;
  Int_t n_hor_planes;
  Int_t n_vert_planes;

  Double_t CellWidth;   // dimension of the cell containing brick and CES
  Double_t ZDimension;  // Dimension of the TTs+bricks total volume

  Int_t fNTT;  // number of TT

  Int_t fDesign;
};

#endif  // SND_EMULSIONTARGET_TARGETTRACKER_H_
