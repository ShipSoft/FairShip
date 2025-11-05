#include "MTCDetHit.h"

#include "FairRunSim.h"
#include "MTCDetPoint.h"
#include "MTCDetector.h"
#include "TGeoBBox.h"
#include "TGeoManager.h"
#include "TGeoNavigator.h"
#include "TROOT.h"

#include <TRandom.h>

namespace
{
constexpr Float_t n_photons_min = 3.5f;
constexpr Float_t n_photons_max = 104.0f;
constexpr Float_t time_res = 150e-3f;     // 150 ps
constexpr Float_t signal_speed = 15.0f;   // cm/ns
const Float_t inv_signal_speed = 1.0f / signal_speed;
// parameters for simulating the digitized information
constexpr Float_t light_attenuation_params[2] = {20., 300.};                 // x_0, lambda
constexpr Float_t n_pixels_to_qdc_params[4] = {0.172, -1.31, 0.006, 0.33};   // A, B, sigma_A, sigma_B
}   // namespace

// -----   Default constructor   -------------------------------------------
MTCDetHit::MTCDetHit()
    : ShipHit()
{
    flag = true;
}

// Optimized MTCDetHit Constructor

MTCDetHit::MTCDetHit(int SiPMChan, const std::vector<MTCDetPoint*>& points, const std::vector<Float_t>& weights)
{
    // Retrieve detector once
    static auto* MTCDet = dynamic_cast<MTCDetector*>(gROOT->GetListOfGlobals()->FindObject("MTC"));

    // Constants
    fDetectorID = SiPMChan;   // Set the detector ID
    // Determine plane type once
    const int plane_type = GetStationType();

    Float_t total_light_yield = 0.0f;
    Float_t earliest_to_A = std::numeric_limits<Float_t>::max();
    Float_t earliest_to_B = std::numeric_limits<Float_t>::max();
    Float_t signal_sum = 0.0f;
    bool hit_flag = false;

    // Separate handling for scintillating mat (plane_type == 2)
    if (plane_type == 2) {
        for (auto* pt : points) {
            signal_sum += pt->GetEnergyLoss();
            // Track earliest arrival time
            Float_t arrival = pt->GetTime();
            earliest_to_B = std::min(earliest_to_B, arrival);
        }
        flag = true;
        time = gRandom->Gaus(earliest_to_B, time_res);
        signals = signal_sum;
        return;
    }

    // Fiber hit processing
    const size_t n = points.size();
    total_light_yield = 0.0f;

    TVector3 sipmA, sipmB;
    MTCDet->GetSiPMPosition(SiPMChan, sipmA, sipmB);

    for (size_t i = 0; i < n; ++i) {
        auto* pt = points[i];
        Float_t energy = pt->GetEnergyLoss();
        Float_t weight = weights[i];
        Float_t signal = energy * weight;

        // Distance from deposit to SiPM
        TVector3 impact(pt->GetX(), pt->GetY(), pt->GetZ());
        const Float_t distance = (sipmB - impact).Mag();

        // Light yield before attenuation
        Float_t light_yield = signal * 1e6f * 0.16f;
        light_yield *= light_attenuation(distance);
        total_light_yield += light_yield;

        // Track earliest arrival time
        Float_t arrival = pt->GetTime() + distance * inv_signal_speed;
        earliest_to_A = std::min(earliest_to_A, arrival);
    }

    // Apply statistical smearing and saturation
    const Int_t smeared_light_yield = gRandom->Poisson(total_light_yield);
    const Float_t n_pixels = sipm_saturation(smeared_light_yield);
    signals = n_pixels_to_qdc(n_pixels);

    // Final hit decision and time
    hit_flag = (smeared_light_yield > n_photons_min);
    flag = hit_flag;
    time = gRandom->Gaus(earliest_to_A, time_res);
}

// -----   Destructor   ----------------------------------------------------
MTCDetHit::~MTCDetHit() {}
// -------------------------------------------------------------------------

// -----   Public method GetEnergy   -------------------------------------------
Float_t MTCDetHit::GetEnergy()
{
    // to be calculated from digis and calibration constants, missing!
    return signals;
}

Float_t MTCDetHit::light_attenuation(Float_t distance)
{
    //	It returns the light yield attenuation depending on the distance to SiPM
    return TMath::Exp(-(distance - light_attenuation_params[0]) / light_attenuation_params[1]);
}

Float_t MTCDetHit::sipm_saturation(Float_t ly)
{
    //	It returns the number of fired pixels per channel
    Float_t factor = 1 - TMath::Exp(-ly / n_photons_max);
    return n_photons_max * factor;
}

Float_t MTCDetHit::n_pixels_to_qdc(Float_t npix)
{
    //	It returns QDC per channel after Gaussian smearing of the parameters
    Float_t A = gRandom->Gaus(n_pixels_to_qdc_params[0], n_pixels_to_qdc_params[2]);
    Float_t B = gRandom->Gaus(n_pixels_to_qdc_params[1], n_pixels_to_qdc_params[3]);
    return A * npix + B;
}

// -----   Public method Print   -------------------------------------------
void MTCDetHit::Print()
{
    std::cout << Form(
        "MTCDetHit: Detector ID %d, Layer %d, Station Type %d, SiPM %d, Channel %d, Signal %.2f, Time %.3f \n",
        fDetectorID,
        GetLayer(),
        GetStationType(),
        GetSiPM(),
        GetSiPMChan(),
        signals,
        time);
}
