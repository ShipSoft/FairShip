# The name of our project is "ShipRoot".  CMakeLists files in this project can
# refer to the root source directory of the project as ${ShipRoot_SOURCE_DIR} 
# or as ${CMAKE_SOURCE_DIR} and to the root binary directory of the project as 
# ${ShipRoot_BINARY_DIR} or ${CMAKE_BINARY_DIR}.
# This difference is important for the base classes which are in FAIRROOT 
# and ShipRoot.

# Check if cmake has the required version
CMAKE_MINIMUM_REQUIRED(VERSION 3.9.4 FATAL_ERROR)

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

if(FAIRROOTPATH)
  find_package(FairRoot)
endif(FAIRROOTPATH)

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

# Check if FairSoft is available, defines SIMPATH
IF(NOT DEFINED ENV{SIMPATH})
   MESSAGE(STATUS "You did not define the environment variable SIMPATH. Using aliBuild recipe.") 
ENDIF(NOT DEFINED ENV{SIMPATH})

SET(SIMPATH $ENV{SIMPATH})

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
find_package(Pythia8 REQUIRED)
find_package(EvtGen REQUIRED)
find_package(GENERATORS REQUIRED)
find_package(GEANT3)
find_package(GEANT4)
find_package(GEANT4DATA)
find_package(GEANT4VMC)
find_package(HEPMC)

IF(DEFINED ${BOOST_ROOT})
  Set(Boost_NO_SYSTEM_PATHS TRUE)
  Set(Boost_NO_BOOST_CMAKE TRUE)
ENDIF(DEFINED ${BOOST_ROOT})
#  set(Boost_DEBUG TRUE)
  IF(DEFINED ENV{SIMPATH})
    If(${ROOT_LIBRARY_DIR} MATCHES /lib/root)
      set(BOOST_ROOT ${SIMPATH})
      set(GSL_DIR ${SIMPATH})
    Else(${ROOT_LIBRARY_DIR} MATCHES /lib/root)
      set(BOOST_ROOT ${SIMPATH}/basics/boost)
      set(GSL_DIR ${SIMPATH}/basics/gsl)
    EndIf(${ROOT_LIBRARY_DIR} MATCHES /lib/root)
  ELSE(DEFINED ENV{SIMPATH})
    IF(DEFINED ${BOOST_ROOT})
      set(BOOST_ROOT $ENV{BOOST_ROOT})
    ENDIF(DEFINED ${BOOST_ROOT})
    IF(DEFINED $ENV{GSL_ROOT})
      set(GSL_DIR $ENV{GSL_ROOT})
    ENDIF(DEFINED $ENV{GSL_ROOT})
  ENDIF(DEFINED ENV{SIMPATH})

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

# Check if the compiler support specific C++11 features
# Up to now this is only a check since the code does not use
# any of the features of the new standard

IF(FAIRROOT_FOUND)
 Set(CheckSrcDir "${FAIRROOTPATH}/share/fairbase/cmake/checks")
ELSE(FAIRROOT_FOUND)
 Set(CheckSrcDir "${CMAKE_SOURCE_DIR}/cmake/checks")
ENDIF(FAIRROOT_FOUND)

include(CheckCXX11Features)

IF(HAS_CXX11_SHAREDPOINTER)
  Add_Definitions(-DHAS_SHAREDPOINTER)
ENDIF(HAS_CXX11_SHAREDPOINTER)

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

IF(NOT FAIRROOT_FOUND)
add_subdirectory (fairtools)
add_subdirectory (base)
add_subdirectory (geobase)
add_subdirectory (parbase)
add_subdirectory (dbase)
add_subdirectory (MbsAPI)
add_subdirectory (trackbase)
add_subdirectory (geane)
add_subdirectory (generators)
ENDIF (NOT FAIRROOT_FOUND)

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
add_subdirectory (online)
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
IF(DEFINED SIMPATH)
  MESSAGE(STATUS "Write configuration files ...")
  WRITE_CONFIG_FILE(config.sh)
  WRITE_CONFIG_FILE(config.csh)

# manipulate the config file:

# add environment for use of GENIE
MESSAGE(STATUS "Looking for GENIE ...")
# genie in general
FIND_PATH(GENIE  NAMES genie PATHS
  ${SIMPATH}/../FairSoft/generators
  ${GENIE_ROOT}
  NO_DEFAULT_PATH
)

If(NOT GENIE)
  Message(STATUS "Could not find Genie source directory")
Else()
  file(APPEND ${CMAKE_BINARY_DIR}/config.csh "setenv GENIE \"${GENIE}/genie\"\n")
  file(APPEND ${CMAKE_BINARY_DIR}/config.sh  "export GENIE=\"${GENIE}/genie\"\n")
EndIf()

# location of cross section files
FIND_PATH(GENPATH NAMES genie PATHS
  ${SIMPATH}/share/
  ${GENIE_ROOT}
  NO_DEFAULT_PATH
)

If(NOT GENPATH)
  Message(STATUS "Could not find Genie data files")
Else()
 file(APPEND ${CMAKE_BINARY_DIR}/config.csh "setenv GENPATH \"${GENPATH}\"\n")
 file(APPEND ${CMAKE_BINARY_DIR}/config.sh  "export GENPATH=\"${GENPATH}\"\n")
EndIf()

# location of pdf file
FIND_PATH(LHAPATH NAMES PDFsets.index PATHS
  ${SIMPATH}/share/lhapdf/PDFsets
  ${LHAPDF5_ROOT}/share/lhapdf
  NO_DEFAULT_PATH
)

If(NOT LHAPATH)
  Message(STATUS "Could not find LHA data files")
Else()
  IF(DEFINED SIMPATH)
    file(APPEND ${CMAKE_BINARY_DIR}/config.csh "setenv LHAPATH \"${LHAPATH}/data\"\n")
    file(APPEND ${CMAKE_BINARY_DIR}/config.sh  "export LHAPATH=\"${LHAPATH}/data\"\n")
  ENDIF(DEFINED SIMPATH)
EndIf()

# for lxplus, need to change LD_LIBRARY_PATH
execute_process(COMMAND lsb_release -is OUTPUT_VARIABLE distribution)

If(${distribution} MATCHES "ScientificCERNSLC")
 Message("add lcg setup")
 file(APPEND ${CMAKE_BINARY_DIR}/config.csh "if ( -f lcg.csh ) then\n")
 file(APPEND ${CMAKE_BINARY_DIR}/config.csh " rm lcg.csh\n")
 file(APPEND ${CMAKE_BINARY_DIR}/config.csh "endif\n")
 file(APPEND ${CMAKE_BINARY_DIR}/config.sh "if [ -e lcg.sh ];\n")
 file(APPEND ${CMAKE_BINARY_DIR}/config.sh "then\n")
 file(APPEND ${CMAKE_BINARY_DIR}/config.sh " rm lcg.sh\n")
 file(APPEND ${CMAKE_BINARY_DIR}/config.sh "fi\n")
 file(APPEND ${CMAKE_BINARY_DIR}/config.csh "eval /afs/cern.ch/sw/lcg/releases/lcgenv/latest/lcgenv -G -p  /afs/cern.ch/sw/lcg/releases/${LCGVERSION} ${GCCVERSION} Python >> lcg.csh\n")
 file(APPEND ${CMAKE_BINARY_DIR}/config.sh  "eval /afs/cern.ch/sw/lcg/releases/lcgenv/latest/lcgenv -G -p  /afs/cern.ch/sw/lcg/releases/${LCGVERSION} ${GCCVERSION} Python >> lcg.sh\n")
 file(APPEND ${CMAKE_BINARY_DIR}/config.csh "eval /afs/cern.ch/sw/lcg/releases/lcgenv/latest/lcgenv -G -p  /afs/cern.ch/sw/lcg/releases/${LCGVERSION} ${GCCVERSION} numpy >> lcg.csh\n")
 file(APPEND ${CMAKE_BINARY_DIR}/config.sh  "eval /afs/cern.ch/sw/lcg/releases/lcgenv/latest/lcgenv -G -p  /afs/cern.ch/sw/lcg/releases/${LCGVERSION} ${GCCVERSION} numpy >> lcg.sh\n")
 file(APPEND ${CMAKE_BINARY_DIR}/config.csh "eval /afs/cern.ch/sw/lcg/releases/lcgenv/latest/lcgenv -G -p /afs/cern.ch/sw/lcg/releases/${LCGVERSION}  ${GCCVERSION} scipy >> lcg.csh\n")
 file(APPEND ${CMAKE_BINARY_DIR}/config.sh  "eval /afs/cern.ch/sw/lcg/releases/lcgenv/latest/lcgenv -G -p /afs/cern.ch/sw/lcg/releases/${LCGVERSION}  ${GCCVERSION} scipy >> lcg.sh\n")
 file(APPEND ${CMAKE_BINARY_DIR}/config.csh "eval /afs/cern.ch/sw/lcg/releases/lcgenv/latest/lcgenv -G -p /afs/cern.ch/sw/lcg/releases/${LCGVERSION}  ${GCCVERSION} matplotlib >> lcg.csh\n")
 file(APPEND ${CMAKE_BINARY_DIR}/config.sh  "eval /afs/cern.ch/sw/lcg/releases/lcgenv/latest/lcgenv -G -p /afs/cern.ch/sw/lcg/releases/${LCGVERSION}  ${GCCVERSION} matplotlib >> lcg.sh\n")
 file(APPEND ${CMAKE_BINARY_DIR}/config.csh "eval /afs/cern.ch/sw/lcg/releases/lcgenv/latest/lcgenv -G -p /afs/cern.ch/sw/lcg/releases/${LCGVERSION}  ${GCCVERSION} numexpr >> lcg.csh\n")
 file(APPEND ${CMAKE_BINARY_DIR}/config.sh  "eval /afs/cern.ch/sw/lcg/releases/lcgenv/latest/lcgenv -G -p /afs/cern.ch/sw/lcg/releases/${LCGVERSION}  ${GCCVERSION} numexpr >> lcg.sh\n")
 file(APPEND ${CMAKE_BINARY_DIR}/config.csh "eval /afs/cern.ch/sw/lcg/releases/lcgenv/latest/lcgenv -G -p /afs/cern.ch/sw/lcg/releases/${LCGVERSION}  ${GCCVERSION} pandas >> lcg.csh\n")
 file(APPEND ${CMAKE_BINARY_DIR}/config.sh  "eval /afs/cern.ch/sw/lcg/releases/lcgenv/latest/lcgenv -G -p /afs/cern.ch/sw/lcg/releases/${LCGVERSION}  ${GCCVERSION} pandas >> lcg.sh\n")
 file(APPEND ${CMAKE_BINARY_DIR}/config.csh "eval /afs/cern.ch/sw/lcg/releases/lcgenv/latest/lcgenv -G -p /afs/cern.ch/sw/lcg/releases/${LCGVERSION}  ${GCCVERSION} scikitlearn >> lcg.csh\n")
 file(APPEND ${CMAKE_BINARY_DIR}/config.sh  "eval /afs/cern.ch/sw/lcg/releases/lcgenv/latest/lcgenv -G -p /afs/cern.ch/sw/lcg/releases/${LCGVERSION}  ${GCCVERSION} scikitlearn >> lcg.sh\n")
# remove duplicated lines
 file(APPEND ${CMAKE_BINARY_DIR}/config.sh  "perl -i -ne 'print if ! \$a{\$_}++' lcg.sh\n")
 file(APPEND ${CMAKE_BINARY_DIR}/config.csh "perl -i -ne 'print if ! \$a{\$_}++' lcg.csh\n")
 file(APPEND ${CMAKE_BINARY_DIR}/config.csh "source lcg.csh\n")
 file(APPEND ${CMAKE_BINARY_DIR}/config.sh  "source ./lcg.sh\n")
 file(APPEND ${CMAKE_BINARY_DIR}/config.csh "rm lcg.csh\n")
 file(APPEND ${CMAKE_BINARY_DIR}/config.sh  "rm lcg.sh\n")
 
EndIf()

# add some other useful environment variables:
file(APPEND ${CMAKE_BINARY_DIR}/config.csh "setenv FAIRSHIPRUN \"${CMAKE_CURRENT_BINARY_DIR}\"\n")
file(APPEND ${CMAKE_BINARY_DIR}/config.sh  "export FAIRSHIPRUN=\"${CMAKE_CURRENT_BINARY_DIR}\"\n")

file(APPEND ${CMAKE_BINARY_DIR}/config.csh  "setenv EOSSHIP \"root://eospublic.cern.ch/\"\n")
file(APPEND ${CMAKE_BINARY_DIR}/config.sh  "export EOSSHIP=\"root://eospublic.cern.ch/\"\n")

file(APPEND ${CMAKE_BINARY_DIR}/config.csh "setenv FAIRSHIP \"${CMAKE_CURRENT_SOURCE_DIR}\"\n")
file(APPEND ${CMAKE_BINARY_DIR}/config.sh  "export FAIRSHIP=\"${CMAKE_CURRENT_SOURCE_DIR}\"\n")

file(APPEND ${CMAKE_BINARY_DIR}/config.sh  "if [ `uname` = \"Darwin\" ]; then\n")
file(APPEND ${CMAKE_BINARY_DIR}/config.sh  "   # DYLD_LIBRARY_PATH is not set in python on macOS due to SIP\n")
file(APPEND ${CMAKE_BINARY_DIR}/config.sh  "   echo \"# This file has been created by config.sh\" > .rootrc\n")
file(APPEND ${CMAKE_BINARY_DIR}/config.sh  "   echo \"Unix.*.Root.DynamicPath: $DYLD_LIBRARY_PATH\" >> .rootrc\n")
file(APPEND ${CMAKE_BINARY_DIR}/config.sh  "fi\n")

file(APPEND ${CMAKE_BINARY_DIR}/config.csh  "if ( `uname` == \"Darwin\" ) then\n")
file(APPEND ${CMAKE_BINARY_DIR}/config.csh  "   # DYLD_LIBRARY_PATH is not set in python on macOS due to SIP\n")
file(APPEND ${CMAKE_BINARY_DIR}/config.csh  "   echo \"# This file has been created by config.csh\" > .rootrc\n")
file(APPEND ${CMAKE_BINARY_DIR}/config.csh  "   echo \"Unix.*.Root.DynamicPath: $DYLD_LIBRARY_PATH\" >> .rootrc\n")
file(APPEND ${CMAKE_BINARY_DIR}/config.csh  "endif\n")

file(APPEND ${CMAKE_BINARY_DIR}/config.csh "  source ${SIMPATH}/bin/geant4.csh ${SIMPATH}/bin\n")
file(APPEND ${CMAKE_BINARY_DIR}/config.sh  "  source ${SIMPATH}/bin/geant4.sh \n")

configure_file(${CMAKE_SOURCE_DIR}/CTestCustom.cmake 
               ${CMAKE_BINARY_DIR}/CTestCustom.cmake
              )

ENDIF(DEFINED SIMPATH)
