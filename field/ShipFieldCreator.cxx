// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#include "ShipFieldCreator.h"

#include <iostream>

#include "FairField.h"
#include "FairRunAna.h"
#include "FairRuntimeDb.h"
#include "ShipConstField.h"
#include "ShipFieldPar.h"
using std::cerr;
using std::cout;
using std::endl;

static ShipFieldCreator gShipFieldCreator;

ShipFieldCreator::ShipFieldCreator() : FairFieldFactory(), fFieldPar(NULL) {}

ShipFieldCreator::~ShipFieldCreator() {}

void ShipFieldCreator::SetParm() {
  FairRunAna* Run = FairRunAna::Instance();
  FairRuntimeDb* RunDB = Run->GetRuntimeDb();
  fFieldPar = dynamic_cast<ShipFieldPar*>(RunDB->getContainer("ShipFieldPar"));
}

FairField* ShipFieldCreator::createFairField() {
  FairField* fMagneticField = 0;

  if (!fFieldPar) {
    cerr << "-E-  No field parameters available!" << endl;
  } else {
    // Instantiate correct field type
    Int_t fType = fFieldPar->GetType();
    if (fType == 0)
      fMagneticField = new ShipConstField(fFieldPar);
    else
      cerr << "-W- FairRunAna::GetField: Unknown field type " << fType << endl;
    cout << "New field at " << fMagneticField << ", type " << fType << endl;
    // Initialise field
    if (fMagneticField) {
      fMagneticField->Init();
      fMagneticField->Print("");
    }
  }
  return fMagneticField;
}
