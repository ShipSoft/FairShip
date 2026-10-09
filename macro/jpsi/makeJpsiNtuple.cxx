// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration
//
// makeJpsiNtuple: writes a sample of the data-driven J/psi generator
// (JpsiSampler) to a ROOT ntuple, with a weight column and the normalisation
// as TParameter<double>. It makes the map base that macro/jpsi/JpsiDataMap.C
// fits the data map on (see macro/jpsi/README.md), and standalone samples for
// comparisons. FairShip itself does not need it: JpsiGenerator calls the
// sampler directly. Built with FairShip as build/bin/makeJpsiNtuple.
//
// Weights: w = nPot * rate / nEvents (the sample stands for nPot protons;
// divide by the stored n_pot for per-POT values). Rows: id px py pz E M mid
// mpx mpy mpz mE w vz, two rows (mu+, mu-) per J/psi with the J/psi as the
// mother, or one row per J/psi with --output jpsi.
//
// Examples:
//   makeJpsiNtuple -n 4000000 --layers <target file> --config base.cfg
//       --mu-pmin 20 --mu-thmax 0.1 --map-base --out gen_mapbase.root
//       the base JpsiDataMap.C fits the map on (NA50 shape, no correction;
//       base.cfg sets the p_T model the map is meant for, e.g. pt_sq_slope)
//   makeJpsiNtuple -n 2000000 --layers <target file> --nominal --out nom.root
//       the configuration FairShip uses by default (SHiP Table 5 shape)
//   makeJpsiNtuple -n 2000000 --nominal --config my_variation.cfg --out v.root
//       the same key-value file as run_fixedTarget.py --jpsi-config
//   makeJpsiNtuple -n 2000000 --layers <target file> --data-map map.txt
//       a map from a JpsiDataMap.C output file
// --mu-pmin / --mu-thmax keep only J/psi whose two muons pass (lab frame);
// n_tried and n_written are stored for the normalisation.

#include <cmath>
#include <cstdint>
#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>

#include "JpsiSampler.h"
#include "TFile.h"
#include "TH2D.h"
#include "TNamed.h"
#include "TNtuple.h"
#include "TParameter.h"

namespace {
int Run(int argc, char** argv) {
  // --nominal starts from FairShip's default configuration, whatever its
  // position; the other options act on top of it
  bool nominal = false;
  for (int i = 1; i < argc; ++i) nominal |= std::string(argv[i]) == "--nominal";
  jpsi::Config cfg = nominal ? jpsi::NominalConfig() : jpsi::Config();
  cfg.ptSq = 1.9;
  // ntuple convention: w = nPot * rate / nEvents
  cfg.physicsWeight = false;
  std::string out = "jpsi_W_400GeV.root";
  bool writeMuons = true;
  // optional pre-selection of both muons (lab frame)
  double muPMin = 0.;
  double muThMax = 10.;
  std::string layersFile;
  std::string mapFile;

  for (int i = 1; i < argc; ++i) {
    const std::string a = argv[i];
    auto next = [&]() {
      if (i + 1 >= argc) throw std::invalid_argument("missing value for " + a);
      return std::string(argv[++i]);
    };
    try {
      if (a == "--nominal") {
        continue;
      } else if (a == "-n" || a == "--nevents") {
        cfg.nEvents = std::stoll(next());
        cfg.enhancement = -1;
      } else if (a == "--enhancement") {
        cfg.enhancement = std::stod(next());
      } else if (a == "--pot") {
        cfg.nPot = std::stod(next());
      } else if (a == "--ptsq") {
        cfg.ptSq = std::stod(next());
      } else if (a == "--fhard") {
        cfg.fHard = std::stod(next());
        cfg.ptSq = -1;
      } else if (a == "--shape") {
        const std::string s = next();
        if (s != "gauss" && s != "data")
          throw std::invalid_argument("shape is data or gauss");
        cfg.yShape = s == "gauss" ? jpsi::YShape::Gauss : jpsi::YShape::Data;
      } else if (a == "--tail") {
        cfg.tailN = std::stod(next());
      } else if (a == "--layers") {
        layersFile = next();
        cfg.layers = jpsi::LoadLayers(layersFile, &cfg.zStart_cm);
      } else if (a == "--data-hi") {
        cfg.dataHi = std::stod(next());
      } else if (a == "--data-map") {
        // a map file written by JpsiDataMap.C
        mapFile = next();
        jpsi::SetDataMap(cfg, jpsi::LoadDataMap(mapFile));
      } else if (a == "--config") {
        // key-value overrides, as run_fixedTarget.py --jpsi-config
        jpsi::ApplyConfigFile(cfg, next());
        if (cfg.dataMap.on) mapFile = cfg.dataMap.source;
        cfg.physicsWeight = false;
      } else if (a == "--map-base") {
        // the base JpsiDataMap.C fits on: NA50 shape, map with zero parameters
        cfg.dataMap = jpsi::DataMap();
        cfg.dataMap.on = true;
        cfg.dataMap.source = "map base (b1 = b2 = c = 0)";
        mapFile = "map base";
      } else if (a == "--data-lo") {
        cfg.dataLo = std::stod(next());
      } else if (a == "--secondary") {
        cfg.secondaryFactor = std::stod(next());
      } else if (a == "--lambda") {
        cfg.lambdaPol = std::stod(next());
      } else if (a == "--target") {
        const std::string t = next();
        cfg.target =
            (t == "Mo") ? jpsi::MolybdenumScaled() : jpsi::TungstenNA50();
      } else if (a == "--seed") {
        cfg.seed = std::stoull(next());
      } else if (a == "--output") {
        // "jpsi": inclusive, undecayed, weight 1/BR larger
        writeMuons = (next() != "jpsi");
      } else if (a == "--mu-pmin") {
        muPMin = std::stod(next());
      } else if (a == "--mu-thmax") {
        muThMax = std::stod(next());
      } else if (a == "--out") {
        out = next();
      } else {
        std::cerr << "unknown option " << a << "\n";
        return 1;
      }
    } catch (const std::exception& e) {
      std::cerr << "makeJpsiNtuple: " << a << ": " << e.what() << "\n";
      return 1;
    }
  }
  cfg.output = writeMuons ? jpsi::Output::MuMu : jpsi::Output::Jpsi;
  if (mapFile.empty())
    std::cout << "makeJpsiNtuple: no data map: SHiP Table 5 shape as published"
              << std::endl;

  std::unique_ptr<jpsi::Sampler> sp;
  try {
    sp = std::make_unique<jpsi::Sampler>(cfg);
  } catch (const std::exception& e) {
    std::cerr << e.what() << std::endl;
    return 1;
  }
  jpsi::Sampler& sampler = *sp;
  std::cout << sampler.Summary() << std::endl;
  const int64_t nEvents = sampler.NEvents();

  TFile f(out.c_str(), "RECREATE");
  TNtuple nt("jpsi", "data-driven J/psi, p-W 400 GeV",
             "id:px:py:pz:E:M:mid:mpx:mpy:mpz:mE:w:vz");  // vz: production z
                                                          // [cm] (layers only)
  const double eBeam = std::hypot(cfg.pBeam, jpsi::kMProton);

  auto F = [](double v) { return static_cast<float>(v); };
  auto accepted = [&](const ROOT::Math::PxPyPzEVector& m) {
    return m.P() > muPMin && std::atan2(m.Pt(), m.Pz()) < muThMax;
  };
  int64_t nWritten = 0;
  // every generated J/psi, before any pre-selection: the denominator of an
  // efficiency
  TH2D hYPt("h_gen_ypt", "generated J/#psi;y_{cm};p_{T} [GeV]", 88, -2.2, 2.2,
            120, 0., 6.);
  TH2D hPzPt("h_gen_pzpt", "generated J/#psi;p_{z} [GeV];p_{T} [GeV]", 80, 0.,
             400., 120, 0., 6.);
  for (int64_t i = 0; i < nEvents; ++i) {
    jpsi::Event ev = sampler.Next();
    if (ev.weight <= 0) continue;
    hYPt.Fill(ev.yCM, ev.jpsi.Pt());
    hPzPt.Fill(ev.jpsi.Pz(), ev.jpsi.Pt());
    if (writeMuons && ev.hasDimuon && !(accepted(ev.mup) && accepted(ev.mum)))
      continue;
    ++nWritten;
    if (writeMuons && ev.hasDimuon) {
      const float row1[13] = {-13,
                              F(ev.mup.Px()),
                              F(ev.mup.Py()),
                              F(ev.mup.Pz()),
                              F(ev.mup.E()),
                              F(jpsi::kMMu),
                              443,
                              F(ev.jpsi.Px()),
                              F(ev.jpsi.Py()),
                              F(ev.jpsi.Pz()),
                              F(ev.jpsi.E()),
                              F(ev.weight),
                              F(ev.z_cm)};
      const float row2[13] = {13,
                              F(ev.mum.Px()),
                              F(ev.mum.Py()),
                              F(ev.mum.Pz()),
                              F(ev.mum.E()),
                              F(jpsi::kMMu),
                              443,
                              F(ev.jpsi.Px()),
                              F(ev.jpsi.Py()),
                              F(ev.jpsi.Pz()),
                              F(ev.jpsi.E()),
                              F(ev.weight),
                              F(ev.z_cm)};
      nt.Fill(row1);
      nt.Fill(row2);
    } else {
      const float row[13] = {443,
                             F(ev.jpsi.Px()),
                             F(ev.jpsi.Py()),
                             F(ev.jpsi.Pz()),
                             F(ev.jpsi.E()),
                             F(jpsi::kMJpsi),
                             2212,
                             0.f,
                             0.f,
                             F(cfg.pBeam),
                             F(eBeam),
                             F(ev.weight),
                             F(ev.z_cm)};
      nt.Fill(row);
    }
  }
  nt.Write();
  hYPt.Write();
  hPzPt.Write();
  // every generated event counts in the normalisation, written or not
  TParameter<double>("n_tried", static_cast<double>(nEvents)).Write();
  TParameter<double>("n_written", static_cast<double>(nWritten)).Write();
  TParameter<double>("mu_pmin", muPMin).Write();
  TParameter<double>("mu_thmax", muThMax).Write();

  for (const auto& kv : sampler.Metadata()) {
    TParameter<double>(kv.first.c_str(), kv.second).Write();
  }
  TNamed("layers_file", layersFile.empty()
                            ? "none (thin target, per interacting proton)"
                            : layersFile.c_str())
      .Write();
  TNamed("data_map_file",
         mapFile.empty() ? "none (SHiP table shape)" : mapFile.c_str())
      .Write();
  TNamed("reference",
         mapFile.empty()
             ? "NA50 EPJ C48 (2006) 329 normalisation; shape NA50 and SHiP "
               "Table 5 (arXiv:2604.03661)"
             : "NA50 EPJ C48 (2006) 329 normalisation; shape NA50 and SHiP "
               "Table 5 (arXiv:2604.03661), corrected with the data map")
      .Write();
  f.Close();
  std::cout << "wrote " << out << ": " << nWritten << " of " << nEvents
            << " events" << std::endl;
  return 0;
}
}  // namespace

int main(int argc, char** argv) {
  try {
    return Run(argc, argv);
  } catch (const std::exception& e) {
    std::cerr << "makeJpsiNtuple: " << e.what() << std::endl;
  } catch (...) {
    std::cerr << "makeJpsiNtuple: unknown error" << std::endl;
  }
  return 1;
}
