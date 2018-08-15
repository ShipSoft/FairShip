#include "splitcalCluster.h"
#include "TMath.h"

#include <iostream>
#include <math.h>

// -----   constructor from vector of splitcalHit   ------------------------------------------
splitcalCluster::splitcalCluster(std::vector<splitcalHit >& v)
{

  SetVectorOfHits(v); //just to fill the data member
  
  // Compute energy weighted average for hits in the same layer 
  // This is in preparation of the linear fit to get the cluster eta and phi 

  // maps to copute the weighted average of all the hits in the same layer
  std::map<int, double> mapLayerWeigthedX;
  std::map<int, double> mapLayerWeigthedY;
  std::map<int, double> mapLayerZ1;
  std::map<int, double> mapLayerZ2;
  std::map<int, double> mapLayerSumWeigthsX;
  std::map<int, double> mapLayerSumWeigthsY;

  // loop over hits to compute cluster energy sum and to compute the coordinates weighted average per layer
  double energy = 0.;
  for (auto hit : v){
    energy += hit.GetEnergy();
    int layer = hit.GetLayerNumber();
    // hits from high precision layers give both x and y coordinates --> use if-if instead of if-else
    if (hit.IsX()){
      if (mapLayerWeigthedX.count(layer)==0) { //if key is not yet in map, initialise element to 0
	mapLayerWeigthedX[layer] = 0.; 
	mapLayerSumWeigthsX[layer] = 0.;
      }
      mapLayerWeigthedX[layer] += hit.GetX()*hit.GetEnergy();
      mapLayerSumWeigthsX[layer] += hit.GetEnergy();
      mapLayerZ1[layer] = hit.getZ();
    }
    if (hit.IsY()){ 
      if (mapLayerWeigthedY.count(layer)==0) { //if key is not yet in map, initialise element to 0
	mapLayerWeigthedY[layer] = 0.; 
	mapLayerSumWeigthsY[layer] = 0.;
      }
      mapLayerWeigthedY[layer] += hit.GetY()*hit.GetEnergy();
      mapLayerSumWeigthsY[layer] += hit.GetEnergy();
      mapLayerZ2[layer] = hit.getZ();
    }
  }//end loop on hit


  // vectors holding the weighted coordinates per layer: x and z for the eta fit, and y and z for the phi fit
  std::vector<double > x;
  std::vector<double > z1;
  std::vector<double > y;
  std::vector<double > z2;

  for (auto const& element : mapLayerWeigthedX){
    int key = element.first;
    x.push_back(element.second/mapLayerSumWeigthsX[layer]);
    z1.push_back(mapLayerZ1[key]);
  }

  double m1 = SlopeFromLinearRegression(z1,x);
  double eta = atan(m1);

  for (auto const& element : mapLayerWeigthedY){
    int key = element.first;
    y.push_back(element.second/mapLayerSumWeigthsY[layer]);
    z2.push_back(mapLayerZ2[key]);
  }

  double m2 = SlopeFromLinearRegression(z2,y);
  double phi = atan(m2);

  SetEtaPhiE(eta, phi, energy);

}



double splitcalCluster::SlopeFromLinearRegression(std::vector<double >& x, std::vector<double >& y) { //, double& slope, double& intercept){

  double slope; //, slopeError;
  // double intercept, interceptError;

  const auto n    = x.size();
  const auto s_x  = std::accumulate(x.begin(), x.end(), 0.);
  const auto s_y  = std::accumulate(y.begin(), y.end(), 0.);
  const auto s_xx = std::inner_product(x.begin(), x.end(), x.begin(), 0.);
  const auto s_xy = std::inner_product(x.begin(), x.end(), y.begin(), 0.);

  slope = (n * s_xy - s_x * s_y) / (n * s_xx - s_x * s_x);
  //intercept = (s_x * s_x * s_y - s_xy * s_x) / (n * s_xx - s_x * s_x);

  return slope;

}


// -------------------------------------------------------------------------

// -----   Destructor   ----------------------------------------------------
splitcalCluster::~splitcalCluster() { }
// -------------------------------------------------------------------------

// -----   Public method Print   -------------------------------------------
void splitcalCluster::Print() const
{

  std::cout<< "-I- splitcalCluster: " <<std::endl;
  std::cout<< "    (eta,phi,energy) = " 
	   << _eta << " ,  "
	   << _phi << " ,  "
	   << _energy << std::endl;  
   std::cout<< "------- " <<std::endl;
}
// -------------------------------------------------------------------------

ClassImp(splitcalCluster)

