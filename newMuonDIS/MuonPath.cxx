// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#include "MuonPath.h"

#include <iostream>
#include <sstream>

#include "FairLogger.h"

MuonPath::MuonPath() {
  flabel = "None";
  fdensity = 0;
  fwdensity = 0;
  flength = 0;
  fzlength = 0;
}

void MuonPath::SetVertexInfo(const ROOT::Math::XYZPoint& vecpos,
                             const ROOT::Math::XYZVector& vecp,
                             const double& time) {
  fvtx.push_back(vecpos);
  fvtxT.push_back(time);
  fpvec.push_back(vecp);
}

// Integrate density only over the sampled tail of the cumulative path.
double MuonPath::GetWeightedDensity(double minLength) const {
  minLength = std::clamp(minLength, 0., flength);
  double weightedDensity = 0.;
  double previous = 0.;
  for (unsigned i = 0; i < fendLength.size(); ++i) {
    const double length =
        std::max(0., fendLength[i] - std::max(previous, minLength));
    weightedDensity += length * fsliceDensity[i];
    previous = fendLength[i];
  }
  return weightedDensity;
}

double MuonPath::GetZAtLength(double length, unsigned& idx) const {
  idx = 0;
  if (fendLength.empty()) return 0.;
  length = std::clamp(length, 0., flength);
  const auto end =
      std::upper_bound(fendLength.begin(), fendLength.end(), length);
  idx = end == fendLength.end() ? fendLength.size() - 1
                                : end - fendLength.begin();
  const double previous = idx == 0 ? 0. : fendLength[idx - 1];
  const double step = fendLength[idx] - previous;
  return step > 0. ? fstart[idx].Z() + (length - previous) / step *
                                           (fendZ[idx] - fstart[idx].Z())
                   : fstart[idx].Z();
}

// Convert the existing compact z coordinate (gaps removed) into path length.
double MuonPath::GetLengthAtZ(const double& aZ) const {
  if (fendLength.empty()) return 0.;
  unsigned idx = 0;
  const double z = GetZ(aZ, idx);
  const double previous = idx == 0 ? 0. : fendLength[idx - 1];
  const double dz = fendZ[idx] - fstart[idx].Z();
  return previous + (dz > 0. ? std::clamp((z - fstart[idx].Z()) / dz, 0., 1.) *
                                   (fendLength[idx] - previous)
                             : 0.);
}

double MuonPath::GetZ(const double& aZ, unsigned& idx) const {
  //@FIXME AMM- is this efficient enough??
  const unsigned nSlices = GetNSlices();
  if (nSlices == 0) {
    idx = 0;
    return aZ;
  }

  if (aZ < fendZ[0]) {
    idx = 0;
    return aZ;
  }
  double prevz = fendZ[0];
  for (unsigned iz(1); iz < nSlices; ++iz) {
    double extraz = aZ - prevz;
    double stepz = fendZ[iz] - fstart[iz].Z();
    if (extraz < stepz) {
      idx = iz;
      return fstart[iz].Z() + extraz;
    }
    prevz += stepz;
  }
  // set a default to the last value
  idx = nSlices - 1;
  return fendZ[idx];
}

std::string MuonPath::GetLabel(const std::string& aVol,
                               const std::string& aMat) const {
  //@FIXME AMM-avoid hardcoding, pass by config ?
  std::string label = "REST";
  if (aVol.find("Magn") != aVol.npos)
    label = "MS";
  else if (aVol.find("Upstream") != aVol.npos)
    label = "UBT";
  // The balloon skin includes the walls and both lids; decay_medium is HE.
  else if (aVol.find("HeBalloon") != aVol.npos)
    label = "HeBalloon";
  else if (aMat.find("helium") != aMat.npos)
    label = "HE";
  else if (aMat.find("air") != aMat.npos)
    label = "AIR";
  else if (aVol.find("straw") != aVol.npos)
    label = "SSTsens";
  else if (aVol.find("gas") != aVol.npos && aMat.find("STT") != aMat.npos)
    label = "SSTsens";
  else if (aVol.find("wire") != aVol.npos && aMat.find("tungsten") != aMat.npos)
    label = "SSTsens";
  else if ((aVol.find("Tr1_frame") != aVol.npos ||
            aVol.find("Tr2_frame") != aVol.npos ||
            aVol.find("Tr3_frame") != aVol.npos ||
            aVol.find("Tr4_frame") != aVol.npos))
    label = "SSTfr";
  else if ((aVol.find("Veto") != aVol.npos ||
            aVol.find("vLongitRib") != aVol.npos))
    label = "SBTfr";
  else if (aVol.find("LiSc") != aVol.npos)
    label = "SBTsens";
  LOG(debug) << aVol << " " << aMat << " assigned to " << label << ".";
  return label;
}

void MuonPath::Print() {
  const unsigned nSlices = GetNSlices();

  std::ostringstream ldebug;
  ldebug << flabel << " "
         << " d=" << fdensity << " l=" << flength << " l_in_z=" << fzlength;
  if (flength > 0) ldebug << " <d>=" << fwdensity / flength << '\n';

  if (nSlices == 0) {
    ldebug << "z-slices n=0\n";
    LOG(debug) << ldebug.str();
    return;
  }

  ldebug << " zIn=" << fstart[0].Z() << " zOut=" << fendZ[nSlices - 1] << '\n';
  ldebug << "z-slices n=" << nSlices << ": \n";
  for (unsigned iz(0); iz < nSlices; ++iz) {
    ldebug << fvolName[iz] << " " << fmaterial[iz] << " vtxz=" << fvtx[iz].Z()
           << " slice [" << fstart[iz].Z() << "-" << fendZ[iz] << "] \n";
  }
  ldebug << '\n';
  LOG(debug) << ldebug.str();
}

bool MuonPath::Add(const MuonPath& aEle) {
  // path added should always have only one element...
  if (aEle.GetNSlices() != 1) {
    LOG(error) << " -- incorrect number of elements in path: "
               << aEle.GetNSlices();
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
  fendLength.push_back(flength);
  fsliceDensity.push_back(aEle.fsliceDensity[0]);
  fwdensity += aEle.fwdensity;
  fzlength += aEle.fendZ[0] - aEle.fstart[0].Z();
  return true;
}
