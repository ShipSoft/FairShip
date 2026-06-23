# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

ship_add_library(
  NAME ShipMuDIS
  SOURCES MuDISProcessor.cxx MuGeoProcessor.cxx MuonPath.cxx
  LINKDEF LinkDef.h
  DEPENDENCIES Base ShipData veto UpstreamTagger strawtubes EvtGen::EvtGen EvtGen::EvtGenExternal FairLogger::FairLogger pythia6::pythia6 pythia6::Pythia6
  INCLUDE_DIRECTORIES ${ROOTEGPythia6_INCLUDE_DIR}
  SYSTEM_INCLUDE_DIRECTORIES ${PYTHIA8_INCLUDE_DIR} ${PYTHIA8_INCLUDE_DIR}/..
                             ${HEPMC_INCLUDE_DIR} ${EVTGEN_INCLUDE_DIR}
                             ${EVTGEN_INCLUDE_DIR}/..
)
