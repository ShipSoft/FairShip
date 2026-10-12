// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

// JpsiGenerator in a small TGeo geometry (Mo slab, gap, W slab):
//  1. the target taken from the geometry gives the same rate per POT and weight
//     as the sampler's layer model for the same slabs (closure);
//  2. injected J/psi: every muon's mother is the J/psi pushed just before it
//     (local index), the muons carry the generator weight and the J/psi the
//     weight 1, and the vertices lie in the material.

#include <TGeoManager.h>
#include <TGeoMaterial.h>
#include <TGeoMatrix.h>
#include <TGeoMedium.h>
#include <TGeoVolume.h>

#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <string>
#include <vector>

#include "FairPrimaryGenerator.h"
#include "JpsiGenerator.h"
#include "JpsiSampler.h"

namespace {

int gFailures = 0;

void Check(const std::string& what, bool ok, const std::string& detail = "") {
  std::printf("  [%s] %s%s%s\n", ok ? "PASS" : "FAIL", what.c_str(),
              detail.empty() ? "" : " : ", detail.c_str());
  if (!ok) ++gFailures;
}

std::string Num(double x) {
  char b[32];
  std::snprintf(b, sizeof b, "%.6g", x);
  return b;
}

struct Track {
  int pdg;
  int parent;
  bool tracked;
  double weight;
  double z;
};

// Records the tracks instead of pushing them to a stack.
class RecordingPrimaryGenerator : public FairPrimaryGenerator {
 public:
  std::vector<Track> tracks;
  void AddTrack(Int_t pdgid, Double_t /*px*/, Double_t /*py*/, Double_t /*pz*/,
                Double_t /*vx*/, Double_t /*vy*/, Double_t vz, Int_t parent,
                Bool_t wanttracking, Double_t /*e*/, Double_t /*tof*/,
                Double_t weight, TMCProcess /*proc*/) override {
    tracks.push_back(
        {pdgid, parent, static_cast<bool>(wanttracking), weight, vz});
  }
};

}  // namespace

int main() {
  // Mo from z = 10 to 40 cm, gap to 45 cm, W from 45 to 105 cm
  auto* geom = new TGeoManager("jpsi_test", "J/psi generator test");
  auto* vacuum =
      new TGeoMedium("vacuum", 1, new TGeoMaterial("vacuum", 0, 0, 0));
  auto* mo = new TGeoMedium("molybdenum", 2,
                            new TGeoMaterial("molybdenum", 95.95, 42, 10.22));
  auto* w = new TGeoMedium("tungsten", 3,
                           new TGeoMaterial("tungsten", 183.84, 74, 19.3));
  TGeoVolume* top = geom->MakeBox("top", vacuum, 50, 50, 500);
  geom->SetTopVolume(top);
  top->AddNode(geom->MakeBox("mo", mo, 10, 10, 15), 1,
               new TGeoTranslation(0, 0, 25));
  top->AddNode(geom->MakeBox("w", w, 10, 10, 30), 1,
               new TGeoTranslation(0, 0, 75));
  geom->CloseGeometry();

  // 950 steps of 0.1 cm: the slab boundaries fall between step centres
  std::printf("Target from the geometry against the layer model\n");
  JpsiGenerator gen;
  gen.SetTargetCoordinates(10., 105.);
  gen.SetScanSteps(950);
  gen.SetNEvents(10);
  if (!gen.Init()) {
    std::printf("JpsiGenerator::Init failed\n");
    return 1;
  }
  std::printf("%s\n", gen.Summary().c_str());

  jpsi::Config ref = jpsi::NominalConfig();
  ref.nEvents = 10;
  ref.zStart_cm = 10.;
  ref.layers = {{jpsi::TargetFromA(95.95, 10.22, "molybdenum"), 30.},
                {jpsi::TargetFromA(1., 0., "gap"), 5.},
                {jpsi::TargetFromA(183.84, 19.3, "tungsten"), 60.}};
  jpsi::Sampler sref(ref);
  const double expect = sref.GetNormalisation().probMuMuPerPot *
                        sref.GetNormalisation().secondaryFactor;
  Check("rate per POT: geometry = layer model",
        std::abs(gen.ProbMuMuPerPot() / expect - 1.) < 1e-6,
        Num(gen.ProbMuMuPerPot()) + " vs " + Num(expect));
  Check("weight = rate per POT (physics weight)",
        std::abs(gen.EventWeight() / sref.GetNormalisation().rate - 1.) < 1e-6);

  std::printf("\nInjection: track bookkeeping\n");
  JpsiGenerator inj;
  inj.SetInjection(kTRUE);
  inj.SetMeanPerEvent(2.5);
  inj.SetTargetCoordinates(10., 105.);
  inj.SetScanSteps(950);
  if (!inj.Init()) {
    std::printf("JpsiGenerator::Init failed\n");
    return 1;
  }
  const double weight = inj.EventWeight();
  bool mothers = true;
  bool weights = true;
  bool vertices = true;
  bool counts = true;
  int nJpsi = 0;
  RecordingPrimaryGenerator rec;
  for (int event = 0; event < 200; ++event) {
    rec.tracks.clear();
    inj.ReadEvent(&rec);
    int inEvent = 0;
    for (std::size_t i = 0; i < rec.tracks.size(); ++i) {
      const Track& t = rec.tracks[i];
      if (t.pdg != 443) continue;
      ++inEvent;
      weights &= t.weight == 1. && !t.tracked && t.parent == -1;
      vertices &= (t.z > 10. && t.z < 40.) || (t.z > 45. && t.z < 105.);
      for (std::size_t k = i + 1; k < i + 3 && k < rec.tracks.size(); ++k) {
        const Track& m = rec.tracks[k];
        mothers &= std::abs(m.pdg) == 13 && m.parent == static_cast<int>(i);
        weights &= std::abs(m.weight / weight - 1.) < 1e-12 && m.tracked;
      }
    }
    counts &= inEvent == 2 || inEvent == 3;
    nJpsi += inEvent;
  }
  Check("muons point to their J/psi (local index)", mothers);
  Check("muons carry the weight, the J/psi weight 1", weights);
  Check("vertices in the material", vertices);
  Check("2 or 3 J/psi per event for mu = 2.5", counts);
  Check("mean number of J/psi per event near 2.5",
        std::abs(nJpsi / 200. - 2.5) < 0.15, Num(nJpsi / 200.));

  std::printf("\n%s (%d failures)\n", gFailures ? "FAILED" : "ALL PASSED",
              gFailures);
  return gFailures ? EXIT_FAILURE : EXIT_SUCCESS;
}
