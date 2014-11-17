/**  hcalStructure.cxx
 *@author Mikhail Prokudin
 **
 ** ECAL structure, consisting of modules
 **/

#include "hcalStructure.h"

#include "hcal.h"
#include "hcalModuleMC.h"


#include <iostream>
#include <algorithm>
#include <cmath>

using namespace std;


hcalModule* hcalStructure::GetModule(Int_t volId, Int_t& section)
{
  UInt_t i;
  static Int_t volidmax = 0;
  volidmax=10000000;

  if ((Int_t)fHash.size()<volidmax)
  {
    fHash.resize(volidmax);
    for(i=0;i<fHash.size();i++)
      fHash[i]=NULL;
  }
  if (volId>volidmax)
    return NULL;
  if (fHash[volId]==NULL)
  {
    Float_t x;
    Float_t y;
    hcal::GetCellCoordInf(volId, x, y, section);
    fHash[volId]=GetModule(x+0.025,y+0.025);
  }
  section=volId%10;
  return fHash[volId];
}

//-----------------------------------------------------------------------------
void hcalStructure::Serialize()
{
  fModules.clear();
  for(UInt_t i=0;i<fStructure.size();i++)
  if (fStructure[i])
    fModules.push_back(fStructure[i]);
}

//-----------------------------------------------------------------------------
hcalModule* hcalStructure::CreateModule(char type, Int_t number, Float_t x1, Float_t y1, Float_t x2, Float_t y2)
{
  if (type!=1)
  {
    Fatal("CreateModule", "All modules in hcal should have type 1");
    return NULL;
  }
  if (fUseMC)
    return new hcalModuleMC(number, x1, y1, x2, y2);
  else
    return new hcalModule(number, x1, y1, x2, y2);
}
//-----------------------------------------------------------------------------

hcalStructure::hcalStructure(hcalInf* hcalinf)
  : TNamed("hcalStructure", "Hadron calorimeter structure"), 
    fUseMC(0),
    fX1(0.),
    fY1(0.),
    fHcalInf(hcalinf),
    fStructure(),
    fModules(),
    fHash()
{
  fX1=fHcalInf->GetXPos()-fHcalInf->GetModuleSize()*fHcalInf->GetXSize()/2.0;
  fY1=fHcalInf->GetYPos()-fHcalInf->GetModuleSize()*fHcalInf->GetYSize()/2.0;
}

//-----------------------------------------------------------------------------
void hcalStructure::Construct()
{
  if (!fHcalInf) return;

  Float_t x1=GetX1();
  Float_t y1=GetY1();
  Float_t x;
  Float_t y;
  Float_t dx;
  Float_t dy;
  Int_t i;
  Int_t j;
  Int_t k;
  Int_t number;
  char type;

  fStructure.resize(fHcalInf->GetXSize()*fHcalInf->GetYSize(), NULL);
	
  dx=fHcalInf->GetModuleSize();
  dy=fHcalInf->GetModuleSize();
  //Creating ECAL Matrix
  for(i=0;i<fHcalInf->GetXSize();i++)
    for(j=0;j<fHcalInf->GetYSize();j++) {
      type=fHcalInf->GetType(i,j);
      if (type) {
	x=x1+i*dx;
	y=y1+j*dy;
	number=(i*100+j)*100;
	fStructure[GetNum(i,j)]=CreateModule(type,number,x,y,x+dx,y+dy);
      }
      else
	fStructure[GetNum(i,j)]=NULL;
    }
#ifdef _DECALSTRUCT
  Info("Construct()", "Calorimeter matrix created.");
#endif
  //Now HCAL matrix created
  list<hcalModule*> neib;
  vector<hcalModule*> cl;
  vector<hcalModule*>::const_iterator pcl;
  
  Int_t num;
  //We want neighbors for ecalModules be ecalModules
  for(i=0;i<fHcalInf->GetXSize();i++)
    for(j=0;j<fHcalInf->GetYSize();j++)
      if (fStructure[GetNum(i,j)]) {
	neib.clear();
	
	num=GetNumber(i-1,j);
	if (-1!=num) {
	  neib.push_back(fStructure[num]);
	}
			
	num=GetNumber(i-1,j+1);
	if (-1!=num) {
	  neib.push_back(fStructure[num]);
	}
	
	num=GetNumber(i,j+1);
	if (-1!=num) {
	  neib.push_back(fStructure[num]);
	}
	
	num=GetNumber(i+1,j+1);
	if (-1!=num) {
	  neib.push_back(fStructure[num]);
	}
	
	num=GetNumber(i+1,j);
	if (-1!=num) {
	  neib.push_back(fStructure[num]);
	}
			
	num=GetNumber(i+1,j-1);
	if (-1!=num) {
	  neib.push_back(fStructure[num]);
	}
	
	num=GetNumber(i,j-1);
	if (-1!=num) {
	  neib.push_back(fStructure[num]);
	}
	
	num=GetNumber(i-1,j-1);
	if (-1!=num) {
	  neib.push_back(fStructure[num]);
	}
	
	num=GetNumber(i,j);
	fStructure[num]->SetNeighborsList(neib);
      }
  Serialize();
}

//-----------------------------------------------------------------------------
void hcalStructure::ResetModules()
{
  list<hcalModule*>::const_iterator p=fModules.begin();
  if (fUseMC==0)
  {
    for(;p!=fModules.end();++p)
      (*p)->ResetEnergyFast();
  }
  else
  {
    for(;p!=fModules.end();++p)
    ((hcalModuleMC*)(*p))->ResetEnergy();
  }
}

//-----------------------------------------------------------------------------
void hcalStructure::GetHitXY(const Int_t hitId, Float_t& x, Float_t& y) const
{
  /** Hit Id -> (x,y) **/

  // Some translation from x*100+y  to y*sizex+x coding...
 
  Int_t mnum=hitId/10;
  Int_t cellx = mnum/100;
  Int_t celly = mnum%100;
  mnum = GetNum(cellx, celly);
  
  // end translation

  hcalModule* module=fStructure[mnum];
  if (module==NULL) return;
  x=module->GetCenterX();
  y=module->GetCenterY();
}

//-----------------------------------------------------------------------------
hcalModule* hcalStructure::GetHitModule(const Int_t hitId) const
{
  /** Hit Id -> Cell **/
 
  // Some translation from x*100+y  to y*sizex+x coding...
 
  Int_t mnum=hitId/10;
  Int_t cellx = mnum/100;
  Int_t celly = mnum%100;
  mnum = GetNum(cellx, celly);
  
  // end translation

  return fStructure[mnum];
}
