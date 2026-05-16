#ifndef SHIPGEN_PARTICLEGUNGENERATOR_H_
#define SHIPGEN_PARTICLEGUNGENERATOR_H_

#include <Rtypes.h>  // for Double32_t, Bool_t, kTRUE, etc

#include "Generator.h"
#include "TH1.h"

class FairPrimaryGenerator;
struct ParticleGunParticle;

enum class SmearMode { kExponential, kGaussian, kUniform };

class ParticleGunGenerator : public SHiP::Generator {
 public:
  /** Default constructor. **/
  ParticleGunGenerator();

  /** Constructor with PDG-ID, multiplicity
   **@param pdgid Particle type (PDG encoding)
   **@param mult  Multiplicity (default is 1)
   **/
  explicit ParticleGunGenerator(Int_t pdgid, Int_t mult = 1);

  /** Destructor **/
  ~ParticleGunGenerator() override;

  /** Modifiers **/

  void SetPRange(Double32_t pmin = 0, Double32_t pmax = 10) {
    fPMin = pmin;
    fPMax = pmax;
    fPRangeIsSet = kTRUE;
  }

  void SetPtRange(Double32_t ptmin = 0, Double32_t ptmax = 10) {
    fPtMin = ptmin;
    fPtMax = ptmax;
    fPtRangeIsSet = kTRUE;
  }

  void SetEkinRange(Double32_t kmin = 0, Double32_t kmax = 10) {
    fEkinMin = kmin;
    fEkinMax = kmax;
    fEkinRangeIsSet = kTRUE;
  }

  void SetPhiRange(Double32_t phimin = 0, Double32_t phimax = 360) {
    fPhiMin = phimin;
    fPhiMax = phimax;
  }

  void SetEtaRange(Double32_t etamin = -5, Double32_t etamax = 7) {
    fEtaMin = etamin;
    fEtaMax = etamax;
    fEtaRangeIsSet = kTRUE;
  }

  void SetYRange(Double32_t ymin = -5, Double32_t ymax = 7) {
    fYMin = ymin;
    fYMax = ymax;
    fYRangeIsSet = kTRUE;
  }

  void SetThetaRange(Double32_t thetamin = 0, Double32_t thetamax = 90) {
    fThetaMin = thetamin;
    fThetaMax = thetamax;
    fThetaRangeIsSet = kTRUE;
  }

  void SetCosTheta() { fCosThetaIsSet = kTRUE; }

  void SetXYZ(Double32_t x = 0, Double32_t y = 0, Double32_t z = 0);

  void SetVertex(Double32_t x = 0, Double32_t y = 0, Double32_t z = 0,
                 Double32_t ex = 0, Double32_t ey = 0, Double32_t ez = 0);

  void SetBoxXYZ(Double32_t x1 = 0, Double32_t y1 = 0, Double32_t x2 = 0,
                 Double32_t y2 = 0, Double32_t z = 0);

  void SetBothCharges(bool flag, Double32_t fraction = 0.5);

  void SetPDGType(int pdgid) { m_pdgid = pdgid; };
  void SetMultiplicity(int mult) { m_mult = mult; };
  int GetPDGType();
  int GetMultiplicity() { return m_mult; };

  void LoadHistoFromFile(const std::string& inFile, const std::string& inHisto,
                         std::vector<std::string> varNames);

  Double32_t GetPDGMass() { return fPDGMass; };

  /**
   * not used, for backward compatibility, please user FairLogger to set debug
   * mode
   * @param
   */
  void SetDebug(Bool_t /*debug*/) {}
  /** Initializer **/

  using SHiP::Generator::Init;
  Bool_t Init() override;
  Bool_t Init(const char* inFile) override { return Init(inFile, 0); };

  Bool_t Init(const char* inFile, int startEvent) override {
    LOG(warning) << "Init with files not implemented for ParticleGunGenerator. "
                    "Using default Init() instead";
    return Init();
  };
  /** Creates an event with given type and multiplicity.
   **@param primGen  pointer to the FairPrimaryGenerator
   **/
  Bool_t ReadEvent(FairPrimaryGenerator* primGen) override;

  /** Clone this object (used in MT mode only) */
  virtual FairGenerator* CloneGenerator() const;

  void SetSmearMode(const std::string& mode);

 protected:
  /** Copy constructor. **/
  ParticleGunGenerator(const ParticleGunGenerator&) = default;
  ParticleGunGenerator& operator=(const ParticleGunGenerator&) = default;

 private:
  SmearMode fSmearMode{SmearMode::kExponential};

  static Double32_t SmearVertex(Double_t centre, Double_t spread,
                                SmearMode mode);

  ParticleGunParticle GenerateKinematics();
  void OverrideFromHistogram(ParticleGunParticle& p);
  Double32_t& GetVar(ParticleGunParticle& p, const std::string& name);
  void SetVar(ParticleGunParticle& p, const std::string& name,
              Double32_t value);

  Double32_t fPtMin{0}, fPtMax{0};    // Transverse momentum range [GeV]
  Double32_t fPhiMin{0}, fPhiMax{0};  // Azimuth angle range [degree]
  Double32_t fEtaMin{0}, fEtaMax{0};  // Pseudorapidity range in lab system
  Double32_t fYMin{0}, fYMax{0};      // Rapidity range in lab system
  Double32_t fPMin{0}, fPMax{0};      // Momentum range in lab system
  Double32_t fThetaMin{0},
      fThetaMax{0};  // Polar angle range in lab system [degree]
  Double32_t fEkinMin{0},
      fEkinMax{0};  // Kinetic Energy range in lab system [GeV]
  Double32_t fVx{0}, fVy{0}, fVz{0};
  Double32_t fVex{0}, fVey{0}, fVez{0};
  Double32_t fPDGMass{0};

  bool m_bothCharges = false;
  Double32_t m_chargeFraction = 1.;

  std::shared_ptr<TH1> fDistHist;  // Some histogram with the variables you want
                                   // to generate from. Can be up to 3D.
  std::vector<std::string> fHistoVars;
  int fDistHistDims = -1;

  Bool_t fEtaRangeIsSet = false;    // True if eta range is set
  Bool_t fYRangeIsSet = false;      // True if rapidity range is set
  Bool_t fThetaRangeIsSet = false;  // True if theta range is set
  Bool_t fCosThetaIsSet = false;    // True if uniform distribution in
  // cos(theta) is set (default -> not set)
  Bool_t fPtRangeIsSet = false;    // True if transverse momentum range is set
  Bool_t fPRangeIsSet = false;     // True if abs.momentum range is set
  Bool_t fEkinRangeIsSet = false;  // True if kinetic energy range is set

  int m_mult{1};
  int m_pdgid{0};
};

#endif  // SHIPGEN_PARTICLEGUNGENERATOR_H_
