# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

ship_add_library(
  NAME EmulsionTarget
  SOURCES Target.cxx TargetTracker.cxx
  LINKDEF EmulsionTargetLinkDef.h
  EXTRA_DICT_HEADERS ${CMAKE_SOURCE_DIR}/Detector/Detector.h
                     ${CMAKE_CURRENT_SOURCE_DIR}/TargetPoint.h
                     ${CMAKE_CURRENT_SOURCE_DIR}/TTPoint.h
  DEPENDENCIES Detector Base ShipData GeoBase ParBase Geom Core FairLogger::FairLogger
)
