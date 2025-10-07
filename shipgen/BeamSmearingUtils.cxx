// SPDX-License-Identifier: LGPL-3.0-or-later
// SPDX-FileCopyrightText: Copyright CERN on behalf of the SHiP Collaboration

#include "BeamSmearingUtils.h"

#include "TMath.h"
#include "TRandom.h"

std::pair<Double_t, Double_t> CalculateBeamOffset(Double_t smearBeam, Double_t paintBeam)
{
    Double_t dx = 0.0;
    Double_t dy = 0.0;

    // Gaussian beam smearing
    if (smearBeam > 0) {
        dx = gRandom->Gaus(0, smearBeam);
        dy = gRandom->Gaus(0, smearBeam);
    }

    // Uniform circular beam painting
    if (paintBeam > 0) {
        Double_t phi = gRandom->Uniform(0., 2 * TMath::Pi());
        dx += paintBeam * TMath::Cos(phi);
        dy += paintBeam * TMath::Sin(phi);
    }

    return {dx, dy};
}
