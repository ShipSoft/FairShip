#include "MuonPath.h"

#include <algorithm>
#include <cmath>
#include <iostream>

#include "FairLogger.h"

MuonPath::MuonPath() {
  flabel = "None";
  fdensity = 0;
  fwdensity = 0;
  flength = 0;
  fzlength = 0;
}

void MuonPath::SetVertexInfo(const TVector3& vecpos, const TVector3& vecp,
                             const double& time, int pdg) {
  fvtx.push_back(vecpos);
  fvtxT.push_back(time);
  fpvec.push_back(vecp);
  fpdg.push_back(pdg);
}

double MuonPath::GetZ(const double& aZ, unsigned& idx) const {
  //@FIXME AMM- is this efficient enough??
  if (aZ < fendZ[0]) {
    idx = 0;
    return aZ;
  }
  double prevz = fendZ[0];
  for (unsigned iz(1); iz < fendZ.size(); ++iz) {
    double extraz = aZ - prevz;
    double stepz = fendZ[iz] - fstart[iz].Z();
    if (extraz < stepz) {
      idx = iz;
      return fstart[iz].Z() + extraz;
    }
    prevz += stepz;
  }
  // set a default to the last value
  return fendZ[fendZ.size()-1];
}

std::string MuonPath::GetLabel(const std::string& aVol,
                               const std::string& aMat) const {
  //@FIXME AMM-avoid hardcoding, pass by config ?
  if (aVol.find("Magn") != aVol.npos)
    return "MS";
  else if (aVol.find("Upstream") != aVol.npos)
    return "UBT";
  else if (aVol.find("Decay") != aVol.npos && aMat.find("helium") != aMat.npos)
    return "HE";
  else if (aMat.find("air") != aMat.npos)
    return "AIR";
  else if (aVol.find("straw") != aVol.npos)
    return "SSTsens";
  else if (aVol.find("gas") != aVol.npos && aMat.find("STT") != aMat.npos)
    return "SSTsens";
  else if (aVol.find("wire") != aVol.npos && aMat.find("tungsten") != aMat.npos)
    return "SSTsens";
  else if ((aVol.find("Tr1_frame") != aVol.npos ||
	    aVol.find("Tr2_frame") != aVol.npos ||
	    aVol.find("Tr3_frame") != aVol.npos ||
	    aVol.find("Tr4_frame") != aVol.npos))
    return "SSTfr";
  else if ((aVol.find("Veto") != aVol.npos ||
            aVol.find("vLongitRib") != aVol.npos))
    return "SBTfr";
  else if (aVol.find("LiSc") != aVol.npos)
    return "SBTsens";
  else {
    LOG(debug) << aVol << " " << aMat << " assigned to REST.";
    return "REST";
  }
}

void MuonPath::Print() {
  std::ostringstream ldebug;
  ldebug << flabel << " "
         << " d=" << fdensity
         << " l=" << flength << " l_in_z=" << fzlength;
  if (flength > 0) ldebug << " <d>=" << fwdensity / flength;
  ldebug << std::endl
         << " zIn=" << fstart[0].Z() << " zOut=" << fendZ[GetNSlices() - 1]
         << std::endl;
  ldebug << "z-slices n=" << GetNSlices() << ": " << std::endl;
  for (unsigned iz(0); iz < GetNSlices(); ++iz) {
    ldebug << fvolName[iz] << " " << fmaterial[iz] << " vtxz=" << fvtx[iz].Z()
           << " slice [" << fstart[iz].Z() << "-" << fendZ[iz] << "] "
           << std::endl;
  }
  ldebug << std::endl;
  LOG(debug) << ldebug.str();
}

bool MuonPath::Add(const MuonPath& aEle) {
  // path added should always have only one element...
  if (aEle.GetNSlices() != 1) {
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
  fpdg.push_back(aEle.fpdg[0]);
  flength += aEle.flength;
  fwdensity += aEle.fdensity * aEle.flength;
  fzlength += aEle.fendZ[0] - aEle.fstart[0].Z();
  return true;
}

void MuonPath::SetField(TVirtualMagField* field) {
  if (!field) {
    LOG(error) << "MuonPath::SetField received null pointer!";
    return;
  }

  fField = field;
}

TVector3 MuonPath::GetField(const TVector3& pos) const {
  if (!fField) {
    LOG(error) << "MuonPath::GetField: no magnetic field set!";
    return TVector3();
  }

  Double_t x[3] = {pos.X(), pos.Y(), pos.Z()};
  Double_t B[3] = {0., 0., 0.};
  fField->Field(x, B);  // position in cm, B in kGauss

  const TVector3 field(B[0], B[1], B[2]);

  return field;
}

void MuonPath::RungeKuttaStep(TVector3& position, TVector3& momentum,
                              double stepCm, int charge,
                              double momentumMagnitude) const {
  // GeV/(c*cm*kGauss).  With position in cm and B in kGauss this gives
  // dp/ds directly in GeV/c per cm.
  const double kB2C = 2.99792458e-4;

  struct Derivative {
    TVector3 dr;
    TVector3 dp;
  };

  auto derivative = [this, charge, kB2C](const TVector3& r,
                                         const TVector3& p) -> Derivative {
    Derivative d;
    const double pMag = p.Mag();
    if (pMag <= 0.) {
      d.dr.SetXYZ(0., 0., 0.);
      d.dp.SetXYZ(0., 0., 0.);
      return d;
    }

    const TVector3 direction = p * (1. / pMag);
    const TVector3 field = GetField(r);
    d.dr = direction;
    d.dp = charge * kB2C * direction.Cross(field);
    return d;
  };

  const Derivative k1 = derivative(position, momentum);
  const Derivative k2 = derivative(position + 0.5 * stepCm * k1.dr,
                                   momentum + 0.5 * stepCm * k1.dp);
  const Derivative k3 = derivative(position + 0.5 * stepCm * k2.dr,
                                   momentum + 0.5 * stepCm * k2.dp);
  const Derivative k4 = derivative(position + stepCm * k3.dr,
                                   momentum + stepCm * k3.dp);

  position += (stepCm / 6.) *
              (k1.dr + 2. * k2.dr + 2. * k3.dr + k4.dr);
  momentum += (stepCm / 6.) *
              (k1.dp + 2. * k2.dp + 2. * k3.dp + k4.dp);

  // The magnetic field changes the direction, not the momentum magnitude.
  if (momentum.Mag() > 0. && momentumMagnitude > 0.)
    momentum.SetMag(momentumMagnitude);
}

bool MuonPath::ExtrapolateField(const TVector3& start,
                                const TVector3& momentum,
                                double zTarget, int pdg,
                                TVector3& outPosition,
                                TVector3& outMomentum,
                                double& outPathLength,
                                double maxStepCm) const {
  outPosition = start;
  outMomentum = momentum;
  outPathLength = 0.;

  if (!fField) {
    LOG(error) << "ExtrapolateField: null magnetic field";
    return false;
  }
  if (pdg != 13 && pdg != -13) {
    LOG(error) << "ExtrapolateField: invalid PDG=" << pdg;
    return false;
  }
  if (momentum.Mag() <= 0. || std::abs(momentum.Z()) < 1.e-12) {
    LOG(error) << "ExtrapolateField: invalid momentum";
    return false;
  }

  const int charge = (pdg == 13) ? -1 : +1;
  const double p0 = momentum.Mag();
  const double maxStep = std::max(0.1, std::abs(maxStepCm));

  TVector3 position = start;
  TVector3 p = momentum;

  for (unsigned i = 0; i < 200000; ++i) {
    const double dz = zTarget - position.Z();

    if (std::abs(dz) < 1.e-5) {
      position.SetZ(zTarget);
      outPosition = position;
      outMomentum = p;
      return true;
    }

    const double pMag = p.Mag();
    if (pMag <= 0. || std::abs(p.Z()) < 1.e-12) {
      LOG(error) << "ExtrapolateField: invalid propagated momentum";
      return false;
    }

    // Convert the remaining delta-z into a path-length step.  This also makes
    // the final RK step land on the requested z plane without overshooting it.
    const double dsToZ = dz * pMag / p.Z();
    const double step = std::copysign(std::min(maxStep, std::abs(dsToZ)), dsToZ);

    RungeKuttaStep(position, p, step, charge, p0);
    outPathLength += std::abs(step);
  }

  LOG(error) << "ExtrapolateField: maximum steps reached targetZ=" << zTarget;
  return false;
}

bool MuonPath::ExtrapolateField(double zTarget, unsigned idx,
                                TVector3& outPosition,
                                TVector3& outMomentum,
                                double& outPathLength,
                                double maxStepCm) const {
  if (idx >= GetNSlices()) {
    LOG(error) << "ExtrapolateField: invalid slice=" << idx;
    return false;
  }

  return ExtrapolateField(fvtx[idx], fpvec[idx], zTarget,
                          fpdg[idx], outPosition,
                          outMomentum, outPathLength, maxStepCm);
}
