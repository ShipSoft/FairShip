# The name of our project is "ShipRoot".  CMakeLists files in this project can
# refer to the root source directory of the project as ${ShipRoot_SOURCE_DIR} 
# or as ${CMAKE_SOURCE_DIR} and to the root binary directory of the project as 
# ${ShipRoot_BINARY_DIR} or ${CMAKE_BINARY_DIR}.
# This difference is important for the base classes which are in FAIRROOT 
# and ShipRoot.

# Check if cmake has the required version
CMAKE_MINIMUM_REQUIRED(VERSION 3.9.4 FATAL_ERROR)
include(CMakePrintHelpers)
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

FIND_PATH(FAIRBASE NAMES FairRun.h  PATHS
  ${CMAKE_SOURCE_DIR}/base/steer
  ${FAIRBASE}
  NO_DEFAULT_PATH
)

If (FAIRBASE)
  Message(STATUS "Found FAIRBASE")
  SET(FAIRBASE ${FAIRBASE})
Else (FAIRBASE)
  Message(STATUS "NOT Found FAIRBASE")
  IF(NOT DEFINED ENV{FAIRROOTPATH})
     MESSAGE(FATAL_ERROR "You did not define the environment variable FAIRROOTPATH which is needed to find FairRoot. Please set this variable and execute cmake again.")
  ENDIF(NOT DEFINED ENV{FAIRROOTPATH})
  SET(FAIRROOTPATH $ENV{FAIRROOTPATH})
EndIf (FAIRBASE)

# where to look first for cmake modules, before ${CMAKE_ROOT}/Modules/ 
# is checked
set(CMAKE_MODULE_PATH "${CMAKE_SOURCE_DIR}/cmake/modules")
set(CMAKE_MODULE_PATH "${FAIRROOTPATH}/share/fairbase/cmake/modules"  ${CMAKE_MODULE_PATH})
set(CMAKE_MODULE_PATH "${FAIRROOTPATH}/share/fairbase/cmake/modules_old"  ${CMAKE_MODULE_PATH})

IF(FAIRROOTPATH)
  Set(CheckSrcDir "${FAIRROOTPATH}/share/fairbase/cmake/checks")
ELSE(FAIRROOTPATH)
  Set(CheckSrcDir "${CMAKE_SOURCE_DIR}/cmake/checks")
ENDIF(FAIRROOTPATH)

# Load some basic macros which are needed later on
include(FairMacros)
include(WriteConfigFile)
include(CTest)
include(CheckCompiler)

#Check the compiler and set the compile and link flags
# change from DEBUG to RELEASE, don't want to waste CPU time
If(NOT CMAKE_BUILD_TYPE)
  Message("Set BuildType RELEASE")
  set(CMAKE_BUILD_TYPE Release)
EndIf(NOT CMAKE_BUILD_TYPE)
Check_Compiler()

set(LIBRARY_OUTPUT_PATH "${CMAKE_BINARY_DIR}/lib")
set(EXECUTABLE_OUTPUT_PATH "${CMAKE_BINARY_DIR}/bin")
set(INCLUDE_OUTPUT_DIRECTORY "${PROJECT_BINARY_DIR}/include")
Set(VMCWORKDIR ${ShipRoot_SOURCE_DIR})
Option(USE_PATH_INFO "Information from PATH and LD_LIBRARY_PATH are
used." OFF)

Set(LD_LIBRARY_PATH $ENV{LD_LIBRARY_PATH})
If(USE_PATH_INFO)
  Set(PATH "$PATH")
  If (APPLE)
    Set(LD_LIBRARY_PATH $ENV{DYLD_LIBRARY_PATH})
  Else (APPLE)
    Set(LD_LIBRARY_PATH $ENV{LD_LIBRARY_PATH})
  EndIf (APPLE)
Else(USE_PATH_INFO)
  STRING(REGEX MATCHALL "[^:]+" PATH $ENV{PATH})
EndIf(USE_PATH_INFO)

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
CHECK_OUT_OF_SOURCE_BUILD()

# Check if we are on an UNIX system. If not stop with an error
# message
IF(NOT UNIX)
  MESSAGE(FATAL_ERROR "You're not on an UNIX system. The project was up to now only tested on UNIX systems, so we break here. If you want to go on please edit the CMakeLists.txt in the source directory.")
ENDIF(NOT UNIX)  

# Check if the external packages are installed into a separate install
# directory
CHECK_EXTERNAL_PACKAGE_INSTALL_DIR()

# Set the build type. Possibilities are None, Debug, Release, 
# RelWithDebInfo and MinSizeRel 
#SET(CMAKE_BUILD_TYPE Debug)

# searches for needed packages
# REQUIRED means that cmake will stop if this packages are not found
# For example the framework can run without GEANT4, but ROOT is
# mandatory

find_package(ROOT 6.10.06 REQUIRED)
find_package2(PUBLIC Pythia8 REQUIRED)
find_package2(PUBLIC EvtGen REQUIRED)
# (GENERATORS REQUIRED)
find_package2(PUBLIC GEANT3)
find_package2(PUBLIC GEANT4)
find_package2(PUBLIC GEANT4DATA)
find_package2(PUBLIC GEANT4VMC)
find_package2(PUBLIC HEPMC)

cmake_print_variables(ROOT_vmc_FOUND)
if(ROOT_FOUND_VERSION GREATER 62599)
  find_package2(PUBLIC VMC REQUIRED)
  set(VMCLIB VMCLibrary)
else()
  set(VMCLIB ROOT::VMC)
endif()

find_package2(PUBLIC FairRoot REQUIRED)

find_package2(PUBLIC FairLogger REQUIRED)

IF(DEFINED ${BOOST_ROOT})
  Set(Boost_NO_SYSTEM_PATHS TRUE)
  Set(Boost_NO_BOOST_CMAKE TRUE)
ENDIF(DEFINED ${BOOST_ROOT})
#  set(Boost_DEBUG TRUE)
IF(DEFINED ${BOOST_ROOT})
      set(BOOST_ROOT $ENV{BOOST_ROOT})
ENDIF(DEFINED ${BOOST_ROOT})
IF(DEFINED $ENV{GSL_ROOT})
      set(GSL_DIR $ENV{GSL_ROOT})
ENDIF(DEFINED $ENV{GSL_ROOT})

  Message("-- Looking for Boost ...")
  # If an older version of boost is found both of the variables below are
  # cached and in a second cmake run, a good boost version is found even 
  # if the version is to old. 
  # To overcome this problem both variables are cleared before checking
  # for boost.
  Unset(Boost_INCLUDE_DIR CACHE)
  Unset(Boost_LIBRARY_DIRS CACHE)
  find_package(Boost 1.41)
  If (Boost_FOUND)
    Set(Boost_Avail 1)
  Else (Boost_FOUND)
    Set(Boost_Avail 0)
  EndIf (Boost_FOUND)

# set a variable which should be used in all CMakeLists.txt
# Defines all basic include directories from fairbase
  Message("-- Setting basic variables ...")
SetBasicVariables()

# Add the FairRoot include directories to the list of libraries which are
# external to the Ship project. For include directories in this list the
# compiler will not generate any warnings. This is usefull since one is only
# interested about warnings from the own project. SYSTEM_INCLUDE_DIRECTORIES
# is defined in FairMacros.cmake. In the moment the defined directories are
# the root and boost include directories. 
Set(SYSTEM_INCLUDE_DIRECTORIES 
  ${SYSTEM_INCLUDE_DIRECTORIES}
  ${BASE_INCLUDE_DIRECTORIES}
  ${FAIRLOGGER_INCLUDE_DIR}
)

# Set the library version in the main CMakeLists.txt
SET(FAIRROOT_MAJOR_VERSION 0)
SET(FAIRROOT_MINOR_VERSION 0)
SET(FAIRROOT_PATCH_VERSION 0)
SET(FAIRROOT_VERSION "${FAIRROOT_MAJOR_VERSION}.${FAIRROOT_MINOR_VERSION}.${FAIRROOT_PATCH_VERSION}")

If(ROOT_FOUND_VERSION LESS 59999)
  SET(FAIRROOT_LIBRARY_PROPERTIES ${FAIRROOT_LIBRARY_PROPERTIES}
      VERSION "${FAIRROOT_VERSION}"
      SOVERSION "${FAIRROOT_MAJOR_VERSION}"
      SUFFIX ".so"
  )
Else()
  SET(FAIRROOT_LIBRARY_PROPERTIES ${FAIRROOT_LIBRARY_PROPERTIES}
      VERSION "${FAIRROOT_VERSION}"
      SOVERSION "${FAIRROOT_MAJOR_VERSION}"
  )
  SET(CMAKE_SHARED_LIBRARY_SUFFIX .so)
EndIf()

Generate_Version_Info()

SET(CBMLIBDIR ${CMAKE_BINARY_DIR}/lib)
SET(LD_LIBRARY_PATH  ${CBMLIBDIR} ${LD_LIBRARY_PATH})

#IF(CMAKE_INSTALL_PREFIX_INITIALIZED_TO_DEFAULT)
#  SET(CMAKE_INSTALL_PREFIX "./install" CACHE PATH "FOO install prefix" FORCE)
#  Message("Set default install path ...")
#ENDIF(CMAKE_INSTALL_PREFIX_INITIALIZED_TO_DEFAULT)

install(DIRECTORY geometry DESTINATION pnd_install 
          PATTERN ".svn" EXCLUDE
          )

Message("-- Set check directory to FairRoot...")
Set(CheckSrcDir "${FAIRROOTPATH}/share/fairbase/cmake/checks")
# Set(CheckSrcDir "${CMAKE_SOURCE_DIR}/cmake/checks")

# --------------- add targets for code style and submission checks -------------
find_package(Git)
find_package(ClangTools)
if ("$ENV{CMAKE_EXPORT_COMPILE_COMMANDS}" STREQUAL "1" OR CLANG_TIDY_FOUND)
  # Generate a Clang compile_commands.json "compilation database" file for use
  # with various development tools, such as Vim's YouCompleteMe plugin.
  # See http://clang.llvm.org/docs/JSONCompilationDatabase.html
  set(CMAKE_EXPORT_COMPILE_COMMANDS 1)
endif()
include(CppStyleGuideChecks)

# Recurse into the given subdirectories. This does not actually
# cause another cmake executable to run. The same process will walk through
# the project's entire directory structure.

IF(NOT FairRoot_FOUND)
Message("--- FairRoot not found ...")
ENDIF (NOT FairRoot_FOUND)

add_subdirectory (sndFairTasks)
add_subdirectory (shipLHC)
add_subdirectory (shipdata)
add_subdirectory (passive)
add_subdirectory (nutaudet)
add_subdirectory (charmdet)
add_subdirectory (ecal)
add_subdirectory (splitcal)
add_subdirectory (hcal)
add_subdirectory (veto)
add_subdirectory (TimeDet)
add_subdirectory (UpstreamTagger)
add_subdirectory (strawtubes)
add_subdirectory (muon)
add_subdirectory (shipgen)
add_subdirectory (field)
add_subdirectory (genfit)
add_subdirectory (preshower)
add_subdirectory (pid)
add_subdirectory (muonShieldOptimization)
add_subdirectory (millepede)

FIND_PATH(TEvePath NAMES TEveEventManager.h PATHS
  ${SIMPATH}/tools/root/include
  ${SIMPATH}/include/root
  $ENV{ROOTSYS}/include/root
  NO_DEFAULT_PATH
)

If(TEvePath)
#find_package(OpenGL)
#If (OPENGL_FOUND AND OPENGL_GLU_FOUND)
  Message("Found TEve, so the eventdisplay will be compiled.")

 IF(NOT FAIRROOT_FOUND)
  add_subdirectory (eventdisplay)
 ENDIF(NOT FAIRROOT_FOUND)

EndIf(TEvePath)

add_custom_target(  # make relative links to folders
    geometry.link ALL
    COMMAND [ -e geometry ] || python -c \"import os.path as p, os\; os.symlink(p.join(p.relpath('${CMAKE_SOURCE_DIR}', '${CMAKE_BINARY_DIR}') , 'geometry') , 'geometry') \"
    COMMAND [ -e macro ] || python -c \"import os.path as p, os\; os.symlink(p.join(p.relpath('${CMAKE_SOURCE_DIR}', '${CMAKE_BINARY_DIR}') , 'macro') , 'macro') \"
)
