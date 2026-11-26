// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#include "Generator.h"

#include "ShipStack.h"
#include "TVirtualMC.h"

SHiP::Generator::~Generator() = default;

void SHiP::Generator::KeepLastTrack() {
  auto* mc = TVirtualMC::GetMC();
  auto* stack = mc ? dynamic_cast<ShipStack*>(mc->GetStack()) : nullptr;
  if (!stack) {
    LOG(warning) << "Generator::KeepLastTrack: no ShipStack, track not kept";
    return;
  }
  stack->KeepTrack(stack->GetNtrack() - 1);
}
