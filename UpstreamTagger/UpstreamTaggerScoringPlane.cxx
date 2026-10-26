// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#include "UpstreamTaggerScoringPlane.h"

#include "ShipDetectorList.h"

UpstreamTaggerScoringPlane::UpstreamTaggerScoringPlane()
    : ScoringPlane("UpstreamTaggerScoringPlane", kTRUE,
                   kUpstreamTaggerScoringPlane) {}

UpstreamTaggerScoringPlane::UpstreamTaggerScoringPlane(const char* name,
                                                       Bool_t active)
    : ScoringPlane(name, active, kUpstreamTaggerScoringPlane) {}
