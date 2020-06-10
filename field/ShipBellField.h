// -------------------------------------------------------------------------
// -----                    ShipBellField header file                  -----
// -----                Created 25/03/14  by M. Al-Turany              -----
// -------------------------------------------------------------------------


/** ShipBellField.h
 ** @author M.Al-Turany <m.al/turany@gsi.de>
 ** @since 25.03.2014
 ** @version1.0
 **
 ** A parametrized magnetic field
 ** Bpeak/(1+abs((z-zmiddle)/2.1)**6)
 **/


#ifndef ShipBellField_H
#define ShipBellField_H 1


#include "FairField.h"


class ShipFieldPar;


class ShipBellField : public FairField
{

 public:    

  /** Default constructor **/
  ShipBellField();


  /** Standard constructor 
   ** @param name   Object name
   ** @param Bpeak       peak field..
   ** @param Zmiddle     middle of the magnet (global coordinates)
   ** @param Btube      largest radius of the tube ellips (inside)
   **/
  ShipBellField(const char* name, Double_t Bpeak, Double_t Zmiddle,Int_t fOrient=1, Double_t Btube=500. );


  /** Constructor from ShipFieldPar **/
  ShipBellField(ShipFieldPar* fieldPar);


  /** Destructor **/
  virtual ~ShipBellField();

 
  /** Get components of field at a given point 
   ** @param x,y,z   Point coordinates [cm]
   **/
  virtual Double_t GetBx(Double_t x, Double_t y, Double_t z);
  virtual Double_t GetBy(Double_t x, Double_t y, Double_t z);
  virtual Double_t GetBz(Double_t x, Double_t y, Double_t z);

  void IncludeTarget(Double_t xy, Double_t z, Double_t l);

  /** Screen output **/
  virtual void Print();


 private:

  /** Field parameters **/
  Double_t fPeak;
  Double_t fMiddle;
  Double_t fBtube;
  Int_t fOrient;
  Bool_t fInclTarget;
  Double_t targetXY;
  Double_t targetZ0;
  Double_t targetL;
  
  ClassDef(ShipBellField, 2);

};


#endif
