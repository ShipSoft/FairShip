/**  ecalCell.h
 *@author Mikhail Prokudin
 **
 ** ECAL cell structure, a part of ECAL module
 **/

#ifndef ECALCELL_H
#define ECALCELL_H

#include "TObject.h"

#include <list>
#include <map>
#include <algorithm>

class ecalCell : public TObject
{
public:
  ecalCell(Int_t cellnumber, Float_t x1=0, Float_t y1=0, Float_t x2=0, Float_t y2=0, Char_t type=0, Float_t energy=0) 
    : TObject(), fNumber(cellnumber), fX1(x1), fY1(y1), fX2(x2),
    fY2(y2), fType(type), fEnergy(energy), fADC(-1111), fNeighbors(), f5x5Cluster(),fTime(-1111)
  {};

  inline Bool_t IsInside(Float_t x, Float_t y) {return x>GetX1()&&x<GetX2()&&y>GetY1()&&y<GetY2();}
  //getters
  inline Char_t GetType() const {return fType;}
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

  inline Int_t   GetCellNumber() const {return fNumber;}
	
  inline Float_t GetEnergy() const {return fEnergy;}
  Float_t GetTime() const {return fTime;}
  void SetTime(Float_t time) {fTime=time;}

  // Neighbours stuff
  // Get list of 8 neighbors
  inline void GetNeighborsList(std::list<ecalCell*> &neib) const
  {
    neib=fNeighbors;
  }
  inline void SetNeighborsList(std::list<ecalCell*> &neib)
  {
    fNeighbors=neib;
  }

  // 5x5 cluster stuff
  inline void Get5x5Cluster(std::list<ecalCell*>& cls)
  {
    if (f5x5Cluster.size()==0) Create5x5Cluster();
    cls=f5x5Cluster;
  }

  inline void SetEnergy(Float_t energy) {fEnergy=energy;}
  inline void SetADC(Short_t adc) {fADC=adc;}
  /** Reset all energies in cell **/
  void ResetEnergyFast();
  inline void AddEnergy(Float_t energy) {fEnergy+=energy;}
	
  // code=0 for "3x3" cluster
  void GetClusterEnergy(Float_t& EcalEnergy);

  inline void SetCoord(Float_t x1, Float_t y1, Float_t x2, Float_t y2)
    { fX1=x1; fY1=y1; fX2=x2; fY2=y2; }
  inline void SetType(Char_t type) {fType=type;}
  /** returns number of neighbors in lst with cell **/
  Int_t CountNeighbors(const std::list<ecalCell*>& lst) const; 
private:
  /**  cell number within the module **/
  Int_t fNumber;
  /** left edge of the cell **/
  Float_t fX1;
  /** bottom edge of the cell **/
  Float_t fY1;
  /** right edge of the cell **/
  Float_t fX2;
  /** upper edge of the cell **/
  Float_t fY2;
  /** type of cell **/
  Char_t fType;
  /** energy in the calorimeter cell **/
  Float_t fEnergy;
  /** ADC counts read **/
  Short_t fADC;


  /** list of neighbor cells **/
  std::list<ecalCell*> fNeighbors;
  /** 5x5 cluster **/
  std::list<ecalCell*> f5x5Cluster;
  void Create5x5Cluster();

  /** Time of cell to fire **/
  Double_t fTime;

  ClassDef(ecalCell,1);
};
  
inline void ecalCell::ResetEnergyFast()
{
  fEnergy=0;
  fADC=-1111;
  fTime=-1111;
}

#endif
