# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

find_package(Python3 COMPONENTS Development REQUIRED)

ship_add_library(
  NAME ShipMuonShieldBackground
  SOURCES exitHadronAbsorber.cxx pyFairModule.cxx
  LINKDEF LinkDef.h
  DEPENDENCIES Base veto ShipData GeoBase ParBase Geom Core FairLogger::FairLogger
  INCLUDE_DIRECTORIES ${Python3_INCLUDE_DIRS}
)
