// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

// The weight of cascade (charm/beauty) events must reproduce the p.o.t. of the
// cascade file: every event reads the two heavy-flavour hadrons of a pair.

#include <TFile.h>
#include <TH1F.h>
#include <TNtuple.h>

#include <cmath>
#include <cstdio>
#include <iostream>

#include "FixedTargetGenerator.h"

int main() {
  const char* fname = "test_cascade_weight.root";
  const int nPairs = 100;       // all primary, i.e. depth 1
  const double chicc = 2.0e-3;  // pairs per p.o.t.
  {
    TFile f(fname, "RECREATE");
    TNtuple nt("pythia6", "synthetic cascade",
               "id:px:py:pz:E:M:mid:mpx:mpy:mpz:mE:mM:k");
    TH1F h("2", "nr signal per cascade depth", 50, 0.5, 50.5);
    for (int i = 0; i < nPairs; ++i) {
      for (int sign : {1, -1}) {
        nt.Fill(421 * sign, 0., 0., 50., 50.035, 1.865, 2212, 0., 0., 400.,
                400.0011, 0.938272, 1);
        h.Fill(1);
      }
    }
    f.Write();
  }
  FixedTargetGenerator gen;
  gen.SetChicc(chicc);
  // process the whole file: nPairs events of one pair each
  if (!gen.InitForCharmOrBeauty(fname, nPairs, 5e13, 0)) {
    std::cerr << "InitForCharmOrBeauty failed" << std::endl;
    return 1;
  }
  const double expected = nPairs / chicc;  // p.o.t. of the whole file
  const double pot = gen.GetPotForCharm();
  std::remove(fname);
  if (std::abs(pot / expected - 1.) > 1e-9) {
    std::cerr << "p.o.t. equivalent " << pot << ", expected " << expected
              << std::endl;
    return 1;
  }
  return 0;
}
