/* Reconstruction for the calorimeter
 * Operates over EcalClusters 
 * Very simple at the momemnt: no real unfolding by tries to divide energy deposition in common cells. */

#ifndef ECALRECO
#define ECALRECO

#include "FairTask.h"

class TClonesArray;
class ecalStructure;
class ecalClusterCalibration;
class ecalCell;
class ecalCluster;

class ecalReco : public FairTask
{
public:
  /** Standard constructor **/
  ecalReco(const char* name, const Int_t verbose);
  /** Only to comply with frame work. **/
  ecalReco();

  /** Finish a task **/
  virtual void Finish();
  /** Exec a task **/
  virtual void Exec(Option_t* option);
  /** Initialization **/
  virtual InitStatus Init();
  TClonesArray* InitPython(TClonesArray* clusters, ecalStructure* str, ecalClusterCalibration* calib);
  /** Destructor **/
  ~ecalReco();
private:
  void ReconstructXY(ecalCell* max, Float_t& x, Float_t& y);
  void TryReconstruct(ecalCluster* cls, Int_t clsnum);
  /** Current event **/
  Int_t fEv;
  /** Current reconstructed particle **/
  Int_t fN;
  /** Number of rejected clusters **/
  Int_t fRejected;
  /** Number of maximums in rejected clusters **/
  Int_t fRejectedP;

  /** An array of clusters **/
  TClonesArray* fClusters;		//!
  /** Array of reconstructed objects **/
  TClonesArray* fReconstucted;		//!
  /** A calorimeter structure **/
  ecalStructure* fStr;			//!
  /** Cluster calibration object for photons **/
  ecalClusterCalibration* fCalib;	//!

  ClassDef(ecalReco, 1)
};

#endif
