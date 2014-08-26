/**  ecalStructure.h
 *@author Mikhail Prokudin
 **
 ** ECAL structure, consisting of modules
 **/

#ifndef ECALSTRUCTURE_H
#define ECALSTRUCTURE_H


#include "ecalInf.h"
#include "ecalModule.h"
#include "ecalCell.h"

#include "TMath.h"
#include "TNamed.h"

#include <vector>

#define _DECALSTRUCT

struct __ecalCellWrapper;

class ecalStructure : public TNamed
{
public:
  ecalStructure(ecalInf* ecalinf);
  void SetUseMC(Int_t mc=0) {fUseMC=mc;}
  Int_t GetUseMC() const {return fUseMC;}
  void Construct();
  Int_t GetNumber(Int_t x, Int_t y) const;
  
  Bool_t AddEnergy(Float_t x, Float_t y, Float_t energy, Bool_t isPS=kFALSE);
  Float_t GetEnergy(Float_t x, Float_t y, Bool_t isPS=kFALSE) const;
  ecalCell* GetCell(Float_t x, Float_t y) const;
  ecalModule* GetModule(Float_t x, Float_t y) const;
  Int_t GetModuleNumber(Float_t x, Float_t y) const;
  
  Float_t GetX1() const {return fX1;};
  Float_t GetY1() const {return fY1;};
  Float_t GetX2() const;
  Float_t GetY2() const;
  inline ecalInf* GetEcalInf() const {return fEcalInf;}
  inline void GetStructure(std::vector<ecalModule*>& stru) const {stru=fStructure;}
  inline void GetCells(std::list<ecalCell*>& cells) const {cells=fCells;}
  //Create neighbors lists
  void CreateNLists(ecalCell* cell);
  void ResetModules();
  
  ecalModule* CreateModule(char type, Int_t number, Float_t x1, Float_t y1, Float_t x2, Float_t y2);
  //Some usefull procedures for hit processing
  
  //Converts (x,y) to hit Id
  Int_t GetHitId(Float_t x, Float_t y) const;
  //Hit Id -> (x,y)
  void GetHitXY(const Int_t hitId, Float_t& x, Float_t& y) const;

  // HitId -> in global cell coordinate 
  void GetGlobalCellXY(const Int_t hitId, Int_t& x, Int_t& y) const;

  // HitId -> cell type
  Int_t GetType(const Int_t hitId) const;

  ecalCell* GetCell(Int_t fVolId, Int_t& ten, Bool_t& isPS);
  //Hit It -> Cell
  ecalCell* GetHitCell(const Int_t hitId) const;

private:
  Int_t GetNum(Int_t x, Int_t y) const;
  
private:
  /** Creates fCells lists **/
  void Serialize();
  /** Use store MC information in cells **/
  Int_t fUseMC;
  /** X coordibate of left bottom angle of ECAL **/
  Float_t fX1;
  /** Y coordibate of left bottom angle of ECAL **/
  Float_t fY1;
  /** ECAL geometry container **/
  ecalInf* fEcalInf;
  /** total list of ECAL modules **/
  std::vector<ecalModule*> fStructure;
  /** All ECAL cells **/
  std::list<ecalCell*> fCells;
  /** MCPoint id -> ECAL cell**/
  std::vector<__ecalCellWrapper*> fHash;

  ecalStructure(const ecalStructure&);
  ecalStructure& operator=(const ecalStructure&);

  ClassDef(ecalStructure,1);
};

inline ecalCell* ecalStructure::GetCell(Float_t x, Float_t y) const
{
  /** get ECAL cell by known cell center coordinate (x,y) **/
  ecalModule* module=GetModule(x,y);
  if (module) return module->FindCell(x,y);
  return NULL;
}

inline ecalModule* ecalStructure::GetModule(Float_t x, Float_t y) const
{
  /** get ECAL module by known module center coordinate (x,y) **/
  Int_t num=GetModuleNumber(x,y);
  if (-1==num) return NULL; else return fStructure[num]; 
}

inline Int_t  ecalStructure::GetModuleNumber(Float_t x, Float_t y) const
{
  /** get ECAL module by known module center coordinate (x,y) **/
  Int_t ix=(Int_t)TMath::Floor((x-GetX1())/fEcalInf->GetModuleSize());
  Int_t iy=(Int_t)TMath::Floor((y-GetY1())/fEcalInf->GetModuleSize());
  return GetNumber(ix,iy);
}

inline Int_t ecalStructure::GetNumber(Int_t x, Int_t y) const
{
  /** get ECAL absolute module number by known module relative number (x,y)
   ** with check for the ECAL boundaries **/
  if (x>-1&&y>-1)
    if (x<fEcalInf->GetXSize()&&y<fEcalInf->GetYSize())
      return GetNum(x,y);
  return -1;
}

inline Int_t ecalStructure::GetNum(Int_t x, Int_t y) const
{
  /** get ECAL absolute module number by known module relative number (x,y) **/
  return y*fEcalInf->GetXSize()+x;
}

inline Float_t ecalStructure::GetX2() const
{
  /** get ECAL right edge coordinate in cm **/
  return fEcalInf->GetXPos()+
         fEcalInf->GetModuleSize()*fEcalInf->GetXSize()/2.0;
}

inline Float_t ecalStructure::GetY2() const
{
  /** get ECAL upper edge coordinate in cm **/
  return fEcalInf->GetYPos()+
         fEcalInf->GetModuleSize()*fEcalInf->GetYSize()/2.0;
}

inline Bool_t ecalStructure::AddEnergy(Float_t x, Float_t y, Float_t energy, Bool_t isPS)
{
  /** Add preshower or calorimeter energy to a cell with coordinate (x,y) **/
  ecalCell* cell=GetCell(x,y);
  if (cell)
  {
    if (isPS) ; // cell->AddPSEnergy(energy); Preshower removed
    else
      cell->AddEnergy(energy);
  }
  else
    return kFALSE;
  return kTRUE;
}

inline Float_t ecalStructure::GetEnergy(Float_t x, Float_t y, Bool_t isPS) const
{
  ecalCell* cell=GetCell(x,y);
  if (cell)
  {
    if (isPS)
      return 0; //  return cell->GetPSEnergy(); Preshower removed
    else
      return cell->GetEnergy();
  }
  return -1111;
}

//Converts (x,y) to hit Id
inline Int_t ecalStructure::GetHitId(Float_t x, Float_t y) const
{
  ecalCell* cell=GetCell(x,y);
  if (cell)
    return cell->GetCellNumber();
  else
    return -1111;
}

struct __ecalCellWrapper
{
public:
  ecalCell* cell;
  Char_t isPsTen;
};

#endif
