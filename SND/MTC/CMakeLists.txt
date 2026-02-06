# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

ship_add_library(
  NAME MTCDetector
  SOURCES MTCDetector.cxx MTCDetPoint.cxx MTCDetHit.cxx
  LINKDEF MTCDetectorLinkDef.h
  DEPENDENCIES Base ShipData GeoBase ParBase Geom Core FairLogger::FairLogger
)
