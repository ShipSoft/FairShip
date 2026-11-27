// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

// FixedTargetGenerator with EvtGen: EvtGen decays D_s with B(D_s -> tau nu)
// set to the world average, and with --tau-only to tau nu only, and keeps
// the tau polarisation. Uses the charm mode with a synthetic cascade file of
// D_s+ D_s- pairs. EvtGen can be set up only once per process, so the
// default and the tau-only mode are separate runs: pass "tauonly" for the
// latter, and "jpsimainly" for --Jpsi-mainly, with J/psi as input, which
// must all decay to mu+ mu-.

#include <TFile.h>
#include <TGeoManager.h>
#include <TGeoMaterial.h>
#include <TGeoMedium.h>
#include <TGeoVolume.h>
#include <TH1F.h>
#include <TLorentzVector.h>
#include <TNtuple.h>

#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <vector>

#include "FairPrimaryGenerator.h"
#include "FixedTargetGenerator.h"
#include "Pythia8/Pythia.h"

namespace {

// Discards the tracks: only the Pythia8 event record is checked
class NullPrimaryGenerator : public FairPrimaryGenerator {
 public:
  void AddTrack(Int_t, Double_t, Double_t, Double_t, Double_t, Double_t,
                Double_t, Int_t, Bool_t, Double_t, Double_t, Double_t,
                TMCProcess) override {}
};

void BuildGeometry() {
  auto* geo = new TGeoManager("geo", "tungsten block");
  auto* vacuum =
      new TGeoMedium("vacuum", 1, new TGeoMaterial("vacuum", 0, 0, 0));
  auto* tungsten = new TGeoMedium(
      "tungsten", 2, new TGeoMaterial("tungsten", 183.84, 74, 19.3));
  TGeoVolume* world = geo->MakeBox("world", vacuum, 100., 100., 200.);
  geo->SetTopVolume(world);
  world->AddNode(geo->MakeBox("target", tungsten, 10., 10., 50.), 1);
  geo->CloseGeometry();
}

}  // namespace

int main(int argc, char** argv) {
  const bool tauOnly = argc > 1 && std::strcmp(argv[1], "tauonly") == 0;
  const bool jpsiMainly = argc > 1 && std::strcmp(argv[1], "jpsimainly") == 0;
  if (std::getenv("EVTGENDATA") == nullptr ||
      std::getenv("FAIRSHIP") == nullptr) {
    std::printf("EVTGENDATA or FAIRSHIP not set: skipping\n");
    return 0;
  }
  BuildGeometry();

  const char* fname = tauOnly      ? "test_ds_tauonly.root"
                      : jpsiMainly ? "test_jpsi.root"
                                   : "test_ds.root";
  const int nPairs = tauOnly || jpsiMainly ? 2000 : 25000;
  const double mDs = 1.96835;
  {
    TFile f(fname, "RECREATE");
    TNtuple nt("pythia6", "synthetic cascade",
               "id:px:py:pz:E:M:mid:mpx:mpy:mpz:mE:mM:k");
    TH1F h("2", "nr signal per cascade depth", 50, 0.5, 50.5);
    for (int i = 0; i < nPairs; ++i) {
      for (int sign : {1, -1}) {
        if (jpsiMainly) {
          nt.Fill(443, 0., 0., 0., 3.0969, 3.0969, 2212, 0., 0., 400., 400.0011,
                  0.938272, 1);
          h.Fill(1);
          continue;
        }
        // D_s at rest, so that the tau direction is the boost axis
        nt.Fill(431 * sign, 0., 0., 0., mDs, mDs, 2212, 0., 0., 400., 400.0011,
                0.938272, 1);
        h.Fill(1);
      }
    }
    f.Write();
  }

  FixedTargetGenerator gen;
  gen.SetChicc(2e-3);
  gen.WithEvtGen();
  gen.SetEnergyCut(0.);
  gen.SetTargetCoordinates(-50., 50.);
  if (tauOnly) gen.SetTauOnly();
  if (jpsiMainly) gen.SetJpsiMainly();
  if (!gen.InitForCharmOrBeauty(fname, nPairs, 5e13, 0) || !gen.Init()) {
    std::printf("FAIL: initialisation\n");
    return 1;
  }
  NullPrimaryGenerator cpg;
  int nDs = 0, nTau = 0, nPi = 0, nJpsi = 0, nJpsiMuMu = 0;
  double sumCos = 0., sumCos2 = 0.;
  for (int i = 0; i < nPairs; ++i) {
    if (!gen.ReadEvent(&cpg)) {
      std::printf("FAIL: ReadEvent\n");
      return 1;
    }
    const Pythia8::Event& event = gen.GetPythia()->event;
    for (int j = 0; j < event.size(); ++j) {
      if (event[j].id() == 443) {
        nJpsi++;
        int nMu = 0;
        for (int d : event[j].daughterList()) {
          nMu += std::abs(event[d].id()) == 13;
        }
        nJpsiMuMu += nMu == 2;
      }
      if (std::abs(event[j].id()) != 431) continue;
      nDs++;
      for (int d : event[j].daughterList()) {
        const Pythia8::Particle& tau = event[d];
        if (std::abs(tau.id()) != 15) continue;
        nTau++;
        // tau -> pi nu: the pion angle in the tau rest frame relative to the
        // tau direction has <cos> = 1/3 for fully polarised taus from D_s
        const std::vector<int> kids = tau.daughterList();
        if (kids.size() != 2) break;
        const int iPi =
            std::abs(event[kids[0]].id()) == 211 ? kids[0] : kids[1];
        if (std::abs(event[iPi].id()) != 211) break;
        TLorentzVector t(tau.px(), tau.py(), tau.pz(), tau.e());
        TLorentzVector pi(event[iPi].px(), event[iPi].py(), event[iPi].pz(),
                          event[iPi].e());
        pi.Boost(-t.BoostVector());
        const double c = std::cos(pi.Vect().Angle(t.Vect()));
        nPi++;
        sumCos += c;
        sumCos2 += c * c;
        break;
      }
    }
  }
  std::remove(fname);

  int failures = 0;
  if (jpsiMainly) {
    std::printf("Jpsi-mainly: %d J/psi, %d to mu+ mu-\n", nJpsi, nJpsiMuMu);
    if (nJpsi != 2 * nPairs || nJpsiMuMu != nJpsi) {
      std::printf("FAIL: every J/psi should decay to mu+ mu-\n");
      failures++;
    }
    if (failures == 0) std::printf("All checks passed\n");
    return failures == 0 ? 0 : 1;
  }
  const double br = static_cast<double>(nTau) / nDs;
  const double brErr = std::sqrt(br * (1. - br) / nDs);
  std::printf("%s: %d D_s, B(D_s -> tau nu) = %.4f +- %.4f\n",
              tauOnly ? "tau-only" : "default", nDs, br, brErr);
  if (nDs != 2 * nPairs) {
    std::printf("FAIL: expected %d D_s, found %d\n", 2 * nPairs, nDs);
    failures++;
  }
  const double expected = tauOnly ? 1. : 0.0536;
  if (std::abs(br - expected) > 5. * std::max(brErr, 1e-6)) {
    std::printf("FAIL: B(D_s -> tau nu) should be %.4f\n", expected);
    failures++;
  }
  const double meanCos = sumCos / nPi;
  const double polarisation = 3. * meanCos;
  const double polErr =
      3. * std::sqrt((sumCos2 / nPi - meanCos * meanCos) / nPi);
  std::printf("tau -> pi nu: %d, polarisation %.2f +- %.2f\n", nPi,
              polarisation, polErr);
  if (polarisation < 1. - 5. * polErr) {
    std::printf("FAIL: taus from D_s should be fully polarised\n");
    failures++;
  }
  if (failures == 0) std::printf("All checks passed\n");
  return failures == 0 ? 0 : 1;
}
