// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#include "JpsiGenerator.h"

#include <algorithm>
#include <cmath>
#include <set>
#include <sstream>

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

void JpsiGenerator::SetConfigFile(const TString& path) {
  // FairShip sets these itself: the run seed, the number of events (-n), the
  // target (from the geometry) and the weight convention (physics weights)
  static const std::set<std::string> kSetByFairShip = {
      "seed", "n_events", "n_pot", "physics_weight", "target", "layers"};
  std::vector<std::string> keys;
  try {
    jpsi::ApplyConfigFile(fCfg, path.Data(), &keys);
  } catch (const std::exception& e) {
    LOG(fatal) << "JpsiGenerator: " << e.what();
  }
  for (const auto& k : keys) {
    if (kSetByFairShip.count(k) != 0) {
      LOG(fatal) << "JpsiGenerator: key '" << k << "' in " << path
                 << " is set by FairShip (seed: the run seed, n_events: -n, "
                    "target and layers: the geometry, weights: physics "
                    "weights); remove it";
    }
  }
  fConfigFile = path.Data();
}

void JpsiGenerator::SetOutputMode(const TString& mode) {
  if (mode == "mumu") {
    fCfg.output = jpsi::Output::MuMu;
  } else if (mode == "jpsi") {
    fCfg.output = jpsi::Output::Jpsi;
  } else {
    LOG(fatal) << "JpsiGenerator: unknown output mode " << mode
               << " (mumu or jpsi)";
  }
}

void JpsiGenerator::SetTargetCoordinates(Double_t z0_cm, Double_t z1_cm,
                                         Double_t x_cm, Double_t y_cm) {
  fUseGeometry = kTRUE;
  fZ0 = z0_cm;
  fZ1 = z1_cm;
  fXoff = x_cm;
  fYoff = y_cm;
}

// ---------------------------------------------------------------- results

Double_t JpsiGenerator::ProbMuMuPerPot() const {
  return fSampler ? fSampler->GetNormalisation().probMuMuPerPot *
                        fSampler->GetNormalisation().secondaryFactor
                  : 0.;
}
Double_t JpsiGenerator::EventWeight() const {
  return fSampler ? fSampler->GetNormalisation().weight : 0.;
}
Double_t JpsiGenerator::MeanPerEvent() const {
  return fSampler ? fSampler->GetNormalisation().meanPerEvent : 0.;
}
Long_t JpsiGenerator::NEventsToGenerate() const {
  return fSampler ? fSampler->NEvents() : 0;
}
std::string JpsiGenerator::ConfigText() const {
  std::string t = fCfg.provenance;
  if (!fCfg.dataMap.text.empty()) {
    t += "# data map file " + fCfg.dataMap.source + "\n" + fCfg.dataMap.text;
  }
  return t;
}
std::string JpsiGenerator::Summary() const {
  if (!fSampler) return "JpsiGenerator: not initialised";
  return fSampler->Summary() + "\n  configuration: " +
         (fConfigFile.empty() ? std::string("nominal (built in)")
                              : "nominal overridden by " + fConfigFile) +
         ScanSummary();
}
std::vector<std::pair<std::string, double>> JpsiGenerator::Metadata() const {
  return fSampler ? fSampler->Metadata()
                  : std::vector<std::pair<std::string, double>>{};
}

// ---------------------------------------------------------------- geometry

Bool_t JpsiGenerator::ScanGeometry() {
  if (!gGeoManager) {
    LOG(fatal) << "JpsiGenerator: no geometry loaded";
    return kFALSE;
  }
  if (fZ1 <= fZ0) {
    LOG(fatal) << "JpsiGenerator: empty target interval";
    return kFALSE;
  }
  // Materials at the middle of each step; consecutive steps in the same
  // material form one layer. Volumes without material (A or density 0) are
  // gaps.
  const Int_t n = std::max(100, fScanSteps);
  const Double_t dz = (fZ1 - fZ0) / n;
  fScan.clear();
  const TGeoMaterial* previous = nullptr;
  bool first = true;
  for (Int_t i = 0; i < n; ++i) {
    const Double_t z = fZ0 + (i + 0.5) * dz;
    const TGeoNode* node = gGeoManager->FindNode(fXoff, fYoff, z);
    const TGeoMaterial* mat = (node && !gGeoManager->IsOutside())
                                  ? node->GetVolume()->GetMaterial()
                                  : nullptr;
    if (mat && (mat->GetA() <= 0 || mat->GetDensity() <= 0)) mat = nullptr;
    if (!first && mat == previous) {
      fScan.back().length += dz;
      continue;
    }
    ScanLayer l;
    l.length = dz;
    if (mat) {
      l.name = mat->GetName();
      l.A = mat->GetA();
      l.density = mat->GetDensity();
      l.intLen = mat->GetIntLen();
    } else {
      l.name = "gap";
    }
    fScan.push_back(l);
    previous = mat;
    first = false;
  }
  fCfg.layers.clear();
  fCfg.zStart_cm = fZ0;
  bool dense = false;
  for (const auto& s : fScan) {
    jpsi::Layer l;
    l.length_cm = s.length;
    l.material = s.density > 0 ? jpsi::TargetFromA(s.A, s.density, s.name)
                               : jpsi::TargetFromA(1., 0., "gap");
    dense |= s.density > 0;
    fCfg.layers.push_back(l);
  }
  if (!dense) {
    LOG(fatal) << "JpsiGenerator: no material found along the target axis";
    return kFALSE;
  }
  return kTRUE;
}

std::string JpsiGenerator::ScanSummary() const {
  if (fScan.empty()) return "";
  // J/psi yield of the layer stack, up to a constant, for interaction lengths
  // lambda(layer): sum of n A^alpha lambda exp(-tau0) (1 - exp(-L/lambda))
  const double alpha = jpsi::TungstenNA50().alphaA;
  auto yield = [&](bool geometry) {
    double tau = 0.;
    double sum = 0.;
    for (const auto& s : fScan) {
      if (s.density <= 0) continue;
      const double lambda =
          geometry ? s.intLen
                   : jpsi::TargetFromA(s.A, s.density, s.name).lambdaInt_gcm2 /
                         s.density;
      const double nA = s.density / s.A;  // Avogadro cancels in the ratio
      sum += nA * std::pow(s.A, alpha) * lambda * std::exp(-tau) *
             (1. - std::exp(-s.length / lambda));
      tau += s.length / lambda;
    }
    return sum;
  };
  std::ostringstream os;
  os << "\n  target from the geometry, z = " << fZ0 << " to " << fZ1
     << " cm at (x, y) = (" << fXoff << ", " << fYoff
     << ") cm; interaction lengths [g/cm2], used (NA50 convention) and in "
        "the geometry:";
  std::set<std::string> listed;
  double length = 0.;
  for (const auto& s : fScan) {
    if (s.density <= 0) continue;
    length += s.length;
    if (!listed.insert(s.name).second) continue;
    const double used =
        jpsi::TargetFromA(s.A, s.density, s.name).lambdaInt_gcm2;
    os << "\n      " << s.name << " (A " << s.A << ", " << s.density
       << " g/cm3): " << used << " used, " << s.intLen * s.density
       << " geometry (x" << s.intLen * s.density / used << ")";
  }
  const double na50 = yield(false);
  os << "\n      " << length << " cm of material (" << fScan.size()
     << " layers with the gaps); with the geometry's interaction lengths the "
        "rate would be x"
     << (na50 > 0 ? yield(true) / na50 : 0.);
  return os.str();
}

// ---------------------------------------------------------------- Init

Bool_t JpsiGenerator::Init() {
  fCfg.physicsWeight = true;  // FairShip output carries physics weights only
  if (fCfg.output == jpsi::Output::Both) {
    LOG(info) << "JpsiGenerator: output 'both' is the same as 'mumu' here";
    fCfg.output = jpsi::Output::MuMu;
  }
  // the weights are per POT: they need the target the protons cross
  if (!fUseGeometry) {
    LOG(fatal) << "JpsiGenerator: no target, call SetTargetCoordinates";
    return kFALSE;
  }
  if (!ScanGeometry()) return kFALSE;
  try {
    fSampler = std::make_unique<jpsi::Sampler>(fCfg);
  } catch (const std::exception& e) {
    LOG(fatal) << "JpsiGenerator: " << e.what();
    return kFALSE;
  }
  LOG(info) << Summary();
  return kTRUE;
}

// ---------------------------------------------------------------- event

Int_t JpsiGenerator::PushJpsi(FairPrimaryGenerator* cpg, const jpsi::Event& ev,
                              Int_t firstIndex) {
  const Double_t w = ev.weight;
  const Double_t z = ev.z_cm;
  // Same beam profile as FixedTargetGenerator (Gaussian smearing + painting).
  const auto [dx, dy] = CalculateBeamOffset(fSmearBeam, fPaintBeam);
  const Double_t x = fXoff + dx;
  const Double_t y = fYoff + dy;

  if (fCfg.output == jpsi::Output::Jpsi) {
    // inclusive, transported J/psi: it carries the physical weight itself
    cpg->AddTrack(443, ev.jpsi.Px(), ev.jpsi.Py(), ev.jpsi.Pz(), x, y, z, -1,
                  kTRUE, ev.jpsi.E(), 0., w, kPPrimary);
    IncrementCounter("stored_tracks");
    IncrementCounter("tracked_final_state_particles");
    return 1;
  }

  // Truth-level mother with weight 1: ShipStack multiplies daughter weights by
  // the parent's when splitting is on, so this must not be w. Mother indices
  // are local to this generator; FairPrimaryGenerator adds the offset of any
  // tracks another generator (the host) already pushed in this event.
  cpg->AddTrack(443, ev.jpsi.Px(), ev.jpsi.Py(), ev.jpsi.Pz(), x, y, z, -1,
                kFALSE, ev.jpsi.E(), 0., 1.0, kPPrimary);
  IncrementCounter("stored_tracks");
  cpg->AddTrack(-13, ev.mup.Px(), ev.mup.Py(), ev.mup.Pz(), x, y, z, firstIndex,
                kTRUE, ev.mup.E(), 0., w, kPDecay);
  cpg->AddTrack(13, ev.mum.Px(), ev.mum.Py(), ev.mum.Pz(), x, y, z, firstIndex,
                kTRUE, ev.mum.E(), 0., w, kPDecay);
  IncrementCounter("stored_tracks", 2);
  IncrementCounter("tracked_final_state_particles", 2);
  return 3;
}

Bool_t JpsiGenerator::ReadEvent(FairPrimaryGenerator* cpg) {
  if (!fSampler) {
    LOG(fatal) << "JpsiGenerator: ReadEvent before Init";
    return kFALSE;
  }
  IncrementCounter("generated_events");

  // standalone: exactly one J/psi per event; injection: a tunable number
  const Int_t nJpsi = fCfg.injection ? fSampler->NumberToInject() : 1;
  Int_t index = 0;
  for (Int_t k = 0; k < nJpsi; ++k) {
    jpsi::Event ev = fSampler->Next();
    index += PushJpsi(cpg, ev, index);
    IncrementCounter("injected_jpsi");
  }
  return kTRUE;
}
