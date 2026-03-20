// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#ifndef SHIPDATA_SHIPGEOUTIL_H_
#define SHIPDATA_SHIPGEOUTIL_H_

#include "FairGeoBuilder.h"
#include "FairGeoInterface.h"
#include "FairGeoLoader.h"
#include "FairGeoMedia.h"
#include "FairGeoMedium.h"
#include "FairLogger.h"
#include "TGeoManager.h"
#include "TGeoMedium.h"

namespace ShipGeo {

/// Initialise a tracking medium from the FairRoot media file.
/// Returns the medium index, or creates it via FairGeoBuilder if it does not
/// yet exist in gGeoManager.
inline Int_t InitMedium(const char* name) {
  static FairGeoLoader* geoLoad = FairGeoLoader::Instance();
  static FairGeoInterface* geoFace = geoLoad->getGeoInterface();
  static FairGeoMedia* media = geoFace->getMedia();
  static FairGeoBuilder* geoBuild = geoLoad->getGeoBuilder();

  FairGeoMedium* ShipMedium = media->getMedium(name);

  if (!ShipMedium) {
    LOG(fatal) << "ShipGeo::InitMedium: Material " << name
               << " not defined in media file.";
    return -1111;
  }
  TGeoMedium* medium = gGeoManager->GetMedium(name);
  if (medium != nullptr) return ShipMedium->getMediumIndex();

  return geoBuild->createMedium(ShipMedium);
}

}  // namespace ShipGeo

#endif  // SHIPDATA_SHIPGEOUTIL_H_
