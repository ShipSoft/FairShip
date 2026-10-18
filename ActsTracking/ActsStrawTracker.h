// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#ifndef ACTSTRACKING_ACTSSTRAWTRACKER_H_
#define ACTSTRACKING_ACTSSTRAWTRACKER_H_

#include <memory>
#include <vector>

#include "RecoTrack.h"
#include "RecoVertex.h"
#include "Rtypes.h"
#include "TVector3.h"

class TGeoManager;
class TVirtualMagField;

namespace SHiP {

/// Straw tracker track and vertex fitting with ACTS.
///
/// Fits track candidates from pattern recognition (or MC truth) with the
/// ACTS Kalman filter, fits vertices with the Billoir vertex fitter and
/// extrapolates fitted tracks to arbitrary planes. All inputs and outputs are
/// in the SHiP frame (cm, GeV); ACTS is an implementation detail.
///
/// Usage per event: ClearEvent(), AddMeasurement() for each straw hit, then
/// FitTrack() for each candidate, then GetTrack()/FitVertex()/DistanceToHit().
class ActsStrawTracker {
 public:
  /// Build the straw surfaces from `geometry` and use `field` for the fit.
  ///
  /// Neither is owned; both must outlive the tracker.
  ActsStrawTracker(const TGeoManager* geometry, TVirtualMagField* field);
  ~ActsStrawTracker();
  ActsStrawTracker(const ActsStrawTracker&) = delete;
  ActsStrawTracker& operator=(const ActsStrawTracker&) = delete;

  /// Forget the measurements and tracks of the previous event
  void ClearEvent();

  /// Add a straw measurement and return its index.
  ///
  /// `driftRadius` is the signed distance of the track from the wire in cm;
  /// its sign resolves the left/right ambiguity. Returns -1 if the detector
  /// ID does not belong to a straw.
  Int_t AddMeasurement(Int_t detectorId, Double_t driftRadius,
                       Double_t resolution);

  /// Fit a track candidate and return the index of the fitted track.
  ///
  /// `measurements` are indices returned by AddMeasurement, ordered along
  /// the track, with at most one per straw layer. The seed position and
  /// momentum are in cm and GeV. Returns -1 if the fit fails.
  Int_t FitTrack(const std::vector<Int_t>& measurements,
                 const TVector3& seedPosition, const TVector3& seedMomentum,
                 Int_t charge);

  Int_t GetNTracks() const;
  RecoTrack GetTrack(Int_t track) const;

  /// Fit a vertex to the given tracks (indices returned by FitTrack).
  ///
  /// Track IDs in `vertex` are the indices passed in. Returns false if the
  /// fit fails.
  Bool_t FitVertex(const std::vector<Int_t>& tracks, RecoVertex& vertex) const;

  /// Distance in cm between a hit and a fitted track at the plane of
  /// constant z through the hit, or -1 if the extrapolation fails
  Double_t DistanceToHit(Int_t track, const TVector3& hit) const;

  /// Number of straws found in the geometry
  Int_t GetNStraws() const;

 private:
  struct Impl;
  std::unique_ptr<Impl> fImpl;
};

}  // namespace SHiP

#endif  // ACTSTRACKING_ACTSSTRAWTRACKER_H_
