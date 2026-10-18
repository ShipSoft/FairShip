// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#include "ActsShipField.hpp"

#include <stdexcept>

#include "Acts/Definitions/Units.hpp"
#include "ActsFrame.hpp"
#include "TVirtualMagField.h"

namespace SHiP {

namespace {
// FairRoot/VMC fields are in kGauss
constexpr double kKiloGauss = 0.1 * Acts::UnitConstants::T;
}  // namespace

ActsShipField::ActsShipField(TVirtualMagField* field) : m_field(field) {
  if (m_field == nullptr) {
    throw std::invalid_argument("ActsShipField: field is null");
  }
}

Acts::MagneticFieldProvider::Cache ActsShipField::makeCache(
    const Acts::MagneticFieldContext& /*mctx*/) const {
  return Cache{};
}

Acts::Result<Acts::Vector3> ActsShipField::getField(
    const Acts::Vector3& position, Cache& /*cache*/) const {
  const Acts::Vector3 shipPosition = ActsFrame::positionToShip(position);
  const double x[3] = {shipPosition.x(), shipPosition.y(), shipPosition.z()};
  double b[3] = {0., 0., 0.};
  m_field->Field(x, b);
  const Acts::Vector3 shipField(b[0], b[1], b[2]);
  return Acts::Result<Acts::Vector3>::success(ActsFrame::toActsRotation() *
                                              shipField * kKiloGauss);
}

}  // namespace SHiP
