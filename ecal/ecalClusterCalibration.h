// A very simple digitization scheme for Ship ECAL
// Operate over ecalStructure

#ifndef ECALCLUSTERCALIBRATION_H
#define ECALCLUSTERCALIBRATION_H

#include "FairTask.h"

#include <map>

class TFormula;

class ecalClusterCalibration : public FairTask
{
public:
  /** Default constructor **/
  ecalClusterCalibration();
  /** Standard constructor. Use this **/
  ecalClusterCalibration(const char* name, Int_t iVerbose=0);
  /** Destructor **/
  virtual ~ecalClusterCalibration();
  /** Initialization of the task **/  
  virtual InitStatus Init();
  ecalClusterCalibration* InitPython() {return this;}
  /** Executed task **/ 
  virtual void Exec(Option_t* option);
  /** Finish task **/ 
  virtual void Finish();
 
  void SetStraightCalibration(Int_t celltype, TFormula* f)
    {fStraightCalibration[celltype]=f;}
  void SetCalibration(Int_t celltype, TFormula* f)
    {fCalibration[celltype]=f;}

  TFormula* StraightCalibration(Int_t celltype) const
    {return fStraightCalibration[celltype];}
  TFormula* Calibration(Int_t celltype) const
    {return fCalibration[celltype];}

  /** Calibration if only cluster energy is known **/
  Double_t Calibrate(Int_t celltype, Double_t energy);
  /** Calibration if theta and cluster energy is known **/
  Double_t Calibrate(Int_t celltype, Double_t energy, Double_t theta);
private:
  // Calibration if only energy deposition in cluster.
  // One formula for each cell type
  TFormula* fStraightCalibration[10];		//!
  // Calibration if the vertex is known
  TFormula* fCalibration[10];			//!

  ecalClusterCalibration(const ecalClusterCalibration&);
  ecalClusterCalibration& operator=(const ecalClusterCalibration&);

  ClassDef(ecalClusterCalibration, 1);
};

#endif
