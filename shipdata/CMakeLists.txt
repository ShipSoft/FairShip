# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

ship_add_library(
  NAME ShipData
  SOURCES ShipStack.cxx ShipMCTrack.cxx ShipParticle.cxx TrackInfo.cxx
  LINKDEF LinkDef.h
  DEPENDENCIES Base EG Physics Core genfit2 FairLogger::FairLogger
  EXTRA_DICT_HEADERS ISTLPointContainer.h
)

# Header-only template included at runtime by eventDisplay.py via cling
install(FILES VectorMCPointSource.h DESTINATION ${CMAKE_INSTALL_INCLUDEDIR})
