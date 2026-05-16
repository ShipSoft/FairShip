
#include "ParticleGunGenerator.h"

#include <TDatabasePDG.h>
#include <TMath.h>
#include <TNamed.h>
#include <TParticlePDG.h>
#include <TRandom.h>

#include <cmath>   // for cos, acos
#include <cstdio>  // for printf

#include "FairLogger.h"
#include "FairPrimaryGenerator.h"
#include "TFile.h"
#include "TH2.h"
#include "TH3.h"

ParticleGunGenerator::ParticleGunGenerator() : SHiP::Generator() {}

ParticleGunGenerator::ParticleGunGenerator(Int_t pdgid, Int_t mult)
    : SHiP::Generator() {
  // Constructor. Set default kinematics limits
  SetPDGType(pdgid);
  SetMultiplicity(mult);
  SetPhiRange();
}

ParticleGunGenerator::~ParticleGunGenerator() = default;

void ParticleGunGenerator::SetXYZ(Double32_t x, Double32_t y, Double32_t z) {
  SetVertex(x, y, z, 0, 0, 0);
}

void ParticleGunGenerator::SetVertex(Double32_t x, Double32_t y, Double32_t z,
                                     Double32_t ex, Double32_t ey,
                                     Double32_t ez) {
  fVx = x;
  fVy = y;
  fVz = z;
  fVex = ex;
  fVey = ey;
  fVez = ez;
}

void ParticleGunGenerator::SetBoxXYZ(Double32_t x1, Double32_t y1,
                                     Double32_t x2, Double32_t y2,
                                     Double32_t z) {
  Double_t X1 = TMath::Min(x1, x2);
  Double_t X2 = TMath::Max(x1, x2);
  Double_t Y1 = TMath::Min(y1, y2);
  Double_t Y2 = TMath::Max(y1, y2);
  Double_t dX = 0.5 * (X2 - X1);
  Double_t dY = 0.5 * (Y2 - Y1);
  Double_t x = 0.5 * (X1 + X2);
  Double_t y = 0.5 * (Y1 + Y2);
  SetVertex(x, y, z, dX, dY, 0);
}

void ParticleGunGenerator::LoadHistoFromFile(
    const std::string& inFile, const std::string& inHisto,
    std::vector<std::string> varNames) {
  TFile loadFile(inFile.c_str());
  auto* raw = dynamic_cast<TH1*>(loadFile.Get(inHisto.c_str()));
  if (!raw) {
    LOG(fatal) << "ParticleGunGenerator: Histogram " << inHisto
               << " not found in file " << inFile;
    return;
  }
  raw = static_cast<TH1*>(raw->Clone());
  raw->SetDirectory(nullptr);  // detach from ROOT's directory ownership
  loadFile.Close();

  const int dims = raw->GetDimension();
  if (static_cast<int>(varNames.size()) != dims)
    LOG(fatal) << "ParticleGunGenerator: " << varNames.size()
               << " variables given for a " << dims << "-D histogram";
  else {
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
          return;
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
  // Check for particle type
  TDatabasePDG* pdgBase = TDatabasePDG::Instance();
  TParticlePDG* particle = pdgBase->GetParticle(m_pdgid);

  if (!particle) {
    LOG(fatal) << "ParticleGunGenerator: PDG " << GetPDGType()
               << " not defined";
    return kFALSE;
  }
  LOG(info) << this->ClassName() << ": particle with PDG =" << GetPDGType()
            << " Found";
  fPDGMass = particle->Mass();

  if (fPhiMax - fPhiMin > 360) {
    LOG(fatal) << "ParticleGunGenerator:Init(): phi range is too wide: "
               << fPhiMin << "<phi<" << fPhiMax;
  }
  if (fEkinRangeIsSet) {
    if (fPRangeIsSet) {
      LOG(fatal) << "ParticleGunGenerator:Init(): Cannot set P and Ekin ranges "
                    "simultaneously";
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
  }
  if (fPRangeIsSet && fYRangeIsSet) {
    LOG(fatal) << "ParticleGunGenerator:Init():  Cannot set P and Y ranges "
                  "simultaneously";
  }
  if ((fThetaRangeIsSet && fYRangeIsSet) ||
      (fThetaRangeIsSet && fEtaRangeIsSet) ||
      (fYRangeIsSet && fEtaRangeIsSet)) {
    LOG(fatal) << "ParticleGunGenerator:Init():  Cannot set Y, Theta or Eta "
                  "ranges simultaneously";
  }
  return kTRUE;
}

void ParticleGunGenerator::SetBothCharges(bool flag, Double32_t fraction) {
  if (flag && (!std::isfinite(fraction) || fraction < 0. || fraction > 1.)) {
    LOG(fatal)
        << "ParticleGunGenerator: charge fraction must be finite and in [0, 1]";
  }
  m_bothCharges = flag;
  m_chargeFraction = flag ? fraction : 1.;
  if (m_bothCharges)
    LOG(info) << "ParticleGunGenerator: Setting to generate both charges, with "
                 "fraction of "
              << m_pdgid << " set to " << m_chargeFraction;
  else
    LOG(info) << "ParticleGunGenerator: Setting to only generate one charge "
                 "for PDG id"
              << m_pdgid;
}

int ParticleGunGenerator::GetPDGType() {
  if (m_bothCharges) {
    float tPDG = gRandom->Uniform();
    return (tPDG > m_chargeFraction) ? -m_pdgid : m_pdgid;
  } else
    return m_pdgid;
}

Bool_t ParticleGunGenerator::ReadEvent(FairPrimaryGenerator* primGen) {
  int pdg_type;
  for (Int_t k = 0; k < GetMultiplicity(); k++) {
    pdg_type = GetPDGType();
    ParticleGunParticle p = GenerateKinematics();
    OverrideFromHistogram(p);
    primGen->AddTrack(pdg_type, p.Px, p.Py, p.Pz, p.X, p.Y, p.Z);
  }
  return kTRUE;
}

ParticleGunParticle ParticleGunGenerator::GenerateKinematics() {
  ParticleGunParticle p;
  // --- Vertex smearing ---
  p.X = SmearVertex(fVx, fVex, fSmearMode);
  p.Y = SmearVertex(fVy, fVey, fSmearMode);
  p.Z = SmearVertex(fVz, fVez, fSmearMode);

  // Now sort the momentum
  LOG(info) << this->ClassName() << ": Event,  vertex = (" << p.X << "," << p.Y
            << "," << p.Z << ") cm,  multiplicity " << m_mult;

  if(fMomentumModel>0)
      GenMomentumModel(p);
  else{
      Double32_t pabs = 0, pt = 0, theta = 0, eta, y, mt, pz = 0;
      // Generate particles
      const Double32_t phi = gRandom->Uniform(fPhiMin, fPhiMax) * TMath::DegToRad();

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

void ParticleGunGenerator::SetSmearMode(const std::string& mode) {
  // Normalise to lowercase so "Gaussian", "GAUSSIAN" etc. all work
  std::string lower = mode;
  std::transform(lower.begin(), lower.end(), lower.begin(), ::tolower);

  if (lower == "gaussian")
    fSmearMode = SmearMode::kGaussian;
  else if (lower == "uniform")
    fSmearMode = SmearMode::kUniform;
  else if (lower == "exponential")
    fSmearMode = SmearMode::kExponential;
  else
    LOG(fatal) << "ParticleGunGenerator: unknown smear mode '" << mode
               << "'. Valid options: exponential, gaussian, uniform";
}

// Apply the requested distribution around `centre` with the given `spread`.
// Spread interpretation:
//   kExponential  — mean of the exponential (drawn symmetrically ±)
//   kGaussian     — sigma (σ) of the Gaussian
//   kUniform      — half-width of the flat distribution  [centre-spread,
//   centre+spread]
Double32_t ParticleGunGenerator::SmearVertex(Double_t centre, Double_t spread,
                                             SmearMode mode) {
  if (spread == 0.) return centre;

  switch (mode) {
    case SmearMode::kGaussian:
      return centre + gRandom->Gaus(0., spread);

    case SmearMode::kUniform:
      return gRandom->Uniform(centre - spread, centre + spread);

    case SmearMode::kExponential:
    default: {
      const Double_t sign = (gRandom->Uniform() < 0.5) ? +1. : -1.;
      return centre + sign * gRandom->Exp(spread);
    }
  }
}

void ParticleGunGenerator::SetMomentumModel(int modelNo, std::vector<Double32_t> pars)
{
    auto it = kMomentumModels.find(modelNo);
    if (it == kMomentumModels.end()) {
        LOG(fatal) << "ParticleGunGenerator: unknown momentum model " << modelNo;
        return;
    }

    const auto& spec = it->second;
    if (static_cast<int>(pars.size()) != spec.expectedPars) {
        LOG(fatal) << "ParticleGunGenerator: momentum model " << modelNo
                   << " (" << spec.description << ") requires "
                   << spec.expectedPars << " parameters, got " << pars.size();
        return;
    }

    fMomentumModel = modelNo;
    fMomentumPars  = std::move(pars);
    LOG(info) << "ParticleGunGenerator: momentum model " << modelNo
              << " (" << spec.description << ")";
}

void ParticleGunGenerator::GenMomentumModel(ParticleGunParticle& p)
{
    kMomentumModels.at(fMomentumModel).generate(p, fMomentumPars);
}

void ParticleGunGenerator::PrintMomentumModels()
{
    LOG(info) << "Available momentum models:";
    for (const auto& [id, spec] : kMomentumModels)
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
  return p.X;  // unreachable, silences compiler warning
}

void ParticleGunGenerator::SetVar(ParticleGunParticle& p,
                                  const std::string& name, Double32_t value) {
  GetVar(p, name) = value;
}

FairGenerator* ParticleGunGenerator::CloneGenerator() const {
  return new ParticleGunGenerator(*this);
}
