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

const Double_t c_light = 29.9792458;             // speed of light in cm/ns
const Double_t muon_mass = 0.10565999895334244;  // muon mass in GeV

struct Path {
  std::string volName;
  std::string label;
  std::string material;
  double density;
  double P;
  double startX;
  double startY;
  double startZ;
  double startT;
  double endZ;
  double px;
  double py;
  double pz;
  double tx;
  double ty;
  double length;
  double v;
  std::vector<std::pair<double,double>> addZ;

  void SetStartInfo(const TVector3 & vecpos, const TVector3 vecp, const double & time){
    startX = vecpos.X();
    startY = vecpos.Y();
    startT = time;
    P = vecp.Mag();
    px = vecp.X();
    py = vecp.Y();
    pz = vecp.Z();
  }
  
  void init(){
    label = GetLabel(volName,material);
    tx = px/pz;
    ty = py/pz;
    length = GetLength(endZ);
    v = c_light * P /
      TMath::Sqrt(TMath::Power(P, 2) + TMath::Power(muon_mass, 2));
  }

  std::string GetLabel(const std::string & aVol,const std::string & aMat){
    if (aVol.find("Magn")!=aVol.npos) return "MS";
    else if (aVol.find("Upstream")!=aVol.npos) return "UBT";
    else if (aVol.find("Decay")!=aVol.npos && aMat.find("helium")!=aMat.npos) return "He";
    else if (aMat.find("air")!=aMat.npos) return "Air";
    else if (aVol.find("straw")!=aVol.npos) return "SST";
    else if (aVol.find("gas")!=aVol.npos && aMat.find("STT")!=aMat.npos) return "SST";
    else return "REST";

    //else if (aVol.find("")!=aVol.npos && aMat.find("")!=aMat.npos) return "";
    //else if (aVol.find("")!=aVol.npos) return "";
  }
  
  double GetX(const double & aZ) const{
    return startX + (aZ-startZ)*tx;
  }
  double GetY(const double & aZ) const{
    return startY + (aZ-startZ)*ty;
  }
  double GetLength(const double & aZ) const{
    return TMath::Sqrt(TMath::Power(GetX(aZ) - startX, 2) +
		       TMath::Power(GetY(aZ) - startY, 2) +
		       TMath::Power(aZ - startZ, 2));  // in cm
  }
  double GetTimeNs(const double & aZ) const{
    return startT + GetLength(aZ)/v;
  }

  void Print(){
    LOG(info) << label << " "
	      << volName << " "
	      << material
	      << " d=" << density << std::endl
	      << " p=" << P
	      << " l=" << length
	      << " zIn=" << startZ
	      << " zOut=" << endZ;
  }

  void Add(const Path & aEle) {
    addZ.push_back(std::pair<double,double>(aEle.startZ,aEle.endZ));
    length += aEle.length;
  }
  
};



struct MuonDISBranches {
  int nDISevts;//per input muon
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
  MuonDISBranches brSBT;
  MuonDISBranches brSST;
  MuonDISBranches brREST;
  void InitTree(TTree* & t){
    t->Branch("muon_MCTracks", &mcTrks);
    t->Branch("muon_SBTPoints", &sbtPt);
    t->Branch("muon_SSTPoints", &sstPt);
    t->Branch("muon_UBTPoints", &ubtPt);
    brMS.InitTree(t,"MS");
    brUBT.InitTree(t,"UBT");
    brSBT.InitTree(t,"SBT");
    brSST.InitTree(t,"SST");
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
