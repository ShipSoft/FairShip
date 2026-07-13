#ifndef SHIPMuDIS_MUDEFS_H_
#define SHIPMuDIS_MUDEFS_H_

#include <string>
#include <vector>

#include "DISparticle.h"
#include "FairLogger.h"  // for FairLogger, MESSAGE_ORIGIN
#include "ShipMCTrack.h"
#include "TROOT.h"
#include "TTree.h"  // for TTree
#include "TVector3.h"
#include "UpstreamTaggerPoint.h"
#include "strawtubesPoint.h"
#include "vetoPoint.h"

struct MuonDISBranches {
  int nDISevts;                 // per input muon per volume
  double wDIS;                  // per input muon per volume
  std::vector<double> DISxsec;  // per input muon per DIS
  std::vector<bool> DIStarget;  // per input muon per DIS, p=true, n=false
  std::vector<double> DISvx;
  std::vector<double> DISvy;
  std::vector<double> DISvz;
  std::vector<double> DISvt;
  std::vector<int> nDISdau;               // per DIS event muon
  std::vector<DISparticle> DISparticles;  // all DIS events together.

  void InitTree(TTree*& t, TString label) {
    t->Branch("muon_nDISevt_" + label, &nDISevts);
    t->Branch("muon_wDIS_" + label, &wDIS);
    t->Branch("mudis_DISxsec_" + label, &DISxsec);
    t->Branch("mudis_DIStarget_" + label, &DIStarget);
    t->Branch("mudis_DISvx_" + label, &DISvx);
    t->Branch("mudis_DISvy_" + label, &DISvy);
    t->Branch("mudis_DISvz_" + label, &DISvz);
    t->Branch("mudis_DISvt_" + label, &DISvt);
    t->Branch("mudis_nDISdaughters_" + label, &nDISdau);
    t->Branch("mudis_DISproducts_" + label, &DISparticles);
  };

  void initEvent(const int& nDIS) {
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
    DISparticles.reserve(10 * nDIS);
  };
};

struct MuonBranches {
  std::vector<ShipMCTrack> mcTrks;
  std::vector<vetoPoint> sbtPt;
  std::vector<UpstreamTaggerPoint> ubtPt;
  std::vector<strawtubesPoint> sstPt;
  MuonDISBranches brMS;
  MuonDISBranches brUBT;
  MuonDISBranches brSBTsens;  // sensitive
  MuonDISBranches brSBTfr;    // frame
  MuonDISBranches brSSTsens;
  MuonDISBranches brSSTfr;
  MuonDISBranches brHE;
  MuonDISBranches brAIR;
  MuonDISBranches brREST;
  void InitTree(TTree*& t) {
    t->Branch("muon_MCTracks", &mcTrks);
    t->Branch("muon_SBTPoints", &sbtPt);
    t->Branch("muon_SSTPoints", &sstPt);
    t->Branch("muon_UBTPoints", &ubtPt);
    brMS.InitTree(t, "MS");
    brUBT.InitTree(t, "UBT");
    brSBTsens.InitTree(t, "SBTsens");
    brSBTfr.InitTree(t, "SBTfr");
    brSSTsens.InitTree(t, "SSTsens");
    brSSTfr.InitTree(t, "SSTfr");
    brHE.InitTree(t, "HE");
    brAIR.InitTree(t, "AIR");
    brREST.InitTree(t, "REST");
  };
};

struct CBMSimBranches {
  std::vector<ShipMCTrack>* MCTrack = nullptr;
  std::vector<vetoPoint>* sbtPt = nullptr;
  std::vector<UpstreamTaggerPoint>* ubtPt = nullptr;
  std::vector<strawtubesPoint>* sstPt = nullptr;

  void Setup(TTree*& t) {
    t->SetBranchAddress("MCTrack", &MCTrack);
    t->SetBranchAddress("vetoPoint", &sbtPt);
    t->SetBranchAddress("UpstreamTaggerPoint", &ubtPt);
    t->SetBranchAddress("strawtubesPoint", &sstPt);
  };
};

//For reading back the tree
struct MuonDISInBranches {
  int* nDISevts = nullptr;                 // per input muon per volume
  double* wDIS = nullptr;                  // per input muon per volume
  std::vector<double>* DISxsec = nullptr;  // per input muon per DIS
  std::vector<bool>* DIStarget = nullptr;  // per input muon per DIS, p=true, n=false
  std::vector<double>* DISvx = nullptr;
  std::vector<double>* DISvy = nullptr;
  std::vector<double>* DISvz = nullptr;
  std::vector<double>* DISvt = nullptr;
  std::vector<int>* nDISdau = nullptr;               // per DIS event muon
  std::vector<DISparticle>* DISparticles = nullptr;  // all DIS events together.

  bool SetupTree(TTree*& t, TString label) {
    bool ok = true;
    ok &= (t->SetBranchAddress("muon_nDISevt_" + label, &nDISevts) >= 0);
    ok &= (t->SetBranchAddress("muon_wDIS_" + label, &wDIS) >= 0);
    ok &= (t->SetBranchAddress("mudis_DISxsec_" + label, &DISxsec) >= 0);
    ok &= (t->SetBranchAddress("mudis_DIStarget_" + label, &DIStarget) >= 0);
    ok &= (t->SetBranchAddress("mudis_DISvx_" + label, &DISvx) >= 0);
    ok &= (t->SetBranchAddress("mudis_DISvy_" + label, &DISvy) >= 0);
    ok &= (t->SetBranchAddress("mudis_DISvz_" + label, &DISvz) >= 0);
    ok &= (t->SetBranchAddress("mudis_DISvt_" + label, &DISvt) >= 0);
    ok &= (t->SetBranchAddress("mudis_nDISdaughters_" + label, &nDISdau) >= 0);
    ok &= (t->SetBranchAddress("mudis_DISproducts_" + label, &DISparticles) >= 0);
    return ok;
  };

};

struct MuonInBranches {
  std::vector<ShipMCTrack>* mcTrks = nullptr;
  std::vector<vetoPoint>* sbtPt = nullptr;
  std::vector<UpstreamTaggerPoint>* ubtPt = nullptr;
  std::vector<strawtubesPoint>* sstPt = nullptr;
  MuonDISInBranches* brMS = nullptr;
  MuonDISInBranches* brUBT = nullptr;
  MuonDISInBranches* brSBTsens = nullptr;  // sensitive
  MuonDISInBranches* brSBTfr = nullptr;    // frame
  MuonDISInBranches* brSSTsens = nullptr;
  MuonDISInBranches* brSSTfr = nullptr;
  MuonDISInBranches* brHE = nullptr;
  MuonDISInBranches* brAIR = nullptr;
  MuonDISInBranches* brREST = nullptr;
  bool Setup(TTree*& t) {
    bool ok = true;
    ok &= (t->SetBranchAddress("muon_MCTracks", &mcTrks) >= 0);
    ok &= (t->SetBranchAddress("muon_SBTPoints", &sbtPt) >= 0);
    ok &= (t->SetBranchAddress("muon_SSTPoints", &sstPt) >= 0);
    ok &= (t->SetBranchAddress("muon_UBTPoints", &ubtPt) >= 0);
    ok &= brMS->SetupTree(t, "MS");
    ok &= brUBT->SetupTree(t, "UBT");
    ok &= brSBTsens->SetupTree(t, "SBTsens");
    ok &= brSBTfr->SetupTree(t, "SBTfr");
    ok &= brSSTsens->SetupTree(t, "SSTsens");
    ok &= brSSTfr->SetupTree(t, "SSTfr");
    ok &= brHE->SetupTree(t, "HE");
    ok &= brAIR->SetupTree(t, "AIR");
    ok &= brREST->SetupTree(t, "REST");
    return ok;
  };
};



#endif
