# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

ship_add_library(NAME SiliconTarget
  SOURCES SiliconTarget.cxx SiliconTargetPoint.cxx SiliconTargetHit.cxx
  LINKDEF SiliconTargetLinkDef.h
  EXTRA_DICT_HEADERS ${CMAKE_SOURCE_DIR}/Detector/Detector.h
  DEPENDENCIES Detector Base ShipData Detector GeoBase ParBase Geom Core FairLogger::FairLogger
)
