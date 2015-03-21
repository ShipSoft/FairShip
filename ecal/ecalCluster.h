#ifndef ECALCLUSTER_H
#define ECALCLUSTER_H

#include "TObject.h"
#include "TArrayI.h"
#include "TArrayD.h"
#include <list>

#include "ecalCell.h"

class ecalMaximum;

struct ecalClusterSortProcess : public std::binary_function<ecalCell*, ecalCell*, Bool_t>
{
  inline Bool_t operator()(const ecalCell* left, const ecalCell* right) const
  {
    if (left->GetEnergy()<right->GetEnergy())
      return kTRUE;
    return kFALSE;
  }
};

/** A temporary cluster needed for debugging of cluster finder procedure **/
class ecalCluster : public TObject
{
friend class ecalClusterFinder;
public:
  /** An empty constructor **/
  ecalCluster();
  /** A more advanced constructor. Should use this. **/
  ecalCluster(Int_t num, const std::list<ecalCell*>& cluster, const std::list<ecalMaximum*>& maximums);
  /** Number of cluster in event **/
  inline Int_t Number() const {return fNum;}
  /** Size of cluster **/
  inline Int_t Size() const {return fSize;}
  /** Number of maximums in cluster **/
  inline Int_t Maxs() const {return fMaxs;}
  /** Energy of cluster **/
  inline Double_t Energy() const {return fEnergy;}
  /** Calibrated energy of the cluster with assumption of normal incident angle **/
  inline Double_t PreCalibrated() const {return fPreCalibrated;}
  /** Second moment **/
  inline Double_t Moment() const {return fMoment;}
  /** Moment over X axis **/
  inline Double_t MomentX() const {return fMomentX;}
  /** Moment over Y axis **/
  inline Double_t MomentY() const {return fMomentY;}
  /** Coordinates of cluster centre of gravity **/
  inline Double_t X() const {return fX;}
  inline Double_t Y() const {return fY;}
  /** \chi^2 of cluster after fitting **/
  inline Double_t Chi2() const {return fChi2;}
  /** Status of the cluster: -1 --- rejected, 0 --- new, 1 --- reconstructed **/
  inline Short_t Status() const {return fStatus;}
  inline void SetStatus(Short_t st) {fStatus=st;}

  /** Getters for cells and peaks **/
  inline Int_t CellNum(Int_t i) const {return fCellNums[i];}
  inline Int_t PeakNum(Int_t i) const {return fPeakNums[i];}
  inline Double_t PreEnergy(Int_t i) const {return fPreEnergy[i];}
  inline ecalMaximum* Maximum(Int_t i) const {return fMaximums[i];}
  /** An virtual destructor **/
  virtual ~ecalCluster();
private:
  /** Cluster number **/
  Int_t fNum;
  /** Cluster size in cells
   ** A separate variable. fCells not stored **/
  Int_t fSize;
  /** Number of maximums in cluster **/
  Int_t fMaxs;
  /** Energy of cluster **/
  Double_t fEnergy;
  /** Calibrated energy of the cluster with assumption of normal incident angle **/
  Double_t fPreCalibrated;
  /** Second moment **/
  Double_t fMoment;
  /** Moment over X axis **/
  Double_t fMomentX;
  /** Moment over Y axis **/
  Double_t fMomentY;
  /** Coordinates of cluster centre of gravity **/
  Double_t fX;
  Double_t fY;
  /** \chi^2 after fitting **/
  Double_t fChi2;
  /** Status of the cluster: -1 --- rejected, 0 --- new, 1 --- reconstructed **/
  Short_t fStatus;
  
  /** Serial numbers of cells in cluster **/
  TArrayI fCellNums;
  /** Serial numbers of peaks in cluster **/
  TArrayI fPeakNums;
  /** An energy deposition in peak areas  (preclusters)  **/
  TArrayD fPreEnergy;
  /** Serial numbers of maximums in system **/
  ecalMaximum** fMaximums;		//!

  ecalCluster(const ecalCluster&);
  ecalCluster& operator=(const ecalCluster&);

  ClassDef(ecalCluster, 2)
};

#endif
