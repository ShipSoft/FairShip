// SPDX-License-Identifier: LGPL-3.0-or-later
//
// FairShip front end for the data-driven J/psi source. All physics lives in
// JpsiSampler; this class handles the geometry scan (vertex distribution and
// absolute rate), the AddTrack calls and the configuration setters.
//
// Like the other shipgen generators, the class has no ClassDef: the LinkDef
// entry (with "-") provides interpreter and Python access, and a generator is
// never written to file, so no streamer is needed.
//
// Weight convention, important with FairShip splitting enabled:
// ShipStack::PushTrack multiplies a daughter weight by its parent's, so the
// truth-level J/psi mother is pushed with weight 1 and the transported muons
// carry the physical event weight. In Output::Jpsi the J/psi itself is the
// transported particle and carries the inclusive weight.

#ifndef SHIPGEN_JPSIGENERATOR_H_
#define SHIPGEN_JPSIGENERATOR_H_

#include <memory>
#include <string>
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

  // ---- beam, target, normalisation ----------------------------------------
  void SetMom(Double_t p) { fCfg.pBeam = p; }
  /// Per-nucleon anchor when no geometry scan is used: "W" or "Mo", or (A, rho).
  void SetTargetMaterial(const TString& name);
  void SetTargetMaterial(Double_t A, Double_t density_gcm3,
                         const TString& name = "custom");
  void SetPot(Double_t nPot) { fCfg.nPot = nPot; }
  void SetNEvents(Long_t n) {
    fCfg.nEvents = n;
    fCfg.enhancement = -1;
  }
  /// Enhancement over the physical rate: 1 = realistic (weight 1 per event),
  /// 1e3 = a thousand times more J/psi at weight 1e-3. Overrides SetNEvents;
  /// read back the count with NEventsToGenerate().
  void SetEnhancement(Double_t e) { fCfg.enhancement = e; }

  // ---- injection into a host production -----------------------------------
  /// Add J/psi to the events of another generator (e.g. FixedTargetGenerator)
  /// instead of producing a standalone sample. The host run's event count sets
  /// the statistics; SetEnhancement(E) or SetMeanPerEvent(mu) sets the J/psi
  /// content, with weight 1/E per J/psi. E = 1 is the physical rate.
  void SetInjection(Bool_t on = kTRUE) { fCfg.injection = on; }
  void SetMeanPerEvent(Double_t mu) { fCfg.meanPerEvent = mu; }
  /// Protons each host event stands for; 1 for FixedTargetGenerator minbias.
  void SetPotPerEvent(Double_t p) { fCfg.potPerEvent = p; }

  // ---- kinematics knobs ----------------------------------------------------
  void SetRapidityShape(const TString& shape);  ///< "data", "hybrid", "gauss"
  void SetForwardTail(Double_t n) { fCfg.tailN = n; }
  void SetYMatch(Double_t y) { fCfg.yMatch = y; }
  void SetDataRange(Double_t lo, Double_t hi) {
    fCfg.dataLo = lo;
    fCfg.dataHi = hi;
  }
  void SetGaussian(Double_t mean, Double_t sigma) {
    fCfg.yGauss0 = mean;
    fCfg.yGaussSigma = sigma;
  }
  void SetPtSq(Double_t ptSq) { fCfg.ptSq = ptSq; }
  void SetFHard(Double_t f) {
    fCfg.fHard = f;
    fCfg.ptSq = -1;
  }
  void SetThermalSlope(Double_t T) { fCfg.T = T; }
  void SetThermalJacobian(Bool_t on) { fCfg.thermalJacobian = on; }
  /// Collins-Soper polar coefficient. Feeds both the decay angles and the
  /// acceptance factor in the normalisation.
  void SetPolarisation(Double_t lambda) { fCfg.lambdaPol = lambda; }
  /// Seeds the sampler (kinematics, decay, vertex). The beam offset uses the
  /// FairShip beam utility and hence gRandom, which the run macro seeds with
  /// the same --seed.
  void SetSeed(ULong64_t s) { fCfg.seed = s; }

  // ---- output --------------------------------------------------------------
  /// "mumu" (default), "jpsi" (inclusive, undecayed) or "both".
  void SetOutputMode(const TString& mode);

  // ---- vertex and absolute rate over the geometry --------------------------
  /// Scan the FairShip geometry between two z positions along (x, y) and use it
  /// for both the vertex distribution and the J/psi -> mu mu rate per POT.
  /// Typically z0 = ship_geo.target.z0, z1 = z0 + ship_geo.target.length.
  void SetTargetCoordinates(Double_t z0_cm, Double_t z1_cm, Double_t x_cm = 0,
                            Double_t y_cm = 0);
  void SetScanSteps(Int_t n) { fScanSteps = n; }
  /// Alternative to the geometry scan: an explicit slab stack.
  void AddLayer(const TString& material, Double_t length_cm);
  void SetZStart(Double_t z_cm) { fCfg.zStart_cm = z_cm; }
  /// Beam profile, same convention and defaults as FixedTargetGenerator:
  /// Gaussian sigma plus uniform painting radius, via CalculateBeamOffset.
  void SetSmearBeam(Double_t sigma_cm) { fSmearBeam = sigma_cm; }
  void SetPaintRadius(Double_t r_cm) { fPaintBeam = r_cm; }

  // ---- results and metadata ------------------------------------------------
  Double_t ChiMuMu() const;
  Double_t ProbMuMuPerPot() const;
  Double_t EventWeight() const;
  Double_t MeanPerEvent() const;
  Long_t NEventsToGenerate() const;
  std::string Summary() const;
  std::vector<std::pair<std::string, double>> Metadata() const;

 private:
  Bool_t ScanGeometry();
  Double_t SampleZ();
  /// Push one J/psi (and its muons); returns the number of tracks added.
  Int_t PushJpsi(FairPrimaryGenerator* cpg, const jpsi::Event& ev,
                 Int_t firstIndex);

  jpsi::Config fCfg;
  std::unique_ptr<jpsi::Sampler> fSampler;

  Bool_t fUseGeometry = kFALSE;
  Double_t fZ0 = 0, fZ1 = 0, fXoff = 0, fYoff = 0;
  Int_t fScanSteps = 4000;
  Double_t fSmearBeam = 0.8;  // cm, FixedTargetGenerator default
  Double_t fPaintBeam = 5.0;  // cm, FixedTargetGenerator default
  std::vector<Double_t> fZGrid;
  std::vector<Double_t> fZCdf;
};

#endif  // SHIPGEN_JPSIGENERATOR_H_
