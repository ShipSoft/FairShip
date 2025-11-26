# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

# Create a library called "libsplitcal" which includes the source files given in
# the array . The extension is already found.  Any number of sources could be
# listed here.

set(INCLUDE_DIRECTORIES ${CMAKE_CURRENT_SOURCE_DIR} ${genfit2_INCDIR})

include_directories(${INCLUDE_DIRECTORIES} ${VMC_INCLUDE_DIRS}
                    ${FAIRROOT_INCLUDE_DIR} ${CMAKE_BINARY_DIR}/include)
include_directories(SYSTEM ${SYSTEM_INCLUDE_DIRECTORIES})

set(LINK_DIRECTORIES ${ROOT_LIBRARY_DIR} ${FAIRROOT_LIBRARY_DIR}
                     ${genfit2_LIBDIR})

link_directories(${LINK_DIRECTORIES})

set(SRCS # Put here your sourcefiles
    splitcal.cxx splitcalContFact.cxx splitcalPoint.cxx splitcalHit.cxx
    splitcalCluster.cxx)

set(LINKDEF LinkDef.h)
set(LIBRARY_NAME splitcal)
set(DEPENDENCIES Base ShipData FairLogger::FairLogger)

generate_library()
