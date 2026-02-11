# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

#[=======================================================================[.rst:
Findgenfit2
-----------

Find GenFit installation (both fork and upstream versions).

This module will first try to find GenFit via its CMake config files
(for the fork olantwin/GenFit which provides genfit2Config.cmake).
If that fails, it will fall back to searching for upstream GenFit
installations using the GENFIT_ROOT and GENFIT environment variables.

Imported Targets
^^^^^^^^^^^^^^^^

This module defines the following :prop_tgt:`IMPORTED` target:

``genfit2``
  The GenFit library (libgenfit2.so)

Result Variables
^^^^^^^^^^^^^^^^

This module will set the following variables in your project:

``genfit2_FOUND``
  True if GenFit is found.

``genfit2_INCLUDE_DIRS``
  Include directories needed to use GenFit.

``genfit2_LIBRARIES``
  Libraries needed to link to GenFit.

Cache Variables
^^^^^^^^^^^^^^^

The following cache variables may also be set:

``genfit2_INCLUDE_DIR``
  The directory containing GenFit header files.

``genfit2_LIBRARY``
  The path to the GenFit library.

Environment Variables
^^^^^^^^^^^^^^^^^^^^^

``GENFIT_ROOT``
  Path to the GenFit installation directory.

``GENFIT``
  Alternative path to the GenFit installation directory.

#]=======================================================================]

# First, try to find GenFit via its CMake config files
# This works for the fork (olantwin/GenFit) which provides genfit2Config.cmake
find_package(genfit2 CONFIG QUIET)

if(genfit2_FOUND AND TARGET genfit2)
  # Modern CMake config was found and target exists, we're done
  return()
endif()

# Handle fork case: config found but no target created
# The fork's genfit2Config.cmake sets genfit2_INCDIR and genfit2_LIBDIR
if(genfit2_FOUND AND DEFINED genfit2_INCDIR AND DEFINED genfit2_LIBDIR)
  # Create the target using the config's variables
  if(NOT TARGET genfit2)
    add_library(genfit2 SHARED IMPORTED)
    set_target_properties(genfit2 PROPERTIES
      IMPORTED_LOCATION "${genfit2_LIBDIR}/${CMAKE_SHARED_LIBRARY_PREFIX}genfit2${CMAKE_SHARED_LIBRARY_SUFFIX}"
      INTERFACE_INCLUDE_DIRECTORIES "${genfit2_INCDIR}"
    )
  endif()
  # Set standard variables for consistency
  set(genfit2_INCLUDE_DIRS "${genfit2_INCDIR}")
  set(genfit2_LIBRARIES "${genfit2_LIBDIR}/${CMAKE_SHARED_LIBRARY_PREFIX}genfit2${CMAKE_SHARED_LIBRARY_SUFFIX}")
  return()
endif()

# Fallback for upstream GenFit installations
# These rely on GENFIT_ROOT or GENFIT environment variables

# Use GENFIT_ROOT and GENFIT environment variables as hints
set(_GENFIT_ROOT_HINTS)
if(DEFINED ENV{GENFIT_ROOT})
  list(APPEND _GENFIT_ROOT_HINTS "$ENV{GENFIT_ROOT}")
endif()
if(DEFINED ENV{GENFIT})
  list(APPEND _GENFIT_ROOT_HINTS "$ENV{GENFIT}")
endif()

# Find the include directory
find_path(genfit2_INCLUDE_DIR
  NAMES AbsTrackRep.h
  HINTS ${_GENFIT_ROOT_HINTS}
  PATH_SUFFIXES include
  DOC "Path to GenFit include directory"
)

# Find the GenFit library
find_library(genfit2_LIBRARY
  NAMES genfit2
  HINTS ${_GENFIT_ROOT_HINTS}
  PATH_SUFFIXES lib lib64
  DOC "Path to GenFit library"
)

# Handle standard arguments (REQUIRED, QUIET, etc.)
include(FindPackageHandleStandardArgs)
find_package_handle_standard_args(genfit2
  REQUIRED_VARS
    genfit2_LIBRARY
    genfit2_INCLUDE_DIR
  FAIL_MESSAGE
    "Could not find GenFit. Please set GENFIT_ROOT or GENFIT environment variable or ensure genfit2Config.cmake is in CMAKE_PREFIX_PATH."
)

if(genfit2_FOUND)
  # Set output variables
  set(genfit2_INCLUDE_DIRS "${genfit2_INCLUDE_DIR}")
  set(genfit2_LIBRARIES "${genfit2_LIBRARY}")

  # Create imported target if it doesn't exist
  if(NOT TARGET genfit2)
    add_library(genfit2 UNKNOWN IMPORTED)
    set_target_properties(genfit2 PROPERTIES
      IMPORTED_LOCATION "${genfit2_LIBRARY}"
      INTERFACE_INCLUDE_DIRECTORIES "${genfit2_INCLUDE_DIR}"
    )
  endif()

  # Mark variables as advanced (don't show in CMake GUI unless "Advanced" is checked)
  mark_as_advanced(
    genfit2_INCLUDE_DIR
    genfit2_LIBRARY
  )
endif()
