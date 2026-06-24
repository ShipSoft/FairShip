#ifndef SHIPMuDIS_MuonPath_H_
#define SHIPMuDIS_MuonPath_H_

#include <string>

#include "TVector3.h"

/*
This class allows to consider a track with changes in directions between the
different points of measurements (start, veto detectors, SST, etc...).

A MuonPath can be made of several slices. For each slice, there is a start and
an end position.

When getting a random z position along the path, the extrapolation is made
linearly using a vertex position which corresponds to the relevant point of
measurement along the trajectory.
*/

const Double_t c_light = 29.9792458;             // speed of light in cm/ns
const Double_t muon_mass = 0.10565999895334244;  // muon mass in GeV

class MuonPath {
 public:
  MuonPath();
  ~MuonPath() {};

  inline void AddVolume(const std::string& aVol, const std::string& aMat,
                        const double& aD) {
    flabel = GetLabel(aVol, aMat);
    fvolName.push_back(aVol);
    fmaterial.push_back(aMat);
    fdensity = aD;
  };

  inline double GetMomentum(const unsigned& idx) const {
    if (idx >= GetNSlices()) return 0;
    return fpvec[idx].Mag();
  };

  inline double Getpx(const unsigned& idx) const {
    if (idx >= GetNSlices()) return 0;
    return fpvec[idx].X();
  };

  inline double Getpy(const unsigned& idx) const {
    if (idx >= GetNSlices()) return 0;
    return fpvec[idx].Y();
  };

  inline double Getpz(const unsigned& idx) const {
    if (idx >= GetNSlices()) return 0;
    return fpvec[idx].Z();
  };

  inline std::string GetLabel() const { return flabel; };

  inline void SetLabel(const std::string& aLab) { flabel = aLab; };

  inline double GetDensity() const { return fdensity; };

  inline double GetWeightedDensity() const { return fwdensity; };

  inline void SetDensity(const double& aD) { fdensity = aD; };

  inline double GetLength() const { return flength; };

  inline double GetZLength() const { return fzlength; };

  inline void SetLength(const double& aStep, const TVector3& aStart,
                        const double& aZ) {
    flength += aStep;
    fzlength += aZ;
    fstart.push_back(aStart);
    fendZ.push_back(aStart.Z() + aZ);
    fwdensity += aStep * fdensity;
    fstartT.push_back(GetTimeNs(aStart.Z(), GetNSlices() - 1));
  };

  inline const unsigned GetNSlices() const { return fvolName.size(); };

  inline double GetstartZ() const { return fstart[0].Z(); };

  inline double GetstartX(const unsigned& idx) const {
    if (idx >= GetNSlices()) return 0;
    return fstart[idx].X();
  };

  inline double GetstartY(const unsigned& idx) const {
    if (idx >= GetNSlices()) return 0;
    return fstart[idx].Y();
  };

  inline double GetstartZ(const unsigned& idx) const {
    if (idx >= GetNSlices()) return 0;
    return fstart[idx].Z();
  };

  void SetVertexInfo(const TVector3& vecpos, const TVector3& vecp,
                     const double& time);
  std::string GetLabel(const std::string& aVol, const std::string& aMat) const;
  void Print();
  double GetZ(const double& aZ, unsigned& idx) const;
  bool Add(const MuonPath& aEle);

  inline double GetX(const double& aZ, const unsigned& idx) const {
    if (idx >= GetNSlices()) return 0;
    return fvtx[idx].X() +
           (aZ - fvtx[idx].Z()) * fpvec[idx].X() / fpvec[idx].Z();
  };

  inline double GetY(const double& aZ, const unsigned& idx) const {
    if (idx >= GetNSlices()) return 0;
    return fvtx[idx].Y() +
           (aZ - fvtx[idx].Z()) * fpvec[idx].Y() / fpvec[idx].Z();
  };

  inline double GetLength(const double& aZ, const unsigned& idx) const {
    if (idx >= GetNSlices()) return 0;
    return TMath::Sqrt(TMath::Power(GetX(aZ, idx) - fvtx[idx].X(), 2) +
                       TMath::Power(GetY(aZ, idx) - fvtx[idx].Y(), 2) +
                       TMath::Power(aZ - fvtx[idx].Z(), 2));  // in cm
  };

  inline double GetTimeNs(const double& aZ, const unsigned& idx) const {
    if (idx >= GetNSlices()) return 0;
    double P = fpvec[idx].Mag();
    double v = c_light * P /
               TMath::Sqrt(TMath::Power(P, 2) + TMath::Power(muon_mass, 2));

    return fvtxT[idx] + GetLength(aZ, idx) / v;
  };

 private:
  std::string flabel;
  double fdensity;
  double fwdensity;
  double flength;
  double fzlength;

  std::vector<std::string> fvolName;
  std::vector<std::string> fmaterial;
  std::vector<TVector3> fvtx;
  std::vector<double> fvtxT;
  std::vector<TVector3> fstart;
  std::vector<double> fstartT;
  std::vector<double> fendZ;
  std::vector<TVector3> fpvec;
};

#endif
