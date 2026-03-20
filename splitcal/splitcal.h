// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#ifndef SPLITCAL_SPLITCAL_H_
#define SPLITCAL_SPLITCAL_H_

#include <map>
#include <vector>

#include "Detector.h"
#include "TLorentzVector.h"
#include "TVector3.h"

class splitcalPoint;
class FairVolume;
class TClonesArray;

class splitcal : public SHiP::Detector<splitcalPoint> {
 public:
  /**      Name :  Detector Name
   *       Active: kTRUE for active detectors (ProcessHits() will be called)
   *               kFALSE for inactive detectors
   */
  splitcal(const char* Name, Bool_t Active);

  /**      default constructor    */
  splitcal();

  /**       this method is called for each step during simulation
   *       (see FairMCApplication::Stepping())
   */
  Bool_t ProcessHits(FairVolume* v = nullptr) override;

  void SetZStart(Double_t ZStart);
  void SetEmpty(Double_t Empty, Double_t BigGap, Double_t ActiveECAL_gas_gap,
                Double_t first_precision_layer, Double_t second_precision_layer,
                Double_t third_precision_layer, Double_t num_precision_layers);

  void SetThickness(Double_t ActiveECALThickness, Double_t ActiveHCALThickness,
                    Double_t FilterECALThickness,
                    Double_t FilterECALThickness_first,
                    Double_t FilterHCALThickness,
                    Double_t ActiveECAL_gas_Thickness);

  void SetMaterial(Double_t ActiveECALMaterial, Double_t ActiveHCALMaterial,
                   Double_t FilterECALMaterial, Double_t FilterHCALMaterial);

  void SetNSamplings(Int_t nECALSamplings, Int_t nHCALSamplings,
                     Double_t ActiveHCAL);

  void SetNModules(Int_t nModulesInX, Int_t nModulesInY);

  void SetNStrips(Int_t nStrips);

  void SetStripSize(Double_t stripHalfWidth, Double_t stripHalfLength);

  void SetXMax(Double_t xMax);

  void SetYMax(Double_t yMax);

  /**      Create the detector geometry        */
  void ConstructGeometry() override;

 private:
  /** Track information to be stored until the track leaves the
  active volume.
  */
  Double_t fActiveECALThickness, fActiveHCALThickness, fFilterECALThickness,
      xfFilterECALThickness, fFilterECALThickness_first, fFilterHCALThickness;
  Double_t fActiveECALMaterial, fActiveHCALMaterial, fFilterECALMaterial,
      fFilterHCALMaterial;
  Double_t fActiveECAL_gas_gap, fActiveECAL_gas_Thickness;
  Int_t fnECALSamplings, fnHCALSamplings;
  Double_t fActiveHCAL;
  Double_t fZStart;
  Double_t fEmpty, fBigGap;
  Double_t fXMax;
  Double_t fYMax;
  Double_t ffirst_precision_layer, fsecond_precision_layer,
      fthird_precision_layer, fnum_precision_layers;
  Int_t fNModulesInX, fNModulesInY;
  Int_t fNStripsPerModule;
  Double_t fStripHalfWidth, fStripHalfLength;

  /** container for data points */

  splitcal(const splitcal&) = delete;
  splitcal& operator=(const splitcal&) = delete;

  ClassDefOverride(splitcal, 3)
};

#endif  // SPLITCAL_SPLITCAL_H_
