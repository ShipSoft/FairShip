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
  void AddVolume(const std::string& aVol, const std::string& aMat, double aD) {
    flabel = GetLabel(aVol, aMat);
    fvolName.push_back(aVol);
    fmaterial.push_back(aMat);
    fdensity = aD;
  }

  double GetMomentum(unsigned idx) const {
    if (idx >= GetNSlices()) return 0;
    return fpvec[idx].R();
  }

  double Getpx(unsigned idx) const {
    if (idx >= GetNSlices()) return 0;
    return fpvec[idx].X();
  }

  double Getpy(unsigned idx) const {
    if (idx >= GetNSlices()) return 0;
    return fpvec[idx].Y();
  }

  double Getpz(unsigned idx) const {
    if (idx >= GetNSlices()) return 0;
    return fpvec[idx].Z();
  }

  std::string GetLabel() const { return flabel; }

  void SetLabel(const std::string& aLab) { flabel = aLab; }

  double GetDensity() const { return fdensity; }

  double GetWeightedDensity() const { return fwdensity; }

  double GetWeightedDensity(double minLength) const;

  void SetDensity(double aD) { fdensity = aD; }

  double GetLength() const { return flength; }

  double GetZLength() const { return fzlength; }

  void SetLength(double aStep, const ROOT::Math::XYZPoint& aStart, double aZ) {
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
  }

  unsigned GetNSlices() const {
    return static_cast<unsigned>(
        std::min({fvolName.size(), fmaterial.size(), fpvec.size(), fvtx.size(),
                  fvtxT.size(), fstart.size(), fstartT.size(), fendZ.size()}));
  }

  double GetstartZ() const { return fstart.empty() ? 0. : fstart.front().Z(); }

  double GetstartX(unsigned idx) const {
    if (idx >= GetNSlices()) return 0;
    return fstart[idx].X();
  }

  double GetstartY(unsigned idx) const {
    if (idx >= GetNSlices()) return 0;
    return fstart[idx].Y();
  }

  double GetstartZ(unsigned idx) const {
    if (idx >= GetNSlices()) return 0;
    return fstart[idx].Z();
  }

  double GetEndZ(unsigned idx) const {
    if (idx >= GetNSlices()) return 0;
    return fendZ[idx];
  }

  double GetSliceLength(unsigned idx) const {
    if (idx >= GetNSlices()) return 0;
    return fendLength[idx] - (idx == 0 ? 0. : fendLength[idx - 1]);
  }

  void SetVertexInfo(const ROOT::Math::XYZPoint& vecpos,
                     const ROOT::Math::XYZVector& vecp, double time);
  std::string GetLabel(const std::string& aVol, const std::string& aMat) const;
  void Print();
  double GetZ(double aZ, unsigned& idx) const;
  double GetZAtLength(double length, unsigned& idx) const;
  double GetLengthAtZ(double aZ) const;
  bool Add(const MuonPath& aEle);

  double GetX(double aZ, unsigned idx) const {
    if (idx >= GetNSlices() || fpvec[idx].Z() == 0) return 0;
    return fvtx[idx].X() +
           (aZ - fvtx[idx].Z()) * fpvec[idx].X() / fpvec[idx].Z();
  }

  double GetY(double aZ, unsigned idx) const {
    if (idx >= GetNSlices() || fpvec[idx].Z() == 0) return 0;
    return fvtx[idx].Y() +
           (aZ - fvtx[idx].Z()) * fpvec[idx].Y() / fpvec[idx].Z();
  }

  double GetLength(double aZ, unsigned idx) const {
    if (idx >= GetNSlices()) return 0;
    return (ROOT::Math::XYZPoint(GetX(aZ, idx), GetY(aZ, idx), aZ) - fvtx[idx])
        .R();  // in cm
  }

  double GetTimeNs(double aZ, unsigned idx) const {
    if (idx >= GetNSlices() || fpvec[idx].Z() == 0.) return 0;
    double P = fpvec[idx].R();
    if (P == 0.) return 0;
    double v = c_light * P / std::hypot(P, muon_mass);
    if (v == 0.) return 0;
    // A slice may precede its reference measurement in z.
    return fvtxT[idx] + (aZ - fvtx[idx].Z()) * P / fpvec[idx].Z() / v;
  }

 private:
  std::string flabel = "None";
  double fdensity = 0.;
  double fwdensity = 0.;
  double flength = 0.;
  double fzlength = 0.;

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
