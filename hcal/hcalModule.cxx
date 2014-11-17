/**  hcalModule.cxx
 *@author Mikhail Prokudin
 **
 ** HCAL module
 **/

#include "hcalModule.h"

#include <algorithm>
#include <iostream>

using std::cout;
using std::endl;
using std::map;
using std::list;

//-----------------------------------------------------------------------------
Int_t hcalModule::CountNeighbors(const std::list<hcalModule*>& lst) const
{
  Int_t c=0;
  list<hcalModule*>::const_iterator p=lst.begin();
  for(;p!=lst.end();++p)
    if (find(fNeighbors.begin(), fNeighbors.end(), *p)!=fNeighbors.end())
      ++c;

  return c;
}

//-----------------------------------------------------------------------------
void hcalModule::GetClusterEnergy(Float_t& EcalEnergy)
{
  EcalEnergy=-1;
  EcalEnergy=GetEnergy();
  list<hcalModule*>::const_iterator p;
  for(p=fNeighbors.begin();p!=fNeighbors.end();++p)
  {
    EcalEnergy+=(*p)->GetEnergy();
  }
}

