/**  ecalCellMC.cxx
 *@author Mikhail Prokudin
 **
 ** ECAL cell structure, a part of ECAL module. This implementation carries an MC information 
 **/

#include "ecalCellMC.h"

#include <algorithm>
#include <iostream>

using std::cout;
using std::endl;
using std::map;
using std::list;

//-----------------------------------------------------------------------------
ecalCellMC::ecalCellMC(Int_t cellnumber, Float_t x1, Float_t y1, Float_t x2, Float_t y2, Char_t type, Float_t energy)
  : ecalCell(cellnumber, x1, y1, x2, y2, type, energy),
    fTrackEnergy(),
    fTrackTime()
{
}
//-----------------------------------------------------------------------------
Float_t ecalCellMC::GetTrackTime(Int_t num) const
{
  map<Int_t, Float_t>::const_iterator p=fTrackTime.find(num);
  if (p==fTrackTime.end()) return 0; else return p->second;
}


//-----------------------------------------------------------------------------
Float_t ecalCellMC::GetTrackEnergy(Int_t num) const
{
  map<Int_t, Float_t>::const_iterator p=fTrackEnergy.find(num);
  if (p==fTrackEnergy.end()) return 0; else return p->second;
}

//-----------------------------------------------------------------------------
void ecalCellMC::ResetEnergy()
{
  ResetEnergyFast();
  fTrackEnergy.clear();
  fTrackTime.clear();
}

//-----------------------------------------------------------------------------
Float_t ecalCellMC::GetTrackClusterEnergy(Int_t num)
{
  Float_t energy=GetTrackEnergy(num);
  list<ecalCell*> cls; GetNeighborsList(cls);
  list<ecalCell*>::const_iterator p=cls.begin();
  for(;p!=cls.end();++p)
    energy+=((ecalCellMC*)(*p))->GetTrackEnergy(num);
  return energy;
}

ClassImp(ecalCellMC)

