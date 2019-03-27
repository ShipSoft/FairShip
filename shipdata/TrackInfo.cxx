#include "TrackInfo.h"
#include "KalmanFitterInfo.h"
#include "AbsMeasurement.h"
#include <stdio.h>

// -----   Default constructor   -------------------------------------------
TrackInfo::TrackInfo()
  : TObject()
{
}

// -----   Standard constructor   ------------------------------------------
TrackInfo::TrackInfo(const genfit::Track* tr)
{
  for (int i = 0; i<tr->getNumPointsWithMeasurement(); i+=1) {
    genfit::TrackPoint *tp = tr->getPointWithMeasurement(i);
    genfit::AbsMeasurement* rawM = tp->getRawMeasurement();
    genfit::KalmanFitterInfo*  info = static_cast<genfit::KalmanFitterInfo*>(tp->getFitterInfo());
    fDetIDs.push_back(rawM->getDetId());
    if (info){
       fWL.push_back(info->getWeights()[0]);
       fWR.push_back(info->getWeights()[1]);
    } else {
       // std::cout << "no info"<<std::endl;
       fWL.push_back( 0 );
       fWR.push_back( 0 );
    }
    // std::cout << "weights " << ((fWL)[i])<<" "<<((fWR)[i])<<" "<<((fDetIDs)[i])<<std::endl;
  }
}

// -----   Copy constructor   ----------------------------------------------
TrackInfo::TrackInfo(const TrackInfo& ti)
  : TObject(ti),
    fDetIDs(ti.fDetIDs),
    fWL(ti.fWL),
    fWR(ti.fWR)
{
}
// -----   Destructor   ----------------------------------------------------
TrackInfo::~TrackInfo() { }
// -------------------------------------------------------------------------


ClassImp(TrackInfo)
