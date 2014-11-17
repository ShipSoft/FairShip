/** Creates a hcalStructure and fill it with Hits/SHits/MCPoints **/

/**  hcalStructureFiller.h
 *@author //Dr.Sys
 **
 ** Class for producing either HCAL hits
 ** or HCAL summable hits from MCPoints,
 **  Definitions:
 ** HCAL hit is total deposited energy by all track in HCAL module
 ** HCAL summable hit is a deposited energy by each tracks in HCAL module
 **/

#ifndef HCALSTRUCTUREFILLER_H
#define HCALSTRUCTUREFILLER_H

#include "FairTask.h"
#include "TString.h"
#include "TVector3.h"

class hcalInf;
class hcalStructure;
class TClonesArray;

class hcalStructureFiller : public FairTask {

public:
  /** Default constructor **/
  hcalStructureFiller();

  /** Standard constructor **/
  hcalStructureFiller(const char *name, const Int_t iVerbose=1, const char* fileGeo="hcal.geo");

  /** Destructor **/
  virtual ~hcalStructureFiller();

  /** Initialization of the task **/  
  virtual InitStatus Init();

  /** Executed task **/ 
  virtual void Exec(Option_t* option);

  /** Finish task **/ 
  virtual void Finish();

  /** Set data source for hit producer.
   ** This must be called before Init()
   ** (No effect other case)! **/
  void SetUseMCPoints(Bool_t UseMCPoints);

  hcalStructure* GetStructure() const;
  void StoreTrackInformation(Bool_t storetrackinfo=kTRUE);
  Bool_t GetStoreTrackInformation() const;

  Bool_t GetUseMCPoints() const;
  Bool_t GetUseSummableHits() const;
  Bool_t GetUseHits() const;
protected:

private:
  /** Init parameter containers **/
  void SetParContainers();
  /** Loop over MCPoints **/
  void LoopForMCPoints();
  hcalStructure* fStr;
  hcalInf* fInf;		//HCAL geometry container

  TClonesArray* fListHCALpts;   //HCAL MC points
  Int_t fEvent;                 //! Internal event counter

  /** Is Init() already done? **/
  Bool_t fInited;
  /** Should we take data from MCPoints? **/
  Bool_t fUseMCPoints;

  /** Should we store information about tracks/energy depostion **/
  Bool_t fStoreTrackInfo;
  /** Geo file to use **/
  TString fFileGeo;

  hcalStructureFiller(const hcalStructureFiller&);
  hcalStructureFiller& operator=(const hcalStructureFiller&);

  ClassDef(hcalStructureFiller,1)

};

inline void hcalStructureFiller::SetUseMCPoints(Bool_t UseMCPoints)
{
  if (fInited) return;
  fUseMCPoints=UseMCPoints;
}

inline Bool_t hcalStructureFiller::GetUseMCPoints() const
{
  return fUseMCPoints;
}

inline void hcalStructureFiller::StoreTrackInformation(Bool_t storetrackinfo)
{
  if (fInited) return;
  fStoreTrackInfo=storetrackinfo;
}

inline Bool_t hcalStructureFiller::GetStoreTrackInformation() const
{
  return fStoreTrackInfo;
}

inline hcalStructure* hcalStructureFiller::GetStructure() const
{
  return fStr;
}

#endif
