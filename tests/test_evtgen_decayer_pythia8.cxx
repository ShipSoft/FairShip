// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

// Pythia8 path of TEvtGenDecayer, the external decayer handed to Geant4:
// decay records, units, branching fractions and seeding.

#include <TClonesArray.h>
#include <TLorentzVector.h>
#include <TParticle.h>
#include <TRandom3.h>

#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <vector>

#include "Pythia8/Pythia.h"
#include "TEvtGenDecayer.h"

namespace {

int failures = 0;

void Check(bool ok, const char* what) {
  if (!ok) {
    std::printf("FAIL: %s\n", what);
    ++failures;
  }
}

// Decay pdg with momentum pz along z and import the record.
int DecayOnce(TEvtGenDecayer& decayer, TClonesArray& record, int pdg,
              double pz) {
  const double m =
      decayer.GetPythia()->particleData.m0(pdg);  // GeV, nominal mass
  TLorentzVector p(0., 0., pz, std::sqrt(pz * pz + m * m));
  decayer.Decay(pdg, &p);
  return decayer.ImportParticles(&record);
}

// Record structure and four-momentum conservation for one decay.
void CheckRecord(const TClonesArray& record, int n, int pdg, double pz) {
  auto* parent = static_cast<TParticle*>(record.At(0));
  Check(parent->GetPdgCode() == pdg, "entry 0 is the decaying particle");
  Check(parent->GetStatusCode() == 0, "decayed parent is not final");
  TLorentzVector sum;
  for (int i = 0; i < n; i++) {
    auto* part = static_cast<TParticle*>(record.At(i));
    Check(part->GetFirstDaughter() < n && part->GetLastDaughter() < n,
          "daughter indices inside the record");
    if (part->GetStatusCode() == 1) {
      TLorentzVector p4;
      part->Momentum(p4);
      sum += p4;
    }
  }
  Check(std::abs(sum.Pz() - pz) < 1e-6 * (1. + pz) && sum.Vect().Perp() < 1e-6,
        "final-state momentum equals parent momentum");
  Check(std::abs(sum.E() - parent->Energy()) < 1e-6 * (1. + parent->Energy()),
        "final-state energy equals parent energy");
}

}  // namespace

int main() {
  gRandom = new TRandom3(42);
  TEvtGenDecayer decayer;  // no EvtGen files: Pythia8 decays everything
  decayer.Init();
  TClonesArray record("TParticle");

  // Records of a few particles the simulation hands to the decayer.
  for (int pdg : {411, -421, 4122, 431, 15, -15}) {
    for (double pz : {0., 50.}) {
      for (int i = 0; i < 100; i++) {
        const int n = DecayOnce(decayer, record, pdg, pz);
        Check(n > 2, "decay record has products");
        CheckRecord(record, n, pdg, pz);
      }
    }
  }

  // Branching fraction: D+ -> K- + anything among the direct daughters,
  // compared with the decay table.
  auto& pd = decayer.GetPythia()->particleData;
  double expected = 0.;
  Pythia8::ParticleDataEntryPtr dplus = pd.particleDataEntryPtr(411);
  double brSum = 0.;
  for (int c = 0; c < dplus->sizeChannels(); c++) {
    const Pythia8::DecayChannel& ch = dplus->channel(c);
    if (ch.onMode() == 0) continue;
    brSum += ch.bRatio();
    for (int j = 0; j < ch.multiplicity(); j++) {
      if (ch.product(j) == -321) {
        expected += ch.bRatio();
        break;
      }
    }
  }
  expected /= brSum;
  const int nDecays = 100000;
  int nWithK = 0;
  for (int i = 0; i < nDecays; i++) {
    DecayOnce(decayer, record, 411, 0.);
    auto* parent = static_cast<TParticle*>(record.At(0));
    for (int d = parent->GetFirstDaughter(); d <= parent->GetLastDaughter();
         d++) {
      if (static_cast<TParticle*>(record.At(d))->GetPdgCode() == -321) {
        nWithK++;
        break;
      }
    }
  }
  const double frac = static_cast<double>(nWithK) / nDecays;
  const double sigma = std::sqrt(expected * (1. - expected) / nDecays);
  std::printf("D+ -> K- X: %.4f +- %.4f (decay table %.4f)\n", frac, sigma,
              expected);
  Check(std::abs(frac - expected) < 5. * sigma,
        "D+ -> K- X fraction agrees with the decay table");

  // Weakly decaying products (c tau0 above 1 um) come back undecayed, for
  // the transport to decay them where they decay: K0S, Lambda, tau from
  // D_s -> tau nu, ... Strong and electromagnetic decays (pi0, eta, rho, K*)
  // happen in Pythia8.
  int nLongLived = 0, nLongLivedDecayed = 0, nTau = 0, nShortLivedFinal = 0;
  for (int pdg : {411, 421, 431, 4122}) {
    for (int i = 0; i < 20000; i++) {
      const int n = DecayOnce(decayer, record, pdg, 0.);
      Check(static_cast<TParticle*>(record.At(0))->GetStatusCode() == 0,
            "the handed-over particle decays");
      for (int j = 1; j < n; j++) {
        auto* part = static_cast<TParticle*>(record.At(j));
        const int id = std::abs(part->GetPdgCode());
        if (pd.tau0(id) > 1e-3) {
          nLongLived++;
          if (part->GetStatusCode() != 1) nLongLivedDecayed++;
          if (id == 15) nTau++;
        } else if (pd.canDecay(id) && part->GetStatusCode() == 1) {
          nShortLivedFinal++;
        }
      }
    }
    Check(!pd.mayDecay(pdg),
          "species of the handed-over particle stays stable");
  }
  std::printf("weakly decaying products: %d (%d decayed), tau: %d\n",
              nLongLived, nLongLivedDecayed, nTau);
  Check(nLongLived > 1000 && nTau > 0, "weakly decaying products occur");
  Check(nLongLivedDecayed == 0, "weakly decaying products are not decayed");
  Check(nShortLivedFinal == 0, "short-lived products are decayed");

  // Units. The decaying particle decays where Geant4 hands it over, so its
  // daughters start at the origin at t = 0. Particles decayed further down
  // the chain get displaced vertices. With K0S decays switched on for this
  // check, their mean proper decay length must be c tau0 in cm and their
  // mean proper time tau0 in s.
  pd.mayDecay(310, true);
  const double cLight = 29979245800.;         // cm/s
  const double ctauK0S = pd.tau0(310) * 0.1;  // mm -> cm
  double sumL = 0., sumL2 = 0., sumT = 0.;
  int nK0S = 0;
  int nDisplacedPrimary = 0;
  for (int i = 0; i < nDecays; i++) {
    const int n = DecayOnce(decayer, record, 411, 50.);
    for (int j = 1; j < n; j++) {
      auto* part = static_cast<TParticle*>(record.At(j));
      if (part->GetFirstMother() == 0 &&
          (part->Vx() != 0. || part->Vy() != 0. || part->Vz() != 0.)) {
        nDisplacedPrimary++;
      }
      if (part->GetPdgCode() != 310 || part->GetFirstDaughter() <= 0) continue;
      auto* daughter =
          static_cast<TParticle*>(record.At(part->GetFirstDaughter()));
      const double bg = part->P() / part->GetMass();
      const double l = std::sqrt(daughter->Vx() * daughter->Vx() +
                                 daughter->Vy() * daughter->Vy() +
                                 daughter->Vz() * daughter->Vz()) /
                       bg;  // cm
      sumL += l;
      sumL2 += l * l;
      sumT += (daughter->T() - part->T()) / (part->Energy() / part->GetMass());
      nK0S++;
    }
  }
  Check(nDisplacedPrimary == 0, "direct daughters start at the origin");
  Check(nK0S > 1000, "enough K0S in D+ decays");
  const double meanL = sumL / nK0S;
  const double errL = std::sqrt((sumL2 / nK0S - meanL * meanL) / nK0S);
  const double meanT = sumT / nK0S;
  std::printf("K0S proper decay length: %.4f +- %.4f cm (c tau0 %.4f cm)\n",
              meanL, errL, ctauK0S);
  std::printf("K0S proper decay time: %.4g +- %.2g s (tau0 %.4g s)\n", meanT,
              errL / cLight, ctauK0S / cLight);
  Check(std::abs(meanL - ctauK0S) < 5. * errL, "decay vertices in cm");
  Check(std::abs(meanT - ctauK0S / cLight) < 5. * errL / cLight,
        "production times in s");
  Check(std::abs(decayer.GetLifetime(310) - ctauK0S / cLight) <
            1e-6 * ctauK0S / cLight,
        "GetLifetime in s");
  pd.mayDecay(310, false);

  // EvtGen path (J/psi, Upsilon(1S)): lab-frame momenta, full record, and
  // only stable or long-lived particles as final ones.
  const char* evtgenData = std::getenv("EVTGENDATA");
  if (evtgenData == nullptr) {
    std::printf("EVTGENDATA not set: skipping the EvtGen checks\n");
  } else {
    TEvtGenDecayer evtgen;
    evtgen.SetEvtGenDecayFile(Form("%s/DECAY.DEC", evtgenData));
    evtgen.SetEvtGenParticleFile(Form("%s/evt.pdl", evtgenData));
    evtgen.AddEvtGenParticle(443);
    evtgen.AddEvtGenParticle(553);
    evtgen.Init();
    // EvtGen's own hadronic Upsilon decays (through Pythia8) occasionally
    // lose a particle, so the direct products of the decaying particle do
    // not always add up to it. The record must reproduce EvtGen exactly:
    // every decayed entry equals the sum of its products, and the final
    // particles add up to the direct products of entry 0.
    int nShortLivedFinal = 0, nLongLivedFinal = 0, nUnbalanced = 0;
    const int nPerSample = 500;
    for (int pdg : {443, 553}) {
      for (double pz : {0., 50.}) {
        for (int i = 0; i < nPerSample; i++) {
          const int n = DecayOnce(evtgen, record, pdg, pz);
          Check(n > 2, "EvtGen record has products");
          TLorentzVector finalSum, direct, parent;
          static_cast<TParticle*>(record.At(0))->Momentum(parent);
          for (int j = 0; j < n; j++) {
            auto* part = static_cast<TParticle*>(record.At(j));
            TLorentzVector p4;
            part->Momentum(p4);
            if (part->GetFirstMother() == 0) direct += p4;
            if (part->GetStatusCode() == 0) {
              TLorentzVector products;
              for (int d = part->GetFirstDaughter();
                   d >= 0 && d <= part->GetLastDaughter(); d++) {
                auto* daughter = static_cast<TParticle*>(record.At(d));
                Check(daughter->GetFirstMother() == j,
                      "EvtGen daughters point to their mother");
                TLorentzVector q;
                daughter->Momentum(q);
                products += q;
              }
              if (j > 0) {
                Check(
                    (products - p4).P() < 1e-6 * (1. + p4.E()) &&
                        std::abs(products.E() - p4.E()) < 1e-6 * (1. + p4.E()),
                    "EvtGen decayed entry equals the sum of its products");
              }
              continue;
            }
            finalSum += p4;
            const int id = std::abs(part->GetPdgCode());
            if (pd.tau0(id) > 1e-3) {
              nLongLivedFinal++;
            } else if (pd.canDecay(id)) {
              nShortLivedFinal++;
            }
          }
          Check((finalSum - direct).P() < 1e-6 * (1. + parent.E()) &&
                    std::abs(finalSum.E() - direct.E()) <
                        1e-6 * (1. + parent.E()),
                "EvtGen final particles add up to the direct products");
          // Lab frame: the products carry the momentum of the boosted
          // parent, up to EvtGen's rare unbalanced decays
          if ((finalSum - parent).P() > 1e-6 * (1. + parent.E()) ||
              std::abs(finalSum.E() - parent.E()) > 1e-6 * (1. + parent.E())) {
            nUnbalanced++;
            Check(std::abs(finalSum.E() - parent.E()) < 0.1 * parent.E(),
                  "EvtGen products are in the lab frame");
          }
        }
      }
    }
    std::printf(
        "EvtGen: long-lived final particles %d, short-lived %d, "
        "unbalanced decays %d of %d\n",
        nLongLivedFinal, nShortLivedFinal, nUnbalanced, 4 * nPerSample);
    Check(nLongLivedFinal > 0, "EvtGen hands long-lived products back");
    Check(nShortLivedFinal == 0, "EvtGen decays short-lived products");
    Check(nUnbalanced < 0.01 * 4 * nPerSample,
          "EvtGen decays conserve four-momentum, up to rare exceptions");
  }

  // Seeding: the decays follow gRandom's seed.
  auto channels = [&record](int seed) {
    gRandom->SetSeed(seed);
    TEvtGenDecayer d;
    d.Init();
    std::vector<int> nProducts;
    for (int i = 0; i < 50; i++) {
      nProducts.push_back(DecayOnce(d, record, 411, 0.));
    }
    return nProducts;
  };
  const auto a = channels(1);
  const auto b = channels(1);
  const auto c = channels(2);
  Check(a == b, "same seed gives the same decays");
  Check(a != c, "different seeds give different decays");

  if (failures > 0) {
    std::printf("%d check(s) failed\n", failures);
    return 1;
  }
  std::printf("All checks passed\n");
  return 0;
}
