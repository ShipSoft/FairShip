// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#ifndef UPSTREAMTAGGER_UPSTREAMTAGGERHIT_H_
#define UPSTREAMTAGGER_UPSTREAMTAGGERHIT_H_

#include "DetectorHit.h"
#include "TVector3.h"

class UpstreamTaggerPoint;

/**
 * @brief Hit class for UpstreamTagger scoring plane
 *
 * Simple hit class for UBT scoring plane detector.
 * Stores the center of the fired constituent tile and the smeared time.
 * Does not store MC truth information directly.
 */
class UpstreamTaggerHit : public SHiP::DetectorHit {
 public:
  /** Default constructor **/
  UpstreamTaggerHit();

  /** Constructor from UpstreamTaggerPoint
   * @param p     MC point
   * @param t0    Event time offset
   * @param digitizedPosition Center of the fired constituent tile (cm)
   * @param time_res Time resolution (ns)
   **/
  UpstreamTaggerHit(UpstreamTaggerPoint* p, Double_t t0,
                    const TVector3& digitizedPosition, Double_t time_res);

  /** Destructor **/
  ~UpstreamTaggerHit() override = default;

  /** Copy constructor **/
  UpstreamTaggerHit(const UpstreamTaggerHit& hit) = default;
  UpstreamTaggerHit& operator=(const UpstreamTaggerHit& hit) = default;

  /** Position accessors **/
  Double_t GetX() const { return fX; }
  Double_t GetY() const { return fY; }
  Double_t GetZ() const { return fZ; }
  TVector3 GetXYZ() const { return TVector3(fX, fY, fZ); }

  /** Time accessor **/
  Double_t GetTime() const { return fTime; }
  Int_t GetADC() const { return static_cast<Int_t>(fdigi); }
  Int_t GetTileID() const { return fTileID; }
  Bool_t IsTriggered() const { return fTriggered; }
  void SetADC(Int_t adc) { SetDigi(adc); }
  void SetTileID(Int_t tileID) { fTileID = tileID; }
  void SetTriggered(Bool_t triggered) { fTriggered = triggered; }

  /** Output to screen **/
  using SHiP::DetectorHit::Print;
  void Print() const;

 private:
  Double_t fX;        ///< Digitized x position (cm)
  Double_t fY;        ///< Digitized y position (cm)
  Double_t fZ;        ///< Digitized z position (cm)
  Double_t fTime;     ///< Smeared time (ns)
  Int_t fTileID;      ///< Unique position- and tile-size-aware constituent ID
  Bool_t fTriggered;  ///< True when ADC is at or above the trigger threshold

  ClassDefOverride(UpstreamTaggerHit, 3);
};

#endif  // UPSTREAMTAGGER_UPSTREAMTAGGERHIT_H_
