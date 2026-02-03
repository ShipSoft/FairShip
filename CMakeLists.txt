# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

# The name of our project is "ShipRoot".  CMakeLists files in this project can
# refer to the root source directory of the project as ${ShipRoot_SOURCE_DIR} or
# as ${CMAKE_SOURCE_DIR} and to the root binary directory of the project as
# ${ShipRoot_BINARY_DIR} or ${CMAKE_BINARY_DIR}. This difference is important
# for the base classes which are in FAIRROOT and ShipRoot.

# CMake minimum version driven by ROOT 6.36.06
cmake_minimum_required(VERSION 3.20.0 FATAL_ERROR)

# CMP0028 and CMP0074 are already NEW at cmake_minimum_required 3.20.
# CMP0144 (3.27): use <PACKAGENAME>_ROOT variables in find_package.
if(POLICY CMP0144)
  cmake_policy(SET CMP0144 NEW)
endif()

# Set name of our project to "ShipRoot". Has to be done after check of cmake
# version since this is a new feature
project(FairShip LANGUAGES CXX)

find_path(
  FAIRBASE
  NAMES FairRun.h
  PATHS ${CMAKE_SOURCE_DIR}/base/steer ${FAIRBASE}
  NO_DEFAULT_PATH)

if(FAIRBASE)
  message(STATUS "Found FAIRBASE")
  set(FAIRBASE ${FAIRBASE})
else()
  message(STATUS "NOT Found FAIRBASE")
  if(NOT DEFINED ENV{FAIRROOTPATH})
    message(
      FATAL_ERROR
        "You did not define the environment variable FAIRROOTPATH which is needed to find FairRoot. Please set this variable and execute cmake again."
    )
  endif()
  set(FAIRROOTPATH $ENV{FAIRROOTPATH})
endif()

# where to look first for cmake modules, before ${CMAKE_ROOT}/Modules/ is
# checked
set(CMAKE_MODULE_PATH "${CMAKE_SOURCE_DIR}/cmake/modules")
set(CMAKE_MODULE_PATH "${FAIRROOTPATH}/share/fairbase/cmake/modules"
                      ${CMAKE_MODULE_PATH})
set(CMAKE_MODULE_PATH "${FAIRROOTPATH}/share/fairbase/cmake/modules_old"
                      ${CMAKE_MODULE_PATH})

if(FAIRROOTPATH)
  set(CheckSrcDir "${FAIRROOTPATH}/share/fairbase/cmake/checks")
else()
  set(CheckSrcDir "${CMAKE_SOURCE_DIR}/cmake/checks")
endif()

# Load some basic macros which are needed later on
include(FairMacros)
include(WriteConfigFile)
include(CTest)
include(CheckCompiler)

# Check the compiler and set the compile and link flags change from DEBUG to
# RELEASE, don't want to waste CPU time
if(NOT CMAKE_BUILD_TYPE)
  message("Set BuildType RELEASE")
  set(CMAKE_BUILD_TYPE Release)
endif()
check_compiler()

set(CMAKE_LIBRARY_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/lib")
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY "${CMAKE_BINARY_DIR}/bin")
set(INCLUDE_OUTPUT_DIRECTORY "${PROJECT_BINARY_DIR}/include")
set(VMCWORKDIR ${ShipRoot_SOURCE_DIR})
option(USE_PATH_INFO "Information from PATH and LD_LIBRARY_PATH are
used." OFF)

set(LD_LIBRARY_PATH $ENV{LD_LIBRARY_PATH})
if(USE_PATH_INFO)
  set(PATH "$PATH")
  if(APPLE)
    set(LD_LIBRARY_PATH $ENV{DYLD_LIBRARY_PATH})
  else()
    set(LD_LIBRARY_PATH $ENV{LD_LIBRARY_PATH})
  endif()
else()
  string(REGEX MATCHALL "[^:]+" PATH $ENV{PATH})
endif()

# --------------------- set rpath options -------------
# When building, use the RPATH
set(CMAKE_SKIP_BUILD_RPATH FALSE) # don't skip the full RPATH for the build tree
set(CMAKE_BUILD_WITH_INSTALL_RPATH FALSE) # use always the build RPATH for the
                                          # build tree
set(CMAKE_INSTALL_RPATH_USE_LINK_PATH TRUE) # point to directories outside the
                                            # build tree to the install RPATH

if(APPLE)
  set(CMAKE_MACOSX_RPATH TRUE) # use RPATH for MacOSX
  set(CMAKE_INSTALL_NAME_DIR "@rpath")
  set(CMAKE_INSTALL_RPATH "@loader_path/") # self relative LIBDIR
else()
  set(CMAKE_INSTALL_RPATH ${CMAKE_INSTALL_FULL_LIBDIR}) # install LIBDIR
endif()
# ------------------- end set rpath options -----------

# Check if the user wants to build the project in the source directory
check_out_of_source_build()

# Check if we are on an UNIX system. If not stop with an error message
if(NOT UNIX)
  message(
    FATAL_ERROR
      "You're not on an UNIX system. The project was up to now only tested on UNIX systems, so we break here. If you want to go on please edit the CMakeLists.txt in the source directory."
  )
endif()

# Set the build type. Possibilities are None, Debug, Release, RelWithDebInfo and
# MinSizeRel SET(CMAKE_BUILD_TYPE Debug)

# searches for needed packages REQUIRED means that cmake will stop if this
# packages are not found For example the framework can run without GEANT4, but
# ROOT is mandatory

find_package(FairCMakeModules 1.0 REQUIRED)
include(FairFindPackage2)
find_package2(PUBLIC ROOT 6.36 REQUIRED)
include(ROOTMacros)
# Include Ship-specific macros to override GENERATE_LIBRARY with target
# propagation
include(ShipMacros)
find_package2(PUBLIC Pythia8 REQUIRED)
find_package2(PUBLIC EvtGen REQUIRED)
# (GENERATORS REQUIRED)
find_package2(PUBLIC GEANT4)
find_package2(PUBLIC GEANT4DATA)
find_package2(PUBLIC GEANT4VMC)
find_package2(PUBLIC HEPMC)
find_package2(PUBLIC fmt)
find_package2(PUBLIC FairRoot REQUIRED)
find_package2(PUBLIC FairLogger REQUIRED)
find_package2(PUBLIC VMC REQUIRED)
find_package(genfit2 REQUIRED)

# TPythia6 was removed from ROOT in 6.32, use external EGPythia6 package
find_package(ROOTEGPythia6 REQUIRED)

if(DEFINED $ENV{GSL_ROOT})
  set(GSL_DIR $ENV{GSL_ROOT})
endif()

# set a variable which should be used in all CMakeLists.txt Defines all basic
# include directories from fairbase
message("-- Setting basic variables ...")
setbasicvariables()

# Add the FairRoot include directories to the list of libraries which are
# external to the Ship project. For include directories in this list the
# compiler will not generate any warnings. This is useful since one is only
# interested about warnings from the own project. SYSTEM_INCLUDE_DIRECTORIES is
# defined in FairMacros.cmake. In the moment the defined directories are the
# root and boost include directories.
set(SYSTEM_INCLUDE_DIRECTORIES ${SYSTEM_INCLUDE_DIRECTORIES}
                               ${BASE_INCLUDE_DIRECTORIES})

# Set the library version in the main CMakeLists.txt
set(FAIRROOT_MAJOR_VERSION 0)
set(FAIRROOT_MINOR_VERSION 0)
set(FAIRROOT_PATCH_VERSION 0)
set(FAIRROOT_VERSION
    "${FAIRROOT_MAJOR_VERSION}.${FAIRROOT_MINOR_VERSION}.${FAIRROOT_PATCH_VERSION}"
)

set(PROJECT_LIBRARY_PROPERTIES
    ${PROJECT_LIBRARY_PROPERTIES} VERSION "${FAIRROOT_VERSION}" SOVERSION
    "${FAIRROOT_MAJOR_VERSION}")

set(CBMLIBDIR ${CMAKE_BINARY_DIR}/lib)
set(LD_LIBRARY_PATH ${CBMLIBDIR} ${LD_LIBRARY_PATH})

install(DIRECTORY geometry DESTINATION pnd_install)

message("-- Set check directory to FairRoot...")
set(CheckSrcDir "${FAIRROOTPATH}/share/fairbase/cmake/checks")
# Set(CheckSrcDir "${CMAKE_SOURCE_DIR}/cmake/checks")

# Generate a Clang compile_commands.json "compilation database" file for use
# with various development tools, such as Vim's YouCompleteMe plugin. See
# http://clang.llvm.org/docs/JSONCompilationDatabase.html
set(CMAKE_EXPORT_COMPILE_COMMANDS 1)

# Recurse into the given subdirectories. This does not actually cause another
# cmake executable to run. The same process will walk through the project's
# entire directory structure.
add_subdirectory(shipdata)
add_subdirectory(passive)
add_subdirectory(SND/EmulsionTarget)
add_subdirectory(SND/MTC)
add_subdirectory(SND/SiliconTarget)
add_subdirectory(splitcal)
add_subdirectory(veto)
add_subdirectory(TimeDet)
add_subdirectory(UpstreamTagger)
add_subdirectory(strawtubes)
add_subdirectory(shipgen)
add_subdirectory(field)
add_subdirectory(muonShieldOptimization)
add_subdirectory(tests)

add_custom_target(
  geometry.link ALL
  COMMAND ${CMAKE_COMMAND} -E create_symlink ${CMAKE_SOURCE_DIR}/geometry
          ${CMAKE_BINARY_DIR}/geometry
  COMMAND ${CMAKE_COMMAND} -E create_symlink ${CMAKE_SOURCE_DIR}/macro
          ${CMAKE_BINARY_DIR}/macro
  COMMENT
    "Creating symlinks from ${CMAKE_SOURCE_DIR} to ${CMAKE_BINARY_DIR} for geometry and macro"
)
