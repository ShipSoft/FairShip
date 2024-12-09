# ##############################################################################
# Copyright (C) 2014 GSI Helmholtzzentrum fuer Schwerionenforschung GmbH    # #
# This software is distributed under the terms of the             # GNU Lesser
# General Public Licence version 3 (LGPL) version 3,        # copied verbatim in
# the file "LICENSE"                       #
# ##############################################################################
# * Try to find EvtGen instalation Once done this will define
#

message(STATUS "Looking for EvtGen ...")

find_path(
  EVTGEN_INCLUDE_DIR
  NAMES EvtGen/EvtGen.hh
  PATHS ${SIMPATH}/include/EvtGen
  NO_DEFAULT_PATH)

find_path(
  EVTGEN_LIBRARY_DIR
  NAMES libEvtGen.so
  PATHS ${SIMPATH}/lib
  NO_DEFAULT_PATH)

find_path(
  EVTGENDATA
  NAMES evt.pdl
  PATHS ${SIMPATH}/share/EvtGen/)

if(NOT EVTGENDATA)
  message(STATUS "Could not find EvtGen data files")
endif()

if(EVTGEN_INCLUDE_DIR AND EVTGEN_LIBRARY_DIR)
  set(EVTGEN_FOUND TRUE)
endif(EVTGEN_INCLUDE_DIR AND EVTGEN_LIBRARY_DIR)

if(EVTGEN_FOUND)
  if(NOT EVTGEN_FOUND_QUIETLY)
    message(STATUS "Looking for EVTGEN... - found ${EVTGEN_LIBRARY_DIR}")
    set(LD_LIBRARY_PATH ${LD_LIBRARY_PATH} ${EVTGEN_LIBRARY_DIR})
  endif(NOT EVTGEN_FOUND_QUIETLY)
else(EVTGEN_FOUND)
  if(EVTGEN_FOUND_REQUIRED)
    message(FATAL_ERROR "Looking for EVTGEN... - Not found")
  endif(EVTGEN_FOUND_REQUIRED)
endif(EVTGEN_FOUND)
