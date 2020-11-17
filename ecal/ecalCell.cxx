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

//-----------------------------------------------------------------------------
// Get list of 8 neighbors
void ecalCell::Create5x5Cluster()
{
  list<ecalCell*> c3;
  list<ecalCell*> c;
  list<ecalCell*>::const_iterator p;
  list<ecalCell*>::const_iterator p2;

  GetNeighborsList(c3);
  for(p=c3.begin();p!=c3.end();++p)
  {
    (*p)->GetNeighborsList(c);
    for(p2=c.begin();p2!=c.end();++p2)
      if (find(f5x5Cluster.begin(), f5x5Cluster.end(), *p2)==f5x5Cluster.end())
        f5x5Cluster.push_back(*p2);
  }
}
 
