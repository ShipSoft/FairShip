// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#ifndef VETO_VETOHITONTRACK_H_
#define VETO_VETOHITONTRACK_H_ 1

#include "Rtypes.h"    // for Double_t, Int_t, Double32_t, etc
#include "TObject.h"   //
#include "TVector3.h"  // for TVector3

/**
 * copied from shipdata/ShipHit.h
 */
class vetoHitOnTrack : public TObject {
 public:
  /** Default constructor **/
  vetoHitOnTrack();

  /** Constructor with hit parameters **/
  vetoHitOnTrack(Int_t hitID, Float_t dist);

  /** Destructor **/
  virtual ~vetoHitOnTrack();

  /** Accessors **/
  Double_t GetDist() const { return fDist; };
  Int_t GetHitID() const { return fHitID; };

  /** Modifiers **/
  void SetDist(Float_t d) { fDist = d; }
  void SetHitID(Int_t hitID) { fHitID = hitID; }

  /*** Output to screen */
  virtual void Print(const Option_t* opt = "") const { ; }

 protected:
  Float_t fDist;  ///< distance to closest veto hit
  Int_t fHitID;   ///< hit ID

  ClassDef(vetoHitOnTrack, 2);
};

#endif  // VETO_VETOHITONTRACK_H_
