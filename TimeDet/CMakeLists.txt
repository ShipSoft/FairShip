# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

ship_add_library(
  NAME TimeDet
  SOURCES TimeDetPoint.cxx TimeDetHit.cxx TimeDet.cxx
  LINKDEF LinkDef.h
  DEPENDENCIES Base ShipData FairLogger::FairLogger
)
