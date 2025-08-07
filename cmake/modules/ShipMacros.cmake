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
      [NO_DICT_SRCS <src1> ...]
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

  ``NO_DICT_SRCS``
    Source files compiled into the library but whose headers are NOT passed
    to rootcling for dictionary generation.  Useful when headers pull in
    external dependencies that rootcling cannot parse.

  ``LINKDEF``
    Path to the ROOT LinkDef header (relative to ``CMAKE_CURRENT_SOURCE_DIR``).

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

Dictionary generation invokes ROOT's rootcling directly and reads include
directories from target properties via generator expressions.

#]=======================================================================]

function(ship_add_library)
  cmake_parse_arguments(
    PARSE_ARGV 0 ARG
    ""
    "NAME;LINKDEF"
    "SOURCES;NO_DICT_SRCS;DEPENDENCIES;INCLUDE_DIRECTORIES;SYSTEM_INCLUDE_DIRECTORIES"
  )

  if(NOT ARG_NAME)
    message(FATAL_ERROR "ship_add_library: NAME is required")
  endif()
  if(NOT ARG_SOURCES)
    message(FATAL_ERROR "ship_add_library(${ARG_NAME}): SOURCES is required")
  endif()

  # --- Derive headers from sources (.cxx -> .h) ---
  CHANGE_FILE_EXTENSION(*.cxx *.h _hdrs "${ARG_SOURCES}")

  # --- Derive headers for NO_DICT_SRCS (not passed to rootcling) ---
  if(ARG_NO_DICT_SRCS)
    CHANGE_FILE_EXTENSION(*.cxx *.h _no_dict_hdrs "${ARG_NO_DICT_SRCS}")
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

  # --- Dictionary generation setup (before add_library) ---
  # We generate the dictionary using rootcling and add it to library sources
  # directly, similar to the old GENERATE_LIBRARY macro approach.
  set(_all_srcs ${ARG_SOURCES} ${ARG_NO_DICT_SRCS})
  if(ARG_LINKDEF)
    set(_dict_basename G__${ARG_NAME})
    set(_dict_file ${CMAKE_CURRENT_BINARY_DIR}/${_dict_basename}.cxx)
    set(_pcm_base ${_dict_basename}_rdict.pcm)
    set(_pcm_file ${CMAKE_LIBRARY_OUTPUT_DIRECTORY}/${_pcm_base})
    set(_rootmap_file ${CMAKE_LIBRARY_OUTPUT_DIRECTORY}/lib${ARG_NAME}.rootmap)

    # Collect headers with absolute paths for rootcling
    # Also extract directories for include paths (matches fairroot_target_root_dictionary)
    set(_abs_headers)
    set(_hdr_dirs)
    foreach(_h ${_hdrs})
      get_filename_component(_abs_h ${_h} ABSOLUTE)
      list(APPEND _abs_headers ${_abs_h})
      get_filename_component(_hdr_dir ${_abs_h} DIRECTORY)
      list(APPEND _hdr_dirs ${_hdr_dir})
    endforeach()
    get_filename_component(_abs_linkdef ${ARG_LINKDEF} ABSOLUTE)
    list(REMOVE_DUPLICATES _hdr_dirs)

    # Include directories for rootcling - will use generator expression after target exists
    set(_inc_dirs_genex $<TARGET_PROPERTY:${ARG_NAME},INCLUDE_DIRECTORIES>)

    # Add dictionary to sources
    list(APPEND _all_srcs ${_dict_file})
    set_source_files_properties(${_dict_file} PROPERTIES
      GENERATED TRUE
      COMPILE_FLAGS "-Wno-old-style-cast"
    )
  endif()

  # --- Create library with ALL sources including dictionary ---
  add_library(${ARG_NAME} SHARED ${_all_srcs} ${_hdrs})
  target_link_libraries(${ARG_NAME} PUBLIC ${_resolved_deps})
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

  # --- Dictionary generation command (after target exists for generator expressions) ---
  if(ARG_LINKDEF)
    # Add header directories as private include directories for dictionary compilation
    # (matches fairroot_target_root_dictionary behaviour)
    target_include_directories(${ARG_NAME} PRIVATE ${_hdr_dirs})

    add_custom_command(
      OUTPUT ${_dict_file} ${_pcm_file} ${_rootmap_file}
      VERBATIM
      COMMAND ${CMAKE_COMMAND} -E env
        "LD_LIBRARY_PATH=${ROOT_LIBRARY_DIR}:$ENV{LD_LIBRARY_PATH}"
        $<TARGET_FILE:ROOT::rootcling>
        -f ${_dict_file}
        -inlineInputHeader
        -rmf ${_rootmap_file}
        -rml $<TARGET_FILE_NAME:${ARG_NAME}>
        "$<$<BOOL:${_inc_dirs_genex}>:-I$<JOIN:${_inc_dirs_genex},$<SEMICOLON>-I>>"
        "$<$<BOOL:$<TARGET_PROPERTY:${ARG_NAME},COMPILE_DEFINITIONS>>:-D$<JOIN:$<TARGET_PROPERTY:${ARG_NAME},COMPILE_DEFINITIONS>,$<SEMICOLON>-D>>"
        ${_abs_headers}
        ${_abs_linkdef}
      COMMAND ${CMAKE_COMMAND} -E copy_if_different
        ${CMAKE_CURRENT_BINARY_DIR}/${_pcm_base} ${_pcm_file}
      COMMAND_EXPAND_LISTS
      DEPENDS ${_abs_headers} ${_abs_linkdef}
    )
    # Ensure ROOT::RIO is linked
    get_property(_libs TARGET ${ARG_NAME} PROPERTY INTERFACE_LINK_LIBRARIES)
    if(NOT ROOT::RIO IN_LIST _libs)
      target_link_libraries(${ARG_NAME} PUBLIC ROOT::RIO)
    endif()
    install(FILES ${_rootmap_file} ${_pcm_file} DESTINATION ${CMAKE_INSTALL_LIBDIR})
  endif()

  install(TARGETS ${ARG_NAME} DESTINATION ${CMAKE_INSTALL_LIBDIR})
  install(FILES ${_hdrs} ${_no_dict_hdrs} DESTINATION ${CMAKE_INSTALL_INCLUDEDIR})
endfunction()
