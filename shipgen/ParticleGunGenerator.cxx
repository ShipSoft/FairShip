
#include "ParticleGunGenerator.h"

#include <TDatabasePDG.h>
#include <TMath.h>
#include <TNamed.h>
#include <TParticlePDG.h>
#include <TRandom.h>

#include <cmath>   // for cos, acos
#include <cstdio>  // for printf
#include <stdexcept>

#include "FairLogger.h"
#include "FairPrimaryGenerator.h"
#include "TFile.h"
#include "TH2.h"
#include "TH3.h"

// Function-local static maps so std::map's allocations happen lazily on
// first use rather than during dynamic initialisation, where the bad_alloc
// would propagate out as an uncatchable exception
// (bugprone-throwing-static-initialization).
static const std::map<std::string, ModelSpec>& kVertexModels() {
  static const std::map<std::string, ModelSpec> models = {
      {"gaussian",
       {5, "Gaus(X), Gaus(Y), Point(Z)",
        [](ParticleGunParticle& p, const std::vector<Double32_t>& pars) {
          p.X = (pars[1] > 0) ? gRandom->Gaus(pars[0], pars[1]) : pars[0];
          p.Y = (pars[3] > 0) ? gRandom->Gaus(pars[2], pars[3]) : pars[2];
          p.Z = pars[4];
        }}},
      {"exponential",
       {5, "Exp(X), Exp(Y), Point(Z)",
        [](ParticleGunParticle& p, const std::vector<Double32_t>& pars) {
          p.X =
              (gRandom->Uniform() > 0.5)
                  ? gRandom->Exp(pars[1]) + pars[0]
                  : -gRandom->Exp(pars[1]) +
                        pars[0];  // Make this symmetric about a specified point
          p.Y = (gRandom->Uniform() > 0.5) ? gRandom->Exp(pars[3]) + pars[2]
                                           : -gRandom->Exp(pars[3]) + pars[2];
          p.Z = pars[4];
        }}},
      {"uniform",
       {5, "Uniform(X), Uniform(Y), Point(Z)",
        [](ParticleGunParticle& p, const std::vector<Double32_t>& pars) {
          p.X = (pars[1] > 0) ? gRandom->Uniform(pars[0] - pars[1] / 2.,
                                                 pars[0] + pars[1] / 2.)
                              : pars[1];
          p.Y = (pars[3] > 0) ? gRandom->Uniform(pars[2] - pars[3] / 2.,
                                                 pars[2] + pars[3] / 2.)
                              : pars[2];
          p.Z = pars[4];
        }}},
  };
  return models;
}

static const std::map<int, ModelSpec>& kMomentumModels() {
  static const std::map<int, ModelSpec> models = {
      {1,
       {6, "Gaus(Px), Gaus(Py), Landau(Pz)",
        [](ParticleGunParticle& p, const std::vector<Double32_t>& pars) {
          p.Px = (pars[1] > 0) ? gRandom->Gaus(pars[0], pars[1]) : pars[0];
          p.Py = (pars[3] > 0) ? gRandom->Gaus(pars[2], pars[3]) : pars[2];
          p.Pz = (pars[5] > 0) ? gRandom->Landau(pars[4], pars[5]) : pars[4];
        }}},
  };
  return models;
}

ParticleGunGenerator::ParticleGunGenerator() : SHiP::Generator() {
  SetPhiRange();
}

ParticleGunGenerator::ParticleGunGenerator(Int_t pdgid, Int_t mult)
    : SHiP::Generator() {
  // Constructor. Set default kinematics limits
  SetPDGType(pdgid);
  SetMultiplicity(mult);
  SetPhiRange();
}

ParticleGunGenerator::~ParticleGunGenerator() = default;

void ParticleGunGenerator::LoadHistoFromFile(
    const std::string& inFile, const std::string& inHisto,
    std::vector<std::string> varNames) {
  TFile* loadFile = TFile::Open(inFile.c_str(), "READ");
  if (!loadFile) {
    delete loadFile;
    LOG(fatal) << "ParticleGunGenerator: Cannot open file " << inFile;
    throw std::runtime_error("ParticleGunGenerator: Cannot open file " +
                             inFile);
  }

  auto* raw = dynamic_cast<TH1*>(loadFile->Get(inHisto.c_str()));
  if (!raw) {
    loadFile->Close();
    delete loadFile;
    LOG(fatal) << "ParticleGunGenerator: Histogram " << inHisto
               << " not found in file " << inFile;
    throw std::runtime_error("ParticleGunGenerator: Histogram " + inHisto +
                             " not found in file " + inFile);
  }
  raw = static_cast<TH1*>(raw->Clone());
  raw->SetDirectory(nullptr);  // detach from ROOT's directory ownership
  loadFile->Close();
  delete loadFile;

  const int dims = raw->GetDimension();
  if (static_cast<int>(varNames.size()) != dims) {
    LOG(fatal) << "ParticleGunGenerator: " << varNames.size()
               << " variables given for a " << dims << "-D histogram";
    throw std::runtime_error(
        "ParticleGunGenerator: " + std::to_string(varNames.size()) +
        " variables given for a " + std::to_string(dims) + "-D histogram");
  } else {
    ParticleGunParticle probe;
    for (const auto& name : varNames) {
      static_cast<void>(GetVar(probe, name));
    }
  }

  // Check for variable name conflicts with already-loaded histograms
  for (const auto& name : varNames) {
    for (const auto& entry : fHistoEntries) {
      for (const auto& existing : entry.varNames) {
        if (existing == name) {
          LOG(fatal)
              << "ParticleGunGenerator: variable \"" << name
              << "\" is already controlled by a previously loaded histogram";
          throw std::runtime_error(
              "ParticleGunGenerator: variable \"" + name +
              "\" is already controlled by a previously loaded histogram");
        }
      }
    }
  }

  fHistoEntries.push_back(
      {std::shared_ptr<TH1>(raw), dims, std::move(varNames)});

  LOG(info) << "ParticleGunGenerator: loaded " << dims << "-D histogram \""
            << inHisto << "\" from " << inFile << " (" << fHistoEntries.size()
            << " total)";
}

Bool_t ParticleGunGenerator::Init() {
  const auto& vertexSpec = kVertexModels().at(fVertexModel);

  if (static_cast<int>(fVertexPars.size()) != vertexSpec.expectedPars) {
    throw std::runtime_error(
        "ParticleGunGenerator: vertex model " + fVertexModel + " requires " +
        std::to_string(vertexSpec.expectedPars) + " parameters, got " +
        std::to_string(fVertexPars.size()));
  }

  // Check for particle type
  TDatabasePDG* pdgBase = TDatabasePDG::Instance();
  TParticlePDG* particle = pdgBase->GetParticle(m_pdgid);

  if (!particle) {
    LOG(fatal) << "ParticleGunGenerator: PDG " << m_pdgid << " not defined";
    return kFALSE;
  }
  LOG(info) << this->ClassName() << ": particle with PDG =" << m_pdgid
            << " Found";
  fPDGMass = particle->Mass();

  if (fPhiMax - fPhiMin > 360) {
    LOG(fatal) << "ParticleGunGenerator:Init(): phi range is too wide: "
               << fPhiMin << "<phi<" << fPhiMax;
    return kFALSE;
  }
  if (fEkinRangeIsSet) {
    if (fPRangeIsSet) {
      LOG(fatal) << "ParticleGunGenerator:Init(): Cannot set P and Ekin ranges "
                    "simultaneously";
      return kFALSE;
    } else {
      fPMin = TMath::Sqrt(fEkinMin * (fEkinMin + 2 * fPDGMass));
      fPMax = TMath::Sqrt(fEkinMax * (fEkinMax + 2 * fPDGMass));
      fPRangeIsSet = kTRUE;
      fEkinRangeIsSet = kFALSE;
    }
  }
  if (fPRangeIsSet && fPtRangeIsSet) {
    LOG(fatal) << "ParticleGunGenerator:Init():  Cannot set P and Pt ranges "
                  "simultaneously";
    return kFALSE;
  }
  if (fPRangeIsSet && fYRangeIsSet) {
    LOG(fatal) << "ParticleGunGenerator:Init():  Cannot set P and Y ranges "
                  "simultaneously";
    return kFALSE;
  }
  if ((fThetaRangeIsSet && fYRangeIsSet) ||
      (fThetaRangeIsSet && fEtaRangeIsSet) ||
      (fYRangeIsSet && fEtaRangeIsSet)) {
    LOG(fatal) << "ParticleGunGenerator:Init():  Cannot set Y, Theta or Eta "
                  "ranges simultaneously";
    return kFALSE;
  }
  return kTRUE;
}

void ParticleGunGenerator::SetBothCharges(bool flag, Double32_t fraction) {
  if (flag && (!std::isfinite(fraction) || fraction < 0. || fraction > 1.)) {
    LOG(fatal)
        << "ParticleGunGenerator: charge fraction must be finite and in [0, 1]";
    throw std::runtime_error(
        "ParticleGunGenerator: charge fraction must be finite and in [0, 1]");
  }
  m_bothCharges = flag;
  m_chargeFraction = flag ? fraction : 1.;
  if (m_bothCharges) {
    // Check for particle type
    TDatabasePDG* pdgBase = TDatabasePDG::Instance();
    TParticlePDG* particle = pdgBase->GetParticle(-m_pdgid);
    if (!particle) {
      LOG(warning) << "ParticleGunGenerator: PDG " << -m_pdgid
                   << " not defined. Only generating " << m_pdgid;
      m_bothCharges = false;
      m_chargeFraction = 1.;
    } else
      LOG(info)
          << "ParticleGunGenerator: Setting to generate both charges, with "
             "fraction of "
          << m_pdgid << " set to " << m_chargeFraction;
  } else
    LOG(info) << "ParticleGunGenerator: Setting to only generate one charge "
                 "for PDG id"
              << m_pdgid;
}

int ParticleGunGenerator::GenPDGType() const {
  if (m_bothCharges) {
    float tPDG = gRandom->Uniform();
    return (tPDG > m_chargeFraction) ? -m_pdgid : m_pdgid;
  } else
    return m_pdgid;
}

Bool_t ParticleGunGenerator::ReadEvent(FairPrimaryGenerator* primGen) {
  int pdg_type;
  for (Int_t k = 0; k < GetMultiplicity(); k++) {
    pdg_type = GenPDGType();
    ParticleGunParticle p = GenerateKinematics();
    OverrideFromHistogram(p);
    primGen->AddTrack(pdg_type, p.Px, p.Py, p.Pz, p.X, p.Y, p.Z);
  }
  return kTRUE;
}

ParticleGunParticle ParticleGunGenerator::GenerateKinematics() {
  ParticleGunParticle p;
  // --- Vertex smearing ---
  GenVertexModel(p);
  if (fMomentumModel > 0)
    GenMomentumModel(p);
  else {
    Double32_t pabs = 0, pt = 0, theta = 0, eta, y, mt, pz = 0;
    // Generate particles
    const Double32_t phi =
        gRandom->Uniform(fPhiMin, fPhiMax) * TMath::DegToRad();

    if (fPRangeIsSet) {
      pabs = gRandom->Uniform(fPMin, fPMax);
    } else if (fPtRangeIsSet) {
      pt = gRandom->Uniform(fPtMin, fPtMax);
    }

    if (fThetaRangeIsSet) {
      if (fCosThetaIsSet)
        theta = acos(gRandom->Uniform(cos(fThetaMax * TMath::DegToRad()),
                                      cos(fThetaMin * TMath::DegToRad())));
      else {
        theta = gRandom->Uniform(fThetaMin, fThetaMax) * TMath::DegToRad();
      }
    } else if (fEtaRangeIsSet) {
      eta = gRandom->Uniform(fEtaMin, fEtaMax);
      theta = 2 * TMath::ATan(TMath::Exp(-eta));
    } else if (fYRangeIsSet) {
      y = gRandom->Uniform(fYMin, fYMax);
      mt = TMath::Sqrt(GetPDGMass() * GetPDGMass() + pt * pt);
      pz = mt * TMath::SinH(y);
    }

    if (fThetaRangeIsSet || fEtaRangeIsSet) {
      if (fPRangeIsSet) {
        pz = pabs * TMath::Cos(theta);
        pt = pabs * TMath::Sin(theta);
      } else if (fPtRangeIsSet) {
        pz = pt / TMath::Tan(theta);
      }
    } else if (fPRangeIsSet) {
      pz = pabs;
    }
    p.Px = pt * TMath::Cos(phi);
    p.Py = pt * TMath::Sin(phi);
    p.Pz = pz;
  }
  return p;
}

void ParticleGunGenerator::OverrideFromHistogram(ParticleGunParticle& p) {
  for (const auto& entry : fHistoEntries) {
    switch (entry.dims) {
      case 1:
        SetVar(p, entry.varNames[0],
               static_cast<TH1*>(entry.hist.get())->GetRandom());
        break;
      case 2:
        static_cast<TH2*>(entry.hist.get())
            ->GetRandom2(GetVar(p, entry.varNames[0]),
                         GetVar(p, entry.varNames[1]));
        break;
      case 3:
        static_cast<TH3*>(entry.hist.get())
            ->GetRandom3(GetVar(p, entry.varNames[0]),
                         GetVar(p, entry.varNames[1]),
                         GetVar(p, entry.varNames[2]));
        break;
      default:
        LOG(error) << "ParticleGunGenerator: unsupported histogram dimension "
                   << entry.dims;
    }
  }
}

void ParticleGunGenerator::SetMomentumModel(int modelNo,
                                            std::vector<Double32_t> pars) {
  auto it = kMomentumModels().find(modelNo);
  if (it == kMomentumModels().end()) {
    LOG(fatal) << "ParticleGunGenerator: unknown momentum model " << modelNo;
    throw std::runtime_error("ParticleGunGenerator: unknown momentum model " +
                             std::to_string(modelNo));
  }

  const auto& spec = it->second;
  if (static_cast<int>(pars.size()) != spec.expectedPars) {
    LOG(fatal) << "ParticleGunGenerator: momentum model " << modelNo << " ("
               << spec.description << ") requires " << spec.expectedPars
               << " parameters, got " << pars.size();
    throw std::runtime_error("ParticleGunGenerator: momentum model " +
                             std::to_string(modelNo) + " (" + spec.description +
                             ") requires " + std::to_string(spec.expectedPars) +
                             " parameters, got " + std::to_string(pars.size()));
  }

  fMomentumModel = modelNo;
  fMomentumPars = std::move(pars);
  LOG(info) << "ParticleGunGenerator: momentum model " << modelNo << " ("
            << spec.description << ")";
}

void ParticleGunGenerator::SetVertexModel(const std::string& model,
                                          std::vector<Double32_t> pars) {
  // Normalise to lowercase so "Gaussian", "GAUSSIAN" etc. all work
  std::string lower = model;
  std::transform(lower.begin(), lower.end(), lower.begin(), ::tolower);

  auto it = kVertexModels().find(lower);
  if (it == kVertexModels().end()) {
    LOG(fatal) << "ParticleGunGenerator: unknown vertex model " << model;
    throw std::runtime_error("ParticleGunGenerator: unknown vertex model " +
                             model);
  }

  const auto& spec = it->second;
  if (static_cast<int>(pars.size()) != spec.expectedPars) {
    LOG(fatal) << "ParticleGunGenerator: vertex model " << model << " ("
               << spec.description << ") requires " << spec.expectedPars
               << " parameters, got " << pars.size();
    throw std::runtime_error("ParticleGunGenerator: vertex model " + model +
                             " (" + spec.description + ") requires " +
                             std::to_string(spec.expectedPars) +
                             " parameters, got " + std::to_string(pars.size()));
  }

  fVertexModel = lower;
  fVertexPars = std::move(pars);
  LOG(info) << "ParticleGunGenerator: vertex model " << lower << " ("
            << spec.description << ")";
}

void ParticleGunGenerator::GenVertexModel(ParticleGunParticle& p) {
  kVertexModels().at(fVertexModel).generate(p, fVertexPars);
}

void ParticleGunGenerator::GenMomentumModel(ParticleGunParticle& p) {
  kMomentumModels().at(fMomentumModel).generate(p, fMomentumPars);
}

void ParticleGunGenerator::PrintVertexModels() {
  LOG(info) << "Available vertex models:";
  for (const auto& [id, spec] : kVertexModels())
    LOG(info) << "  Model " << id << " (" << spec.expectedPars
              << " pars): " << spec.description;
}

void ParticleGunGenerator::PrintMomentumModels() {
  LOG(info) << "Available momentum models:";
  for (const auto& [id, spec] : kMomentumModels())
    LOG(info) << "  Model " << id << " (" << spec.expectedPars
              << " pars): " << spec.description;
}

Double32_t& ParticleGunGenerator::GetVar(ParticleGunParticle& p,
                                         const std::string& name) {
  if (name == "X") return p.X;
  if (name == "Y") return p.Y;
  if (name == "Z") return p.Z;
  if (name == "Px") return p.Px;
  if (name == "Py") return p.Py;
  if (name == "Pz") return p.Pz;
  LOG(fatal) << "ParticleGunGenerator: unknown variable name '" << name << "'";
  throw std::runtime_error("ParticleGunGenerator: unknown variable name '" +
                           name + "'");
  return p.X;  // unreachable, silences compiler warning
}

void ParticleGunGenerator::SetVar(ParticleGunParticle& p,
                                  const std::string& name, Double32_t value) {
  GetVar(p, name) = value;
}

FairGenerator* ParticleGunGenerator::CloneGenerator() const {
  auto* clone = new ParticleGunGenerator(*this);
  for (auto& entry : clone->fHistoEntries) {
    entry.hist.reset(static_cast<TH1*>(entry.hist->Clone()));
    entry.hist->SetDirectory(nullptr);
  }
  return clone;
}
