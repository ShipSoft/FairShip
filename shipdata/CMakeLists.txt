# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

ship_add_library(
  NAME ShipData
  SOURCES ShipHit.cxx ShipStack.cxx ShipMCTrack.cxx ShipParticle.cxx TrackInfo.cxx
  LINKDEF LinkDef.h
  DEPENDENCIES Base EG Physics Core genfit2 FairLogger::FairLogger
)
