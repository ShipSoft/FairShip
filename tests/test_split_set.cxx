// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

// The split set of a ShipMCTrack must default to "not split", survive copies
// and I/O, and read back as "not split" from files written before it existed.

#include <TClonesArray.h>
#include <TFile.h>
#include <TTree.h>

#include <cstdio>
#include <iostream>
#include <memory>

#include "ShipMCTrack.h"

namespace {

int failures = 0;

void Check(bool ok, const char* what) {
  if (!ok) {
    std::cerr << "FAIL " << what << std::endl;
    ++failures;
  }
}

}  // namespace

int main(int argc, char** argv) {
  ShipMCTrack plain;
  Check(plain.GetSplitSet() == -1, "default split set");
  Check(plain.GetSplitRole() == ShipMCTrack::kNotSplit, "default split role");
  Check(!plain.IsSplitDecay() && !plain.IsSplitSurvivor(), "default flags");

  ShipMCTrack clone(321, 0, 0., 0., 50., 50.002, 0., 0., 10., 0.3, 0, 0, 7,
                    0.25);
  Check(clone.GetSplitSet() == -1, "standard constructor split set");
  clone.SetSplitSet(3, ShipMCTrack::kSplitDecay, 0.5);
  Check(clone.IsSplitDecay() && !clone.IsSplitSurvivor(), "decay role");
  const ShipMCTrack copy(clone);
  Check(copy.GetSplitSet() == 3 && copy.IsSplitDecay() &&
            copy.GetSplitWeight() == 0.5,
        "copy keeps split set");

  // Round trip through a file.
  const char* fname = "test_split_set.root";
  {
    TFile f(fname, "RECREATE");
    ShipMCTrack survivor(clone);
    survivor.SetSplitSet(3, ShipMCTrack::kSplitSurvivor, 0.5);
    f.WriteObject(&clone, "clone");
    f.WriteObject(&survivor, "survivor");
  }
  {
    TFile f(fname);
    std::unique_ptr<ShipMCTrack> c(f.Get<ShipMCTrack>("clone"));
    std::unique_ptr<ShipMCTrack> s(f.Get<ShipMCTrack>("survivor"));
    Check(c && c->GetSplitSet() == 3 && c->IsSplitDecay() &&
              c->GetSplitWeight() == 0.5,
          "read back clone");
    Check(s && s->GetSplitSet() == 3 && s->IsSplitSurvivor(),
          "read back survivor");
  }
  std::remove(fname);

  // A file written before the split set existed (ShipMCTrack version 9).
  if (argc > 1) {
    TFile f(argv[1]);
    auto* tree = f.Get<TTree>("cbmsim");
    Check(tree != nullptr, "old file has cbmsim");
    if (tree) {
      // This file predates the move to std::vector: MCTrack is a TClonesArray.
      TClonesArray* tracks = nullptr;
      tree->SetBranchAddress("MCTrack", &tracks);
      Long64_t n = 0;
      bool allUnsplit = true;
      for (Long64_t i = 0; i < tree->GetEntries(); ++i) {
        tree->GetEntry(i);
        for (Int_t j = 0; tracks && j < tracks->GetEntriesFast(); ++j) {
          const auto* t = dynamic_cast<const ShipMCTrack*>(tracks->At(j));
          if (!t) continue;
          ++n;
          allUnsplit &= t->GetSplitSet() == -1 &&
                        t->GetSplitRole() == ShipMCTrack::kNotSplit;
        }
      }
      Check(n > 0, "old file has tracks");
      Check(allUnsplit, "old tracks read back as not split");
      tree->ResetBranchAddresses();
      delete tracks;
    }
  }

  if (failures) {
    std::cerr << failures << " check(s) failed" << std::endl;
    return 1;
  }
  return 0;
}
