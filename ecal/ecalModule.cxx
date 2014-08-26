/**  ecalModule.cxx
 *@author Mikhail Prokudin
 **
 ** ECAL module structure, consisting of cells
 ** Useless if we have only modules with one lightisolated cell
 **/

#include "ecalModule.h"

#include "ecalCellMC.h"

#include "TMath.h"

using std::list;
using std::vector;

//-----------------------------------------------------------------------------
ecalModule::ecalModule(char type, Int_t cellnumber, Float_t x1, Float_t y1, Float_t x2, Float_t y2, Int_t mc, Float_t energy) 
  : ecalCell(cellnumber, x1,y1,x2,y2, type, energy), 
    fDx(x2-x1), 
    fDy(y2-y1),
    fCells()
{
  if (GetType()<1) return;
	
  Int_t i;
  Int_t j;
  Int_t mt;
  Int_t num;
	
  mt=type;
  fCells.resize(mt*mt,NULL);

  num=cellnumber/100;

  if (mc==0)
    for(i=0;i<mt;i++)
      for(j=0;j<mt;j++)
        fCells[i*mt+j]=new ecalCell((num*10+i+1)*10+j+1, x1+j*fDx/mt, y1+i*fDy/mt, x1+(j+1)*fDx/mt, y1+(i+1)*fDy/mt, type);
  else 
    for(i=0;i<mt;i++)
      for(j=0;j<mt;j++)
        fCells[i*mt+j]=new ecalCellMC((num*10+i+1)*10+j+1, x1+j*fDx/mt, y1+i*fDy/mt, x1+(j+1)*fDx/mt, y1+(i+1)*fDy/mt, type);
}

//-----------------------------------------------------------------------------
ecalCell* ecalModule::Locate(Int_t x, Int_t y) const
{
  if (x<0||y<0||x>=GetType()||y>=GetType()) return NULL;
  return fCells[y*GetType()+x];
}

//-----------------------------------------------------------------------------
ecalCell* ecalModule::FindCell(Float_t x, Float_t y) const
{
  Int_t ix=(Int_t)TMath::Floor( (x-GetX1())/GetDX()*GetType() );
  Int_t iy=(Int_t)TMath::Floor( (y-GetY1())/GetDY()*GetType() );
  if (ix<0) ix=0; if (ix>=GetType()) ix=GetType()-1;
  if (iy<0) iy=0; if (iy>=GetType()) iy=GetType()-1;
  return At(ix,iy);
}

//-----------------------------------------------------------------------------
void ecalModule::AddEnergy(Float_t x, Float_t y, Float_t energy)
{
  ecalCell* tmp=FindCell(x,y);
  if (!tmp) return;
  tmp->AddEnergy(energy);
  ecalCell::AddEnergy(energy);
}

//-----------------------------------------------------------------------------
list<ecalCell*> ecalModule::GetCellsX(Float_t x) const 
{
  list<ecalCell*> tmp;
  vector<ecalCell*>::const_iterator p;

  for(p=fCells.begin();p!=fCells.end();++p)
    if (x>(*p)->GetX1()&&x<(*p)->GetX2()) tmp.push_back(*p);
  return tmp;
}

//-----------------------------------------------------------------------------
list<ecalCell*> ecalModule::GetCellsY(Float_t y) const
{
  list<ecalCell*> tmp;
  vector<ecalCell*>::const_iterator p;

  for(p=fCells.begin();p!=fCells.end();++p)
    if (y>(*p)->GetY1()&&y<(*p)->GetY2()) tmp.push_back(*p);
  return tmp;
}
