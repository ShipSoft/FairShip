# The name of our project is "ShipRoot".  CMakeLists files in this project can
# refer to the root source directory of the project as ${ShipRoot_SOURCE_DIR}
# or as ${CMAKE_SOURCE_DIR} and to the root binary directory of the project as
# ${ShipRoot_BINARY_DIR} or ${CMAKE_BINARY_DIR}.
# This difference is important for the base classes which are in FAIRROOT
# and ShipRoot.

# Check if cmake has the required version
cmake_minimum_required(VERSION 3.12.0 FATAL_ERROR)

foreach(p
  CMP0028 # double colon for imported and alias targets
  CMP0074 # use _ROOT env variables
  )
  if(POLICY ${p})
  cmake_policy(SET ${p} NEW)
  endif()
endforeach()

# Set name of our project to "ShipRoot". Has to be done
# after check of cmake version since this is a new feature
project(ShipRoot)

find_path(FAIRBASE NAMES FairRun.h  PATHS
  ${CMAKE_SOURCE_DIR}/base/steer
  ${FAIRBASE}
  NO_DEFAULT_PATH
)

if(FAIRBASE)
  message(STATUS "Found FAIRBASE")
  set(FAIRBASE ${FAIRBASE})
else()
  message(STATUS "NOT Found FAIRBASE")
  if(NOT DEFINED ENV{FAIRROOTPATH})
    message(FATAL_ERROR "You did not define the environment variable FAIRROOTPATH which is needed to find FairRoot. Please set this variable and execute cmake again.")
  endif()
  set(FAIRROOTPATH $ENV{FAIRROOTPATH})
endif()

# where to look first for cmake modules, before ${CMAKE_ROOT}/Modules/
# is checked
set(CMAKE_MODULE_PATH "${CMAKE_SOURCE_DIR}/cmake/modules")
set(CMAKE_MODULE_PATH "${FAIRROOTPATH}/share/fairbase/cmake/modules"  ${CMAKE_MODULE_PATH})
set(CMAKE_MODULE_PATH "${FAIRROOTPATH}/share/fairbase/cmake/modules_old"  ${CMAKE_MODULE_PATH})

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

#Check the compiler and set the compile and link flags
# change from DEBUG to RELEASE, don't want to waste CPU time
if(NOT CMAKE_BUILD_TYPE)
  message("Set BuildType RELEASE")
  set(CMAKE_BUILD_TYPE Release)
endif()
check_compiler()

set(LIBRARY_OUTPUT_PATH "${CMAKE_BINARY_DIR}/lib")
set(EXECUTABLE_OUTPUT_PATH "${CMAKE_BINARY_DIR}/bin")
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

#--------------------- set rpath options -------------
# When building, use the RPATH
set(CMAKE_SKIP_BUILD_RPATH FALSE)           # don't skip the full RPATH for the build tree
set(CMAKE_BUILD_WITH_INSTALL_RPATH FALSE)   # use always the build RPATH for the build tree
set(CMAKE_INSTALL_RPATH_USE_LINK_PATH TRUE) # point to directories outside the build tree to the install RPATH

if(APPLE)
  set(CMAKE_MACOSX_RPATH TRUE)                 # use RPATH for MacOSX
  set(CMAKE_INSTALL_NAME_DIR "@rpath")
  set(CMAKE_INSTALL_RPATH "@loader_path/")     # self relative LIBDIR
else()
  set(CMAKE_INSTALL_RPATH ${CMAKE_INSTALL_FULL_LIBDIR}) # install LIBDIR
endif()
#------------------- end set rpath options -----------

# Check if the user wants to build the project in the source
# directory
check_out_of_source_build()

# Check if we are on an UNIX system. If not stop with an error
# message
if(NOT UNIX)
  message(FATAL_ERROR "You're not on an UNIX system. The project was up to now only tested on UNIX systems, so we break here. If you want to go on please edit the CMakeLists.txt in the source directory.")
endif(NOT UNIX)

# Set the build type. Possibilities are None, Debug, Release,
# RelWithDebInfo and MinSizeRel
#SET(CMAKE_BUILD_TYPE Debug)

# searches for needed packages
# REQUIRED means that cmake will stop if this packages are not found
# For example the framework can run without GEANT4, but ROOT is
# mandatory

find_package(FairCMakeModules 1.0 REQUIRED)
include(FairFindPackage2)
find_package2(PUBLIC ROOT 6.26.14 REQUIRED)
include(ROOTMacros)
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

if(DEFINED ${BOOST_ROOT})
  set(Boost_NO_SYSTEM_PATHS TRUE)
  set(Boost_NO_BOOST_CMAKE TRUE)
endif(DEFINED ${BOOST_ROOT})
#  set(Boost_DEBUG TRUE)
if(DEFINED ${BOOST_ROOT})
      set(BOOST_ROOT $ENV{BOOST_ROOT})
endif(DEFINED ${BOOST_ROOT})
if(DEFINED $ENV{GSL_ROOT})
      set(GSL_DIR $ENV{GSL_ROOT})
endif(DEFINED $ENV{GSL_ROOT})

find_package(Boost 1.70 REQUIRED)

# set a variable which should be used in all CMakeLists.txt
# Defines all basic include directories from fairbase
message("-- Setting basic variables ...")
setbasicvariables()

# Add the FairRoot include directories to the list of libraries which are
# external to the Ship project. For include directories in this list the
# compiler will not generate any warnings. This is usefull since one is only
# interested about warnings from the own project. SYSTEM_INCLUDE_DIRECTORIES
# is defined in FairMacros.cmake. In the moment the defined directories are
# the root and boost include directories.
set(SYSTEM_INCLUDE_DIRECTORIES
  ${SYSTEM_INCLUDE_DIRECTORIES}
  ${BASE_INCLUDE_DIRECTORIES}
)

# Set the library version in the main CMakeLists.txt
set(FAIRROOT_MAJOR_VERSION 0)
set(FAIRROOT_MINOR_VERSION 0)
set(FAIRROOT_PATCH_VERSION 0)
set(FAIRROOT_VERSION "${FAIRROOT_MAJOR_VERSION}.${FAIRROOT_MINOR_VERSION}.${FAIRROOT_PATCH_VERSION}")

set(FAIRROOT_LIBRARY_PROPERTIES ${FAIRROOT_LIBRARY_PROPERTIES}
	VERSION "${FAIRROOT_VERSION}"
	SOVERSION "${FAIRROOT_MAJOR_VERSION}"
)
set(CMAKE_SHARED_LIBRARY_SUFFIX .so)

set(CBMLIBDIR ${CMAKE_BINARY_DIR}/lib)
set(LD_LIBRARY_PATH  ${CBMLIBDIR} ${LD_LIBRARY_PATH})

install(DIRECTORY geometry DESTINATION pnd_install
          PATTERN ".svn" EXCLUDE
          )

message("-- Set check directory to FairRoot...")
set(CheckSrcDir "${FAIRROOTPATH}/share/fairbase/cmake/checks")
# Set(CheckSrcDir "${CMAKE_SOURCE_DIR}/cmake/checks")

# Generate a Clang compile_commands.json "compilation database" file for use
# with various development tools, such as Vim's YouCompleteMe plugin.
# See http://clang.llvm.org/docs/JSONCompilationDatabase.html
set(CMAKE_EXPORT_COMPILE_COMMANDS 1)

# Recurse into the given subdirectories. This does not actually
# cause another cmake executable to run. The same process will walk through
# the project's entire directory structure.
add_subdirectory(shipdata)
add_subdirectory(passive)
add_subdirectory(nutaudet)
add_subdirectory(ecal)
add_subdirectory(splitcal)
add_subdirectory(hcal)
add_subdirectory(veto)
add_subdirectory(TimeDet)
add_subdirectory(UpstreamTagger)
add_subdirectory(strawtubes)
add_subdirectory(muon)
add_subdirectory(shipgen)
add_subdirectory(field)
add_subdirectory(pid)

add_custom_target(  # make relative links to folders
    geometry.link ALL
    COMMAND [ -e geometry ] || python -c \"import os.path as p, os\; os.symlink(p.join(p.relpath('${CMAKE_SOURCE_DIR}', '${CMAKE_BINARY_DIR}') , 'geometry') , 'geometry') \"
    COMMAND [ -e macro ] || python -c \"import os.path as p, os\; os.symlink(p.join(p.relpath('${CMAKE_SOURCE_DIR}', '${CMAKE_BINARY_DIR}') , 'macro') , 'macro') \"
)
