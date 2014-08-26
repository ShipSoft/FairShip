/**  ecalModule.h
 *@author Mikhail Prokudin
 **
 ** ECAL module structure, consisting of cells
 ** Useless if we have only modules with one lightisolated cell
 **/

#ifndef ECALMODULE_H
#define ECALMODULE_H

#include "ecalCell.h"

#include <vector>
#include <list>

class ecalModule : public ecalCell
{

public:
  // Set mc==1 to construct ecalCellMC, not ecalCell 
  ecalModule(char type=1, Int_t cellnumber=-1, Float_t x1=0, Float_t y1=0, Float_t x2=0, Float_t y2=0, Int_t mc=0,Float_t energy=0);
	
  ecalCell* Locate(Int_t x, Int_t y) const;
  
  //Faster than Locate, but doesn't check boundaries
  inline ecalCell* At(Int_t x, Int_t y) const {return fCells[y*GetType()+x];}
  ecalCell* FindCell(Float_t x, Float_t y) const;
  void AddEnergy(Float_t x, Float_t y, Float_t energy); 
  inline Float_t GetEnergy(Float_t x, Float_t y) const
  {
    ecalCell* tmp=FindCell(x,y);
    if (tmp) return tmp->GetEnergy();
    return -1;
  }
  void ResetModule();
  
  inline Float_t GetDX() const {return fDx;}
  inline Float_t GetDY() const {return fDy;}
  std::vector<ecalCell*> GetCells() const {return fCells;}
  
  //returns cells for which X1<x<X2
  std::list<ecalCell*> GetCellsX(Float_t x) const; 
  //returns cells for which Y1<y<Y2
  std::list<ecalCell*> GetCellsY(Float_t y) const;

private:
  /** module x-size **/
  Float_t fDx;
  /** module y-size **/
  Float_t fDy;
  /** list of cells contained in a module **/
  std::vector<ecalCell*> fCells;

  ClassDef(ecalModule,1);
};

inline void ecalModule::ResetModule()
{
  ResetEnergyFast();
  for(UInt_t i=0;i<fCells.size();i++) fCells[i]->ResetEnergyFast();
}
#endif
