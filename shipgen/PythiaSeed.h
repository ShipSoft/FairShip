// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN for the benefit of the SHiP
// Collaboration

#ifndef SHIPGEN_PYTHIASEED_H_
#define SHIPGEN_PYTHIASEED_H_

#include <cstdint>

namespace SHiP {

constexpr std::uint32_t kMaxPythiaSeed = 900000000U;

/// Return a seed accepted by the Pythia 6 and Pythia 8 interfaces.
constexpr std::uint32_t NormalizePythiaSeed(std::uint32_t seed) {
  if (seed <= kMaxPythiaSeed) return seed;
  const std::uint32_t normalizedSeed = seed % kMaxPythiaSeed;
  return normalizedSeed == 0U ? kMaxPythiaSeed : normalizedSeed;
}

static_assert(NormalizePythiaSeed(0U) == 0U);
static_assert(NormalizePythiaSeed(kMaxPythiaSeed) == kMaxPythiaSeed);
static_assert(NormalizePythiaSeed(kMaxPythiaSeed + 1U) == 1U);
static_assert(NormalizePythiaSeed(2U * kMaxPythiaSeed) == kMaxPythiaSeed);
static_assert(NormalizePythiaSeed(UINT32_MAX) <= kMaxPythiaSeed);

}  // namespace SHiP

#endif  // SHIPGEN_PYTHIASEED_H_
