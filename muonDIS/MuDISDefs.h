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
  double wdensity;
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
  double zlength;
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
    zlength = endZ-startZ;
    length = GetLength(endZ);
    wdensity = density*length;
    v = c_light * P /
      TMath::Sqrt(TMath::Power(P, 2) + TMath::Power(muon_mass, 2));
  }

  std::string GetLabel(const std::string & aVol,const std::string & aMat){
    //@FIXME AMM-avoid hardcoding, pass by config ?
    if (aVol.find("Magn")!=aVol.npos) return "MS";
    else if (aVol.find("Upstream")!=aVol.npos) return "UBT";
    else if (aVol.find("Decay")!=aVol.npos && aMat.find("helium")!=aMat.npos) return "HE";
    else if (aMat.find("air")!=aMat.npos) return "AIR";
    else if (aVol.find("straw")!=aVol.npos) return "SST";
    else if (aVol.find("gas")!=aVol.npos && aMat.find("STT")!=aMat.npos) return "SST";
    else {
      LOG(debug) << aVol << " " << aMat << " assigned to REST.";  
      return "REST";
    }
    //else if (aVol.find("")!=aVol.npos && aMat.find("")!=aMat.npos) return "";
    //else if (aVol.find("")!=aVol.npos) return "";
  }
  
  double GetX(const double & aZ) const{
    return startX + (aZ-startZ)*tx;
  }
  
  double GetY(const double & aZ) const{
    return startY + (aZ-startZ)*ty;
  }
  
  double GetZ(const double & aZ) const{
    //@FIXME AMM- is this efficient enough?? 
    if (aZ<endZ) return aZ;
    double prevz = endZ;
    for (unsigned iz(0);iz<addZ.size();++iz){
      double extraz = aZ-prevz;
      double stepz= addZ[iz].second-addZ[iz].first;
      if (extraz<stepz) return addZ[iz].first+extraz;
      prevz+=stepz;
    }
    //set a default but should not happen?
    return endZ;
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
    LOG(debug) << label << " "
	       << volName << " "
	       << material
	       << " d=" << density
	       << " <d>=" << wdensity/length << std::endl
	       << " p=" << P
	       << " l=" << length
	       << " l_in_z=" << zlength
	       << " zIn=" << startZ
	       << " zOut=" << endZ;
  }

  void Add(const Path & aEle) {
    addZ.push_back(std::pair<double,double>(aEle.startZ,aEle.endZ));
    length += aEle.length;
    wdensity += aEle.density*aEle.length;
    zlength += aEle.endZ-aEle.startZ;
  }

  
};



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
  MuonDISBranches brSBT;
  MuonDISBranches brSST;
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
    brSBT.InitTree(t,"SBT");
    brSST.InitTree(t,"SST");
    brSST.InitTree(t,"HE");
    brSST.InitTree(t,"AIR");
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
