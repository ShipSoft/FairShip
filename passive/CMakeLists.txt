# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

ship_add_library(
  NAME ShipPassive
  SOURCES ShipCave.cxx ShipGeoCave.cxx ShipMagnet.cxx ShipTargetStation.cxx
          ShipMuonShield.cxx ShipPassiveContFact.cxx ShipTAUMagneticSpectrometer.cxx
  LINKDEF LinkDef.h
  DEPENDENCIES Base ShipData GeoBase ParBase Geom Core FairLogger::FairLogger
)
