# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

# Define PYTHIA_VERSION_INTEGER for older Pythia8 versions that don't have it
try_compile(
  HAS_PYTHIA_VERSION_INTEGER ${CMAKE_BINARY_DIR}/temp
  ${CMAKE_SOURCE_DIR}/cmake/test_pythia_version.cpp
  CMAKE_FLAGS "-DINCLUDE_DIRECTORIES=${PYTHIA8_INCLUDE_DIR}"
  OUTPUT_VARIABLE COMPILE_OUTPUT)

ship_add_library(
  NAME ShipGen
  SOURCES ShipGenerator.cxx Pythia8Generator.cxx Pythia6Generator.cxx tPythia6Generator.cxx
          HNLPythia8Generator.cxx DPPythia8Generator.cxx GenieGenerator.cxx
          NtupleGenerator.cxx MuonBackGenerator.cxx CosmicsGenerator.cxx
          MuDISGenerator.cxx FixedTargetGenerator.cxx EvtCalcGenerator.cxx
          TEvtGenDecayer.cxx BeamSmearingUtils.cxx MeanMaterialBudget.cxx
  LINKDEF LinkDef.h
  DEPENDENCIES Base ShipData veto EvtGen::EvtGen EvtGen::EvtGenExternal
               FairLogger::FairLogger ROOT::EGPythia6
  INCLUDE_DIRECTORIES ${ROOTEGPythia6_INCLUDE_DIR}
  SYSTEM_INCLUDE_DIRECTORIES ${PYTHIA8_INCLUDE_DIR} ${PYTHIA8_INCLUDE_DIR}/..
                             ${HEPMC_INCLUDE_DIR} ${EVTGEN_INCLUDE_DIR}
                             ${EVTGEN_INCLUDE_DIR}/..
)

# Apply Pythia version definition to this target only
if(NOT HAS_PYTHIA_VERSION_INTEGER)
  if(PYTHIA8_VERSION)
    string(REPLACE "." "" PYTHIA8_VERSION_INTEGER ${PYTHIA8_VERSION})
    target_compile_definitions(ShipGen PRIVATE
      PYTHIA_VERSION_INTEGER=${PYTHIA8_VERSION_INTEGER})
    message(STATUS
      "Defined PYTHIA_VERSION_INTEGER=${PYTHIA8_VERSION_INTEGER} for Pythia8 ${PYTHIA8_VERSION}")
  else()
    target_compile_definitions(ShipGen PRIVATE PYTHIA_VERSION_INTEGER=8223)
    message(STATUS "Defined PYTHIA_VERSION_INTEGER=8223 for old Pythia8 version")
  endif()
else()
  message(STATUS "PYTHIA_VERSION_INTEGER already defined in Pythia8 headers")
endif()
