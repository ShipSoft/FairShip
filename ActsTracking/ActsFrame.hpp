// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#ifndef ACTSTRACKING_ACTSFRAME_HPP_
#define ACTSTRACKING_ACTSFRAME_HPP_

#include "Acts/Definitions/Algebra.hpp"
#include "Acts/Definitions/Units.hpp"

/// Conversions between the SHiP frame and the ACTS reconstruction frame.
///
/// The SHiP frame has the beam along z and lengths in cm. The ACTS frame used
/// for the fit has the beam along x, so that tracks sit near theta = 90 deg
/// and away from the coordinate singularity of the bound parameters, and
/// lengths in mm:
///
///   x_acts = z_ship, y_acts = y_ship, z_acts = -x_ship
namespace SHiP::ActsFrame {

/// Rotation taking ACTS-frame vectors to the SHiP frame
inline Acts::RotationMatrix3 toShipRotation() {
  Acts::RotationMatrix3 rotation;
  rotation << 0, 0, -1,  //
      0, 1, 0,           //
      1, 0, 0;
  return rotation;
}

/// Rotation taking SHiP-frame vectors to the ACTS frame
inline Acts::RotationMatrix3 toActsRotation() {
  return toShipRotation().transpose();
}

/// Length unit of the SHiP frame, in ACTS units
inline constexpr double kShipLength = Acts::UnitConstants::cm;

inline Acts::Vector3 positionToActs(double x, double y, double z) {
  return toActsRotation() * Acts::Vector3(x, y, z) * kShipLength;
}

inline Acts::Vector3 positionToShip(const Acts::Vector3& position) {
  return toShipRotation() * position / kShipLength;
}

inline Acts::Vector3 momentumToActs(double px, double py, double pz) {
  return toActsRotation() * Acts::Vector3(px, py, pz) *
         Acts::UnitConstants::GeV;
}

inline Acts::Vector3 momentumToShip(const Acts::Vector3& momentum) {
  return toShipRotation() * momentum / Acts::UnitConstants::GeV;
}

/// Transform of a TGeo placement (SHiP frame, cm) in the ACTS frame
inline Acts::Transform3 transformToActs(const Acts::Transform3& shipTransform) {
  Acts::Transform3 transform = Acts::Transform3::Identity();
  transform.linear() = toActsRotation() * shipTransform.linear();
  transform.translation() =
      toActsRotation() * shipTransform.translation() * kShipLength;
  return transform;
}

}  // namespace SHiP::ActsFrame

#endif  // ACTSTRACKING_ACTSFRAME_HPP_
