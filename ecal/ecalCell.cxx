/**  ecalCell.cxx
 *@author Mikhail Prokudin
 **
 ** ECAL cell structure, a part of ECAL module
 **/

#include "ecalCell.h"

#include <algorithm>
#include <iostream>

using std::cout;
using std::endl;
using std::map;
using std::list;

//-----------------------------------------------------------------------------
Int_t ecalCell::CountNeighbors(const std::list<ecalCell*>& lst) const
{
  Int_t c=0;
  list<ecalCell*>::const_iterator p=lst.begin();
  for(;p!=lst.end();++p)
    if (find(fNeighbors.begin(), fNeighbors.end(), *p)!=fNeighbors.end())
      ++c;

  return c;
}

//-----------------------------------------------------------------------------
void ecalCell::GetClusterEnergy(Float_t& EcalEnergy)
{
  EcalEnergy=-1;
  EcalEnergy=GetEnergy();
  list<ecalCell*>::const_iterator p;
  for(p=fNeighbors.begin();p!=fNeighbors.end();++p)
  {
    EcalEnergy+=(*p)->GetEnergy();
  }
}

