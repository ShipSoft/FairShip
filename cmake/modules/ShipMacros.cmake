# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

#[=======================================================================[.rst:
ShipMacros
----------

Provides ``ship_add_library()`` — a modern, target-based replacement for
FairRoot's scope-variable-driven ``GENERATE_LIBRARY()`` macro.

.. command:: ship_add_library

  Create a shared library with ROOT dictionary generation and proper
  target-based include propagation::

    ship_add_library(
      NAME <target_name>
      SOURCES <src1> [<src2> ...]
      LINKDEF <linkdef_file>
      DEPENDENCIES <dep1> [<dep2> ...]
      [INCLUDE_DIRECTORIES <dir1> ...]
      [SYSTEM_INCLUDE_DIRECTORIES <dir1> ...]
    )

  ``NAME``
    Name of the library target to create.

  ``SOURCES``
    List of C++ source files (``.cxx``).  Headers are derived automatically
    by replacing ``.cxx`` with ``.h``.

  ``LINKDEF``
    Path to the ROOT LinkDef header (relative to ``CMAKE_CURRENT_SOURCE_DIR``
    or absolute).

  ``DEPENDENCIES``
    Link dependencies — target names, library file paths, or variable-based
    library names (looked up as ``${name}_LIBRARY``).

  ``INCLUDE_DIRECTORIES``
    Extra include directories needed only by this target (added as PRIVATE).

  ``SYSTEM_INCLUDE_DIRECTORIES``
    External include directories added as SYSTEM PRIVATE (suppresses warnings).

The current source directory is always added as a PUBLIC include directory
with a ``BUILD_INTERFACE`` / ``INSTALL_INTERFACE`` generator expression, so
dependents of the library automatically receive its include path.

#]=======================================================================]

function(ship_add_library)
  cmake_parse_arguments(
    PARSE_ARGV 0 ARG
    ""
    "NAME;LINKDEF"
    "SOURCES;DEPENDENCIES;INCLUDE_DIRECTORIES;SYSTEM_INCLUDE_DIRECTORIES"
  )

  if(NOT ARG_NAME)
    message(FATAL_ERROR "ship_add_library: NAME is required")
  endif()
  if(NOT ARG_SOURCES)
    message(FATAL_ERROR "ship_add_library(${ARG_NAME}): SOURCES is required")
  endif()

  # --- Derive headers from sources (.cxx -> .h) ---
  CHANGE_FILE_EXTENSION(*.cxx *.h _hdrs "${ARG_SOURCES}")
  install(FILES ${_hdrs} DESTINATION include)

  # --- Prepare scope variables for FairRoot's dictionary macros ---
  set(LIBRARY_NAME ${ARG_NAME})
  set(HDRS ${_hdrs})
  set(DICTIONARY ${CMAKE_CURRENT_BINARY_DIR}/G__${ARG_NAME}Dict.cxx)
  set(LIBRARY_OUTPUT_PATH ${CMAKE_BINARY_DIR}/lib)

  # Build INCLUDE_DIRECTORIES for rootcling: own source dir + extras +
  # source dirs of FairShip dependency targets.
  set(INCLUDE_DIRECTORIES
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${ARG_INCLUDE_DIRECTORIES}
  )
  set(SYSTEM_INCLUDE_DIRECTORIES ${ARG_SYSTEM_INCLUDE_DIRECTORIES})

  foreach(_dep IN LISTS ARG_DEPENDENCIES)
    if(TARGET ${_dep})
      get_target_property(_dep_src ${_dep} SOURCE_DIR)
      if(_dep_src)
        list(APPEND INCLUDE_DIRECTORIES ${_dep_src})
      endif()
    endif()
  endforeach()

  # --- Dictionary generation ---
  set(_all_srcs ${ARG_SOURCES})

  if(ARG_LINKDEF)
    if(IS_ABSOLUTE "${ARG_LINKDEF}")
      set(LINKDEF "${ARG_LINKDEF}")
    else()
      set(LINKDEF "${CMAKE_CURRENT_SOURCE_DIR}/${ARG_LINKDEF}")
    endif()

    if(COMMAND FAIRROOT_GENERATE_DICTIONARY)
      FAIRROOT_GENERATE_DICTIONARY()
    else()
      ROOT_GENERATE_DICTIONARY()
    endif()

    list(APPEND _all_srcs ${DICTIONARY})
    set_source_files_properties(${DICTIONARY} PROPERTIES
      COMPILE_FLAGS "-Wno-old-style-cast"
    )
  endif()

  # --- Resolve dependencies ---
  set(_resolved_deps)
  foreach(_dep IN LISTS ARG_DEPENDENCIES)
    get_filename_component(_ext "${_dep}" EXT)
    if(_ext)
      list(APPEND _resolved_deps ${_dep})
    elseif(TARGET ${_dep})
      list(APPEND _resolved_deps ${_dep})
    else()
      list(APPEND _resolved_deps ${${_dep}_LIBRARY})
    endif()
  endforeach()

  # --- Create library ---
  add_library(${ARG_NAME} SHARED ${_all_srcs})
  target_link_libraries(${ARG_NAME} ${_resolved_deps})
  set_target_properties(${ARG_NAME} PROPERTIES ${PROJECT_LIBRARY_PROPERTIES})

  # --- Target-based include propagation ---
  target_include_directories(${ARG_NAME}
    PUBLIC
      $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}>
      $<INSTALL_INTERFACE:include>
  )
  if(ARG_INCLUDE_DIRECTORIES)
    target_include_directories(${ARG_NAME} PRIVATE
      ${ARG_INCLUDE_DIRECTORIES}
    )
  endif()
  if(ARG_SYSTEM_INCLUDE_DIRECTORIES)
    target_include_directories(${ARG_NAME} SYSTEM PRIVATE
      ${ARG_SYSTEM_INCLUDE_DIRECTORIES}
    )
  endif()

  install(TARGETS ${ARG_NAME} DESTINATION lib)
endfunction()
