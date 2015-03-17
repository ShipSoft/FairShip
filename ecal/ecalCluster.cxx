#include "ecalCluster.h"

#include "ecalCell.h"
#include "ecalMaximum.h"

#include "TMath.h"

#include <algorithm>
#include <iostream>

using namespace std;

/** An empty constructor **/
ecalCluster::ecalCluster()
  : TObject(),
    fNum(0),
    fSize(0),
    fMaxs(0),
    fEnergy(0.),
    fPreCalibrated(-1111.),
    fMoment(0.),
    fMomentX(0.),
    fMomentY(0.),
    fX(0.),
    fY(0.),
    fChi2(0.),
    fStatus(0),
    fCellNums(),
    fPeakNums(),
    fPreEnergy(),
    fMaximums(NULL)
{
}

/** A more advanced constructor. Should use this. **/
ecalCluster::ecalCluster(Int_t num, const std::list<ecalCell*>& cluster, const std::list<ecalMaximum*>& maximums)
  : TObject(),
    fNum(num),
    fSize(0),
    fMaxs(0),
    fEnergy(0.),
    fPreCalibrated(-1111.),
    fMoment(0.),
    fMomentX(0.),
    fMomentY(0.),
    fX(0.),
    fY(0.),
    fChi2(0.),
    fStatus(0),
    fCellNums(),
    fPeakNums(),
    fPreEnergy(),
    fMaximums(NULL)
{
  std::list<ecalCell*> cls;
  list<ecalCell*>::const_iterator p=cluster.begin();
  list<ecalMaximum*>::const_iterator pm;
  Double_t e;
  Double_t x;
  Double_t y;
  Double_t r;
  Int_t i;

  fMaxs=maximums.size();
  fEnergy=0;
  fX=0;
  fY=0;
  for(;p!=cluster.end();++p)
  {
    cls.push_back(*p);
    e=(*p)->GetEnergy();
    x=(*p)->GetCenterX();
    y=(*p)->GetCenterY();
    fX+=x*e; fY+=y*e;
    fEnergy+=e;
  }
  fSize=cls.size();

  cls.sort(ecalClusterSortProcess());
  cls.reverse();
  fX/=fEnergy;
  fY/=fEnergy;
  fChi2=-1111.0;

  fCellNums.Set(fSize);
  fPeakNums.Set(fMaxs);
  fPreEnergy.Set(fMaxs);

  fMomentX=0; fMomentY=0; fMoment=0;
  for(p=cls.begin();p!=cls.end();++p)
  {
    /** Still not clear about next 3 variables **/
    e=(*p)->GetEnergy();
    x=fX-(*p)->GetCenterX(); x*=x;
    y=fY-(*p)->GetCenterY(); y*=y;
    fMomentX+=x*e; fMomentY+=y*e; fMoment+=(x+y)*e;
  }
  fMomentX/=fEnergy; fMomentY/=fEnergy; fMoment/=fEnergy;

  i=0;
  for(p=cls.begin();p!=cls.end();++p)
    fCellNums[i++]=(*p)->GetCellNumber();
  i=0;
  fMaximums=new ecalMaximum*[fMaxs];
  for(pm=maximums.begin();pm!=maximums.end();++pm)
  {
    fMaximums[i]=(*pm);
    fPeakNums[i++]=(*pm)->Cell()->GetCellNumber();
  }
}
/** An virtual destructor **/
ecalCluster::~ecalCluster()
{
  delete [] fMaximums;
}

ClassImp(ecalCluster)
