# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN on behalf of the SHiP Collaboration

#[=======================================================================[.rst:
FindEvtGen
----------

Find EvtGen installation (both CMake and autotools-based versions).

This module will first try to find EvtGen via its CMake config files
(for newer CMake-based installations). If that fails, it will fall back
to searching for old autotools-based installations using the EVTGEN_ROOT
environment variable.

Imported Targets
^^^^^^^^^^^^^^^^

This module defines the following :prop_tgt:`IMPORTED` targets:

``EvtGen::EvtGen``
  The EvtGen library (libEvtGen.so)

``EvtGen::EvtGenExternal``
  The EvtGenExternal library (libEvtGenExternal.so)

Result Variables
^^^^^^^^^^^^^^^^

This module will set the following variables in your project:

``EvtGen_FOUND``
  True if EvtGen is found.

``EvtGen_INCLUDE_DIRS``
  Include directories needed to use EvtGen.

``EvtGen_LIBRARIES``
  Libraries needed to link to EvtGen.

``EvtGen_VERSION``
  The version of EvtGen found (if available).

Cache Variables
^^^^^^^^^^^^^^^

The following cache variables may also be set:

``EvtGen_INCLUDE_DIR``
  The directory containing EvtGen header files.

``EvtGen_LIBRARY``
  The path to the EvtGen library.

``EvtGen_External_LIBRARY``
  The path to the EvtGenExternal library.

Environment Variables
^^^^^^^^^^^^^^^^^^^^^

``EVTGEN_ROOT``
  Path to the EvtGen installation directory.

#]=======================================================================]

# First, try to find EvtGen via its CMake config files
# This works for modern CMake-based installations
find_package(EvtGen CONFIG QUIET)

if(EvtGen_FOUND)
  # Modern CMake config was found, we're done
  return()
endif()

# Fallback for old autotools-based installations
# These rely on EVTGEN_ROOT environment variable

# Use EVTGEN_ROOT environment variable as a hint
set(_EVTGEN_ROOT_HINTS)
if(DEFINED ENV{EVTGEN_ROOT})
  list(APPEND _EVTGEN_ROOT_HINTS "$ENV{EVTGEN_ROOT}")
endif()

# Find the include directory
find_path(EvtGen_INCLUDE_DIR
  NAMES EvtGen/EvtGen.hh
  HINTS ${_EVTGEN_ROOT_HINTS}
  PATH_SUFFIXES include
  DOC "Path to EvtGen include directory"
)

# Find the main EvtGen library
find_library(EvtGen_LIBRARY
  NAMES EvtGen
  HINTS ${_EVTGEN_ROOT_HINTS}
  PATH_SUFFIXES lib lib64
  DOC "Path to EvtGen library"
)

# Find the EvtGenExternal library
find_library(EvtGen_External_LIBRARY
  NAMES EvtGenExternal
  HINTS ${_EVTGEN_ROOT_HINTS}
  PATH_SUFFIXES lib lib64
  DOC "Path to EvtGenExternal library"
)

# Handle standard arguments (REQUIRED, QUIET, etc.)
include(FindPackageHandleStandardArgs)
find_package_handle_standard_args(EvtGen
  REQUIRED_VARS
    EvtGen_LIBRARY
    EvtGen_External_LIBRARY
    EvtGen_INCLUDE_DIR
  FAIL_MESSAGE
    "Could not find EvtGen. Please set EVTGEN_ROOT environment variable or ensure EvtGenConfig.cmake is in CMAKE_PREFIX_PATH."
)

if(EvtGen_FOUND)
  # Set output variables
  set(EvtGen_INCLUDE_DIRS "${EvtGen_INCLUDE_DIR}")
  set(EvtGen_LIBRARIES "${EvtGen_LIBRARY}" "${EvtGen_External_LIBRARY}")

  # Create imported target for EvtGenExternal (must be created first)
  if(NOT TARGET EvtGen::EvtGenExternal)
    add_library(EvtGen::EvtGenExternal UNKNOWN IMPORTED)
    set_target_properties(EvtGen::EvtGenExternal PROPERTIES
      IMPORTED_LOCATION "${EvtGen_External_LIBRARY}"
      INTERFACE_INCLUDE_DIRECTORIES "${EvtGen_INCLUDE_DIR}"
    )
  endif()

  # Create imported target for EvtGen
  if(NOT TARGET EvtGen::EvtGen)
    add_library(EvtGen::EvtGen UNKNOWN IMPORTED)
    set_target_properties(EvtGen::EvtGen PROPERTIES
      IMPORTED_LOCATION "${EvtGen_LIBRARY}"
      INTERFACE_INCLUDE_DIRECTORIES "${EvtGen_INCLUDE_DIR}"
      INTERFACE_LINK_LIBRARIES "EvtGen::EvtGenExternal"
    )
  endif()

  # Mark variables as advanced (don't show in CMake GUI unless "Advanced" is checked)
  mark_as_advanced(
    EvtGen_INCLUDE_DIR
    EvtGen_LIBRARY
    EvtGen_External_LIBRARY
  )
endif()
