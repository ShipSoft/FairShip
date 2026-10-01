# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

ship_add_library(NAME MTCDetector
  SOURCES MTCDetector.cxx MTCDetHit.cxx
  LINKDEF MTCDetectorLinkDef.h
  EXTRA_DICT_HEADERS ${CMAKE_SOURCE_DIR}/Detector/Detector.h
                     ${CMAKE_CURRENT_SOURCE_DIR}/MTCDetPoint.h
  DEPENDENCIES Detector Base ShipData Detector GeoBase ParBase Geom Core FairLogger::FairLogger
)
