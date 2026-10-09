// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration
//
// Data-driven J/psi -> mu+ mu- source for 400 GeV/c protons on a thick target.
//
//   production shape : NA50 (Eur. Phys. J. C48 (2006) 329) below y_cm = 0.4,
//                      SHiP Table 5 (arXiv:2604.03661) for 0.4 < y_cm < 2.0,
//                      (1-|xF|)^n above; optionally corrected in (y, p_T) by a
//                      data map read from a file (DataMap, macro/jpsi)
//   absolute scale   : NA50 B_mumu * sigma(J/psi)/A, scaled with A^alpha
//   decay            : two-body, Collins-Soper polar angle 1 + lambda cos^2
//
// Uses ROOT's GenVector and MathCore only (no FairRoot), so the core can be
// unit tested and run standalone; JpsiGenerator wraps it for FairShip.
//
// Normalisation is deterministic: no Monte Carlo enters f_y or the weight.

#ifndef SHIPGEN_JPSISAMPLER_H_
#define SHIPGEN_JPSISAMPLER_H_

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <map>
#include <random>
#include <string>
#include <vector>

#include "Math/Vector4D.h"

namespace jpsi {

// Version of the sampler, stored with every sample (Metadata, FileSummary).
constexpr int kVersionMajor = 1;
constexpr int kVersionMinor = 10;
constexpr const char* kVersion = "1.10";

constexpr double kMJpsi = 3.0969;      // GeV
constexpr double kMMu = 0.1056584;     // GeV
constexpr double kMProton = 0.938272;  // GeV
constexpr double kBrMuMu = 0.05961;    // PDG BR(J/psi -> mu+ mu-)

/// Rapidity model.
///   Gauss : NA50 Gaussian everywhere (hard forward, kept for comparison)
///   Data  : SHiP Table 5 in [dataLo, dataHi], Gaussian below, (1-|xF|)^n
///           above. dataHi = 2.0 uses every table bin.
/// (The values are those stored in the metadata; 1 was a model removed in
/// v1.8.)
enum class YShape { Gauss = 0, Data = 2 };

/// Where the (1-|xF|)^n continuation starts when a data map is used:
///   Table  : above dataHi, after the SHiP Table 5 bins between yHi and dataHi
///   MapEnd : directly at the end of the map (yHi), matched to the map there,
///            with the exponent fitted to the same data (DataMap::tailN)
enum class ForwardTail { Table = 0, MapEnd = 1 };

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

/// One slab of the target for the built-in vertex and rate integral. A gap
/// (helium, air) is a layer with density 0: it takes space but neither absorbs
/// protons nor makes J/psi.
struct Layer {
  TargetSpec material;
  double length_cm = 0.;
};

// clang-format off
/// Read a layer stack from a text file, one entry per line:
///
///     # comment
///     zstart <cm>                             optional: z of the upstream face
///     layer  <name> <A> <density g/cm3> <cm>  a slab (nuclear quantities scaled from NA50 W)
///     gap    <cm>                             empty space
///
/// Throws on a malformed line. zStart is set if the file gives one.
// clang-format on
std::vector<Layer> LoadLayers(const std::string& path,
                              double* zStart = nullptr);

// clang-format off
/// Optional correction of the generator by corrected dimuon data, fitted by
/// macro/jpsi/JpsiDataMap.C (see macro/jpsi/README.md) and read from a file
/// (data_map <file> in a configuration file). With the map on, the rapidity
/// shape is
///
///     y < yHi     NA50 Gaussian x w   (NA50 alone below yJoin = 0.6; its window fixes the rate)
///     yHi - 2.0   SHiP table, scaled to the map level at yHi (the only measurement there)
///     y > 2.0     (1 - |xF|)^n tail
///
/// and the joint (y, pT) density is weighted by
///
///     w(y, pT) = exp(D (b1 + b2 D) + c D (q - q0)),  D = clamp(y - yJoin, 0, yHi - yJoin),
///                                                    q = min(pT^2, qMax)
///
/// b1, b2: the y shape of the data relative to NA50. c: how the pT
/// spectrum changes with y (pz = mT sinh(y + y_beam), so this also fixes the
/// pz-pT correlation). The map base (b1 = b2 = c = 0) is what the fit
/// reweights; the map is valid only on the base configuration it was fitted on
/// (base* fields, checked; < 0 or NaN = not checked).
// clang-format on
struct DataMap {
  bool on = false;
  double yJoin = 0.6;
  double yHi = 1.6;
  double q0 = 1.5;
  double qMax = 16.;
  double b1 = 0.;
  double b2 = 0.;
  double c = 0.;
  /// fit uncertainties of b1, b2, c (information only)
  double eb1 = 0.;
  double eb2 = 0.;
  double ec = 0.;
  double baseMeanPtSq = -1.;
  double basePtSqSlope = NAN;
  double baseLambda = NAN;
  /// exponent of the (1-|xF|)^n continuation fitted to the same data above
  /// the map (JpsiDataMap.C, key tail_n); NaN if the file has none
  double tailN = NAN;
  double eTailN = NAN;
  std::string source;  ///< file it was read from
  std::string text;    ///< content of that file (LoadDataMap), for provenance
};
/// Key-value file written by JpsiDataMap.C. Throws if a required key is
/// missing. Keeps the file content in DataMap::text. If the file has tail_n,
/// ApplyConfigFile ("data_map <file>") also switches the forward continuation
/// to the end of the map with that exponent (see Config::forwardTail).
DataMap LoadDataMap(const std::string& path);
struct Config;
/// Switch the data map m on in cfg, with its fitted forward continuation if
/// it has one (forward_tail map, tailN = m.tailN), as "data_map <file>" does.
void SetDataMap(Config& cfg, const DataMap& m);

inline double DataMapDy(const DataMap& m, double y) {
  return std::min(std::max(y - m.yJoin, 0.), m.yHi - m.yJoin);
}
/// the p_T-independent part (it multiplies the y density)
inline double DataMapYFactor(const DataMap& m, double y) {
  if (!m.on) return 1.;
  const double d = DataMapDy(m, y);
  return std::exp(d * (m.b1 + m.b2 * d));
}
/// the y-p_T correlation part (it reshapes the p_T spectrum at fixed y)
inline double DataMapPtFactor(const DataMap& m, double y, double pt) {
  if (!m.on || m.c == 0.) return 1.;
  const double q = std::min(pt * pt, m.qMax);
  return std::exp(m.c * DataMapDy(m, y) * (q - m.q0));
}
/// The full weight, as JpsiDataMap.C applies it event by event to the base.
inline double DataMapWeight(const DataMap& m, double y, double pt) {
  return DataMapYFactor(m, y) * DataMapPtFactor(m, y, pt);
}

struct Config {
  // ---- beam and target -----------------------------------------------------
  double pBeam = 400.0;  ///< GeV/c
  TargetSpec target = TungstenNA50();
  /// Optional slab model. When given, both the vertex distribution AND the
  /// absolute rate per POT are integrated over it, so mixed Mo/W is consistent.
  std::vector<Layer> layers;
  double zStart_cm = 0.;

  // ---- transverse momentum -------------------------------------------------
  double T = 0.2867;   ///< thermal slope [GeV]
  double p0 = 2.349;   ///< power-law scale [GeV]
  double nPow = 6.0;   ///< power-law exponent
  double fHard = 0.5;  ///< weight of the power-law term, [0,1]
  double ptSq = -1.0;  ///< if > 0, fHard is solved for this <pT^2>
  /// Thick-target secondary production: a MODELLING ASSUMPTION, not a
  /// simulation of secondary interactions. NA50 measured a thin target, so its
  /// rate counts only primary proton-nucleus interactions. The factor scales
  /// the primary yield; the added J/psi get the primary production depth and
  /// kinematics.
  ///
  /// 1.10: the generator with the NA50 normalisation and the Mo/W target
  /// layers, compared with the absolute SHiP values (arXiv:2604.03661; for
  /// 0.3 < y_cm < 0.6, B*sigma/A = 1.18 +- 0.04 +- 0.10 nb/nucleon against
  /// NA50's 0.99 for W), read as |cos theta_CS| < 0.5 like NA50. SHiP sees no
  /// significant enhancement (< 32% at 90% CL). Systematic range 1.0
  /// (thin-target rate) to 1.32. If the SHiP values were for the full
  /// cos theta range, the same comparison would give 0.55.
  double secondaryFactor = 1.10;
  /// Depth variation of the secondary component [cm]. 0: the secondary J/psi
  /// are made where the primary ones are. > 0: their vertex distribution is
  /// the primary one convolved with exp(-dz / secondaryDepth_cm), restricted
  /// to material; the rate is unchanged. Only with a layer model.
  double secondaryDepth_cm = 0.;

  /// Rapidity dependence of the transverse momentum: <pT^2>(y_cm) = ptSq +
  /// ptSqSlope * |y_cm|. 0 = factorised (the NA50 assumption). A negative
  /// slope, as expected from the kinematic limit (NA3 and E866 see <pT^2>
  /// fall with x_F), can be set in a configuration file (pt_sq_slope). Below
  /// the lowest <pT^2> the thermal + power-law mixture reaches, the softer of
  /// the two components is rescaled continuously (power law: p0; thermal: T).
  double ptSqSlope = 0.;
  bool thermalJacobian = true;  ///< dN/dpT ~ pT mT K1 (false: mT K1)
  double ptMax = 10.0;

  // ---- rapidity ------------------------------------------------------------
  YShape yShape = YShape::Data;
  /// dN/dx_F ~ (1 - |xF|)^n above dataHi, fitted to the forward bins of SHiP
  /// Table 5 with this p_T spectrum. The joint (y, p_T) density there is
  /// f(p_T | y) (1 - |xF|)^n |dxF/dy|; both the rapidity density and the p_T
  /// sampled at a given y follow from it.
  double tailN = 5.5;
  double dataLo = 0.4;
  double dataHi = 2.0;
  /// optional 2D correction read from a file; off = SHiP Table 5 as published
  DataMap dataMap;
  /// forward continuation with a data map (ignored without one)
  ForwardTail forwardTail = ForwardTail::Table;
  /// Optional nuclear dependence of the shape against x_F: the y-p_T density
  /// is multiplied by (A_eff / shapeA)^(alphaXf1 xF + alphaXf2 xF^2), where
  /// shapeA is the mass number of the target the shape was measured on and
  /// A_eff the J/psi-weighted mass number of the target model. sigma ~
  /// A^alpha(xF) with alpha falling at large x_F (E866, HERA-B) makes the
  /// forward region of a heavier target softer. NA60 at 400 GeV sees no x_F
  /// dependence for -0.075 < xF < 0.125. Off by default (0, 0).
  double alphaXf1 = 0.;
  double alphaXf2 = 0.;
  double shapeA = 95.95;  ///< 2018 target: 98% of the J/psi made in Mo
  double yGauss0 = -0.2;
  double yGaussSigma = 0.85;

  // ---- decay ---------------------------------------------------------------
  double lambdaPol = 0.0;  ///< CS polar coefficient; also enters f_cos

  // ---- normalisation -------------------------------------------------------
  double nPot = 5e13;         ///< protons this sample stands for
  int64_t nEvents = 1000000;  ///< J/psi to generate
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

  // ---- weight convention ----------------------------------------------------
  /// false: weight = nPot * rate / nEvents, the sample stands for nPot protons
  ///        (standalone ntuples).
  /// true:  physics weight only, weight = rate * potPerEvent per J/psi (divided
  ///        by the mean number injected in injection mode). Every event stands
  ///        for potPerEvent protons; the POT normalisation is applied in the
  ///        analysis, as for minimum bias. nPot is not used, nor the
  ///        enhancement outside injection. FairShip's JpsiGenerator always
  ///        uses true.
  bool physicsWeight = false;

  // ---- bookkeeping ---------------------------------------------------------
  Output output = Output::MuMu;
  std::uint64_t seed = 12345;
  /// Text of every configuration file applied (ApplyConfigFile), stored with
  /// the sample so that a run can be reproduced from its output.
  std::string provenance;
};

/// The production configuration (what FairShip uses by default): NA50 Gaussian
/// below y_cm = 0.4, SHiP Table 5 to 2.0, (1-|xF|)^5.5 tail; <pT^2> = 1.9
/// GeV^2, independent of y; lambda = 0.11 (SHiP, arXiv:2604.03661); secondary
/// factor 1.10; no data map.
/// Physics weights.
Config NominalConfig();

// clang-format off
/// Testing path: override a configuration from a key-value file, one key per
/// line ('#' starts a comment). Each key may appear once and the order of the
/// lines does not matter: data_map is applied first, then map_b1, map_b2,
/// map_c and map_base_check, then the other keys, which are independent of one
/// another (forward_tail and tail override the continuation a map file brings).
/// Throws on an unknown or repeated key, a malformed value, ptsq together with
/// fhard, and map_* without a data map. Keys:
///
///     p_T          ptsq <GeV^2> | fhard <0..1> | pt_sq_slope <GeV^2> | thermal_slope <GeV>
///                  thermal_jacobian <0|1>
///     rapidity     shape data|gauss | tail <n> | data_lo <y> | data_hi <y>
///                  y_gauss <mean> <sigma> | forward_tail table|map
///                  alpha_xf <a1> <a2> [<shape A>]
///     data map     data_map none|base|<file> | map_b1 <v> | map_b2 <v> | map_c <v>
///                  map_base_check <0|1>
///     rate, decay  secondary <f> | secondary_depth <cm> | lambda <v>
///                  output mumu|jpsi|both
///     standalone   target W|Mo | layers <file> | physics_weight <0|1> | n_events <n>
///                  n_pot <v> | seed <n>   (FairShip sets these itself and rejects them)
///
/// "data_map base" is the uncorrected base the map is fitted on. "map_base_check
/// 0" allows the map on a p_T or polarisation variation, which the sampler
/// otherwise refuses. Relative paths (data_map, layers) are taken relative to
/// the directory of the configuration file. The file text is appended to
/// cfg.provenance. If keys is given, the keys found are appended to it.
// clang-format on
void ApplyConfigFile(Config& cfg, const std::string& path,
                     std::vector<std::string>* keys = nullptr);

struct Event {
  double weight = 0.;  ///< nominal weight, identical for every event
  ROOT::Math::PxPyPzEVector jpsi;
  ROOT::Math::PxPyPzEVector mup;  ///< mu+, filled unless Output::Jpsi
  ROOT::Math::PxPyPzEVector mum;  ///< mu-, filled unless Output::Jpsi
  bool hasDimuon = false;
  double cosThetaCS = 0.;
  double yCM = 0.;
  double xF = 0.;
  double z_cm = 0.;
};

/// Normalisation actually used; store this alongside any sample.
struct Normalisation {
  /// fraction inside the NA50 rapidity window
  double fY = 0.;
  /// fraction inside |cos Theta_CS| < 0.5
  double fCos = 0.5;
  /// B*sigma/A extrapolated to full phase space
  double bSigmaFull_nb = 0.;
  double sigmaInel_mb = 0.;
  /// J/psi -> mu mu per interacting proton, secondaries included
  double chiMuMu = 0.;
  /// the NA50 thin-target value, before the secondary factor
  double chiMuMuPrimary = 0.;
  double secondaryFactor = 1.;
  /// inclusive J/psi per interacting proton
  double chiJpsi = 0.;
  /// primary J/psi -> mu mu per POT integrated over the target model, if any
  /// (the rate multiplies it by the secondary factor)
  double probMuMuPerPot = 0.;
  /// probability that a proton interacts in the layer stack
  double pInteract = 0.;
  double targetLength_cm = 0.;
  /// fraction of the J/psi made in each material
  std::vector<std::pair<std::string, double>> materialShare;
  /// what the weight actually uses (see Output)
  double rate = 0.;
  /// nominal weight per generated event
  double weight = 0.;
  double enhancement = 0.;
  /// at y_cm = 0 (the p_T spectrum depends on y when the slope is non-zero)
  double meanPt = 0.;
  double meanPtSq = 0.;
  double fHard = 0.;
  double ptSqSlope = 0.;
  /// rapidity nodes of the p_T model, and those where the requested <pT^2>
  /// is below the mixture's floor, so the softer component was rescaled, or
  /// was clipped (|y| > 1.8)
  int ptNodes = 0;
  int ptNodesSoftened = 0;
  int ptNodesClipped = 0;
  /// lowest <pT^2> the two-component mixture reaches [GeV^2]
  double ptMixtureFloor = 0.;
  /// J/psi-weighted mass number of the target model and the nuclear x_F
  /// factor at y = 1.6, p_T = 1 GeV (1 when the option is off)
  double aEff = 0.;
  double nuclearXfAt16 = 1.;
  /// injection mode only
  double meanPerEvent = 0.;
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
  int64_t NEvents() const { return fNEvents; }
  std::string Summary() const;
  /// key = value lines, for storage as run metadata.
  std::vector<std::pair<std::string, double>> Metadata() const;

  /// unnormalised, for tests
  double YDensity(double y) const;
  /// Joint density d^2N/(dy dp_T) the sampler draws from, on the same scale as
  /// YDensity: its integral over p_T is YDensity(y). For tests and
  /// validation (conditional p_T moments, tail probabilities against y).
  double JointDensity(double y, double pt) const;
  /// exact kinematic limit (J/psi + at least two nucleons)
  double PtMaxAt(double y) const;
  double SqrtS() const { return fSqrtS; }
  double YBeam() const { return fYShift; }

 private:
  void Validate() const;
  void BuildPtGrids();
  double PtSqAt(double y) const;
  void BuildYGrid();
  void Normalise();
  void RecomputeRate();
  double PtMoment(const std::vector<double>& pdf, int k) const;
  double PtCdfAt(double pt, double y) const;
  /// integrated over the local pT spectrum
  double TailDensity(double y) const;
  /// (1 - |xF|)^n |dxF/dy| at (y, pT): the tail's factor on f(p_T | y)
  double TailFactor(double y, double pt) const;
  bool InTail(double y) const { return y >= fTailStart; }
  double SamplePt(double y);
  int PtNode(double y) const;
  double SampleY();
  void DrawKinematics(double& y, double& pt);
  /// p_T at rapidity y, from the conditional of JointDensity
  double DrawPt(double y);
  double SampleCosTheta();
  void Decay(const ROOT::Math::PxPyPzEVector& jpsi, double cosTheta,
             ROOT::Math::PxPyPzEVector& mup, ROOT::Math::PxPyPzEVector& mum);
  double SampleVertex();
  void BuildTargetModel();
  /// J/psi-weighted mass number of the target model (target.A without layers)
  double EffectiveA() const;
  /// the nuclear x_F factor (1 when the option is off)
  double NuclearXfFactor(double y, double pt) const;

  Config fCfg;
  Normalisation fNorm;
  int64_t fNEvents = 0;

  std::mt19937_64 fRng;
  std::uniform_real_distribution<double> fFlat{0., 1.};

  std::vector<double> fPtGrid;
  std::vector<double> fPtThermal;
  std::vector<double> fPtHard;
  // one pT spectrum per rapidity node, so <pT^2> can depend on y
  std::vector<double> fPtNodeY;
  std::vector<std::vector<double>> fPtPdfN;
  std::vector<std::vector<double>> fPtCdfN;
  // integral of the node's p_T density after the data map (1 without)
  std::vector<double> fPtNodeScale;
  std::vector<double> fYGrid;
  std::vector<double> fYPdf;
  std::vector<double> fYCdf;
  // JointDensity = fYJoint(y) * f(p_T | y) [* TailFactor in the tail]
  std::vector<double> fYJoint;
  double fTailStart = HUGE_VAL;  // y where the (1-|xF|)^n tail begins
  double fTailJoint = 0.;
  std::vector<double> fZGrid;
  std::vector<double> fZCdf;

  double fSqrtS = 0.;
  double fYShift = 0.;
};

}  // namespace jpsi

#endif  // SHIPGEN_JPSISAMPLER_H_
