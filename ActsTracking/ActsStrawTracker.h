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
/// Finds tracks with its own pattern recognition (StrawPatRec), or fits track
/// candidates from another pattern recognition (or MC truth), with the ACTS
/// Kalman filter; the left/right ambiguity of each straw hit is resolved in
/// the fit. Also fits vertices with the Billoir vertex fitter and
/// extrapolates fitted tracks to arbitrary planes. All inputs and outputs are
/// in the SHiP frame (cm, GeV); ACTS is an implementation detail.
///
/// Usage per event: ClearEvent(), AddMeasurement() for each straw hit, then
/// FindTracks() or FitCandidate() for each candidate, then
/// GetTrack()/FitVertex()/DistanceToHit().
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
  /// `driftRadius` is the (unsigned) drift distance in cm and `resolution`
  /// its uncertainty. Returns -1 if the detector ID does not belong to a
  /// straw.
  Int_t AddMeasurement(Int_t detectorId, Double_t driftRadius,
                       Double_t resolution);

  /// Find and fit all tracks among the measurements; returns their number
  Int_t FindTracks();

  /// Fit the measurements of one track candidate (indices returned by
  /// AddMeasurement), and return the index of the fitted track, or -1 if
  /// the candidate cannot be fitted. Measurements that do not fit the track
  /// are dropped.
  Int_t FitCandidate(const std::vector<Int_t>& measurements);

  /// Measurements of the fitted states of a track, one per entry of the
  /// fitted points, residuals and pulls of GetTrack(), in the same order
  std::vector<Int_t> GetTrackMeasurements(Int_t track) const;

  Int_t GetNTracks() const;
  RecoTrack GetTrack(Int_t track) const;

  /// Fit a vertex to the given tracks (track indices).
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
