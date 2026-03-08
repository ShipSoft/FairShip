// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#ifndef DETECTOR_DETECTOR_H_
#define DETECTOR_DETECTOR_H_

#include <vector>
#include <utility>
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
  virtual ~Detector() { delete fDetPoints; };
  Detector(const char* Name, Bool_t Active, Int_t detID)
      : FairDetector(Name, Active, detID),
        fEventID(-1),
        fTrackID(-1),
        fVolumeID(-1),
        fPos(),
        fMom(),
        fTime(-1.),
        fLength(-1.),
        fELoss(-1),
        fDetPoints(NULL) {};

  Detector(const char* Name, Bool_t Active) : Detector(Name, Active, 0) {};

  template<typename... Args>
  PointType* AddHit(Args&&... args) {
    fDetPoints->emplace_back(std::forward<Args>(args)...);
    return &(fDetPoints->back());
  };

  /**  Create the detector geometry */
  virtual void ConstructGeometry() = 0;

  virtual void Initialize() { FairDetector::Initialize(); };

  virtual void Reset() { fDetPoints->clear(); };

  virtual void EndOfEvent() { fDetPoints->clear(); };

  virtual void Register() {
    fDetPoints = new std::vector<PointType>();
    static PointType t;
    FairRootManager::Instance()->RegisterAny(t.GetName(), fDetPoints, kTRUE);
  };

  virtual void FinishPrimary() { ; }
  virtual void FinishRun() { ; }
  virtual void BeginPrimary() { ; }
  virtual void PostTrack() { ; }
  virtual void PreTrack() { ; }
  virtual void BeginEvent() { ; }

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
 private:
};
}  // namespace SHiP

#endif  // DETECTOR_DETECTOR_H_
