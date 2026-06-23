#include "MuonPath.h"
#include "FairLogger.h"
#include <iostream>


MuonPath::MuonPath(){
  flabel="None";
  fdensity = 0;
  fwdensity = 0;
  flength = 0;
  fzlength = 0;
}

void MuonPath::SetVertexInfo(const TVector3 & vecpos,
			     const TVector3 & vecp,
			     const double & time){
  fvtx.push_back(vecpos);
  fvtxT.push_back(time);
  fpvec.push_back(vecp);
}

double MuonPath::GetZ(const double & aZ, unsigned & idx) const{
  //@FIXME AMM- is this efficient enough?? 
  if (aZ<fendZ[0]) {
    idx=0;
    return aZ;
  }
  double prevz = fendZ[0];
  for (unsigned iz(1);iz<fendZ.size();++iz){
    double extraz = aZ-prevz;
    double stepz = fendZ[iz]-fstart[iz].Z();
    if (extraz<stepz){
      idx=iz;
      return fstart[iz].Z()+extraz;
    }
    prevz+=stepz;
  }
  //set a default but should not happen?
  return 0;
}

std::string MuonPath::GetLabel(const std::string & aVol,const std::string & aMat) const{
  //@FIXME AMM-avoid hardcoding, pass by config ?
  if (aVol.find("Magn")!=aVol.npos) return "MS";
  else if (aVol.find("Upstream")!=aVol.npos) return "UBT";
  else if (aVol.find("Decay")!=aVol.npos && aMat.find("helium")!=aMat.npos) return "HE";
  else if (aMat.find("air")!=aMat.npos) return "AIR";
  else if (aVol.find("straw")!=aVol.npos) return "SSTsens";
  else if (aVol.find("gas")!=aVol.npos && aMat.find("STT")!=aMat.npos) return "SSTsens";
  else if (aVol.find("wire")!=aVol.npos && aMat.find("tungsten")!=aMat.npos) return "SSTsens";
  else if (aVol.find("Tr1_frame")!=aVol.npos && aMat.find("steel")!=aMat.npos) return "SSTfr";
  else if ((aVol.find("Veto")!=aVol.npos || aVol.find("vLongitRib")!=aVol.npos) && aMat.find("Aluminum")!=aMat.npos) return "SBTfr";
  else if (aVol.find("LiSc")!=aVol.npos) return "SBTsens";
  else {
    LOG(debug) << aVol << " " << aMat << " assigned to REST.";  
    return "REST";
  }
}

void MuonPath::Print(){
  std::ostringstream ldebug;
  ldebug << flabel << " "
	 << " d=" << fdensity
	 << " <d>=" << fwdensity/flength << std::endl
	 << " l=" << flength
	 << " l_in_z=" << fzlength
	 << " zIn=" << fstart[0].Z()
	 << " zOut=" << fendZ[GetNSlices()-1] << std::endl;
  ldebug << "z-slices n=" << GetNSlices() << ": " << std::endl;
  for (unsigned iz(0);iz<GetNSlices();++iz){
    ldebug << fvolName[iz] << " "
	   << fmaterial[iz]
	   << " vtxz=" << fvtx[iz].Z()
	   << " slice [" << fstart[iz].Z() << "-" << fendZ[iz] << "] "
	   << std::endl;
  }
  ldebug << std::endl;
  LOG(debug) << ldebug.str();
}

bool MuonPath::Add(const MuonPath & aEle) {
  //path added should always have only one element...
  if (aEle.GetNSlices() !=1 ){
    LOG(error) << " -- incorrect number of elements in path: " << GetNSlices();
    return false;
  }
  fvolName.push_back(aEle.fvolName[0]);
  fmaterial.push_back(aEle.fmaterial[0]);
  fpvec.push_back(aEle.fpvec[0]);
  fvtx.push_back(aEle.fvtx[0]);
  fvtxT.push_back(aEle.fvtxT[0]);
  fstart.push_back(aEle.fstart[0]);
  fstartT.push_back(aEle.fstartT[0]);
  fendZ.push_back(aEle.fendZ[0]);
  flength += aEle.flength;
  fwdensity += aEle.fdensity*aEle.flength;
  fzlength += aEle.fendZ[0]-aEle.fstart[0].Z();
  return true;
}
