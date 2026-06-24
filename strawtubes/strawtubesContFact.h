// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#ifndef STRAWTUBES_STRAWTUBESCONTFACT_H_
#define STRAWTUBES_STRAWTUBESCONTFACT_H_

#include "FairContFact.h"

class FairContainer;

class strawtubesContFact : public FairContFact {
 private:
  void setAllContainers();

 public:
  strawtubesContFact();
  ~strawtubesContFact() override = default;
  FairParSet* createContainer(FairContainer*) override;
  ClassDefOverride(strawtubesContFact,
                   0)  // Factory for all strawtubes parameter containers
};

#endif  // STRAWTUBES_STRAWTUBESCONTFACT_H_
