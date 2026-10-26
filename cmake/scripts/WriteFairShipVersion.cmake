# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

# Write FairShipVersion.h at build time, so the commit it records follows the
# source tree without re-running CMake. Run with cmake -P and
# -DFAIRSHIP_SOURCE_DIR, -DIN, -DOUT and -DGIT_EXECUTABLE. configure_file only
# touches OUT when its content changes.

include(${CMAKE_CURRENT_LIST_DIR}/../modules/FairShipGitVersion.cmake)

set(PROJECT_VERSION "${FAIRSHIP_VERSION}")
if(FAIRSHIP_VERSION_TWEAK)
    string(APPEND PROJECT_VERSION ".${FAIRSHIP_VERSION_TWEAK}")
endif()

configure_file(${IN} ${OUT} @ONLY)
