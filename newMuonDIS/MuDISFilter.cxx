// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#include "MuDISFilter.h"

#include <Pythia8/Pythia.h>
#include <TFile.h>
#include <TTree.h>
#include <TTreeReader.h>
#include <TTreeReaderValue.h>

#include <algorithm>
#include <cmath>
#include <format>
#include <iostream>
#include <memory>
#include <sstream>
#include <stdexcept>
#include <string>
#include <string_view>

#include "FairLogger.h"
#include "MagneticTrackPropagator.h"

using ROOT::Math::XYZPoint;
using ROOT::Math::XYZVector;
using ShipMuDIS::MatTypeStr;
using ShipMuDIS::MuonDISInBranches;
using ShipMuDIS::MuonInBranches;
using ShipMuDIS::nMats;

namespace {
// Keep the nominal bin width and reserve one visible bin at each end.
template <typename Histogram>
Histogram* WithFlowBins(TDirectory* dir, const std::string& name,
                        const std::string& title, int bins, double low,
                        double high) {
  const double width = (high - low) / bins;
  auto* histogram = new Histogram(name.c_str(), title.c_str(), bins + 2,
                                  low - width, high + width);
  histogram->SetDirectory(dir);
  return histogram;
}

template <typename Histogram>
Histogram* WithFlowBins(TDirectory* dir, const std::string& name,
                        const std::string& title, int nx, double xmin,
                        double xmax, int ny, double ymin, double ymax) {
  const double dx = (xmax - xmin) / nx, dy = (ymax - ymin) / ny;
  auto* histogram =
      new Histogram(name.c_str(), title.c_str(), nx + 2, xmin - dx, xmax + dx,
                    ny + 2, ymin - dy, ymax + dy);
  histogram->SetDirectory(dir);
  return histogram;
}

double VisibleFlowValue(const TAxis* axis, double value) {
  if (value < axis->GetBinLowEdge(2)) return axis->GetBinCenter(1);
  if (value >= axis->GetBinLowEdge(axis->GetNbins()))
    return axis->GetBinCenter(axis->GetNbins());
  return value;
}

void FillWithFlow(TH1* histogram, double value) {
  if (!histogram) return;
  histogram->Fill(VisibleFlowValue(histogram->GetXaxis(), value));
}

void FillWithFlow(TH2* histogram, double x, double y) {
  if (!histogram) return;
  histogram->Fill(VisibleFlowValue(histogram->GetXaxis(), x),
                  VisibleFlowValue(histogram->GetYaxis(), y));
}

bool IsNeutrino(const DISparticle& particle) {
  const int pid = std::abs(particle.pid);
  return pid == 12 || pid == 14 || pid == 16;
}

bool InsideXY(const XYZPoint& hit, const std::array<double, 4>& bounds) {
  return hit.X() >= bounds[0] && hit.X() <= bounds[1] && hit.Y() >= bounds[2] &&
         hit.Y() <= bounds[3];
}

bool PassesChargedMomentumCut(const DISparticle& particle) {
  return std::sqrt(particle.px * particle.px + particle.py * particle.py +
                   particle.pz * particle.pz) > 1.;
}

constexpr std::array<double, 5> kMomentumEdges = {2., 20., 50., 100., 400.};
constexpr std::array<double, 6> kPtEdges = {0., 1., 2., 3., 5., 10.};

int KinematicBin(double value, const double* edges, unsigned bins) {
  if (!std::isfinite(value) || value < edges[0] || value > edges[bins])
    return -1;
  for (unsigned bin = 0; bin < bins; ++bin)
    if (value < edges[bin + 1] || bin + 1 == bins) return bin;
  return -1;
}
}  // namespace

// -----   Default constructor   -------------------------------------------
MuDISFilter::MuDISFilter() : fPDG(TDatabasePDG::Instance()) {}

void MuDISFilter::SetFilterEfficiencyBinning(double xmin, double xmax,
                                             unsigned xbins, double ymin,
                                             double ymax, unsigned ybins,
                                             double zmin, double zmax,
                                             unsigned zbins) {
  const auto symmetricAboutZero = [](double low, double high) {
    return std::abs(low + high) <=
           1.e-12 * std::max({1., std::abs(low), std::abs(high)});
  };
  if (!std::isfinite(xmin) || !std::isfinite(xmax) || !std::isfinite(ymin) ||
      !std::isfinite(ymax) || !std::isfinite(zmin) || !std::isfinite(zmax) ||
      xmin >= xmax || ymin >= ymax || zmin >= zmax || xbins == 0 ||
      ybins == 0 || zbins == 0 || xbins % 2 == 0 || ybins % 2 == 0 ||
      !symmetricAboutZero(xmin, xmax) || !symmetricAboutZero(ymin, ymax))
    throw std::invalid_argument(
        "Filter-efficiency x/y axes must be symmetric about zero with an odd "
        "positive number of bins; all axis bounds must increase");
  fEfficiencyXYBounds = {xmin, xmax, ymin, ymax};
  fEfficiencyXBins = xbins;
  fEfficiencyYBins = ybins;
  fEfficiencyZBounds = {zmin, zmax};
  fEfficiencyZBins = zbins;
}

Histograms MuDISFilter::BookHistograms(TDirectory* dir, const std::string& mat,
                                       const std::string& label) {
  dir->cd();

  Histograms h;

  h.dis_vxz = WithFlowBins<TH2D>(
      dir, std::format("vertex_x_vs_z_{}", label),
      std::format("DIS vertex x vs z - {};z [cm];x [cm]", mat), 3300, 2700.,
      9000., 600, -300., 300.);
  h.dis_vyz = WithFlowBins<TH2D>(
      dir, std::format("vertex_y_vs_z_{}", label),
      std::format("DIS vertex y vs z - {};z [cm];y [cm]", mat), 3300, 2700.,
      9000., 600, -300., 300.);
  h.dis_vxy = WithFlowBins<TH2D>(
      dir, std::format("vertex_y_vs_x_{}", label),
      std::format("DIS vertex y vs x - {};x [cm];y [cm]", mat), 600, -300.,
      300., 600, -300., 300.);
  if (fDetailedHistograms)
    h.dis_vr = WithFlowBins<TH1D>(
        dir, std::format("vertex_r_{}", label),
        std::format("DIS vertex radius - {};r [cm];Events", mat), 600, 0.,
        600.);
  h.dis_vz = WithFlowBins<TH1D>(
      dir, std::format("vertex_z_{}", label),
      std::format("DIS vertex z - {};z [cm];Events", mat), 3300, 2700., 9000.);
  if (fDetailedHistograms)
    h.dis_pdg = WithFlowBins<TH1I>(
        dir, std::format("daughter_pdg_{}", label),
        std::format("PDG code of DIS daughters - {};PDG code;Particles", mat),
        12001, -6000.5, 6000.5);
  h.dis_pdgGrouped = WithFlowBins<TH1I>(
      dir, std::format("daughter_pdg_grouped_{}", label),
      std::format("DIS daughter species - {};Species;Particles", mat), 11, 0.5,
      11.5);
  constexpr std::array<const char*, 11> labels = {
      "e^{+}",     "e^{-}",   "#mu^{+}", "#mu^{-}", "#gamma", "#nu/#bar{#nu}",
      "#pi^{#pm}", "h^{#pm}", "#pi^{0}", "h^{0}",   "other"};
  for (std::size_t bin = 0; bin < labels.size(); ++bin)
    h.dis_pdgGrouped->GetXaxis()->SetBinLabel(bin + 2, labels[bin]);
  if (fDetailedHistograms)
    h.dis_n = WithFlowBins<TH1I>(
        dir, std::format("n_daughters_{}", label),
        std::format("Number of DIS daughters - {};multiplicity;Event", mat), 50,
        0, 50);
  if (fDetailedHistograms)
    h.dis_nCharged = WithFlowBins<TH1I>(
        dir, std::format("n_daughters_charged_{}", label),
        std::format(
            "Number of charged DIS daughters - {};charged multiplicity;Event",
            mat),
        50, 0, 50);
  h.dis_nChargedCandidates = WithFlowBins<TH1I>(
      dir, std::format("n_charged_candidates_{}", label),
      std::format(
          "Number of charged filter candidates - {};charged multiplicity;Event",
          mat),
      50, 0, 50);
  h.dis_eNeutralTD = WithFlowBins<TH1D>(
      dir, std::format("neutral_candidate_energy_TD_{}", label),
      std::format("Visible neutral candidate energy reaching timing detector - "
                  "{};energy [GeV];Event",
                  mat),
      400, 0., 400.);
  if (fDetailedHistograms)
    h.dis_pChargedFrac = WithFlowBins<TH1D>(
        dir, std::format("pfrac_charged_{}", label),
        std::format("Charged fraction - {};p(charged)/p(all);Event", mat), 101,
        0, 1.01);
  if (fDetailedHistograms)
    h.dis_pMuFrac = WithFlowBins<TH1D>(
        dir, std::format("pfrac_mu_{}", label),
        std::format("p fraction of outgoing mu - {};p(mu)/p(all);Event", mat),
        101, 0, 1.01);
  if (fDetailedHistograms)
    h.mu_p = WithFlowBins<TH1D>(
        dir, std::format("muon_p_{}", label),
        std::format("muon momentum - {};p_{{#mu,in}} [GeV]; Input mu events",
                    mat),
        400, 0., 400.);
  if (fDetailedHistograms)
    h.mu_pt = WithFlowBins<TH1D>(
        dir, std::format("muon_pt_{}", label),
        std::format("muon p_{{T}} - {};p_{{T,#mu,in}} [GeV];Input mu events",
                    mat),
        100, 0., 10.);
  h.mu_ppt = WithFlowBins<TH2D>(
      dir, std::format("muon_pt_vs_p_{}", label),
      std::format("muon p_{{T}} vs p - {};p_{{#mu,in}} [GeV]; "
                  "p_{{T,#mu,in}} [GeV];Input mu events",
                  mat),
      400, 0, 400, 100, 0., 10.);
  if (fDetailedHistograms)
    h.mu_ndis = WithFlowBins<TH1I>(
        dir, std::format("muon_n_dis_{}", label),
        std::format(
            "Number of DIS events - {};DIS multiplicity;Input mu events", mat),
        1001, 0, 1001);
  if (fDetailedHistograms)
    h.mu_wdis = WithFlowBins<TH1D>(
        dir, std::format("muon_vtx_weight_{}", label),
        std::format("DIS vertex weight - {};wDIS;Input mu events", mat), 100,
        0., 1000.);
  return h;
}

void MuDISFilter::BookFilterEfficiencyHistograms(TDirectory* dir) {
  dir->cd();
  fFilterEfficiency = {};
  const double xmin = fEfficiencyXYBounds[0], xmax = fEfficiencyXYBounds[1];
  const double ymin = fEfficiencyXYBounds[2], ymax = fEfficiencyXYBounds[3];
  for (unsigned ip = 0; ip < kMomentumBins; ++ip)
    for (unsigned ipt = 0; ipt < kPtBins; ++ipt)
      for (unsigned imat = 0; imat < kEfficiencyMaterials; ++imat) {
        const std::string tag =
            std::format("p{}_pt{}_{}", ip, ipt, MatTypeStr[imat]);
        const std::string title = std::format(
            "DIS filter efficiency, {:.0f} #leq p < {:.0f} GeV, "
            "{:.0f} #leq p_{{T}} < {:.0f} GeV - {};x_{{#mu,start}} [cm];"
            "y_{{#mu,start}} [cm]",
            kMomentumEdges[ip], kMomentumEdges[ip + 1], kPtEdges[ipt],
            kPtEdges[ipt + 1], MatTypeStr[imat]);
        auto*& all = fFilterEfficiency.allXY[ip][ipt][imat];
        auto*& passed = fFilterEfficiency.passedXY[ip][ipt][imat];
        all = new TH2D(("filter_efficiency_all_" + tag).c_str(), title.c_str(),
                       fEfficiencyXBins, xmin, xmax, fEfficiencyYBins, ymin,
                       ymax);
        passed = new TH2D(("filter_efficiency_passed_" + tag).c_str(),
                          title.c_str(), fEfficiencyXBins, xmin, xmax,
                          fEfficiencyYBins, ymin, ymax);
        all->SetDirectory(dir);
        all->Sumw2();
        passed->SetDirectory(dir);
        passed->Sumw2();
        if (!fDetailedHistograms) continue;
        auto& allZByX = fFilterEfficiency.allZ[ip][ipt];
        auto& passedZByX = fFilterEfficiency.passedZ[ip][ipt];
        allZByX.resize(fEfficiencyXBins);
        passedZByX.resize(fEfficiencyXBins);
        for (unsigned ix = 0; ix < fEfficiencyXBins; ++ix) {
          allZByX[ix].resize(fEfficiencyYBins);
          passedZByX[ix].resize(fEfficiencyYBins);
          for (unsigned iy = 0; iy < fEfficiencyYBins; ++iy) {
            auto*& allZ = fFilterEfficiency.allZ[ip][ipt][ix][iy][imat];
            auto*& passedZ = fFilterEfficiency.passedZ[ip][ipt][ix][iy][imat];
            allZ = new TH1D(
                std::format("filter_efficiency_z_all_{}_x{}_y{}", tag, ix, iy)
                    .c_str(),
                (title + ";z_{DIS} [cm];Weighted DIS events").c_str(),
                fEfficiencyZBins, fEfficiencyZBounds[0], fEfficiencyZBounds[1]);
            passedZ =
                new TH1D(std::format("filter_efficiency_z_passed_{}_x{}_y{}",
                                     tag, ix, iy)
                             .c_str(),
                         allZ->GetTitle(), fEfficiencyZBins,
                         fEfficiencyZBounds[0], fEfficiencyZBounds[1]);
            allZ->SetDirectory(dir);
            allZ->Sumw2();
            passedZ->SetDirectory(dir);
            passedZ->Sumw2();
          }
        }
      }
}

void MuDISFilter::FillFilterEfficiencyHistograms(unsigned material,
                                                 double momentum, double pt,
                                                 double x, double y, double z,
                                                 double weight, bool passed) {
  if (material >= kEfficiencyMaterials || !std::isfinite(weight)) return;
  const int ip = KinematicBin(momentum, kMomentumEdges.data(), kMomentumBins);
  const int ipt = KinematicBin(pt, kPtEdges.data(), kPtBins);
  if (ip < 0 || ipt < 0) return;
  auto* all = fFilterEfficiency.allXY[ip][ipt][material];
  auto* accepted = fFilterEfficiency.passedXY[ip][ipt][material];
  all->Fill(x, y, weight);
  if (passed) accepted->Fill(x, y, weight);
  if (!fDetailedHistograms) return;
  const int ix = all->GetXaxis()->FindFixBin(x) - 1;
  const int iy = all->GetYaxis()->FindFixBin(y) - 1;
  if (ix < 0 || ix >= static_cast<int>(fEfficiencyXBins) || iy < 0 ||
      iy >= static_cast<int>(fEfficiencyYBins))
    return;
  fFilterEfficiency.allZ[ip][ipt][ix][iy][material]->Fill(z, weight);
  if (passed)
    fFilterEfficiency.passedZ[ip][ipt][ix][iy][material]->Fill(z, weight);
}

void MuDISFilter::init(int aEvts, int aStart) {
  if (aEvts < -1 || aStart < 0)
    throw std::invalid_argument("Invalid event range");
  fnEvts = aEvts;
  fstartEvt = aStart;
}

bool MuDISFilter::InitFile(const char* fileName) {
  return InitFile(fileName, 0);
}

bool MuDISFilter::InitFiles(const std::vector<std::string>& fileNames) {
  return InitFiles(fileNames, 0);
}

// -----   Default constructor   -------------------------------------------
bool MuDISFilter::InitFile(const char* fileName, const int startEvent) {
  std::vector<std::string> fileNames = {fileName};
  return InitFiles(fileNames, startEvent);
}

bool MuDISFilter::InitFiles(const std::vector<std::string>& fileNames,
                            const int startEvent) {
  if (startEvent < 0) return false;
  fstartEvt = startEvent;
  if (fileNames.empty()) {
    LOG(error) << "MuDISFilter: no input files provided. "
               << "Check the -f/--inputFile argument or input file glob.";
    return false;
  }
  for (const auto& fileName : fileNames) {
    if (fileName.empty()) {
      LOG(error) << "MuDISFilter: received an empty input file name. "
                 << "Check the -f/--inputFile argument.";
      return false;
    }
  }

  for (const auto& name : fileNames) {
    std::unique_ptr<TFile> file(TFile::Open(name.c_str(), "READ"));
    TTree* tree = nullptr;
    if (file && !file->IsZombie()) file->GetObject("MuonDIS", tree);
    if (!tree) {
      LOG(error) << "MuDISFilter: missing MuonDIS tree in " << name;
      return false;
    }
    MuonInBranches check;
    if (!check.Setup(tree)) return false;
    tree->ResetBranchAddresses();
  }

  {
    ftree = std::make_unique<TChain>("MuonDIS");
    for (const auto& name : fileNames) {
      if (!ftree->Add(name.c_str())) return false;
    }
    std::int64_t treeEvts = ftree->GetEntries();
    LOG(info) << "Reading " << treeEvts << " entries.";
    bool ok = finEv.Setup(ftree.get());

    if (!ok) {
      LOG(error) << "MuDISFilter: failed to bind one or more required branches";
      return false;
    }
    LOG(info) << "MuDISFilter: Initialization successful.";
    return true;
  }
  return false;
}

void MuDISFilter::process_file(const std::string& input,
                               const std::string& output) {
  std::vector<std::string> fileNames = {input};
  return process_file(fileNames, output);
}

void MuDISFilter::process_file(const std::vector<std::string>& input,
                               const std::string& output) {
  if (!fFilter && fFilterOption != 0 && !fUseDetectorAcceptance)
    throw std::runtime_error(
        "Filter options 1 and 2 require detector acceptance");
  if (!fFilter && fUseDetectorAcceptance && !fPropagator)
    throw std::runtime_error(
        "Configure detector acceptance with geometry and field map first");

  bool treeOK = InitFiles(input, fstartEvt);

  if (!treeOK) {
    throw std::runtime_error("MuDISFilter: failed to initialize input files");
  }

  if (!fFilter && fUseDetectorAcceptance && fPropagator->HasMuonShieldField()) {
    // A separate, vertex-only reader preserves the filtering chain's branch
    // addresses and cache learning. Restrict the scan to the requested entries.
    TChain vertices("MuonDIS");
    for (const auto& name : input) vertices.Add(name.c_str());
    TTreeReader reader(&vertices);
    std::vector<std::unique_ptr<TTreeReaderValue<std::vector<double>>>> vz;
    for (unsigned imat = 0; imat < nMats; ++imat)
      vz.push_back(std::make_unique<TTreeReaderValue<std::vector<double>>>(
          reader, ("mudis_DISvz_" + MatTypeStr[imat]).c_str()));
    const std::int64_t end =
        fnEvts >= 0 ? std::min<std::int64_t>(std::int64_t{fstartEvt} + fnEvts,
                                             ftree->GetEntries())
                    : ftree->GetEntries();
    double minimum = std::numeric_limits<double>::infinity(),
           msMinimum = minimum;
    bool valid = true;
    if (fstartEvt < end) {
      reader.SetEntriesRange(fstartEvt, end);
      std::int64_t scanned = 0;
      while (reader.Next()) {
        ++scanned;
        for (unsigned imat = 0; imat < nMats; ++imat) {
          const auto* values = vz[imat]->Get();
          if (!values || vz[imat]->GetSetupStatus() < 0 ||
              vz[imat]->GetReadStatus() !=
                  TTreeReaderValue<std::vector<double>>::kReadSuccess) {
            valid = false;
            continue;
          }
          for (double z : *values) {
            if (!std::isfinite(z)) {
              valid = false;
              continue;
            }
            minimum = std::min(minimum, z);
            if (MatTypeStr[imat] == "MS") msMinimum = std::min(msMinimum, z);
          }
        }
      }
      valid = valid && scanned == end - fstartEvt;
    }
    if (valid && std::isfinite(minimum)) {
      const double detectorMinimum =
          fFilterOption == 2 ? fDetectorVolumeZ.first
          : fFilterOption == 1
              ? *std::min_element(fStationZ.begin(), fStationZ.end())
              : fDetectorZ;
      minimum = std::min(minimum, detectorMinimum);
      LOG(info) << "Muon shield field bounds: input MS minimum z = "
                << msMinimum << " cm; conservative scan minimum z = " << minimum
                << " cm";
      fPropagator->SetMuonShieldMinZ(minimum);
    } else {
      // No usable vertices or failed reads: retain the complete field map.
      fPropagator->SetMuonShieldMinZ(-std::numeric_limits<double>::infinity());
      if (!valid)
        LOG(warn)
            << "Vertex range scan failed; using full muon shield field bounds";
    }
  }

  // Histograms belong to this file, even if ROOT's automatic attachment is
  // disabled. Clear borrowed pointers on success and on exception alike.
  const auto closeOutput = [this](TFile* file) {
    delete file;
    fouttree = nullptr;
    for (auto& hist : hist_all) hist = {};
    for (auto& hist : hist_filt) hist = {};
    fFilterEfficiency = {};
  };
  std::unique_ptr<TFile, decltype(closeOutput)> outfile(
      TFile::Open(output.c_str(), "CREATE"), closeOutput);
  if (!outfile || outfile->IsZombie()) {
    throw std::runtime_error("MuDISFilter: cannot create output file " +
                             output);
  }
  outfile->cd();

  for (unsigned imat = 0; imat < nMats; ++imat) {
    TDirectory* dir = outfile->mkdir(MatTypeStr[imat].c_str());

    hist_all[imat] = BookHistograms(dir, MatTypeStr[imat]);
    hist_filt[imat] = BookHistograms(dir, MatTypeStr[imat], "filtered");
  }
  BookFilterEfficiencyHistograms(outfile->mkdir("filter_efficiency"));

  outfile->cd();
  // Owned by outfile, which deletes it on Close().
  fouttree = new TTree(
      "MuonDIS", "Muon information, DIS products and soft interaction tracks");
  foutEv.InitTree(fouttree);

  std::int64_t n = ftree->GetEntries();
  LOG(info) << " * input tree with " << n << " entries";

  ProcessEvents();

  outfile->cd();
  if (outfile->Write() <= 0 || outfile->TestBit(TFile::kWriteError))
    throw std::runtime_error("MuDISFilter: failed to write output file");
  outfile->Close();
}

MuDISFilter::~MuDISFilter() = default;

void MuDISFilter::initEvent() {
  foutEv.initEvent();
  for (unsigned i = 0; i < nMats; ++i) foutEv.br[i].initEvent(0);
}

bool MuDISFilter::IsCharged(const DISparticle& particle) const {
  return Charge(particle) != 0.;
}

double MuDISFilter::Charge(const DISparticle& particle) const {
  const auto* pdg = fPDG->GetParticle(particle.pid);
  // Nuclear PDG codes encode Z in digits 5--7 (10LZZZAAAI).
  if (!pdg && std::abs(particle.pid) >= 1000000000)
    return ((std::abs(particle.pid) / 10000) % 1000) *
           (particle.pid > 0 ? 1. : -1.);
  return pdg ? pdg->Charge() / 3. : 0.;
}

int MuDISFilter::DaughterCategory(const DISparticle& particle) const {
  switch (particle.pid) {
    case -11:
      return 1;
    case 11:
      return 2;
    case -13:
      return 3;
    case 13:
      return 4;
    case 22:
      return 5;
    case 12:
    case -12:
    case 14:
    case -14:
    case 16:
    case -16:
      return 6;
    case 211:
    case -211:
      return 7;
    case 111:
      return 9;
    default:
      break;
  }
  const auto* pdg = fPDG->GetParticle(particle.pid);
  if (pdg) {
    const std::string_view particleClass = pdg->ParticleClass();
    if (particleClass == "Meson" || particleClass == "Baryon")
      return pdg->Charge() != 0. ? 8 : 10;
  }
  return 11;
}

void MuDISFilter::ConfigureFilterGeometry(
    unsigned option, const MagneticTrackPropagator& propagator) {
  if (option == 1) {
    const std::array<const char*, 5> names = {"Tr1", "Tr2", "Tr3", "Tr4",
                                              "Timing Detector"};
    std::array<double, 5> planes;
    std::array<std::array<double, 4>, 5> bounds;
    for (unsigned i = 0; i < names.size(); ++i) {
      planes[i] = propagator.GetPlaneZ(names[i]);
      bounds[i] = propagator.GetVolumeExitFaceXY(names[i]);
    }
    fStationZ = planes;
    fStationXY = bounds;
  } else if (option == 2) {
    const double front = propagator.GetVolumeZRange("Tr1").first;
    const double end = propagator.GetVolumeZRange("SplitCalDetector").second;
    if (front >= end)
      throw std::runtime_error(
          "Calorimeter end must be downstream of the Tr1 front");
    fDetectorVolumeZ = {front, end};
  }
}

void MuDISFilter::SetFilterOption(unsigned option) {
  if (option > 2)
    throw std::invalid_argument("Filter option must be 0, 1 or 2");
  if (fPropagator) ConfigureFilterGeometry(option, *fPropagator);
  fFilterOption = option;
}

void MuDISFilter::InitialisePythiaDecayer() {
  fPythiaDecayer = std::make_unique<Pythia8::Pythia>();
  fPythiaDecayer->readString("ProcessLevel:all = off");
  fPythiaDecayer->readString("Random:setSeed = on");
  unsigned seed = fPythiaDecaySeed;
  if (seed == 0) {
    // Pythia's time-based seed can exceed the Random:seed input range.
    // Wrap before init so replaying the logged seed follows the same setup.
    fPythiaDecayer->rndm.init(0);
    seed =
        1 + (static_cast<unsigned>(fPythiaDecayer->rndm.getState().seed) - 1) %
                900000000;
  }
  if (!fPythiaDecayer->readString("Random:seed = " + std::to_string(seed)))
    throw std::invalid_argument("MuDISFilter: invalid Pythia8 decay seed");
  constexpr std::array<int, 10> decayIds = {211,  321,  130,  310,  3112,
                                            3122, 3222, 3312, 3322, 3334};
  for (int id : decayIds) {
    if (!fPythiaDecayer->readString(std::to_string(id) + ":mayDecay = on"))
      throw std::runtime_error(
          "MuDISFilter: cannot enable Pythia8 decay for PDG " +
          std::to_string(id));
  }
  if (!fPythiaDecayer->init())
    throw std::runtime_error(
        "MuDISFilter: failed to initialize the Pythia8 decayer");
  LOG(info) << "MuDISFilter: Pythia8 decay seed = "
            << fPythiaDecayer->rndm.getState().seed;
}

void MuDISFilter::SetUsePythiaDecays(bool enabled) {
  fUsePythiaDecays = enabled;
  if (enabled)
    InitialisePythiaDecayer();
  else
    fPythiaDecayer.reset();
}

void MuDISFilter::SetPythiaDecaySeed(unsigned seed) {
  fPythiaDecaySeed = seed;
  if (fUsePythiaDecays) InitialisePythiaDecayer();
}

std::vector<MuDISFilter::FilterCandidate> MuDISFilter::DecayDaughters(
    const std::vector<DISparticle>& daughters, const XYZPoint& vertex) const {
  if (!fUsePythiaDecays) {
    std::vector<FilterCandidate> candidates;
    candidates.reserve(daughters.size());
    for (const auto& particle : daughters)
      candidates.push_back({particle, vertex});
    return candidates;
  }
  if (!fPythiaDecayer || !std::isfinite(fTr1Z))
    throw std::runtime_error("MuDISFilter: Pythia decays require Tr1 geometry");

  std::vector<FilterCandidate> candidates;
  const double tr1Zmm = 10. * fTr1Z;
  const auto addParticle = [&candidates](const Pythia8::Particle& particle) {
    DISparticle daughter;
    daughter.pid = particle.id();
    daughter.px = particle.px();
    daughter.py = particle.py();
    daughter.pz = particle.pz();
    daughter.E = particle.e();
    candidates.push_back(
        {daughter, XYZPoint(particle.xProd() / 10., particle.yProd() / 10.,
                            particle.zProd() / 10.)});
  };
  for (const auto& daughter : daughters) {
    fPythiaDecayer->event.reset();
    const double momentum2 = daughter.px * daughter.px +
                             daughter.py * daughter.py +
                             daughter.pz * daughter.pz;
    const double mass2 = daughter.E * daughter.E - momentum2;
    if (mass2 < -1.e-8) {
      candidates.push_back({daughter, vertex});
      continue;
    }
    const int root = fPythiaDecayer->event.append(
        daughter.pid, 1, 0, 0, daughter.px, daughter.py, daughter.pz,
        daughter.E, std::sqrt(std::max(0., mass2)));
    fPythiaDecayer->event[root].vProd(10. * vertex.X(), 10. * vertex.Y(),
                                      10. * vertex.Z(), 0.);
    // Manually appended particles have tau = 0. Pythia samples lifetimes
    // for its own decay products, but the original particle needs one here.
    fPythiaDecayer->event[root].tau(fPythiaDecayer->event[root].tau0() *
                                    fPythiaDecayer->rndm.exp());

    std::function<void(int)> decay = [&](int index) {
      const auto& particle = fPythiaDecayer->event[index];
      if ((tr1Zmm - particle.zProd()) * particle.pz() <= 0.) {
        addParticle(particle);
        return;
      }
      if (!fPythiaDecayer->moreDecays(index) ||
          fPythiaDecayer->event[index].isFinal() ||
          ((tr1Zmm - fPythiaDecayer->event[index].zDec()) *
               fPythiaDecayer->event[index].pz() <=
           0)) {
        addParticle(fPythiaDecayer->event[index]);
        return;
      }
      for (int child : fPythiaDecayer->event[index].daughterList())
        decay(child);
    };
    decay(root);
  }
  return candidates;
}

bool MuDISFilter::HitsTrackingAndTD(double charge, const DISparticle& particle,
                                    const XYZPoint& vertex) const {
  XYZPoint position = vertex;
  XYZVector momentum(particle.px, particle.py, particle.pz);
  std::array<unsigned, 5> order = {0, 1, 2, 3, 4};
  std::sort(order.begin(), order.end(),
            [this, &particle](unsigned a, unsigned b) {
              return particle.pz >= 0. ? fStationZ[a] < fStationZ[b]
                                       : fStationZ[a] > fStationZ[b];
            });
  bool firstPair = false, secondPair = false, TD = false;
  for (unsigned station : order) {
    if ((fStationZ[station] - vertex.Z()) * particle.pz < 0.) continue;
    XYZPoint hit;
    XYZVector nextMomentum;
    if (!fPropagator->Extrapolate(charge, position, momentum,
                                  fStationZ[station], hit, nextMomentum))
      return false;
    position = hit;
    momentum = nextMomentum;
    if (!InsideXY(hit, fStationXY[station])) continue;
    if (station < 2)
      firstPair = true;
    else if (station < 4)
      secondPair = true;
    else
      TD = true;
    if (firstPair && secondPair && TD) return true;
  }
  return false;
}

bool MuDISFilter::PassDetectorFilter(
    const std::vector<FilterCandidate>& candidates) const {
  if (fFilterOption == 2) {
    const XYZPoint minimum(-200., -300., fDetectorVolumeZ.first);
    const XYZPoint maximum(200., 300., fDetectorVolumeZ.second);
    for (const auto& candidate : candidates) {
      const auto& particle = candidate.particle;
      if (IsNeutrino(particle)) continue;
      if (!fIncludeMuons && std::abs(particle.pid) == 13) continue;
      if (fPropagator->IntersectsBox(
              Charge(particle), candidate.vertex,
              XYZVector(particle.px, particle.py, particle.pz), minimum,
              maximum))
        return true;
    }
    return false;
  }
  // Count candidates before expensive transport; option 1 always requires two.
  unsigned remaining = 0, accepted = 0;
  std::vector<double> charges;
  charges.reserve(candidates.size());
  for (const auto& candidate : candidates) {
    const auto& particle = candidate.particle;
    const double charge = !fIncludeMuons && std::abs(particle.pid) == 13 ? 0.
                          : PassesChargedMomentumCut(particle)
                              ? Charge(particle)
                              : 0.;
    charges.push_back(charge);
    if (charge != 0.) ++remaining;
  }
  for (std::size_t i = 0; i < candidates.size(); ++i) {
    if (accepted + remaining < 2) return false;
    if (charges[i] == 0.) continue;
    --remaining;
    if (HitsTrackingAndTD(charges[i], candidates[i].particle,
                          candidates[i].vertex) &&
        ++accepted == 2)
      return true;
  }
  return false;
}

void MuDISFilter::SetDetectorAcceptance(ShipBFieldMap* field,
                                        TGeoManager* geometry, double z,
                                        ShipBFieldMap* muonShieldField) {
  if (!field)
    throw std::invalid_argument("Detector acceptance requires a field map");
  auto propagator = std::make_unique<MagneticTrackPropagator>(field, geometry,
                                                              muonShieldField);
  if (muonShieldField) {
    const auto range = propagator->GetMuonShieldZRange();
    LOG(info)
        << "MuDISFilter: muon shield geometry z range [" << range.first << ", "
        << range.second
        << "] cm; propagating with shield map including nonzero fringe fields";
  }
  const double planeZ = std::isnan(z) ? propagator->GetPlaneZ() : z;
  if (!std::isfinite(planeZ))
    throw std::invalid_argument("Detector z must be finite");
  fTr1Z = propagator->GetPlaneZ("Tr1");
  try {
    fTimingDetectorZ = propagator->GetPlaneZ("Timing Detector");
    fTimingDetectorXY = propagator->GetVolumeExitFaceXY("Timing Detector");
  } catch (const std::runtime_error&) {
    fTimingDetectorZ = std::numeric_limits<double>::quiet_NaN();
  }
  ConfigureFilterGeometry(fFilterOption, *propagator);
  fPropagator = std::move(propagator);
  fDetectorZ = planeZ;
  fUseDetectorAcceptance = true;
}

bool MuDISFilter::PassFilter(const std::vector<DISparticle>& daughters) const {
  if (!fFilter && (fUseDetectorAcceptance || fFilterOption != 0))
    throw std::runtime_error(
        "Detector acceptance requires the DIS vertex; use "
        "PassFilter(daughters, vertex)");
  return PassFilter(daughters, XYZPoint());
}

bool MuDISFilter::PassFilter(const std::vector<DISparticle>& daughters,
                             const XYZPoint& vertex) const {
  if (fFilter) return fFilter(daughters);
  return PassCandidates(DecayDaughters(daughters, vertex));
}

bool MuDISFilter::PassCandidates(
    const std::vector<FilterCandidate>& candidates) const {
  if (fFilterOption != 0 && !fUseDetectorAcceptance)
    throw std::runtime_error(
        "Filter options 1 and 2 require detector acceptance");
  if (fUseDetectorAcceptance && !fPropagator)
    throw std::runtime_error(
        "Configure detector acceptance with geometry and field map first");
  if (fFilterOption != 0) return PassDetectorFilter(candidates);
  if (fMinChargedDaughters == 0) return true;
  if (candidates.size() < fMinChargedDaughters) return false;
  std::vector<double> charges;
  unsigned remaining = 0;
  if (fUseDetectorAcceptance) {
    charges.reserve(candidates.size());
    for (const auto& candidate : candidates) {
      const auto& p = candidate.particle;
      // Count only candidates that can make a forward physical crossing.
      const double charge =
          (!fIncludeMuons && std::abs(p.pid) == 13) ||
                  (fDetectorZ - candidate.vertex.Z()) * p.pz < 0. ||
                  !PassesChargedMomentumCut(p)
              ? 0.
              : Charge(p);
      charges.push_back(charge);
      if (charge != 0.) ++remaining;
    }
    if (remaining < fMinChargedDaughters) return false;
  }
  unsigned charged = 0;
  for (std::size_t i = 0; i < candidates.size(); ++i) {
    const auto& candidate = candidates[i];
    const auto& p = candidate.particle;
    if (!fIncludeMuons && std::abs(p.pid) == 13) continue;
    const double charge = fUseDetectorAcceptance ? charges[i] : Charge(p);
    if (charge == 0.) continue;
    if (!PassesChargedMomentumCut(p)) continue;
    if (fUseDetectorAcceptance) {
      if (charged + remaining < fMinChargedDaughters) return false;
      --remaining;
      XYZPoint hit;
      XYZVector momentum;
      if (!fPropagator->Extrapolate(charge, candidate.vertex,
                                    XYZVector(p.px, p.py, p.pz), fDetectorZ,
                                    hit, momentum) ||
          std::abs(hit.X()) > 200. || std::abs(hit.Y()) > 300.)
        continue;
    }
    ++charged;
    if (charged >= fMinChargedDaughters) return true;
  }
  return charged >= fMinChargedDaughters;
}

bool MuDISFilter::HitsTimingDetector(const FilterCandidate& candidate) const {
  if (!fUseDetectorAcceptance || !fPropagator ||
      !std::isfinite(fTimingDetectorZ) ||
      (fTimingDetectorZ - candidate.vertex.Z()) * candidate.particle.pz < 0.)
    return false;
  XYZPoint hit;
  XYZVector momentum;
  return fPropagator->Extrapolate(
             Charge(candidate.particle), candidate.vertex,
             XYZVector(candidate.particle.px, candidate.particle.py,
                       candidate.particle.pz),
             fTimingDetectorZ, hit, momentum) &&
         InsideXY(hit, fTimingDetectorXY);
}

void MuDISFilter::FillDIS(Histograms& h, const MuonDISInBranches& br, int idis,
                          const std::vector<DISparticle>& daughters,
                          const std::vector<FilterCandidate>& candidates,
                          Histograms* filtered) {
  unsigned charged = 0;
  double totalP = 0., chargedP = 0., muonP = 0.;
  for (const auto& p : daughters) {
    const int category = DaughterCategory(p);
    for (auto* target : {&h, filtered}) {
      if (!target) continue;
      FillWithFlow(target->dis_pdg, p.pid);
      FillWithFlow(target->dis_pdgGrouped, category);
    }
    const double momentum = std::sqrt(p.px * p.px + p.py * p.py + p.pz * p.pz);
    totalP += momentum;
    if (IsCharged(p)) {
      ++charged;
      chargedP += momentum;
    }
    if (std::abs(p.pid) == 13) muonP += momentum;
  }
  unsigned chargedCandidates = 0;
  double neutralTDEnergy = 0.;
  for (const auto& candidate : candidates) {
    if (IsCharged(candidate.particle)) {
      ++chargedCandidates;
    } else if (!IsNeutrino(candidate.particle) &&
               HitsTimingDetector(candidate)) {
      neutralTDEnergy += candidate.particle.E;
    }
  }
  for (auto* target : {&h, filtered}) {
    if (!target) continue;
    FillWithFlow(target->dis_vxz, br.DISvz->at(idis), br.DISvx->at(idis));
    FillWithFlow(target->dis_vyz, br.DISvz->at(idis), br.DISvy->at(idis));
    FillWithFlow(target->dis_vxy, br.DISvx->at(idis), br.DISvy->at(idis));
    FillWithFlow(target->dis_vr,
                 std::hypot(br.DISvx->at(idis), br.DISvy->at(idis)));
    FillWithFlow(target->dis_vz, br.DISvz->at(idis));
    FillWithFlow(target->dis_n, daughters.size());
    FillWithFlow(target->dis_nCharged, charged);
    FillWithFlow(target->dis_nChargedCandidates, chargedCandidates);
    FillWithFlow(target->dis_eNeutralTD, neutralTDEnergy);
    if (totalP > 0.) {
      FillWithFlow(target->dis_pChargedFrac, chargedP / totalP);
      FillWithFlow(target->dis_pMuFrac, muonP / totalP);
    }
  }
}

void MuDISFilter::ProcessEvents() {
  if (!ftree || !fouttree)
    throw std::runtime_error("Initialize input and output first");
  if (fstartEvt < 0) throw std::invalid_argument("Negative start event");
  const std::int64_t end =
      fnEvts >= 0 ? std::min<std::int64_t>(std::int64_t{fstartEvt} + fnEvts,
                                           ftree->GetEntries())
                  : ftree->GetEntries();
  std::int64_t selected = 0, skipped = 0;
  std::array<std::int64_t, nMats> selectedDIS{}, processedDIS{};
  std::array<double, nMats> weightedDIS{}, weightedProcessedDIS{};
  std::array<double, nMats> weightedMuons{}, weightedSelectedMuons{};
  for (std::int64_t event = fstartEvt; event < end; ++event) {
    if ((event - fstartEvt) % 100 == 0)
      LOG(info) << "MuDISFilter: processing entry " << event;
    if (!finEv.PrepareEntry(ftree.get(), event) ||
        ftree->GetEntry(event) <= 0 || !finEv.mcTrks || finEv.mcTrks->empty() ||
        !finEv.sbtPt || !finEv.ubtPt || !finEv.sstPt) {
      ++skipped;
      continue;
    }
    // Check all vector lengths before filling histograms or copying any data.
    bool valid = true;
    for (const auto& br : finEv.br) {
      if (!br.IsValid()) {
        valid = false;
        break;
      }
    }
    if (!valid) {
      LOG(error) << "MuDISFilter: malformed entry " << event << "; skipping";
      ++skipped;
      continue;
    }
    initEvent();
    const auto& muon = finEv.mcTrks->at(0);
    const double muonP = muon.GetP(), muonPt = muon.GetPt();
    bool keep = false;
    for (unsigned imat = 0; imat < nMats; ++imat) {
      const auto& in = finEv.br[imat];
      auto& out = foutEv.br[imat];
      out.wDIS = in.wDIS;
      out.nDISevtsGenerated = in.nDISevtsGenerated;
      out.pPythia = in.pPythia;
      std::size_t offset = 0;
      for (int idis = 0; idis < in.nDISevts; ++idis) {
        const auto endOffset = offset + in.nDISdau->at(idis);
        std::vector<DISparticle> daughters(
            in.DISparticles->begin() + offset,
            in.DISparticles->begin() + endOffset);
        offset = endOffset;
        const XYZPoint vertex(in.DISvx->at(idis), in.DISvy->at(idis),
                              in.DISvz->at(idis));
        std::vector<FilterCandidate> candidates;
        if (fFilter) {
          candidates.reserve(daughters.size());
          for (const auto& daughter : daughters)
            candidates.push_back({daughter, vertex});
        } else {
          candidates = DecayDaughters(daughters, vertex);
        }
        bool identical = candidates.size() == daughters.size();
        for (std::size_t i = 0; identical && i < daughters.size(); ++i) {
          const auto& original = daughters[i];
          const auto& candidate = candidates[i];
          identical = candidate.particle.pid == original.pid &&
                      candidate.particle.px == original.px &&
                      candidate.particle.py == original.py &&
                      candidate.particle.pz == original.pz &&
                      candidate.particle.E == original.E &&
                      candidate.vertex.Z() == vertex.Z();
        }
        if (!identical) {
          std::ostringstream original;
          for (const auto& daughter : daughters) original << ' ' << daughter;
          LOG(debug) << "MuDISFilter: " << MatTypeStr[imat] << " DIS " << idis
                     << " at z=" << vertex.Z()
                     << " cm original daughters:" << original.str();
          std::ostringstream final;
          for (const auto& candidate : candidates) {
            const auto& daughter = candidate.particle;
            final << " [" << daughter.pid << ',' << daughter.px << ','
                  << daughter.py << ',' << daughter.pz << ',' << daughter.E
                  << "; vz=" << candidate.vertex.Z() << ']';
          }
          LOG(debug) << "MuDISFilter: " << MatTypeStr[imat] << " DIS " << idis
                     << " final stable daughters:" << final.str();
        }
        const bool accepted =
            fFilter ? fFilter(daughters) : PassCandidates(candidates);
        FillDIS(hist_all[imat], in, idis, daughters, candidates,
                accepted ? &hist_filt[imat] : nullptr);
        FillFilterEfficiencyHistograms(imat, muonP, muonPt, muon.GetStartX(),
                                       muon.GetStartY(), vertex.Z(), in.wDIS,
                                       accepted);
        if (!accepted) continue;
        ++out.nDISevts;
        out.DISxsec.push_back(in.DISxsec->at(idis));
        out.DIStarget.push_back(in.DIStarget->at(idis));
        out.DISvx.push_back(in.DISvx->at(idis));
        out.DISvy.push_back(in.DISvy->at(idis));
        out.DISvz.push_back(in.DISvz->at(idis));
        out.DISvt.push_back(in.DISvt->at(idis));
        out.nDISdau.push_back(daughters.size());
        out.DISparticles.insert(out.DISparticles.end(), daughters.begin(),
                                daughters.end());
        keep = true;
      }
      auto fillMuon = [muonP, muonPt, &in](Histograms& h, int count) {
        FillWithFlow(h.mu_p, muonP);
        FillWithFlow(h.mu_pt, muonPt);
        FillWithFlow(h.mu_ppt, muonP, muonPt);
        FillWithFlow(h.mu_ndis, count);
        FillWithFlow(h.mu_wdis, in.wDIS);
      };
      fillMuon(hist_all[imat], in.nDISevts);
      if (out.nDISevts > 0) fillMuon(hist_filt[imat], out.nDISevts);
      selectedDIS[imat] += out.nDISevts;
      if (out.nDISevts > 0) weightedDIS[imat] += out.nDISevts * in.wDIS;
      processedDIS[imat] += in.nDISevts;
      if (in.nDISevts > 0) weightedProcessedDIS[imat] += in.nDISevts * in.wDIS;
      weightedMuons[imat] += in.wDIS;
      if (out.nDISevts > 0) weightedSelectedMuons[imat] += in.wDIS;
    }
    if (keep) {
      foutEv.mcTrks = *finEv.mcTrks;
      foutEv.sbtPt = *finEv.sbtPt;
      foutEv.ubtPt = *finEv.ubtPt;
      foutEv.sstPt = *finEv.sstPt;
      foutEv.tdPt = *finEv.tdPt;
      foutEv.pathLength = finEv.pathLength;
      foutEv.pathLengthByMat = finEv.pathLengthByMat;
      if (fouttree->Fill() < 0)
        throw std::runtime_error("Failed writing MuonDIS entry");
      ++selected;
    }
  }
  LOG(info) << "MuDISFilter: saved " << selected << " muon entries; skipped "
            << skipped << " unreadable or malformed entries.";
  for (unsigned imat = 0; imat < nMats; ++imat) {
    LOG(info) << "MuDISFilter: selected DIS events in " << MatTypeStr[imat]
              << ": raw = " << selectedDIS[imat]
              << ", weighted = " << weightedDIS[imat];
    auto* counts =
        new TH1D("filter_counts", "Filter counts;Sample;Count", 8, 0., 8.);
    counts->SetDirectory(
        fouttree->GetDirectory()->GetDirectory(MatTypeStr[imat].c_str()));
    constexpr std::array<const char*, 8> labels = {
        "muons_processed_raw", "muons_processed_weighted",
        "muons_selected_raw",  "muons_selected_weighted",
        "dis_processed_raw",   "dis_processed_weighted",
        "dis_selected_raw",    "dis_selected_weighted"};
    const std::array<double, 8> values = {
        hist_all[imat].mu_ppt->GetEntries(),     weightedMuons[imat],
        hist_filt[imat].mu_ppt->GetEntries(),    weightedSelectedMuons[imat],
        static_cast<double>(processedDIS[imat]), weightedProcessedDIS[imat],
        static_cast<double>(selectedDIS[imat]),  weightedDIS[imat]};
    for (std::size_t bin = 0; bin < labels.size(); ++bin) {
      counts->GetXaxis()->SetBinLabel(bin + 1, labels[bin]);
      counts->SetBinContent(bin + 1, values[bin]);
    }
  }
}
