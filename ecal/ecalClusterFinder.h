/** A simple and modern version of ecalClusterFinder
 ** Produces a ecalCluster. **/

#ifndef ECALCLUSTERFINDER_H
#define ECALCLUSTERFINDER_H

#include "FairTask.h"
#include <list>

class TClonesArray;
class ecalStructure;
class ecalCell;
class ecalInf;
class ecalPreCluster;
class ecalMaximum;
class ecalClusterCalibration;

class ecalClusterFinder: public FairTask
{
public:
  /** Standard constructor **/
  ecalClusterFinder(const char* name, const Int_t verbose);
  /** Only to comply with frame work. **/
  ecalClusterFinder();

  /** Destructor **/
  virtual ~ecalClusterFinder();

  /** Finish a task **/
  virtual void Finish();

  /** Exec a task **/
  virtual void Exec(Option_t* option);

  /** Initialization **/
  virtual InitStatus Init();
  TClonesArray* InitPython(ecalStructure* structure, TClonesArray* maximums, ecalClusterCalibration* calib);

  Double_t MinMaxE() const {return fMinMaxE;}
  Double_t MinClusterE() const {return fMinClusterE;}

  /** Minimum precluster uncalibrated energy **/
  void SetMinMaxE(Double_t minmaxe=0.015) {fMinMaxE=minmaxe;} 
  /** Minimum uncalibrated energy of precluster maximum for consideration **/
  void SetMinClusterE(Double_t minmaxe=0.03) {fMinClusterE=minmaxe;} 
private:
  /** Form clusters from precluster **/
  void FormClusters();
  /** Form a preclusters **/
  void FormPreClusters();
  /** Clear a preclusters list **/
  void ClearPreClusters();
  /** Current event **/
  Int_t fEv;

  /** Array of maximums in calorimeter.
   ** Maximums belong to charged tracks excluded. **/
  TClonesArray* fMaximums;		//!
  /** An array of clusters **/
  TClonesArray* fClusters;		//!
  /** A calorimeter structure **/
  ecalStructure* fStr;			//!
  /** Cluster calibration object for photons **/
  ecalClusterCalibration* fCalib;	//!
  /** An information about calorimeter **/
  ecalInf* fInf;			//!

  /** A list of preclusters
   ** May be better use TClonesArray? **/
  std::list<ecalPreCluster*> fPreClusters;		//!

  /** Minimum precluster uncalibrated energy **/
  Double_t fMinClusterE;
  /** Minimum uncalibrated energy of precluster maximum for consideration **/
  Double_t fMinMaxE;

  ecalClusterFinder(const ecalClusterFinder&);
  ecalClusterFinder& operator=(const ecalClusterFinder&);

  ClassDef(ecalClusterFinder, 1)
};

#endif

