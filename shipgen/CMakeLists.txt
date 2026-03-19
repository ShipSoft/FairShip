# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

ship_add_library(
  NAME ShipGen
  SOURCES Generator.cxx Pythia8Generator.cxx Pythia6Generator.cxx tPythia6Generator.cxx
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
