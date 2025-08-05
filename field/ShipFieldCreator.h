// -------------------------------------------------------------------------
// -----                    ShipFieldCreator header file                  -----
// -----                Created 26/03/14  by M. Al-Turany              -----
// -------------------------------------------------------------------------


#ifndef FIELD_SHIPFIELDCREATOR_H_
#define FIELD_SHIPFIELDCREATOR_H_

#include "FairFieldFactory.h"

class ShipFieldPar;

class FairField;

class ShipFieldCreator : public FairFieldFactory
{

 public:
  ShipFieldCreator();
  virtual ~ShipFieldCreator();
  virtual FairField* createFairField();
  virtual void SetParm();
  ClassDef(ShipFieldCreator,1);

 protected:
  ShipFieldPar* fFieldPar;

 private:
  ShipFieldCreator(const ShipFieldCreator&);
  ShipFieldCreator& operator=(const ShipFieldCreator&);

};
#endif  // FIELD_SHIPFIELDCREATOR_H_
