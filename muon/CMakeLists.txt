# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

# Create a library called "libmuon" which includes the source files given in the
# array . The extension is already found.  Any number of sources could be listed
# here.

set(INCLUDE_DIRECTORIES ${CMAKE_CURRENT_SOURCE_DIR} ${genfit2_INCDIR}
                        ${VMC_INCLUDE_DIRS})

include_directories(${INCLUDE_DIRECTORIES} ${FAIRROOT_INCLUDE_DIR}
                    ${CMAKE_BINARY_DIR}/include)
include_directories(SYSTEM ${SYSTEM_INCLUDE_DIRECTORIES})

set(LINK_DIRECTORIES ${ROOT_LIBRARY_DIR} ${genfit2_LIBDIR}
                     ${FAIRROOT_LIBRARY_DIR})

link_directories(${LINK_DIRECTORIES})

set(SRCS # Put here your sourcefiles
    muon.cxx muonContFact.cxx muonPoint.cxx muonHit.cxx)

set(LINKDEF LinkDef.h)
set(LIBRARY_NAME muon)
set(DEPENDENCIES Base ShipData FairLogger::FairLogger)

generate_library()
