// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#include "splitcalCluster.h"

#include <cmath>
#include <iostream>
#include <map>

// -----   Default constructor   -------------------------------------------
splitcalCluster::splitcalCluster() {}

void splitcalCluster::ComputeEtaPhiE(const std::vector<splitcalHit>& hits) {
  // Compute energy weighted average for hits in the same layer
  // This is in preparation of the linear fit to get the cluster eta and phi

  // maps to compute the weighted average of all the hits in the same layer
  std::map<int, double> mapLayerWeigthedX;
  std::map<int, double> mapLayerWeigthedY;
  std::map<int, double> mapLayerZ1;
  std::map<int, double> mapLayerZ2;
  std::map<int, double> mapLayerSumWeigthsX;
  std::map<int, double> mapLayerSumWeigthsY;

  // loop over hits to compute cluster energy sum and to compute the coordinates
  // weighted average per layer
  double energy = 0.;
  for (size_t i = 0; i < _hitIndices.size(); ++i) {
    const auto& hit = hits[_hitIndices[i]];
    double hitEnergy =
        hit.GetEnergy() * _hitWeights[i];  // Use weight from cluster
    energy += hitEnergy;
    int layer = hit.GetLayerNumber();
    // hits from high precision layers give both x and y coordinates --> use
    // if-if instead of if-else
    if (hit.IsX()) {
      if (!mapLayerWeigthedX.contains(layer)) {
        mapLayerWeigthedX[layer] = 0.;
        mapLayerSumWeigthsX[layer] = 0.;
      }
      mapLayerWeigthedX[layer] += hit.GetX() * hitEnergy;
      mapLayerSumWeigthsX[layer] += hitEnergy;
      mapLayerZ1[layer] = hit.GetZ();
    }
    if (hit.IsY()) {
      if (!mapLayerWeigthedY.contains(layer)) {
        mapLayerWeigthedY[layer] = 0.;
        mapLayerSumWeigthsY[layer] = 0.;
      }
      mapLayerWeigthedY[layer] += hit.GetY() * hitEnergy;
      mapLayerSumWeigthsY[layer] += hitEnergy;
      mapLayerZ2[layer] = hit.GetZ();
    }
  }  // end loop on hit

  auto const& [minLayerX, weightedMinX] = *mapLayerWeigthedX.begin();
  double minX = weightedMinX / mapLayerSumWeigthsX[minLayerX];
  double minZ1 = mapLayerZ1[minLayerX];

  auto const& [minLayerY, weightedMinY] = *mapLayerWeigthedY.begin();
  double minY = weightedMinY / mapLayerSumWeigthsY[minLayerY];
  double minZ2 = mapLayerZ1[minLayerY];

  double minZ = (minZ1 + minZ2) / 2.;

  SetStartPoint(minX, minY, minZ);

  auto const& [maxLayerX, weightedMaxX] = *mapLayerWeigthedX.rbegin();
  double maxX = weightedMaxX / mapLayerSumWeigthsX[maxLayerX];
  double maxZ1 = mapLayerZ1[maxLayerX];

  auto const& [maxLayerY, weightedMaxY] = *mapLayerWeigthedY.rbegin();
  double maxY = weightedMaxY / mapLayerSumWeigthsY[maxLayerY];
  double maxZ2 = mapLayerZ1[maxLayerY];

  double maxZ = (maxZ1 + maxZ2) / 2.;

  SetEndPoint(maxX, maxY, maxZ);

  // get direction vector from end-start vector difference
  TVector3 start(_start[0], _start[1], _start[2]);
  TVector3 end(_end[0], _end[1], _end[2]);
  TVector3 direction = end - start;
  double eta = direction.Eta();
  double phi = direction.Phi();
  SetEtaPhiE(eta, phi, energy);
}

// -------------------------------------------------------------------------

// -----   Destructor   ----------------------------------------------------
splitcalCluster::~splitcalCluster() {}
// -------------------------------------------------------------------------

// -----   Public method Print   -------------------------------------------
void splitcalCluster::Print() const {
  std::cout << "-I- splitcalCluster: " << std::endl;
  std::cout << "    (eta,phi,energy) = " << _eta << " ,  " << _phi << " ,  "
            << _energy << std::endl;
  std::cout << "    start(x,y,z) = " << _start[0] << " ,  " << _start[1]
            << " ,  " << _start[2] << std::endl;
  std::cout << "    end(x,y,z) = " << _end[0] << " ,  " << _end[1] << " ,  "
            << _end[2] << std::endl;
  std::cout << "------- " << std::endl;
}
// -------------------------------------------------------------------------
