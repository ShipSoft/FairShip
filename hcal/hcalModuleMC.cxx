/**  hcalModuleMC.cxx
 *@author Mikhail Prokudin
 **
 ** HCAL module. This implementation carries an MC information 
 **/

#include "hcalModuleMC.h"

#include <algorithm>
#include <iostream>

using std::cout;
using std::endl;
using std::map;
using std::list;

//-----------------------------------------------------------------------------
hcalModuleMC::hcalModuleMC(Int_t number, Float_t x1, Float_t y1, Float_t x2, Float_t y2)
  : hcalModule(number, x1, y1, x2, y2),
    fTrackEnergy(),
    fTrackEnergy2()
{
}

//-----------------------------------------------------------------------------
Float_t hcalModuleMC::GetTrackEnergy(Int_t num) const
{
  map<Int_t, Float_t>::const_iterator p=fTrackEnergy.find(num);
  if (p==fTrackEnergy.end()) return 0; else return p->second;
}

//-----------------------------------------------------------------------------
Float_t hcalModuleMC::GetTrackEnergy2(Int_t num) const
{
  map<Int_t, Float_t>::const_iterator p=fTrackEnergy2.find(num);
  if (p==fTrackEnergy2.end()) return 0; else return p->second;
}

//-----------------------------------------------------------------------------
void hcalModuleMC::ResetEnergy()
{
  ResetEnergyFast();
  fTrackEnergy.clear();
  fTrackEnergy2.clear();
}

//-----------------------------------------------------------------------------
Float_t hcalModuleMC::GetTrackClusterEnergy(Int_t num)
{
  Float_t energy=GetTrackEnergy(num);
  list<hcalModule*> mdls; GetNeighborsList(mdls);
  list<hcalModule*>::const_iterator p=mdls.begin();
  for(;p!=mdls.end();++p)
    energy+=((hcalModuleMC*)(*p))->GetTrackEnergy(num);
  return energy;
}

ClassImp(hcalModuleMC)

