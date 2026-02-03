# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

ship_add_library(
  NAME veto
  SOURCES veto.cxx vetoContFact.cxx vetoPoint.cxx vetoHit.cxx vetoHitOnTrack.cxx
  LINKDEF LinkDef.h
  DEPENDENCIES Base ShipData FairLogger::FairLogger
)
