// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#include "splitcalContFact.h"

#include <iostream>

#include "FairRuntimeDb.h"

splitcalContFact::splitcalContFact() : FairContFact() {
  /** Constructor (called when the library is loaded) */
  fName = "splitcalContFact";
  fTitle = "Factory for parameter containers in libsplitcal";
  setAllContainers();
  FairRuntimeDb::instance()->addContFactory(this);
}

void splitcalContFact::setAllContainers() {}

FairParSet* splitcalContFact::createContainer(FairContainer* c) {
  return nullptr;
}
