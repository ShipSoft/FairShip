# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

ship_add_library(
  NAME splitcal
  SOURCES splitcal.cxx splitcalContFact.cxx splitcalPoint.cxx splitcalHit.cxx
          splitcalCluster.cxx
  LINKDEF LinkDef.h
  DEPENDENCIES Base ShipData FairLogger::FairLogger
)
