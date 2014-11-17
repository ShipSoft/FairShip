/**  hcalStructure.h
 *@author Mikhail Prokudin
 **
 ** HCAL structure, consisting of modules
 **/

#ifndef HCALSTRUCTURE_H
#define HCALSTRUCTURE_H

#include "hcalInf.h"
#include "hcalModule.h"

#include "TMath.h"
#include "TNamed.h"

#include <vector>

#define _DHCALSTRUCT

class hcalStructure : public TNamed
{
public:
  hcalStructure(hcalInf* hcalinf);
  void SetUseMC(Int_t mc=0) {fUseMC=mc;}
  Int_t GetUseMC() const {return fUseMC;}
  void Construct();
  Int_t GetNumber(Int_t x, Int_t y) const;
  
  Bool_t AddEnergy(Float_t x, Float_t y, Float_t energy, Float_t energy2);
  Float_t GetEnergy(Float_t x, Float_t y, Int_t section=0) const;
  hcalModule* GetModule(Float_t x, Float_t y) const;
  Int_t GetModuleNumber(Float_t x, Float_t y) const;
  
  Float_t GetX1() const {return fX1;};
  Float_t GetY1() const {return fY1;};
  Float_t GetX2() const;
  Float_t GetY2() const;
  inline hcalInf* GetHcalInf() const {return fHcalInf;}
  inline void GetStructure(std::vector<hcalModule*>& stru) const {stru=fStructure;}
  inline void GetModules(std::list<hcalModule*>& mdls) const {mdls=fModules;}
  void ResetModules();
  
  hcalModule* CreateModule(char type, Int_t number, Float_t x1, Float_t y1, Float_t x2, Float_t y2);
  //Some usefull procedures for hit processing
  
  //Converts (x,y) to hit Id
  Int_t GetHitId(Float_t x, Float_t y) const;
  //Hit Id -> (x,y)
  void GetHitXY(const Int_t hitId, Float_t& x, Float_t& y) const;

  hcalModule* GetModule(Int_t fVolId, Int_t& section);
  //Hit It -> Cell
  hcalModule* GetHitModule(const Int_t hitId) const;

private:
  Int_t GetNum(Int_t x, Int_t y) const;
  
private:
  /** Creates modules lists **/
  void Serialize();
  /** Use store MC information in modules **/
  Int_t fUseMC;
  /** X coordibate of left bottom angle of ECAL **/
  Float_t fX1;
  /** Y coordibate of left bottom angle of ECAL **/
  Float_t fY1;
  /** HCAL geometry container **/
  hcalInf* fHcalInf;
  /** vector of HCAL modules **/
  std::vector<hcalModule*> fStructure;
  /** All ECAL modules **/
  std::list<hcalModule*> fModules;
  /** MCPoint id -> HCAL mdoule**/
  std::vector<hcalModule*> fHash;

  hcalStructure(const hcalStructure&);
  hcalStructure& operator=(const hcalStructure&);

  ClassDef(hcalStructure,1);
};

inline hcalModule* hcalStructure::GetModule(Float_t x, Float_t y) const
{
  /** get ECAL module by known module center coordinate (x,y) **/
  Int_t num=GetModuleNumber(x,y);
  if (-1==num) return NULL; else return fStructure[num]; 
}

inline Int_t  hcalStructure::GetModuleNumber(Float_t x, Float_t y) const
{
  /** get ECAL module by known module center coordinate (x,y) **/
  Int_t ix=(Int_t)TMath::Floor((x-GetX1())/fHcalInf->GetModuleSize());
  Int_t iy=(Int_t)TMath::Floor((y-GetY1())/fHcalInf->GetModuleSize());
  return GetNumber(ix,iy);
}

inline Int_t hcalStructure::GetNumber(Int_t x, Int_t y) const
{
  /** get ECAL absolute module number by known module relative number (x,y)
   ** with check for the ECAL boundaries **/
  if (x>-1&&y>-1)
    if (x<fHcalInf->GetXSize()&&y<fHcalInf->GetYSize())
      return GetNum(x,y);
  return -1;
}

inline Int_t hcalStructure::GetNum(Int_t x, Int_t y) const
{
  /** get ECAL absolute module number by known module relative number (x,y) **/
  return y*fHcalInf->GetXSize()+x;
}

inline Float_t hcalStructure::GetX2() const
{
  /** get ECAL right edge coordinate in cm **/
  return fHcalInf->GetXPos()+fHcalInf->GetModuleSize()*fHcalInf->GetXSize()/2.0;
}

inline Float_t hcalStructure::GetY2() const
{
  /** get ECAL upper edge coordinate in cm **/
  return fHcalInf->GetYPos()+fHcalInf->GetModuleSize()*fHcalInf->GetYSize()/2.0;
}

inline Bool_t hcalStructure::AddEnergy(Float_t x, Float_t y, Float_t energy, Float_t energy2)
{
  /** Add preshower or calorimeter energy to a module with coordinate (x,y) **/
  hcalModule* mdl=GetModule(x,y);
  if (mdl)
  {
    mdl->AddEnergy(energy);
    mdl->AddEnergy2(energy2);
  }
  else
    return kFALSE;
  return kTRUE;
}

inline Float_t hcalStructure::GetEnergy(Float_t x, Float_t y, Int_t section) const
{
  hcalModule* mdl=GetModule(x,y);
  if (mdl)
  {
    if (section==1)
      return mdl->GetEnergy2();
    else
      return mdl->GetEnergy();
  }
  return -1111;
}

//Converts (x,y) to hit Id
inline Int_t hcalStructure::GetHitId(Float_t x, Float_t y) const
{
  hcalModule* mdl=GetModule(x,y);
  if (mdl)
    return mdl->GetNumber();
  else
    return -1111;
}

#endif
