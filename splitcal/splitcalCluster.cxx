#include "splitcalCluster.h"
#include "TMath.h"

#include <iostream>
#include <math.h>
#include <functional>   
#include <numeric>     


// -----   constructor from list/vector of splitcalHit   ------------------------------------------
// splitcalCluster::splitcalCluster(boost::python::list& l)
// {
//   std::vector<splitcalHit > v;
//   for(int i=0; i<boost::python::len(l); i++) { 
//     v.push_back(boost::python::extract<splitcalHit >(l[i]));
//   }
//   SetVectorOfHits(v);
// }

// -----   Default constructor   -------------------------------------------
splitcalCluster::splitcalCluster()
{
}
// -----   constructor from splitcalHit   ------------------------------------------
splitcalCluster::splitcalCluster(splitcalHit* h)
{
  _vectorOfHits.push_back(h);
 
  if ( _vectorOfHits.size() == 1){ //first element added to the cluster
    SetStartPoint(h);
    SetEndPoint(h);
  } else {
    if (_start.Z() > h->GetZ()) SetStartPoint(h); // start point is the hit with the smalllest z
    if (_end.Z() < h->GetZ()) SetEndPoint(h); // end point is the hit with the largest z
  }
 
}


void splitcalCluster::ComputeEtaPhiE()
{
  
  
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
  for (auto hit : _vectorOfHits){
    energy += hit->GetEnergyForCluster(_index);
    int layer = hit->GetLayerNumber();
    // hits from high precision layers give both x and y coordinates --> use if-if instead of if-else
    if (hit->IsX()){
      if (mapLayerWeigthedX.count(layer)==0) { //if key is not yet in map, initialise element to 0
	mapLayerWeigthedX[layer] = 0.; 
	mapLayerSumWeigthsX[layer] = 0.;
      }
      mapLayerWeigthedX[layer] += hit->GetX()*hit->GetEnergyForCluster(_index);
      mapLayerSumWeigthsX[layer] += hit->GetEnergyForCluster(_index);
      mapLayerZ1[layer] = hit->GetZ();
    }
    if (hit->IsY()){ 
      if (mapLayerWeigthedY.count(layer)==0) { //if key is not yet in map, initialise element to 0
	mapLayerWeigthedY[layer] = 0.; 
	mapLayerSumWeigthsY[layer] = 0.;
      }
      mapLayerWeigthedY[layer] += hit->GetY()*hit->GetEnergyForCluster(_index);
      mapLayerSumWeigthsY[layer] += hit->GetEnergyForCluster(_index);
      mapLayerZ2[layer] = hit->GetZ();
    }
  }//end loop on hit


  // FIXME: regression fit seems instable --> for the moment commented it out in favour of simple direction from initial and end point 

  auto const& firstElementX = mapLayerWeigthedX.begin();
  int minLayerX = firstElementX->first;
  double minX = firstElementX->second/mapLayerSumWeigthsX[minLayerX];
  double minZ1 = mapLayerZ1[minLayerX];

  auto const& firstElementY = mapLayerWeigthedY.begin();
  int minLayerY = firstElementY->first;
  double minY = firstElementY->second/mapLayerSumWeigthsY[minLayerY];
  double minZ2 = mapLayerZ1[minLayerY];
  
  double minZ = (minZ1+minZ2)/2.;
  
  SetStartPoint(minX, minY, minZ);

  auto const& lastElementX = mapLayerWeigthedX.rbegin();
  int maxLayerX = lastElementX->first;
  double maxX = lastElementX->second/mapLayerSumWeigthsX[maxLayerX];
  double maxZ1 = mapLayerZ1[maxLayerX];

  auto const& lastElementY = mapLayerWeigthedY.rbegin();
  int maxLayerY = lastElementY->first;
  double maxY = lastElementY->second/mapLayerSumWeigthsY[maxLayerY];
  double maxZ2 = mapLayerZ1[maxLayerY];
  
  double maxZ = (maxZ1+maxZ2)/2.;
  
  SetEndPoint(maxX, maxY, maxZ);

  // get direction vector from end-strat vector difference
  TVector3 direction;
  direction = _end - _start;
  double eta = direction.Eta();
  double phi = direction.Phi();
  SetEtaPhiE(eta, phi, energy);


  // // vectors holding the weighted coordinates per layer: x and z for the eta fit, and y and z for the phi fit
  // std::vector<double > x;
  // std::vector<double > z1;
  // std::vector<double > y;
  // std::vector<double > z2;

  // for (auto const& element : mapLayerWeigthedX){
  //   int key = element.first;
  //   x.push_back(element.second/mapLayerSumWeigthsX[key]);
  //   z1.push_back(mapLayerZ1[key]);
  // }

  // regression resultZX = LinearRegression(z1,x);
  // double alpha = acos(resultZX.slope);

  // for (auto const& element : mapLayerWeigthedY){
  //   int key = element.first;
  //   y.push_back(element.second/mapLayerSumWeigthsY[key]);
  //   z2.push_back(mapLayerZ2[key]);
  // }

  // regression resultZY = LinearRegression(z2,y);
  // double eta_check = acos(resultZY.slope);

  // // regression resultXY = LinearRegression(x,y);
  // // double phi = acos(resultXY.slope);

  // std::cout<<" ---- before fit " << std::endl;
  // _start.Print();
  // _end.Print();

  // // replace the x and y of start and end points with the re-evaluated values from the corresponding fit
  // _start.SetX( resultZX.slope * _start.Z() + resultZX.intercept ); 
  // _start.SetY( resultZY.slope * _start.Z() + resultZY.intercept ); 

  // _end.SetX( resultZX.slope * _end.Z() + resultZX.intercept ); 
  // _end.SetY( resultZY.slope * _end.Z() + resultZY.intercept ); 
  
  // // get direction vector from end-strat vector difference
  // TVector3 direction;
  // direction = _end - _start;
  // double eta = direction.Eta();
  // double phi = direction.Phi();

  // std::cout<<" ---- after fit " << std::endl;
  // _start.Print();
  // _end.Print();

  // std::cout<<" -- eta = "<< eta << std::endl;
  // std::cout<<" -- eta_check = "<< eta_check << std::endl;
  // std::cout<<" -- phi = "<< phi << std::endl;
  // std::cout<<" -- energy = "<< energy << std::endl;
  
  // SetEtaPhiE(eta, phi, energy);

  // // temporary for test
  // _mZX = resultZX.slope;
  // _qZX = resultZX.intercept;
  // _mZY = resultZY.slope;
  // _qZY = resultZY.intercept;
  
  return;
}



regression splitcalCluster::LinearRegression(std::vector<double >& x, std::vector<double >& y) {

  const auto n    = x.size();
  const auto s_x  = std::accumulate(x.begin(), x.end(), 0.);
  const auto s_y  = std::accumulate(y.begin(), y.end(), 0.);
  const auto s_xx = std::inner_product(x.begin(), x.end(), x.begin(), 0.);
  const auto s_xy = std::inner_product(x.begin(), x.end(), y.begin(), 0.);

  regression result;

  result.slope = (n * s_xy - s_x * s_y) / (n * s_xx - s_x * s_x);
  result.intercept = (s_x * s_x * s_y - s_xy * s_x) / (n * s_xx - s_x * s_x);

  std::cout<< "--- LinearRegression ---" <<std::endl;
  std::cout<< "--------- slope = " <<  result.slope <<std::endl;
  std::cout<< "--------- intercept = " <<  result.intercept <<std::endl;

  return result;

}


void splitcalCluster::SetStartPoint(splitcalHit*& h) {
  SetStartPoint(h->GetX(),h->GetY(),h->GetZ());
} 

void  splitcalCluster::SetEndPoint(splitcalHit*& h) {
  SetEndPoint(h->GetX(),h->GetY(),h->GetZ());
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
  std::cout<< "    start(x,y,z) = " 
	   << _start.X() << " ,  "
	   << _start.Y() << " ,  "
	   << _start.Z() << std::endl;  
  std::cout<< "    end(x,y,z) = " 
	   << _end.X() << " ,  "
	   << _end.Y() << " ,  "
	   << _end.Z() << std::endl;  
   std::cout<< "------- " <<std::endl;
}
// -------------------------------------------------------------------------

ClassImp(splitcalCluster)

