/* 
generic interface to B fields of FairShip
assumes that magnetic fields for tracking are global fields, not matched to a volume.
*/
#include "FairShipFields.h"
#include "TVirtualMC.h"
#include <iostream>
using std::cout;
using std::endl;

namespace genfit {

  FairShipFields::FairShipFields()
    : AbsBField()
  { ; }


TVector3 FairShipFields::get(const TVector3& pos) const {
  Double_t bx,by,bz; 
  get(pos.X(),pos.Y(),pos.Z(),bx,by,bz);
  TVector3 field_(bx,by,bz);
  return field_;
}

void FairShipFields::get(const double& x, const double& y, const double& z, double& Bx, double& By, double& Bz) const {
  Double_t X[3] = {x,y,z};
  Double_t B[3] = {Bx,By,Bz};
  if (!gMC && !gField_){
   cout<<"no Field Manager instantiated"<<endl;
   return;
  }
  if (gMC){
    gMC->GetMagField()->Field(X,B);
  } else {
    gField_->Field(X,B);
  }
  Bx = B[0];
  By = B[1];
  Bz = B[2];
}

} /* End of namespace genfit */
