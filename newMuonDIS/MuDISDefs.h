#ifndef SHIPMuDIS_MUDEFS_H_
#define SHIPMuDIS_MUDEFS_H_

#include <string>
#include <vector>
#include <sstream>
#include <iostream>

#include "DISparticle.h"
#include "FairLogger.h"  // for FairLogger, MESSAGE_ORIGIN
#include "ShipMCTrack.h"
#include "TROOT.h"
#include "TTree.h"  // for TTree
#include "TChain.h"  // for TTree
#include "TVector3.h"
#include "UpstreamTaggerPoint.h"
#include "strawtubesPoint.h"
#include "vetoPoint.h"

namespace ShipMuDIS {
  static const unsigned nMats = 9;
  
  enum MatType {
    MS = 0,
    UBT = 1,
    SBTsens = 2,
    SBTfr = 3,
    SSTsens = 4,
    SSTfr = 5,
    HE = 6,
    AIR = 7,
    REST = 8
  };
  
  static TString MatTypeStr[nMats] = {
    "MS","UBT",
    "SBTsens","SBTfr",
    "SSTsens","SSTfr",
    "HE",//"HEfr",
    "AIR","REST"
  };
  
  
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
    
    void InitTree(TTree*& aT, TString & aLabel) {
      aT->Branch("muon_nDISevt_" + aLabel, &nDISevts);
      aT->Branch("muon_wDIS_" + aLabel, &wDIS);
      aT->Branch("mudis_DISxsec_" + aLabel, &DISxsec);
      aT->Branch("mudis_DIStarget_" + aLabel, &DIStarget);
      aT->Branch("mudis_DISvx_" + aLabel, &DISvx);
      aT->Branch("mudis_DISvy_" + aLabel, &DISvy);
      aT->Branch("mudis_DISvz_" + aLabel, &DISvz);
      aT->Branch("mudis_DISvt_" + aLabel, &DISvt);
      aT->Branch("mudis_nDISdaughters_" + aLabel, &nDISdau);
      aT->Branch("mudis_DISproducts_" + aLabel, &DISparticles);
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
    MuonDISBranches br[nMats];
    void InitTree(TTree*& aT) {
      aT->Branch("muon_MCTracks", &mcTrks);
      aT->Branch("muon_SBTPoints", &sbtPt);
      aT->Branch("muon_SSTPoints", &sstPt);
      aT->Branch("muon_UBTPoints", &ubtPt);
      for (unsigned i(0);i<nMats;++i){
	br[i].InitTree(aT, MatTypeStr[i]);
      }
    };
    void initEvent(const int& nMax = 100) {
      mcTrks.clear();
      mcTrks.reserve(nMax);
      sbtPt.clear();
      sbtPt.reserve(nMax);
      ubtPt.clear();
      ubtPt.reserve(nMax);
      sstPt.clear();
      sstPt.reserve(nMax);
    };
  };
  
  struct CBMSimBranches {
    std::vector<ShipMCTrack>* MCTrack = nullptr;
    std::vector<vetoPoint>* sbtPt = nullptr;
    std::vector<UpstreamTaggerPoint>* ubtPt = nullptr;
    std::vector<strawtubesPoint>* sstPt = nullptr;
    
    bool Setup(TChain* aT) {
      bool ok = true;
      ok &= (aT->SetBranchAddress("MCTrack", &MCTrack) >= 0);
      ok &= (aT->SetBranchAddress("vetoPoint", &sbtPt) >= 0);
      ok &= (aT->SetBranchAddress("UpstreamTaggerPoint", &ubtPt) >= 0);
      ok &= (aT->SetBranchAddress("strawtubesPoint", &sstPt) >= 0);
      return ok;
    };
  };
  
  //For reading back the DIS tree
  struct MuonDISInBranches {
    int nDISevts = 0;                 // per input muon per volume
    double wDIS = 1;                  // per input muon per volume
    std::vector<double>* DISxsec = nullptr;  // per input muon per DIS
    std::vector<bool>* DIStarget = nullptr;  // per input muon per DIS, p=true, n=false
    std::vector<double>* DISvx = nullptr;
    std::vector<double>* DISvy = nullptr;
    std::vector<double>* DISvz = nullptr;
    std::vector<double>* DISvt = nullptr;
    std::vector<int>* nDISdau = nullptr;               // per DIS event muon
    std::vector<DISparticle>* DISparticles = nullptr;  // all DIS events together.
    
    bool SetupTree(TTree* aT, TString aLabel) {
      bool ok = true;
      ok &= (aT->SetBranchAddress("muon_nDISevt_" + aLabel, &nDISevts) >= 0);
      ok &= (aT->SetBranchAddress("muon_wDIS_" + aLabel, &wDIS) >= 0);
      ok &= (aT->SetBranchAddress("mudis_DISxsec_" + aLabel, &DISxsec) >= 0);
      ok &= (aT->SetBranchAddress("mudis_DIStarget_" + aLabel, &DIStarget) >= 0);
      ok &= (aT->SetBranchAddress("mudis_DISvx_" + aLabel, &DISvx) >= 0);
      ok &= (aT->SetBranchAddress("mudis_DISvy_" + aLabel, &DISvy) >= 0);
      ok &= (aT->SetBranchAddress("mudis_DISvz_" + aLabel, &DISvz) >= 0);
      ok &= (aT->SetBranchAddress("mudis_DISvt_" + aLabel, &DISvt) >= 0);
      ok &= (aT->SetBranchAddress("mudis_nDISdaughters_" + aLabel, &nDISdau) >= 0);
      ok &= (aT->SetBranchAddress("mudis_DISproducts_" + aLabel, &DISparticles) >= 0);
      return ok;
    };

    template<class T>
    std::string Print(const std::vector<T>& aVec, const TString & aName){
      std::ostringstream lOut;
      lOut << " - " << aName << " size " << aVec.size() << " pointer " << &aVec << ": ";
      for (const auto& value : aVec) {
	lOut << value << " ";
      }
      lOut << std::endl;
      return lOut.str();
    };    

    std::ostringstream Print(const unsigned & aEvt, const TString & aLabel){
      std::ostringstream lOut;
      lOut << "------------ print evt " << aEvt << " branch " << aLabel << " -------------" << std::endl
	   << " - nDISevts = " << nDISevts  << std::endl
	   << " - wDIS = " << wDIS  << std::endl;
      lOut << Print(*DISxsec,"DISxsec");
      lOut << Print(*DIStarget,"DIStarget");
      lOut << Print(*DISvx,"DISvx");
      lOut << Print(*DISvy,"DISvy");
      lOut << Print(*DISvz,"DISvz");
      lOut << Print(*DISvt,"DISvt");
      lOut << Print(*nDISdau,"nDISdau");
      lOut << DISparticles << " " << Print(*DISparticles,"DISparticles");

      return lOut;
    };

    
  };
  
  
  struct MuonInBranches {
    std::vector<ShipMCTrack>* mcTrks = nullptr;
    std::vector<vetoPoint>* sbtPt = nullptr;
    std::vector<UpstreamTaggerPoint>* ubtPt = nullptr;
    std::vector<strawtubesPoint>* sstPt = nullptr;
    MuonDISInBranches br[nMats];

    bool Setup(TTree* aT) {
      bool ok = true;
      ok &= (aT->SetBranchAddress("muon_MCTracks", &mcTrks) >= 0);
      ok &= (aT->SetBranchAddress("muon_SBTPoints", &sbtPt) >= 0);
      ok &= (aT->SetBranchAddress("muon_SSTPoints", &sstPt) >= 0);
      ok &= (aT->SetBranchAddress("muon_UBTPoints", &ubtPt) >= 0);
      for (unsigned i(0);i<nMats;++i){
	ok &= br[i].SetupTree(aT, MatTypeStr[i]);
      }
      return ok;
    };
  };

}


#endif
