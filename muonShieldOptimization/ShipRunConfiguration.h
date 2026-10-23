// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#ifndef MUONSHIELDOPTIMIZATION_SHIPRUNCONFIGURATION_H_
#define MUONSHIELDOPTIMIZATION_SHIPRUNCONFIGURATION_H_

#include "TG4RunConfiguration.h"
#include "TG4SteppingAction.h"

class G4Step;

/// Stepping action that passes every Geant4 step to the per-step kaon/pion
/// splitting of exitHadronAbsorber.
///
/// FairRoot only calls a detector's ProcessHits() for steps it attributes to
/// one of the detector's sensitive volumes, and a step that ends on a volume
/// boundary is attributed to the volume after it. Whether a step was seen
/// therefore depended on how it ended: a decay inside a splitting volume was
/// seen, the same step running into an unregistered volume was not. Per-step
/// splitting is only unbiased if the decision to split a step does not depend
/// on whether the particle decays in it, so it runs from here instead, for
/// every step.
class ShipSteppingAction : public TG4SteppingAction {
 public:
  void SteppingAction(const G4Step* step) override;
};

/// Geant4 VMC run configuration installing ShipSteppingAction.
class ShipRunConfiguration : public TG4RunConfiguration {
 public:
  using TG4RunConfiguration::TG4RunConfiguration;
  TG4SteppingAction* CreateSteppingAction() override;
};

#endif  // MUONSHIELDOPTIMIZATION_SHIPRUNCONFIGURATION_H_
