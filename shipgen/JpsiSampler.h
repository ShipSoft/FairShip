// SPDX-License-Identifier: LGPL-3.0-or-later
//
// Data-driven J/psi -> mu+ mu- source for 400 GeV/c protons on a thick target.
//
//   production shape : NA50 (Eur. Phys. J. C48 (2006) 329) + SHiP 2018 testbeam
//                      (CERN-SHiP-ANA-2019-002, Table 2)
//   absolute scale   : NA50 B_mumu * sigma(J/psi)/A, scaled with A^alpha
//   decay            : two-body, Collins-Soper polar angle 1 + lambda cos^2
//
// No ROOT or FairRoot dependency, so the core can be unit tested and reused
// standalone; JpsiGenerator wraps it for FairShip.
//
// Normalisation is deterministic: no Monte Carlo enters f_y or the weight.
 
#ifndef JPSI_JPSISAMPLER_H_
#define JPSI_JPSISAMPLER_H_
 
#include <cstdint>
#include <random>
#include <string>
#include <vector>
 
namespace jpsi {
 
constexpr const char* kVersion = "1.0";
 
constexpr double kMJpsi = 3.0969;      // GeV
constexpr double kMMu = 0.1056584;     // GeV
constexpr double kMProton = 0.938272;  // GeV
constexpr double kBrMuMu = 0.05961;    // PDG BR(J/psi -> mu+ mu-)
constexpr double kAvogadro = 6.02214076e23;
 
/// Rapidity model.
///   Gauss  : NA50 Gaussian everywhere (hard forward, kept for comparison)
///   Hybrid : Gaussian below yMatch, (1-|xF|)^tailN above
///   Data   : SHiP Table 2 in [dataLo, dataHi], Gaussian below, tail above
enum class YShape { Gauss, Hybrid, Data };
 
/// What the sample represents, which also fixes the normalisation:
///   MuMu / Both : every J/psi is decayed, weight uses B_mumu * sigma
///   Jpsi        : inclusive undecayed J/psi, weight uses sigma (1/BR larger)
enum class Output { MuMu, Jpsi, Both };
 
/// Per-nucleon anchor for one target material.
struct TargetSpec {
  double A = 183.84;               ///< mass number
  double lambdaInt_gcm2 = 186.9;   ///< interaction length (NA50 convention)
  double bSigmaWindow_nb = 3.791;  ///< B_mumu*sigma/A inside BOTH NA50 windows
  double alphaA = 0.925;           ///< sigma_Jpsi ~ A^alpha
  double density_gcm3 = 19.3;
  std::string name = "W";
};
 
TargetSpec TungstenNA50();
TargetSpec MolybdenumScaled();
TargetSpec TargetFromA(double A, double density_gcm3, const std::string& name);
 
/// One slab of the target for the built-in vertex and rate integral.
struct Layer {
  TargetSpec material;
  double length_cm = 0.;
};
 
struct Config {
  // ---- beam and target -----------------------------------------------------
  double pBeam = 400.0;  ///< GeV/c
  TargetSpec target = TungstenNA50();
  /// Optional slab model. When given, both the vertex distribution AND the
  /// absolute rate per POT are integrated over it, so mixed Mo/W is consistent.
  std::vector<Layer> layers;
  double zStart_cm = 0.;
  /// Set by JpsiGenerator when the rate integral is done over the FairShip
  /// geometry instead of the slab model. Negative means "not supplied".
  double probMuMuPerPotOverride = -1.0;
 
  // ---- transverse momentum -------------------------------------------------
  double T = 0.2867;            ///< thermal slope [GeV]
  double p0 = 2.349;            ///< power-law scale [GeV]
  double nPow = 6.0;            ///< power-law exponent
  double fHard = 0.5;           ///< weight of the power-law term, [0,1]
  double ptSq = -1.0;           ///< if > 0, fHard is solved for this <pT^2>
  /// Thick-target secondary production. NA50 measured a thin target, so its rate counts
  /// only primary proton-nucleus interactions, while the SHiP shape (and the SHiP target)
  /// include J/psi made by secondaries re-interacting. Comparing our NA50-normalised
  /// generator with the absolute SHiP Table 2 values gives k = 1.10 +- 0.05, i.e. the data
  /// want 10% more than the primary-only rate, consistent with the note's bound of <= 32%
  /// on secondaries. Set to 1.0 to recover the pure thin-target normalisation.
  double secondaryFactor = 1.10;
 
  /// Rapidity dependence of the transverse momentum: <pT^2>(y_cm) = ptSq + ptSqSlope * |y_cm|.
  /// Default from our analysis of the 2018 SHiP dimuon data: -0.36 +- 0.10 GeV^2 per unit
  /// rapidity, stable across selections differing by 40% in yield, and of the sign expected
  /// from the kinematic limit (NA3, E866 see the same in x_F). It is a reconstruction-level
  /// value: the pT acceptance within a rapidity bin is not corrected, which is expected to
  /// steepen it rather than flatten it. Systematic band: 0 (factorised, the NA50 assumption)
  /// to -0.5.
  double ptSqSlope = -0.36;
  bool thermalJacobian = true;  ///< dN/dpT ~ pT mT K1 (false: mT K1)
  double ptMax = 10.0;
 
  // ---- rapidity ------------------------------------------------------------
  YShape yShape = YShape::Data;
  double tailN = 5.5;  ///< refitted to SHiP 2018 with the generated p_T spectrum
  double yMatch = 0.5;
  double dataLo = 0.4;
  double dataHi = 1.8;
  double yGauss0 = -0.2;
  double yGaussSigma = 0.85;
 
  // ---- decay ---------------------------------------------------------------
  double lambdaPol = 0.0;  ///< CS polar coefficient; also enters f_cos
 
  // ---- normalisation -------------------------------------------------------
  double nPot = 5e13;         ///< protons this sample stands for
  long nEvents = 1000000;     ///< J/psi to generate
  double enhancement = -1.0;  ///< if > 0, sets nEvents = E * nPot * rate
 
  // ---- injection into a host production (e.g. Pythia8 minimum bias) --------
  /// When true, J/psi are added to the events of another generator instead of
  /// forming their own sample. Each host event stands for potPerEvent protons;
  /// on average meanPerEvent J/psi are injected per event, each with weight
  ///   w = rate * potPerEvent / meanPerEvent = 1 / enhancement.
  /// Set either enhancement (E = 1: physical rate, weight 1) or meanPerEvent.
  bool injection = false;
  double meanPerEvent = -1.0;
  double potPerEvent = 1.0;
 
  // ---- bookkeeping ---------------------------------------------------------
  Output output = Output::MuMu;
  std::uint64_t seed = 12345;
};
 
struct Vec4 {
  double px = 0, py = 0, pz = 0, E = 0;
  double P() const;
  double Pt() const;
  double Rapidity() const;
};
 
struct Event {
  double weight = 0.;  ///< nominal weight, identical for every event
  Vec4 jpsi;
  Vec4 mup, mum;       ///< filled unless Output::Jpsi
  bool hasDimuon = false;
  double cosThetaCS = 0.;
  double yCM = 0.;
  double xF = 0.;
  double z_cm = 0.;
};
 
/// Normalisation actually used; store this alongside any sample.
struct Normalisation {
  double fY = 0.;             ///< fraction inside the NA50 rapidity window
  double fCos = 0.5;          ///< fraction inside |cos Theta_CS| < 0.5
  double bSigmaFull_nb = 0.;  ///< B*sigma/A extrapolated to full phase space
  double sigmaInel_mb = 0.;
  double chiMuMu = 0.;          ///< J/psi -> mu mu per interacting proton, secondaries included
  double chiMuMuPrimary = 0.;   ///< the NA50 thin-target value, before the secondary factor
  double secondaryFactor = 1.;
  double chiJpsi = 0.;    ///< inclusive J/psi per interacting proton
  double probMuMuPerPot = 0.;  ///< integrated over the target, if modelled
  double rate = 0.;       ///< what the weight actually uses (see Output)
  double weight = 0.;     ///< nominal weight per generated event
  double enhancement = 0.;
  double meanPt = 0., meanPtSq = 0., fHard = 0.;  ///< at y_cm = 0 when the slope is non-zero
  double ptSqSlope = 0.;
  double meanPerEvent = 0.;  ///< injection mode only
  /// Diagnostic only: what chi_mumu would be if the NA50 anchor were quoted
  /// over the full cos Theta_CS range. Never used in the weight.
  double chiMuMuFullCosDiagnostic = 0.;
};
 
/// Fraction of 1 + lambda cos^2 inside |cos| < cut.
double CosAcceptance(double lambda, double cut = 0.5);
 
class Sampler {
 public:
  explicit Sampler(const Config& cfg);
 
  Event Next();
  /// Injection mode: how many J/psi to add to the current host event,
  /// floor(mu) plus one more with probability frac(mu).
  int NumberToInject();
 
  const Config& GetConfig() const { return fCfg; }
  const Normalisation& GetNormalisation() const { return fNorm; }
  long NEvents() const { return fNEvents; }
  std::string Summary() const;
  /// key = value lines, for storage as run metadata.
  std::vector<std::pair<std::string, double>> Metadata() const;
 
  /// Uniform deviate from the sampler's own stream. JpsiGenerator uses it for
  /// vertex and beam smearing so that one seed controls the whole generator.
  double Uniform() { return fFlat(fRng); }
 
  /// Supply the J/psi -> mu mu probability per POT integrated over the real
  /// geometry (JpsiGenerator does this after its material scan). The weight,
  /// the enhancement and nEvents are recomputed consistently.
  void SetProbMuMuPerPot(double p);
  /// Full-phase-space B*sigma(J/psi) for one nucleus, in cm^2, with the NA50
  /// tungsten anchor and A^alpha scaling. Used by external geometry scans.
  double BSigmaFullForA(double A) const;
 
  double YDensity(double y) const;   ///< unnormalised, for tests
  double PtMaxAt(double y) const;    ///< kinematic limit |x_F| < 1
  double SqrtS() const { return fSqrtS; }
  double YBeam() const { return fYShift; }
 
 private:
  void Validate() const;
  void BuildPtGrids();
  double PtSqAt(double y) const;
  void BuildYGrid();
  void Normalise();
  void RecomputeRate();
  double SolveFHard(double ptSq) const;
  double PtMoment(const std::vector<double>& pdf, int k) const;
  double PtCdfAt(double pt, double y) const;
  double TailDensity(double y) const;  ///< integrated over the local pT spectrum
  double SamplePt(double y);
  int PtNode(double y) const;
  double SampleY();
  void DrawKinematics(double& y, double& pt);
  double SampleCosTheta();
  void Decay(const Vec4& jpsi, double cosTheta, Vec4& mup, Vec4& mum);
  double SampleVertex();
  void BuildTargetModel();
 
  Config fCfg;
  Normalisation fNorm;
  long fNEvents = 0;
 
  std::mt19937_64 fRng;
  std::uniform_real_distribution<double> fFlat{0., 1.};
 
  std::vector<double> fPtGrid, fPtThermal, fPtHard;
  // one pT spectrum per rapidity node, so <pT^2> can depend on y
  std::vector<double> fPtNodeY;
  std::vector<std::vector<double>> fPtPdfN, fPtCdfN;
  std::vector<double> fYGrid, fYPdf, fYCdf, fYValid;
  std::vector<double> fZGrid, fZCdf;
 
  double fSqrtS = 0., fYShift = 0.;
};
 
}  // namespace jpsi
 
#endif  // JPSI_JPSISAMPLER_H_
 

