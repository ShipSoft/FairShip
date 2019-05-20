/** Creates a ecalStructure and fill it with Hits/SHits/MCPoints **/

/**  ecalStructureFiller.h
 *@author //Dr.Sys
 **
 ** Class for producing either ECAL hits
 ** or ECAL summable hits from MCPoints,
 **  Definitions:
 ** ECAL hit is total deposited energy by all track in ECAL cell
 ** ECAL summable hit is a deposited energy by each tracks in ECAL cell
 **/

#ifndef ECALSTRUCTUREFILLER_H
#define ECALSTRUCTUREFILLER_H

#include "FairTask.h"
#include "TString.h"
#include "TVector3.h"

class ecalInf;
class ecalStructure;
class TClonesArray;

class ecalStructureFiller : public FairTask {

public:
  /** Default constructor **/
  ecalStructureFiller();

  /** Standard constructor **/
  ecalStructureFiller(const char *name, const Int_t iVerbose=1, const char* fileGeo="ecal_FullMC.geo");

  /** Destructor **/
  virtual ~ecalStructureFiller();

  /** Initialization of the task **/  
  virtual InitStatus Init();

  ecalStructure* InitPython(TClonesArray* litePoints);

  /** Executed task **/ 
  virtual void Exec(Option_t* option,TClonesArray* litePoints);

  /** Finish task **/ 
  virtual void Finish();

  /** Set data source for hit producer.
   ** This must be called before Init()
   ** (No effect other case)! **/
  void SetUseMCPoints(Bool_t UseMCPoints);

  ecalStructure* GetStructure() const;
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
  ecalStructure* fStr;
  ecalInf* fInf;		//ECAL geometry container

  TClonesArray* fListECALpts;   // ECAL MC points
  Int_t fEvent;                 //! Internal event counter

  /** Is Init() already done? **/
  Bool_t fInited;
  /** Should we take data from MCPoints? **/
  Bool_t fUseMCPoints;

  /** Should we store information about tracks/energy depostion **/
  Bool_t fStoreTrackInfo;
  /** Geo file to use **/
  TString fFileGeo;

  ecalStructureFiller(const ecalStructureFiller&);
  ecalStructureFiller& operator=(const ecalStructureFiller&);

  ClassDef(ecalStructureFiller,1)

};

inline void ecalStructureFiller::SetUseMCPoints(Bool_t UseMCPoints)
{
	if (fInited) return;
	fUseMCPoints=UseMCPoints;
}

inline Bool_t ecalStructureFiller::GetUseMCPoints() const
{
	return fUseMCPoints;
}

inline void ecalStructureFiller::StoreTrackInformation(Bool_t storetrackinfo)
{
  if (fInited) return;
  fStoreTrackInfo=storetrackinfo;
}

inline Bool_t ecalStructureFiller::GetStoreTrackInformation() const
{
  return fStoreTrackInfo;
}

inline ecalStructure* ecalStructureFiller::GetStructure() const
{
  return fStr;
}

#endif
