# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

# Determine the FairShip version from git (CalVer: year.month[.patch]) in
# FAIRSHIP_SOURCE_DIR. Sets FAIRSHIP_VERSION ("0.0.0" if unknown),
# FAIRSHIP_VERSION_TWEAK (commits since the tag, if any) and FAIRSHIP_GIT_HASH
# (with "-dirty" if tracked files have uncommitted changes, empty if unknown).
#
# A GitHub tarball (as built by the conda recipe) has no .git, but git archive
# has filled in .git_archival.txt (export-subst in .gitattributes).
#
# Used at configure time by CMakeLists.txt and at build time by
# cmake/scripts/WriteFairShipVersion.cmake.

set(FAIRSHIP_GIT_HASH "")
set(FAIRSHIP_GIT_DESCRIBE "")
set(FAIRSHIP_VERSION_TWEAK "")
set(GIT_DESCRIBE_RESULT 1)

if(NOT GIT_EXECUTABLE AND NOT CMAKE_SCRIPT_MODE_FILE)
    find_package(Git QUIET)
endif()
if(GIT_EXECUTABLE)
    execute_process(
        COMMAND ${GIT_EXECUTABLE} describe --tags --match "[0-9]*"
        WORKING_DIRECTORY ${FAIRSHIP_SOURCE_DIR}
        OUTPUT_VARIABLE FAIRSHIP_GIT_DESCRIBE
        OUTPUT_STRIP_TRAILING_WHITESPACE
        ERROR_QUIET
        RESULT_VARIABLE GIT_DESCRIBE_RESULT
    )
    execute_process(
        COMMAND ${GIT_EXECUTABLE} rev-parse HEAD
        WORKING_DIRECTORY ${FAIRSHIP_SOURCE_DIR}
        OUTPUT_VARIABLE FAIRSHIP_GIT_HASH
        OUTPUT_STRIP_TRAILING_WHITESPACE
        ERROR_QUIET
        RESULT_VARIABLE _rev_parse_result
    )
    if(_rev_parse_result EQUAL 0)
        execute_process(
            COMMAND ${GIT_EXECUTABLE} status --porcelain --untracked-files=no
            WORKING_DIRECTORY ${FAIRSHIP_SOURCE_DIR}
            OUTPUT_VARIABLE _status
            ERROR_QUIET
            RESULT_VARIABLE _status_result
        )
        if(_status_result EQUAL 0 AND NOT _status STREQUAL "")
            string(APPEND FAIRSHIP_GIT_HASH "-dirty")
        endif()
    else()
        set(FAIRSHIP_GIT_HASH "")
    endif()
endif()

if(
    NOT GIT_DESCRIBE_RESULT EQUAL 0
    AND EXISTS "${FAIRSHIP_SOURCE_DIR}/.git_archival.txt"
)
    file(STRINGS "${FAIRSHIP_SOURCE_DIR}/.git_archival.txt" _archival)
    # Outside a git archive the lines still hold $Format:...$ and match nothing.
    foreach(_line IN LISTS _archival)
        if(_line MATCHES "^node: ([0-9a-f]+)$")
            set(FAIRSHIP_GIT_HASH "${CMAKE_MATCH_1}")
        elseif(_line MATCHES "^describe-name: ([0-9].*)$")
            set(FAIRSHIP_GIT_DESCRIBE "${CMAKE_MATCH_1}")
            set(GIT_DESCRIBE_RESULT 0)
        endif()
    endforeach()
endif()

if(GIT_DESCRIBE_RESULT EQUAL 0)
    # Parse: "26.05", "26.05.1", "26.05-12-gabcdef", or "26.05.1-3-gabcdef"
    string(
        REGEX MATCH "^[0-9]+\\.[0-9]+(\\.[0-9]+)?"
        FAIRSHIP_VERSION
        "${FAIRSHIP_GIT_DESCRIBE}"
    )
    if(FAIRSHIP_GIT_DESCRIBE MATCHES "^[0-9.]+-([0-9]+)-g")
        set(FAIRSHIP_VERSION_TWEAK "${CMAKE_MATCH_1}")
    endif()
else()
    set(FAIRSHIP_VERSION "0.0.0")
endif()
