// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#include "ShipRunConfiguration.h"

#include "exitHadronAbsorber.h"

void ShipSteppingAction::SteppingAction(const G4Step* step) {
  exitHadronAbsorber::SplitStepHook(step);
}

TG4SteppingAction* ShipRunConfiguration::CreateSteppingAction() {
  return new ShipSteppingAction();
}
