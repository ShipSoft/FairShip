// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#include "Tracklet.h"

#include <unordered_map>

#include "strawtubesHit.h"
#include "strawtubesPoint.h"

// -----   Default constructor   -------------------------------------------
Tracklet::Tracklet() : flag(0) {}

// -----   Constructor with indices -------------------------------------------
Tracklet::Tracklet(Int_t fl, const std::vector<unsigned int>& indices)
    : aTracklet(indices), flag(fl) {}

// -----   Constructor with hits   -------------------------------------------
Tracklet::Tracklet(Int_t fl, const std::vector<strawtubesHit>& hits,
                   const std::vector<strawtubesHit>& container)
    : flag(fl) {
  aTracklet.reserve(hits.size());
  for (const auto& hit : hits) {
    // Find index of hit in container by comparing addresses
    for (size_t i = 0; i < container.size(); ++i) {
      if (&container[i] == &hit) {
        aTracklet.push_back(static_cast<unsigned int>(i));
        break;
      }
    }
  }
}

// -----   Destructor   ----------------------------------------------------
Tracklet::~Tracklet() {}
// -------------------------------------------------------------------------

Int_t Tracklet::link2MCTrack(std::vector<strawtubesPoint>* strawPoints,
                             Float_t min) {
  Int_t nTot = aTracklet.size();
  std::unordered_map<int, int> MC;
  Int_t trackID = -1;
  for (std::vector<int>::size_type i = 0; i != aTracklet.size(); i++) {
    trackID = (*strawPoints)[aTracklet[i]].GetTrackID();
    MC[trackID] += 1. / nTot;
    if (MC[trackID] > min) {
      break;
    }
  }
  return trackID;
}
