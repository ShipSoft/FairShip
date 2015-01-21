/** A helper class for cluster finder
 ** Need refactoring. April 2011 //Dr.Sys **/
#ifndef ECALPRECLUSTER_H
#define ECALPRECLUSTER_H

#include "ecalCell.h"
#include "ecalMaximum.h"

#include <list>
//#include <iostream>

class ecalPreCluster
{
public:
  ecalPreCluster(const std::list<ecalCell*> cells, ecalCell* max, Double_t energy=-1111.0) 
    : fCells(cells), fMaximum(max), fEnergy(energy), fMax(NULL), fMark(0) 
  {
  }

  ecalPreCluster(const std::list<ecalCell*> cells, ecalMaximum* max, Double_t energy=-1111.0) 
    : fCells(cells), fMaximum(max->Cell()), fEnergy(energy), fMax(max), fMark(0) 
  {
//    std::cout << "list: " << fEnergy << std::endl;
  }

  ecalPreCluster(ecalCell** cells, Int_t size, ecalCell* max, Double_t energy=-1111.0)
    : fCells(), fMaximum(max), fEnergy(energy), fMax(NULL), fMark(0) 
  {
    fCells.clear();
    for(Int_t i=0;i<size;i++)
      fCells.push_back(cells[i]);
  }

  ecalPreCluster(ecalCell** cells, Int_t size, ecalMaximum* max, Double_t energy=-1111.0)
    : fCells(), fMaximum(max->Cell()), fEnergy(energy), fMax(max), fMark(0) 
  {
    fCells.clear();
    for(Int_t i=0;i<size;i++)
      fCells.push_back(cells[i]);
  }

  std::list<ecalCell*> fCells;
  ecalCell* fMaximum;
  Double_t fEnergy;
  ecalMaximum* fMax;		//!
  Int_t fMark;

 private:
  ecalPreCluster(const ecalPreCluster&);
  ecalPreCluster& operator=(const ecalPreCluster&);
};

#endif
