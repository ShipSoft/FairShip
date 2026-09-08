// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#include "Generator.h"

#include "TRandom.h"

SHiP::Generator::~Generator() = default;

void SHiP::Generator::SetSeed(UInt_t seed) {
  gRandom->SetSeed(seed);
  fSeed = gRandom->GetSeed();
}

UInt_t SHiP::Generator::GetSeed() const {
  return fSeed != 0 ? fSeed : gRandom->GetSeed();
}
