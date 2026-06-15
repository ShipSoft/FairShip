#ifndef SHIPMuDIS_MUGEOPROCESSOR_H_
#define SHIPMuDIS_MUGEOPROCESSOR_H_

#include <string>
#include <map>

#include "FairLogger.h"  // for FairLogger, MESSAGE_ORIGIN
#include "TGeoManager.h"
#include "TGeoMaterial.h"
#include "TGeoNode.h"
#include "TGeoShape.h"
#include "TGeoVolume.h"
#include "TMath.h"
#include "TVector3.h"

#include "MuDISDefs.h"

class MuGeoProcessor {
 public:
  /** default constructor **/
  MuGeoProcessor();
  
  /** destructor **/
  ~MuGeoProcessor();

  void initialise(MuonBranches& aEvt);
  TVector3 GetVertex(const TVector3 & r1, const TVector3 & p1,
		     const TVector3 & r2, const TVector3 & p2);                                                        
  void CheckAllVolumes();  
  std::map<std::string,Path> & FillMuonPath();

 private:
  //position
  TVector3 fStartpos;
  TVector3 fUBTpos;
  TVector3 fSBTpos;
  TVector3 fSSTpos;
  //momentum direction
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
  
  std::map<std::string,Path> fPathMap;

};//class

#endif

  
