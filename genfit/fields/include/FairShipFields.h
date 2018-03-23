/* 
generic interface to B fields of FairShip
*/

#ifndef genfit_FairShipFields_h
#define genfit_FairShipFields_h

#include "AbsBField.h"


namespace genfit {

/** @brief  Field for SHiP
 *
 *  @author Thomas Ruf CERN
 */
class FairShipFields : public AbsBField {
 public:

  /** Default constructor **/
  FairShipFields();


  //! return value at position
  TVector3 get(const TVector3& pos) const;
  void get(const double& posX, const double& posY, const double& posZ, double& Bx, double& By, double& Bz) const;

};

} /* End of namespace genfit */
/** @} */

#endif // genfit_FairShipFields_h
