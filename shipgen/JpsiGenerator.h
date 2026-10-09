// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration
//
// FairShip front end for the data-driven J/psi -> mu mu source (JpsiSampler):
// NA50 normalisation, rapidity shape from NA50 and SHiP Table 5
// (arXiv:2604.03661), optionally corrected by a data map read from a file.
// All physics lives in JpsiSampler; this class
// turns the target in the geometry into the sampler's layer model, makes the
// AddTrack calls and handles the configuration.
//
// Configuration: the nominal generator is built in (jpsi::NominalConfig). For
// tests and systematic variations, SetConfigFile() overrides it from a
// key-value file (keys in JpsiSampler.h, ApplyConfigFile). Keys that FairShip
// sets itself (seed, n_events, n_pot, physics_weight, target, layers) are
// rejected there.
//
// Target: the materials along the beam line between the target coordinates
// become layers of the sampler's target model, which gives the vertex
// distribution and the J/psi -> mu mu probability per POT. The proton
// absorption uses the NA50 convention (sigma_inel ~ A^0.71 anchored on NA50
// tungsten), so a thick target gives chi_mumu per interacting proton as NA50
// measured it. The geometry's own interaction lengths (TGeoMaterial, the
// Geant4 formula 35 A^(1/3) g/cm^2) are listed in Summary() with the rate they
// would give.
//
// Weights are physics weights only: every event stands for one POT (as a
// minimum-bias event does), and each J/psi carries
//   standalone: w = P(J/psi -> mu mu) per POT           (one J/psi per event)
//   injected  : w = P(J/psi -> mu mu) per POT / mu      (mu J/psi per event)
// (inclusive "jpsi" output: P(J/psi) per POT). The number of POT is applied in
// the analysis: N_expected = N_POT / N_events * sum of weights.
//
// With FairShip splitting, ShipStack::PushTrack multiplies a daughter weight
// by its parent's, so the truth-level J/psi is pushed with weight 1 and the
// transported muons carry w. In "jpsi" output the J/psi itself is transported
// and carries w.
//
// Injection is an independent weighted overlay: it preserves the mean J/psi
// yield per POT, but the injected J/psi is not part of the host collision (no
// energy-momentum balance with it, no correlation with the other particles of
// the minimum-bias event). Studies of coincidences or vetoes that depend on
// such correlations need a different approach.
//
// The veto in the host (FixedTargetGenerator::SetVetoJpsi) removes Pythia8's
// J/psi and everything descending from them, so J/psi from chi_c and psi(2S)
// decays are replaced too: the data-driven rate is inclusive, feed-down
// included. Direct psi(2S) -> mu mu and the Upsilon states are not vetoed.
// Pythia8 makes them through the same charmonium and bottomonium channels in
// its multiparton interactions, and overestimates them in the same way, but
// psi(2S) -> mu mu is only about 1-2% of the J/psi -> mu mu yield (NA50).
// Dedicated productions can remove onia from the multiparton interactions
// altogether with MultipartonInteractions:processLevel = 2 in the Pythia8
// configuration, which leaves open charm and beauty unchanged.
//
// Like the other shipgen generators, the class has no ClassDef and its LinkDef
// entry uses "-"; Init() and ReadEvent() are defined in the .cxx so that the
// type information is emitted there.

#ifndef SHIPGEN_JPSIGENERATOR_H_
#define SHIPGEN_JPSIGENERATOR_H_

#include <memory>
#include <string>
#include <utility>
#include <vector>

#include "Generator.h"
#include "JpsiSampler.h"
#include "TString.h"

class FairPrimaryGenerator;

class JpsiGenerator : public SHiP::Generator {
 public:
  JpsiGenerator() = default;
  ~JpsiGenerator() override;

  Bool_t Init() override;
  Bool_t Init(const char*) override { return Init(); }
  Bool_t Init(const char*, int) override { return Init(); }
  using SHiP::Generator::Init;

  Bool_t ReadEvent(FairPrimaryGenerator*) override;

  // ---- configuration
  // ---------------------------------------------------------
  /// Override the nominal configuration from a key-value file (testing path).
  /// Call it first: the setters below act on top of it.
  void SetConfigFile(const TString& path);
  void SetMom(Double_t p) { fCfg.pBeam = p; }
  /// "mumu" (default) or "jpsi" (inclusive, undecayed and transported).
  void SetOutputMode(const TString& mode);
  /// Seeds the sampler (kinematics, decay, vertex). The beam offset uses the
  /// FairShip beam utility and hence gRandom, seeded by the run macro.
  void SetSeed(ULong64_t s) { fCfg.seed = s; }

  // ---- statistics
  // --------------------------------------------------------------
  /// Standalone sample: number of events (one J/psi each).
  void SetNEvents(Long_t n) { fCfg.nEvents = n; }
  /// Injection into the events of a host generator (FixedTargetGenerator):
  /// mu J/psi per event on average, weight rate/mu. Either the mean number
  /// (SetMeanPerEvent) or the enhancement over the physical rate
  /// (SetEnhancement, 1 = physical, then mu = rate and the weight is 1).
  void SetInjection(Bool_t on = kTRUE) { fCfg.injection = on; }
  void SetMeanPerEvent(Double_t mu) { fCfg.meanPerEvent = mu; }
  void SetEnhancement(Double_t e) { fCfg.enhancement = e; }
  /// POT each host event stands for; 1 for FixedTargetGenerator minimum bias.
  void SetPotPerEvent(Double_t p) { fCfg.potPerEvent = p; }

  // ---- target
  // ----------------------------------------------------------------
  /// Take the target from the geometry along the line (x, y) between z0 and
  /// z1. Typically z0 = ship_geo.target.z0, z1 = z0 + ship_geo.target.length.
  /// Required: Init() fails without it.
  void SetTargetCoordinates(Double_t z0_cm, Double_t z1_cm, Double_t x_cm = 0,
                            Double_t y_cm = 0);
  /// Number of steps of the scan along the beam line (default 4000).
  void SetScanSteps(Int_t n) { fScanSteps = n; }
  /// Beam profile, same convention and defaults as FixedTargetGenerator.
  void SetSmearBeam(Double_t sigma_cm) { fSmearBeam = sigma_cm; }
  void SetPaintRadius(Double_t r_cm) { fPaintBeam = r_cm; }

  // ---- results (valid after run.Init())
  // -----------------------------------------
  /// J/psi -> mu mu per POT over the target, secondary factor included
  Double_t ProbMuMuPerPot() const;
  /// weight per J/psi
  Double_t EventWeight() const;
  /// injection only
  Double_t MeanPerEvent() const;
  Long_t NEventsToGenerate() const;
  /// path of the configuration file, empty for the nominal configuration
  std::string ConfigFile() const { return fConfigFile; }
  /// text of the configuration file and of a data-map file read through it
  std::string ConfigText() const;
  std::string Version() const { return jpsi::kVersion; }
  std::string Summary() const;
  std::vector<std::pair<std::string, double>> Metadata() const;

 private:
  /// One stretch of the same material along the beam line.
  struct ScanLayer {
    std::string name;
    Double_t A = 0;        // g/mol
    Double_t density = 0;  // g/cm3
    Double_t length = 0;   // cm
    Double_t intLen = 0;   // cm
  };
  Bool_t ScanGeometry();
  std::string ScanSummary() const;
  /// Push one J/psi (and its muons); returns the number of tracks added.
  Int_t PushJpsi(FairPrimaryGenerator* cpg, const jpsi::Event& ev,
                 Int_t firstIndex);

  jpsi::Config fCfg = jpsi::NominalConfig();
  std::unique_ptr<jpsi::Sampler> fSampler;
  std::string fConfigFile;

  Bool_t fUseGeometry = kFALSE;
  Double_t fZ0 = 0;
  Double_t fZ1 = 0;
  Double_t fXoff = 0;
  Double_t fYoff = 0;
  Int_t fScanSteps = 4000;
  Double_t fSmearBeam = 0.8;  // cm, FixedTargetGenerator default
  Double_t fPaintBeam = 5.0;  // cm, FixedTargetGenerator default
  std::vector<ScanLayer> fScan;
};

#endif  // SHIPGEN_JPSIGENERATOR_H_
