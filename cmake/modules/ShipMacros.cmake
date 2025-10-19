# ShipMacros.cmake Extended version of GENERATE_LIBRARY() with target-based
# include propagation
#
# This file should be included AFTER FairRootMacros.cmake to wrap GENERATE_LIBRARY

# Save FairRoot's original GENERATE_LIBRARY macro
macro(_FAIRROOT_GENERATE_LIBRARY)
  generate_library()
endmacro()

# Rename the original macro before we override it
if(COMMAND generate_library)
  # Store a reference to FairRoot's implementation
  macro(_FAIRROOT_ORIGINAL_GENERATE_LIBRARY)
    _cmake_original_generate_library_impl()
  endmacro()
endif()

# Override GENERATE_LIBRARY to add target-based include propagation
macro(GENERATE_LIBRARY)
  # Store library name and source dir for later use
  set(_SHIP_LIB_NAME ${LIBRARY_NAME})
  set(_SHIP_CURRENT_SOURCE ${CMAKE_CURRENT_SOURCE_DIR})

  # Call FairRoot's original GENERATE_LIBRARY implementation
  # We can't rename macros in CMake, so we need to inline the call
  # This works by temporarily undefining our override
  macro(_ship_temp_generate_library)
    # Include FairRoot's macro file again to get the original implementation
    # But we can't do that, so instead we just call it directly by duplicating
    # the exact same code that FairRoot uses

    # Actually, let's try a different approach: just call the macro
    # that FairRoot defines, which should be available
    set(Int_LIB ${LIBRARY_NAME})
    set(HeaderRuleName "${Int_LIB}_HEADER_RULES")
    set(DictName "G__${Int_LIB}Dict.cxx")

    if(NOT DICTIONARY)
      set(DICTIONARY ${CMAKE_CURRENT_BINARY_DIR}/${DictName})
    endif()

    if(IS_ABSOLUTE ${DICTIONARY})
      set(DICTIONARY ${DICTIONARY})
    else()
      set(Int_DICTIONARY ${CMAKE_CURRENT_SOURCE_DIR}/${DICTIONARY})
    endif()

    set(Int_SRCS ${SRCS})

    if(HEADERS)
      set(HDRS ${HEADERS})
    else()
      CHANGE_FILE_EXTENSION(*.cxx *.h HDRS "${SRCS}")
    endif()

    install(FILES ${HDRS} DESTINATION include)

    if(LINKDEF)
      if(IS_ABSOLUTE ${LINKDEF})
        set(Int_LINKDEF ${LINKDEF})
      else()
        set(Int_LINKDEF ${CMAKE_CURRENT_SOURCE_DIR}/${LINKDEF})
      endif()

      # For dictionary generation, we need to add source directories of dependencies
      # to INCLUDE_DIRECTORIES so rootcint can find headers
      set(_original_include_dirs ${INCLUDE_DIRECTORIES})
      foreach(d ${DEPENDENCIES})
        # Skip targets that aren't FairShip libraries
        if(TARGET ${d})
          get_target_property(_dep_source_dir ${d} SOURCE_DIR)
          if(_dep_source_dir)
            list(APPEND INCLUDE_DIRECTORIES ${_dep_source_dir})
          endif()
        endif()
      endforeach()

      # Use FairRoot's dictionary generation macro
      # Both FairRoot v18.8.2 and v19+ use macros with no parameters
      # They read variables from parent scope: LINKDEF, DICTIONARY, LIBRARY_NAME, HDRS, etc.
      if(COMMAND FAIRROOT_GENERATE_DICTIONARY)
        # FairRoot v19+ - call without parameters
        FAIRROOT_GENERATE_DICTIONARY()
      else()
        # FairRoot v18.8.2 - call ROOT_GENERATE_DICTIONARY without parameters
        ROOT_GENERATE_DICTIONARY()
      endif()

      # Restore original INCLUDE_DIRECTORIES
      set(INCLUDE_DIRECTORIES ${_original_include_dirs})

      set(Int_SRCS ${Int_SRCS} ${DICTIONARY})
      set_source_files_properties(${DICTIONARY} PROPERTIES COMPILE_FLAGS
                                                            "-Wno-old-style-cast")
    endif()

    set(Int_DEPENDENCIES)
    foreach(d ${DEPENDENCIES})
      get_filename_component(_ext ${d} EXT)
      if(_ext)
        set(Int_DEPENDENCIES ${Int_DEPENDENCIES} ${d})
      else()
        if(TARGET ${d})
          set(Int_DEPENDENCIES ${Int_DEPENDENCIES} ${d})
        else()
          set(Int_DEPENDENCIES ${Int_DEPENDENCIES} ${${d}_LIBRARY})
        endif()
      endif()
    endforeach()

    add_library(${Int_LIB} SHARED ${Int_SRCS})
    target_link_libraries(${Int_LIB} ${Int_DEPENDENCIES})
    set_target_properties(${Int_LIB} PROPERTIES ${PROJECT_LIBRARY_PROPERTIES})

    install(TARGETS ${Int_LIB} DESTINATION lib)
  endmacro()

  _ship_temp_generate_library()

  # Add Ship extension - target-based include propagation
  if(TARGET ${_SHIP_LIB_NAME})
    target_include_directories(
      ${_SHIP_LIB_NAME}
      PUBLIC # During build, use the source directory
             $<BUILD_INTERFACE:${_SHIP_CURRENT_SOURCE}>
             # After install, use the install include directory
             $<INSTALL_INTERFACE:include>)
  endif()
endmacro()
