// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#ifndef ACTSTRACKING_ACTSSHIPFIELD_HPP_
#define ACTSTRACKING_ACTSSHIPFIELD_HPP_

#include "Acts/MagneticField/MagneticFieldContext.hpp"
#include "Acts/MagneticField/MagneticFieldProvider.hpp"
#include "Acts/Utilities/Result.hpp"

class TVirtualMagField;

namespace SHiP {

/// ACTS view of a FairShip magnetic field.
///
/// Wraps the field used in the simulation (e.g. the global field of the
/// ShipFieldMaker), so the fit sees the same field map, placement and
/// orientation as Geant4. Positions and field values are converted between
/// the ACTS reco frame and the SHiP frame (cm, kGauss).
class ActsShipField final : public Acts::MagneticFieldProvider {
 public:
  /// The field is not owned and must outlive this object
  explicit ActsShipField(TVirtualMagField* field);

  Cache makeCache(const Acts::MagneticFieldContext& mctx) const override;
  Acts::Result<Acts::Vector3> getField(const Acts::Vector3& position,
                                       Cache& cache) const override;

 private:
  TVirtualMagField* m_field;
};

}  // namespace SHiP

#endif  // ACTSTRACKING_ACTSSHIPFIELD_HPP_
