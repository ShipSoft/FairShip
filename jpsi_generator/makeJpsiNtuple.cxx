// SPDX-License-Identifier: LGPL-3.0-or-later
//
// Standalone writer: dumps a data-driven J/psi sample to a ROOT ntuple with an
// explicit per-particle weight column, plus the full normalisation metadata as
// TParameter<double>. The column layout follows the charm input for
// convenience, but the file is NOT a drop-in charm input: the charm reader does
// not know about the "w" column or the file-level metadata, so it needs the
// dedicated reader. For the direct FairShip integration this file is not needed
// at all - JpsiGenerator calls the sampler in place.
//
// Build (with ROOT in the environment):
//   g++ -O2 -std=c++17 makeJpsiNtuple.cxx JpsiSampler.cxx \
//       $(root-config --cflags --libs) -o makeJpsiNtuple
//
// Example:
//   ./makeJpsiNtuple -n 1000000 --ptsq 1.9 --shape data --out jpsi_W.root
//   ./makeJpsiNtuple --enhancement 1 --output jpsi   # realistic-rate sample

#include <cstdlib>
#include <cstring>
#include <iostream>
#include <string>

#include "JpsiSampler.h"
#include "TFile.h"
#include "TNamed.h"
#include "TNtuple.h"
#include "TParameter.h"

int main(int argc, char** argv) {
  jpsi::Config cfg;
  cfg.ptSq = 1.9;
  std::string out = "jpsi_W_400GeV.root";
  bool writeMuons = true;

  for (int i = 1; i < argc; ++i) {
    const std::string a = argv[i];
    auto next = [&]() { return std::string(argv[++i]); };
    if (a == "-n" || a == "--nevents") {
      cfg.nEvents = std::stol(next());
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
      cfg.yShape = s == "gauss"    ? jpsi::YShape::Gauss
                   : s == "hybrid" ? jpsi::YShape::Hybrid
                                   : jpsi::YShape::Data;
    } else if (a == "--tail") {
      cfg.tailN = std::stod(next());
    } else if (a == "--lambda") {
      cfg.lambdaPol = std::stod(next());
    } else if (a == "--target") {
      const std::string t = next();
      cfg.target = (t == "Mo") ? jpsi::MolybdenumScaled() : jpsi::TungstenNA50();
    } else if (a == "--seed") {
      cfg.seed = std::stoull(next());
    } else if (a == "--output") {
      writeMuons = (next() != "jpsi");  // "jpsi" = inclusive, 1/BR larger weight
    } else if (a == "--out") {
      out = next();
    } else {
      std::cerr << "unknown option " << a << "\n";
      return 1;
    }
  }
  cfg.output = writeMuons ? jpsi::Output::MuMu : jpsi::Output::Jpsi;

  jpsi::Sampler sampler(cfg);
  std::cout << sampler.Summary() << std::endl;
  const auto& n = sampler.GetNormalisation();
  const long nEvents = sampler.NEvents();

  TFile f(out.c_str(), "RECREATE");
  TNtuple nt("jpsi", "data-driven J/psi, p-W 400 GeV",
             "id:px:py:pz:E:M:mid:mpx:mpy:mpz:mE:w");
  const double eBeam = std::hypot(cfg.pBeam, jpsi::kMProton);

  for (long i = 0; i < nEvents; ++i) {
    jpsi::Event ev = sampler.Next();
    if (ev.weight <= 0) continue;
    if (writeMuons && ev.hasDimuon) {
      const float row1[12] = {-13,         float(ev.mup.px), float(ev.mup.py),
                              float(ev.mup.pz), float(ev.mup.E),  float(jpsi::kMMu),
                              443,         float(ev.jpsi.px), float(ev.jpsi.py),
                              float(ev.jpsi.pz), float(ev.jpsi.E), float(ev.weight)};
      const float row2[12] = {13,          float(ev.mum.px), float(ev.mum.py),
                              float(ev.mum.pz), float(ev.mum.E),  float(jpsi::kMMu),
                              443,         float(ev.jpsi.px), float(ev.jpsi.py),
                              float(ev.jpsi.pz), float(ev.jpsi.E), float(ev.weight)};
      nt.Fill(row1);
      nt.Fill(row2);
    } else {
      const float row[12] = {443,   float(ev.jpsi.px), float(ev.jpsi.py),
                             float(ev.jpsi.pz), float(ev.jpsi.E), float(jpsi::kMJpsi),
                             2212,  0.f,        0.f,
                             float(cfg.pBeam), float(eBeam), float(ev.weight)};
      nt.Fill(row);
    }
  }
  nt.Write();

  for (const auto& kv : sampler.Metadata()) {
    TParameter<double>(kv.first.c_str(), kv.second).Write();
  }
  (void)n;
  TNamed("reference",
         "NA50 EPJ C48 (2006) 329 normalisation; shape CERN-SHiP-ANA-2019-002 "
         "Table 2")
      .Write();
  f.Close();
  std::cout << "wrote " << out << " with " << nEvents << " events" << std::endl;
  return 0;
}
