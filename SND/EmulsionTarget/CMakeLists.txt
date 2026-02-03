# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

ship_add_library(
  NAME EmulsionTarget
  SOURCES Target.cxx TargetPoint.cxx TargetTracker.cxx TTPoint.cxx
  LINKDEF EmulsionTargetLinkDef.h
  DEPENDENCIES Base ShipData GeoBase ParBase Geom Core FairLogger::FairLogger
)
