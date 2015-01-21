#include "ecalMaximum.h"

#include "ecalCell.h"

#include "TMath.h"

#include <list>

using namespace std;

ecalMaximum::ecalMaximum(ecalCell* cell, Double_t z)
  : TObject(), 
    fCell(cell), 
    fCX(0.), 
    fCY(0.), 
    fX(0.), 
    fY(0.), 
    fMark(0),
    fTheta(0)
{
  Double_t me=cell->GetEnergy();
  Double_t e;
  Int_t i;
  list<ecalCell*> cells;
  list<ecalCell*>::const_iterator p;

  fCX=cell->GetCenterX();
  fCY=cell->GetCenterY();
  fX=cell->GetEnergy()*fCX;
  fY=cell->GetEnergy()*fCY;


  cell->GetNeighborsList(cells);
  for(p=cells.begin();p!=cells.end();++p)
  {
    fX+=(*p)->GetEnergy()*(*p)->GetCenterX();
    fY+=(*p)->GetEnergy()*(*p)->GetCenterY();
  }
  fX/=me; fY/=me;
}

ClassImp(ecalMaximum)
