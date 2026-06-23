#ifndef SHIPMuDIS_MUDEFS_H_
#define SHIPMuDIS_MUDEFS_H_

#include <string>
#include <vector>

#include "FairLogger.h"  // for FairLogger, MESSAGE_ORIGIN
#include "TROOT.h"
#include "TTree.h"  // for TTree
#include "TVector3.h"

#include "ShipMCTrack.h"
#include "vetoPoint.h"
#include "UpstreamTaggerPoint.h"
#include "strawtubesPoint.h"
#include "DISparticle.h"

struct MuonDISBranches {
  int nDISevts;//per input muon per volume
  double wDIS;//per input muon per volume
  std::vector<double> DISxsec;//per input muon per DIS
  std::vector<bool> DIStarget;//per input muon per DIS, p=true, n=false
  std::vector<double> DISvx;
  std::vector<double> DISvy;
  std::vector<double> DISvz;
  std::vector<double> DISvt;
  std::vector<int> nDISdau;//per DIS event muon
  std::vector<DISparticle> DISparticles;//all DIS events together.

  void InitTree(TTree* & t, TString label){
    t->Branch("muon_nDISevt_"+label, &nDISevts);
    t->Branch("muon_wDIS_"+label, &wDIS);
    t->Branch("mudis_DISxsec_"+label, &DISxsec);
    t->Branch("mudis_DIStarget_"+label, &DIStarget);
    t->Branch("mudis_DISvx_"+label, &DISvx);
    t->Branch("mudis_DISvy_"+label, &DISvy);
    t->Branch("mudis_DISvz_"+label, &DISvz);
    t->Branch("mudis_DISvt_"+label, &DISvt);
    t->Branch("mudis_nDISdaughters_"+label, &nDISdau);
    t->Branch("mudis_DISproducts_"+label, &DISparticles);
  };

  void initEvent(const int & nDIS){
    nDISevts = 0;
    wDIS = 1;
    DISxsec.clear();
    DISxsec.reserve(nDIS);
    DIStarget.clear();
    DIStarget.reserve(nDIS);
    DISvx.clear();
    DISvx.reserve(nDIS);
    DISvy.clear();
    DISvy.reserve(nDIS);
    DISvz.clear();
    DISvz.reserve(nDIS);
    DISvt.clear();
    DISvt.reserve(nDIS);
    nDISdau.clear();
    nDISdau.reserve(nDIS);
    DISparticles.clear();
    DISparticles.reserve(10*nDIS);

  };
  
};


struct MuonBranches {
  std::vector<ShipMCTrack> mcTrks;
  std::vector<vetoPoint> sbtPt;
  std::vector<UpstreamTaggerPoint> ubtPt;
  std::vector<strawtubesPoint> sstPt;
  MuonDISBranches brMS;
  MuonDISBranches brUBT;
  MuonDISBranches brSBTsens;//sensitive
  MuonDISBranches brSBTfr;//frame
  MuonDISBranches brSSTsens;
  MuonDISBranches brSSTfr;
  MuonDISBranches brHE;
  MuonDISBranches brAIR;
  MuonDISBranches brREST;
  void InitTree(TTree* & t){
    t->Branch("muon_MCTracks", &mcTrks);
    t->Branch("muon_SBTPoints", &sbtPt);
    t->Branch("muon_SSTPoints", &sstPt);
    t->Branch("muon_UBTPoints", &ubtPt);
    brMS.InitTree(t,"MS");
    brUBT.InitTree(t,"UBT");
    brSBTsens.InitTree(t,"SBTsens");
    brSBTfr.InitTree(t,"SBTfr");
    brSSTsens.InitTree(t,"SSTsens");
    brSSTfr.InitTree(t,"SSTfr");
    brHE.InitTree(t,"HE");
    brAIR.InitTree(t,"AIR");
    brREST.InitTree(t,"REST");
  };
};



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
  };
};


#endif
