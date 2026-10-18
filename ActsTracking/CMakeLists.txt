# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

# Only ActsStrawTracker goes through the dictionary; its header keeps ACTS
# behind a pointer, so rootcling never parses ACTS headers.
ship_add_library(
  NAME ShipActsTracking
  SOURCES ActsStrawTracker.cxx
  LINKDEF LinkDef.h
  DEPENDENCIES ShipData Geom Core
)
target_sources(ShipActsTracking PRIVATE ActsShipField.cpp ActsStrawGeometry.cpp)
target_link_libraries(ShipActsTracking PRIVATE Acts::Core ROOT::Geom)
