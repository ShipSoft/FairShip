# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN on behalf of the SHiP Collaboration

# Create a library called "SiliconTarget" which includes the source files given in
# the array . The extension is already found.  Any number of sources could be
# listed here.

set(INCLUDE_DIRECTORIES
    ${BASE_INCLUDE_DIRECTORIES} ${CMAKE_SOURCE_DIR}/shipdata
    ${CMAKE_SOURCE_DIR}/SND/SiliconTarget ${VMC_INCLUDE_DIRS} ${genfit2_INCDIR})

include_directories(${INCLUDE_DIRECTORIES} ${FAIRROOT_INCLUDE_DIR})
include_directories(SYSTEM ${SYSTEM_INCLUDE_DIRECTORIES})

set(LINK_DIRECTORIES ${ROOT_LIBRARY_DIR} ${FAIRROOT_LIBRARY_DIR}
                     ${genfit2_LIBDIR})

link_directories(${LINK_DIRECTORIES})

set(SRCS SiliconTarget.cxx SiliconTargetPoint.cxx SiliconTargetHit.cxx)

set(HEADERS)
set(LINKDEF SiliconTargetLinkDef.h)
set(LIBRARY_NAME SiliconTarget)
set(DEPENDENCIES
    Base
    ShipData
    GeoBase
    ParBase
    Geom
    Core
    FairLogger::FairLogger)

generate_library()
