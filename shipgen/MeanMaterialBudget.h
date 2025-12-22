// SPDX-License-Identifier: BSD-3-Clause
// SPDX-FileCopyrightText: ALICE Experiment at CERN, All rights reserved

#ifndef SHIPGEN_MEANMATERIALBUDGET_H_
#define SHIPGEN_MEANMATERIALBUDGET_H_

//
// Calculate mean material budget and material properties between two points
// in the geometry using TGeoManager navigation.
//
// Origin: AliTrackerBase::MeanMaterialBudget from ALICE AliRoot
// Author: The ALICE Off-line Project
//
// Original ALICE contributors:
//   Marian Ivanov, Marian.Ivanov@cern.ch (original implementation)
//   Andrea Dainese, Andrea.Dainese@lnl.infn.it (improvements)
//   Andrei Gheata, Andrei.Gheata@cern.ch (improvements)
//
// SHiP enhancements:
//   Thomas Ruf, Thomas.Ruf@cern.ch (added interaction length and cross section
//                                   calculations for hadronic physics, Dec
//                                   2016)
//   Anupama Reghunath, anupama.reghunath@cern.ch (improved error logging, Nov
//   2024)
//

namespace shipgen {

//
// Calculate mean material budget and material properties between
// the points "start" and "end".
//
// Parameters:
//   start  - starting point coordinates [x, y, z] in cm
//   end    - ending point coordinates [x, y, z] in cm
//   mparam - output array with material parameters (must have at least 10
//   elements):
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
// Returns: mean density along the path
//
double MeanMaterialBudget(const double* start, const double* end,
                          double* mparam);

}  // namespace shipgen

#endif  // SHIPGEN_MEANMATERIALBUDGET_H_
