// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

// -------------------------------------------------------------------------
// -----                      ShipMCTrack header file                  -----
// -------------------------------------------------------------------------

/** ShipMCTrack.h
 ** Data class for storing Monte Carlo tracks processed by the ShipStack.
 ** A MCTrack can be a primary track put into the simulation or a
 ** secondary one produced by the transport through decay or interaction.
 **/

#ifndef SHIPDATA_SHIPMCTRACK_H_
#define SHIPDATA_SHIPMCTRACK_H_

#include "Rtypes.h"            // for Double_t, Int_t, Double32_t, etc
#include "ShipDetectorList.h"  // for DetectorId
#include "TLorentzVector.h"    // for TLorentzVector
#include "TMCProcess.h"        // enum with process ids
#include "TMath.h"             // for Sqrt
#include "TObject.h"           // for TObject
#include "TString.h"
#include "TVector3.h"  // for TVector3
class TParticle;

class ShipMCTrack : public TObject {
 public:
  /** Role of a track in a split set (see GetSplitSet()). **/
  enum SplitRole : Int_t {
    kNotSplit = 0,       ///< not part of a split set
    kSplitSurvivor = 1,  ///< the split track itself, or its continuation
    kSplitDecay = 2      ///< a clone standing for one decay of the split track
  };

  /**  Default constructor  **/
  ShipMCTrack();

  /**  Standard constructor  **/
  explicit ShipMCTrack(Int_t pdgCode, Int_t motherID, Double_t px, Double_t py,
                       Double_t pz, Double_t E, Double_t x, Double_t y,
                       Double_t z, Double_t t, Int_t nPoints, Int_t eventID,
                       Int_t trackID, Double_t w);

  /**  Copy constructor  **/
  ShipMCTrack(const ShipMCTrack& track);

  /**  Constructor from TParticle  **/
  explicit ShipMCTrack(TParticle* particle);

  /**  Destructor  **/
  ~ShipMCTrack() override;

  /**  Output to screen  **/
  using TObject::Print;
  void Print(Int_t iTrack = 0) const;

  /**  Accessors  **/
  Int_t GetPdgCode() const { return fPdgCode; }
  Int_t GetMotherId() const { return fMotherId; }
  Double_t GetPx() const { return fPx; }
  Double_t GetPy() const { return fPy; }
  Double_t GetPz() const { return fPz; }
  Double_t GetStartX() const { return fStartX; }
  Double_t GetStartY() const { return fStartY; }
  Double_t GetStartZ() const { return fStartZ; }
  Double_t GetStartT() const { return fStartT; }
  Int_t GetEventID() const { return fEventID; }
  void SetProcID(Int_t i) { fProcID = i; }
  Int_t GetProcID() const { return fProcID; }
  TString GetProcName() const { return TMCProcessName[fProcID]; }
  Double_t GetMass() const;
  Double_t GetEnergy() const;
  Double_t GetPt() const { return TMath::Sqrt(fPx * fPx + fPy * fPy); }
  Double_t GetP() const {
    return TMath::Sqrt(fPx * fPx + fPy * fPy + fPz * fPz);
  }
  Double_t GetRapidity() const;
  void MultiplyWeight(Double_t w) { fW = fW * w; }
  void SetWeight(Double_t w) { fW = w; }
  Double_t GetWeight() const;
  void GetMomentum(TVector3& momentum);
  void Get4Momentum(TLorentzVector& momentum);
  void GetStartVertex(TVector3& vertex);

  /** Split set of the track, -1 if it is not part of one. Splitting a kaon or
   ** pion replaces its decay by weighted alternatives, which are mutually
   ** exclusive histories rather than particles that exist together. All
   ** tracks created for one split track share its split set: the track itself
   ** and its continuations (kSplitSurvivor), and the clones that each stand
   ** for one of its decays (kSplitDecay). The clones and continuations are
   ** pushed with the split track's mother as their mother, so the split set,
   ** not the mother index, tells them apart from real siblings. The ID is
   ** unique within an event.
   ** GetSplitWeight() is the weight of the split track before it was split,
   ** the same for every member: a decay alternative of weight w stands for a
   ** decay with probability w / GetSplitWeight(). A survivor track carries
   ** the weight of its own path, before any decay that ends it. Clones whose
   ** products were not stored are pruned from the output, so the stored
   ** alternatives of a set need not add up to it. **/
  Int_t GetSplitSet() const { return fSplitSet; }
  Int_t GetSplitRole() const { return fSplitRole; }
  Double_t GetSplitWeight() const { return fSplitWeight; }
  Bool_t IsSplitDecay() const { return fSplitRole == kSplitDecay; }
  Bool_t IsSplitSurvivor() const { return fSplitRole == kSplitSurvivor; }

  /**  Modifiers  **/
  void SetMotherId(Int_t id) { fMotherId = id; }
  void SetStartT(Double_t t) { fStartT = t; }
  void SetEventID(const Int_t& eventID);
  void SetTrackID(const Int_t& trackID);
  void SetSplitSet(Int_t splitSet, Int_t role, Double_t splitWeight) {
    fSplitSet = splitSet;
    fSplitRole = role;
    fSplitWeight = splitWeight;
  }

 private:
  /**  PDG particle code  **/
  Int_t fPdgCode;

  /**  Index of mother track. -1 for primary particles.  **/
  Int_t fMotherId;

  /** Momentum components at start vertex [GeV]  **/
  Double32_t fPx, fPy, fPz, fM;

  /** Coordinates of start vertex [cm, ns]  **/
  Double32_t fStartX, fStartY, fStartZ, fStartT;

  /** weight **/
  Double32_t fW;

  /** Geant4 process ID which created the particle **/
  Int_t fProcID;

  /**  Bitvector representing the number of MCPoints for this track in
   **  each subdetector. The detectors are represented by
   **  REF:         Bit  0      (1 bit,  max. value  1)
   **  MVD:         Bit  1 -  3 (3 bits, max. value  7)
   **  STS:         Bit  4 -  8 (5 bits, max. value 31)
   **  RICH:        Bit  9      (1 bit,  max. value  1)
   **  MUCH:        Bit 10 - 14 (5 bits, max. value 31)
   **  TRD:         Bit 15 - 19 (5 bits, max. value 31)
   **  TOF:         Bit 20 - 23 (4 bits, max. value 15)
   **  ECAL:        Bit 24      (1 bit,  max. value  1)
   **  ZDC:         Bit 25      (1 bit,  max. value  1)
   **  The respective point numbers can be accessed and modified
   **  with the inline functions.
   **  Bits 26-31 are spare for potential additional detectors.
   **/
  Int_t fNPoints;

  /** Index of the event **/
  Int_t fEventID;

  /** Index of track in the event **/
  Int_t fTrackID;

  /** Split set the track belongs to, -1 if none (see GetSplitSet()) **/
  Int_t fSplitSet;

  /** Role in the split set, a SplitRole **/
  Int_t fSplitRole;

  /** Weight of the split track before splitting (see GetSplitSet()) **/
  Double32_t fSplitWeight;

  ClassDefOverride(ShipMCTrack, 10);
};

// ==========   Inline functions   ========================================

inline void ShipMCTrack::GetMomentum(TVector3& momentum) {
  momentum.SetXYZ(fPx, fPy, fPz);
}

inline void ShipMCTrack::Get4Momentum(TLorentzVector& momentum) {
  momentum.SetXYZT(fPx, fPy, fPz, GetEnergy());
}

inline void ShipMCTrack::GetStartVertex(TVector3& vertex) {
  vertex.SetXYZ(fStartX, fStartY, fStartZ);
}

#endif  // SHIPDATA_SHIPMCTRACK_H_
