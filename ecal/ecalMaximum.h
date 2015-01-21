#ifndef ECALMAXIMUM_H
#define ECALMAXIMUM_H

#include "TObject.h"

class ecalCell;
/** A calorimeter maximum. Used for unification of photon reconstruction and
 ** electron identification procedures **/
class ecalMaximum : public TObject
{
public:
  /** An emtry constructor **/
  ecalMaximum() : TObject(), fCell(NULL), fCX(0.), fCY(0.), fX(0.), fY(0.), fMark(0), fTheta(0)
    {};
  /** Simplest constructor **/
  ecalMaximum(ecalCell* cell, Double_t z);
  /** Standard constructor **/
  ecalMaximum(ecalCell* cell, Double_t cx, Double_t cy, Double_t x, Double_t y);
  ~ecalMaximum() {};

  ecalCell* Cell() const {return fCell;}
  Double_t CX() const {return fCX;}
  Double_t CY() const {return fCY;}
  Double_t X() const {return fX;}
  Double_t Y() const {return fY;}
  Int_t Mark() const {return fMark;}
  Double_t Theta() const {return fTheta;}

  void SetMark(Int_t mark) {fMark=mark;}
  void SetTheta(Double_t theta) {fTheta=theta;}
private:
  ecalCell* fCell;
  /** Coordinates of cell **/
  Double_t fCX;
  Double_t fCY;
  /** Coobdinates of center of mass of maximum subcluster **/
  Double_t fX;
  Double_t fY;
  /** A mark. Used for maximum exclusion. **/
  Int_t fMark;
  /** Theta angle. 0 by default. Should be set outside if information 
   * about photon origin are here. **/
  Double_t fTheta;

  ecalMaximum(const ecalMaximum&);
  ecalMaximum& operator=(const ecalMaximum&);

  ClassDef(ecalMaximum, 1)
};

inline ecalMaximum::ecalMaximum(ecalCell* cell, Double_t cx, Double_t cy, Double_t x, Double_t y)
  : TObject(), fCell(cell), fCX(cx), fCY(cy), fX(x), fY(y), fMark(0), fTheta(0)
{
  ;
}
#endif

