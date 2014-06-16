/* Copyright 2008-2010, Technische Universitaet Muenchen,
   Authors: Christian Hoeppner & Sebastian Neubert & Johannes Rauch

   This file is part of GENFIT.

   GENFIT is free software: you can redistribute it and/or modify
   it under the terms of the GNU Lesser General Public License as published
   by the Free Software Foundation, either version 3 of the License, or
   (at your option) any later version.

   GENFIT is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU Lesser General Public License for more details.

   You should have received a copy of the GNU Lesser General Public License
   along with GENFIT.  If not, see <http://www.gnu.org/licenses/>.
*/
#include "BellField.h"
#include "math.h"

// implementation of Bellshape field for Ship
namespace genfit {

  BellField::BellField()
    : AbsBField(),
      fMiddle(0),fPeak(0)
  { ; }
  BellField::BellField(double Peak, double Middle)
    : AbsBField(),
      fMiddle(Middle),fPeak(Peak)
  { ; }

TVector3 BellField::get(const TVector3& pos) const {
  Double_t zlocal=(pos.z()-fMiddle)/100.;
  TVector3 field_(0.,fPeak/(1.+pow(fabs(zlocal)/2.1,6.)),0.);
  return field_;
}

void BellField::get(const double& x, const double& y, const double& z, double& Bx, double& By, double& Bz) const {
  Bx = 0.;
  Double_t zlocal=(z-fMiddle)/100.;
  By = fPeak/(1.+pow(fabs(zlocal)/2.1,6.));
  Bz = 0.;
}

} /* End of namespace genfit */
