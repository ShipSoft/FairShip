// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#ifndef NEWMUONDIS_MUDISFILTER_H_
#define NEWMUONDIS_MUDISFILTER_H_

#include <array>
#include <functional>
#include <limits>
#include <memory>
#include <utility>
#include <vector>

#include "FairLogger.h"  // for FairLogger, MESSAGE_ORIGIN
#include "MuDISDefs.h"
#include "TChain.h"  // for TTree
#include "TDatabasePDG.h"
#include "TH1.h"
#include "TH2.h"
#include "TVector3.h"

class MagneticTrackPropagator;
class ShipBFieldMap;
class TGeoManager;
namespace Pythia8 {
class Pythia;
}

struct Histograms {
  TH2D* dis_vxz = nullptr;
  TH2D* dis_vyz = nullptr;
  TH2D* dis_vxy = nullptr;
  TH1D* dis_vr = nullptr;
  TH1D* dis_vz = nullptr;

  TH1I* dis_pdg = nullptr;
  TH1I* dis_pdgGrouped = nullptr;
  TH1I* dis_n = nullptr;
  TH1I* dis_nCharged = nullptr;
  TH1I* dis_nChargedCandidates = nullptr;
  TH1D* dis_eNeutralTD = nullptr;
  TH1D* dis_pChargedFrac = nullptr;
  TH1D* dis_pMuFrac = nullptr;

  TH2D* mu_ppt = nullptr;
  TH1D* mu_p = nullptr;
  TH1D* mu_pt = nullptr;
  TH1I* mu_ndis = nullptr;
  TH1D* mu_wdis = nullptr;
};

class MuDISFilter {
 public:
  /** default constructor **/
  MuDISFilter();

  /** destructor **/
  ~MuDISFilter();
  MuDISFilter(const MuDISFilter&) = delete;
  MuDISFilter& operator=(const MuDISFilter&) = delete;

  // Generic filter on daughter particles
  using Filter = std::function<bool(const std::vector<DISparticle>&)>;
  void SetFilter(Filter filter) { fFilter = std::move(filter); }
  void SetFilterOption(unsigned option);
  unsigned GetFilterOption() const { return fFilterOption; }
  // for default filter
  void SetMinChargedDaughters(unsigned minimum) {
    fMinChargedDaughters = minimum;
  }
  void SetIncludeMuons(bool include) { fIncludeMuons = include; }
  void SetDetectorAcceptance(
      ShipBFieldMap* field, TGeoManager* geometry,
      double z = std::numeric_limits<double>::quiet_NaN(),
      ShipBFieldMap* muonShieldField = nullptr);
  void SetUseDetectorAcceptance(bool enabled) {
    fUseDetectorAcceptance = enabled;
  }
  void SetUsePythiaDecays(bool enabled);
  void SetPythiaDecaySeed(unsigned seed);
  void SetFilterEfficiencyBinning(double xmin, double xmax, unsigned xbins,
                                  double ymin, double ymax, unsigned ybins,
                                  double zmin, double zmax, unsigned zbins);
  void SetDetailedHistograms(bool enabled) { fDetailedHistograms = enabled; }
  double GetDetectorZ() const { return fDetectorZ; }

  bool PassFilter(const std::vector<DISparticle>& daughters) const;
  bool PassFilter(const std::vector<DISparticle>& daughters,
                  const TVector3& vertex) const;

  Histograms BookHistograms(TDirectory* dir, const TString& mat,
                            const TString& label = "");
  void init(const int& aEvts, const int& aStart);

  bool InitFile(const char*, int);
  bool InitFile(const char*);
  bool InitFiles(const std::vector<std::string>&, int);
  bool InitFiles(const std::vector<std::string>&);
  void process_file(const std::string& input, const std::string& output);
  void process_file(const std::vector<std::string>& input,
                    const std::string& output);
  void initEvent();
  void ProcessEvents();

 private:
  struct FilterCandidate {
    DISparticle particle;
    TVector3 vertex;
  };

  void ConfigureFilterGeometry(unsigned option,
                               const MagneticTrackPropagator& propagator);
  void InitialisePythiaDecayer();
  std::vector<FilterCandidate> DecayDaughters(
      const std::vector<DISparticle>& daughters, const TVector3& vertex) const;
  bool PassCandidates(const std::vector<FilterCandidate>& candidates) const;
  bool PassDetectorFilter(const std::vector<FilterCandidate>& candidates) const;
  bool HitsTimingDetector(const FilterCandidate& candidate) const;
  bool HitsTrackingAndTD(double charge, const DISparticle& particle,
                         const TVector3& vertex) const;
  bool IsCharged(const DISparticle& particle) const;
  double Charge(const DISparticle& particle) const;
  int DaughterCategory(const DISparticle& particle) const;
  void FillDIS(Histograms& h, const ShipMuDIS::MuonDISInBranches& br, int idis,
               const std::vector<DISparticle>& daughters,
               const std::vector<FilterCandidate>& candidates,
               Histograms* filtered);
  static constexpr unsigned kMomentumBins = 4;
  static constexpr unsigned kPtBins = 5;
  static constexpr unsigned kEfficiencyMaterials =
      ShipMuDIS::nMats - 1;  // Exclude REST.
  using EfficiencyMaps =
      std::array<std::array<std::array<TH2D*, kEfficiencyMaterials>, kPtBins>,
                 kMomentumBins>;
  using EfficiencyZHistograms = std::array<
      std::array<
          std::vector<std::vector<std::array<TH1D*, kEfficiencyMaterials>>>,
          kPtBins>,
      kMomentumBins>;
  struct FilterEfficiencyHistograms {
    EfficiencyMaps allXY = {};
    EfficiencyMaps passedXY = {};
    EfficiencyZHistograms allZ = {};
    EfficiencyZHistograms passedZ = {};
  };
  void BookFilterEfficiencyHistograms(TDirectory* dir);
  void FillFilterEfficiencyHistograms(unsigned material, double momentum,
                                      double pt, double x, double y, double z,
                                      double weight, bool passed);
  unsigned fMinChargedDaughters = 2;
  unsigned fFilterOption = 0;
  std::array<std::array<double, 4>, 5> fStationXY = {};
  std::array<double, 4> fTimingDetectorXY = {};
  std::array<double, 5> fStationZ = {};  //! Tr1, Tr2, Tr3, Tr4, TD plane
  std::pair<double, double> fDetectorVolumeZ = {0., 0.};
  bool fIncludeMuons = true;
  bool fUseDetectorAcceptance = true;
  double fDetectorZ = std::numeric_limits<double>::quiet_NaN();
  double fTr1Z = std::numeric_limits<double>::quiet_NaN();
  double fTimingDetectorZ = std::numeric_limits<double>::quiet_NaN();
  bool fUsePythiaDecays = false;
  unsigned fPythiaDecaySeed = 0;
  mutable std::unique_ptr<Pythia8::Pythia> fPythiaDecayer;  //! Runtime decayer
  std::unique_ptr<MagneticTrackPropagator> fPropagator;  //! Runtime transport
  Filter fFilter;  //! User-supplied runtime predicate
  TChain* ftree;
  ShipMuDIS::MuonInBranches finEv;

  TTree* fouttree;
  ShipMuDIS::MuonBranches foutEv;

  int fnEvts;
  int fstartEvt;

  TDatabasePDG* fPDG;
  Histograms hist_all[ShipMuDIS::nMats];
  Histograms hist_filt[ShipMuDIS::nMats];
  FilterEfficiencyHistograms fFilterEfficiency;
  bool fDetailedHistograms = false;
  std::array<double, 4> fEfficiencyXYBounds = {-200., 200., -300., 300.};
  unsigned fEfficiencyXBins = 5;
  unsigned fEfficiencyYBins = 5;
  std::array<double, 2> fEfficiencyZBounds = {2500., 9500.};
  unsigned fEfficiencyZBins = 70;
};

#endif  // NEWMUONDIS_MUDISFILTER_H_
