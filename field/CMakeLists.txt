# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

ship_add_library(
  NAME ShipField
  SOURCES ShipConstField.cxx ShipFieldCreator.cxx ShipFieldPar.cxx ShipBellField.cxx
          ShipBFieldMap.cxx ShipCompField.cxx ShipFieldMaker.cxx FairShipFields.cxx
  LINKDEF LinkDef.h
  DEPENDENCIES Base FairLogger::FairLogger genfit2
  INCLUDE_DIRECTORIES ${GEANT4_VMC_INCLUDE_DIR} ${GEANT4_INCLUDE_DIR}
)
