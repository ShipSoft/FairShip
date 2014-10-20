// -------------------------------------------------------------------------
// -----                    ShipFieldCreator header file                  -----
// -----                Created 26/03/14  by M. Al-Turany              -----
// -------------------------------------------------------------------------


#ifndef ShipFieldCreator_H
#define ShipFieldCreator_H

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
#endif //ShipFieldCreator_H
