# SPDX-License-Identifier: LGPL-3.0-only
# SPDX-FileCopyrightText: Copyright (C) 2014 GSI Helmholtzzentrum fuer Schwerionenforschung GmbH

 ################################################################################
 #    Copyright (C) 2014 GSI Helmholtzzentrum fuer Schwerionenforschung GmbH    #
 #                                                                              #
 #              This software is distributed under the terms of the             #
 #         GNU Lesser General Public Licence version 3 (LGPL) version 3,        #
 #                  copied verbatim in the file "LICENSE"                       #
 ################################################################################
# - Try to find EvtGen installation
# Once done this will define:
#   EVTGEN_FOUND - system has EvtGen
#   EVTGEN_INCLUDE_DIR - the EvtGen include directory
#   EVTGEN_LIBRARY_DIR - the EvtGen library directory
#   EVTGENDATA - path to EvtGen data files
#
# And creates the following imported targets:
#   EvtGen - the core EvtGen library
#   EvtGenExternal - the EvtGen external interfaces library

MESSAGE(STATUS "Looking for EvtGen ...")

# First try CONFIG mode (for modern EvtGen installations with CMake config files)
find_package(EvtGen CONFIG QUIET)

if(EvtGen_FOUND)
  MESSAGE(STATUS "Looking for EvtGen... - found via CONFIG mode")
  # Modern installation provides targets, but ensure backwards compat
  if(TARGET EvtGen::EvtGen)
    get_target_property(EVTGEN_INCLUDE_DIR EvtGen::EvtGen INTERFACE_INCLUDE_DIRECTORIES)
    get_target_property(_evtgen_location EvtGen::EvtGen IMPORTED_LOCATION)
    if(_evtgen_location)
      get_filename_component(EVTGEN_LIBRARY_DIR "${_evtgen_location}" DIRECTORY)
    endif()
  endif()

  # Alias targets without namespace for backward compatibility
  if(TARGET EvtGen::EvtGen AND NOT TARGET EvtGen)
    add_library(EvtGen ALIAS EvtGen::EvtGen)
  endif()
  if(TARGET EvtGen::EvtGenExternal AND NOT TARGET EvtGenExternal)
    add_library(EvtGenExternal ALIAS EvtGen::EvtGenExternal)
  endif()

  return()
endif()

# Fallback: MODULE mode for installations without CMake config files
# Use EVTGEN_ROOT environment variable (standard package location hint)
if(DEFINED ENV{EVTGEN_ROOT})
  set(EVTGEN_ROOT_HINT $ENV{EVTGEN_ROOT})
elseif(DEFINED EVTGEN_ROOT)
  set(EVTGEN_ROOT_HINT ${EVTGEN_ROOT})
endif()

FIND_PATH(EVTGEN_INCLUDE_DIR NAMES EvtGen/EvtGen.hh
  HINTS ${EVTGEN_ROOT_HINT}
  PATH_SUFFIXES include include/EvtGen
)

FIND_PATH(EVTGEN_LIBRARY_DIR NAMES libEvtGen.so libEvtGen.dylib
  HINTS ${EVTGEN_ROOT_HINT}
  PATH_SUFFIXES lib lib64
)

# Try to find data directory - check both EVTGEN_ROOT and EVTGENDATA env vars
if(DEFINED ENV{EVTGENDATA})
  set(EVTGENDATA $ENV{EVTGENDATA})
else()
  Find_Path(EVTGENDATA NAMES evt.pdl
    HINTS ${EVTGEN_ROOT_HINT}
    PATH_SUFFIXES share/EvtGen share
  )
endif()

If (NOT EVTGENDATA)
  Message(STATUS "Could not find EvtGen data files")
EndIf()

if (EVTGEN_INCLUDE_DIR AND EVTGEN_LIBRARY_DIR)
   set(EVTGEN_FOUND TRUE)
endif (EVTGEN_INCLUDE_DIR AND EVTGEN_LIBRARY_DIR)

if (EVTGEN_FOUND)
  if (NOT EVTGEN_FOUND_QUIETLY)
    MESSAGE(STATUS "Looking for EVTGEN... - found ${EVTGEN_LIBRARY_DIR}")
    SET(LD_LIBRARY_PATH ${LD_LIBRARY_PATH} ${EVTGEN_LIBRARY_DIR})
  endif (NOT EVTGEN_FOUND_QUIETLY)

  # Create imported target for EvtGen core library
  if(NOT TARGET EvtGen)
    add_library(EvtGen SHARED IMPORTED)
    set_target_properties(EvtGen PROPERTIES
      IMPORTED_LOCATION "${EVTGEN_LIBRARY_DIR}/libEvtGen${CMAKE_SHARED_LIBRARY_SUFFIX}"
      INTERFACE_INCLUDE_DIRECTORIES "${EVTGEN_INCLUDE_DIR};${EVTGEN_INCLUDE_DIR}/.."
    )
  endif()

  # Create imported target for EvtGenExternal library
  if(NOT TARGET EvtGenExternal)
    # Check if the External library exists
    if(EXISTS "${EVTGEN_LIBRARY_DIR}/libEvtGenExternal${CMAKE_SHARED_LIBRARY_SUFFIX}")
      add_library(EvtGenExternal SHARED IMPORTED)
      set_target_properties(EvtGenExternal PROPERTIES
        IMPORTED_LOCATION "${EVTGEN_LIBRARY_DIR}/libEvtGenExternal${CMAKE_SHARED_LIBRARY_SUFFIX}"
        INTERFACE_INCLUDE_DIRECTORIES "${EVTGEN_INCLUDE_DIR};${EVTGEN_INCLUDE_DIR}/.."
        INTERFACE_LINK_LIBRARIES "EvtGen"
      )
    else()
      MESSAGE(STATUS "EvtGenExternal library not found - may be older EvtGen version")
      # Create interface target that just depends on EvtGen for compatibility
      add_library(EvtGenExternal INTERFACE IMPORTED)
      set_target_properties(EvtGenExternal PROPERTIES
        INTERFACE_LINK_LIBRARIES "EvtGen"
      )
    endif()
  endif()

else (EVTGEN_FOUND)
  if (EVTGEN_FOUND_REQUIRED)
    message(FATAL_ERROR "Looking for EVTGEN... - Not found. Set EVTGEN_ROOT environment variable.")
  endif (EVTGEN_FOUND_REQUIRED)
endif (EVTGEN_FOUND)

# Mark variables as advanced
mark_as_advanced(EVTGEN_INCLUDE_DIR EVTGEN_LIBRARY_DIR EVTGENDATA)
