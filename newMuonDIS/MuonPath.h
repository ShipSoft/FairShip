// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#ifndef NEWMUONDIS_MUONPATH_H_
#define NEWMUONDIS_MUONPATH_H_

#include <algorithm>
#include <cmath>
#include <string>
#include <vector>

#include "Math/Point3D.h"
#include "Math/Vector3D.h"

/*
This class allows to consider a track with changes in directions between the
different points of measurements (start, veto detectors, SST, etc...).

A MuonPath can be made of several slices. For each slice, there is a start and
an end position.

When getting a random z position along the path, the extrapolation is made
linearly using a vertex position which corresponds to the relevant point of
measurement along the trajectory.
*/

constexpr double c_light = 29.9792458;             // speed of light in cm/ns
constexpr double muon_mass = 0.10565999895334244;  // muon mass in GeV

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
    return fpvec[idx].R();
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

  double GetWeightedDensity(double minLength) const;

  inline void SetDensity(const double& aD) { fdensity = aD; };

  inline double GetLength() const { return flength; };

  inline double GetZLength() const { return fzlength; };

  inline void SetLength(const double& aStep, const ROOT::Math::XYZPoint& aStart,
                        const double& aZ) {
    flength += aStep;
    fendLength.push_back(flength);
    fzlength += aZ;
    fstart.push_back(aStart);
    fendZ.push_back(aStart.Z() + aZ);
    fwdensity += aStep * fdensity;
    fsliceDensity.push_back(fdensity);
    const unsigned idx = static_cast<unsigned>(fstart.size() - 1);
    fstartT.push_back(0.);
    fstartT.back() = GetTimeNs(aStart.Z(), idx);
  };

  inline unsigned GetNSlices() const {
    return static_cast<unsigned>(
        std::min({fvolName.size(), fmaterial.size(), fpvec.size(), fvtx.size(),
                  fvtxT.size(), fstart.size(), fstartT.size(), fendZ.size()}));
  };

  inline double GetstartZ() const {
    return fstart.empty() ? 0. : fstart.front().Z();
  };

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

  inline double GetEndZ(const unsigned& idx) const {
    if (idx >= GetNSlices()) return 0;
    return fendZ[idx];
  };

  inline double GetSliceLength(const unsigned& idx) const {
    if (idx >= GetNSlices()) return 0;
    return fendLength[idx] - (idx == 0 ? 0. : fendLength[idx - 1]);
  };

  void SetVertexInfo(const ROOT::Math::XYZPoint& vecpos,
                     const ROOT::Math::XYZVector& vecp, const double& time);
  std::string GetLabel(const std::string& aVol, const std::string& aMat) const;
  void Print();
  double GetZ(const double& aZ, unsigned& idx) const;
  double GetZAtLength(double length, unsigned& idx) const;
  double GetLengthAtZ(const double& aZ) const;
  bool Add(const MuonPath& aEle);

  inline double GetX(const double& aZ, const unsigned& idx) const {
    if (idx >= GetNSlices() || fpvec[idx].Z() == 0) return 0;
    return fvtx[idx].X() +
           (aZ - fvtx[idx].Z()) * fpvec[idx].X() / fpvec[idx].Z();
  };

  inline double GetY(const double& aZ, const unsigned& idx) const {
    if (idx >= GetNSlices() || fpvec[idx].Z() == 0) return 0;
    return fvtx[idx].Y() +
           (aZ - fvtx[idx].Z()) * fpvec[idx].Y() / fpvec[idx].Z();
  };

  inline double GetLength(const double& aZ, const unsigned& idx) const {
    if (idx >= GetNSlices()) return 0;
    return (ROOT::Math::XYZPoint(GetX(aZ, idx), GetY(aZ, idx), aZ) - fvtx[idx])
        .R();  // in cm
  };

  inline double GetTimeNs(const double& aZ, const unsigned& idx) const {
    if (idx >= GetNSlices() || fpvec[idx].Z() == 0.) return 0;
    double P = fpvec[idx].R();
    if (P == 0.) return 0;
    double v = c_light * P / std::hypot(P, muon_mass);
    if (v == 0.) return 0;
    // A slice may precede its reference measurement in z.
    return fvtxT[idx] + (aZ - fvtx[idx].Z()) * P / fpvec[idx].Z() / v;
  };

 private:
  std::string flabel;
  double fdensity;
  double fwdensity;
  double flength;
  double fzlength;

  std::vector<std::string> fvolName;
  std::vector<std::string> fmaterial;
  std::vector<ROOT::Math::XYZPoint> fvtx;
  std::vector<double> fvtxT;
  std::vector<ROOT::Math::XYZPoint> fstart;
  std::vector<double> fstartT;
  std::vector<double> fendZ;
  std::vector<double> fsliceDensity;
  std::vector<double>
      fendLength;  // cumulative segment lengths, excluding jumps
  std::vector<ROOT::Math::XYZVector> fpvec;
};

#endif  // NEWMUONDIS_MUONPATH_H_
