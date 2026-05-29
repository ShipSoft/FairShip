#ifndef SHIPMuDIS_MUDISPROCESSOR_H_
#define SHIPMuDIS_MUDISPROCESSOR_H_

#include "FairLogger.h"  // for FairLogger, MESSAGE_ORIGIN
#include "TClonesArray.h"
#include "TF1.h"  // for TF1
#include "TROOT.h"
#include "TTree.h"  // for TTree
#include "TVector3.h"

#include "TPythia6.h"
#include "TPythia6Calls.h"
#include "TDatabasePDG.h"
#include "vector"

#include "ShipMCTrack.h"
#include "vetoPoint.h"
#include "UpstreamTaggerPoint.h"
#include "strawtubesPoint.h"
#include "DISparticle.h"

struct CBMSimBranches {
  std::vector<ShipMCTrack>* MCTrack = nullptr;
  std::vector<vetoPoint>* sbtPt = nullptr;
  std::vector<UpstreamTaggerPoint>* ubtPt = nullptr;
  std::vector<strawtubesPoint>* sstPt = nullptr;
  
  void Setup(TTree* & t) {
    t->SetBranchAddress("MCTrack", &MCTrack);
    t->SetBranchAddress("vetoPoint", &sbtPt);
    t->SetBranchAddress("UpstreamTaggerPoint", &ubtPt);
    t->SetBranchAddress("strawtubesPoint", &sstPt);
  }
};


struct MuonDISBranches {
  std::vector<ShipMCTrack> mcTrks;
  std::vector<vetoPoint> sbtPt;
  std::vector<UpstreamTaggerPoint> ubtPt;
  std::vector<strawtubesPoint> sstPt;
  int nDISevts;//per input muon
  std::vector<double> DISxsec;//per input muon per DIS
  std::vector<bool> DIStarget;//per input muon per DIS, p=true, n=false
  std::vector<int> nDISdau;//per DIS event muon
  std::vector<DISparticle> DISparticles;//all DIS events together.

  void InitTree(TTree* & t){
    t->Branch("muon_MCTracks", &mcTrks);
    t->Branch("muon_SBTPoints", &sbtPt);
    t->Branch("muon_SSTPoints", &sstPt);
    t->Branch("muon_UBTPoints", &ubtPt);
    t->Branch("muon_nDISevt", &nDISevts);
    t->Branch("mudis_DISxsec", &DISxsec);
    t->Branch("mudis_DIStarget", &DIStarget);
    t->Branch("mudis_nDISdaughters", &nDISdau);
    t->Branch("mudis_DISproducts", &DISparticles);
  }
};

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

  void ProcessMuons();
  
 private:
  TTree* ftree;
  CBMSimBranches finEv;

  TTree* fouttree;
  MuonDISBranches foutEv;

  FairLogger* fLogger;        //!   don't make it persistent, magic ROOT command
  int fnEvts;

  TPythia6* fPythia;
  TDatabasePDG* fPDG;
  
  int fnDIS;
  int fP6seed;
  
  //void FillMuonTracks(int muon_id);
  //void FillVetoPoints(int muon_id);
  //void FillUBTPoints(int muon_id);
  //void FillSSTPoints(int muon_id);
  
};

#endif
