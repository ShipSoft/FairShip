# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

ship_add_library(
  NAME CaloScoringPlane
  SOURCES
    CaloScoringPlane.cxx
    CaloScoringPlanePoint.cxx
    CaloScoringPlaneHit.cxx
    CaloScoringPlanePID.cxx
  LINKDEF LinkDef.h
  EXTRA_DICT_HEADERS ${CMAKE_SOURCE_DIR}/Detector/Detector.h
  DEPENDENCIES
    Base
    ShipData
    EG
    FairLogger::FairLogger
    Detector
    ${SHIP_YAML_CPP_TARGET}
)
