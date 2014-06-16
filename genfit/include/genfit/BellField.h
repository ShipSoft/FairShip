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
/** @addtogroup genfit
 * @{
 */

#ifndef genfit_BellField_h
#define genfit_BellField_h

#include "AbsBField.h"


namespace genfit {

/** @brief Bell Field for SHiP
 *
 *  @author Thomas Ruf CERN
 */
class BellField : public AbsBField {
 public:

  /** Default constructor **/
  BellField();

  /** Standard constructor **/
  BellField(double Peak, double Middle);


  //! return value at position
  TVector3 get(const TVector3& pos) const;
  void get(const double& posX, const double& posY, const double& posZ, double& Bx, double& By, double& Bz) const;

 private:
  double fMiddle;
  double fPeak;
};

} /* End of namespace genfit */
/** @} */

#endif // genfit_BellField_h
