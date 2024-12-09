# ##############################################################################
# Copyright (C) 2014 GSI Helmholtzzentrum fuer Schwerionenforschung GmbH    # #
# This software is distributed under the terms of the             # GNU Lesser
# General Public Licence (LGPL) version 3,             # copied verbatim in the
# file "LICENSE"                       #
# ##############################################################################
# Configure FairVersion.h
# ------------------------------

find_package(Git)

if(GIT_FOUND AND EXISTS "${SOURCE_DIR}/.git")
  execute_process(
    COMMAND ${GIT_EXECUTABLE} describe --tags
    OUTPUT_VARIABLE FAIRROOT_GIT_VERSION
    OUTPUT_STRIP_TRAILING_WHITESPACE
    WORKING_DIRECTORY ${SOURCE_DIR})
  execute_process(
    COMMAND ${GIT_EXECUTABLE} log -1 --format=%cd
    OUTPUT_VARIABLE FAIRROOT_GIT_DATE
    OUTPUT_STRIP_TRAILING_WHITESPACE
    WORKING_DIRECTORY ${SOURCE_DIR})
  message(
    STATUS
      "FairShip Version - ${FAIRSHIP_GIT_VERSION} from - ${FAIRSHIP_GIT_DATE}")
endif()
