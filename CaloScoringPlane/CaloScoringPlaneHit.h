// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#ifndef CALOSCORINGPLANE_CALOSCORINGPLANEHIT_H_
#define CALOSCORINGPLANE_CALOSCORINGPLANEHIT_H_

#include "CaloScoringPlanePID.h"
#include "DetectorHit.h"
#include "TVector3.h"

class CaloScoringPlanePoint;

/**
 * @brief Digitised scoring-plane hit with a particle-identification outcome.
 *
 * Position and time are smeared from the MC point; the momentum is the
 * MC-truth momentum at the plane. The PID outcome (electron / hadron /
 * muon, or unknown) is drawn with CaloScoringPlanePID from energy-dependent
 * confusion matrices and stored as a CaloScoringPlanePID::Species value. The MC
 * truth link is kept in the separate digiCaloScoringPlane2MC branch.
 */
class CaloScoringPlaneHit : public SHiP::DetectorHit {
 public:
  CaloScoringPlaneHit();

  /**
   * @param p        MC point
   * @param t0       event time offset (ns)
   * @param pos_res  Gaussian x/y resolution (cm), 0 = no smearing
   * @param time_res Gaussian time resolution (ns), 0 = no smearing
   * @param pid      identified species (CaloScoringPlanePID::Species)
   */
  CaloScoringPlaneHit(const CaloScoringPlanePoint* p, Double_t t0,
                      Double_t pos_res, Double_t time_res, Int_t pid);

  ~CaloScoringPlaneHit() override = default;
  CaloScoringPlaneHit(const CaloScoringPlaneHit& hit) = default;
  CaloScoringPlaneHit& operator=(const CaloScoringPlaneHit& hit) = default;

  Double_t GetX() const { return fX; }
  Double_t GetY() const { return fY; }
  Double_t GetZ() const { return fZ; }
  TVector3 GetXYZ() const { return TVector3(fX, fY, fZ); }
  Double_t GetTime() const { return fTime; }

  Double_t GetPx() const { return fPx; }
  Double_t GetPy() const { return fPy; }
  Double_t GetPz() const { return fPz; }
  TVector3 GetMom() const { return TVector3(fPx, fPy, fPz); }
  Double_t GetP() const { return GetMom().Mag(); }

  /** Identified species, a CaloScoringPlanePID::Species value. */
  Int_t GetPid() const { return fPid; }
  void SetPid(Int_t pid) { fPid = pid; }
  Bool_t IsIdentified() const { return fPid != CaloScoringPlanePID::kUnknown; }
  Bool_t IsElectron() const { return fPid == CaloScoringPlanePID::kElectron; }
  Bool_t IsHadron() const { return fPid == CaloScoringPlanePID::kHadron; }
  Bool_t IsMuon() const { return fPid == CaloScoringPlanePID::kMuon; }

  using SHiP::DetectorHit::Print;
  void Print() const;

 private:
  Double_t fX = 0.;     ///< smeared x (cm)
  Double_t fY = 0.;     ///< smeared y (cm)
  Double_t fZ = 0.;     ///< z of the MC point (cm)
  Double_t fTime = 0.;  ///< smeared time incl. t0 (ns)
  Double_t fPx = 0.;    ///< MC-truth momentum (GeV/c)
  Double_t fPy = 0.;
  Double_t fPz = 0.;
  Int_t fPid = CaloScoringPlanePID::kUnknown;  ///< identified species

  ClassDefOverride(CaloScoringPlaneHit, 1);
};

#endif  // CALOSCORINGPLANE_CALOSCORINGPLANEHIT_H_
