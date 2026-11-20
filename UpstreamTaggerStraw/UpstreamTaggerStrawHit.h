// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#ifndef UPSTREAMTAGGERSTRAW_UPSTREAMTAGGERSTRAWHIT_H_
#define UPSTREAMTAGGERSTRAW_UPSTREAMTAGGERSTRAWHIT_H_

#include "DetectorHit.h"
#include "TVector3.h"

class UpstreamTaggerStrawPoint;

/**
 * @brief Hit class for UpstreamTaggerStraw scoring plane
 *
 * Simple hit class for UBT scoring plane detector.
 * Stores smeared position and time from MC truth.
 * Does not store MC truth information directly.
 */
class UpstreamTaggerStrawHit : public SHiP::DetectorHit {
 public:
  /** Default constructor **/
  UpstreamTaggerStrawHit();

  /** Constructor from UpstreamTaggerStrawPoint
   * @param p     MC point
   * @param t0    Event time offset
   * @param pos_res Position resolution (cm)
   * @param time_res Time resolution (ns)
   **/
  UpstreamTaggerStrawHit(UpstreamTaggerStrawPoint* p, Double_t t0, Double_t pos_res,
                    Double_t time_res);

  /** Destructor **/
  ~UpstreamTaggerStrawHit() override = default;

  /** Copy constructor **/
  UpstreamTaggerStrawHit(const UpstreamTaggerStrawHit& hit) = default;
  UpstreamTaggerStrawHit& operator=(const UpstreamTaggerStrawHit& hit) = default;

  /** Position accessors **/
  Double_t GetX() const { return fX; }
  Double_t GetY() const { return fY; }
  Double_t GetZ() const { return fZ; }
  TVector3 GetXYZ() const { return TVector3(fX, fY, fZ); }

  /** Time accessor **/
  Double_t GetTime() const { return fTime; }

  /** Output to screen **/
  using SHiP::DetectorHit::Print;
  void Print() const;

 private:
  Double_t fX;      ///< Smeared x position (cm)
  Double_t fY;      ///< Smeared y position (cm)
  Double_t fZ;      ///< Smeared z position (cm)
  Double_t fTime;   ///< Smeared time (ns)
  Int_t fSubDetID;  ///< Which layer of the UBT is this

  ClassDefOverride(UpstreamTaggerStrawHit, 2);
};

#endif  // UPSTREAMTAGGERSTRAW_UPSTREAMTAGGERSTRAWHIT_H_
