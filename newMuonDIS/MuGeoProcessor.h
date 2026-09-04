#ifndef SHIPMuDIS_MUGEOPROCESSOR_H_
#define SHIPMuDIS_MUGEOPROCESSOR_H_

#include <map>
#include <set>
#include <string>

#include "FairLogger.h"  // for FairLogger, MESSAGE_ORIGIN
#include "MuDISDefs.h"
#include "MuonPath.h"
#include "TGeoManager.h"
#include "TGeoMaterial.h"
#include "TGeoNode.h"
#include "TGeoShape.h"
#include "TGeoVolume.h"
#include "TMath.h"
#include "TVector3.h"

class MuGeoProcessor {
 public:
  /** default constructor **/
  MuGeoProcessor();

  /** destructor **/
  ~MuGeoProcessor();

  void initialise(ShipMuDIS::MuonBranches& aEvt);

  inline void SetZmax(const double& zmax) {
    LOG(info) << " Maximum z position for MuonPath building: " << zmax
              << " cm.";
    fZmax = zmax;
  };
  inline void SetZmin(const double& zmin) {
    LOG(info) << " Minimum z position for MuonPath building: " << zmin
              << " cm.";
    fZmin = zmin;
  };

  inline double FindZmax(const std::string& aLabel) {
    auto it = fZmaxMap.find(aLabel);
    if (it != fZmaxMap.end())
      return it->second;
    else {
      LOG(error) << " * MuGeoProcessor::FindZmax() Volume label " << aLabel
                 << " not found, using default Zmax: " << fZmax << "."
                 << std::endl;
      return fZmax;
    }
  };

  TVector3 GetVertex(const TVector3& r1, const TVector3& p1, const TVector3& r2,
                     const TVector3& p2);
  void CheckAllVolumes();
  void FillZmaxVolumes();
  std::map<std::string, MuonPath>& FillMuonPath();
  void PrintVolumes();

 private:
  double fZmax;
  double fZmin;
  // position
  TVector3 fStartpos;
  TVector3 fUBTpos;
  TVector3 fSBTpos;
  TVector3 fSSTpos;
  // momentum direction
  TVector3 fStartp;
  TVector3 fUBTp;
  TVector3 fSBTp;
  TVector3 fSSTp;

  TVector3 fVtx12;
  TVector3 fVtx13;
  TVector3 fVtx14;
  TVector3 fVtx23;
  TVector3 fVtx24;
  TVector3 fVtx34;

  double fStartT;
  double fUBTT;
  double fSBTT;
  double fSSTT;

  bool fhasUBThit;
  bool fhasSBThit;
  bool fhasSSThit;

  std::map<std::string, MuonPath> fPathMap;
  std::map<std::string, std::set<std::string>> fVolMap;
  std::map<std::string, double> fZmaxMap;

};  // class

#endif
