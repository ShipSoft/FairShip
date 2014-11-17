/**  hcalModule.h
 *@author Mikhail Prokudin
 **
 ** hcalModule module
 **/

#ifndef HCALMODULE_H
#define HCALMODULE_H

#include "TObject.h"

#include <list>
#include <map>
#include <algorithm>

class hcalModule : public TObject
{
public:
  hcalModule(Int_t modulenumber, Float_t x1=0, Float_t y1=0, Float_t x2=0, Float_t y2=0) 
    : TObject(), fNumber(modulenumber), fX1(x1), fY1(y1), fX2(x2),
    fY2(y2), fEnergy(0), fEnergy2(0), fADC(-1111), fNeighbors()
  {};

  inline Bool_t IsInside(Float_t x, Float_t y) {return x>GetX1()&&x<GetX2()&&y>GetY1()&&y<GetY2();}
  //getters
  inline Float_t X1() const {return fX1;}
  inline Float_t Y1() const {return fY1;}
  inline Float_t X2() const {return fX2;}
  inline Float_t Y2() const {return fY2;}
  inline Float_t GetX1() const {return fX1;}
  inline Float_t GetY1() const {return fY1;}
  inline Float_t GetX2() const {return fX2;}
  inline Float_t GetY2() const {return fY2;}
  inline Float_t GetCenterX() const {return (fX1+fX2)/2.0;}
  inline Float_t GetCenterY() const {return (fY1+fY2)/2.0;}
  inline Short_t ADC() const {return fADC;}
  inline Short_t GetADC() const {return fADC;}

  inline Int_t   GetNumber() const {return fNumber;}
	
  inline Float_t GetEnergy()  const {return fEnergy;}
  inline Float_t GetEnergy2() const {return fEnergy2;}
	
  inline void GetNeighborsList(std::list<hcalModule*> &neib) const
  {
    neib=fNeighbors;
  }
  inline void SetNeighborsList(std::list<hcalModule*> &neib)
  {
    fNeighbors=neib;
  }
  inline void SetEnergy(Float_t energy)  {fEnergy=energy;}
  inline void SetEnergy2(Float_t energy) {fEnergy2=energy;}
  inline void SetADC(Short_t adc) {fADC=adc;}
  /** Reset all energies in module **/
  void ResetEnergyFast();
  inline void AddEnergy(Float_t energy)  {fEnergy+=energy;}
  inline void AddEnergy2(Float_t energy) {fEnergy2+=energy;}

  /** 3x3 cluster, first section **/
  void GetClusterEnergy(Float_t& EcalEnergy);

  inline void SetCoord(Float_t x1, Float_t y1, Float_t x2, Float_t y2)
    { fX1=x1; fY1=y1; fX2=x2; fY2=y2; }
  /** returns number of neighbors in list with module **/
  Int_t CountNeighbors(const std::list<hcalModule*>& lst) const; 
private:
  /**  module number **/
  Int_t fNumber;
  /** left edge of the module **/
  Float_t fX1;
  /** bottom edge of the module **/
  Float_t fY1;
  /** right edge of the module **/
  Float_t fX2;
  /** upper edge of the module **/
  Float_t fY2;
  /** energy in first section of hcal module  **/
  Float_t fEnergy;
  /** energy in second section of hcal module  **/
  Float_t fEnergy2;
  /** ADC counts read **/
  Short_t fADC;


  /** list of neighbor modules **/
  std::list<hcalModule*> fNeighbors;

  ClassDef(hcalModule,1);
};
  
inline void hcalModule::ResetEnergyFast()
{
  fEnergy=0.0;
  fEnergy2=0.0;
  fADC=-1111;
}

#endif
