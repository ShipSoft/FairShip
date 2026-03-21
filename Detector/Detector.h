// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#ifndef DETECTOR_DETECTOR_H_
#define DETECTOR_DETECTOR_H_

#include <utility>
#include <vector>

#include "DetectorPoint.h"
#include "FairDetector.h"
#include "FairRootManager.h"
#include "ISTLPointContainer.h"
#include "TLorentzVector.h"
#include "TVector3.h"

namespace SHiP {
template <typename PointType>
class Detector : public FairDetector, public ISTLPointContainer {
 public:
  Detector() = default;
  ~Detector() override = default;
  Detector(const char* Name, Bool_t Active, Int_t detID)
      : FairDetector(Name, Active, detID),
        fEventID(-1),
        fTrackID(-1),
        fVolumeID(-1),
        fPos(),
        fMom(),
        fTime(-1.),
        fLength(-1.),
        fELoss(-1) {}

  Detector(const char* Name, Bool_t Active) : Detector(Name, Active, 0) {}

  template <typename... Args>
  PointType* AddHit(Args&&... args) {
    fDetPoints->emplace_back(std::forward<Args>(args)...);
    return &(fDetPoints->back());
  }

  /**  Create the detector geometry */
  void ConstructGeometry() override = 0;

  void Initialize() override { FairDetector::Initialize(); }

  void Reset() override { fDetPoints->clear(); }

  void EndOfEvent() override { fDetPoints->clear(); }

  void Register() override {
    fDetPoints = new std::vector<PointType>();
    FairRootManager::Instance()->RegisterAny(PointType::Class()->GetName(),
                                             fDetPoints, kTRUE);
  }

  TClonesArray* GetCollection(Int_t iColl) const override { return nullptr; }

  void UpdatePointTrackIndices(
      const std::map<Int_t, Int_t>& indexMap) override {
    for (auto& point : *fDetPoints) {
      Int_t oldTrackID = point.GetTrackID();
      auto iter = indexMap.find(oldTrackID);
      if (iter != indexMap.end()) {
        point.SetTrackID(iter->second);
      }
    }
  }

  void SetSpecialPhysicsCuts() override { ; }
  void FinishPrimary() override { ; }
  void FinishRun() override { ; }
  void BeginPrimary() override { ; }
  void PostTrack() override { ; }
  void PreTrack() override { ; }
  void BeginEvent() override { ; }
  void CopyClones(TClonesArray* cl1, TClonesArray* cl2, Int_t offset) override {
    ;
  }

 protected:
  /** Track information to be stored until the track leaves the active volume.*/
  Int_t fEventID;       //!  event index
  Int_t fTrackID;       //!  track index
  Int_t fVolumeID;      //!  volume id
  TLorentzVector fPos;  //!  position at entrance
  TLorentzVector fMom;  //!  momentum at entrance
  Double_t fTime;       //!  time
  Double_t fLength;     //!  length
  Double_t fELoss;      //!  energy loss
  std::vector<PointType>* fDetPoints = nullptr;

  TGeoVolume* fDetector = nullptr;  // Detector object
};
}  // namespace SHiP

#endif  // DETECTOR_DETECTOR_H_
