# SPDX-License-Identifier: LGPL-3.0-or-later
# SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP Collaboration

ship_add_library(
  NAME ShipMuDIS
  SOURCES MuDISFilter.cxx MagneticTrackPropagator.cxx MuDISProcessor.cxx MuGeoProcessor.cxx MuonPath.cxx NewMuDISGenerator.cxx
  LINKDEF LinkDef.h
  DEPENDENCIES Base ShipData ShipField veto ShipGen UpstreamTagger strawtubes TimeDet EvtGen::EvtGen EvtGen::EvtGenExternal FairLogger::FairLogger ROOT::EGPythia6
  EXTRA_DICT_HEADERS MuDISDefs.h
  INCLUDE_DIRECTORIES ${ROOTEGPythia6_INCLUDE_DIR}
  SYSTEM_INCLUDE_DIRECTORIES ${PYTHIA8_INCLUDE_DIR} ${PYTHIA8_INCLUDE_DIR}/..
                             ${EVTGEN_INCLUDE_DIR} ${EVTGEN_INCLUDE_DIR}/..
)
