#ifndef SHIPMuDIS_MUDISPROCESSOR_H_
#define SHIPMuDIS_MUDISPROCESSOR_H_

#include "FairLogger.h"  // for FairLogger, MESSAGE_ORIGIN
#include "TROOT.h"
#include "TTree.h"  // for TTree
#include "TVector3.h"

#include "TPythia6.h"
#include "TPythia6Calls.h"
#include "TDatabasePDG.h"
#include "vector"

#include "MuGeoProcessor.h"
#include "MuDISDefs.h"

class MuDISProcessor {
 public:
  /** default constructor **/
  MuDISProcessor();
  
  /** destructor **/
  ~MuDISProcessor(){};

  void init(const int & aEvts, const int & aDIS, const int & aSeed);
  void initPythia6();
  
  void rotate(const TVector3 & pvec,
	      const double & theta,
	      const double & phi,
	      TVector3 & newp);

  void process_file(const std::string& input,
		    const std::string& output);
  void initEvent();
  void fillMCTracks(const Int_t aIdx);
  void fillSBTHits(const Int_t aIdx);
  void fillUBTHits(const Int_t aIdx);
  void fillSSTHits(const Int_t aIdx);

  void generateDISevents(const std::string & tType,
			 const std::string & aLabel,
			 const Path & aPath,
			 MuonDISBranches & aDISBr);
  
  void ProcessMuons();

  
 private:
  TTree* ftree;
  CBMSimBranches finEv;

  TTree* fouttree;
  MuonBranches foutEv;

  FairLogger* fLogger;        //!   don't make it persistent, magic ROOT command
  int fnEvts;

  TPythia6* fPythia;
  TDatabasePDG* fPDG;
  
  int fnDIS;
  int fP6seed;

  MuGeoProcessor fGeoProcessor;

  //void FillMuonTracks(int muon_id);
  //void FillVetoPoints(int muon_id);
  //void FillUBTPoints(int muon_id);
  //void FillSSTPoints(int muon_id);
  
};

#endif
