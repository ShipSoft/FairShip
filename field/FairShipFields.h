/* 
generic interface to B fields of FairShip
*/

#ifndef genfit_FairShipFields_h
#define genfit_FairShipFields_h

#include "AbsBField.h"
#include "ShipCompField.h"


namespace genfit {

/** @brief  Field for SHiP
 *
 *  @author Thomas Ruf CERN
 */
class FairShipFields : public AbsBField {
 public:

  /** Default constructor **/
  FairShipFields();

  //! set field if not gMC present 
  inline void setField(ShipCompField* gField)  { gField_ = gField; }

  //! return value at position
  TVector3 get(const TVector3& pos) const;
  void get(const double& posX, const double& posY, const double& posZ, double& Bx, double& By, double& Bz) const;

 private:
  ShipCompField* gField_;
};

} /* End of namespace genfit */
/** @} */

#endif // genfit_FairShipFields_h
