/**  ecalStructure.cxx
 *@author Mikhail Prokudin
 **
 ** ECAL structure, consisting of modules
 **/

#include "ecalStructure.h"

#include "ecal.h"
#include "ecalCellMC.h"

#include "ecalCell.h"

#include <iostream>
#include <algorithm>
#include <cmath>

using namespace std;


ecalCell* ecalStructure::GetCell(Int_t volId, Int_t& ten, Bool_t& isPS)
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
    Bool_t lisPS;
    Int_t iten;
    Float_t x;
    Float_t y;
    fHash[volId]=new __ecalCellWrapper();
    lisPS=ecal::GetCellCoordInf(volId, x, y, iten);
    fHash[volId]->cell=GetCell(x+0.025,y+0.025);
    fHash[volId]->isPsTen=iten*2;
    if (lisPS) fHash[volId]->isPsTen+=1;
  }
  ten=fHash[volId]->isPsTen/2;
  isPS=fHash[volId]->isPsTen%2;
  return fHash[volId]->cell;
}

//-----------------------------------------------------------------------------
void ecalStructure::Serialize()
{
  fCells.clear();
  for(UInt_t i=0;i<fStructure.size();i++)
  if (fStructure[i])
  {
    vector<ecalCell*> cells=fStructure[i]->GetCells();
    copy(cells.begin(),cells.end(), back_inserter(fCells));
  }
}

//-----------------------------------------------------------------------------
ecalModule* ecalStructure::CreateModule(char type, Int_t number, Float_t x1, Float_t y1, Float_t x2, Float_t y2)
{
  return new ecalModule(type, number, x1, y1, x2, y2, fUseMC);
}
//-----------------------------------------------------------------------------

ecalStructure::ecalStructure(ecalInf* ecalinf)
  : TNamed("ecalStructure", "Calorimeter structure"), 
    fUseMC(0),
    fX1(0.),
    fY1(0.),
    fEcalInf(ecalinf),
    fStructure(),
    fCells(),
    fHash()
{
  fX1=fEcalInf->GetXPos()-\
    fEcalInf->GetModuleSize()*fEcalInf->GetXSize()/2.0;
  fY1=fEcalInf->GetYPos()-\
    fEcalInf->GetModuleSize()*fEcalInf->GetYSize()/2.0;
}

//-----------------------------------------------------------------------------
void ecalStructure::Construct()
{
  if (!fEcalInf) return;

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

  fStructure.resize(fEcalInf->GetXSize()*fEcalInf->GetYSize(), NULL);
	
  dx=fEcalInf->GetModuleSize();
  dy=fEcalInf->GetModuleSize();
  //Creating ECAL Matrix
  for(i=0;i<fEcalInf->GetXSize();i++)
    for(j=0;j<fEcalInf->GetYSize();j++) {
      type=fEcalInf->GetType(i,j);
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
  cerr << "-I- ecalStructure::Construct(): calorimeter matrix created." << endl;
#endif
  //Now ECAL matrix created
  list<ecalCell*> neib;
  vector<ecalCell*> cl;
  vector<ecalCell*>::const_iterator pcl;
  
  Int_t num;
  //We want neighbors for ecalModules be ecalModules
  for(i=0;i<fEcalInf->GetXSize();i++)
    for(j=0;j<fEcalInf->GetYSize();j++)
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
	cl=fStructure[num]->GetCells();
	for(pcl=cl.begin();pcl!=cl.end();++pcl)
	  CreateNLists(*pcl);
      }
  Serialize();
}

//-----------------------------------------------------------------------------
void _add_not_null(ecalModule* mod, list<ecalModule*>& lst)
{
  if (mod)
    if (find(lst.begin(),lst.end(),mod)==lst.end())	
      lst.push_back(mod);
}

//-----------------------------------------------------------------------------
void _add_not_null(list<ecalCell*> from, list<ecalCell*>& where)
{
  list<ecalCell*>::const_iterator p;
  for(p=from.begin();p!=from.end();++p)
    if (find(where.begin(),where.end(),(*p))==where.end())
      //this p uniq!
      where.push_back(*p);
}

//-----------------------------------------------------------------------------
void _add_not_null(ecalCell* cell, list<ecalCell*>& lst)
{
  if (find(lst.begin(),lst.end(),cell)==lst.end())	
    lst.push_back(cell);
}

//-----------------------------------------------------------------------------
void ecalStructure::CreateNLists(ecalCell* cell)
{
  Float_t x=cell->GetCenterX();
  Float_t y=cell->GetCenterY();
  Float_t dx=(cell->GetX2()-cell->GetX1())/2.0;
  Float_t dy=(cell->GetX2()-cell->GetX1())/2.0;
  Float_t x1;
  Float_t x2;
  Float_t y1;
  Float_t y2;
  Float_t mx1=cell->GetX1();
  Float_t mx2=cell->GetX2();
  Float_t my1=cell->GetY1();
  Float_t my2=cell->GetY2();
  Float_t cx;
  Float_t cy;
  Float_t d=0.1;
  Float_t dd=1e-6;
  list<ecalCell*> neib;
  list<ecalCell*> tl;
  list<ecalModule*> tml; 
  list<ecalModule*>::const_iterator ptml;
  list<ecalCell*>::const_iterator ptl;
  Int_t i;

  neib.clear();

  tml.clear();
  _add_not_null(GetModule(x-2*dx,y-2*dy),tml);
  _add_not_null(GetModule(x-2*dx,y     ),tml);
  _add_not_null(GetModule(x-2*dx,y+2*dy),tml);
  _add_not_null(GetModule(x     ,y-2*dy),tml);
  _add_not_null(GetModule(x     ,y     ),tml);
  _add_not_null(GetModule(x     ,y+2*dy),tml);
  _add_not_null(GetModule(x+2*dx,y-2*dy),tml);
  _add_not_null(GetModule(x+2*dx,y     ),tml);
  _add_not_null(GetModule(x+2*dx,y+2*dy),tml);
  if (tml.empty()) {
    cerr << "Error during creating neighbors lists." << endl;
    cerr << "Can't' find any modules neighbors to cell." << endl;
    cerr << "Cell: CenterX=" << x << ", CenterY=" << y << "." << endl; 
    return;
  }
  tl.empty();
  for(ptml=tml.begin();ptml!=tml.end();++ptml) {
    _add_not_null((*ptml)->GetCellsY(y-dy-d),tl);
    _add_not_null((*ptml)->GetCellsY(y+dy+d),tl);
    _add_not_null((*ptml)->GetCellsX(x-dx-d),tl);
    _add_not_null((*ptml)->GetCellsX(x+dx+d),tl);
  }
  if (tl.empty()) {
    cerr << "Error during creating neighbors lists." << endl;
    cerr << "Can't' find any cells neighbors to cell." << endl;
    cerr << "Cell: CenterX=" << x << ", CenterY=" << y << "." << endl; 
    return;
  }
  for(ptl=tl.begin();ptl!=tl.end();++ptl) {
    x1=(*ptl)->GetX1();
    x2=(*ptl)->GetX2();
    y1=(*ptl)->GetY1();
    y2=(*ptl)->GetY2();
    cx=(*ptl)->GetCenterX();
    cy=(*ptl)->GetCenterY();
    if (fabs(mx1-x2)<dd) {
      if ((cy-y+2*dy>-dd&&cy-y-dy/2<dd)||fabs(y-dy-y1)<dd||fabs(y-dy-y2)<dd) {
	_add_not_null((*ptl),neib);
      }
      if ((cy-y-2*dy<dd&&cy-y+dy/2>-dd)||fabs(y+dy-y1)<dd||fabs(y+dy-y2)<dd) {
	_add_not_null((*ptl),neib);
      }
    }
    if (fabs(my1-y2)<dd) {
      if ((cx-x+2*dx>-dd&&cx-x-dx/2<dd)||fabs(x-dx-x1)<dd||fabs(x-dx-x2)<dd) {
	_add_not_null((*ptl),neib);
      }
      if ((cx-x-2*dx<dd&&cx-x+dx/2>-dd)||fabs(x+dx-x1)<dd||fabs(x+dx-x2)<dd) {
	_add_not_null((*ptl),neib);
      }
    }
    if (fabs(mx2-x1)<dd) {
      if ((cy-y+2*dy>-dd&&cy-y-dy/2<dd)||fabs(y-dy-y1)<dd||fabs(y-dy-y2)<dd) {
	_add_not_null((*ptl),neib);
      }
      if ((cy-y-2*dy<dd&&cy-y+dy/2>-dd)||fabs(y+dy-y1)<dd||fabs(y+dy-y2)<dd) {
	_add_not_null((*ptl),neib);
      }
    }
    if (fabs(my2-y1)<dd) {
      if ((cx-x+2*dx>-dd&&cx-x-dx/2<dd)||fabs(x-dx-x1)<dd||fabs(x-dx-x2)<dd) {
	_add_not_null((*ptl),neib);
      }
      if ((cx-x-2*dx<dd&&cx-x+dx/2>-dd)||fabs(x+dx-x1)<dd||fabs(x+dx-x2)<dd) {
	_add_not_null((*ptl),neib);
      }
    }
    
  }
  cell->SetNeighborsList(neib);
}

//-----------------------------------------------------------------------------
void ecalStructure::ResetModules()
{
  list<ecalCell*>::const_iterator p=fCells.begin();
  if (fUseMC==0)
  {
    for(;p!=fCells.end();++p)
      (*p)->ResetEnergyFast();
  }
  else
  {
    for(;p!=fCells.end();++p)
    ((ecalCellMC*)(*p))->ResetEnergy();
  }
}

//-----------------------------------------------------------------------------
void ecalStructure::GetHitXY(const Int_t hitId, Float_t& x, Float_t& y) const
{
  /** Hit Id -> (x,y) **/

  // Some translation from x*100+y  to y*sizex+x coding...
 
  Int_t mnum=hitId/100;
  Int_t cellx = mnum/100;
  Int_t celly = mnum%100;
  mnum = GetNum(cellx, celly);
  
  // end translation

  ecalModule* module=fStructure[mnum];
  ecalCell* cell;

  Int_t cellnum=hitId%100;
  // change place
  Int_t cx=cellnum%10-1;
  Int_t cy=cellnum/10-1;

  if (module==NULL||cx<0||cy<0||cx>=module->GetType()||cy>=module->GetType()) {x=0; y=0; return;}
  cell=module->At(cx,cy);
  x=cell->GetCenterX();
  y=cell->GetCenterY();
}

//-----------------------------------------------------------------------------
ecalCell* ecalStructure::GetHitCell(const Int_t hitId) const
{
  /** Hit Id -> Cell **/
 
  // Some translation from x*100+y  to y*sizex+x coding...
 
  Int_t mnum=hitId/100;
  Int_t cellx = mnum/100;
  Int_t celly = mnum%100;
  mnum = GetNum(cellx, celly);
  
  // end translation

  ecalModule* module=fStructure[mnum];

  Int_t cellnum=hitId%100;
  Int_t cx=cellnum%10-1;
  Int_t cy=cellnum/10-1;

  if (module==NULL||cx<0||cy<0||cx>=module->GetType()||cy>=module->GetType()) 
    return NULL;
//  cout << hitId << " --- " << module->At(cx,cy)->GetCellNumber() << endl;
  return module->At(cx,cy);
}

//-----------------------------------------------------------------------------

void ecalStructure::GetGlobalCellXY(const Int_t hitId, Int_t& x, Int_t& y) const
{


  Int_t modulenum = hitId/100;
  Int_t cellx = modulenum/100;
  Int_t celly = modulenum%100; 

  Int_t innernum =  hitId%100;
  Int_t iny = innernum/10;
  Int_t inx = innernum%10;
  Int_t msize = fEcalInf->GetType(cellx,celly);

   
  x = (cellx-1)* msize + inx;
  y = (celly-1)* msize + iny;

}
//
Int_t ecalStructure::GetType(const Int_t hitId) const
{
  Int_t modulenum = hitId/100;
  Int_t cellx = modulenum/100;
  Int_t celly = modulenum%100; 

  Int_t msize = fEcalInf->GetType(cellx,celly);
  return msize;
}
