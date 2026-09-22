// SPDX-License-Identifier: LGPL-3.0-or-later

#include "JpsiGenerator.h"

#include <algorithm>
#include <cmath>

#include "BeamSmearingUtils.h"
#include "FairLogger.h"
#include "FairPrimaryGenerator.h"
#include "TGeoManager.h"
#include "TGeoMaterial.h"
#include "TGeoNode.h"
#include "TGeoVolume.h"
#include "TMCProcess.h"

JpsiGenerator::~JpsiGenerator() = default;

// ---------------------------------------------------------------- setters

void JpsiGenerator::SetTargetMaterial(const TString& name) {
  if (name == "W" || name == "tungsten") {
    fCfg.target = jpsi::TungstenNA50();
  } else if (name == "Mo" || name == "molybdenum") {
    fCfg.target = jpsi::MolybdenumScaled();
  } else {
    LOG(fatal) << "JpsiGenerator: unknown target material " << name;
  }
}

void JpsiGenerator::SetTargetMaterial(Double_t A, Double_t density_gcm3,
                                      const TString& name) {
  fCfg.target = jpsi::TargetFromA(A, density_gcm3, name.Data());
}

void JpsiGenerator::SetRapidityShape(const TString& shape) {
  if (shape == "data") {
    fCfg.yShape = jpsi::YShape::Data;
  } else if (shape == "hybrid") {
    fCfg.yShape = jpsi::YShape::Hybrid;
  } else if (shape == "gauss") {
    fCfg.yShape = jpsi::YShape::Gauss;
  } else {
    LOG(fatal) << "JpsiGenerator: unknown rapidity shape " << shape;
  }
}

void JpsiGenerator::SetOutputMode(const TString& mode) {
  if (mode == "mumu") {
    fCfg.output = jpsi::Output::MuMu;
  } else if (mode == "jpsi") {
    fCfg.output = jpsi::Output::Jpsi;
  } else if (mode == "both") {
    fCfg.output = jpsi::Output::Both;
  } else {
    LOG(fatal) << "JpsiGenerator: unknown output mode " << mode;
  }
}

void JpsiGenerator::AddLayer(const TString& material, Double_t length_cm) {
  jpsi::Layer l;
  if (material == "W") {
    l.material = jpsi::TungstenNA50();
  } else if (material == "Mo") {
    l.material = jpsi::MolybdenumScaled();
  } else {
    LOG(fatal) << "JpsiGenerator: unknown layer material " << material;
  }
  l.length_cm = length_cm;
  fCfg.layers.push_back(l);
}

void JpsiGenerator::SetTargetCoordinates(Double_t z0_cm, Double_t z1_cm,
                                         Double_t x_cm, Double_t y_cm) {
  fUseGeometry = kTRUE;
  fZ0 = z0_cm;
  fZ1 = z1_cm;
  fXoff = x_cm;
  fYoff = y_cm;
  fCfg.layers.clear();
}

Double_t JpsiGenerator::ChiMuMu() const {
  return fSampler ? fSampler->GetNormalisation().chiMuMu : 0.;
}
Double_t JpsiGenerator::ProbMuMuPerPot() const {
  return fSampler ? fSampler->GetNormalisation().probMuMuPerPot : 0.;
}
Double_t JpsiGenerator::EventWeight() const {
  return fSampler ? fSampler->GetNormalisation().weight : 0.;
}
Long_t JpsiGenerator::NEventsToGenerate() const {
  return fSampler ? fSampler->NEvents() : 0;
}
std::string JpsiGenerator::Summary() const {
  return fSampler ? fSampler->Summary()
                  : std::string("JpsiGenerator: not initialised");
}
std::vector<std::pair<std::string, double>> JpsiGenerator::Metadata() const {
  return fSampler ? fSampler->Metadata()
                  : std::vector<std::pair<std::string, double>>{};
}

// ---------------------------------------------------------------- geometry

Bool_t JpsiGenerator::ScanGeometry() {
  // One scan gives both the vertex CDF and the absolute rate:
  //   dP/dz = exp(-tau(z)) * n_A(z) * B_mumu sigma_Jpsi(A(z))
  // with sigma_Jpsi ~ A^alpha, which is NOT proportional to the inelastic
  // density once the target mixes materials.
  if (!gGeoManager) {
    LOG(fatal) << "JpsiGenerator: no geometry loaded";
    return kFALSE;
  }
  if (fZ1 <= fZ0) {
    LOG(fatal) << "JpsiGenerator: empty target interval";
    return kFALSE;
  }

  const Int_t n = std::max(100, fScanSteps);
  const Double_t dz = (fZ1 - fZ0) / n;
  fZGrid.assign(n + 1, 0.);
  std::vector<Double_t> dens(n + 1, 0.);
  Double_t tau = 0.;
  Double_t rate = 0.;  // J/psi -> mu mu per POT

  for (Int_t i = 0; i <= n; ++i) {
    const Double_t z = fZ0 + i * dz;
    fZGrid[i] = z;
    TGeoNode* node = gGeoManager->FindNode(fXoff, fYoff, z);
    if (!node || gGeoManager->IsOutside()) continue;
    TGeoMaterial* mat = node->GetVolume()->GetMaterial();
    if (!mat || mat->GetA() <= 0 || mat->GetDensity() <= 0) continue;
    const Double_t intLen_cm = mat->GetIntLen();  // cm
    if (i > 0 && intLen_cm > 0) tau += dz / intLen_cm;
    const Double_t nA_cm3 =
        mat->GetDensity() * jpsi::kAvogadro / mat->GetA();
    const Double_t bSigma_cm2 = fSampler->BSigmaFullForA(mat->GetA());
    dens[i] = std::exp(-tau) * nA_cm3 * bSigma_cm2;
  }
  for (Int_t i = 1; i <= n; ++i) rate += 0.5 * (dens[i] + dens[i - 1]) * dz;
  if (rate <= 0) {
    LOG(fatal) << "JpsiGenerator: no material found along the target axis";
    return kFALSE;
  }

  fZCdf.assign(n + 1, 0.);
  for (Int_t i = 1; i <= n; ++i) {
    fZCdf[i] = fZCdf[i - 1] + 0.5 * (dens[i] + dens[i - 1]) * dz;
  }
  for (auto& c : fZCdf) c /= fZCdf.back();

  fSampler->SetProbMuMuPerPot(rate);
  LOG(info) << "JpsiGenerator: geometry scan gives P(J/psi->mumu)/POT = " << rate;
  return kTRUE;
}

// ---------------------------------------------------------------- Init

Bool_t JpsiGenerator::Init() {
  try {
    fSampler = std::make_unique<jpsi::Sampler>(fCfg);
  } catch (const std::exception& e) {
    LOG(fatal) << "JpsiGenerator: " << e.what();
    return kFALSE;
  }
  if (fUseGeometry && !ScanGeometry()) return kFALSE;
  LOG(info) << fSampler->Summary();
  return kTRUE;
}

// ---------------------------------------------------------------- event

Bool_t JpsiGenerator::ReadEvent(FairPrimaryGenerator* cpg) {
  if (!fSampler) {
    LOG(fatal) << "JpsiGenerator: ReadEvent before Init";
    return kFALSE;
  }
  IncrementCounter("generated_events");

  jpsi::Event ev = fSampler->Next();
  const Double_t w = ev.weight;

  // vertex: geometry CDF, slab model, or the fixed start plane
  Double_t z = fCfg.zStart_cm;
  if (!fZCdf.empty()) {
    const double u = fSampler->Uniform();
    const auto it = std::lower_bound(fZCdf.begin(), fZCdf.end(), u);
    const std::size_t i =
        std::min<std::size_t>(std::distance(fZCdf.begin(), it), fZCdf.size() - 1);
    if (i == 0) {
      z = fZGrid.front();
    } else {
      const double den = fZCdf[i] - fZCdf[i - 1];
      const double f = den > 0 ? (u - fZCdf[i - 1]) / den : 0.;
      z = fZGrid[i - 1] + f * (fZGrid[i] - fZGrid[i - 1]);
    }
  } else {
    z = ev.z_cm;
  }

  // Same beam profile as FixedTargetGenerator (Gaussian smearing + painting).
  const auto [dx, dy] = CalculateBeamOffset(fSmearBeam, fPaintBeam);
  const Double_t x = fXoff + dx;
  const Double_t y = fYoff + dy;

  if (fCfg.output == jpsi::Output::Jpsi) {
    // inclusive, transported J/psi: it carries the physical weight itself
    cpg->AddTrack(443, ev.jpsi.px, ev.jpsi.py, ev.jpsi.pz, x, y, z, -1, kTRUE,
                  ev.jpsi.E, 0., w, kPPrimary);
    IncrementCounter("stored_tracks");
    IncrementCounter("tracked_final_state_particles");
    return kTRUE;
  }

  // Truth-level mother with weight 1: ShipStack multiplies daughter weights by
  // the parent's when splitting is on, so this must not be w.
  cpg->AddTrack(443, ev.jpsi.px, ev.jpsi.py, ev.jpsi.pz, x, y, z, -1, kFALSE,
                ev.jpsi.E, 0., 1.0, kPPrimary);
  IncrementCounter("stored_tracks");

  if (!IsInVesselAcceptance(ev.mup.px, ev.mup.py, ev.mup.pz) &&
      !IsInVesselAcceptance(ev.mum.px, ev.mum.py, ev.mum.pz)) {
    IncrementCounter("geometry_rejected_events");
    return kTRUE;
  }
  cpg->AddTrack(-13, ev.mup.px, ev.mup.py, ev.mup.pz, x, y, z, 0, kTRUE,
                ev.mup.E, 0., w, kPDecay);
  cpg->AddTrack(13, ev.mum.px, ev.mum.py, ev.mum.pz, x, y, z, 0, kTRUE,
                ev.mum.E, 0., w, kPDecay);
  IncrementCounter("stored_tracks", 2);
  IncrementCounter("tracked_final_state_particles", 2);
  return kTRUE;
}

ClassImp(JpsiGenerator);
