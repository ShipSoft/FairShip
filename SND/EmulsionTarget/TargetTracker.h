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

#include <map>
#include <string>  // for string
#include <vector>

#include "FairDetector.h"
#include "FairModule.h"  // for FairModule
#include "ISTLPointContainer.h"
#include "Rtypes.h"  // for ShipMuonShield::Class, Bool_t, etc
#include "TLorentzVector.h"
#include "TVector3.h"

class TTPoint;
class FairVolume;
class TClonesArray;

class TargetTracker : public FairDetector, public ISTLPointContainer {
 public:
  TargetTracker(const char* name, Double_t TTX, Double_t TTY, Double_t TTZ,
                Bool_t Active, const char* Title = "TargetTrackers");
  TargetTracker();
  ~TargetTracker() override;

  void ConstructGeometry();

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

  /**      Initialization of the detector is done here    */
  void Initialize() override;

  /**       this method is called for each step during simulation
   *       (see FairMCApplication::Stepping())
   */
  Bool_t ProcessHits(FairVolume* v = 0) override;

  /**       Registers the produced collections in FAIRRootManager.     */
  void Register() override;

  /** Gets the produced collections */
  TClonesArray* GetCollection(Int_t iColl) const override;

  /** Update track indices in point collection (for std::vector migration) */
  void UpdatePointTrackIndices(const std::map<Int_t, Int_t>& indexMap);

  /**      has to be called after each event to reset the containers      */
  void Reset() override;

  /**      This method is an example of how to add your own point
   *       of type TTPoint to the clones array
   */

  TTPoint* AddHit(Int_t trackID, Int_t detID, TVector3 pos, TVector3 mom,
                  Double_t time, Double_t length, Double_t eLoss,
                  Int_t pdgCode);

  /** The following methods can be implemented if you need to make
   *  any optional action in your detector during the transport.
   */

  void CopyClones(TClonesArray* cl1, TClonesArray* cl2, Int_t offset) override {
    ;
  }
  void SetSpecialPhysicsCuts() override { ; }
  void EndOfEvent() override;
  void FinishPrimary() override { ; }
  void FinishRun() override { ; }
  void BeginPrimary() override { ; }
  void PostTrack() override { ; }
  void PreTrack() override { ; }
  void BeginEvent() override { ; }

  TargetTracker(const TargetTracker&) = delete;
  TargetTracker& operator=(const TargetTracker&) = delete;

  ClassDefOverride(TargetTracker, 4);

 private:
  /** Track information to be stored until the track leaves the
   active volume.
   */
  Int_t fTrackID;       //!  track index
  Int_t fVolumeID;      //!  volume id
  TLorentzVector fPos;  //!  position at entrance
  TLorentzVector fMom;  //!  momentum at entrance
  Double32_t fTime;     //!  time
  Double32_t fLength;   //!  length
  Double32_t fELoss;    //!  energy loss

  /** container for data points */
  std::vector<TTPoint>* fTTPoints;

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
