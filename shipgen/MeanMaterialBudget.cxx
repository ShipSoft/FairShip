// SPDX-License-Identifier: BSD-3-Clause
// SPDX-FileCopyrightText: ALICE Experiment at CERN, All rights reserved

#include "MeanMaterialBudget.h"

#include "FairLogger.h"
#include "TGeoManager.h"
#include "TGeoMaterial.h"
#include "TGeoNode.h"
#include "TGeoShape.h"
#include "TGeoVolume.h"
#include "TMath.h"

namespace shipgen {

double MeanMaterialBudget(const double* start, const double* end,
                          double* mparam) {
  //
  // Calculate mean material budget and material properties between
  //    the points "start" and "end".
  //
  // "mparam" - parameters used for the energy and multiple scattering
  //  corrections:
  //
  // mparam[0] - mean density: sum(x_i*rho_i)/sum(x_i) [g/cm3]
  // mparam[1] - equivalent rad length fraction: sum(x_i/X0_i) [dimensionless]
  // mparam[2] - mean A: sum(x_i*A_i)/sum(x_i) [dimensionless]
  // mparam[3] - mean Z: sum(x_i*Z_i)/sum(x_i) [dimensionless]
  // mparam[4] - length: sum(x_i) [cm]
  // mparam[5] - Z/A mean: sum(x_i*Z_i/A_i)/sum(x_i) [dimensionless]
  // mparam[6] - number of boundary crosses
  // mparam[7] - maximum density encountered (g/cm^3)
  // mparam[8] - equivalent interaction length fraction: sum(x_i/I0_i)
  // [dimensionless] mparam[9] - maximum cross section encountered (mbarn)
  //
  //  Origin:  Marian Ivanov, Marian.Ivanov@cern.ch
  //
  //  Original ALICE improvements by
  //        Andrea Dainese, Andrea.Dainese@lnl.infn.it
  //        Andrei Gheata,  Andrei.Gheata@cern.ch
  //
  //  SHiP enhancements:
  //        Thomas Ruf,  Thomas.Ruf@cern.ch (interaction length support, Dec
  //        2016) Anupama Reghunath, anupama.reghunath@cern.ch (error logging,
  //        Nov 2024)
  //

  mparam[0] = 0;
  mparam[1] = 1;
  mparam[2] = 0;
  mparam[3] = 0;
  mparam[4] = 0;
  mparam[5] = 0;
  mparam[6] = 0;
  mparam[7] = 0;
  mparam[8] = 0;
  mparam[9] = 0;
  //
  double bparam[7];                           // total parameters
  double lparam[7];                           // local parameters
  double mbarn = 1E-3 * 1E-24 * TMath::Na();  // cm^2 * Avogadro

  for (Int_t i = 0; i < 7; i++) bparam[i] = 0;

  if (!gGeoManager) {
    return 0.;
  }
  //
  double length;
  double dir[3];
  length = TMath::Sqrt((end[0] - start[0]) * (end[0] - start[0]) +
                       (end[1] - start[1]) * (end[1] - start[1]) +
                       (end[2] - start[2]) * (end[2] - start[2]));
  mparam[4] = length;
  if (length < TGeoShape::Tolerance()) return 0.0;
  double invlen = 1. / length;
  dir[0] = (end[0] - start[0]) * invlen;
  dir[1] = (end[1] - start[1]) * invlen;
  dir[2] = (end[2] - start[2]) * invlen;

  // Initialise start point and direction
  TGeoNode* currentnode = 0;
  TGeoNode* startnode = gGeoManager->InitTrack(start, dir);
  if (!startnode) {
    LOG(error) << "MeanMaterialBudget: start point out of geometry: x "
               << start[0] << ", y " << start[1] << ", z " << start[2];
    return 0.0;
  }
  TGeoMaterial* material = startnode->GetVolume()->GetMedium()->GetMaterial();
  lparam[0] = material->GetDensity();
  if (lparam[0] > mparam[7]) mparam[7] = lparam[0];
  lparam[1] = material->GetRadLen();
  lparam[2] = material->GetA();
  lparam[3] = material->GetZ();
  lparam[4] = length;
  lparam[5] = lparam[3] / lparam[2];
  lparam[6] = material->GetIntLen();
  double n = lparam[0] / lparam[2];
  double sigma = 1. / (n * lparam[6]) / mbarn;
  if (sigma > mparam[9]) mparam[9] = sigma;
  if (material->IsMixture()) {
    TGeoMixture* mixture = dynamic_cast<TGeoMixture*>(material);
    lparam[5] = 0;
    double sum = 0;
    for (Int_t iel = 0; iel < mixture->GetNelements(); iel++) {
      sum += mixture->GetWmixt()[iel];
      lparam[5] += mixture->GetZmixt()[iel] * mixture->GetWmixt()[iel] /
                   mixture->GetAmixt()[iel];
    }
    lparam[5] /= sum;
  }

  // Locate next boundary within length without computing safety.
  // Propagate either with length (if no boundary found) or just cross boundary
  gGeoManager->FindNextBoundaryAndStep(length, kFALSE);
  double step = 0.0;  // Step made
  double snext = gGeoManager->GetStep();
  // If no boundary within proposed length, return current density
  if (!gGeoManager->IsOnBoundary()) {
    mparam[0] = lparam[0];
    mparam[1] = lparam[4] / lparam[1];
    mparam[2] = lparam[2];
    mparam[3] = lparam[3];
    mparam[4] = lparam[4];
    mparam[8] = lparam[4] / lparam[6];
    return lparam[0];
  }
  // Try to cross the boundary and see what is next
  Int_t nzero = 0;
  while (length > TGeoShape::Tolerance()) {
    currentnode = gGeoManager->GetCurrentNode();
    if (snext < 2. * TGeoShape::Tolerance())
      nzero++;
    else
      nzero = 0;
    if (nzero > 3) {
      // This means navigation has problems on one boundary
      // Try to cross by making a small step
      mparam[0] = bparam[0] / step;
      mparam[1] = bparam[1];
      mparam[2] = bparam[2] / step;
      mparam[3] = bparam[3] / step;
      mparam[5] = bparam[5] / step;
      mparam[8] = bparam[6];
      mparam[4] = step;
      mparam[0] = 0.;       // if crash of navigation take mean density 0
      mparam[1] = 1000000;  // and infinite rad length
      return bparam[0] / step;
    }
    mparam[6] += 1.;
    step += snext;
    bparam[1] += snext / lparam[1];
    bparam[2] += snext * lparam[2];
    bparam[3] += snext * lparam[3];
    bparam[5] += snext * lparam[5];
    bparam[6] += snext / lparam[6];
    bparam[0] += snext * lparam[0];

    if (snext >= length) break;
    if (!currentnode) break;
    length -= snext;
    material = currentnode->GetVolume()->GetMedium()->GetMaterial();
    lparam[0] = material->GetDensity();
    if (lparam[0] > mparam[7]) mparam[7] = lparam[0];
    lparam[1] = material->GetRadLen();
    lparam[2] = material->GetA();
    lparam[3] = material->GetZ();
    lparam[5] = lparam[3] / lparam[2];
    lparam[6] = material->GetIntLen();
    n = lparam[0] / lparam[2];
    sigma = 1. / (n * lparam[6]) / mbarn;
    if (sigma > mparam[9]) mparam[9] = sigma;
    if (material->IsMixture()) {
      TGeoMixture* mixture = dynamic_cast<TGeoMixture*>(material);
      lparam[5] = 0;
      double sum = 0;
      for (Int_t iel = 0; iel < mixture->GetNelements(); iel++) {
        sum += mixture->GetWmixt()[iel];
        lparam[5] += mixture->GetZmixt()[iel] * mixture->GetWmixt()[iel] /
                     mixture->GetAmixt()[iel];
      }
      lparam[5] /= sum;
    }
    gGeoManager->FindNextBoundaryAndStep(length, kFALSE);
    snext = gGeoManager->GetStep();
  }
  mparam[0] = bparam[0] / step;
  mparam[1] = bparam[1];
  mparam[2] = bparam[2] / step;
  mparam[3] = bparam[3] / step;
  mparam[5] = bparam[5] / step;
  mparam[8] = bparam[6];
  return bparam[0] / step;
}

}  // namespace shipgen
